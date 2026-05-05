import os
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity
from fido2.utils import websafe_encode, websafe_decode
from fido2.webauthn import AuthenticatorSelectionCriteria, UserVerificationRequirement

RP_ID = os.getenv("RP_ID", "localhost")
RP_NAME = "Edmitted Auth"

class PasskeyService:
    def __init__(self):
        print(f"Initializing FIDO2 Server with RP_ID: {RP_ID}")
        self.rp = PublicKeyCredentialRpEntity(id=RP_ID, name=RP_NAME)
        self.server = Fido2Server(self.rp)

    def start_registration(self, user_email: str):
        """Begin WebAuthn registration process."""
        # Simple user info for FIDO2
        user_info = {
            "id": user_email.encode(),
            "name": user_email,
            "displayName": user_email.split('@')[0]
        }
        
        # Options for creating a new credential
        # Updated to be compatible with older fido2 versions
        registration_data, state = self.server.register_begin(
            user_info,
            credentials=[],
            authenticator_attachment="platform" # Use "platform" for biometric (TouchID/FaceID/Windows Hello)
        )
        
        # state must be stored to verify the finish step
        # For MVP, we'll return it as a base64 string to be stored in the frontend 
        # (or just use a session/cache if we had one set up)
        return registration_data, state

    def finish_registration(self, state, response):
        """Complete WebAuthn registration process."""
        auth_data = self.server.register_complete(state, response)
        return auth_data

    def start_authentication(self, credentials):
        """Begin WebAuthn authentication process."""
        # credentials is a list of registered keys for the user
        auth_data, state = self.server.authenticate_begin(credentials)
        return auth_data, state

    def finish_authentication(self, state, credentials, response):
        """Complete WebAuthn authentication process."""
        # credentials is the list of keys we started with
        # response is what we got back from the browser
        auth_data = self.server.authenticate_complete(state, credentials, response)
        return auth_data

# Singleton instance
passkey_service = PasskeyService()
