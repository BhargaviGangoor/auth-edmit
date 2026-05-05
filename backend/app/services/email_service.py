import os
import smtplib
import ssl
from email.message import EmailMessage

class EmailService:
    def __init__(self):
        self.sender_email = os.getenv("EMAIL_USER")
        self.sender_password = os.getenv("EMAIL_PASS")
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_otp_email(self, to_email: str, otp: str, magic_token: str = None) -> bool:
        """Send a 6-digit OTP and optional magic link to the user's email."""
        if not self.sender_email or not self.sender_password:
            print("SMTP Error: Credentials not configured.")
            return False

        try:
            msg = EmailMessage()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = 'Your OTP Code'
            
            body = f"Your one-time password is: {otp}\n\n"
            if magic_token:
                # Assuming frontend is on port 5173 for dev
                frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
                magic_link = f"{frontend_url}/auth/callback?token={magic_token}"
                body += f"Alternatively, click this link to login instantly:\n{magic_link}\n\n"
            
            body += "This code and link will expire in 5 minutes.\nIf you didn't request this, you can safely ignore this email."
            msg.set_content(body)

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            print(f"OTP Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"SMTP Error: {str(e)}")
            return False

# Create a singleton instance
email_service = EmailService()
