from fastapi import APIRouter
from app.config import CAMPUS_LOCATIONS
from app.database import list_items
from app.models import CampusStats, LocationInsight

router = APIRouter(prefix="/api/insights", tags=["insights"])

@router.get("/stats", response_model=CampusStats)
def get_campus_stats():
    all_items = list_items(limit=1000)
    
    total_lost = sum(1 for i in all_items if i["item_type"] == "lost")
    total_found = sum(1 for i in all_items if i["item_type"] == "found")
    total_resolved = sum(1 for i in all_items if i["status"] in ("claimed", "returned"))
    
    overall_recovery_rate = round((total_resolved / max(total_lost + total_found, 1)) * 100.0, 1)

    # Category counts
    category_counts = {}
    for item in all_items:
        cat = item.get("category", "Other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Location hotspots
    location_map = {}
    for loc_name in CAMPUS_LOCATIONS.keys():
        location_map[loc_name] = {"lost": 0, "found": 0, "resolved": 0}
        
    for item in all_items:
        loc = item.get("location", "")
        if loc in location_map:
            if item["item_type"] == "lost":
                location_map[loc]["lost"] += 1
            else:
                location_map[loc]["found"] += 1
            if item["status"] in ("claimed", "returned"):
                location_map[loc]["resolved"] += 1

    hotspots = []
    for loc, stats in location_map.items():
        total_act = stats["lost"] + stats["found"]
        rate = round((stats["resolved"] / max(total_act, 1)) * 100.0, 1)
        hotspots.append(
            LocationInsight(
                location=loc,
                lost_count=stats["lost"],
                found_count=stats["found"],
                total_activity=total_act,
                recovery_rate=rate
            )
        )

    # Sort hotspots descending by activity
    hotspots.sort(key=lambda x: x.total_activity, reverse=True)

    return CampusStats(
        total_lost=total_lost,
        total_found=total_found,
        total_resolved=total_resolved,
        overall_recovery_rate=overall_recovery_rate,
        top_categories=category_counts,
        location_hotspots=hotspots,
        recent_activity_count=len(all_items)
    )
