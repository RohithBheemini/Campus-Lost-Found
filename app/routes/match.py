from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.database import get_item, list_items
from app.ml.matcher import match_items
from app.models import MatchResponse, MatchCandidate, ItemResponse, MatchScoreBreakdown

router = APIRouter(prefix="/api/match", tags=["matching"])

class DirectCompareRequest(BaseModel):
    query_title: str
    query_description: str
    query_category: str
    query_location: str
    query_date_time: str
    candidate_title: str
    candidate_description: str
    candidate_category: str
    candidate_location: str
    candidate_date_time: str

@router.get("/{item_id}", response_model=MatchResponse)
def get_matches_for_item(
    item_id: int,
    min_confidence: float = Query(0.10, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=100)
):
    query_item = get_item(item_id)
    if not query_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Match against the opposite pool
    target_type = "found" if query_item["item_type"] == "lost" else "lost"
    candidates_raw = list_items(item_type=target_type, limit=200)

    scored_candidates = []
    for cand in candidates_raw:
        if cand["id"] == query_item["id"]:
            continue
            
        breakdown = match_items(query_item, cand)
        
        if breakdown["overall_confidence"] >= min_confidence:
            # Sanitize candidate item secret answer
            cand_sanitized = dict(cand)
            cand_sanitized.pop("secret_verification_answer", None)
            
            scored_candidates.append(
                MatchCandidate(
                    item=ItemResponse(**cand_sanitized),
                    score_breakdown=MatchScoreBreakdown(**breakdown)
                )
            )

    # Sort descending by overall confidence score
    scored_candidates.sort(key=lambda x: x.score_breakdown.overall_confidence, reverse=True)
    top_candidates = scored_candidates[:limit]

    # Sanitize query item
    query_sanitized = dict(query_item)
    query_sanitized.pop("secret_verification_answer", None)

    return MatchResponse(
        query_item=ItemResponse(**query_sanitized),
        candidates=top_candidates,
        total_candidates=len(scored_candidates)
    )

@router.post("/compare")
def compare_direct(req: DirectCompareRequest):
    item1 = {
        "title": req.query_title,
        "description": req.query_description,
        "category": req.query_category,
        "location": req.query_location,
        "date_time": req.query_date_time
    }
    item2 = {
        "title": req.candidate_title,
        "description": req.candidate_description,
        "category": req.candidate_category,
        "location": req.candidate_location,
        "date_time": req.candidate_date_time
    }
    
    breakdown = match_items(item1, item2)
    return {
        "item1": item1,
        "item2": item2,
        "match_breakdown": breakdown
    }
