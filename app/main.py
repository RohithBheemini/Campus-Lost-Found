import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.database import init_db
from app.config import BASE_DIR, UPLOAD_DIR, SAMPLE_IMG_DIR
from app.routes.items import router as items_router
from app.routes.match import router as match_router
from app.routes.claims import router as claims_router
from app.routes.insights import router as insights_router
from app.routes.notifications import router as notifications_router
from app.routes.evaluation import router as evaluation_router

# Initialize database
init_db()

app = FastAPI(
    title="Campus Lost & Found Intelligence Platform",
    description="AI-powered platform for multi-modal matching of lost and found items with computer vision, NLP, 3D spatial campus radar, and automated claim verification.",
    version="1.0.0"
)

# CORS middleware for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(items_router)
app.include_router(match_router)
app.include_router(claims_router)
app.include_router(insights_router)
app.include_router(notifications_router)
app.include_router(evaluation_router)

# Mount static files
static_dir = BASE_DIR / "app" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def serve_index():
    index_file = static_dir / "index.html"
    return FileResponse(str(index_file))

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "Campus Lost & Found Intelligence",
        "version": "1.0.0",
        "features": {
            "computer_vision": "active (PyTorch CNN + OpenCV HSV + CIELAB K-Means)",
            "nlp_analysis": "active (Scikit-Learn TF-IDF + Named Entity Extraction)",
            "3d_radar": "active (Three.js WebGL)",
            "claim_verification": "active (Automated Challenge Assessment)"
        }
    }
