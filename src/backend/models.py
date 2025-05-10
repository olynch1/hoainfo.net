from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str
    role: str = "resident"  # Options: resident, board, admin
    tier: str = "solo"       # Options: solo, household, landlord
    is_tenant: bool = Field(default=False)
    community_id: str
    verified: bool = Field(default=False)

class TenantInvite(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    landlord_id: str  # The user ID of the landlord
    tenant_email: str  # The email address of the tenant
    token: str  # Invite token or code for tenant to claim
    claimed: bool = Field(default=False)
    invited_at: datetime = Field(default_factory=datetime.utcnow)
    claimed_at: Optional[datetime] = None
    community_id: str

class Message(SQLModel, table=True):
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
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    community_id: str
    status: str = "open"  # Options: open, closed, resolved

class ActivityLog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str
    action: str
    endpoint: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    community_id: Optional[str] = None


