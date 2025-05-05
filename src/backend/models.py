
from sqlmodel import SQLModel, Field
from typing import Optional

# ✅ User model used for role-based/tier-based access (not a DB table for now)
class User(SQLModel):
    email: str
    role: str
    tier: Optional[str] = None

# ✅ Complaint database model
class Complaint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    timestamp: str
    user_email: str
    photo_url: Optional[str] = None

# ✅ Optional response model for filtered/safe outputs
class ComplaintResponse(SQLModel):
    id: int
    title: str
    description: str
    timestamp: str
    user_email: str
    photo_url: Optional[str]


