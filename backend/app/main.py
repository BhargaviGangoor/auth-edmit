from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database.session import engine, Base
from app.routes import auth, otp, passkey

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Edmitted Auth API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def catch_exceptions_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        print("\n" + "="*50)
        print("CRITICAL SERVER ERROR DETECTED")
        print("="*50)
        traceback.print_exc()
        print("="*50 + "\n")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "traceback": "Check server logs for details"},
            headers={"Access-Control-Allow-Origin": "*"} # Ensure CORS doesn't hide the error
        )

# Include Routers
app.include_router(auth.router)
app.include_router(otp.router)
app.include_router(passkey.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
