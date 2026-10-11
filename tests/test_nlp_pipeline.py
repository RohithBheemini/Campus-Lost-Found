import pytest
from app.ml.nlp import get_nlp_engine

def test_brand_extraction():
    nlp = get_nlp_engine()
    assert nlp.extract_brand("Lost my Apple MacBook Pro 14") == "Apple"
    assert nlp.extract_brand("Found a Dell XPS 13 silver laptop") == "Dell"
    assert nlp.extract_brand("Left my Casio scientific calculator on table") == "Casio"
    assert nlp.extract_brand("Hydro Flask bottle in black color") == "Hydro Flask"
    assert nlp.extract_brand("Generic unbranded water tumbler") is None

def test_color_extraction():
    nlp = get_nlp_engine()
    colors1 = nlp.extract_colors("Lost my space gray laptop with dark black borders")
    assert "Space Gray" in colors1
    assert "Black" in colors1

    colors2 = nlp.extract_colors("Crimson red lanyard with gold keychain")
    assert "Crimson Red" in colors2
    assert "Gold / Yellow" in colors2

def test_category_inference():
    nlp = get_nlp_engine()
    assert nlp.infer_category("Lost my laptop and charger") == "Electronics & Gadgets"
    assert nlp.infer_category("Student ID card with roll number and badge") == "ID Cards & Wallets"
    assert nlp.infer_category("Calculus textbook and spiral notebook") == "Books & Stationery"
    assert nlp.infer_category("Black water flask bottle with straw") == "Bottles & Containers"
    assert nlp.infer_category("Random unknown object") == "Other"

def test_distinguishing_features():
    nlp = get_nlp_engine()
    features = nlp.extract_distinguishing_features("Black laptop with sticker of Pikachu and cracked top corner")
    assert len(features) >= 1
    assert any("sticker" in f.lower() or "cracked" in f.lower() for f in features)

def test_text_similarity():
    nlp = get_nlp_engine()
    sim1 = nlp.compute_text_similarity(
        "Lost my Apple MacBook Pro in space gray with github stickers",
        "Found space gray Apple laptop with stickers"
    )
    assert sim1 > 0.40

    sim2 = nlp.compute_text_similarity(
        "Apple MacBook Pro laptop",
        "Red soccer ball in sports field"
    )
    assert sim2 < 0.20
