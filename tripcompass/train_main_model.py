"""
Train the main neural network model for satisfaction prediction.

This replaces the Random Forest with a NumPy-based feed-forward neural network
as specified in the proposal.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from tripcompass.models.neural_network import SimpleFFN

RANDOM_SEED = 42

# 1. Load user–POI rating data
ratings_path = "tripcompass/data/user_poi_ratings.csv"
df = pd.read_csv(ratings_path)
print("Loaded ratings:", df.shape)

# 2. Feature columns (baseline + new engineered ones)
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

target_col = "satisfaction"

X = df[feature_cols].values
y = df[target_col].values

# 3. Train/validation/test split (80/10/10)
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_SEED
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=RANDOM_SEED
)

print(f"Train size: {X_train.shape[0]}, Val size: {X_val.shape[0]}, Test size: {X_test.shape[0]}")

# 4. Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Ensure y is 2D for neural network
y_train = y_train.reshape(-1, 1)
y_val = y_val.reshape(-1, 1)
y_test_2d = y_test.reshape(-1, 1)

# 5. Main model: Simple Feed-Forward Neural Network
print("\n=== Training Neural Network ===")
input_dim = X_train_scaled.shape[1]
hidden_dim = 64

nn_model = SimpleFFN(
    input_dim=input_dim,
    hidden_dim=hidden_dim,
    random_seed=RANDOM_SEED,
)

# Train the model
nn_model.train(
    X_train_scaled,
    y_train,
    X_val=X_val_scaled,
    y_val=y_val,
    epochs=200,
    learning_rate=0.01,
    batch_size=128,
    verbose=True,
)

# 6. Evaluate on test set
print("\n=== Evaluating on Test Set ===")
y_pred = nn_model.predict(X_test_scaled).flatten()

rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"RMSE: {rmse:.3f}")
print(f"MAE : {mae:.3f}")
print(f"R^2 : {r2:.3f}")

# Sample predictions
comparison = pd.DataFrame({
    "y_true": y_test[:10],
    "y_pred": np.round(y_pred[:10], 2)
})
print("\nSample predictions:")
print(comparison)

# 7. Save model and scaler
model_path = Path("tripcompass/main_nn_model.npz")
scaler_path = Path("tripcompass/main_scaler.joblib")

nn_model.save_weights(model_path)
joblib.dump(scaler, scaler_path)

print(f"\n✅ Saved main model to {model_path}")
print(f"✅ Saved scaler to {scaler_path}")

# 8. Save training history and metrics
reports_dir = Path("reports")
reports_dir.mkdir(exist_ok=True)

training_history = nn_model.get_training_history()
metrics = {
    "rmse": float(rmse),
    "mae": float(mae),
    "r2": float(r2),
    "model_type": "SimpleFFN",
    "input_dim": int(input_dim),
    "hidden_dim": int(hidden_dim),
    "epochs": 200,
    "learning_rate": 0.01,
    "batch_size": 128,
}

# Save training history
history_path = reports_dir / "main_model_training_history.json"
history_path.write_text(json.dumps(training_history, indent=2))

# Save metrics
metrics_path = reports_dir / "main_model_metrics.json"
metrics_path.write_text(json.dumps(metrics, indent=2))

print(f"✅ Saved training history to {history_path}")
print(f"✅ Saved metrics to {metrics_path}")
