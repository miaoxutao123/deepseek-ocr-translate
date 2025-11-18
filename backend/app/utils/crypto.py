from cryptography.fernet import Fernet
from passlib.context import CryptContext
import base64
import hashlib

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


class EncryptionManager:
    """Manage API key encryption/decryption using user-specific keys"""

    @staticmethod
    def _get_user_key(user_id: int, secret_key: str) -> bytes:
        """Generate a user-specific encryption key"""
        combined = f"{user_id}:{secret_key}".encode()
        key_hash = hashlib.sha256(combined).digest()
        return base64.urlsafe_b64encode(key_hash)

    @staticmethod
    def encrypt_api_key(api_key: str, user_id: int, secret_key: str) -> str:
        """Encrypt an API key for a specific user"""
        if not api_key:
            return ""
        user_key = EncryptionManager._get_user_key(user_id, secret_key)
        f = Fernet(user_key)
        encrypted = f.encrypt(api_key.encode())
        return encrypted.decode()

    @staticmethod
    def decrypt_api_key(encrypted_key: str, user_id: int, secret_key: str) -> str:
        """Decrypt an API key for a specific user"""
        if not encrypted_key:
            return ""
        user_key = EncryptionManager._get_user_key(user_id, secret_key)
        f = Fernet(user_key)
        decrypted = f.decrypt(encrypted_key.encode())
        return decrypted.decode()
