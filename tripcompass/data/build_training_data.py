import numpy as np
import pandas as pd

np.random.seed(42)

POI_CSV = "tripcompass/data/pois_sf_enriched.csv"   # enriched POIs
N_USERS = 30

PACES = ["slow", "moderate", "fast"]
INTEREST_DIMENSIONS = [
    "food",
    "museums",
    "outdoors",
    "parks",
    "shopping",
    "nightlife",
    "culture",
]

# -------------------------
# LOAD POIs
# -------------------------
pois = pd.read_csv(POI_CSV)
print("Loaded POIs:", pois.shape)

# -------------------------
# USER PROFILES
# -------------------------
def generate_user_profiles(n_users: int) -> pd.DataFrame:
    profiles = []
    for user_id in range(n_users):
        interests = {dim: np.round(np.random.uniform(0.0, 1.0), 2)
                     for dim in INTEREST_DIMENSIONS}

        pace = np.random.choice(PACES)
        days = int(np.random.randint(2, 6))   # 2–5 days
        budget = int(np.random.randint(300, 1201))  # $300–$1200

        # SF-ish hotel location
        hotel_lat = 37.7749 + np.random.normal(0, 0.01)
        hotel_lon = -122.4194 + np.random.normal(0, 0.01)

        profile = {
            "user_id": user_id,
            "pace": pace,
            "days": days,
            "budget": budget,
            "hotel_lat": hotel_lat,
            "hotel_lon": hotel_lon,
        }
        for dim in INTEREST_DIMENSIONS:
            profile[f"interest_{dim}"] = interests[dim]

        profiles.append(profile)

    return pd.DataFrame(profiles)


user_profiles = generate_user_profiles(N_USERS)
user_profiles.to_csv("user_profiles.csv", index=False)
print("✅ Saved user_profiles.csv with", len(user_profiles), "users")

# -------------------------
# FEATURE HELPERS
# -------------------------
def pace_fit(pace: str, duration_hours: float) -> float:
    """Simple heuristic for pace compatibility [0,1]."""
    if pace == "fast":
        if duration_hours <= 1.5:
            return 1.0
        elif duration_hours <= 3.0:
            return 0.6
        else:
            return 0.3
    elif pace == "slow":
        if duration_hours >= 2.0:
            return 1.0
        elif duration_hours >= 1.0:
            return 0.7
        else:
            return 0.4
    else:  # moderate
        if 1.5 <= duration_hours <= 3.0:
            return 1.0
        else:
            return 0.7


def interest_tag_match(user_row, poi_tags: str, poi_category: str = None) -> float:
    """Compute interest–tag match in [0,1] using keyword mapping.
    
    Args:
        user_row: User profile row with interest_* columns
        poi_tags: Comma-separated tags string
        poi_category: POI category (e.g., "restaurant", "museum", "nightlife")
    
    Returns:
        Interest match score [0,1]. Returns 0.0 if user has 0 interest in all matched categories.
    """
    if not isinstance(poi_tags, str):
        poi_tags = ""
    
    tags_lower = poi_tags.lower()
    category_lower = poi_category.lower() if poi_category else ""
    scores = []
    matched_interests = set()

    # Food/Restaurant matching
    if (any(k in tags_lower for k in ["restaurant", "food", "cafe", "diner"]) or 
        category_lower == "restaurant"):
        interest_val = user_row.get("interest_food", 0.0)
        scores.append(interest_val)
        matched_interests.add("food")

    # Museum matching (separate from culture) - handled below with culture fallback
    # This check is now redundant but kept for tag-based matching of non-category museums
    if (any(k in tags_lower for k in ["museum", "gallery"]) and category_lower != "museum"):
        interest_val = user_row.get("interest_museums", 0.0)
        scores.append(interest_val)
        matched_interests.add("museums")

    # Parks/Outdoors matching
    if (any(k in tags_lower for k in ["park", "trail", "beach", "outdoor"]) or 
        category_lower == "park"):
        interest_val_outdoors = user_row.get("interest_outdoors", 0.0)
        interest_val_parks = user_row.get("interest_parks", 0.0)
        scores.append(max(interest_val_outdoors, interest_val_parks))  # Use max of the two
        matched_interests.add("outdoors")
        matched_interests.add("parks")

    # Shopping matching - handled below with culture fallback
    # This check is now redundant but kept for tag-based matching of non-category shopping
    if (any(k in tags_lower for k in ["shopping", "mall", "market", "store"]) and category_lower != "shopping"):
        interest_val = user_row.get("interest_shopping", 0.0)
        scores.append(interest_val)
        matched_interests.add("shopping")

    # Culture matching (theater, concert, performing arts - separate from museums)
    # Also include nightlife venues with music/concert tags as culture venues
    # Check this BEFORE nightlife matching to prioritize culture
    culture_direct_match = False
    is_culture_venue = False
    if (any(k in tags_lower for k in ["theater", "concert", "performing arts", "opera", "jazz", "music", "venue"]) or
        (category_lower == "nightlife" and any(k in tags_lower for k in ["music", "concert", "venue"]))):
        interest_val = user_row.get("interest_culture", 0.0)
        scores.append(interest_val)
        matched_interests.add("culture")
        culture_direct_match = True
        is_culture_venue = True

    # Nightlife matching (only if not already matched as culture venue)
    if not is_culture_venue and ((any(k in tags_lower for k in ["bar", "club", "nightlife", "pub", "dancing", "dj"]) or 
        category_lower == "nightlife")):
        interest_val = user_row.get("interest_nightlife", 0.0)
        scores.append(interest_val)
        matched_interests.add("nightlife")

    # Art matching (for galleries that aren't museums)
    if "art" in tags_lower and "museum" not in tags_lower and category_lower != "museum":
        # Art galleries that aren't museums - match to culture
        interest_val = user_row.get("interest_culture", 0.0)
        scores.append(interest_val)
        matched_interests.add("culture")
        culture_direct_match = True
    
    # Museums: match to interest_museums primarily, but also to culture as fallback
    if category_lower == "museum":
        # Primary match to museums interest
        museum_interest = user_row.get("interest_museums", 0.0)
        if museum_interest > 0.0:
            scores.append(museum_interest)
            matched_interests.add("museums")
        # Fallback to culture interest if culture > 0 and no direct culture match yet
        culture_interest = user_row.get("interest_culture", 0.0)
        if culture_interest > 0.0 and not culture_direct_match:
            scores.append(culture_interest * 0.8)  # Slightly lower weight as fallback
            matched_interests.add("culture")
    
    # Shopping: match to interest_shopping primarily, but also to culture as fallback
    if category_lower == "shopping":
        # Primary match to shopping interest
        shopping_interest = user_row.get("interest_shopping", 0.0)
        if shopping_interest > 0.0:
            scores.append(shopping_interest)
            matched_interests.add("shopping")
        # Fallback to culture interest if culture > 0 and no direct culture match yet
        culture_interest = user_row.get("interest_culture", 0.0)
        if culture_interest > 0.0 and not culture_direct_match:
            scores.append(culture_interest * 0.6)  # Lower weight for shopping as fallback
            matched_interests.add("culture")

    if not scores:
        # No matching tags - return very low score instead of neutral
        return 0.0

    # If user has 0 interest in ALL matched categories, return 0
    if all(user_row.get(f"interest_{interest}", 0.0) == 0.0 for interest in matched_interests):
        return 0.0

    # Return mean of matched interest scores
    return float(np.mean(scores))

# -------------------------
# BUILD USER–POI DATASET
# -------------------------
def build_user_poi_dataset(users_df: pd.DataFrame, pois_df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    popularity_norm = pois_df["popularity"] / pois_df["popularity"].max()
    max_cost = max(pois_df["cost"].max(), 1.0)

    for _, user in users_df.iterrows():
        budget_scale = min(1.0, user["budget"] / 1000.0)

        for poi_idx, poi in pois_df.iterrows():
            match = interest_tag_match(user, poi.get("tags", ""), poi.get("category"))
            pace_score = pace_fit(user["pace"], poi["duration_hours"])
            pop = float(popularity_norm.iloc[poi_idx])
            cost = float(poi["cost"])
            dur = float(poi["duration_hours"])

            cost_norm = cost / max_cost

            # ---------- NEW NONLINEAR SATISFACTION FUNCTION ----------
            base = (
                0.30 * (match ** 1.8) +
                0.20 * np.sqrt(pop + 1e-6) +
                0.15 * (pace_score ** 1.5) +
                0.15 * (match * pace_score) +
                0.10 * (pop * pace_score) +
                0.10 * (match * pop * pace_score)
            )

            cost_term = np.exp(-0.75 * cost_norm)

            sat_01 = base * cost_term

            eps = np.random.normal(0, 0.05)
            sat_01 = sat_01 + eps

            sat_01 = max(0.0, min(1.0, sat_01))
            sat_05 = 1.0 + 4.0 * sat_01
            # ---------- END NONLINEAR LABEL ----------

            distance = np.sqrt(
                (poi["lat"] - user["hotel_lat"])**2 +
                (poi["lon"] - user["hotel_lon"])**2
            )

            row = {
                "user_id": user["user_id"],
                "poi_id": poi["id"],
                "satisfaction": sat_05,

                # Base features
                "duration_hours": dur,
                "cost": cost,
                "popularity": poi["popularity"],
                "open_start": poi["open_start"],
                "open_end": poi["open_end"],
                "pace_fast": 1 if user["pace"] == "fast" else 0,
                "pace_slow": 1 if user["pace"] == "slow" else 0,
                "pace_moderate": 1 if user["pace"] == "moderate" else 0,
                "interest_match": match,
                "pace_fit": pace_score,

                # Nonlinear Features
                "popularity_sq": poi["popularity"] ** 2,
                "duration_sq": dur ** 2,
                "cost_per_hour": cost / max(dur, 0.25),

                # Interaction Features
                "match_x_pop": match * poi["popularity"],
                "pace_x_duration": pace_score * dur,
                "cost_x_interest": cost * match,
                "duration_x_interest": dur * match,

                # Spatial Feature
                "distance_from_hotel": distance,
            }

            rows.append(row)

    return pd.DataFrame(rows)


user_poi = build_user_poi_dataset(user_profiles, pois)
user_poi.to_csv("user_poi_ratings.csv", index=False)
print("✅ Saved user_poi_ratings.csv with", len(user_poi), "rows")
print(user_poi.head())
