import math
from typing import List, Dict, Tuple, Union

from tripcompass.model import TripModel



def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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




def travel_time_hours(lat1, lon1, lat2, lon2, speed_kmh: float = 4.0) -> float:
    dist = haversine_km(lat1, lon1, lat2, lon2)
    if speed_kmh <= 0:
        return 0.0
    return dist / speed_kmh


# ------------ core greedy planner ------------

def _poi_value(model: TripModel, poi: Dict) -> float:
    """Numeric value for a POI dict."""
    try:
        return float(model.poi_value(poi))
    except Exception:
        return float(poi.get("popularity", 1.0))



def _select_next_poi(
    model: TripModel,
    current_lat: float,
    current_lon: float,
    remaining_hours: float,
    unvisited: List[Dict],
    home_lat: float,
    home_lon: float,
    speed_kmh: float = 4.0,
) -> Tuple[Dict | None, float, float]:
    best_poi = None
    best_score_per_time = 0.0
    best_travel_h = 0.0
    best_visit_h = 0.0

    for poi in unvisited:
        lat = float(poi["lat"])
        lon = float(poi["lon"])
        visit_hours = float(poi.get("duration_hours", 1.0))

        to_poi = travel_time_hours(current_lat, current_lon, lat, lon, speed_kmh)
        back_home = travel_time_hours(lat, lon, home_lat, home_lon, speed_kmh)

        total_needed = to_poi + visit_hours + back_home
        if total_needed > remaining_hours:
            continue

        value = _poi_value(model, poi)
        time_cost = max(to_poi + visit_hours, 1e-6)
        score_per_time = value / time_cost

        if best_poi is None or score_per_time > best_score_per_time:
            best_poi = poi
            best_score_per_time = score_per_time
            best_travel_h = to_poi
            best_visit_h = visit_hours

    if best_poi is None:
        return None, 0.0, 0.0

    return best_poi, best_travel_h, best_visit_h


def plan_day(
    pois: List[Dict],
    home_lat: float,
    home_lon: float,
    day_hours: float = 10.0,
    speed_kmh: float = 4.0,
) -> List[Dict]:
    """
    Plan a single-day itinerary.

    Returns an ordered list of POIs representing the route in visit order.
    """
    model = TripModel(pois, home_lat, home_lon)
    unvisited = list(pois)
    route: List[Dict] = []

    current_lat = home_lat
    current_lon = home_lon
    remaining = float(day_hours)

    while True:
        next_poi, travel_h, visit_h = _select_next_poi(
            model,
            current_lat,
            current_lon,
            remaining,
            unvisited,
            home_lat,
            home_lon,
            speed_kmh,
        )

        if next_poi is None:
            break

        # Commit to this POI
        remaining -= (travel_h + visit_h)
        current_lat = float(next_poi["lat"])
        current_lon = float(next_poi["lon"])

        route.append(next_poi)
        unvisited.remove(next_poi)

        # Safety break in case of weird values
        if remaining <= 0:
            break

    return route


# Convenience wrappers, in case main.py expects different names

def plan_trip(
    pois: List[Dict],
    home_lat: float,
    home_lon: float,
    day_hours: float = 10.0,
    speed_kmh: float = 4.0,
) -> List[Dict]:
    return plan_day(pois, home_lat, home_lon, day_hours, speed_kmh)


def plan(
    pois: List[Dict],
    home_lat: float,
    home_lon: float,
    day_hours: float = 10.0,
    speed_kmh: float = 4.0,
) -> List[Dict]:
    """
    Default entrypoint used by other modules.
    """
    return plan_day(pois, home_lat, home_lon, day_hours, speed_kmh)
