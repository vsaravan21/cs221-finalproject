"""
Model inference utilities for loading and using trained models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd

from tripcompass.models.neural_network import SimpleFFN


def load_baseline_model(
    model_path: str | Path = "tripcompass/baseline_linear_model.joblib",
    scaler_path: str | Path = "tripcompass/baseline_scaler.joblib",
) -> Tuple[object, object]:
    """
    Load the baseline linear regression model and scaler.
    
    Args:
        model_path: Path to the saved baseline model
        scaler_path: Path to the saved scaler
        
    Returns:
        Tuple of (model, scaler)
    """
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    return model, scaler


def load_main_model(
    model_path: str | Path = "tripcompass/main_nn_model.npz",
    scaler_path: str | Path = "tripcompass/main_scaler.joblib",
) -> Tuple[SimpleFFN, object]:
    """
    Load the main neural network model and scaler.
    
    Args:
        model_path: Path to the saved NN model weights (.npz)
        scaler_path: Path to the saved scaler
        
    Returns:
        Tuple of (model, scaler)
    """
    model = SimpleFFN.load_weights(model_path)
    scaler = joblib.load(scaler_path)
    return model, scaler


def predict_satisfaction(
    model: object | SimpleFFN,
    scaler: object,
    user_row: pd.Series,
    poi_row: pd.Series,
    feature_cols: list[str] | None = None,
) -> float:
    """
    Predict satisfaction for a single user-POI pair.
    
    Args:
        model: Trained model (sklearn or SimpleFFN)
        scaler: Feature scaler
        user_row: User profile row (pandas Series)
        poi_row: POI row (pandas Series)
        feature_cols: List of feature column names (if None, uses default)
        
    Returns:
        Predicted satisfaction score (float)
    """
    from tripcompass.data.build_training_data import pace_fit, interest_tag_match
    import math

    if feature_cols is None:
        feature_cols = [
            "duration_hours",
            "cost",
            "popularity",
            "open_start",
            "open_end",
            "pace_fast",
            "pace_slow",
            "pace_moderate",
            "interest_match",
            "pace_fit",
            "popularity_sq",
            "duration_sq",
            "cost_per_hour",
            "match_x_pop",
            "pace_x_duration",
            "cost_x_interest",
            "duration_x_interest",
            "distance_from_hotel",
        ]

    # Build feature vector
    match = interest_tag_match(user_row, poi_row.get("tags", ""))
    pace_score = pace_fit(user_row["pace"], poi_row["duration_hours"])

    dur = float(poi_row["duration_hours"])
    cost = float(poi_row["cost"])
    pop = float(poi_row["popularity"])

    distance = math.sqrt(
        (poi_row["lat"] - user_row["hotel_lat"]) ** 2
        + (poi_row["lon"] - user_row["hotel_lon"]) ** 2
    )

    features = {
        "duration_hours": dur,
        "cost": cost,
        "popularity": pop,
        "open_start": poi_row["open_start"],
        "open_end": poi_row["open_end"],
        "pace_fast": 1 if user_row["pace"] == "fast" else 0,
        "pace_slow": 1 if user_row["pace"] == "slow" else 0,
        "pace_moderate": 1 if user_row["pace"] == "moderate" else 0,
        "interest_match": match,
        "pace_fit": pace_score,
        "popularity_sq": pop ** 2,
        "duration_sq": dur ** 2,
        "cost_per_hour": cost / max(dur, 0.25),
        "match_x_pop": match * pop,
        "pace_x_duration": pace_score * dur,
        "cost_x_interest": cost * match,
        "duration_x_interest": dur * match,
        "distance_from_hotel": distance,
    }

    X = np.array([[features[col] for col in feature_cols]])
    X_scaled = scaler.transform(X)

    # Predict
    if isinstance(model, SimpleFFN):
        pred = model.predict(X_scaled)
        return float(pred[0, 0])
    else:
        # sklearn model
        pred = model.predict(X_scaled)
        return float(pred[0])


def predict_batch(
    model: object | SimpleFFN,
    scaler: object,
    user_row: pd.Series,
    pois_df: pd.DataFrame,
    feature_cols: list[str] | None = None,
) -> pd.DataFrame:
    """
    Predict satisfaction scores for a user across all POIs.
    
    Args:
        model: Trained model (sklearn or SimpleFFN)
        scaler: Feature scaler
        user_row: User profile row (pandas Series)
        pois_df: DataFrame of POIs
        feature_cols: List of feature column names (if None, uses default)
        
    Returns:
        DataFrame with POI IDs and predicted_satisfaction column
    """
    from tripcompass.data.build_training_data import pace_fit, interest_tag_match
    import math

    if feature_cols is None:
        feature_cols = [
            "duration_hours",
            "cost",
            "popularity",
            "open_start",
            "open_end",
            "pace_fast",
            "pace_slow",
            "pace_moderate",
            "interest_match",
            "pace_fit",
            "popularity_sq",
            "duration_sq",
            "cost_per_hour",
            "match_x_pop",
            "pace_x_duration",
            "cost_x_interest",
            "duration_x_interest",
            "distance_from_hotel",
        ]

    feature_matrix = []
    poi_ids = []

    for _, poi in pois_df.iterrows():
        match = interest_tag_match(user_row, poi.get("tags", ""))
        pace_score = pace_fit(user_row["pace"], poi["duration_hours"])

        dur = float(poi["duration_hours"])
        cost = float(poi["cost"])
        pop = float(poi["popularity"])

        distance = math.sqrt(
            (poi["lat"] - user_row["hotel_lat"]) ** 2
            + (poi["lon"] - user_row["hotel_lon"]) ** 2
        )

        features = {
            "duration_hours": dur,
            "cost": cost,
            "popularity": pop,
            "open_start": poi["open_start"],
            "open_end": poi["open_end"],
            "pace_fast": 1 if user_row["pace"] == "fast" else 0,
            "pace_slow": 1 if user_row["pace"] == "slow" else 0,
            "pace_moderate": 1 if user_row["pace"] == "moderate" else 0,
            "interest_match": match,
            "pace_fit": pace_score,
            "popularity_sq": pop ** 2,
            "duration_sq": dur ** 2,
            "cost_per_hour": cost / max(dur, 0.25),
            "match_x_pop": match * pop,
            "pace_x_duration": pace_score * dur,
            "cost_x_interest": cost * match,
            "duration_x_interest": dur * match,
            "distance_from_hotel": distance,
        }

        feature_vector = np.array([features[col] for col in feature_cols])
        feature_matrix.append(feature_vector)
        poi_ids.append(poi["id"])

    X = np.vstack(feature_matrix)
    X_scaled = scaler.transform(X)

    # Predict
    if isinstance(model, SimpleFFN):
        predictions = model.predict(X_scaled)
        predictions = predictions.flatten()
    else:
        # sklearn model
        predictions = model.predict(X_scaled)

    result_df = pois_df.copy()
    result_df["predicted_satisfaction"] = predictions

    return result_df

