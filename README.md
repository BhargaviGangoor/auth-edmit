# 🔥 Secure Multi-Method Authentication System

A production-ready authentication microservice providing a seamless and secure login experience using a combination of Firebase and custom backend logic. 

## ✨ Features
- **Google Sign-In:** One-click OAuth login via Firebase.
- **Custom OTP Authentication:** Backend-driven One-Time Password flow.
- **Rate Limiting:** Built-in protection against brute-force attacks using SlowAPI.
- **Database Agnostic:** Configured for SQLite out-of-the-box for rapid development, with seamless scaling to PostgreSQL.

## 🏗️ Technology Stack

### **Frontend**
- **React 19 & Vite:** Fast, modern frontend framework and build tool.
- **Firebase JS SDK:** Handles complex UI popups and token generation.
- **Vanilla CSS & Lucide React:** Clean, glassmorphic styling and scalable icons.

### **Backend**
- **FastAPI:** High-performance Python API framework.
- **SQLAlchemy:** ORM for database interactions.
- **Google Auth Library:** Securely verifies token signatures mathematically.
- **SQLite / PostgreSQL:** Persistent user data storage.

## 🤔 Why are we using Firebase?

**Firebase is used for exactly two specific jobs** in this project. It acts as our secure front door, but we maintain control of our own data.

1. **Frontend (The User Interface):** We use Firebase to handle the "Sign in with Google" popup. Instead of building the complex Google login flow from scratch, Firebase does it for us. Once the user successfully signs in, Firebase hands our frontend a secure "ID Badge" (a digital token).
2. **Backend (The Bouncer):** We use the Google Auth library on our backend to verify that "ID Badge". When the frontend sends the token to our server, the backend cryptographically verifies it, asking Google, *"Is this a real token?"* If it's real, we log the user into our system.

**Key Takeaway for Mentors & Reviewers:** 
We migrated to Firebase purely to offload the complex Google OAuth flow on the frontend and to securely verify those login tokens on the backend. **We do not use Firebase's database.** We use our own database (SQLite/PostgreSQL) to store the actual user records. Firebase just acts as the secure bouncer.

## 🚀 Getting Started

### 1. Backend Setup
Open a terminal and navigate to the `backend` directory:
```bash
cd backend
python -m venv .venv
# Activate the virtual environment (Windows):
.venv\Scripts\activate
# Activate the virtual environment (Mac/Linux):
# source .venv/bin/activate

pip install -r requirements.txt
```

Run the FastAPI server:
```bash
uvicorn main:app --reload --port 8005
```
*(The backend is now configured to run on port 8005 by default to avoid conflicts).*
*(Note: If your entry point is inside `app/`, you may need to run `uvicorn app.main:app --reload`)*

### 2. Frontend Setup
Open a separate terminal and navigate to the `frontend` directory:
```bash
cd frontend
npm install
npm run dev
```

Your backend will be running at `http://localhost:8005` and the frontend at the Vite port (typically `http://localhost:5173`).
