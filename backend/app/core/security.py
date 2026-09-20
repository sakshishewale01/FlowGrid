"""
Security & Cryptographic Utilities
==================================
Handles secure password hashing using pwdlib (Argon2) and JWT token generation/validation.

Why Argon2?
-----------
Argon2 is the winner of the Password Hashing Competition (PHC) and is recommended
by OWASP and IETF for state-of-the-art password storage resistance against GPU-based attacks.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# ------------------------------------------------------------------------------
# 1. Password Hashing (Argon2 via pwdlib)
# ------------------------------------------------------------------------------
# Recommended defaults configure Argon2id with robust memory and time cost parameters
password_hasher = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    """
    Hashes a plain-text password using the Argon2id algorithm.
    """
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies that a plain-text candidate password matches the stored Argon2 hash.
    """
    return password_hasher.verify(plain_password, hashed_password)


# ------------------------------------------------------------------------------
# 2. JSON Web Token (JWT) Handling
# ------------------------------------------------------------------------------
def create_access_token(
    subject: Union[str, int],
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generates a signed JWT access token containing subject (user_id), role, and expiration.

    Args:
        subject: The unique user identifier (e.g. user ID).
        role: The user's role (ADMIN, MANAGER, DRIVER, VIEWER).
        expires_delta: Optional custom duration; defaults to settings.access_token_expire_minutes.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": now,
        "exp": expire,
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a signed JWT access token.
    Enforces expiration, subject identity claim, and signing signature.

    Args:
        token: The encoded JWT string.

    Returns:
        The payload dict if valid, or None if signature is invalid, expired, or claims missing.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub", "iat"], "verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None
