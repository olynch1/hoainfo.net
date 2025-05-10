from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
import uuid

class ActivityLog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str
    action: str
    endpoint: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    community_id: Optional[str] = None

