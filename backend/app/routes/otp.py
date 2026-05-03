from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.otp_service import OTPService
from app.services.auth_service import AuthService

from app.services.email_service import email_service
import os

router = APIRouter(prefix="/otp", tags=["OTP Auth"])

@router.post("/send-otp")
async def send_otp(email: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """Generate and send an OTP to the user's email via SendGrid."""
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Generate and store OTP
    otp = OTPService.create_otp(db, email)
    
    # Send real email via SendGrid
    success = email_service.send_otp_email(email, otp)
    
    if not success:
        # If email fails, we still return the OTP in development so testing doesn't break
        if os.getenv("APP_MODE") != "production":
            return {
                "success": False,
                "message": "Failed to send email, but here is your code for testing.",
                "otp_test": otp
            }
        raise HTTPException(status_code=500, detail="Failed to send authentication email.")

    response = {
        "success": True,
        "message": f"OTP sent to {email}"
    }

    # Only include the OTP in the response if we are in development mode
    if os.getenv("APP_MODE") != "production":
        response["otp_test"] = otp

    return response

@router.post("/verify-otp")
async def verify_otp(
    email: str = Body(..., embed=True), 
    otp: str = Body(..., embed=True), 
    db: Session = Depends(get_db)
):
    """Verify the OTP and return a session token/user data."""
    is_valid = OTPService.validate_otp(db, email, otp)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    
    # Get or create local user
    user = AuthService.get_or_create_user(db, email)
    
    return AuthService.unified_auth_response(user, method="otp")
