# tripcompass/model.py

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple


# ----------------- geometry helpers -----------------


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points in kilometers."""
    r = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return r * c


# ----------------- core TripModel -----------------


class TripModel:
    """
    Simple model that works directly with POIs as dicts
    (matching the columns in pois_sf.csv).
    """

    WALK_SPEED_KMPH = 4.0
    TRANSIT_SPEED_KMPH = 14.0

    POPULARITY_WEIGHT = 1.0
    COST_WEIGHT = 0.08
    TRANSPORT_PENALTY = 0.5
    PARK_BONUS = 0.5
    RESTAURANT_BONUS = 0.7
    AIRPORT_PENALTY = 1.0

    def __init__(
        self,
        pois: List[Dict],
        home_lat: float,
        home_lon: float,
        day_start: float = 9.0,
        day_end: float = 21.0,
    ) -> None:
        # Just store the dicts
        self.pois: List[Dict] = list(pois)

        # Index by id
        self.id_to_poi: Dict[str, Dict] = {}
        for p in self.pois:
            pid = str(p.get("id", ""))
            if pid:
                self.id_to_poi[pid] = p

        self.home_lat = float(home_lat)
        self.home_lon = float(home_lon)
        self.day_start = float(day_start)
        self.day_end = float(day_end)

    # -------- accessors --------

    def all_pois(self) -> List[Dict]:
        return list(self.pois)

    def get(self, poi_id: str) -> Optional[Dict]:
        return self.id_to_poi.get(poi_id)

    # -------- helpers to read fields --------

    @staticmethod
    def _coords(poi: Dict) -> Tuple[float, float]:
        return float(poi["lat"]), float(poi["lon"])

    @staticmethod
    def _category(poi: Dict) -> str:
        return str(poi.get("category", "")).lower()

    @staticmethod
    def _popularity(poi: Dict) -> float:
        return float(poi.get("popularity", 1.0))

    @staticmethod
    def _cost(poi: Dict) -> float:
        return float(poi.get("cost", 0.0))

    @staticmethod
    def _open_interval(poi: Dict) -> Tuple[float, float]:
        return float(poi.get("open_start", 0.0)), float(poi.get("open_end", 24.0))

    # -------- travel model --------

    def _speed_between(self, a: Optional[Dict], b: Optional[Dict]) -> float:
        if a is not None and self._category(a) == "transport":
            return self.TRANSIT_SPEED_KMPH
        if b is not None and self._category(b) == "transport":
            return self.TRANSIT_SPEED_KMPH
        return self.WALK_SPEED_KMPH

    def travel_time_hours(self, a: Optional[Dict], b: Optional[Dict]) -> float:
        if a is None and b is None:
            return 0.0

        if a is None:
            lat1, lon1 = self.home_lat, self.home_lon
        else:
            lat1, lon1 = self._coords(a)

        if b is None:
            lat2, lon2 = self.home_lat, self.home_lon
        else:
            lat2, lon2 = self._coords(b)

        dist = haversine_km(lat1, lon1, lat2, lon2)
        if dist == 0.0:
            return 0.0

        speed = self._speed_between(a, b)
        return dist / speed

    # -------- value function --------

    def poi_value(self, poi: Dict) -> float:
        v = self.POPULARITY_WEIGHT * self._popularity(poi)

        cat = self._category(poi)
        if cat == "park":
            v += self.PARK_BONUS
        elif cat == "restaurant":
            v += self.RESTAURANT_BONUS
        elif cat == "transport":
            v -= self.TRANSPORT_PENALTY
        elif cat == "airport":
            v -= self.AIRPORT_PENALTY

        v -= self.COST_WEIGHT * self._cost(poi)
        return v

    def is_open(self, poi: Dict, arrival_time: float) -> bool:
        start, end = self._open_interval(poi)
        return start <= arrival_time <= end

    # -------- itinerary scoring (optional helper) --------

    def score_itinerary(self, poi_ids: List[str]) -> float:
        time = self.day_start
        total_value = 0.0
        prev: Optional[Dict] = None

        for pid in poi_ids:
            poi = self.get(pid)
            if poi is None:
                continue

            travel = self.travel_time_hours(prev, poi)
            arrival = time + travel
            if arrival > self.day_end:
                break

            if not self.is_open(poi, arrival):
                time = arrival
                prev = poi
                continue

            visit = float(poi.get("duration_hours", 1.0))
            finish = arrival + visit
            if finish > self.day_end:
                break

            total_value += self.poi_value(poi)
            time = finish
            prev = poi

        if prev is not None:
            total_value -= self.travel_time_hours(prev, None) * 0.0  # no penalty

        return total_value

