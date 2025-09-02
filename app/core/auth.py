# src/core/auth.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from dotenv import load_dotenv
import requests
import os

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
ALGORITHMS = ["RS256"]
JWKS_URL = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"

security = HTTPBearer()


def get_jwks():
    resp = requests.get(JWKS_URL)
    if resp.status_code != 200:
        raise Exception("Failed to fetch JWKS")
    return resp.json()


def get_rsa_key(token: str):
    jwks = get_jwks()
    unverified_header = jwt.get_unverified_header(token)

    if "kid" not in unverified_header:
        raise HTTPException(status_code=401, detail="Malformed token header")

    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }

    raise HTTPException(status_code=401, detail="Public key not found")


# The reusable core decoder
def decode_token(token: str):
    rsa_key = get_rsa_key(token)
    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# Dependency for FastAPI routes
def verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
):
    return decode_token(credentials.credentials)


# Manual extractor for middleware
def verify_token_from_request(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = auth_header.removeprefix("Bearer ").strip()
    return decode_token(token)


def get_auth0_id(request: Request) -> str:
    try:
        payload = verify_token_from_request(request)
        identity = payload.get("sub", "anonymous")
        return identity
    except Exception:
        return "anonymous"
