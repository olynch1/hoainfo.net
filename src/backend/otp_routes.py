from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from src.backend.auth_utils import create_access_token
from src.backend.models import User
from src.backend.database import otp_store, get_session

router = APIRouter()

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

@router.post("/verify-otp")
def verify_otp(request: OTPVerifyRequest):
    email = request.email
    otp_input = request.otp

    stored_otp_data = otp_store.get(email)

    if not stored_otp_data:
        raise HTTPException(status_code=404, detail="OTP not found or expired")

    otp_code, _, _ = stored_otp_data

    if otp_code != otp_input:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    del otp_store[email]

    with get_session() as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        token = create_access_token(user.email)
        return {
            "access_token": token,
            "token_type": "bearer"
        }

