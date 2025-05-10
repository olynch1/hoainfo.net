from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class Message(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    subject: str
    body: str
    user_id: str
    community_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 🆕 Reply support
    response: Optional[str] = None
    responded_by: Optional[str] = None
    responded_at: Optional[datetime] = None
    is_read: bool = Field(default=False)

