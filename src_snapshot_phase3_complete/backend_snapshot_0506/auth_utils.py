import os
import time
from fastapi import Header, HTTPException
from jose import JWTError, jwt

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

def create_token(username: str):
    payload = {"sub": username, "exp": time.time() + 3600}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except (ValueError, JWTError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

