from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from src.backend.auth_utils import verify_token_optional
from src.backend.models import User
from sentence_transformers import SentenceTransformer, util
import json
import torch
import os

router = APIRouter()

# Load and parse JSON data
json_path = os.path.join("src", "backend", "legal", "nrs_nv.json")
with open(json_path, "r") as f:
    nrs_data = json.load(f)

# Load model once globally
model = SentenceTransformer('all-MiniLM-L6-v2')

# Precompute embeddings for all NRS summaries
for entry in nrs_data:
    entry["embedding"] = model.encode(
        " ".join([entry.get("title", ""), entry.get("summary", ""), entry.get("category", "")]),
        convert_to_tensor=True
    )

@router.post("/ask")
async def ask_legal_ai(request: Request, user: User = Depends(verify_token_optional)
):
 # 🔍 DEBUG PRINT START
    print("\n===== /ask endpoint accessed =====")
    if user:
        print(f"✅ User: {user.email}")
        print(f"🟢 Tier: {user.tier}")
        print(f"🛠️ Role: {user.role}")
    else:
        print("⚠️ No user detected (free-tier assumed)")
    print("===================================\n")
    # 🔍 DEBUG PRINT END
    body = await request.json()
    question = body.get("question", "").strip()

    if not question:
        return JSONResponse({"message": "Empty question received."}, status_code=400)

    question_embedding = model.encode(question, convert_to_tensor=True)

    best_match = None
    best_score = -1

    for entry in nrs_data:
        score = util.pytorch_cos_sim(question_embedding, entry["embedding"]).item()
        if score > best_score:
            best_score = score
            best_match = entry

    if not best_match or best_score < 0.35:
        return JSONResponse({"message": "No relevant NRS statute found."}, status_code=404)

    # Handle premium access (paid tier or board/admin role)
    if user and (user.tier in ["solo", "household", "landlord"] or user.role in ["board", "admin"]):
        return {
            "NRS": best_match.get("number") or best_match.get("statute"),
            "title": best_match.get("title", "N/A"),
            "category": best_match.get("category", "N/A"),
            "summary": best_match.get("summary", "N/A"),
            "score": round(best_score, 3)
        }

    # Free tier: show only general info
    return {
        "category": best_match.get("category", "Miscellaneous Rights, Duties and Restrictions"),
        "message": "This topic is addressed under Nevada Revised Statutes Chapter 116. Upgrade to access specific statute references."
    }

