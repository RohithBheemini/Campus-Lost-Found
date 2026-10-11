import sys
import json

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.ml.evaluator import run_evaluation_benchmark

def main():
    print("=" * 70)
    print("[AI BENCHMARK] Running OmniFind AI Evaluation Suite")
    print("=" * 70)
    
    results = run_evaluation_benchmark()
    
    print(f"Dataset Size:               {results['dataset_size']} items")
    print(f"Ground Truth Query Pairs:   {results['num_ground_truth_pairs']} pairs")
    print(f"Distractor Pool:            {results['distractors_count']} items")
    print("-" * 70)
    print(f"Top-1 Accuracy:             {results['top_1_accuracy'] * 100:.1f}%")
    print(f"Top-3 Accuracy:             {results['top_3_accuracy'] * 100:.1f}%")
    print(f"Top-5 Accuracy:             {results['top_5_accuracy'] * 100:.1f}%")
    print(f"Mean Reciprocal Rank (MRR): {results['mean_reciprocal_rank']:.4f}")
    print(f"Precision @ 1:              {results['precision_at_1']:.4f}")
    print(f"Precision @ 3:              {results['precision_at_3']:.4f}")
    print(f"Recall @ 3:                 {results['recall_at_3']:.4f}")
    print(f"Avg Inference Latency/Pair: {results['avg_inference_latency_ms']:.2f} ms")
    print("-" * 70)
    print("Query Level Results:")
    for idx, q in enumerate(results["query_details"], 1):
        print(f"  [{idx}] Query: {q['query_title']}")
        print(f"      Matched: {q['true_match_title']} (Rank #{q['rank']}, Score: {int(q['true_match_score'] * 100)}%)")
        print(f"      Reason:  {q['explanation']}")
    print("=" * 70)

if __name__ == "__main__":
    main()
