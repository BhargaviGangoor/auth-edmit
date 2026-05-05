from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from app.database.session import Base

class User(Base):
    """Unified user model for Google, Email Link, and OTP auth."""
    __tablename__ = "users"

    # email is the primary key and unique identifier
    email = Column(String, primary_key=True, index=True)
    # name can be null if not provided by auth method
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    role = Column(String, nullable=True) # student, mentor
    onboarded = Column(Boolean, default=False)
    preferences = Column(String, nullable=True) # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
