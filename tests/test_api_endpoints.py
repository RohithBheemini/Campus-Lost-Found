import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "computer_vision" in data["features"]

def test_get_items():
    res = client.get("/api/items")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    assert len(items) > 0

def test_get_item_detail_and_custody():
    # Fetch first item
    items = client.get("/api/items").json()
    item_id = items[0]["id"]
    res = client.get(f"/api/items/{item_id}")
    assert res.status_code == 200
    detail = res.json()
    assert "item" in detail
    assert "custody_history" in detail
    # Verify secret answer is sanitized
    assert "secret_verification_answer" not in detail["item"]

def test_match_explorer():
    # Get a lost item
    lost_items = client.get("/api/items?item_type=lost").json()
    assert len(lost_items) > 0
    item_id = lost_items[0]["id"]
    res = client.get(f"/api/match/{item_id}")
    assert res.status_code == 200
    data = res.json()
    assert "query_item" in data
    assert "candidates" in data

def test_insights_stats():
    res = client.get("/api/insights/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "total_lost" in stats
    assert "total_found" in stats
    assert "overall_recovery_rate" in stats
    assert "location_hotspots" in stats

def test_evaluation_metrics_endpoint():
    res = client.get("/api/evaluation/metrics")
    assert res.status_code == 200
    bench = res.json()
    assert "top_1_accuracy" in bench
    assert bench["top_1_accuracy"] >= 0.80
    assert "mean_reciprocal_rank" in bench
    assert "avg_inference_latency_ms" in bench

def test_create_and_claim_item_lifecycle():
    # 1. Report a found item
    form_data = {
        "title": "Found Wireless Earbuds in Case",
        "description": "Black Anker Soundcore earbuds left on gym bench",
        "category": "Electronics & Gadgets",
        "location": "Sports Complex & Gymnasium",
        "specific_spot": "Bench 4",
        "date_time": "2026-10-11 12:00",
        "item_type": "found",
        "contact_name": "Gym Coach",
        "contact_email": "coach@campus.edu",
        "brand": "Anker",
        "primary_color": "Black",
        "secret_verification_question": "What model number or brand is printed on the lid?",
        "secret_verification_answer": "Soundcore"
    }
    create_res = client.post("/api/items", data=form_data)
    assert create_res.status_code == 200
    created = create_res.json()
    item_id = created["id"]

    # 2. Submit wrong claim -> should be rejected
    bad_claim = {
        "item_id": item_id,
        "claimant_name": "Intruder",
        "claimant_student_id": "9999",
        "claimant_email": "intruder@campus.edu",
        "secret_answer": "Apple AirPods Pro"
    }
    claim_res1 = client.post("/api/claims", json=bad_claim)
    assert claim_res1.status_code == 200
    data1 = claim_res1.json()
    assert data1["verification_passed"] is False

    # 3. Submit valid claim -> should be verified
    good_claim = {
        "item_id": item_id,
        "claimant_name": "Real Owner",
        "claimant_student_id": "2024CS99",
        "claimant_email": "owner@campus.edu",
        "secret_answer": "Soundcore"
    }
    claim_res2 = client.post("/api/claims", json=good_claim)
    assert claim_res2.status_code == 200
    data2 = claim_res2.json()
    assert data2["verification_passed"] is True
    assert data2["status"] == "verified"

    # 4. Verify item status changed to claimed
    item_check = client.get(f"/api/items/{item_id}").json()
    assert item_check["item"]["status"] == "claimed"

def test_invalid_item_type_rejected():
    form_data = {
        "title": "Invalid Item",
        "description": "Item with illegal type",
        "category": "Electronics & Gadgets",
        "location": "Central Library",
        "date_time": "2026-10-11 12:00",
        "item_type": "stolen", # invalid
        "contact_name": "Test",
        "contact_email": "test@campus.edu"
    }
    res = client.post("/api/items", data=form_data)
    assert res.status_code == 400
    assert "item_type must be either 'lost' or 'found'" in res.json()["detail"]

def test_unsupported_file_extension_rejected():
    form_data = {
        "title": "Item with script upload",
        "description": "Testing rejection of executable/script files",
        "category": "Books & Stationery",
        "location": "Central Library",
        "date_time": "2026-10-11 12:00",
        "item_type": "lost",
        "contact_name": "Test",
        "contact_email": "test@campus.edu"
    }
    # Upload a .sh or .exe file
    files = {"image": ("exploit.sh", b"#!/bin/bash\necho test", "text/x-shellscript")}
    res = client.post("/api/items", data=form_data, files=files)
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]

def test_mark_notification_read_api():
    # 1. Fetch notifications
    notifs = client.get("/api/notifications").json()
    if notifs:
        n_id = notifs[0]["id"]
        res = client.post(f"/api/notifications/{n_id}/read")
        assert res.status_code == 200
        assert res.json()["id"] == n_id

    # 2. Non-existent notification must return 404
    bad_res = client.post("/api/notifications/9999999/read")
    assert bad_res.status_code == 404

