import os
from sqlalchemy.orm import Session
from app.models.user import User
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "otp-auth-project-3b7b0")

class AuthService:
    @staticmethod
    def get_or_create_user(db: Session, email: str, name: str = None, picture: str = None) -> User:
        """Fetch a user or create a new one if they don't exist."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, name=name, picture=picture)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def verify_firebase_token(token: str):
        """Verify Firebase ID Token using google-auth library."""
        try:
            id_info = id_token.verify_firebase_token(
                token, 
                google_requests.Request(), 
                audience=FIREBASE_PROJECT_ID
            )
            return id_info
        except Exception as e:
            print(f"Firebase verification error: {e}")
            return None

    @staticmethod
    def unified_auth_response(user: User, method: str):
        """Format a consistent response for all auth methods."""
        return {
            "uid": user.email, # Using email as UID for simplicity in this prototype
            "email": user.email,
            "auth_status": "authenticated",
            "method": method,
            "user": {
                "name": user.name or user.email.split('@')[0],
                "picture": user.picture,
                "created_at": user.created_at.isoformat()
            }
        }
