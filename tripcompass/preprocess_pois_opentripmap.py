import csv
import os
import sys

csv.field_size_limit(sys.maxsize)

def load_airport_poi():
    path = os.path.join("tripcompass/data", "City_Facilities_-_Airport_(SFO)_Jurisdiction_or_Leased_20251122.csv")
    lats = []
    lons = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
            except (KeyError, ValueError):
                continue
            lats.append(lat)
            lons.append(lon)

    if not lats:
        return None

    lat = sum(lats) / len(lats)
    lon = sum(lons) / len(lons)

    poi = {
        "id": "SFO",
        "name": "San Francisco International Airport (SFO)",
        "category": "airport",
        "duration_hours": 3.0,
        "cost": 0.0,
        "open_start": 0.0,
        "open_end": 24.0,
        "lat": lat,
        "lon": lon,
        "popularity": 4.5,
        "tags": "airport,sfo,transport",
    }
    return poi

import csv
import os

def load_parks_pois(max_parks=300):
    """
    Load Recreation and Parks properties as POIs.

    Returns a list of dicts with the same keys as pois_sf.csv.
    """
    path = os.path.join("tripcompass/data", "Recreation_and_Parks_Properties_20251122.csv")
    pois = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lon = float(row["longitude"])
                lat = float(row["latitude"])
            except (KeyError, ValueError):
                continue 

            name = row.get("property_name", "Park")
            prop_type = row.get("propertytype", "Park")

            poi = {
                "id": f"park_{row.get('property_id', row.get('objectid', '0'))}",
                "name": name,
                "category": "park",
                "duration_hours": 1.5,          
                "cost": 0.0,
                "open_start": 6.0,            
                "open_end": 22.0,
                "lat": lat,
                "lon": lon,
                "popularity": 4.0,            
                "tags": f"park,{prop_type}",
            }
            pois.append(poi)

            if len(pois) >= max_parks:
                break

    print(f"Loaded {len(pois)} park POIs")
    return pois


def load_restaurant_pois(max_places=500):
    """
    Load food service businesses from the Registered Business Locations file.

    Returns a list of dicts with the same keys as pois_sf.csv.
    """
    path = os.path.join(
        "tripcompass/data",
        "Registered_Business_Locations_-_San_Francisco_20251122.csv",
    )

    pois = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only keep food services in San Francisco
            if row.get("NAICS Code") != "7220-7229":
                continue
            if row.get("City") != "San Francisco":
                continue

            # Parse "POINT (lon lat)" from Business Location
            loc = row.get("Business Location", "")
            if not loc.startswith("POINT"):
                continue
            try:
                inside = loc[len("POINT ("):-1]  # strip 'POINT (' and final ')'
                lon_str, lat_str = inside.split()
                lon = float(lon_str)
                lat = float(lat_str)
            except Exception:
                continue

            name = row.get("DBA Name") or row.get("Ownership Name") or "Food place"

            poi = {
                "id": f"rest_{row.get('Location Id', row.get('UniqueID', '0'))}",
                "name": name,
                "category": "restaurant",
                "duration_hours": 1.5,
                "cost": 15.0,          # rough average spend, adjust if you want
                "open_start": 11.0,    # pretend 11am to 10pm
                "open_end": 22.0,
                "lat": lat,
                "lon": lon,
                "popularity": 4.2,     # placeholder rating
                "tags": "food,restaurant",
            }
            pois.append(poi)

            if len(pois) >= max_places:
                break

    print(f"Loaded {len(pois)} restaurant POIs")
    return pois

def load_muni_pois(max_stops=500):
    """
    Load Muni stops as transport POIs.
    Returns a list of dicts with the same keys as pois_sf.csv.
    """
    path = os.path.join("tripcompass/data", "Muni_Stops_20251122.csv")
    pois = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row["LATITUDE"])
                lon = float(row["LONGITUDE"])
            except (KeyError, ValueError):
                continue

            name = row.get("STOPNAME", "Muni stop")
            stop_id = row.get("STOPID", row.get("OBJECTID", "0"))

            poi = {
                "id": f"muni_{stop_id}",
                "name": name,
                "category": "transport",
                "duration_hours": 0.1,   # about 6 minutes at a stop
                "cost": 0.0,
                "open_start": 0.0,
                "open_end": 24.0,
                "lat": lat,
                "lon": lon,
                "popularity": 3.5,       # placeholder
                "tags": "muni,transit,stop",
            }
            pois.append(poi)

            if len(pois) >= max_stops:
                break

    print(f"Loaded {len(pois)} Muni stop POIs")
    return pois

def write_pois(pois, path="data/pois_sf.csv"):
    if not pois:
        print("No POIs to write")
        return

    fieldnames = list(pois[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for poi in pois:
            writer.writerow(poi)

def main():
    processed = []

    airport_poi = load_airport_poi()
    if airport_poi:
        processed.append(airport_poi)

    park_pois = load_parks_pois()
    processed.extend(park_pois)

    restaurant_pois = load_restaurant_pois()
    processed.extend(restaurant_pois)

    muni_pois = load_muni_pois()
    processed.extend(muni_pois)

    write_pois(processed, "tripcompass/data/pois_sf.csv")
    print(f"Finished. Wrote {len(processed)} POIs.")


if __name__ == "__main__":
    main()
