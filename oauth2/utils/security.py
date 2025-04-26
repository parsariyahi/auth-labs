from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import secrets
import hashlib
import base64
from ..config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRATION

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + TOKEN_EXPIRATION["access_token"]
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_token(length=32):
    return secrets.token_urlsafe(length)

def generate_code_challenge(code_verifier):
    """Generate PKCE code challenge from verifier"""
    code_verifier_bytes = code_verifier.encode('ascii')
    m = hashlib.sha256()
    m.update(code_verifier_bytes)
    code_challenge_bytes = m.digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge_bytes).decode('ascii')
    return code_challenge.rstrip('=')

def verify_code_challenge(code_verifier, code_challenge):
    """Verify PKCE code challenge"""
    expected_challenge = generate_code_challenge(code_verifier)
    return expected_challenge == code_challenge 