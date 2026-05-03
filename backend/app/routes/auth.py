from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.auth_service import AuthService

router = APIRouter(tags=["Firebase Auth"])

@router.post("/verify-firebase-token")
async def verify_firebase_token(
    token: str = Body(..., embed=True), 
    db: Session = Depends(get_db)
):
    """Verify a Firebase ID Token (Google or Email Link)."""
    id_info = AuthService.verify_firebase_token(token)
    if not id_info:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
    
    email = id_info.get("email")
    name = id_info.get("name")
    picture = id_info.get("picture")
    
    user = AuthService.get_or_create_user(db, email, name, picture)
    
    return AuthService.unified_auth_response(user, method="firebase")
