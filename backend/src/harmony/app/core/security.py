from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
import hashlib
import secrets

password_hash = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def create_access_token(data: dict, expires_delta: timedelta, secret_key: str, algorithm: str) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt

def decode_access_token(token: str, secret_key: str, algorithm: str) -> dict:
    payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    return payload
    
def hash_refresh_token(plain_token: str) -> str:
    return hashlib.sha256(plain_token.encode()).hexdigest()

def generate_refresh_token() -> tuple[str, str]:
    plain_token = secrets.token_urlsafe(64)
    token_hash = hash_refresh_token(plain_token)
    return plain_token, token_hash