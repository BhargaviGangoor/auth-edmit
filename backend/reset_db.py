from database import engine, Base, OTP

def reset_otps():
    print("Dropping 'otps' table...")
    OTP.__table__.drop(engine, checkfirst=True)
    print("Recreating all tables...")
    Base.metadata.create_all(engine)
    print("Database reset complete.")

if __name__ == "__main__":
    reset_otps()
