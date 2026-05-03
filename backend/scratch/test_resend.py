import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

try:
    # Just list domains to verify key
    domains = resend.Domains.list()
    print("Resend API Key is VALID.")
    print(f"Domains found: {len(domains['data'])}")
except Exception as e:
    print(f"Resend API Key check FAILED: {e}")
