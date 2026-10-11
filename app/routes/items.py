import os
import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from app.config import UPLOAD_DIR
from app.models import ItemCreate, ItemResponse
from app.database import (
    insert_item, get_item, list_items, update_item_status,
    get_custody_history, insert_notification
)
from app.ml.vision import analyze_image
from app.ml.nlp import get_nlp_engine
from app.ml.matcher import match_items, HIGH_CONFIDENCE_THRESHOLD

router = APIRouter(prefix="/api/items", tags=["items"])

@router.post("", response_model=ItemResponse)
async def create_item(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    location: str = Form(...),
    specific_spot: Optional[str] = Form(None),
    date_time: str = Form(...),
    item_type: str = Form(...), # 'lost' or 'found'
    contact_name: str = Form(...),
    contact_email: str = Form(...),
    contact_phone: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    primary_color: Optional[str] = Form(None),
    secondary_color: Optional[str] = Form(None),
    distinguishing_features: Optional[str] = Form(None), # JSON or comma-separated
    secret_verification_question: Optional[str] = Form(None),
    secret_verification_answer: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    # Validate item_type
    normalized_item_type = item_type.strip().lower()
    if normalized_item_type not in ("lost", "found"):
        raise HTTPException(status_code=400, detail="item_type must be either 'lost' or 'found'")

    nlp = get_nlp_engine()
    
    # 1. NLP automatic attribute extraction if fields not explicitly provided
    extracted = nlp.extract_attributes(description, title)
    final_brand = brand or extracted.get("brand")
    final_category = category if category and category != "Other" else extracted.get("category", "Other")
    
    parsed_features = []
    if distinguishing_features:
        try:
            parsed_features = json.loads(distinguishing_features)
        except Exception:
            parsed_features = [f.strip() for f in distinguishing_features.split(",") if f.strip()]
    if not parsed_features:
        parsed_features = extracted.get("distinguishing_features", [])

    # 2. Image Processing & Vision feature extraction
    image_url = None
    vision_embedding = None
    vision_extracted = 0
    final_primary_color = primary_color or extracted.get("primary_color")
    final_secondary_color = secondary_color or extracted.get("secondary_color")

    ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

    if image and image.filename:
        ext = Path(image.filename).suffix.lower()
        if not ext:
            ext = ".jpg"
        if ext not in ALLOWED_IMAGE_EXTS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Allowed image formats: {', '.join(sorted(ALLOWED_IMAGE_EXTS))}"
            )

        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        saved_path = UPLOAD_DIR / unique_name
        
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        try:
            vis_profile = analyze_image(str(saved_path))
            image_url = f"/static/uploads/{unique_name}"
            vision_embedding = vis_profile
            vision_extracted = 1
            if not final_primary_color:
                final_primary_color = vis_profile.get("primary_color")
            if not final_secondary_color:
                final_secondary_color = vis_profile.get("secondary_color")
        except Exception as e:
            # Clean up corrupted/non-image upload so bad files don't stay on disk
            if os.path.exists(saved_path):
                try:
                    os.remove(saved_path)
                except OSError:
                    pass
            image_url = None
            print(f"Warning: Vision feature extraction error on uploaded file: {e}")

    item_dict = {
        "title": title,
        "description": description,
        "category": final_category,
        "location": location,
        "specific_spot": specific_spot,
        "date_time": date_time,
        "item_type": item_type.lower(),
        "contact_name": contact_name,
        "contact_email": contact_email,
        "contact_phone": contact_phone,
        "brand": final_brand,
        "primary_color": final_primary_color,
        "secondary_color": final_secondary_color,
        "distinguishing_features": parsed_features,
        "secret_verification_question": secret_verification_question,
        "secret_verification_answer": secret_verification_answer,
        "image_url": image_url,
        "status": "active",
        "vision_embedding": vision_embedding,
        "vision_features_extracted": vision_extracted,
        "nlp_features_extracted": 1,
        "created_at": datetime.now().isoformat()
    }

    item_id = insert_item(item_dict)
    saved_item = get_item(item_id)

    # 3. Automatic background match trigger against opposite pool
    opposite_type = "found" if item_type.lower() == "lost" else "lost"
    candidates = list_items(item_type=opposite_type, status="active", limit=50)
    for cand in candidates:
        m = match_items(saved_item, cand)
        if m["overall_confidence"] >= HIGH_CONFIDENCE_THRESHOLD:
            # Trigger notification
            insert_notification(
                recipient_email=saved_item["contact_email"],
                title=f"Potential Match Detected ({int(m['overall_confidence'] * 100)}%)",
                message=f"Your {item_type} item '{saved_item['title']}' has a high-confidence match: '{cand['title']}'. {m['explanation']}",
                item_id=saved_item["id"],
                match_id=cand["id"]
            )
            # Also notify the opposite party
            insert_notification(
                recipient_email=cand["contact_email"],
                title=f"Potential Match Detected ({int(m['overall_confidence'] * 100)}%)",
                message=f"Your {cand['item_type']} item '{cand['title']}' matches newly reported '{saved_item['title']}'.",
                item_id=cand["id"],
                match_id=saved_item["id"]
            )

    return saved_item

@router.get("", response_model=List[ItemResponse])
def get_items(
    item_type: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, le=200)
):
    return list_items(
        item_type=item_type,
        category=category,
        location=location,
        status=status,
        search=search,
        limit=limit
    )

@router.get("/{item_id}")
def get_item_detail(item_id: int):
    item = get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    history = get_custody_history(item_id)
    
    # Hide ground truth secret answer from public output for security
    sanitized_item = dict(item)
    sanitized_item["has_secret_verification"] = bool(sanitized_item.get("secret_verification_answer"))
    sanitized_item.pop("secret_verification_answer", None)
    
    return {
        "item": sanitized_item,
        "custody_history": history
    }

@router.post("/{item_id}/status")
def change_status(item_id: int, new_status: str = Form(...), actor: str = Form("Campus Security"), details: str = Form("")):
    item = get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    update_item_status(item_id, new_status, actor, details)
    return {"message": f"Status updated to {new_status}", "item_id": item_id}
