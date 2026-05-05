from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Boolean
from app.database.session import Base

class OTPCode(Base):
    """Storage for backend-generated OTP codes."""
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    otp_hash = Column(String)
    magic_token_hash = Column(String, nullable=True)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
