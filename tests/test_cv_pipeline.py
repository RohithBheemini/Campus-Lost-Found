import os
import numpy as np
import pytest
from app.ml.vision import (
    VisualEmbeddingNet,
    get_vision_model,
    closest_color_name,
    extract_dominant_colors,
    compute_hsv_histogram,
    extract_shape_and_texture,
    analyze_image,
    compute_visual_similarity
)

def test_vision_model_forward():
    model = get_vision_model()
    import torch
    dummy_input = torch.randn(2, 3, 128, 128)
    out = model(dummy_input)
    assert out.shape == (2, 128)
    # Check unit norm
    norms = torch.norm(out, p=2, dim=1)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-4)

def test_closest_color_name():
    assert closest_color_name((20, 20, 20)) == "Black"
    assert closest_color_name((245, 245, 245)) == "White"
    assert closest_color_name((75, 75, 80)) == "Space Gray"
    assert closest_color_name((180, 25, 35)) == "Crimson Red"

def test_dominant_colors_extraction():
    # Create synthetic blue image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :] = (100, 40, 20) # BGR for Navy Blue
    dom_colors = extract_dominant_colors(img, k=2)
    assert len(dom_colors) == 2
    assert dom_colors[0][0] in ["Navy Blue", "Royal Blue", "Black"]
    assert dom_colors[0][2] > 0.5 # majority proportion

def test_shape_and_texture():
    img = np.zeros((100, 150, 3), dtype=np.uint8)
    img[20:80, 30:120] = 255 # white rectangle
    res = extract_shape_and_texture(img)
    assert "edge_density" in res
    assert "sharpness" in res
    assert res["aspect_ratio"] == 1.5

def test_analyze_image_ndarray():
    img = np.full((128, 128, 3), 120, dtype=np.uint8)
    profile = analyze_image(img)
    assert "deep_embedding" in profile
    assert len(profile["deep_embedding"]) == 128
    assert "dominant_colors" in profile
    assert "color_histogram" in profile

def test_compute_visual_similarity():
    # Same profile should give similarity ~ 1.0
    img = np.full((128, 128, 3), 75, dtype=np.uint8)
    p1 = analyze_image(img)
    p2 = analyze_image(img)
    sim = compute_visual_similarity(p1, p2)
    assert sim >= 0.85

    # Completely different image (e.g. black vs bright red)
    red_img = np.zeros((128, 128, 3), dtype=np.uint8)
    red_img[:, :, 2] = 240 # Red in BGR
    p_red = analyze_image(red_img)
    sim_diff = compute_visual_similarity(p1, p_red)
    assert sim_diff < sim

def test_analyze_tiny_and_multichannel_images():
    from PIL import Image
    # 1x1 image (used to crash K-Means with IndexError)
    tiny_img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    prof_tiny = analyze_image(tiny_img)
    assert "deep_embedding" in prof_tiny
    assert len(prof_tiny["deep_embedding"]) == 128
    assert prof_tiny["primary_color"] == "Crimson Red"

    # RGBA image with alpha transparency
    rgba_img = Image.new("RGBA", (64, 64), color=(0, 0, 255, 128))
    prof_rgba = analyze_image(rgba_img)
    assert "dominant_colors" in prof_rgba

    # Grayscale image
    gray_img = Image.new("L", (64, 64), color=200)
    prof_gray = analyze_image(gray_img)
    assert "shape_texture" in prof_gray

