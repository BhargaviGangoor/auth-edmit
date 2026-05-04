from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.session import engine, Base
from app.routes import auth, otp

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Edmitted Auth API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(otp.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
