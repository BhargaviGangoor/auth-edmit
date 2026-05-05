import os
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.jwt_service import JWTService
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

class AuthService:
    @staticmethod
    def get_or_create_user(db: Session, email: str, name: str = None, picture: str = None) -> tuple[User, bool]:
        """Fetch a user or create a new one if they don't exist. Returns (user, is_new)."""
        user = db.query(User).filter(User.email == email).first()
        is_new = False
        if not user:
            user = User(email=email, name=name, picture=picture)
            db.add(user)
            db.commit()
            db.refresh(user)
            is_new = True
        return user, is_new

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
    def unified_auth_response(user: User, method: str, is_new: bool = False, has_passkey: bool = False):
        """Format a consistent response for all auth methods, including JWTs."""
        # Generate JWT Tokens
        user_data = {"sub": user.email, "email": user.email}
        access_token = JWTService.create_access_token(user_data)
        refresh_token = JWTService.create_refresh_token(user_data)

        return {
            "uid": user.email,
            "email": user.email,
            "auth_status": "authenticated",
            "method": method,
            "is_new_user": is_new or (not user.onboarded),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "email": user.email,
                "name": user.name or user.email.split('@')[0],
                "picture": user.picture,
                "role": user.role,
                "onboarded": user.onboarded,
                "has_passkey": has_passkey,
                "created_at": user.created_at.isoformat()
            }
        }
