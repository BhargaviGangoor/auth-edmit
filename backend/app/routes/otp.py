from fastapi import APIRouter, Depends, HTTPException, Body, Request, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.otp_service import OTPService
from app.services.auth_service import AuthService

from app.services.email_service import email_service
from app.services.captcha_service import CaptchaService
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request, BackgroundTasks
import os

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/otp", tags=["OTP Auth"])

class SendOTPRequest(BaseModel):
    email: str
    captcha_token: str = None

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str

@router.post("/send-otp")
@limiter.limit("5/minute")
async def send_otp(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: SendOTPRequest,
    db: Session = Depends(get_db)
):
    """Generate and send an OTP + Magic Link to the user's email."""
    print(f"Incoming payload: {payload.dict()}")
    email = payload.email
    captcha_token = payload.captcha_token
    
    # 1. Verify Captcha
    if not CaptchaService.verify_turnstile_token(captcha_token):
        raise HTTPException(status_code=400, detail="Captcha verification failed")
    
    # 2. Generate OTP and Magic Token
    otp, magic_token = OTPService.create_otp(db, email)
    
    # 3. Send email in background
    background_tasks.add_task(email_service.send_otp_email, email, otp, magic_token)
    
    response = {
        "success": True,
        "message": f"Login link and code sent to {email}"
    }

    if os.getenv("APP_MODE") != "production":
        response["otp_test"] = otp
        response["magic_token_test"] = magic_token

    return response

@router.post("/verify-otp")
async def verify_otp(
    payload: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """Verify the OTP and return JWT tokens + user data."""
    is_valid = OTPService.validate_otp(db, payload.email, payload.otp)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    
    # Get or create local user
    user, is_new = AuthService.get_or_create_user(db, payload.email)
    
    # Check if user has passkey
    from app.models.passkey import Passkey
    has_passkey = db.query(Passkey).filter(Passkey.user_email == user.email).first() is not None
    
    return AuthService.unified_auth_response(user, method="otp", is_new=is_new, has_passkey=has_passkey)
