from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class RegisterModel(BaseModel):
    email: EmailStr
    password: str
    community_id: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class EmailRequest(BaseModel):
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

# 📝 Complaint Submission Schema
class ComplaintModel(BaseModel):
    title: str
    description: str
    community_id: str
    photo_url: Optional[str] = None

# 📬 Complaint Response Schema
class ComplaintResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    timestamp: datetime
    read: bool
    read_at: Optional[datetime]
    photo_url: Optional[str]

