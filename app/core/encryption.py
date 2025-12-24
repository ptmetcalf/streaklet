from cryptography.fernet import Fernet
from app.core.config import settings
import base64


def _get_fernet() -> Fernet:
    """Get Fernet instance using the app secret key."""
    if not settings.app_secret_key:
        raise ValueError("APP_SECRET_KEY environment variable must be set for token encryption")

    # Ensure key is properly formatted (32 bytes, base64-encoded)
    key = settings.app_secret_key.encode()
    if len(key) != 44:  # Base64-encoded 32 bytes = 44 characters
        # If not properly formatted, derive a key from the provided secret
        # This is for convenience - in production, use Fernet.generate_key()
        from hashlib import sha256
        key = base64.urlsafe_b64encode(sha256(key).digest())

    return Fernet(key)


def encrypt_token(token: str) -> str:
    """Encrypt a token using Fernet symmetric encryption."""
    fernet = _get_fernet()
    encrypted = fernet.encrypt(token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token using Fernet symmetric encryption."""
    fernet = _get_fernet()
    decrypted = fernet.decrypt(encrypted_token.encode())
    return decrypted.decode()
