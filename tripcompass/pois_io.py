# tripcompass/pois_io.py

import csv
import os
from dataclasses import dataclass
from typing import List


@dataclass
class POI:
    id: str
    name: str
    category: str
    duration_hours: float
    cost: float
    open_start: float
    open_end: float
    lat: float
    lon: float
    popularity: float
    tags: str


def load_pois(path: str = "data/pois_sf.csv") -> List[POI]:
    """
    Load the combined POI CSV written by preprocess_pois_opentripmap.py
    and convert each row into a POI dataclass.
    """
    pois: List[POI] = []
    full_path = os.path.join(os.path.dirname(__file__), path)

    with open(full_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                poi = POI(
                    id=row["id"],
                    name=row["name"],
                    category=row["category"],
                    duration_hours=float(row["duration_hours"]),
                    cost=float(row["cost"]),
                    open_start=float(row["open_start"]),
                    open_end=float(row["open_end"]),
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    popularity=float(row["popularity"]),
                    tags=row.get("tags", ""),
                )
            except (KeyError, ValueError):
                continue

            pois.append(poi)

    print(f"Loaded {len(pois)} POIs from {path}")
    return pois
