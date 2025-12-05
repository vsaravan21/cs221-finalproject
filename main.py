from tripcompass.pois_io import load_pois
from tripcompass.data_loader import load_user_profile
from tripcompass.planner import plan

def main():
    pois = load_pois()   # reads tripcompass/data/pois_sf.csv
    profile = load_user_profile()

    home_lat = profile["home_lat"]
    home_lon = profile["home_lon"]
    day_hours = profile.get("day_hours", 10.0)

    print(f"Loaded {len(pois)} POIs.")
    print(f"Home location: ({home_lat}, {home_lon})")

    itinerary = plan(pois, home_lat, home_lon, day_hours)

    print("\nPlanned itinerary:")
    for i, poi in enumerate(itinerary, 1):
        print(f"{i}. {poi['name']} — {poi['category']} ({poi['lat']}, {poi['lon']})")


if __name__ == "__main__":
    main()
