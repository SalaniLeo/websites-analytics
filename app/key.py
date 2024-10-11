import os
import base64
import hashlib
from cryptography.fernet import Fernet

PROTECTED_ENDPOINTS = [
    '/api/user/entered'
]

def generate_key(key_str):
    key_bytes = hashlib.sha256(key_str.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)

def encrypt_string(key, message):
    fernet = Fernet(key)
    encrypted_message = fernet.encrypt(message.encode())
    return encrypted_message

def decrypt_string(key, encrypted_message):
    fernet = Fernet(key)
    try:
        decrypted_message = fernet.decrypt(encrypted_message).decode()
        return decrypted_message
    except Exception:
        return None