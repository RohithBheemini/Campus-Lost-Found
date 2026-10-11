import re
from fastapi import APIRouter, HTTPException
from app.models import ClaimCreate, ClaimResponse
from app.database import (
    get_item, insert_claim, list_claims_for_item,
    update_item_status, insert_notification
)
from app.ml.nlp import get_nlp_engine

router = APIRouter(prefix="/api/claims", tags=["claims"])

def evaluate_claim_proof(ground_truth_answer: str, claimant_answer: str, distinguishing_features: list, additional_proof: str = "") -> tuple[float, bool, str]:
    """
    Automated AI verification engine:
    Evaluates claimant's secret answer and additional proof against ground truth.
    Returns: (score, passed, notes)
    """
    nlp = get_nlp_engine()
    
    gt_norm = (ground_truth_answer or "").strip().lower()
    cl_norm = (claimant_answer or "").strip().lower()
    
    # Strip boundary punctuation/whitespace
    cl_cleaned = re.sub(r"^[^\w]+|[^\w]+$", "", cl_norm)
    gt_cleaned = re.sub(r"^[^\w]+|[^\w]+$", "", gt_norm)
    
    if not cl_cleaned:
        return 0.0, False, "Claimant secret answer was empty or non-alphanumeric."
        
    if not gt_cleaned:
        # If no secret answer was configured on the found item,
        # evaluate claimant proof against private distinguishing features
        combined_proof = f"{cl_cleaned} {(additional_proof or '').strip().lower()}".strip()
        matched_feats = 0
        total_feats = len(distinguishing_features)
        
        if total_feats == 0:
            return 0.50, False, "No hidden challenge or distinguishing marks recorded. Item flagged for manual security inspection."
            
        for f in distinguishing_features:
            f_norm = str(f).lower().strip()
            # Require whole phrase or at least 2 significant words to match
            f_words = [w for w in re.findall(r"\w+", f_norm) if len(w) >= 3 and w not in {"the", "and", "with", "item", "side"}]
            if f_norm in combined_proof:
                matched_feats += 1
            elif f_words:
                matching_words = sum(1 for w in f_words if w in combined_proof)
                if matching_words >= min(2, len(f_words)):
                    matched_feats += 1
                    
        score = min(1.0, 0.35 + (0.65 * (matched_feats / max(total_feats, 1))))
        passed = (matched_feats > 0 and score >= 0.70)
        notes = f"Proof matched {matched_feats} of {total_feats} private distinguishing item traits."
        return round(score, 3), passed, notes

    # 1. Exact match
    if gt_cleaned == cl_cleaned:
        return 1.0, True, "Exact verification match on private ownership challenge."
    
    # 2. Substring containment:
    # A) Claimant answer contains the entire ground truth: e.g. "it has a yellow JS sticker" contains "yellow JS sticker"
    if len(gt_cleaned) >= 3 and gt_cleaned in cl_cleaned:
        return 0.95, True, "Full ownership challenge answer verified within claimant description."
        
    # B) Claimant answer is contained in ground truth:
    # ONLY valid if claimant provided a substantial portion of the answer (at least 60% of chars or multi-word match),
    # NEVER for single characters or short trivial fragments like 'a', 'e', 'in'!
    if len(cl_cleaned) >= 5 and cl_cleaned in gt_cleaned:
        length_ratio = len(cl_cleaned) / len(gt_cleaned)
        if length_ratio >= 0.55:
            return 0.90, True, "Strong ownership match verifying primary challenge details."

    # 3. Numeric / Serial identification match (require at least 2 consecutive digits)
    gt_digits = [d for d in re.findall(r"\d+", gt_cleaned) if len(d) >= 2]
    cl_digits = [d for d in re.findall(r"\d+", cl_cleaned) if len(d) >= 2]
    digit_overlap = bool(gt_digits and cl_digits and set(gt_digits).intersection(set(cl_digits)))
    
    # 4. Token & Semantic NLP Similarity
    semantic_sim = nlp.compute_text_similarity(gt_cleaned, cl_cleaned)
    
    # Jaccard word token overlap
    gt_words = set(w for w in re.findall(r"\w+", gt_cleaned) if len(w) >= 2)
    cl_words = set(w for w in re.findall(r"\w+", cl_cleaned) if len(w) >= 2)
    word_overlap = len(gt_words.intersection(cl_words)) / max(len(gt_words), 1) if gt_words else 0.0

    if digit_overlap:
        # Significant identifying digits match exactly (e.g. student ID digits or room number)
        combined_score = max(0.80, 0.50 + 0.30 * word_overlap + 0.20 * semantic_sim)
    else:
        combined_score = 0.55 * semantic_sim + 0.45 * word_overlap

    # Also check if claimant mentioned unique distinguishing features
    if additional_proof and distinguishing_features:
        proof_clean = additional_proof.lower()
        feats_text = " ".join(distinguishing_features).lower()
        proof_sim = nlp.compute_text_similarity(feats_text, proof_clean)
        if proof_sim > 0.30:
            combined_score = max(combined_score, 0.60 * combined_score + 0.40 * proof_sim)

    combined_score = round(float(combined_score), 3)
    
    if combined_score >= 0.70:
        return combined_score, True, f"High AI verification confidence ({int(combined_score * 100)}%). Ownership verified."
    elif combined_score >= 0.40:
        return combined_score, False, f"Moderate similarity ({int(combined_score * 100)}%). Flagged for manual campus security review."
    else:
        return combined_score, False, f"Low verification score ({int(combined_score * 100)}%). Answer does not match registered item details."

@router.post("", response_model=ClaimResponse)
def submit_claim(claim: ClaimCreate):
    item = get_item(claim.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    if item["item_type"] != "found":
        raise HTTPException(status_code=400, detail="Claims can only be filed against 'found' items.")

    # Ground truth challenge check
    gt_answer = item.get("secret_verification_answer") or ""
    dist_feats = item.get("distinguishing_features") or []
    
    score, passed, notes = evaluate_claim_proof(
        ground_truth_answer=gt_answer,
        claimant_answer=claim.secret_answer,
        distinguishing_features=dist_feats,
        additional_proof=claim.additional_proof or ""
    )

    claim_status = "verified" if passed else ("under_review" if score >= 0.40 else "rejected")

    claim_record = {
        "item_id": claim.item_id,
        "claimant_name": claim.claimant_name,
        "claimant_student_id": claim.claimant_student_id,
        "claimant_email": claim.claimant_email,
        "claimant_phone": claim.claimant_phone,
        "secret_answer": claim.secret_answer,
        "additional_proof": claim.additional_proof,
        "status": claim_status,
        "verification_score": score,
        "verification_passed": passed,
        "verification_notes": notes
    }

    claim_id = insert_claim(claim_record)

    # If verified, update item status and trigger notifications
    if passed:
        update_item_status(
            claim.item_id,
            new_status="claimed",
            actor=f"AutoClaim AI (Verified for {claim.claimant_name})",
            details=f"Claim #{claim_id} verified with {int(score * 100)}% confidence."
        )
        # Notify claimant
        insert_notification(
            recipient_email=claim.claimant_email,
            title="Claim Verified! Item Ready for Pickup",
            message=f"Your claim for '{item['title']}' has been verified! Please collect it at the Central Security Desk with your ID card (ID: {claim.claimant_student_id}).",
            item_id=claim.item_id
        )
        # Notify finder
        insert_notification(
            recipient_email=item["contact_email"],
            title="Item Owner Successfully Verified",
            message=f"The item '{item['title']}' you reported has been verified and claimed by {claim.claimant_name}.",
            item_id=claim.item_id
        )
    else:
        # Notify claimant of review status
        insert_notification(
            recipient_email=claim.claimant_email,
            title=f"Claim Status: {claim_status.title()}",
            message=f"Your claim for '{item['title']}' was evaluated with status: {claim_status}. {notes}",
            item_id=claim.item_id
        )

    claims = list_claims_for_item(claim.item_id)
    new_claim = next((c for c in claims if c["id"] == claim_id), None)
    if not new_claim:
        raise HTTPException(status_code=500, detail="Failed to retrieve created claim")
        
    return ClaimResponse(**new_claim)

@router.get("/item/{item_id}", response_model=list[ClaimResponse])
def get_claims_for_item(item_id: int):
    item = get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return list_claims_for_item(item_id)
