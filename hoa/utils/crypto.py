"""
Cryptographic utilities for password hashing and token management.
"""

import hashlib
import secrets
from typing import Optional

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    
    Note:
        Bcrypt has a maximum password length of 72 bytes.
        Passwords longer than this will be truncated.
    """
    # Bcrypt has a 72-byte limit
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def hash_token(token: str) -> str:
    """
    Hash a token using SHA-256.
    
    Args:
        token: Plain text token
    
    Returns:
        Hashed token (hex encoded)
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(plain_token: str, hashed_token: str) -> bool:
    """
    Verify a token against its hash.
    
    Args:
        plain_token: Plain text token to verify
        hashed_token: Hashed token to compare against
    
    Returns:
        True if token matches, False otherwise
    """
    return secrets.compare_digest(hash_token(plain_token), hashed_token)


def generate_session_token() -> str:
    """
    Generate a secure random session token.
    
    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(32)


def generate_key_id(length: int = 16) -> str:
    """
    Generate a random key ID for JWT keys.
    
    Args:
        length: Length of the key ID in bytes
    
    Returns:
        Hex-encoded key ID
    """
    return secrets.token_hex(length)

