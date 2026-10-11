import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "app" / "static" / "uploads"
SAMPLE_IMG_DIR = BASE_DIR / "app" / "static" / "sample_images"
DB_PATH = DATA_DIR / "campus_lost_found.db"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SAMPLE_IMG_DIR, exist_ok=True)

# Campus Locations with 3D coordinates (x, z) on the campus plane
CAMPUS_LOCATIONS = {
    "Central Library": {"x": -25, "z": -20, "zone": "Academic", "color": "#3b82f6"},
    "Tech Hub / Engineering Block": {"x": 25, "z": -25, "zone": "Engineering", "color": "#0284c7"},
    "Science Hall": {"x": 40, "z": 10, "zone": "Sciences", "color": "#10b981"},
    "Student Center & Union": {"x": 0, "z": 0, "zone": "Student Life", "color": "#f59e0b"},
    "Campus Cafeteria & Food Court": {"x": -35, "z": 15, "zone": "Dining", "color": "#ef4444"},
    "Sports Complex & Gymnasium": {"x": -20, "z": 45, "zone": "Recreation", "color": "#06b6d4"},
    "North Hostels & Dormitories": {"x": 30, "z": 40, "zone": "Residential", "color": "#ec4899"},
}

ITEM_CATEGORIES = [
    "Electronics & Gadgets",
    "ID Cards & Wallets",
    "Books & Stationery",
    "Bags & Backpacks",
    "Personal Accessories",
    "Keys & Keychains",
    "Clothing & Wearables",
    "Bottles & Containers",
    "Other",
]

# Multi-modal matching weights
WEIGHT_CATEGORY = 0.25
WEIGHT_TEXT = 0.25
WEIGHT_VISION = 0.25
WEIGHT_ATTRIBUTES = 0.15
WEIGHT_SPATIOTEMPORAL = 0.10

HIGH_CONFIDENCE_THRESHOLD = 0.75
MEDIUM_CONFIDENCE_THRESHOLD = 0.50
