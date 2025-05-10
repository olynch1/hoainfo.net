from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    community_id: str
    is_board_member: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Complaint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_email: str
    community_id: str


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender_email: str
    recipient_email: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OTP(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_email: str
    otp_code: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime


