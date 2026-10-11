from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

class ItemBase(BaseModel):
    title: str = Field(..., description="Short title of the item")
    description: str = Field(..., description="Detailed description")
    category: str = Field(..., description="Item category")
    location: str = Field(..., description="Campus location")
    specific_spot: Optional[str] = Field(None, description="Specific room, desk, bench, etc.")
    date_time: str = Field(..., description="Date and time when lost or found (ISO format or YYYY-MM-DD HH:MM)")
    item_type: str = Field(..., description="'lost' or 'found'")
    contact_name: str = Field(..., description="Name of student/staff reporting")
    contact_email: str = Field(..., description="Campus email for notifications")
    contact_phone: Optional[str] = Field(None, description="Phone number")
    
    # Visual and attribute extractions
    brand: Optional[str] = Field(None, description="Extracted or provided brand (e.g., Apple, Dell, Casio)")
    primary_color: Optional[str] = Field(None, description="Dominant color name")
    secondary_color: Optional[str] = Field(None, description="Secondary color name")
    distinguishing_features: Optional[List[str]] = Field(default_factory=list, description="Unique stickers, scratches, markings")
    
    # Secret verification challenge (for ownership proof)
    secret_verification_question: Optional[str] = Field(None, description="Challenge prompt, e.g., 'What sticker is on the laptop lid?'")
    secret_verification_answer: Optional[str] = Field(None, description="Hidden ground truth answer for claim verification")

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v: str) -> str:
        norm = v.strip().lower()
        if norm not in ("lost", "found"):
            raise ValueError("item_type must be either 'lost' or 'found'")
        return norm

class ItemCreate(ItemBase):
    image_url: Optional[str] = Field(None, description="Path or URL to item image")

class ItemResponse(ItemBase):
    id: int
    image_url: Optional[str] = None
    created_at: str
    status: str = "active" # active, matched, claimed, returned
    vision_features_extracted: bool = False
    nlp_features_extracted: bool = False

class MatchScoreBreakdown(BaseModel):
    category_score: float
    text_score: float
    vision_score: float
    attribute_score: float
    spatiotemporal_score: float
    overall_confidence: float
    confidence_level: str # 'High', 'Medium', 'Low'
    explanation: str

class MatchCandidate(BaseModel):
    item: ItemResponse
    score_breakdown: MatchScoreBreakdown

class MatchResponse(BaseModel):
    query_item: ItemResponse
    candidates: List[MatchCandidate]
    total_candidates: int

class ClaimCreate(BaseModel):
    item_id: int
    claimant_name: str
    claimant_student_id: str
    claimant_email: str
    claimant_phone: Optional[str] = None
    secret_answer: str
    additional_proof: Optional[str] = None

class ClaimResponse(BaseModel):
    id: int
    item_id: int
    claimant_name: str
    claimant_student_id: str
    claimant_email: str
    claimant_phone: Optional[str] = None
    submitted_at: str
    status: str # 'pending', 'verified', 'rejected', 'handed_over'
    verification_score: float
    verification_passed: bool
    verification_notes: str

class LocationInsight(BaseModel):
    location: str
    lost_count: int
    found_count: int
    total_activity: int
    recovery_rate: float

class CampusStats(BaseModel):
    total_lost: int
    total_found: int
    total_resolved: int
    overall_recovery_rate: float
    top_categories: Dict[str, int]
    location_hotspots: List[LocationInsight]
    recent_activity_count: int

class BenchmarkMetrics(BaseModel):
    dataset_size: int
    num_ground_truth_pairs: int
    top_1_accuracy: float
    top_3_accuracy: float
    top_5_accuracy: float
    mean_reciprocal_rank: float
    precision_at_1: float
    precision_at_3: float
    recall_at_3: float
    avg_inference_latency_ms: float
    evaluation_timestamp: str
