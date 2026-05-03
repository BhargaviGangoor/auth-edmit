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

    def send_otp_email(self, to_email: str, otp: str) -> bool:
        """Send a 6-digit OTP to the user's email using Gmail SMTP."""
        if not self.sender_email or not self.sender_password:
            print("SMTP Error: Credentials not configured.")
            return False

        try:
            msg = EmailMessage()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = 'Your OTP Code'
            
            body = f"Your one-time password is: {otp}\nThis code will expire in 5 minutes.\nIf you didn't request this code, you can safely ignore this email."
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
