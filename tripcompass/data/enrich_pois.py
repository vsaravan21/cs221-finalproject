import pandas as pd
import numpy as np

np.random.seed(42)

INPUT_CSV = "pois_sf.csv"
OUTPUT_CSV = "pois_sf_enriched.csv"

df = pd.read_csv(INPUT_CSV)

print("Before enrichment:")
print(df.head())


def infer_category_type(row):
    """Rough semantic type from category + tags."""
    cat = str(row.get("category", "")).lower()
    tags = str(row.get("tags", "")).lower()

    if "airport" in cat or "airport" in tags:
        return "airport"
    if "museum" in tags or "museum" in cat:
        return "museum"
    if "library" in tags:
        return "library"
    if "park" in tags or "park" in cat:
        return "park"
    if any(x in tags for x in ["restaurant", "food", "cafe", "diner", "eatery"]):
        return "restaurant"
    if any(x in tags for x in ["bar", "pub", "nightlife", "club"]):
        return "nightlife"
    if any(x in tags for x in ["shopping", "mall", "market", "store"]):
        return "shopping"
    if any(x in tags for x in ["landmark", "monument", "sight", "viewpoint"]):
        return "landmark"
    # fallback
    return "other"


def sample_duration_hours(cat_type):
    """Sample a realistic duration for each type."""
    if cat_type == "airport":
        return np.random.uniform(2.5, 4.5)
    if cat_type == "museum":
        return np.random.uniform(1.5, 3.0)
    if cat_type == "library":
        return np.random.uniform(1.0, 2.0)
    if cat_type == "park":
        return np.random.uniform(1.0, 3.0)
    if cat_type == "restaurant":
        return np.random.uniform(1.0, 2.0)
    if cat_type == "nightlife":
        return np.random.uniform(2.0, 4.0)
    if cat_type == "shopping":
        return np.random.uniform(1.0, 3.0)
    if cat_type == "landmark":
        return np.random.uniform(0.75, 2.0)
    # other
    return np.random.uniform(0.75, 2.5)


def sample_cost(cat_type):
    """Sample a rough cost per visit."""
    if cat_type == "airport":
        return 0.0  # airport itself, not flight
    if cat_type == "museum":
        return np.random.uniform(10, 30)
    if cat_type == "library":
        return 0.0
    if cat_type == "park":
        return 0.0
    if cat_type == "restaurant":
        return np.random.uniform(15, 50)
    if cat_type == "nightlife":
        return np.random.uniform(20, 80)
    if cat_type == "shopping":
        return np.random.uniform(20, 150)
    if cat_type == "landmark":
        return np.random.uniform(0, 25)
    # other
    return np.random.uniform(0, 30)


def jitter_popularity(pop):
    """Add a little noise to popularity so it's not all constant."""
    if pd.isna(pop):
        base = 4.0
    else:
        base = float(pop)
    # small noise, keep in [3.0, 5.0]
    jittered = base + np.random.normal(0, 0.3)
    return float(np.clip(jittered, 3.0, 5.0))


# Apply the enrichment
cat_types = []
new_durations = []
new_costs = []
new_pops = []

for _, row in df.iterrows():
    ctype = infer_category_type(row)
    cat_types.append(ctype)
    new_durations.append(sample_duration_hours(ctype))
    new_costs.append(sample_cost(ctype))
    new_pops.append(jitter_popularity(row.get("popularity", 4.0)))

df["semantic_type"] = cat_types
df["duration_hours"] = np.round(new_durations, 2)
df["cost"] = np.round(new_costs, 2)
df["popularity"] = np.round(new_pops, 1)

print("\nAfter enrichment (preview):")
print(df.head())

df.to_csv(OUTPUT_CSV, index=False)
print(f"\n✅ Saved enriched POIs to {OUTPUT_CSV}")