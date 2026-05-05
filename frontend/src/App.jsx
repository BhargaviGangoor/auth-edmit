import React, { useState, useEffect, useRef } from 'react';
import { Mail, ShieldCheck, ArrowRight, CheckCircle2, AlertCircle, ArrowLeft, LogOut, User as UserIcon, Lock, GraduationCap, Users, Fingerprint } from 'lucide-react';
import confetti from 'canvas-confetti';
import { auth, googleProvider } from './firebaseConfig';
import { 
  signInWithPopup, 
  onAuthStateChanged,
  signOut
} from 'firebase/auth';

const API_BASE = 'http://localhost:8005';

// Helper for WebAuthn binary data
const bufferToBase64 = (buffer) => btoa(String.fromCharCode(...new Uint8Array(buffer)))
  .replace(/\+/g, "-")
  .replace(/\//g, "_")
  .replace(/=/g, "");

const base64ToBuffer = (base64) => {
  const binary = atob(base64.replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(binary, c => c.charCodeAt(0));
};

// Global Turnstile Callback
window.onTurnstileSuccess = (token) => {
  console.log("Turnstile global verified:", token.substring(0, 10) + "...");
  window.dispatchEvent(new CustomEvent('captcha-verified', { detail: token }));
};

window.onTurnstileError = (code) => {
  console.error("Turnstile error:", code);
  window.dispatchEvent(new CustomEvent('captcha-error', { detail: code }));
};

window.onTurnstileExpired = () => {
  console.warn("Turnstile expired");
  window.dispatchEvent(new CustomEvent('captcha-expired'));
};

function App() {
  const [step, setStep] = useState(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        const parsed = JSON.parse(savedUser);
        return parsed.onboarded ? 'success' : 'onboarding';
      } catch (e) {
        return 'email';
      }
    }
    return 'email';
  });
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [user, setUser] = useState(null);
  const [isNewUser, setIsNewUser] = useState(false);
  const [captchaToken, setCaptchaToken] = useState('');
  const [onboardingData, setOnboardingData] = useState({ name: '', role: 'student' });
  const [hasPasskey, setHasPasskey] = useState(false);
  
  const turnstileRef = useRef(null);
  const passkeyRequestPendingRef = useRef(false);
  const passkeyAbortControllerRef = useRef(null);

  // 1. Handle Magic Link Callback on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (token) {
      handleMagicLinkAuth(token);
    }

    // Load user and email from localStorage if available
    const savedUser = localStorage.getItem('user');
    const savedEmail = localStorage.getItem('email');
    if (savedEmail) setEmail(savedEmail);
    
    if (savedUser) {
      const parsed = JSON.parse(savedUser);
      setUser(parsed);
      setHasPasskey(parsed.has_passkey || false);
      if (!parsed.onboarded) setStep('onboarding');
      else setStep('success');
    }

    // Listen for global captcha event
    const handleCaptcha = (e) => {
      console.log("App received captcha token");
      setCaptchaToken(e.detail);
    };
    window.addEventListener('captcha-verified', handleCaptcha);
    window.addEventListener('captcha-error', (e) => setError(`CAPTCHA Error: ${e.detail}. Check if you added 'localhost' to Cloudflare.`));
    window.addEventListener('captcha-expired', () => {
      setCaptchaToken('');
      setError('CAPTCHA expired. Please verify again.');
    });

    return () => {
      window.removeEventListener('captcha-verified', handleCaptcha);
    };
  }, []);

  // Conditional UI (Passkey Autofill)
  useEffect(() => {
    if (step === 'email') {
      const triggerConditionalUI = async () => {
        if (window.PublicKeyCredential && 
            PublicKeyCredential.isConditionalMediationAvailable) {
          const available = await PublicKeyCredential.isConditionalMediationAvailable();
          if (available) {
            console.log("Conditional UI available, starting...");
            handlePasskeyLogin(true);
          }
        }
      };
      triggerConditionalUI();
    }
  }, [step]);

  // Auto-redirect on success
  useEffect(() => {
    if (step === 'success' && !loading) {
      const timer = setTimeout(() => {
        console.log("Auto-redirecting to edmitted.org...");
        window.location.href = "https://edmitted.org";
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [step, loading]);

  const handleMagicLinkAuth = async (token) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/callback?token=${token}`);
      const data = await res.json();
      if (res.ok) {
        handleAuthSuccess(data);
        window.history.replaceState({}, document.title, "/");
      } else {
        setError(data.detail || 'Magic link failed.');
      }
    } catch (err) {
      setError('Connection error.');
    } finally {
      setLoading(false);
    }
  };

  const handleAuthSuccess = (data) => {
    const { user, access_token, refresh_token, is_new_user } = data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('email', user.email);
    
    setUser(user);
    setEmail(user.email);
    setIsNewUser(is_new_user);
    setHasPasskey(user.has_passkey || false);
    
    if (is_new_user || !user.onboarded) {
      setStep('onboarding');
    } else {
      setStep('success');
      confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 } });
    }
  };

  const handleEmailSubmitted = async (e) => {
    e.preventDefault();
    
    // In development, we allow skipping the CAPTCHA if it's stuck
    if (!captchaToken) {
      console.warn("CAPTCHA not verified. Proceeding anyway because we are in development.");
    }
    
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/otp/send-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, captcha_token: captchaToken }),
      });
      const data = await res.json();
      if (res.ok) {
        setStep('otp');
      } else {
        setError(data.detail || 'Failed to send login link.');
      }
    } catch (err) {
      setError('Backend unreachable.');
    } finally {
      setLoading(false);
    }
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
      if (res.ok) {
        handleAuthSuccess(data);
      } else {
        setError(data.detail || 'Invalid code.');
      }
    } catch (err) {
      setError('Verification failed.');
    } finally {
      setLoading(false);
    }
  };

  // Passkey Registration
  const handleRegisterPasskey = async () => {
    let userEmail = user?.email || email || localStorage.getItem('email');
    
    if (!userEmail) {
      userEmail = prompt("Please confirm your email address to enable Passkey:");
    }
    
    if (!userEmail) return; // User cancelled prompt

    setLoading(true);
    setError('');
    try {
      const payload = { email: userEmail };
      console.log("Submitting passkey register payload:", payload);
      
      const startRes = await fetch(`${API_BASE}/passkey/register/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const options = await startRes.json();
      
      if (!options.publicKey) {
        console.error("Backend returned invalid options:", options);
        throw new Error(options.detail || "Failed to start registration");
      }

      // Convert options for navigator.credentials.create
      options.publicKey.challenge = base64ToBuffer(options.publicKey.challenge);
      options.publicKey.user.id = base64ToBuffer(options.publicKey.user.id);
      
      const credential = await navigator.credentials.create(options);
      
      // Convert credential for backend
      const response = {
        id: credential.id,
        rawId: bufferToBase64(credential.rawId),
        type: credential.type,
        response: {
          attestationObject: bufferToBase64(credential.response.attestationObject),
          clientDataJSON: bufferToBase64(credential.response.clientDataJSON),
        },
      };

      const finishRes = await fetch(`${API_BASE}/passkey/register/finish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: userEmail, response }),
      });
      
      if (finishRes.ok) {
        alert("Passkey enabled successfully!");
        setHasPasskey(true);
      } else {
        const errorData = await finishRes.json();
        setError(errorData.detail || "Registration failed");
      }
    } catch (err) {
      console.error(err);
      setError("Passkey setup failed.");
    } finally {
      setLoading(false);
    }
  };

  // Passkey Login
  const handlePasskeyLogin = async (isConditional = false) => {
    // If user manually clicks the button, abort the background conditional UI request
    if (!isConditional && passkeyAbortControllerRef.current) {
      console.log("Aborting conditional passkey request for manual request...");
      passkeyAbortControllerRef.current.abort();
      passkeyAbortControllerRef.current = null;
      passkeyRequestPendingRef.current = false;
    }

    if (passkeyRequestPendingRef.current) {
      console.log("Passkey request already pending, skipping...");
      return;
    }

    if (!isConditional) {
      setLoading(true);
      setError('');
    }
    
    const abortController = new AbortController();
    if (isConditional) {
      passkeyAbortControllerRef.current = abortController;
    }

    passkeyRequestPendingRef.current = true;
    try {
      const startRes = await fetch(`${API_BASE}/passkey/login/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email || null }),
      });
      const options = await startRes.json();

      if (!startRes.ok) {
        console.error("Passkey login start failed:", options);
        if (!isConditional) {
          setError(typeof options.detail === 'string' ? options.detail : "Validation error on server");
        }
        return;
      }
      
      // Convert challenge
      options.publicKey.challenge = base64ToBuffer(options.publicKey.challenge);
      if (options.publicKey.allowCredentials) {
        options.publicKey.allowCredentials.forEach(c => c.id = base64ToBuffer(c.id));
      }

      // Add mediation for autofill support
      if (isConditional) {
        options.mediation = 'conditional';
      }
      
      options.signal = abortController.signal;
      
      console.log("Requesting credential with options:", options);
      const assertion = await navigator.credentials.get(options);
      
      if (!assertion) return;

      const response = {
        id: assertion.id,
        rawId: bufferToBase64(assertion.rawId),
        type: assertion.type,
        response: {
          authenticatorData: bufferToBase64(assertion.response.authenticatorData),
          clientDataJSON: bufferToBase64(assertion.response.clientDataJSON),
          signature: bufferToBase64(assertion.response.signature),
          userHandle: assertion.response.userHandle ? bufferToBase64(assertion.response.userHandle) : null,
        },
      };

      const finishRes = await fetch(`${API_BASE}/passkey/login/finish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          email: email || null, 
          challengeId: options.challengeId,
          response 
        }),
      });
      
      const data = await finishRes.json();
      if (finishRes.ok) {
        handleAuthSuccess(data);
      } else {
        if (!isConditional) {
          setError(data.detail || "Passkey login failed");
          // If passkey not found, help them sign in with email
          if (data.detail === "Passkey not recognized" || data.detail === "Passkey mismatch") {
            setTimeout(() => setStep('email'), 2000);
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log("Passkey request aborted.");
        return;
      }
      console.error("Passkey login error:", err);
      if (!isConditional) {
        setError("Passkey login failed. If you don't have an account, please sign in with email first.");
        // Redirect to email step after a short delay so they can see the error
        setTimeout(() => setStep('email'), 3000);
      }
    } finally {
      passkeyRequestPendingRef.current = false;
      if (isConditional) passkeyAbortControllerRef.current = null;
      if (!isConditional) setLoading(false);
    }
  };

  const handleOnboardingSubmit = async (e) => {
    e.preventDefault();
    const userEmail = user?.email || email || localStorage.getItem('email');
    if (!userEmail) {
      setError("Please verify your email address below to continue.");
      return;
    }
    const payload = { ...onboardingData, email: userEmail };
    console.log("Submitting onboarding payload:", payload);
    
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/onboarding`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const updatedUser = { ...user, ...onboardingData, onboarded: true };
        setUser(updatedUser);
        localStorage.setItem('user', JSON.stringify(updatedUser));
        setStep('success');
        confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 } });
      } else {
        setError('Failed to save onboarding info.');
      }
    } catch (err) {
      setError('Connection error.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setUser(null);
    setStep('email');
    setEmail('');
    setOtp('');
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const idToken = await result.user.getIdToken();
      const res = await fetch(`${API_BASE}/auth/verify-firebase-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: idToken }),
      });
      const data = await res.json();
      if (res.ok) {
        handleAuthSuccess(data);
      } else {
        setError(data.detail || 'Google Sign-In failed.');
      }
    } catch (err) {
      setError('Google Sign-In failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="card">
        {step === 'email' && (
          <div className="auth-step-container">
            <button type="button" className="btn btn-passkey" onClick={() => handlePasskeyLogin()} disabled={loading} style={{ marginBottom: '1.5rem' }}>
              <Fingerprint size={18} /> Sign in with Passkey
            </button>

            <form onSubmit={handleEmailSubmitted}>
              <div className="header">
                <h1>Welcome to Edmitted</h1>
                <p>Sign in or create your account instantly</p>
              </div>
              <div className="input-group">
                <label className="input-label">Email Address</label>
                <div className="input-wrapper">
                  <input
                    type="email"
                    name="username"
                    className="input-field"
                    placeholder="name@edmitted.org"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="username webauthn"
                    required
                  />
                </div>
              </div>
              
              <div 
                className="cf-turnstile" 
                data-sitekey="0x4AAAAAADJf0jX9daW5O7pM" 
                data-callback="onTurnstileSuccess"
                data-error-callback="onTurnstileError"
                data-expired-callback="onTurnstileExpired"
                style={{ marginBottom: '1rem' }}
              ></div>

              <button type="submit" className="btn" disabled={loading}>
                {loading ? <div className="loading-spinner" /> : <><ShieldCheck size={18} /> Continue with Email</>}
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
                <h1>Check your email</h1>
                <p>We've sent a magic link and a 6-digit code to {email}</p>
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
              </div>
              <button type="submit" className="btn" disabled={loading || otp.length < 6}>
                {loading ? <div className="loading-spinner" /> : 'Verify Code'}
              </button>
              <p className="hint">Tip: Clicking the link in your email is faster!</p>
            </form>
            {error && <div className="error-message" style={{ marginTop: '1rem' }}><AlertCircle size={14} /> {error}</div>}
          </div>
        )}

        {step === 'onboarding' && (
          <div className="auth-step-container">
            <form onSubmit={handleOnboardingSubmit}>
              <div className="header">
                <h1>Last step!</h1>
                <p>Tell us a bit about yourself</p>
              </div>
              <div className="input-group">
                <label className="input-label">Full Name</label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="John Doe"
                  value={onboardingData.name}
                  onChange={(e) => setOnboardingData({...onboardingData, name: e.target.value})}
                  required
                />
              </div>

              {!email && !user?.email && (
                <div className="input-group">
                  <label className="input-label">Verify Email</label>
                  <input
                    type="email"
                    className="input-field"
                    placeholder="name@edmitted.org"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              )}
              <div className="input-group">
                <label className="input-label">I am a...</label>
                <div className="role-selector">
                  <div className={`role-option ${onboardingData.role === 'student' ? 'active' : ''}`} onClick={() => setOnboardingData({...onboardingData, role: 'student'})}>
                    <GraduationCap size={24} />
                    <span>Student</span>
                  </div>
                  <div className={`role-option ${onboardingData.role === 'mentor' ? 'active' : ''}`} onClick={() => setOnboardingData({...onboardingData, role: 'mentor'})}>
                    <Users size={24} />
                    <span>Mentor</span>
                  </div>
                </div>
              </div>
              <button type="submit" className="btn" disabled={loading}>
                {loading ? <div className="loading-spinner" /> : 'Start Exploring'}
              </button>
            </form>
          </div>
        )}

        {step === 'success' && (
          <div className="success-state">
            <div className="user-profile">
              <div className="profile-placeholder"><UserIcon size={32} /></div>
              <div className="status-badge"><CheckCircle2 size={16} /></div>
            </div>
            <div className="header">
              <h1>Welcome back, {user?.name}!</h1>
              <p>You are logged in as a <strong>{user?.role || 'user'}</strong>.</p>
            </div>
            
            <div className="redirect-notice" style={{ margin: '1rem 0', padding: '10px', background: '#f0fdf4', borderRadius: '8px', color: '#16a34a', fontSize: '0.9rem' }}>
              <CheckCircle2 size={16} style={{ verticalAlign: 'middle', marginRight: '5px' }} /> 
              Authentication Complete. Redirecting to Edmitted...
            </div>

            {!hasPasskey && (
              <button className="btn btn-passkey" onClick={handleRegisterPasskey} disabled={loading} style={{ marginBottom: '1rem' }}>
                <Fingerprint size={18} /> Enable Passkey Login
              </button>
            )}

            <button className="btn" onClick={() => window.location.href = "https://edmitted.org"} style={{ marginBottom: '1rem', background: '#6366f1' }}>
              <ArrowRight size={18} /> Enter Dashboard
            </button>

            <button className="btn btn-secondary" onClick={handleLogout}>
              <LogOut size={18} /> Sign Out
            </button>
            {error && <div className="error-message" style={{ marginTop: '1rem' }}><AlertCircle size={14} /> {error}</div>}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
