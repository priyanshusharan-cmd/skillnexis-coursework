"""Password hashing (scrypt, standard library) and JWT access tokens (HS256)."""
import base64
import hashlib
import hmac
import os
import time

import jwt

_N, _R, _P = 2**14, 8, 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_b64, digest_b64 = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    digest = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64), n=_N, r=_R, p=_P, dklen=32)
    return hmac.compare_digest(digest, base64.b64decode(digest_b64))


def create_token(user_id: int, secret: str, ttl_seconds: int = 3600) -> str:
    now = int(time.time())
    return jwt.encode({"sub": str(user_id), "iat": now, "exp": now + ttl_seconds}, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> int:
    """Return the user id, or raise jwt.InvalidTokenError (expired, tampered, wrong alg...)."""
    payload = jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["sub", "exp", "iat"]})
    return int(payload["sub"])
