import os
import math
import numpy as np
import cv2
import torch
import torch.nn as nn
from PIL import Image
from typing import Dict, Any, List, Tuple, Optional

# Color reference palette in RGB and named equivalents
NAMED_COLORS = {
    "Black": (20, 20, 20),
    "White": (245, 245, 245),
    "Space Gray": (75, 75, 80),
    "Silver": (192, 192, 198),
    "Navy Blue": (20, 40, 100),
    "Royal Blue": (30, 90, 200),
    "Sky Blue": (110, 180, 240),
    "Crimson Red": (180, 25, 35),
    "Maroon / Burgundy": (115, 20, 35),
    "Forest Green": (25, 105, 45),
    "Lime Green": (80, 190, 60),
    "Gold / Yellow": (230, 190, 40),
    "Orange": (235, 115, 30),
    "Purple": (120, 45, 160),
    "Pink": (230, 110, 160),
    "Brown": (110, 65, 40),
}

class VisualEmbeddingNet(nn.Module):
    """
    Lightweight Deep Convolutional Vision Feature Extractor.
    Extracts high-level spatial visual representations projected into a 128-dim unit sphere.
    """
    def __init__(self, embedding_dim: int = 128):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((2, 2))
        )
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 2 * 2, embedding_dim)
        )
        
        # Initialize deterministic weights for reproducible feature representation
        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
        self.eval()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            feat = self.features(x)
            emb = self.fc(feat)
            norm = emb.norm(p=2, dim=1, keepdim=True).clamp(min=1e-8)
            return emb / norm

# Global singleton model for low-latency inference
_model = None

def get_vision_model():
    global _model
    if _model is None:
        _model = VisualEmbeddingNet(embedding_dim=128)
        _model.eval()
    return _model

def closest_color_name(rgb: Tuple[int, int, int]) -> str:
    """Find the closest human-recognizable color using Euclidean RGB distance."""
    r, g, b = rgb
    min_dist = float("inf")
    closest = "Black"
    for name, (cr, cg, cb) in NAMED_COLORS.items():
        dist = math.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
        if dist < min_dist:
            min_dist = dist
            closest = name
    return closest

def extract_dominant_colors(image_bgr: np.ndarray, k: int = 3) -> List[Tuple[str, List[int], float]]:
    """
    Extract top-k dominant colors using K-Means clustering.
    Returns: List of (ColorName, [R, G, B], proportion)
    """
    if image_bgr is None or image_bgr.size == 0:
        return [("Unknown", [128, 128, 128], 1.0)]

    h, w = image_bgr.shape[:2]
    if h == 0 or w == 0:
        return [("Unknown", [128, 128, 128], 1.0)]

    # Downsample for rapid clustering
    scale = min(128.0 / max(h, 1), 128.0 / max(w, 1), 1.0)
    resized = cv2.resize(image_bgr, (max(1, int(w * scale)), max(1, int(h * scale))))
    
    if resized.ndim == 2:
        rgb = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)
    elif resized.ndim == 3 and resized.shape[2] == 4:
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGRA2RGB)
    else:
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
    pixels = rgb.reshape(-1, 3).astype(np.float32)

    # If image has fewer pixels than requested clusters, return direct average
    if len(pixels) < k:
        mean_rgb = np.mean(pixels, axis=0).astype(int).tolist()
        name = closest_color_name((mean_rgb[0], mean_rgb[1], mean_rgb[2]))
        return [(name, mean_rgb, 1.0)]

    # Filter out extreme bright or pure white background if needed
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 0.2)
    try:
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 5, cv2.KMEANS_PP_CENTERS)
        counts = np.bincount(labels.flatten(), minlength=k)
        total = float(len(labels))
        proportions = counts / total

        # Sort descending by frequency
        sorted_indices = np.argsort(-proportions)
        results = []
        for idx in sorted_indices:
            c_rgb = centers[idx].astype(int).tolist()
            name = closest_color_name((c_rgb[0], c_rgb[1], c_rgb[2]))
            results.append((name, c_rgb, float(proportions[idx])))

        return results if results else [("Unknown", [128, 128, 128], 1.0)]
    except Exception:
        mean_rgb = np.mean(pixels, axis=0).astype(int).tolist()
        name = closest_color_name((mean_rgb[0], mean_rgb[1], mean_rgb[2]))
        return [(name, mean_rgb, 1.0)]

def compute_hsv_histogram(image_bgr: np.ndarray) -> np.ndarray:
    """
    Compute 3D HSV color histogram normalized to unit sum.
    Bins: 16 Hue, 8 Saturation, 8 Value.
    """
    if image_bgr is None or image_bgr.size == 0 or image_bgr.shape[0] < 1 or image_bgr.shape[1] < 1:
        return np.zeros(16 * 8 * 8, dtype=np.float32)

    if image_bgr.ndim == 2:
        img_3ch = cv2.cvtColor(image_bgr, cv2.COLOR_GRAY2BGR)
    elif image_bgr.ndim == 3 and image_bgr.shape[2] == 4:
        img_3ch = cv2.cvtColor(image_bgr, cv2.COLOR_BGRA2BGR)
    else:
        img_3ch = image_bgr

    hsv = cv2.cvtColor(img_3ch, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1, 2], None, [16, 8, 8], [0, 180, 0, 256, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()
    return hist

def extract_shape_and_texture(image_bgr: np.ndarray) -> Dict[str, Any]:
    """Extract edge density, sharpness/variance, and contour aspect ratio."""
    if image_bgr is None or image_bgr.size == 0 or image_bgr.shape[0] < 2 or image_bgr.shape[1] < 2:
        return {"edge_density": 0.0, "sharpness": 0.0, "aspect_ratio": 1.0}

    if image_bgr.ndim == 2:
        gray = image_bgr
    elif image_bgr.ndim == 3 and image_bgr.shape[2] == 4:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGRA2GRAY)
    else:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.count_nonzero(edges) / max(edges.size, 1))
    
    # Laplacian variance (sharpness)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    h, w = gray.shape[:2]
    aspect_ratio = round(float(w) / max(float(h), 1.0), 2)
    
    return {
        "edge_density": round(edge_density, 3),
        "sharpness": round(laplacian_var, 1),
        "aspect_ratio": aspect_ratio
    }

def analyze_image(image_input) -> Dict[str, Any]:
    """
    Full CV Analysis Pipeline:
    Accepts file path (str) or cv2 ndarray or PIL Image.
    Returns visual profile: deep embedding, dominant colors, histogram, shape/texture.
    """
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"Image not found at {image_input}")
        image_bgr = cv2.imread(image_input)
        if image_bgr is None:
            raise ValueError(f"Failed to decode image from {image_input}")
    elif isinstance(image_input, Image.Image):
        # Convert PIL mode safely
        rgb_img = image_input.convert("RGB")
        rgb_arr = np.array(rgb_img)
        image_bgr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
    elif isinstance(image_input, np.ndarray):
        if image_input.ndim == 2:
            image_bgr = cv2.cvtColor(image_input, cv2.COLOR_GRAY2BGR)
        elif image_input.ndim == 3 and image_input.shape[2] == 4:
            image_bgr = cv2.cvtColor(image_input, cv2.COLOR_BGRA2BGR)
        else:
            image_bgr = image_input
    else:
        raise TypeError("Unsupported image input type")

    h, w = image_bgr.shape[:2]
    if h == 0 or w == 0:
        raise ValueError("Image has 0 dimensions")
    
    # 1. Dominant colors
    dom_colors = extract_dominant_colors(image_bgr, k=3)
    primary_color = dom_colors[0][0] if dom_colors else "Unknown"
    secondary_color = dom_colors[1][0] if len(dom_colors) > 1 else None

    # 2. Shape and texture
    shape_tex = extract_shape_and_texture(image_bgr)

    # 3. Deep CNN embedding
    img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    img_tensor = cv2.resize(img_rgb, (128, 128)).astype(np.float32) / 255.0
    # Normalize with standard mean/std
    img_tensor = (img_tensor - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
    tensor_input = torch.tensor(img_tensor.transpose(2, 0, 1), dtype=torch.float32).unsqueeze(0)

    model = get_vision_model()
    with torch.no_grad():
        embedding_vec = model(tensor_input).squeeze(0).cpu().numpy().tolist()

    # 4. Color histogram
    hsv_hist = compute_hsv_histogram(image_bgr).tolist()

    return {
        "deep_embedding": embedding_vec,
        "dominant_colors": [c[0] for c in dom_colors],
        "dominant_rgb": [c[1] for c in dom_colors],
        "dominant_proportions": [round(c[2], 3) for c in dom_colors],
        "primary_color": primary_color,
        "secondary_color": secondary_color,
        "shape_texture": shape_tex,
        "color_histogram": hsv_hist,
    }

def compute_visual_similarity(feat1: Dict[str, Any], feat2: Dict[str, Any]) -> float:
    """
    Computes visual similarity between two item profiles:
    - Deep embedding cosine similarity (weight: 0.50)
    - Color histogram intersection (weight: 0.30)
    - Dominant color overlap (weight: 0.20)
    """
    if not feat1 or not feat2:
        return 0.0

    scores = []
    
    # 1. Deep embedding cosine similarity
    emb1 = np.array(feat1.get("deep_embedding", []), dtype=np.float32)
    emb2 = np.array(feat2.get("deep_embedding", []), dtype=np.float32)
    if len(emb1) > 0 and len(emb2) > 0 and len(emb1) == len(emb2):
        dot = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 > 0 and norm2 > 0:
            cos_sim = float(dot / (norm1 * norm2))
            # Map [-1, 1] to [0, 1]
            deep_score = max(0.0, min(1.0, (cos_sim + 1.0) / 2.0))
            scores.append((deep_score, 0.50))

    # 2. Color histogram correlation
    hist1 = np.array(feat1.get("color_histogram", []), dtype=np.float32)
    hist2 = np.array(feat2.get("color_histogram", []), dtype=np.float32)
    if len(hist1) > 0 and len(hist2) > 0 and len(hist1) == len(hist2):
        corr = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        hist_score = max(0.0, min(1.0, (corr + 1.0) / 2.0))
        scores.append((hist_score, 0.30))

    # 3. Dominant color match bonus
    c1 = set(feat1.get("dominant_colors", [])[:2])
    c2 = set(feat2.get("dominant_colors", [])[:2])
    if c1 and c2:
        overlap = len(c1.intersection(c2))
        color_score = 1.0 if overlap >= 2 else (0.75 if overlap == 1 else 0.15)
        scores.append((color_score, 0.20))

    if not scores:
        return 0.0

    total_weight = sum(w for _, w in scores)
    weighted_sum = sum(s * w for s, w in scores)
    return round(float(weighted_sum / total_weight), 4)
