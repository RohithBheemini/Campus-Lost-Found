import pytest
from app.ml.matcher import match_items, compute_spatiotemporal_score, compute_attribute_score

def test_spatiotemporal_score():
    # Same building, 1h apart
    i1 = {"location": "Central Library", "date_time": "2026-10-10 14:00"}
    i2 = {"location": "Central Library", "date_time": "2026-10-10 15:00"}
    score, reason = compute_spatiotemporal_score(i1, i2)
    assert score >= 0.85
    assert "Identical campus location" in reason

    # Different campus buildings (Library vs Sports Complex)
    i3 = {"location": "Sports Complex & Gymnasium", "date_time": "2026-10-10 14:00"}
    score_far, _ = compute_spatiotemporal_score(i1, i3)
    assert score_far < score

def test_attribute_score():
    i1 = {
        "brand": "Apple",
        "primary_color": "Space Gray",
        "distinguishing_features": ["GitHub sticker"]
    }
    i2 = {
        "brand": "Apple",
        "primary_color": "Space Gray",
        "distinguishing_features": ["github sticker"]
    }
    score, reasons = compute_attribute_score(i1, i2)
    assert score >= 0.90
    assert any("Matching brand 'Apple'" in r for r in reasons)

    # Incompatible brand
    i_diff = {
        "brand": "Dell",
        "primary_color": "Silver",
        "distinguishing_features": []
    }
    score_diff, _ = compute_attribute_score(i1, i_diff)
    assert score_diff < 0.40

def test_matching_gate_cross_category():
    lost_laptop = {
        "title": "Lost MacBook Pro",
        "description": "Space gray laptop",
        "category": "Electronics & Gadgets",
        "location": "Central Library",
        "date_time": "2026-10-10 14:00",
        "brand": "Apple",
        "primary_color": "Space Gray"
    }
    found_keys = {
        "title": "Found Bike Keys",
        "description": "Keys with red tag",
        "category": "Keys & Keychains",
        "location": "Central Library",
        "date_time": "2026-10-10 14:30",
        "primary_color": "Crimson Red"
    }
    res = match_items(lost_laptop, found_keys)
    # Category gate must suppress confidence
    assert res["overall_confidence"] < 0.35
    assert res["confidence_level"] == "Low"

def test_matching_high_confidence_pair():
    lost_mac = {
        "title": "Lost Space Gray MacBook Pro 14",
        "description": "Apple laptop with github sticker on lid",
        "category": "Electronics & Gadgets",
        "location": "Central Library",
        "date_time": "2026-10-10 14:00",
        "brand": "Apple",
        "primary_color": "Space Gray",
        "distinguishing_features": ["github sticker"]
    }
    found_mac = {
        "title": "Found Apple MacBook in Library",
        "description": "Space gray Apple laptop with github stickers on lid",
        "category": "Electronics & Gadgets",
        "location": "Central Library",
        "date_time": "2026-10-10 15:00",
        "brand": "Apple",
        "primary_color": "Space Gray",
        "distinguishing_features": ["github sticker"]
    }
    res = match_items(lost_mac, found_mac)
    assert res["overall_confidence"] >= 0.75
    assert res["confidence_level"] == "High"
    assert "Overall AI confidence" in res["explanation"]

def test_category_case_insensitivity():
    # Category case and whitespace must not break matching
    lost = {
        "title": "Lost Laptop",
        "category": "Electronics & Gadgets",
        "location": "Central Library",
        "date_time": "2026-10-10 14:00"
    }
    found = {
        "title": "Found Laptop",
        "category": "  electronics & gadgets  ",
        "location": "Central Library",
        "date_time": "2026-10-10 14:30"
    }
    res = match_items(lost, found)
    assert res["category_score"] == 1.0
    assert res["overall_confidence"] >= 0.50

def test_spatiotemporal_unlisted_distinct_locations():
    # Two distinct unlisted locations must NOT collapse to 0m distance
    i1 = {"location": "Auditorium Main Gate", "date_time": "2026-10-10 14:00"}
    i2 = {"location": "Chemistry Research Lab 3", "date_time": "2026-10-10 14:00"}
    score, reason = compute_spatiotemporal_score(i1, i2)
    assert "Different campus zones" in reason
    assert "Identical" not in reason
    assert score <= 0.55

    # But two identical unlisted locations must match
    i3 = {"location": "Auditorium Main Gate", "date_time": "2026-10-10 14:00"}
    score_same, reason_same = compute_spatiotemporal_score(i1, i3)
    assert "Identical campus location" in reason_same
    assert score_same >= 0.90

def test_brand_canonical_alias_matching():
    # Sub-brand/alias (MacBook Pro vs Apple)
    i1 = {"brand": "MacBook Pro"}
    i2 = {"brand": "Apple"}
    score, reasons = compute_attribute_score(i1, i2)
    assert score >= 0.80
    assert any("Matching brand" in r for r in reasons)

    # Hydroflask vs Hydro Flask
    i3 = {"brand": "Hydroflask"}
    i4 = {"brand": "Hydro Flask"}
    score2, _ = compute_attribute_score(i3, i4)
    assert score2 >= 0.80

