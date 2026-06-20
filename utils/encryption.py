from cryptography.fernet import Fernet, InvalidToken
import os

def get_fernet():
    key = os.getenv("ENCRYPTION_KEY")
    if not key or key.startswith("<"):
        raise RuntimeError("ENCRYPTION_KEY not set in environment or left as placeholder")
    return Fernet(key.encode() if isinstance(key, str) else key)

def encrypt_value(plaintext: str) -> str:
    f = get_fernet()
    return f.encrypt(plaintext.encode()).decode()

def decrypt_value(token_str: str) -> str:
    f = get_fernet()
    try:
        return f.decrypt(token_str.encode()).decode()
    except InvalidToken:
        raise RuntimeError("Cannot decrypt value: invalid encryption key or corrupted token")
