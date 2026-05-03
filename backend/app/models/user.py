from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.database.session import Base

class User(Base):
    """Unified user model for Google, Email Link, and OTP auth."""
    __tablename__ = "users"

    # email is the primary key and unique identifier
    email = Column(String, primary_key=True, index=True)
    # name can be null if not provided by auth method
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
