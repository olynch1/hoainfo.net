from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional
import os
import json

from src.backend.auth_utils import verify_token
from src.backend.models import User
from src.backend.database import get_session

router = APIRouter()

# ✅ Premium Tier AI Helpdesk Search
@router.get("/ai/helpdesk")
def legal_ai_helpdesk(
    keyword: str = Query(..., description="Keyword to search in state law"),
    user: User = Depends(verify_token),
    session: Session = Depends(get_session)
):
    if user.tier not in ("solo", "household", "landlord"):
        return {"response": "Upgrade to access AI helpdesk."}

    filepath = "src/backend/legal/nrs_nv.json"
    if not os.path.exists(filepath):
        return {"error": "NRS law file not found."}

    with open(filepath, "r") as f:
        entries = json.load(f)

    matches = [entry for entry in entries if keyword.lower() in entry.get("summary", "").lower()]

    if not matches:
        return {"response": f"No statute found for keyword: '{keyword}'."}

    return {"matches": matches}

# ✅ Free Tier - General Summary Only
@router.get("/api/legal/nrs-summary")
def legal_summary():
    return {
        "response": (
            "You can manually browse Nevada HOA law (NRS 116) using the categorized summary available. "
            "For personalized answers, AI search, and plain-English interpretations, upgrade to a premium plan."
        )
    }

