import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import uvicorn

if __name__ == "__main__":
    print("=" * 65)
    print("[SERVER] OmniFind AI: Campus Lost & Found Intelligence Platform")
    print("CV: PyTorch CNN + OpenCV HSV + CIELAB K-Means")
    print("NLP: Scikit-Learn TF-IDF + Named Entity Extraction")
    print("3D Experience: Three.js WebGL Spatial Campus Radar")
    print("Claim Verification: Automated Ownership Challenge Assessment")
    print("Web Server URL: http://127.0.0.1:8000")
    print("=" * 65)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
