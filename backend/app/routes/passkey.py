from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
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

class PasskeyFinishRequest(BaseModel):
    email: str
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
async def login_start(payload: PasskeyEmailRequest, db: Session = Depends(get_db)):
    """Start Passkey login."""
    email = payload.email
    passkeys = db.query(Passkey).filter(Passkey.user_email == email).all()
    if not passkeys:
        raise HTTPException(status_code=400, detail="No passkeys registered for this email")
    
    # Reconstruct AttestedCredentialData for fido2
    credentials = []
    for p in passkeys:
        # This is a bit simplified, usually you'd store more info
        # But for MVP we'll try to reconstruct or just use the ID
        pass # fido2 can work with just the ID for authenticate_begin
    
    # fido2 authenticate_begin expects a list of registered credentials
    # but for simple verification, we can just start and then verify against the DB
    auth_data, state = passkey_service.server.authenticate_begin([
        AttestedCredentialData.create(
            websafe_decode(p.credential_id), 
            cbor.decode(p.public_key),
            b"" # AAGUID
        ) for p in passkeys
    ])
    
    challenge_store[email] = state
    return json_serializable({
        "publicKey": auth_data["publicKey"]
    })

@router.post("/login/finish")
async def login_finish(
    payload: PasskeyFinishRequest,
    db: Session = Depends(get_db)
):
    """Complete Passkey login."""
    email = payload.email
    response = payload.response
    state = challenge_store.get(email)
    if not state:
        raise HTTPException(status_code=400, detail="Challenge not found")
    
    passkeys = db.query(Passkey).filter(Passkey.user_email == email).all()
    credentials = [
        AttestedCredentialData.create(
            websafe_decode(p.credential_id), 
            cbor.decode(p.public_key),
            b""
        ) for p in passkeys
    ]
    
    try:
        # Verify
        auth_data = passkey_service.finish_authentication(state, credentials, response)
        
        # Update sign count
        # Find which passkey was used
        cred_id = websafe_encode(auth_data.credential_data.credential_id)
        db_passkey = db.query(Passkey).filter(Passkey.credential_id == cred_id).first()
        if db_passkey:
            db_passkey.sign_count = auth_data.counter
            db.commit()
            
        # Authenticate user
        user = db.query(User).filter(User.email == email).first()
        del challenge_store[email]
        
        return AuthService.unified_auth_response(user, method="passkey")
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Passkey verification failed")
