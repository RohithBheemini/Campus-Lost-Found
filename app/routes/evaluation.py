from fastapi import APIRouter
from app.ml.evaluator import run_evaluation_benchmark

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])

@router.get("/metrics")
def get_evaluation_metrics():
    """Triggers real-time evaluation benchmark and returns accuracy, precision@k, and latency."""
    return run_evaluation_benchmark()
