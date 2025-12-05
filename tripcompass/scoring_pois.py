import pandas as pd
import numpy as np
import joblib

# -----------------------
# Load Models + Data
# -----------------------
def load_models():
    model = joblib.load("main_rf_model.joblib")
    scaler = joblib.load("main_scaler.joblib")
    return model, scaler


def load_data():
    users = pd.read_csv("data/user_profiles.csv")
    pois = pd.read_csv("data/pois_sf_enriched.csv")
    return users, pois


# -----------------------
# Feature Construction
# -----------------------
def make_feature_vector(user, poi):
    """Build one feature vector for (user, poi)."""
    
    match = interest_tag_match(user, poi.get("tags", ""))
    pace_score = pace_fit(user["pace"], poi["duration_hours"])
    
    dur = poi["duration_hours"]
    cost = poi["cost"]
    pop = poi["popularity"]

    # spatial feature
    distance = np.sqrt(
        (poi["lat"] - user["hotel_lat"])**2 +
        (poi["lon"] - user["hotel_lon"])**2
    )

    return [
        # Base features
        dur,
        cost,
        pop,
        poi["open_start"],
        poi["open_end"],
        1 if user["pace"] == "fast" else 0,
        1 if user["pace"] == "slow" else 0,
        1 if user["pace"] == "moderate" else 0,
        match,
        pace_score,

        # Nonlinear features
        pop**2,
        dur**2,
        cost / max(dur, 0.25),

        # Interactions
        match * pop,
        pace_score * dur,
        cost * match,
        dur * match,

        # Spatial
        distance,
    ]


# These must match your build_training_data script
from build_training_data import pace_fit, interest_tag_match


# -----------------------
# Score POIs for a User
# -----------------------
def score_pois_for_user(user_id):
    model, scaler = load_models()
    users, pois = load_data()

    user = users[users["user_id"] == user_id].iloc[0]

    features = []
    poi_ids = []

    for _, poi in pois.iterrows():
        fv = make_feature_vector(user, poi)
        features.append(fv)
        poi_ids.append(poi["id"])

    X = np.array(features)
    X_scaled = scaler.transform(X)

    preds = model.predict(X_scaled)

    result = pd.DataFrame({
        "poi_id": poi_ids,
        "predicted_satisfaction": preds
    }).sort_values(by="predicted_satisfaction", ascending=False)

    return result
