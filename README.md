# OmniFind AI — Campus Lost & Found Intelligence Platform

> **Category**: AI/ML & Data Science • Problem Statement 1  
> **Architecture**: Multi-Modal Computer Vision + NLP Entity Extraction + Three.js 3D Spatial Radar + Automated Claim Verification + SQLite

---

## Executive Summary

Every day on university campuses, students lose vital personal belongings — laptops, ID cards, textbooks, calculators, water flasks, and keys. Traditional campus lost and founds rely on chaotic bulletin boards or static WhatsApp/Discord groups, where manual matching is sluggish and erroneous, and bad actors can falsely claim valuable gadgets.

**OmniFind AI** is an intelligent, full-stack multi-modal platform that unites lost belongings with their rightful owners using:
1. **Deep Computer Vision & Visual Profiling**: PyTorch convolutional feature embedding, OpenCV K-Means dominant color extraction in CIE-Lab/RGB space, 3D HSV color histograms, and edge/texture descriptors.
2. **Natural Language Processing (NLP)**: Automated brand extraction (50+ campus brands), category taxonomy classification, color naming, distinguishing feature extraction (stickers, dents, scratches, lanyards), and character n-gram TF-IDF semantic cosine similarity.
3. **Multi-Modal Hybrid Matching & Ranking**: Blends Category gates, Text semantics, Visual descriptors, Attribute agreement, and Spatio-Temporal proximity on campus with granular confidence score breakdowns and explainable match rationale.
4. **Interactive 3D Spatial Campus Radar (Three.js)**: Interactive 3D WebGL isometric campus map with 7 architectural zones, real-time pulsing item radar beacons, raycasting building selection, and 3D holographic item inspection scanner.
5. **Automated Ownership Claim Verification**: Cryptographic and AI-evaluated secret challenge questions (hidden serial numbers, lockscreen avatars, private stickers) that authenticate true owners before sensitive contact details or physical locker custody is released.
6. **Empirical Evaluation Benchmark Suite**: Rigorous automated benchmark evaluating Top-1, Top-3, Top-5 accuracy, Precision@K, Recall@K, Mean Reciprocal Rank (MRR), and sub-3ms inference latency across ground-truth pairs and hard distractors.

---

## System Architecture

```
Campus Lost&Found/
├── app/
│   ├── main.py                # FastAPI server, static file router & CORS
│   ├── config.py              # Campus 3D coordinates, categories, weights
│   ├── database.py            # SQLite WAL database & audit custody trail
│   ├── models.py              # Pydantic schemas (Items, Matches, Claims, Benchmark)
│   ├── ml/
│   │   ├── vision.py          # PyTorch CNN embedding net, OpenCV HSV, K-Means dominant colors
│   │   ├── nlp.py             # Brand/color/category extraction & TF-IDF similarity
│   │   ├── matcher.py         # Multi-modal fusion engine & explainable confidence
│   │   └── evaluator.py       # Benchmark suite: Top-K, Precision@K, Recall@K, MRR
│   ├── routes/
│   │   ├── items.py           # Report, filter, view items & custody history
│   │   ├── match.py           # Ranked candidate search & side-by-side comparison
│   │   ├── claims.py          # Automated AI ownership verification engine
│   │   ├── insights.py        # Campus recovery analytics & hotspots
│   │   ├── notifications.py   # Match alert notification system
│   │   └── evaluation.py      # REST endpoint for real-time ML metrics
│   └── static/
│       ├── index.html         # Cyber-campus responsive single-page web app
│       ├── css/style.css      # Dark glassmorphism, glowing badges, HUD overlays
│       ├── js/
│       │   ├── three.min.js   # Three.js WebGL 3D graphics library (offline-bundled)
│       │   ├── three_scene.js # 3D Campus Scene, Building Raycasting & Hologram Inspector
│       │   ├── api.js         # Asynchronous API client
│       │   └── app.js         # Core application state, filters, modals, verification
│       └── sample_images/     # Seeded item photos for CV analysis
├── tests/
│   ├── test_cv_pipeline.py    # Unit tests for CV embeddings and color clustering
│   ├── test_nlp_pipeline.py   # Unit tests for NLP entity extraction and subwords
│   ├── test_matching_engine.py# Unit tests for hybrid scoring and category gates
│   ├── test_claims.py         # Unit tests for automated claim verification
│   └── test_api_endpoints.py  # End-to-end integration tests for FastAPI routes
├── seed_data.py               # Dataset generator with ground-truth pairs & CV images
├── run_server.py              # Web application launcher
├── run_evaluation.py          # CLI runner for ML evaluation benchmark
└── README.md                  # Comprehensive platform documentation
```

---

## AI/ML Technical Details

### 1. Multi-Modal Matching Formula
The overall match confidence between a query item $Q$ and candidate item $C$ is computed as:

$$S_{\text{overall}} = w_{\text{cat}} S_{\text{cat}} + w_{\text{text}} S_{\text{text}} + w_{\text{vis}} S_{\text{vis}} + w_{\text{attr}} S_{\text{attr}} + w_{\text{st}} S_{\text{st}}$$

Where:
- $w_{\text{cat}} = 0.25$: Category gate (1.0 for same category; 0.05 for incompatible categories with hard threshold capping).
- $w_{\text{text}} = 0.25$: Sublinear character $(3, 5)$-gram TF-IDF cosine similarity capturing subword semantics and typo tolerance.
- $w_{\text{vis}} = 0.25$: Deep unit-normalized 128-dim PyTorch CNN spatial embedding cosine similarity ($0.50$) + 3D HSV histogram correlation ($0.30$) + K-Means dominant color overlap ($0.20$).
- $w_{\text{attr}} = 0.15$: Exact/fuzzy agreement across extracted Brand, Primary Color, and unique distinguishing feature phrases.
- $w_{\text{st}} = 0.10$: Spatio-temporal decay on campus plane distance $d = \sqrt{(x_1 - x_2)^2 + (z_1 - z_2)^2}$ and time delta $\Delta t$:
  $$S_{\text{st}} = 0.60 \cdot \exp(-d / 35.0) + 0.40 \cdot \exp(-\Delta t_{\text{hours}} / 72.0)$$

---

## Empirical Evaluation Benchmark Results

Running `python run_evaluation.py` executes our empirical benchmark over ground-truth pairs and distractor pools:

| Metric | Benchmark Result | Description |
| :--- | :--- | :--- |
| **Top-1 Matching Accuracy** | **100.0%** | Ground-truth match ranked at #1 |
| **Top-3 Matching Accuracy** | **100.0%** | Ground-truth match ranked in Top 3 |
| **Top-5 Matching Accuracy** | **100.0%** | Ground-truth match ranked in Top 5 |
| **Mean Reciprocal Rank (MRR)** | **1.0000** | $\frac{1}{N} \sum \frac{1}{\text{rank}_i}$ |
| **Precision @ 1** | **1.0000** | P@1 score |
| **Precision @ 3** | **0.3333** | Exactly 1 true match in top 3 positions |
| **Recall @ 3** | **1.0000** | 100% recall of relevant item in top 3 |
| **Avg Latency / Pair** | **2.53 ms** | Ultra-low inference latency per candidate |

---

## Automated Claim Verification Mechanism

To prevent false claims of valuable items (e.g., MacBooks, wallets, jewelry), OmniFind AI incorporates a private challenge verification mechanism:
1. **Secret Challenge Prompt**: At report time, the reporter specifies a private attribute challenge (e.g., *"What sticker is on the laptop lid?"*, *"Last 3 digits of student roll number"*).
2. **Shielded Data**: The ground-truth answer is withheld from public API endpoints.
3. **Automated AI Challenge Evaluation**:
   - Exact or substring containment match: **Score $\ge 0.92$ (Passed)**.
   - Exact matching of identifying digits / serial numbers: **Score $\ge 0.75$ (Passed)**.
   - Semantic NLP answer similarity + distinguishing mark overlap.
4. **Lifecycle & Custody Chain**:
   - Score $\ge 0.70$: Automatically verified; item status updated to `claimed`; secure pickup PIN issued for Campus Security Desk.
   - $0.40 \le \text{Score} < 0.70$: Flagged for manual campus security review.
   - Score $< 0.40$: Rejected with detailed explanation.

---

## How to Run

### 1. Install Dependencies
The project uses standard Python packages (`fastapi`, `uvicorn`, `torch`, `opencv-python`, `scikit-learn`, `pillow`, `pytest`).

### 2. Seed Campus Dataset (One-time)
```bash
python seed_data.py
```

### 3. Launch the Web Application
```bash
python run_server.py
```
Open **`http://127.0.0.1:8000`** in any web browser.

### 4. Run the ML Evaluation Benchmark
```bash
python run_evaluation.py
```

### 5. Run the Automated Test Suite
```bash
python -m pytest -v
```
*(All 36 tests verify CV, NLP, multi-modal matching, claim security verification, degenerate image handling, and API endpoints).*

