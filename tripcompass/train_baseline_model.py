import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

RANDOM_SEED = 42

# 1. Load user–POI rating data
ratings_path = "data/user_poi_ratings.csv"  # adjust if needed
df = pd.read_csv(ratings_path)
print("Loaded ratings:", df.shape)

# 2. Choose feature columns and target
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
]

target_col = "satisfaction"

X = df[feature_cols].values
y = df[target_col].values

# 3. Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_SEED
)

print("Train size:", X_train.shape[0], "Test size:", X_test.shape[0])

# 4. Scale features (good practice for linear models)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 5. Train baseline model (Linear Regression)
model = LinearRegression()
model.fit(X_train_scaled, y_train)

# 6. Evaluate
y_pred = model.predict(X_test_scaled)

rmse = mean_squared_error(y_test, y_pred, squared=False)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\n=== Baseline Linear Regression Performance ===")
print(f"RMSE: {rmse:.3f}")
print(f"MAE : {mae:.3f}")
print(f"R^2 : {r2:.3f}")

# 7. Inspect a few predictions vs true labels
comparison = pd.DataFrame({
    "y_true": y_test[:10],
    "y_pred": np.round(y_pred[:10], 2)
})
print("\nSample predictions:")
print(comparison)

# 8. Save model + scaler for later use in planner
joblib.dump(model, "baseline_linear_model.joblib")
joblib.dump(scaler, "baseline_scaler.joblib")
print("\nSaved model to baseline_linear_model.joblib and scaler to baseline_scaler.joblib")
