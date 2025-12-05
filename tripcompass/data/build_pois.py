"""
Multi-source POI enrichment pipeline.

Usage:
    python -m tripcompass.data.build_pois
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from tripcompass import config


STANDARD_COLUMNS = [
    "id",
    "name",
    "category",
    "duration_hours",
    "cost",
    "open_start",
    "open_end",
    "lat",
    "lon",
    "popularity",
    "tags",
    "source",
    "needs_review",
]

SOURCE_PRIORITIES = {
    "base_pois": 0,
    "sf_landmarks_curated": 1,
    "sf_recreation_parks": 2,
    "registered_businesses": 3,
    "muni_stops": 4,
    "sfo_facilities": 5,
    "film_locations": 6,
}

LAT_RANGE = (37.0, 37.95)
LON_RANGE = (-123.1, -122.0)


def _parse_point_wkt(point: str) -> Tuple[float | None, float | None]:
    if not isinstance(point, str):
        return None, None
    point = point.strip()
    if not point.startswith("POINT"):
        return None, None
    try:
        coords = point.split("(")[1].strip(" )")
        lon_str, lat_str = coords.split()
        return float(lat_str), float(lon_str)
    except (IndexError, ValueError):
        return None, None


def _coerce_float(series: pd.Series, default: float) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    return values.fillna(default)


def _random_duration(category: str, rng: np.random.Generator) -> float:
    mapping = {
        "airport": (2.5, 4.5),
        "transport": (0.15, 0.4),
        "restaurant": (1.0, 2.0),
        "nightlife": (2.0, 4.0),
        "shopping": (1.0, 2.5),
        "museum": (1.5, 3.0),
        "park": (1.0, 3.0),
        "landmark": (0.75, 2.0),
    }
    lo, hi = mapping.get(category, (0.75, 2.5))
    return float(rng.uniform(lo, hi))


def _random_cost(category: str, rng: np.random.Generator) -> float:
    """
    Generate realistic costs for different categories.
    For restaurants, uses a diverse range of $10-50 dollars.
    """
    if category == "restaurant":
        # Generate costs in $10-50 range with good distribution
        # Use a weighted distribution to create variety
        tier = rng.choice([0, 1, 2, 3], p=[0.25, 0.35, 0.30, 0.10])
        if tier == 0:
            # Budget-friendly: $10-20 (25%)
            return float(rng.uniform(10.0, 20.0))
        elif tier == 1:
            # Mid-range: $20-35 (35%)
            return float(rng.uniform(20.0, 35.0))
        elif tier == 2:
            # Upper-mid: $35-45 (30%)
            return float(rng.uniform(35.0, 45.0))
        else:
            # Upscale: $45-50 (10%)
            return float(rng.uniform(45.0, 50.0))
    
    mapping = {
        "airport": (0.0, 0.0),
        "transport": (0.0, 3.0),
        "nightlife": (20.0, 80.0),
        "shopping": (20.0, 120.0),
        "museum": (10.0, 35.0),
        "park": (0.0, 5.0),
        "landmark": (0.0, 25.0),
    }
    lo, hi = mapping.get(category, (0.0, 30.0))
    if lo == hi:
        return lo
    return float(rng.uniform(lo, hi))


def _random_popularity(rng: np.random.Generator, base: float | None = None) -> float:
    center = 4.2 if base is None or math.isnan(base) else base
    value = rng.normal(center, 0.25)
    return float(np.clip(value, 3.0, 5.0))


def _base_frame(df: pd.DataFrame, source: str, rng: np.random.Generator) -> pd.DataFrame:
    frame = df.copy()
    frame["source"] = source
    frame["needs_review"] = False
    
    # Regenerate costs for ALL restaurants to ensure they're in $10-50 range
    # This ensures more realistic price variation
    if "category" in frame.columns and "cost" in frame.columns:
        restaurant_mask = (frame["category"] == "restaurant")
        if restaurant_mask.any():
            frame.loc[restaurant_mask, "cost"] = frame.loc[restaurant_mask].apply(
                lambda row: _random_cost("restaurant", rng), axis=1
            )
    
    return frame[STANDARD_COLUMNS]


def load_base_pois(rng: np.random.Generator) -> Tuple[pd.DataFrame, str]:
    path = config.DATA_DIR / "pois_sf.csv"
    df = pd.read_csv(path)
    return _base_frame(df, "base_pois", rng), str(path)


def load_recreation_dataset(
    rng: np.random.Generator, sample_size: int = 500
) -> Tuple[pd.DataFrame, str]:
    path = config.DATA_DIR / "Recreation_and_Parks_Properties_20251122.csv"
    cols = [
        "property_id",
        "property_name",
        "propertytype",
        "latitude",
        "longitude",
        "analysis_neighborhood",
    ]
    df = pd.read_csv(path, usecols=cols)
    if sample_size and len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)

    records = []
    for _, row in df.iterrows():
        lat = float(row.get("latitude", np.nan))
        lon = float(row.get("longitude", np.nan))
        if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]):
            continue
        category = "park"
        tags = ",".join(
            filter(
                None,
                [
                    "park",
                    str(row.get("propertytype", "")).lower(),
                    str(row.get("analysis_neighborhood", "")).lower(),
                ],
            )
        )
        records.append(
            {
                "id": f"sf_rec_{row['property_id']}",
                "name": row["property_name"],
                "category": category,
                "duration_hours": _random_duration(category, rng),
                "cost": 0.0,
                "open_start": 6.0,
                "open_end": 22.0,
                "lat": lat,
                "lon": lon,
                "popularity": _random_popularity(rng, 4.2),
                "tags": tags,
                "source": "sf_recreation_parks",
                "needs_review": False,
            }
        )

    return pd.DataFrame(records, columns=STANDARD_COLUMNS), str(path)


def load_registered_businesses(
    rng: np.random.Generator, sample_size: int = 600
) -> Tuple[pd.DataFrame, str]:
    path = config.DATA_DIR / "Registered_Business_Locations_-_San_Francisco_20251122.csv"
    cols = [
        "Location Id",
        "DBA Name",
        "Ownership Name",
        "NAICS Code Description",
        "Business Location",
        "Neighborhoods - Analysis Boundaries",
    ]
    df = pd.read_csv(path, usecols=cols)
    df["lat"], df["lon"] = zip(*df["Business Location"].map(_parse_point_wkt))
    df = df.dropna(subset=["lat", "lon"])
    df = df[
        (df["lat"].between(LAT_RANGE[0], LAT_RANGE[1]))
        & (df["lon"].between(LON_RANGE[0], LON_RANGE[1]))
    ]
    if sample_size and len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)

    records = []
    for _, row in df.iterrows():
        name = row["DBA Name"] or row["Ownership Name"] or "Unnamed Business"
        tags = ",".join(
            filter(
                None,
                [
                    "restaurant",
                    str(row.get("NAICS Code Description", "")).lower(),
                    str(row.get("Neighborhoods - Analysis Boundaries", "")).lower(),
                ],
            )
        )
        category = "restaurant"
        records.append(
            {
                "id": f"biz_{row['Location Id']}",
                "name": name.title(),
                "category": category,
                "duration_hours": _random_duration(category, rng),
                "cost": _random_cost(category, rng),
                "open_start": 8.0,
                "open_end": 22.0,
                "lat": row["lat"],
                "lon": row["lon"],
                "popularity": _random_popularity(rng),
                "tags": tags,
                "source": "registered_businesses",
                "needs_review": False,
            }
        )
    return pd.DataFrame(records, columns=STANDARD_COLUMNS), str(path)


def load_muni_stops(
    rng: np.random.Generator, sample_size: int = 400
) -> Tuple[pd.DataFrame, str]:
    path = config.DATA_DIR / "Muni_Stops_20251122.csv"
    cols = ["STOPID", "STOPNAME", "LATITUDE", "LONGITUDE", "shape"]
    df = pd.read_csv(path, usecols=cols)
    df["lat"], df["lon"] = zip(*df["shape"].map(_parse_point_wkt))
    df["lat"] = df["lat"].fillna(df["LATITUDE"])
    df["lon"] = df["lon"].fillna(df["LONGITUDE"])
    df = df.dropna(subset=["lat", "lon"])
    df = df[
        (df["lat"].between(LAT_RANGE[0], LAT_RANGE[1]))
        & (df["lon"].between(LON_RANGE[0], LON_RANGE[1]))
    ]
    if sample_size and len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)

    records = []
    for _, row in df.iterrows():
        category = "transport"
        records.append(
            {
                "id": f"muni_{row['STOPID']}",
                "name": row["STOPNAME"].title(),
                "category": category,
                "duration_hours": _random_duration(category, rng),
                "cost": 0.0,
                "open_start": 5.0,
                "open_end": 24.0,
                "lat": row["lat"],
                "lon": row["lon"],
                "popularity": _random_popularity(rng, 3.5),
                "tags": "transport,muni,transit",
                "source": "muni_stops",
                "needs_review": True,
            }
        )
    return pd.DataFrame(records, columns=STANDARD_COLUMNS), str(path)


def load_sfo_facilities(
    rng: np.random.Generator, sample_size: int = 80
) -> Tuple[pd.DataFrame, str]:
    path = config.DATA_DIR / "City_Facilities_-_Airport_(SFO)_Jurisdiction_or_Leased_20251122.csv"
    cols = ["facility_id", "common_name", "longitude", "latitude", "jurisdiction"]
    df = pd.read_csv(path, usecols=cols)
    df = df.dropna(subset=["latitude", "longitude"])
    if sample_size and len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)

    records = []
    for _, row in df.iterrows():
        category = "airport"
        records.append(
            {
                "id": f"sfo_{row['facility_id']}",
                "name": row["common_name"].title(),
                "category": category,
                "duration_hours": _random_duration(category, rng),
                "cost": 0.0,
                "open_start": 0.0,
                "open_end": 24.0,
                "lat": row["latitude"],
                "lon": row["longitude"],
                "popularity": _random_popularity(rng, 4.4),
                "tags": f"airport,{str(row.get('jurisdiction', '')).lower()}",
                "source": "sfo_facilities",
                "needs_review": False,
            }
        )
    return pd.DataFrame(records, columns=STANDARD_COLUMNS), str(path)


def load_sf_landmarks_curated(rng: np.random.Generator) -> Tuple[pd.DataFrame, str]:
    """
    Curated list of major San Francisco landmarks, museums, and cultural sites.
    Data compiled from public sources and major tourist attractions.
    """
    landmarks = [
        # Museums & Cultural Sites
        {"name": "San Francisco Museum of Modern Art (SFMOMA)", "lat": 37.7857, "lon": -122.4011, "category": "museum", "cost": 25.0, "tags": "museum,art,modern,sfmoma"},
        {"name": "de Young Museum", "lat": 37.7713, "lon": -122.4687, "category": "museum", "cost": 15.0, "tags": "museum,art,golden gate park"},
        {"name": "California Academy of Sciences", "lat": 37.7699, "lon": -122.4661, "category": "museum", "cost": 39.95, "tags": "museum,science,aquarium,planetarium"},
        {"name": "Asian Art Museum", "lat": 37.7803, "lon": -122.4168, "category": "museum", "cost": 20.0, "tags": "museum,art,asian,culture"},
        {"name": "Exploratorium", "lat": 37.8014, "lon": -122.3976, "category": "museum", "cost": 29.95, "tags": "museum,science,interactive,hands-on"},
        {"name": "Walt Disney Family Museum", "lat": 37.8011, "lon": -122.4586, "category": "museum", "cost": 25.0, "tags": "museum,disney,history"},
        {"name": "Legion of Honor", "lat": 37.7844, "lon": -122.5006, "category": "museum", "cost": 15.0, "tags": "museum,art,european,classical"},
        {"name": "Contemporary Jewish Museum", "lat": 37.7870, "lon": -122.4041, "category": "museum", "cost": 16.0, "tags": "museum,jewish,culture,contemporary"},
        {"name": "Museum of the African Diaspora", "lat": 37.7870, "lon": -122.4041, "category": "museum", "cost": 12.0, "tags": "museum,african,diaspora,culture"},
        {"name": "Cable Car Museum", "lat": 37.7947, "lon": -122.4107, "category": "museum", "cost": 8.0, "tags": "museum,transportation,history,cable car"},
        
        # Major Landmarks
        {"name": "Golden Gate Bridge", "lat": 37.8199, "lon": -122.4783, "category": "landmark", "cost": 0.0, "tags": "landmark,bridge,iconic,viewpoint"},
        {"name": "Alcatraz Island", "lat": 37.8267, "lon": -122.4230, "category": "landmark", "cost": 45.0, "tags": "landmark,prison,island,history,tour"},
        {"name": "Fisherman's Wharf", "lat": 37.8080, "lon": -122.4177, "category": "landmark", "cost": 0.0, "tags": "landmark,waterfront,shopping,food,tourist"},
        {"name": "Pier 39", "lat": 37.8087, "lon": -122.4098, "category": "landmark", "cost": 0.0, "tags": "landmark,pier,shopping,entertainment,seals"},
        {"name": "Lombard Street", "lat": 37.8021, "lon": -122.4186, "category": "landmark", "cost": 0.0, "tags": "landmark,street,curved,scenic"},
        {"name": "Coit Tower", "lat": 37.8024, "lon": -122.4058, "category": "landmark", "cost": 9.0, "tags": "landmark,tower,viewpoint,telegraph hill"},
        {"name": "Palace of Fine Arts", "lat": 37.8024, "lon": -122.4488, "category": "landmark", "cost": 0.0, "tags": "landmark,architecture,marina,scenic"},
        {"name": "Painted Ladies", "lat": 37.7761, "lon": -122.4328, "category": "landmark", "cost": 0.0, "tags": "landmark,victorian,houses,architecture"},
        {"name": "Twin Peaks", "lat": 37.7544, "lon": -122.4477, "category": "landmark", "cost": 0.0, "tags": "landmark,viewpoint,panoramic,scenic"},
        {"name": "Sutro Baths", "lat": 37.7800, "lon": -122.5092, "category": "landmark", "cost": 0.0, "tags": "landmark,ruins,ocean,scenic,history"},
        {"name": "Golden Gate Park", "lat": 37.7694, "lon": -122.4862, "category": "park", "cost": 0.0, "tags": "park,large,recreation,museums"},
        {"name": "Presidio of San Francisco", "lat": 37.7983, "lon": -122.4658, "category": "park", "cost": 0.0, "tags": "park,historic,military,trails"},
        {"name": "Crissy Field", "lat": 37.8026, "lon": -122.4618, "category": "park", "cost": 0.0, "tags": "park,beach,waterfront,golden gate bridge view"},
        {"name": "Lands End", "lat": 37.7874, "lon": -122.5062, "category": "park", "cost": 0.0, "tags": "park,trail,ocean,scenic,cliffs"},
        {"name": "Dolores Park", "lat": 37.7597, "lon": -122.4280, "category": "park", "cost": 0.0, "tags": "park,recreation,popular,mission"},
        
        # Markets & Shopping
        {"name": "Ferry Building Marketplace", "lat": 37.7956, "lon": -122.3933, "category": "shopping", "cost": 0.0, "tags": "marketplace,food,ferry building,local"},
        {"name": "Chinatown", "lat": 37.7941, "lon": -122.4078, "category": "shopping", "cost": 0.0, "tags": "shopping,neighborhood,culture,food,chinese"},
        {"name": "Union Square", "lat": 37.7879, "lon": -122.4075, "category": "shopping", "cost": 0.0, "tags": "shopping,plaza,retail,central"},
        {"name": "Mission District", "lat": 37.7599, "lon": -122.4148, "category": "shopping", "cost": 0.0, "tags": "neighborhood,shopping,food,culture,latino"},
        
        # Theaters & Entertainment
        {"name": "War Memorial Opera House", "lat": 37.7791, "lon": -122.4209, "category": "landmark", "cost": 50.0, "tags": "theater,opera,performing arts,civic center"},
        {"name": "SFJAZZ Center", "lat": 37.7749, "lon": -122.4194, "category": "nightlife", "cost": 35.0, "tags": "jazz,music,nightlife,performing arts,venue"},
        {"name": "The Fillmore", "lat": 37.7841, "lon": -122.4331, "category": "nightlife", "cost": 40.0, "tags": "venue,music,concert,nightlife,historic"},
        
        # Nightlife & Bars
        {"name": "Twin Peaks Tavern", "lat": 37.7749, "lon": -122.4294, "category": "nightlife", "cost": 15.0, "tags": "bar,lgbtq,nightlife,historic"},
        {"name": "The Saloon", "lat": 37.7975, "lon": -122.4067, "category": "nightlife", "cost": 10.0, "tags": "bar,blues,music,nightlife,historic"},
        {"name": "Bimbo's 365 Club", "lat": 37.8024, "lon": -122.4208, "category": "nightlife", "cost": 25.0, "tags": "club,music,nightlife,venue,entertainment"},
        {"name": "The Independent", "lat": 37.7756, "lon": -122.4372, "category": "nightlife", "cost": 30.0, "tags": "venue,music,concert,nightlife,indie"},
        {"name": "Great American Music Hall", "lat": 37.7870, "lon": -122.4187, "category": "nightlife", "cost": 35.0, "tags": "venue,music,concert,nightlife,historic"},
        {"name": "Bottom of the Hill", "lat": 37.7575, "lon": -122.4028, "category": "nightlife", "cost": 20.0, "tags": "venue,music,rock,nightlife,bar"},
        {"name": "Rickshaw Stop", "lat": 37.7749, "lon": -122.4214, "category": "nightlife", "cost": 20.0, "tags": "venue,music,nightlife,indie,dj"},
        {"name": "The Chapel", "lat": 37.7575, "lon": -122.4214, "category": "nightlife", "cost": 25.0, "tags": "venue,music,concert,nightlife,mission"},
        {"name": "Audio Discotech", "lat": 37.7749, "lon": -122.4094, "category": "nightlife", "cost": 30.0, "tags": "club,electronic,dj,nightlife,dancing"},
        {"name": "Temple Nightclub", "lat": 37.7749, "lon": -122.4094, "category": "nightlife", "cost": 35.0, "tags": "club,electronic,nightlife,dancing,venue"},
        {"name": "Ruby Skye", "lat": 37.7879, "lon": -122.4074, "category": "nightlife", "cost": 40.0, "tags": "club,nightlife,dancing,venue,electronic"},
        {"name": "The Warfield", "lat": 37.7843, "lon": -122.4094, "category": "nightlife", "cost": 45.0, "tags": "venue,music,concert,nightlife,historic"},
        {"name": "The Regency Ballroom", "lat": 37.7749, "lon": -122.4094, "category": "nightlife", "cost": 40.0, "tags": "venue,music,concert,nightlife,ballroom"},
        {"name": "Mezzanine", "lat": 37.7749, "lon": -122.4094, "category": "nightlife", "cost": 25.0, "tags": "venue,music,nightlife,indie,electronic"},
        {"name": "1015 Folsom", "lat": 37.7749, "lon": -122.4094, "category": "nightlife", "cost": 30.0, "tags": "club,electronic,nightlife,dancing,venue"},
        
        # Viewpoints & Scenic Spots
        {"name": "Battery Spencer", "lat": 37.8264, "lon": -122.4800, "category": "landmark", "cost": 0.0, "tags": "viewpoint,golden gate bridge,scenic"},
        {"name": "Baker Beach", "lat": 37.7936, "lon": -122.4836, "category": "park", "cost": 0.0, "tags": "beach,scenic,golden gate bridge view"},
        {"name": "Ocean Beach", "lat": 37.7594, "lon": -122.5102, "category": "park", "cost": 0.0, "tags": "beach,ocean,scenic,sunset"},
    ]
    
    records = []
    for i, landmark in enumerate(landmarks):
        category = landmark["category"]
        records.append({
            "id": f"landmark_{i+1:03d}",
            "name": landmark["name"],
            "category": category,
            "duration_hours": _random_duration(category, rng),
            "cost": landmark.get("cost", 0.0),
            "open_start": 9.0 if category == "museum" else (20.0 if category == "nightlife" else 6.0),
            "open_end": 17.0 if category == "museum" else (2.0 if category == "nightlife" else 22.0),
            "lat": landmark["lat"],
            "lon": landmark["lon"],
            "popularity": _random_popularity(rng, 4.5),
            "tags": landmark["tags"],
            "source": "sf_landmarks_curated",
            "needs_review": False,
        })
    
    return pd.DataFrame(records, columns=STANDARD_COLUMNS), "curated_landmarks"


def load_film_locations(rng: np.random.Generator) -> Tuple[pd.DataFrame, str]:
    """
    Load film locations dataset if available.
    Falls back to empty DataFrame if file doesn't exist.
    """
    path = config.DATA_DIR / "Film_Locations_in_San_Francisco.csv"
    if not path.exists():
        return pd.DataFrame(columns=STANDARD_COLUMNS), "film_locations (not found)"
    
    try:
        df = pd.read_csv(path)
        # Try to extract location data - column names may vary
        # Common columns: Title, Locations, Fun Facts, etc.
        if "Locations" not in df.columns:
            return pd.DataFrame(columns=STANDARD_COLUMNS), str(path)
        
        records = []
        for idx, row in df.iterrows():
            location_str = str(row.get("Locations", ""))
            # Try to parse coordinates if available, otherwise skip
            # For now, we'll mark these as needing manual geocoding
            if pd.isna(row.get("Latitude", np.nan)) or pd.isna(row.get("Longitude", np.nan)):
                continue
            
            lat = float(row.get("Latitude", np.nan))
            lon = float(row.get("Longitude", np.nan))
            
            if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]):
                continue
            
            title = str(row.get("Title", "Unknown Film Location"))
            records.append({
                "id": f"film_{idx}",
                "name": f"Film Location: {title}",
                "category": "landmark",
                "duration_hours": _random_duration("landmark", rng),
                "cost": 0.0,
                "open_start": 0.0,
                "open_end": 24.0,
                "lat": lat,
                "lon": lon,
                "popularity": _random_popularity(rng, 3.8),
                "tags": f"film location,{title.lower()},movie,entertainment",
                "source": "film_locations",
                "needs_review": True,  # May need manual verification
            })
        
        return pd.DataFrame(records, columns=STANDARD_COLUMNS), str(path)
    except Exception as e:
        print(f"Warning: Could not load film locations: {e}")
        return pd.DataFrame(columns=STANDARD_COLUMNS), str(path)


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["key"] = (
        df["name"].str.lower().str.strip().fillna("")
        + "|"
        + df["lat"].round(5).astype(str)
        + "|"
        + df["lon"].round(5).astype(str)
    )
    df["priority"] = df["source"].map(SOURCE_PRIORITIES).fillna(99)
    df = df.sort_values(["key", "priority"])
    df = df.drop_duplicates(subset="key", keep="first")
    return df.drop(columns=["key", "priority"])


def apply_defaults(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    df = df.copy()
    numeric_cols = ["duration_hours", "cost", "open_start", "open_end", "popularity"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    category_stats = df.groupby("category")[numeric_cols].median()
    global_stats = df[numeric_cols].median()

    for col in numeric_cols:
        def fill_func(row):
            if not math.isnan(row[col]):
                # Special handling: regenerate restaurant costs to ensure $10-50 range
                if col == "cost" and row["category"] == "restaurant":
                    # Check if cost is outside $10-50 range, regenerate if so
                    current_cost = row[col]
                    if current_cost < 10.0 or current_cost > 50.0:
                        return _random_cost("restaurant", rng)
                return row[col]
            cat = row["category"]
            
            # Special handling for restaurant costs - regenerate instead of using median
            if col == "cost" and cat == "restaurant":
                return _random_cost("restaurant", rng)
            
            if cat in category_stats.index and not math.isnan(category_stats.loc[cat, col]):
                return category_stats.loc[cat, col]
            return global_stats[col]

        df[col] = df.apply(fill_func, axis=1)

    df["tags"] = df["tags"].fillna("")
    df["needs_review"] = df["needs_review"].fillna(False).astype(bool)
    return df


def validate_dataset(df: pd.DataFrame) -> Dict[str, object]:
    issues: List[str] = []
    if df["id"].duplicated().any():
        dupes = df[df["id"].duplicated()]["id"].head(5).tolist()
        issues.append(f"duplicate ids: {dupes}")
    if not df["lat"].between(LAT_RANGE[0], LAT_RANGE[1]).all():
        issues.append("latitude outside expected range")
    if not df["lon"].between(LON_RANGE[0], LON_RANGE[1]).all():
        issues.append("longitude outside expected range")
    if (df["duration_hours"] <= 0).any():
        issues.append("non-positive duration detected")
    if (df["open_end"] < df["open_start"]).any():
        issues.append("open_end earlier than open_start detected")

    category_counts = df["category"].value_counts().to_dict()
    summary = {
        "record_count": int(len(df)),
        "category_counts": category_counts,
        "cost_range": [float(df["cost"].min()), float(df["cost"].max())],
        "popularity_range": [float(df["popularity"].min()), float(df["popularity"].max())],
        "issues": issues,
    }
    return summary


def write_manifest(entries: List[Dict[str, object]]) -> None:
    config.RAW_DATA_MANIFEST.write_text(json.dumps(entries, indent=2))


def build_dataset(seed: int = 42) -> Tuple[pd.DataFrame, Dict[str, object], List[Dict[str, object]]]:
    rng = np.random.default_rng(seed)
    config.ensure_directories()

    sources = []
    base_df, base_path = load_base_pois(rng)
    sources.append(("base_pois", base_path, base_df))
    
    # Curated landmarks (museums, major attractions)
    landmarks_df, landmarks_path = load_sf_landmarks_curated(rng)
    sources.append(("sf_landmarks_curated", landmarks_path, landmarks_df))
    
    rec_df, rec_path = load_recreation_dataset(rng)
    sources.append(("sf_recreation_parks", rec_path, rec_df))
    biz_df, biz_path = load_registered_businesses(rng)
    sources.append(("registered_businesses", biz_path, biz_df))
    muni_df, muni_path = load_muni_stops(rng)
    sources.append(("muni_stops", muni_path, muni_df))
    sfo_df, sfo_path = load_sfo_facilities(rng)
    sources.append(("sfo_facilities", sfo_path, sfo_df))
    
    # Film locations (optional - only if file exists)
    film_df, film_path = load_film_locations(rng)
    if not film_df.empty:
        sources.append(("film_locations", film_path, film_df))

    frames = [frame for _, _, frame in sources if not frame.empty]
    combined = pd.concat(frames, ignore_index=True)
    combined = deduplicate(combined)
    combined = apply_defaults(combined, rng)

    summary = validate_dataset(combined)

    manifest_entries: List[Dict[str, object]] = []
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    for source_name, source_path, frame in sources:
        manifest_entries.append(
            {
                "source": source_name,
                "path": source_path,
                "records": int(len(frame)),
                "generated_at": timestamp,
            }
        )

    return combined, summary, manifest_entries


def main() -> None:
    dataset, summary, manifest = build_dataset()
    dataset.to_csv(config.POI_OUTPUT_PATH, index=False)
    config.DATA_QUALITY_REPORT.write_text(json.dumps(summary, indent=2))
    write_manifest(manifest)
    print(
        f"Wrote {len(dataset)} POIs to {config.POI_OUTPUT_PATH.relative_to(config.REPO_ROOT)}"
    )
    if summary["issues"]:
        print("Validation issues:")
        for issue in summary["issues"]:
            print(f" - {issue}")
    else:
        print("Validation passed with no blocking issues.")


if __name__ == "__main__":
    main()

