import sys
import os

# Add the current directory to sys.path to allow imports from 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8005, reload=True)
