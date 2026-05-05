from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, LargeBinary, ForeignKey
from app.database.session import Base

class Passkey(Base):
    """Storage for user's registered WebAuthn credentials."""
    __tablename__ = "passkeys"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email"), index=True)
    credential_id = Column(String, unique=True, index=True)
    public_key = Column(LargeBinary)
    sign_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
