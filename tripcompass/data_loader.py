from tripcompass.pois_io import load_pois
def get_pois():
    pois = load_pois()
    return pois 

def load_user_profile(path="tripcompass/data/user_profile.json"):
    import json
    with open(path, "r") as f:
        return json.load(f)
