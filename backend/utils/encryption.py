"""
Encryption utilities for sensitive data
"""
from cryptography.fernet import Fernet
import base64
import os


def get_encryption_key():
    """Get or generate encryption key"""
    key = os.environ.get('ENCRYPTION_KEY', 'default-encryption-key-change-in-production')
    # Ensure key is 32 bytes for Fernet
    key_bytes = key.encode()[:32].ljust(32, b'0')
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_password(password):
    """Encrypt password"""
    if not password:
        return ''
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password):
    """Decrypt password"""
    if not encrypted_password:
        return ''
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return ''
