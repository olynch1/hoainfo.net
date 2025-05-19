from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.backend.database import otp_store

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

    return {"message": "OTP verified successfully"}

