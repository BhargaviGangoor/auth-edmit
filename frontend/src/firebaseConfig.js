import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyC9tQMBM69uYyQqrIZPj5HeoH5UgSc5SGI",
  authDomain: "otp-auth-project-3b7b0.firebaseapp.com",
  projectId: "otp-auth-project-3b7b0",
  storageBucket: "otp-auth-project-3b7b0.firebasestorage.app",
  messagingSenderId: "425241427281",
  appId: "1:425241427281:web:2445518b5b275b6d94a770",
  measurementId: "G-G9CEVNZ2CG"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
