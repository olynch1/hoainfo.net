from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import uuid

# ----------------- USER -----------------
class User(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str
    password_hash: str
    role: Optional[str] = Field(default="resident")
    tier: Optional[str] = Field(default="solo")
    community_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    show_in_directory: bool = Field(default=False)

    complaints: List["Complaint"] = Relationship(back_populates="user")
    messages: List["Message"] = Relationship(back_populates="user")
    notifications: List["Notification"] = Relationship(back_populates="user")
    documents: List["Document"] = Relationship(back_populates="user")
    invites: List["TenantInvite"] = Relationship(back_populates="landlord")
    board_verifications: List["BoardVerificationRequest"] = Relationship(back_populates="user")
    activity_logs: List["ActivityLog"] = Relationship(back_populates="user")

# ----------------- COMPLAINT -----------------
class Complaint(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    title: str
    description: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    photo_url: Optional[str] = None
    community_id: str
    read: bool = Field(default=False)
    read_at: Optional[datetime] = None
    status: str = Field(default="Pending")

    user: Optional[User] = Relationship(back_populates="complaints")

# ----------------- MESSAGE -----------------
class Message(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    subject: str
    body: str
    read: bool = Field(default=False)
    read_at: Optional[datetime] = Field(default=None, nullable=True)
    action: str
    endpoint: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    community_id: str

    user: Optional[User] = Relationship(back_populates="messages")

# ----------------- TENANT INVITE -----------------
class TenantInvite(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    landlord_id: str = Field(foreign_key="user.id")
    tenant_email: str
    verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    landlord: Optional[User] = Relationship(back_populates="invites")

# ----------------- BOARD VERIFICATION -----------------
class BoardVerificationRequest(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    community_id: str
    approvals: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    response: Optional[str] = None

    user: Optional[User] = Relationship(back_populates="board_verifications")

# ----------------- DOCUMENT -----------------
class Document(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    title: str
    description: Optional[str] = None
    filename: str
    url: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    community_id: str

    user: Optional[User] = Relationship(back_populates="documents")

# ----------------- ACTIVITY LOG -----------------
class ActivityLog(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    community_id: str
    approvals: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="activity_logs")

# ----------------- NOTIFICATION -----------------
class Notification(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}

    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = Field(default=False)

    user: Optional[User] = Relationship(back_populates="notifications")

