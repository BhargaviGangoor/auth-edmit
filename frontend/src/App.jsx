import React, { useState, useEffect } from 'react';
import { Mail, ShieldCheck, ArrowRight, CheckCircle2, AlertCircle, ArrowLeft, LogOut, User as UserIcon, Lock } from 'lucide-react';
import confetti from 'canvas-confetti';
import { auth, googleProvider } from './firebaseConfig';
import { 
  signInWithPopup, 
  onAuthStateChanged,
  signOut
} from 'firebase/auth';

const API_BASE = 'http://127.0.0.1:8005';

function App() {
  const [step, setStep] = useState('email'); // email, otp, success
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [user, setUser] = useState(null);
  const [debugOtp, setDebugOtp] = useState('');

  // 1. Handle Persistence on mount
  useEffect(() => {
    // Handle session persistence
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser && !user) {
        const idToken = await firebaseUser.getIdToken();
        try {
          const res = await fetch(`${API_BASE}/verify-firebase-token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: idToken }),
          });
          const data = await res.json();
          if (res.ok) {
            setUser(data.user);
            setStep('success');
          }
        } catch (e) {
          console.error("Session persistence failed");
        }
      }
    });
    return () => unsubscribe();
  }, [user]);

  // 2. Auth Success Handler
  const handleAuthSuccess = (userData) => {
    setUser(userData);
    setStep('success');
    confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 } });
    setTimeout(() => { window.location.href = 'https://edmitted.org'; }, 2500);
  };

  // 3. Backend Verifiers
  const verifyFirebaseWithBackend = async (idToken) => {
    try {
      const res = await fetch(`${API_BASE}/verify-firebase-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: idToken }),
      });
      const data = await res.json();
      if (res.ok) handleAuthSuccess(data.user);
      else setError(data.detail || 'Verification failed.');
    } catch (err) { setError('Backend connection error.'); }
    finally { setLoading(false); }
  };

  // 4. Action Handlers
  const handleEmailSubmitted = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/otp/send-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (res.ok) {
        setStep('otp');
        if (data.otp_test) setDebugOtp(data.otp_test);
      } else setError(data.detail || 'Failed to send OTP.');
    } catch (err) { setError('Backend unreachable.'); }
    finally { setLoading(false); }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/otp/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp }),
      });
      const data = await res.json();
      if (res.ok) handleAuthSuccess(data.user);
      else setError(data.detail || 'Invalid code.');
    } catch (err) { setError('Verification failed.'); }
    finally { setLoading(false); }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const idToken = await result.user.getIdToken();
      await verifyFirebaseWithBackend(idToken);
    } catch (err) { setError('Google Sign-In failed.'); }
    finally { setLoading(false); }
  };

  const handleLogout = async () => {
    await signOut(auth);
    setUser(null);
    setStep('email');
    setEmail('');
    setOtp('');
  };

  return (
    <div className="container">
      <div className="card">
        {step === 'email' && (
          <div className="auth-step-container">
            <form onSubmit={handleEmailSubmitted}>
              <div className="header">
                <h1>Welcome</h1>
                <p>Enter your email to get started</p>
              </div>
              <div className="input-group">
                <label className="input-label">Email Address</label>
                <div className="input-wrapper">
                  <input
                    type="email"
                    className="input-field"
                    placeholder="name@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>
              <button type="submit" className="btn" disabled={loading}>
                {loading ? <div className="loading-spinner" /> : <><ShieldCheck size={18} /> Continue with Code</>}
              </button>
            </form>
            {error && <div className="error-message" style={{ marginTop: '1rem' }}><AlertCircle size={14} /> {error}</div>}
            
            <div className="divider"><span>or</span></div>
            <button type="button" className="btn btn-secondary" onClick={handleGoogleLogin} disabled={loading}>
              <svg width="18" height="18" viewBox="0 0 18 18" style={{ marginRight: '10px' }}>
                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.184L12.048 13.558c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
                <path d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707s.102-1.167.282-1.707V4.961H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.039l3.007-2.332z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.441 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.483 0 2.443 2.043.957 4.961L3.964 7.293C4.672 5.166 6.656 3.58 9 3.58z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>
          </div>
        )}

        {step === 'otp' && (
          <div className="auth-step-container">
            <form onSubmit={handleVerifyOtp}>
              <button type="button" className="back-btn" onClick={() => setStep('email')}><ArrowLeft size={14} /> Back</button>
              <div className="header">
                <h1>Verify Code</h1>
                <p>Enter the 6-digit code sent to {email}</p>
              </div>
              <div className="input-group">
                <input
                  type="text"
                  className="input-field"
                  placeholder="000000"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  style={{ textAlign: 'center', fontSize: '1.5rem', letterSpacing: '0.5rem' }}
                  required
                />
                {debugOtp && <div className="debug-hint" style={{ fontSize: '0.8rem', color: 'var(--primary)', marginTop: '0.5rem' }}>Debug Code: {debugOtp}</div>}
              </div>
              {error && <div className="error-message" style={{ marginTop: '1rem', marginBottom: '1rem' }}><AlertCircle size={14} /> {error}</div>}
              <button type="submit" className="btn" disabled={loading || otp.length < 6}>
                {loading ? <div className="loading-spinner" /> : 'Verify & Sign In'}
              </button>
            </form>
          </div>
        )}

        {step === 'success' && (
          <div className="success-state">
            <div className="user-profile">
              {user?.picture ? <img src={user.picture} alt="Profile" className="profile-img" /> : <div className="profile-placeholder"><UserIcon size={32} /></div>}
              <div className="status-badge"><CheckCircle2 size={16} /></div>
            </div>
            <div className="header">
              <h1>Welcome back!</h1>
              <p>Redirecting you to <strong>edmitted.org</strong>...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
