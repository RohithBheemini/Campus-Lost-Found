import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from app.ml.matcher import match_items

# Ground truth test pairs: (Lost Query, True Matching Found Item, Category)
EVALUATION_PAIRS = [
    {
        "lost": {
            "title": "Lost Space Gray MacBook Pro 14 inch",
            "description": "Left my Apple MacBook Pro M2 in space gray with a GitHub Octocat sticker and python sticker on the front lid. Lost near Central Library 2nd floor reading area.",
            "category": "Electronics & Gadgets",
            "location": "Central Library",
            "date_time": "2026-10-10 14:00",
            "brand": "Apple",
            "primary_color": "Space Gray",
            "distinguishing_features": ["GitHub Octocat sticker", "python sticker"]
        },
        "found": {
            "title": "Found Apple Laptop in Library",
            "description": "Found a dark gray Apple MacBook with coding stickers on the lid in the library study carrels.",
            "category": "Electronics & Gadgets",
            "location": "Central Library",
            "date_time": "2026-10-10 15:30",
            "brand": "Apple",
            "primary_color": "Space Gray",
            "distinguishing_features": ["coding stickers", "github sticker"]
        }
    },
    {
        "lost": {
            "title": "Lost Student Identity Card - Rohith K",
            "description": "Lost my campus ID card in a blue lanyard with student ID 2023CS014 near Tech Hub cafeteria.",
            "category": "ID Cards & Wallets",
            "location": "Tech Hub / Engineering Block",
            "date_time": "2026-10-09 12:15",
            "brand": None,
            "primary_color": "Navy Blue",
            "distinguishing_features": ["blue lanyard", "student ID 2023CS014"]
        },
        "found": {
            "title": "Found Student ID Card with Lanyard",
            "description": "Campus student card found on ground outside engineering lab with blue neck lanyard.",
            "category": "ID Cards & Wallets",
            "location": "Tech Hub / Engineering Block",
            "date_time": "2026-10-09 13:00",
            "brand": None,
            "primary_color": "Navy Blue",
            "distinguishing_features": ["blue lanyard"]
        }
    },
    {
        "lost": {
            "title": "Lost Matte Black Hydro Flask 32oz",
            "description": "Matte black vacuum insulated water bottle with a small dent on the bottom rim and National Parks sticker.",
            "category": "Bottles & Containers",
            "location": "Sports Complex & Gymnasium",
            "date_time": "2026-10-08 17:30",
            "brand": "Hydro Flask",
            "primary_color": "Black",
            "distinguishing_features": ["dent on bottom rim", "national parks sticker"]
        },
        "found": {
            "title": "Black Metal Water Bottle Left at Bleachers",
            "description": "Black Hydro Flask flask found at the basketball bleachers, noticeable dent on base.",
            "category": "Bottles & Containers",
            "location": "Sports Complex & Gymnasium",
            "date_time": "2026-10-08 18:45",
            "brand": "Hydro Flask",
            "primary_color": "Black",
            "distinguishing_features": ["dent on base"]
        }
    },
    {
        "lost": {
            "title": "Lost White Sony WH-1000XM4 Headphones",
            "description": "Over-ear noise cancelling headphones in silver/white with beige hard case, left in Student Union quiet room.",
            "category": "Electronics & Gadgets",
            "location": "Student Center & Union",
            "date_time": "2026-10-09 11:00",
            "brand": "Sony",
            "primary_color": "White",
            "distinguishing_features": ["beige hard case"]
        },
        "found": {
            "title": "Found Sony Wireless Headphones",
            "description": "Silver/white Sony over-ear headphones in zippered carrying case handed to Student Union help desk.",
            "category": "Electronics & Gadgets",
            "location": "Student Center & Union",
            "date_time": "2026-10-09 12:30",
            "brand": "Sony",
            "primary_color": "White",
            "distinguishing_features": ["zippered carrying case"]
        }
    },
    {
        "lost": {
            "title": "Lost Black North Face Recon Backpack",
            "description": "Black nylon backpack containing calculus notebook, casio calculator, and house keys with red carabiner.",
            "category": "Bags & Backpacks",
            "location": "Science Hall",
            "date_time": "2026-10-10 09:30",
            "brand": "North Face",
            "primary_color": "Black",
            "distinguishing_features": ["red carabiner", "casio calculator inside"]
        },
        "found": {
            "title": "Found Backpack in Lecture Hall 101",
            "description": "Black North Face backpack left under row 4 seats in chemistry lecture hall.",
            "category": "Bags & Backpacks",
            "location": "Science Hall",
            "date_time": "2026-10-10 11:00",
            "brand": "North Face",
            "primary_color": "Black",
            "distinguishing_features": ["keychain on side"]
        }
    },
    {
        "lost": {
            "title": "Lost Casio fx-991CW Scientific Calculator",
            "description": "Black Casio calculator with 'RK' scratched on the protective slider cover.",
            "category": "Electronics & Gadgets",
            "location": "Tech Hub / Engineering Block",
            "date_time": "2026-10-07 16:00",
            "brand": "Casio",
            "primary_color": "Black",
            "distinguishing_features": ["scratched initials RK"]
        },
        "found": {
            "title": "Casio Scientific Calculator Found",
            "description": "Scientific engineering calculator found on lab desk with engraved initials.",
            "category": "Electronics & Gadgets",
            "location": "Tech Hub / Engineering Block",
            "date_time": "2026-10-07 17:15",
            "brand": "Casio",
            "primary_color": "Black",
            "distinguishing_features": ["engraved initials"]
        }
    },
    {
        "lost": {
            "title": "Lost Brown Leather Fossil Wallet",
            "description": "Bi-fold dark brown leather wallet containing state driving license and blue bus pass.",
            "category": "ID Cards & Wallets",
            "location": "Campus Cafeteria & Food Court",
            "date_time": "2026-10-10 13:10",
            "brand": "Fossil",
            "primary_color": "Brown",
            "distinguishing_features": ["state driving license inside", "blue bus pass"]
        },
        "found": {
            "title": "Found Men's Brown Leather Wallet",
            "description": "Brown leather wallet turned in to the cafeteria register staff with cards inside.",
            "category": "ID Cards & Wallets",
            "location": "Campus Cafeteria & Food Court",
            "date_time": "2026-10-10 14:00",
            "brand": "Fossil",
            "primary_color": "Brown",
            "distinguishing_features": ["cards inside"]
        }
    },
    {
        "lost": {
            "title": "Lost Honda Bike Key with Red Tag",
            "description": "Single motorcycle key with rubber Honda logo fob and a red gym locker barcode tag.",
            "category": "Keys & Keychains",
            "location": "North Hostels & Dormitories",
            "date_time": "2026-10-06 20:00",
            "brand": None,
            "primary_color": "Crimson Red",
            "distinguishing_features": ["Honda logo fob", "red barcode tag"]
        },
        "found": {
            "title": "Found Motorcycle Key on Pavement",
            "description": "Vehicle key with red tag found along walkway near North Hostels block B.",
            "category": "Keys & Keychains",
            "location": "North Hostels & Dormitories",
            "date_time": "2026-10-06 21:30",
            "brand": None,
            "primary_color": "Crimson Red",
            "distinguishing_features": ["red tag"]
        }
    }
]

# Hard negative distractors to challenge the ranker
DISTRACTORS = [
    {
        "title": "Found Silver Dell XPS 13",
        "description": "Silver Dell Windows laptop with corporate asset tag, no stickers.",
        "category": "Electronics & Gadgets",
        "location": "Central Library",
        "date_time": "2026-10-10 16:00",
        "brand": "Dell",
        "primary_color": "Silver",
        "distinguishing_features": ["asset tag"]
    },
    {
        "title": "Found Blue Milton Water Flask",
        "description": "Dark blue plastic water bottle found at gym.",
        "category": "Bottles & Containers",
        "location": "Sports Complex & Gymnasium",
        "date_time": "2026-10-08 19:00",
        "brand": "Milton",
        "primary_color": "Navy Blue",
        "distinguishing_features": []
    },
    {
        "title": "Found Red Nike Sports Backpack",
        "description": "Bright red Nike gym sack with soccer shoes.",
        "category": "Bags & Backpacks",
        "location": "Sports Complex & Gymnasium",
        "date_time": "2026-10-09 18:00",
        "brand": "Nike",
        "primary_color": "Crimson Red",
        "distinguishing_features": []
    },
    {
        "title": "Found Black Bose QC35 Headphones",
        "description": "Black Bose headphones in black case left at dining table.",
        "category": "Electronics & Gadgets",
        "location": "Campus Cafeteria & Food Court",
        "date_time": "2026-10-09 14:00",
        "brand": "Bose",
        "primary_color": "Black",
        "distinguishing_features": []
    },
    {
        "title": "Found Texas Instruments TI-84 Plus",
        "description": "Graphing calculator with yellow battery cover found in math hall.",
        "category": "Electronics & Gadgets",
        "location": "Science Hall",
        "date_time": "2026-10-07 18:00",
        "brand": "Texas Instruments",
        "primary_color": "Black",
        "distinguishing_features": ["yellow battery cover"]
    }
]

def run_evaluation_benchmark() -> Dict[str, Any]:
    """
    Executes real empirical evaluation across ground-truth pairs and distractor pool.
    Calculates: Top-1, Top-3, Top-5 Accuracy, Precision@K, Recall@K, MRR, and latency.
    """
    start_time = time.time()
    
    # Candidate pool includes all found items from pairs + all distractors
    candidate_pool = [pair["found"] for pair in EVALUATION_PAIRS] + DISTRACTORS
    
    ranks = []
    top1_hits = 0
    top3_hits = 0
    top5_hits = 0
    precision1_sum = 0.0
    precision3_sum = 0.0
    recall3_sum = 0.0
    
    per_item_results = []
    
    for idx, pair in enumerate(EVALUATION_PAIRS):
        query = pair["lost"]
        ground_truth_found = pair["found"]
        
        # Score query against all candidates in pool
        scores = []
        for cand_idx, candidate in enumerate(candidate_pool):
            match_res = match_items(query, candidate)
            is_true_match = (candidate["title"] == ground_truth_found["title"])
            scores.append({
                "candidate_index": cand_idx,
                "title": candidate["title"],
                "score": match_res["overall_confidence"],
                "breakdown": match_res,
                "is_true_match": is_true_match
            })
            
        # Sort candidates descending by confidence score
        scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Find 1-based rank of the true match
        rank = None
        for r, item in enumerate(scores, 1):
            if item["is_true_match"]:
                rank = r
                break
                
        ranks.append(rank)
        
        if rank == 1:
            top1_hits += 1
            precision1_sum += 1.0
        if rank <= 3:
            top3_hits += 1
            precision3_sum += (1.0 / 3.0) # 1 true item in top 3
            recall3_sum += 1.0
        if rank <= 5:
            top5_hits += 1
            
        per_item_results.append({
            "query_title": query["title"],
            "true_match_title": ground_truth_found["title"],
            "rank": rank,
            "top_predicted_title": scores[0]["title"],
            "top_predicted_score": scores[0]["score"],
            "true_match_score": next(s["score"] for s in scores if s["is_true_match"]),
            "explanation": next(s["breakdown"]["explanation"] for s in scores if s["is_true_match"])
        })
        
    num_queries = len(EVALUATION_PAIRS)
    elapsed = time.time() - start_time
    avg_latency_ms = (elapsed / max(num_queries * len(candidate_pool), 1)) * 1000.0
    
    top_1_acc = round(top1_hits / num_queries, 4)
    top_3_acc = round(top3_hits / num_queries, 4)
    top_5_acc = round(top5_hits / num_queries, 4)
    mrr = round(sum(1.0 / r for r in ranks) / num_queries, 4)
    prec_at_1 = round(precision1_sum / num_queries, 4)
    prec_at_3 = round(precision3_sum / num_queries, 4)
    recall_at_3 = round(recall3_sum / num_queries, 4)
    
    return {
        "dataset_size": len(candidate_pool),
        "num_ground_truth_pairs": num_queries,
        "distractors_count": len(DISTRACTORS),
        "top_1_accuracy": top_1_acc,
        "top_3_accuracy": top_3_acc,
        "top_5_accuracy": top_5_acc,
        "mean_reciprocal_rank": mrr,
        "precision_at_1": prec_at_1,
        "precision_at_3": prec_at_3,
        "recall_at_3": recall_at_3,
        "avg_inference_latency_ms": round(avg_latency_ms, 2),
        "evaluation_timestamp": datetime.now().isoformat(),
        "query_details": per_item_results
    }
