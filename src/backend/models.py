from sqlalchemy import Column
from sqlalchemy.dialects.sqlite import JSON
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import uuid

class User(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str
    password_hash: str  # ✅ required for bcrypt
    role: Optional[str] = Field(default="resident")  # resident, board, admin
    tier: Optional[str] = Field(default="solo")      # solo, household, landlord
    community_id: str

    # Reverse relationships (optional)
    complaints: List["Complaint"] = Relationship(back_populates="user")
    messages: List["Message"] = Relationship(back_populates="user")


class Complaint(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    title: str
    description: str
    timestamp: Optional[str]
    photo_url: Optional[str] = None
    community_id: str
    read: bool = False
    user: Optional[User] = Relationship(back_populates="complaints")


class Message(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    subject: str
    body: str
    timestamp: Optional[str]
    read: bool = False
    response: Optional[str] = None
    community_id: str

    user: Optional[User] = Relationship(back_populates="messages")


class ActivityLog(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str
    action: str
    endpoint: str
    ip_address: str
    user_agent: str
    timestamp: str
    community_id: str


class TenantInvite(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    landlord_email: str
    tenant_email: str
    community_id: str
    verified: bool = False

class BoardVerificationRequest(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    community_id: str
    approved_by: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    verified: bool = Field(default=False)

