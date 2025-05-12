from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from backend.models import User
from backend.database import get_session
from backend.otp_service import otp_store
from backend.auth_utils import create_access_token

router = APIRouter()

@router.post("/verify-otp")
def verify_otp(email: str, otp: str, session: Session = Depends(get_session)):
    record = otp_store.get(email)
    if not record or record["otp"] != otp:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_access_token(user.email)
    return {"access_token": access_token}

