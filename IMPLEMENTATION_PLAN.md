# TripCompass Model Implementation Plan

## Overview
Complete the model implementation to match the proposal: replace Random Forest with NumPy-based feed-forward neural network, integrate with beam search planner, and add comprehensive evaluation.

---

## Phase 1: Neural Network Model Implementation

### 1.1 Create NumPy Neural Network Class
**File:** `tripcompass/models/neural_network.py`

**Tasks:**
- [ ] Implement `SimpleFFN` class with:
  - One hidden layer with ReLU activation
  - Single linear output unit
  - Forward pass method
  - Backward pass (gradient computation)
  - Batch gradient descent training loop
- [ ] Methods needed:
  - `__init__(input_dim, hidden_dim, random_seed=42)`
  - `forward(X)` - compute predictions
  - `backward(X, y, y_pred)` - compute gradients
  - `train(X_train, y_train, X_val, y_val, epochs, learning_rate, batch_size)`
  - `predict(X)` - inference
  - `save_weights(path)` - save to .npz file
  - `load_weights(path)` - load from .npz file

**Key Requirements:**
- Use only NumPy (no PyTorch/TensorFlow)
- MSE loss function
- ReLU activation for hidden layer
- Linear output (no activation on final layer)
- Support batch training

---

### 1.2 Replace Random Forest with Neural Network
**File:** `tripcompass/train_main_model.py`

**Tasks:**
- [ ] Replace `RandomForestRegressor` with `SimpleFFN`
- [ ] Use same feature columns as baseline (18 features)
- [ ] Train with batch gradient descent
- [ ] Add validation set monitoring (early stopping optional)
- [ ] Save model weights to `main_nn_model.npz` (not .joblib)
- [ ] Keep scaler saving to `main_scaler.joblib`
- [ ] Log training curves (loss per epoch)
- [ ] Compare metrics: RMSE, MAE, R² vs baseline

**Expected Output:**
- `main_nn_model.npz` - neural network weights
- `main_scaler.joblib` - feature scaler
- Training metrics logged to console
- Optional: save training curves to `reports/training_curves.json`

---

### 1.3 Create Model Inference Helper
**File:** `tripcompass/models/__init__.py` or `tripcompass/models/inference.py`

**Tasks:**
- [ ] Create unified model loading interface:
  - `load_baseline_model()` - returns (model, scaler)
  - `load_main_model()` - returns (model, scaler)
- [ ] Create prediction wrapper:
  - `predict_satisfaction(model, scaler, user_row, poi_row)` - single prediction
  - `predict_batch(model, scaler, user_row, pois_df)` - batch predictions
- [ ] Handle both baseline (sklearn) and main (NumPy NN) models

---

## Phase 2: Update Beam Search Planner

### 2.1 Update Model Loading in Beam Planner
**File:** `tripcompass/beam_planner.py`

**Tasks:**
- [ ] Replace `load_model_and_scaler()` to use new inference helper
- [ ] Ensure it loads the NumPy neural network (not Random Forest)
- [ ] Update `predict_poi_scores_for_user()` to work with NN model
- [ ] Test that predictions match training-time behavior

---

### 2.2 Enhance Beam Search Output
**File:** `tripcompass/beam_planner.py`

**Tasks:**
- [ ] Add per-leg transport mode tracking (walk/transit/Uber)
- [ ] Add explicit travel time per leg
- [ ] Add buffer time calculation
- [ ] Format output to match proposal spec:
  - Per-day totals: activity time, transit time, buffer, cost
  - Per-activity: start/end times, travel mode, predicted satisfaction
  - Cumulative cost tracking
  - Feasibility flags

---

## Phase 3: Evaluation Metrics

### 3.1 Implement Itinerary Quality Score (IQS)
**File:** `tripcompass/eval.py`

**Tasks:**
- [ ] Implement IQS components:
  1. **Total predicted satisfaction** - sum of model scores
  2. **Budget fit** - ratio of used budget to total budget
  3. **Time feasibility** - penalty for violations (hours/window violations, excessive idle time)
  4. **Category diversity** - entropy or count of unique categories
- [ ] Combine into single IQS score (weighted sum)
- [ ] Add helper functions:
  - `compute_iqs(itinerary_state, user_profile)` - main IQS calculator
  - `check_feasibility(itinerary_state)` - returns violation list
  - `compute_travel_efficiency(itinerary_state)` - transit minutes per activity
  - `compute_category_diversity(itinerary_state)` - diversity metric

---

### 3.2 Model Evaluation Metrics
**File:** `tripcompass/eval.py` (or extend training scripts)

**Tasks:**
- [ ] Add ranking metrics:
  - `compute_ndcg_at_k(y_true, y_pred, k=10)` - NDCG@k for top activities
- [ ] Keep regression metrics:
  - RMSE, MAE, R² (already in training scripts)
- [ ] Save evaluation results to `reports/model_evaluation.json`

---

## Phase 4: Integration & Testing

### 4.1 Update Main Entry Point
**File:** `tripcompass/main.py` or `main.py`

**Tasks:**
- [ ] Integrate full pipeline:
  1. Load user profile
  2. Load POIs
  3. Load trained model (NN)
  4. Run beam search planner
  5. Compute IQS and feasibility
  6. Format and display itinerary
- [ ] Add command-line arguments for:
  - User ID
  - Beam width
  - Day index
  - Model choice (baseline vs main)

---

### 4.2 Create End-to-End Test
**File:** `tripcompass/test_pipeline.py` or add to existing test files

**Tasks:**
- [ ] Test full pipeline:
  1. Load data
  2. Train baseline model
  3. Train main model (NN)
  4. Generate itinerary
  5. Evaluate IQS
- [ ] Verify:
  - Models load correctly
  - Predictions are in valid range [1, 5]
  - Itineraries are feasible
  - IQS is computed correctly

---

## Phase 5: Documentation & Reporting

### 5.1 Update Training Scripts
**Files:** `tripcompass/train_baseline_model.py`, `tripcompass/train_main_model.py`

**Tasks:**
- [ ] Add proper logging to files:
  - Save metrics to `reports/baseline_metrics.json`
  - Save metrics to `reports/main_model_metrics.json`
- [ ] Add comparison table (baseline vs main)
- [ ] Include feature importance analysis (for baseline)

---

### 5.2 Create Model Comparison Report
**File:** `tripcompass/compare_models.py` (optional)

**Tasks:**
- [ ] Compare baseline vs main model:
  - RMSE, MAE, R² side-by-side
  - Sample predictions comparison
  - Training time comparison
- [ ] Generate report: `reports/model_comparison.json`

---

## Implementation Order

### Priority 1 (Core Functionality):
1. ✅ **Phase 1.1** - Create NumPy neural network class
2. ✅ **Phase 1.2** - Replace Random Forest with NN in training
3. ✅ **Phase 1.3** - Create model inference helpers
4. ✅ **Phase 2.1** - Update beam planner to use NN

### Priority 2 (Evaluation):
5. ✅ **Phase 3.1** - Implement IQS metrics
6. ✅ **Phase 3.2** - Add model evaluation metrics

### Priority 3 (Polish):
7. ✅ **Phase 2.2** - Enhance beam search output formatting
8. ✅ **Phase 4.1** - Update main entry point
9. ✅ **Phase 4.2** - End-to-end testing
10. ✅ **Phase 5.1** - Documentation updates

---

## Files to Create/Modify

### New Files:
- `tripcompass/models/__init__.py`
- `tripcompass/models/neural_network.py`
- `tripcompass/models/inference.py` (optional, can be in __init__.py)
- `tripcompass/eval.py`
- `reports/model_evaluation.json` (generated)
- `reports/baseline_metrics.json` (generated)
- `reports/main_model_metrics.json` (generated)

### Files to Modify:
- `tripcompass/train_main_model.py` - Replace RF with NN
- `tripcompass/beam_planner.py` - Update model loading
- `main.py` - Integrate full pipeline
- `tripcompass/train_baseline_model.py` - Add metrics saving

---

## Success Criteria

- [ ] Neural network trains successfully and beats baseline
- [ ] Model predictions are in range [1, 5]
- [ ] Beam search planner uses NN model correctly
- [ ] IQS is computed for all generated itineraries
- [ ] Feasibility checks pass (no hour violations, budget respected)
- [ ] End-to-end pipeline runs without errors
- [ ] All metrics logged to reports/

---

## Notes

- Keep feature engineering consistent across baseline and main model
- Use same random seed (42) for reproducibility
- Validate that NN model file format (.npz) is loadable
- Ensure backward compatibility if possible (can still load old RF model)

