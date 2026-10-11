import pytest
from app.routes.claims import evaluate_claim_proof

def test_claim_exact_secret_match():
    score, passed, notes = evaluate_claim_proof(
        ground_truth_answer="yellow JS sticker",
        claimant_answer="yellow JS sticker",
        distinguishing_features=["github sticker"]
    )
    assert score == 1.0
    assert passed is True
    assert "Exact verification match" in notes

def test_claim_substring_match():
    score, passed, notes = evaluate_claim_proof(
        ground_truth_answer="Alex Chen avatar",
        claimant_answer="Alex Chen",
        distinguishing_features=[]
    )
    assert score >= 0.90
    assert passed is True

def test_claim_semantic_match_with_digits():
    score, passed, notes = evaluate_claim_proof(
        ground_truth_answer="roll number ending in 088",
        claimant_answer="my id ends with 088",
        distinguishing_features=[]
    )
    assert score >= 0.70
    assert passed is True

def test_claim_rejection_on_mismatch():
    score, passed, notes = evaluate_claim_proof(
        ground_truth_answer="Campbell Biology",
        claimant_answer="Organic Chemistry by Klein",
        distinguishing_features=["blue case"]
    )
    assert score < 0.40
    assert passed is False

def test_claim_single_letter_exploit_rejected():
    # Crucial security regression test: single character must never pass ownership verification
    for fake_ans in ["e", "a", "s", "y", "in", "the", "JS"]:
        score, passed, notes = evaluate_claim_proof(
            ground_truth_answer="yellow JS sticker on back lid",
            claimant_answer=fake_ans,
            distinguishing_features=[]
        )
        assert passed is False, f"Failed: '{fake_ans}' erroneously passed verification with score {score}"
        assert score < 0.70

def test_claim_empty_or_punctuation_rejected():
    score, passed, notes = evaluate_claim_proof(
        ground_truth_answer="yellow JS sticker",
        claimant_answer="   ???  ",
        distinguishing_features=[]
    )
    assert score == 0.0
    assert passed is False

def test_claim_full_sentence_containment_match():
    score, passed, notes = evaluate_claim_proof(
        ground_truth_answer="yellow JS sticker",
        claimant_answer="I have a yellow JS sticker next to the logo",
        distinguishing_features=[]
    )
    assert score >= 0.90
    assert passed is True

