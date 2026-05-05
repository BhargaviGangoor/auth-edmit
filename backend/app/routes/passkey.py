from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.passkey import Passkey
from app.models.user import User
from app.services.passkey_service import passkey_service
from app.services.auth_service import AuthService
from fido2.webauthn import AttestedCredentialData
from fido2.utils import websafe_encode, websafe_decode
from fido2 import cbor
import json

import base64

def json_serializable(obj):
    """Recursively convert bytes to base64 strings for JSON serialization."""
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode('utf-8')
    if isinstance(obj, dict):
        return {k: json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_serializable(v) for v in obj]
    return obj

router = APIRouter(prefix="/passkey", tags=["Passkey"])

# Pydantic models for cleaner request handling
class PasskeyEmailRequest(BaseModel):
    email: str

class PasskeyLoginStartRequest(BaseModel):
    email: Optional[str] = None

class PasskeyFinishRequest(BaseModel):
    email: Optional[str] = None
    challengeId: Optional[str] = None
    response: dict

# Simple in-memory storage for challenges (Use Redis in production!)
challenge_store = {}

@router.post("/register/start")
async def register_start(payload: PasskeyEmailRequest, db: Session = Depends(get_db)):
    """Start Passkey registration."""
    email = payload.email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    registration_data, state = passkey_service.start_registration(email)
    
    # Store state for verification
    challenge_store[email] = state
    
    # Use the helper to convert bytes to base64 strings
    return json_serializable({
        "publicKey": registration_data["publicKey"]
    })

@router.post("/register/finish")
async def register_finish(
    payload: PasskeyFinishRequest,
    db: Session = Depends(get_db)
):
    """Complete Passkey registration."""
    email = payload.email
    response = payload.response
    state = challenge_store.get(email)
    if not state:
        raise HTTPException(status_code=400, detail="Challenge not found or expired")
    
    try:
        auth_data = passkey_service.finish_registration(state, response)
        credential_data = auth_data.credential_data
        
        # Save to DB - Encode the public key as CBOR bytes
        new_passkey = Passkey(
            user_email=email,
            credential_id=websafe_encode(credential_data.credential_id),
            public_key=cbor.encode(credential_data.public_key),
            sign_count=auth_data.counter
        )
        db.add(new_passkey)
        db.commit()
        
        # Cleanup challenge
        del challenge_store[email]
        
        return {"success": True, "message": "Passkey registered successfully"}
    except Exception as e:
        import traceback
        print(f"Registration finish error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login/start")
async def login_start(payload: dict = Body(...), db: Session = Depends(get_db)):
    """Start Passkey login."""
    email = payload.get("email")
    credentials = []
    
    if email:
        passkeys = db.query(Passkey).filter(Passkey.user_email == email).all()
        if passkeys:
            credentials = [
                AttestedCredentialData.create(
                    b"\0" * 16,
                    websafe_decode(p.credential_id), 
                    cbor.decode(p.public_key)
                ) for p in passkeys
            ]
    
    # fido2 authenticate_begin([]) allows discoverable credentials
    auth_data, state = passkey_service.server.authenticate_begin(credentials)
    
    # Get the challenge bytes from the auth_data
    challenge_bytes = auth_data['publicKey']['challenge']
    if isinstance(challenge_bytes, str):
        challenge_bytes = challenge_bytes.encode()
        
    # Store state by challenge to handle discoverable login where email isn't known yet
    challenge_id = websafe_encode(challenge_bytes)
    challenge_store[challenge_id] = state
    
    if email:
        challenge_store[email] = state
        
    return json_serializable({
        "publicKey": auth_data["publicKey"],
        "challengeId": challenge_id
    })

@router.post("/login/finish")
async def login_finish(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """Complete Passkey login."""
    email = payload.get("email")
    challenge_id = payload.get("challengeId")
    response = payload.get("response")
    
    state = None
    if challenge_id:
        state = challenge_store.get(challenge_id)
    if not state and email:
        state = challenge_store.get(email)
        
    if not state:
        raise HTTPException(status_code=400, detail="Challenge not found or expired")
    
    # Identify which credential was used
    cred_id_encoded = response.get('id')
    if not cred_id_encoded:
        raise HTTPException(status_code=400, detail="Credential ID missing")
        
    db_passkey = db.query(Passkey).filter(Passkey.credential_id == cred_id_encoded).first()
    if not db_passkey:
        raise HTTPException(status_code=401, detail="Passkey not recognized")
    
    if not email:
        email = db_passkey.user_email
    elif email != db_passkey.user_email:
        raise HTTPException(status_code=401, detail="Passkey mismatch")

    credentials = [
        AttestedCredentialData.create(
            b"\0" * 16,
            websafe_decode(db_passkey.credential_id), 
            cbor.decode(db_passkey.public_key)
        )
    ]
    
    try:
        # Verify
        auth_data = passkey_service.finish_authentication(state, credentials, response)
        
        # Update sign count (handle different fido2 versions)
        new_counter = None
        if hasattr(auth_data, 'counter'):
            new_counter = auth_data.counter
        elif hasattr(auth_data, 'authenticator_data') and hasattr(auth_data.authenticator_data, 'counter'):
            new_counter = auth_data.authenticator_data.counter
            
        if new_counter is not None:
            db_passkey.sign_count = new_counter
            
        db.commit()
            
        # Authenticate user
        user = db.query(User).filter(User.email == email).first()
        
        # Cleanup
        if challenge_id: challenge_store.pop(challenge_id, None)
        if email: challenge_store.pop(email, None)
        
        return AuthService.unified_auth_response(user, method="passkey", has_passkey=True)
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Passkey verification failed")
