from app.database.session import SessionLocal, engine
from app.models.user import User
from app.models.otp import OTPCode
from sqlalchemy import text

def verify_tables():
    print("Checking database tables...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result]
        print(f"Tables found: {tables}")
        
        if 'users' in tables and 'otp_codes' in tables:
            print("✅ Core tables exist.")
        else:
            print("❌ Missing tables. Run the app to initialize them.")

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"\n--- Users ({len(users)}) ---")
        for user in users:
            print(f"Email: {user.email} | Created: {user.created_at}")
    finally:
        db.close()

def list_otps():
    db = SessionLocal()
    try:
        otps = db.query(OTPCode).all()
        print(f"\n--- OTP Codes ({len(otps)}) ---")
        for otp in otps:
            status = "USED" if otp.is_used else "ACTIVE"
            print(f"ID: {otp.id} | Email: {otp.email} | Status: {status} | Expires: {otp.expires_at}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_tables()
    list_users()
    list_otps()
