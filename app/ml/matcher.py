import math
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from app.config import (
    CAMPUS_LOCATIONS,
    WEIGHT_CATEGORY,
    WEIGHT_TEXT,
    WEIGHT_VISION,
    WEIGHT_ATTRIBUTES,
    WEIGHT_SPATIOTEMPORAL,
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
)
from app.ml.vision import compute_visual_similarity
from app.ml.nlp import get_nlp_engine

def compute_spatiotemporal_score(item1: Dict[str, Any], item2: Dict[str, Any]) -> Tuple[float, str]:
    """
    Computes spatial proximity on campus and temporal difference score.
    Returns (score, reason_string)
    """
    loc1 = (item1.get("location") or "").strip()
    loc2 = (item2.get("location") or "").strip()
    
    # Check exact name match first
    same_named_location = (loc1.lower() == loc2.lower()) if (loc1 and loc2) else False
    in_campus1 = loc1 in CAMPUS_LOCATIONS
    in_campus2 = loc2 in CAMPUS_LOCATIONS

    if same_named_location:
        dist_m = 0.0
        spatial_score = 1.0
        loc_desc = f"Identical campus location ({loc1})"
    elif in_campus1 and in_campus2:
        coord1 = CAMPUS_LOCATIONS[loc1]
        coord2 = CAMPUS_LOCATIONS[loc2]
        dx = coord1["x"] - coord2["x"]
        dz = coord1["z"] - coord2["z"]
        dist_m = math.sqrt(dx * dx + dz * dz)
        spatial_score = math.exp(-dist_m / 35.0)
        loc_desc = f"{int(dist_m)}m campus separation ({loc1} vs {loc2})"
    else:
        # At least one location is unlisted and they are not identical strings
        dist_m = 65.0
        spatial_score = 0.20
        loc_desc = f"Different campus zones ({loc1 or 'Unspecified'} vs {loc2 or 'Unspecified'})"

    # Temporal component
    time_score = 0.75 # default if unparseable or missing
    hours_diff = None
    try:
        t1_str = str(item1.get("date_time", ""))[:16]
        t2_str = str(item2.get("date_time", ""))[:16]
        if t1_str and t2_str:
            t1 = datetime.fromisoformat(t1_str.replace(" ", "T"))
            t2 = datetime.fromisoformat(t2_str.replace(" ", "T"))
            hours_diff = abs((t1 - t2).total_seconds()) / 3600.0
            # Temporal decay over 4 days (96 hours)
            time_score = math.exp(-hours_diff / 72.0)
    except Exception:
        pass
        
    combined = 0.60 * spatial_score + 0.40 * time_score
    time_desc = f"{int(hours_diff)}h apart" if hours_diff is not None else "similar timeframe"
    reason = f"{loc_desc}, {time_desc}"
    
    return round(float(combined), 4), reason

def canonical_brand(b: str) -> str:
    """Normalize brand and model lines to canonical brand family."""
    if not b:
        return ""
    norm = b.lower().replace("-", " ").replace("_", " ").strip()
    alias_map = {
        "macbook": "apple", "macbook pro": "apple", "macbook air": "apple",
        "ipad": "apple", "iphone": "apple", "airpods": "apple",
        "thinkpad": "lenovo", "ideapad": "lenovo", "yoga": "lenovo",
        "xps": "dell", "alienware": "dell",
        "pavilion": "hp", "envy": "hp", "spectre": "hp",
        "rog": "asus", "zenbook": "asus",
        "galaxy": "samsung",
        "hydroflask": "hydro flask", "hydro flask": "hydro flask",
    }
    return alias_map.get(norm, norm)

def compute_attribute_score(item1: Dict[str, Any], item2: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Computes attribute agreement: Brand, Primary Color, Secondary Color, Distinguishing Features.
    """
    reasons = []
    scores = []
    
    # Brand check with canonical alias normalization
    raw_b1 = (item1.get("brand") or "").strip()
    raw_b2 = (item2.get("brand") or "").strip()
    b1 = canonical_brand(raw_b1)
    b2 = canonical_brand(raw_b2)
    
    if b1 and b2:
        if b1 == b2 or b1 in b2 or b2 in b1:
            scores.append((1.0, 0.40))
            matched_display = raw_b1 if raw_b1 else raw_b2
            reasons.append(f"Matching brand '{matched_display}'")
        else:
            scores.append((0.0, 0.40))
    elif b1 or b2:
        scores.append((0.5, 0.20)) # One brand unspecified
        
    # Primary color check
    c1 = (item1.get("primary_color") or "").strip().lower()
    c2 = (item2.get("primary_color") or "").strip().lower()
    if c1 and c2:
        if c1 == c2:
            scores.append((1.0, 0.35))
            reasons.append(f"Matching primary color '{item1.get('primary_color')}'")
        else:
            scores.append((0.15, 0.35))
    elif c1 or c2:
        scores.append((0.5, 0.15))

    # Distinguishing features overlap
    f1 = set(str(x).lower().strip() for x in (item1.get("distinguishing_features") or []))
    f2 = set(str(x).lower().strip() for x in (item2.get("distinguishing_features") or []))
    if f1 and f2:
        # Check subword or fuzzy overlaps
        overlap = 0
        matched_feats = []
        for feat1 in f1:
            for feat2 in f2:
                words1 = set(feat1.split())
                words2 = set(feat2.split())
                if feat1 == feat2 or len(words1.intersection(words2)) >= 1:
                    overlap += 1
                    matched_feats.append(feat1)
                    break
        if overlap > 0:
            scores.append((1.0, 0.25))
            reasons.append(f"Shared unique markings: {', '.join(matched_feats[:2])}")
        else:
            scores.append((0.2, 0.25))
            
    if not scores:
        return 0.5, ["Neutral attribute data"]
        
    total_w = sum(w for _, w in scores)
    attr_score = sum(s * w for s, w in scores) / total_w
    return round(float(attr_score), 4), reasons

def match_items(query_item: Dict[str, Any], candidate_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes multi-modal match between a query item (Lost/Found) and a candidate item (Found/Lost).
    Returns detailed score breakdown and natural language explanation.
    """
    nlp = get_nlp_engine()
    
    # 1. Category Gate & Score with robust normalization
    cat1 = (query_item.get("category") or "").strip().lower()
    cat2 = (candidate_item.get("category") or "").strip().lower()
    if cat1 and cat2 and cat1 == cat2:
        category_score = 1.0
    elif cat1 == "other" or cat2 == "other" or not cat1 or not cat2:
        category_score = 0.55
    else:
        # Cross-category penalty
        category_score = 0.05

    # 2. Text NLP Similarity
    text1 = f"{query_item.get('title', '')} {query_item.get('description', '')}"
    text2 = f"{candidate_item.get('title', '')} {candidate_item.get('description', '')}"
    text_score = nlp.compute_text_similarity(text1, text2)

    # 3. Vision Score
    v1 = query_item.get("vision_embedding")
    v2 = candidate_item.get("vision_embedding")
    if isinstance(v1, dict) and isinstance(v2, dict) and "deep_embedding" in v1 and "deep_embedding" in v2:
        vision_score = compute_visual_similarity(v1, v2)
    else:
        # If image embeddings are missing for one or both, blend text color/brand proxy
        c1 = (query_item.get("primary_color") or "").lower()
        c2 = (candidate_item.get("primary_color") or "").lower()
        if c1 and c2 and c1 == c2:
            vision_score = 0.85
        elif c1 and c2:
            vision_score = 0.20
        else:
            vision_score = 0.50

    # 4. Attribute Score
    attribute_score, attr_reasons = compute_attribute_score(query_item, candidate_item)

    # 5. Spatiotemporal Score
    spatiotemporal_score, st_reason = compute_spatiotemporal_score(query_item, candidate_item)

    # Overall weighted score
    overall_raw = (
        WEIGHT_CATEGORY * category_score +
        WEIGHT_TEXT * text_score +
        WEIGHT_VISION * vision_score +
        WEIGHT_ATTRIBUTES * attribute_score +
        WEIGHT_SPATIOTEMPORAL * spatiotemporal_score
    )

    # Hard category gate: if completely different categories, cap maximum confidence
    if category_score < 0.2:
        overall_raw = min(overall_raw, 0.35)

    overall_confidence = round(float(overall_raw), 4)

    # Confidence tier
    if overall_confidence >= HIGH_CONFIDENCE_THRESHOLD:
        confidence_level = "High"
    elif overall_confidence >= MEDIUM_CONFIDENCE_THRESHOLD:
        confidence_level = "Medium"
    else:
        confidence_level = "Low"

    # Natural-language explanation
    explanation_parts = []
    if category_score >= 0.9:
        explanation_parts.append(f"Matching category '{cat1}'")
    if attr_reasons:
        explanation_parts.extend(attr_reasons)
    if text_score > 0.40:
        explanation_parts.append(f"High text descriptive correlation ({int(text_score * 100)}%)")
    explanation_parts.append(st_reason)

    explanation = "; ".join(explanation_parts) + f". Overall AI confidence: {int(overall_confidence * 100)}%."

    return {
        "category_score": round(category_score, 4),
        "text_score": round(text_score, 4),
        "vision_score": round(vision_score, 4),
        "attribute_score": round(attribute_score, 4),
        "spatiotemporal_score": round(spatiotemporal_score, 4),
        "overall_confidence": overall_confidence,
        "confidence_level": confidence_level,
        "explanation": explanation
    }
