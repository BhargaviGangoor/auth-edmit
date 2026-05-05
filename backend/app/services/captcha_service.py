import os
import requests

TURNSTILE_SECRET = os.getenv("TURNSTILE_SECRET")

class CaptchaService:
    @staticmethod
    def verify_turnstile_token(token: str) -> bool:
        """Verify Cloudflare Turnstile token."""
        # Allow skipping in development if token is missing
        if not token or not TURNSTILE_SECRET:
            if os.getenv("APP_MODE") != "production":
                print("CAPTCHA skipped in development mode.")
                return True
            return False

        try:
            print(f"Verifying token: {token[:10]}...")
            response = requests.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": TURNSTILE_SECRET,
                    "response": token,
                }
            )
            result = response.json()
            print(f"Cloudflare response: {result}")
            return result.get("success", False)
        except Exception as e:
            print(f"Turnstile verification error: {e}")
            return False
