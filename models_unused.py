from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid

class User(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str
    role: str = "resident"  # resident, board, admin
    tier: str = "solo"      # solo, household, landlord
    community_id: str

class Message(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    subject: str
    body: str
    user_id: str
    community_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    response: Optional[str] = None
    responded_by: Optional[str] = None
    responded_at: Optional[datetime] = None
    is_read: bool = False

class Complaint(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    community_id: str
    status: str = "open"  # open, closed, resolved

class ActivityLog(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str
    action: str
    endpoint: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    community_id: Optional[str] = None

