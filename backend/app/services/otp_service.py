import random
import string
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.otp import OTPCode
from app.models.user import User

class OTPService:
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a random numeric OTP."""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def hash_otp(otp: str) -> str:
        """Hash the OTP using SHA-256."""
        return hashlib.sha256(otp.encode()).hexdigest()

    @staticmethod
    def verify_otp_hash(otp: str, hashed_otp: str) -> bool:
        """Verify a plain OTP against its SHA-256 hash."""
        return hashlib.sha256(otp.encode()).hexdigest() == hashed_otp

    @staticmethod
    def create_otp(db: Session, email: str) -> str:
        """
        Create a new OTP, invalidate previous ones for this email, 
        and return the plain text OTP.
        """
        # Invalidate previous unused OTPs for this email
        db.query(OTPCode).filter(
            OTPCode.email == email, 
            OTPCode.is_used == False
        ).update({"is_used": True})

        otp = OTPService.generate_otp()
        otp_hash = OTPService.hash_otp(otp)
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        new_otp = OTPCode(
            email=email,
            otp_hash=otp_hash,
            expires_at=expires_at
        )
        db.add(new_otp)
        db.commit()
        return otp

    @staticmethod
    def validate_otp(db: Session, email: str, otp: str) -> bool:
        """
        Validate the OTP for the given email.
        Checks existence, hash, expiry, and usage status.
        """
        otp_record = db.query(OTPCode).filter(
            OTPCode.email == email,
            OTPCode.is_used == False,
            OTPCode.expires_at > datetime.utcnow()
        ).order_by(OTPCode.created_at.desc()).first()

        if not otp_record:
            return False

        if OTPService.verify_otp_hash(otp, otp_record.otp_hash):
            otp_record.is_used = True
            db.commit()
            return True
        
        return False
