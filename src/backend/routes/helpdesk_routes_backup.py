from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from backend.auth_utils import verify_token
from backend.database import get_session
from backend.models import User

import os

router = APIRouter()

# Map community_id → state
community_state_map = {
    "00001": "NV",  # Granbury
    "00002": "CA",
    "00003": "FL",
    # Add more as needed
}

@router.get("/ai/helpdesk")
def legal_ai_helpdesk(
    keyword: str = Query(..., description="Keyword to search in law files"),
    user: User = Depends(veirfy_token),
    session: Session = Depends(get_session)
):
    # Determine state based on community_id
    state = community_state_map.get(user.community_id, "NV")

    # Load legal corpus
    file_path = f"src/backend/legal/nrs_{state.lower()}.txt"
    if not os.path.exists(file_path):
        return {"error": f"No legal corpus found for state: {state}"}

    with open(file_path, "r") as f:
        raw_sections = f.read().split("=== ")[1:]  # skip header
        matches = []

        for section in raw_sections:
            if keyword.lower() in section.lower():
                heading = "NRS " + section[:8].strip()
                quote = section.split("SUMMARY:")[0].strip()
                summary = section.split("SUMMARY:")[1].strip() if "SUMMARY:" in section else ""
                matches.append({
                    "source": heading,
                    "quote": quote,
                    "summary": summary
                })

    if not matches:
        return {"message": f"No law found for keyword '{keyword}' in {state}."}

    return {
        "state": state,
        "results": matches
    }

