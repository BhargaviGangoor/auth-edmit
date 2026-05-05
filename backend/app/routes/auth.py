from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import AuthService
from app.services.otp_service import OTPService
from app.services.jwt_service import JWTService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])

class FirebaseVerifyRequest(BaseModel):
    token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class OnboardingRequest(BaseModel):
    name: str
    role: str
    email: str
    preferences: Optional[str] = None

@router.post("/verify-firebase-token")
async def verify_firebase_token(
    payload: FirebaseVerifyRequest,
    db: Session = Depends(get_db)
):
    """Verify a Firebase ID Token and return JWTs."""
    id_info = AuthService.verify_firebase_token(payload.token)
    if not id_info:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
    
    email = id_info.get("email")
    name = id_info.get("name")
    picture = id_info.get("picture")
    
    user, is_new = AuthService.get_or_create_user(db, email, name, picture)
    
    return AuthService.unified_auth_response(user, method="firebase", is_new=is_new)

@router.get("/callback")
async def magic_link_callback(token: str, db: Session = Depends(get_db)):
    """Authenticate user via magic link token."""
    email = OTPService.validate_magic_token(db, token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired magic link")
    
    user, is_new = AuthService.get_or_create_user(db, email)
    return AuthService.unified_auth_response(user, method="magic_link", is_new=is_new)

@router.post("/refresh")
async def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh the access token using a valid refresh token."""
    refresh_token = payload.refresh_token
    payload_data = JWTService.decode_token(refresh_token)
    if not payload_data or payload_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    email = payload_data.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_access_token = JWTService.create_access_token({"sub": user.email, "email": user.email})
    return {"access_token": new_access_token}

@router.post("/onboarding")
async def complete_onboarding(
    payload: OnboardingRequest,
    db: Session = Depends(get_db)
):
    """Complete onboarding for a new user."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.name = payload.name
    user.role = payload.role
    user.preferences = payload.preferences
    user.onboarded = True
    db.commit()
    
    return {"success": True, "message": "Onboarding complete"}
