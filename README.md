# Edmitted Unified Authentication System

A premium, passwordless authentication platform featuring **Email OTP**, **Google OAuth**, and **WebAuthn (Passkeys)** biometrics.

## 🚀 The User Journeys

### 1. The New User (Onboarding)
- **Entry**: User enters their email address OR clicks **"Continue with Google"**.
- **Bot Protection**: Cloudflare Turnstile verifies the user silently.
- **Verification (Email)**: User receives a 6-digit OTP in their inbox to verify their identity.
- **Verification (Google)**: User selects their Google account; the system automatically merges or creates their Edmitted account.
- **Identity**: Upon first login, the user completes a brief onboarding (Name & Role).
- **Security Upgrade**: User is prompted to "Enable Passkey" to register their fingerprint/FaceID for future visits.
- **Destination**: Automatic redirection to `edmitted.org`.

### 2. The Returning User (Fast-Track)
- **Biometric Entry**: User clicks "Sign in with Passkey."
- **Instant Auth**: User touches their fingerprint sensor; the backend verifies the device signature.
- **Zero Friction**: No email, no codes, no passwords. Instant redirection to the dashboard.

---

## 🛠️ Tech Stack & Core Libraries

### Backend (FastAPI + Python)
- **`fastapi`**: Modern web framework with Pydantic validation.
- **`fido2`**: The core engine for WebAuthn/Passkey handshakes.
- **`firebase-admin`**: Handles secure verification of Google OAuth tokens.
- **`python-jose`**: Handles stateless JWT session management (`access_token` & `refresh_token`).
- **`sqlalchemy`**: Database ORM (SQLite for local dev, PostgreSQL ready).
- **`slowapi`**: Implements rate-limiting on sensitive OTP endpoints.
- **`cbor2`**: Used for encoding complex security keys into database-friendly formats.

### Frontend (React + Vite)
- **`firebase`**: Managed Google Authentication popup and tokens.
- **`lucide-react`**: Beautiful, consistent iconography.
- **`canvas-confetti`**: For that premium "Success" celebration.
- **`Cloudflare Turnstile`**: Privacy-first, non-intrusive CAPTCHA.

---

## 🧠 Technical Logic (Handover Notes)

### 1. Identity Merging (Email & GAuth)
The system uses **Email Address** as the primary unique identifier. Whether a user authenticates via Google, OTP, or Passkey, they are always linked to the same record in the `users` table. This prevents duplicate accounts if a user switches login methods.

### 2. Passkey Serialization (Critical)
The `fido2` library uses raw bytes and complex objects that don't serialize to JSON by default.
- **Start Step**: We use a custom `json_serializable` helper in `passkey.py` to convert bytes to base64 before sending to the frontend.
- **Storage**: Public keys are stored as **CBOR-encoded bytes** in the `passkeys` table to preserve their cryptographic structure.

### 3. JWT Strategy
- **Access Tokens**: Short-lived (15 mins) for security.
- **Refresh Tokens**: Long-lived, stored in `localStorage`, used to silently get new access tokens without logging the user out.

### 4. Developer Safety
- **Global Error Logger**: Located in `main.py`, it catches all backend crashes and prints full tracebacks to the terminal while preventing CORS from hiding the error from the developer.
- **Dev-Mode CAPTCHA**: Turnstile is optional on `localhost` to prevent blocking development during network outages.

---

## 🏃 Running the Project

1. **Backend (Port 8005)**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8005
   ```
2. **Frontend (Port 5173)**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Environment**: Ensure `.env` in the `backend` folder contains your keys. The frontend is pre-configured to look for the backend on port 8005.
