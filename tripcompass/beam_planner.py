import math
import numpy as np
import pandas as pd

from tripcompass.data.build_training_data import pace_fit, interest_tag_match
from tripcompass.models.inference import load_main_model, predict_batch


# ----------------------------------------
# Model & Data Loading
# ----------------------------------------

def load_model_and_scaler():
    """Load the main neural network model and scaler."""
    model, scaler = load_main_model(
        model_path="tripcompass/main_nn_model.npz",
        scaler_path="tripcompass/main_scaler.joblib",
    )
    return model, scaler


def load_users_and_pois():
    from tripcompass import config
    import pathlib
    
    # Use config paths for consistency
    users_path = config.DATA_DIR / "user_profiles.csv"
    pois_path = config.POI_OUTPUT_PATH
    
    # Fallback to relative paths if config paths don't exist
    if not users_path.exists():
        users_path = pathlib.Path("tripcompass/data/user_profiles.csv")
    if not pois_path.exists():
        pois_path = pathlib.Path("tripcompass/data/pois_sf_enriched.csv")
    
    users = pd.read_csv(users_path)
    pois = pd.read_csv(pois_path)
    return users, pois


# ----------------------------------------
# Feature Construction for (user, poi)
# Must match training features
# ----------------------------------------

FEATURE_COLS_ORDER = [
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


def make_feature_vector(user_row, poi_row):
    match = interest_tag_match(user_row, poi_row.get("tags", ""), poi_row.get("category"))
    pace_score = pace_fit(user_row["pace"], poi_row["duration_hours"])

    dur = float(poi_row["duration_hours"])
    cost = float(poi_row["cost"])
    pop = float(poi_row["popularity"])

    distance = math.sqrt(
        (poi_row["lat"] - user_row["hotel_lat"]) ** 2 +
        (poi_row["lon"] - user_row["hotel_lon"]) ** 2
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

    return np.array([features[col] for col in FEATURE_COLS_ORDER])


def predict_poi_scores_for_user(user_row, pois_df, model, scaler):
    """
    Predict satisfaction scores for a user across all POIs.
    Uses the inference module's predict_batch function for consistency.
    """
    return predict_batch(model, scaler, user_row, pois_df)


# ----------------------------------------
# Travel Time Approximation
# ----------------------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points on Earth (in km)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def select_travel_mode(lat1, lon1, lat2, lon2, default_mode="walk"):
    """
    Select travel mode based on distance and default preference.
    
    Logic:
    - < 1 km: walk
    - 1-5 km: transit (if available) or walk
    - > 5 km: transit or car/Uber
    
    Args:
        lat1, lon1: Starting coordinates
        lat2, lon2: Ending coordinates
        default_mode: Default mode preference
        
    Returns:
        Selected mode: "walk", "transit", or "Uber"
    """
    d_km = haversine_km(lat1, lon1, lat2, lon2)
    
    if default_mode == "walk":
        # Always walk if explicitly requested
        return "walk"
    elif default_mode == "transit":
        # Use transit for longer distances
        if d_km < 0.5:
            return "walk"
        else:
            return "transit"
    elif default_mode == "Uber" or default_mode == "car":
        # Use Uber for longer distances
        if d_km < 0.5:
            return "walk"
        elif d_km < 2.0:
            return "transit"
        else:
            return "Uber"
    else:
        # Default logic: walk for short, transit for medium, Uber for long
        if d_km < 1.0:
            return "walk"
        elif d_km < 5.0:
            return "transit"
        else:
            return "Uber"


def travel_time_hours(lat1, lon1, lat2, lon2, mode="walk"):
    """
    Approximate travel time in hours.
    
    Includes pickup/wait time for transit and Uber.
    """
    d_km = haversine_km(lat1, lon1, lat2, lon2)
    
    if mode == "walk":
        speed = 4.0  # km/h
        wait_time = 0.0
    elif mode == "transit":
        speed = 12.0  # km/h (average transit speed)
        wait_time = 0.08  # ~5 minutes average wait time
    elif mode == "Uber" or mode == "car":
        speed = 25.0  # km/h (city driving average)
        wait_time = 0.13  # ~8 minutes pickup time
    else:
        speed = 4.0
        wait_time = 0.0
    
    travel_time = (d_km / speed) + wait_time
    return travel_time


# ----------------------------------------
# Beam Search Itinerary Planner (Single Day)
# ----------------------------------------

class ItineraryState:
    def __init__(
        self,
        activities,
        current_time,
        current_lat,
        current_lon,
        remaining_budget,
        total_satisfaction,
        total_travel_time,
        visited_ids,
        recent_categories=None
    ):
        self.activities = activities  # list of dicts
        self.current_time = current_time
        self.current_lat = current_lat
        self.current_lon = current_lon
        self.remaining_budget = remaining_budget
        self.total_satisfaction = total_satisfaction
        self.total_travel_time = total_travel_time
        self.visited_ids = visited_ids
        self.recent_categories = recent_categories if recent_categories else []  # Track last 2 categories for diversity

    def copy(self):
        return ItineraryState(
            activities=list(self.activities),
            current_time=self.current_time,
            current_lat=self.current_lat,
            current_lon=self.current_lon,
            remaining_budget=self.remaining_budget,
            total_satisfaction=self.total_satisfaction,
            total_travel_time=self.total_travel_time,
            visited_ids=set(self.visited_ids),
            recent_categories=list(self.recent_categories),
        )


def beam_search_itinerary_for_user(
    user_id,
    day_index=0,
    beam_width=10,
    max_steps=10,
    day_start_hour=9.0,
    day_end_hour=21.0,
    mode="walk",
    travel_penalty_per_hour=0.1,
    exclude_poi_ids=None,
):
    """
    Beam search day itinerary for a single user.
    
    Args:
        exclude_poi_ids: Set of POI IDs to exclude (e.g., already visited on previous days)
    """
    if exclude_poi_ids is None:
        exclude_poi_ids = set()
    
    model, scaler = load_model_and_scaler()
    users, pois = load_users_and_pois()

    user = users[users["user_id"] == user_id].iloc[0]
    total_budget = user["budget"]
    days = max(1, int(user["days"]))
    daily_budget = total_budget / days

    # Score POIs with the RF model
    scored_pois = predict_poi_scores_for_user(user, pois, model, scaler)
    
    # Filter out transport POIs - they are not activities, only used for routing
    # Transport POIs should not be selected as destinations
    scored_pois = scored_pois[scored_pois['category'] != 'transport'].copy()
    
    # Calculate interest match scores for each POI to prioritize by user interest
    def get_interest_match(poi_row):
        """Get interest match score for a POI."""
        category = poi_row.get("category", "unknown")
        if category in ["transport", "airport"]:
            return 0.0
        tags = poi_row.get("tags", "")
        return interest_tag_match(user, tags, category)
    
    scored_pois['interest_match'] = scored_pois.apply(get_interest_match, axis=1)
    
    # Calculate proportional interest weights for balanced selection
    # The goal is to ensure categories are selected proportionally to their interest scores
    # If food=1.0 and museums=0.7, we want roughly 59% food (1.0/1.7) and 41% museums (0.7/1.7)
    # Get all user interest values
    interest_values = [
        user.get('interest_food', 0.0),
        user.get('interest_museums', 0.0),
        user.get('interest_outdoors', 0.0),
        user.get('interest_parks', 0.0),
        user.get('interest_shopping', 0.0),
        user.get('interest_nightlife', 0.0),
        user.get('interest_culture', 0.0),
    ]
    # Sum of all interests (for normalization)
    total_interest = sum(max(0, iv) for iv in interest_values)
    
    # If total interest is 0, use uniform weights (shouldn't happen, but safety check)
    if total_interest == 0:
        interest_normalization_factor = 1.0
    else:
        # Use the interest_match directly as a proportional weight
        # This means a POI with interest_match=0.7 will score 70% of what a POI with interest_match=1.0 scores
        # We'll use this in the combined score calculation
        interest_normalization_factor = 1.0  # Don't divide - use interest_match directly as weight
    
    # Filter out already visited POIs (from previous days)
    if exclude_poi_ids:
        scored_pois = scored_pois[~scored_pois['id'].isin(exclude_poi_ids)].copy()
    
    # OPTIMIZATION: Limit candidate POIs to top 200 by combined score to speed up beam search
    # This prevents iterating over thousands of POIs for each state
    # NEW APPROACH: Use proportional scoring - interest_match is used directly as a weight
    # This ensures that a POI with interest_match=0.7 scores proportionally to one with interest_match=1.0
    # Combined score balances interest (proportional) with predicted satisfaction
    if len(scored_pois) > 200:
        # Use interest_match directly as a proportional weight (0.7 interest = 70% of 1.0 interest)
        # Combine with satisfaction to allow high-satisfaction lower-interest POIs to compete
        scored_pois['combined_score'] = (
            scored_pois['interest_match'] * 1.2 +  # Proportional weight - 0.7 gets 70% of 1.0
            scored_pois['predicted_satisfaction'] * 1.0   # Equal weight for satisfaction
        )
        scored_pois = scored_pois.nlargest(200, 'combined_score').copy()
        scored_pois = scored_pois.drop(columns=['combined_score'])
    
    # Sort by combined score (proportional) rather than strict interest_match first
    # This allows lower-interest categories to be mixed in proportionally
    if len(scored_pois) <= 200:
        scored_pois['combined_score'] = (
            scored_pois['interest_match'] * 1.2 +  # Proportional weight
            scored_pois['predicted_satisfaction'] * 1.0
        )
        scored_pois = scored_pois.sort_values(
            by=['combined_score'],  # Sort by balanced score, not just interest
            ascending=[False]
        ).copy()
        scored_pois = scored_pois.drop(columns=['combined_score'])

    # Create a lookup dict for interest_match scores to avoid repeated DataFrame lookups
    interest_match_lookup = dict(zip(scored_pois['id'], scored_pois['interest_match']))

    # initial state: at hotel, no activities
    start_state = ItineraryState(
        activities=[],
        current_time=day_start_hour,
        current_lat=user["hotel_lat"],
        current_lon=user["hotel_lon"],
        remaining_budget=daily_budget,
        total_satisfaction=0.0,
        total_travel_time=0.0,
        visited_ids=set(),
        recent_categories=[],
    )

    beam = [start_state]
    best_state = start_state

    for step in range(max_steps):
        new_beam = []

        for state in beam:
            # Try adding each unvisited POI (now limited to top 200)
            for _, poi in scored_pois.iterrows():
                poi_id = poi["id"]
                if poi_id in state.visited_ids:
                    continue

                # Select travel mode and compute travel time
                selected_mode = select_travel_mode(
                    state.current_lat, state.current_lon,
                    poi["lat"], poi["lon"],
                    default_mode=mode
                )
                t_travel = travel_time_hours(
                    state.current_lat, state.current_lon,
                    poi["lat"], poi["lon"],
                    mode=selected_mode
                )

                arrival_time = state.current_time + t_travel
                duration = float(poi["duration_hours"])
                finish_time = arrival_time + duration

                # Opening hours feasibility
                open_start = float(poi["open_start"])
                open_end = float(poi["open_end"])

                # must arrive after opening and leave before closing and day end
                if arrival_time < open_start or finish_time > min(open_end, day_end_hour):
                    continue

                # budget feasibility
                cost = float(poi["cost"])
                if cost > state.remaining_budget:
                    continue

                # Category diversity check: avoid stacking same category
                # But allow it if the POI is very close (within 0.5 km) to minimize travel
                poi_category = poi.get("category", "unknown")
                distance_km = haversine_km(state.current_lat, state.current_lon, poi["lat"], poi["lon"])
                
                # Check if last 2 activities were the same category
                if len(state.recent_categories) >= 2:
                    last_two_same = (state.recent_categories[-1] == poi_category == state.recent_categories[-2])
                    # Skip if same category 3 times in a row AND not very close
                    if last_two_same and distance_km > 0.5:
                        continue  # Skip to avoid stacking

                # If feasible, create new state
                new_state = state.copy()
                new_state.current_time = finish_time
                new_state.current_lat = poi["lat"]
                new_state.current_lon = poi["lon"]
                new_state.remaining_budget -= cost
                new_state.total_travel_time += t_travel
                new_state.total_satisfaction += float(poi["predicted_satisfaction"])
                new_state.visited_ids.add(poi_id)
                
                # Update recent categories (keep last 2)
                new_state.recent_categories.append(poi_category)
                if len(new_state.recent_categories) > 2:
                    new_state.recent_categories = new_state.recent_categories[-2:]

                # Calculate cumulative cost
                cumulative_cost = daily_budget - new_state.remaining_budget
                
                new_state.activities.append({
                    "poi_id": poi_id,
                    "name": poi["name"],
                    "category": poi_category,
                    "start_time": arrival_time,
                    "end_time": finish_time,
                    "travel_time_from_prev": t_travel,
                    "travel_mode": selected_mode,
                    "cost": cost,
                    "cumulative_cost": cumulative_cost,
                    "predicted_satisfaction": float(poi["predicted_satisfaction"]),
                    "open_start": open_start,
                    "open_end": open_end,
                })

                new_beam.append(new_state)

            # Also keep the option of "stopping here"
            new_beam.append(state)

        if not new_beam:
            break

        # Rank states by objective: satisfaction - travel penalty + diversity bonus + interest bonus
        def score_state(s):
            base_score = s.total_satisfaction - travel_penalty_per_hour * s.total_travel_time
            
            # Interest-based scoring: use proportional weights instead of harsh penalties
            # This ensures categories are selected proportionally to their interest scores
            # OPTIMIZATION: Use lookup dict instead of DataFrame queries
            interest_score = 0.0
            zero_interest_penalty = 0.0
            for act in s.activities:
                poi_id = act.get("poi_id", "")
                interest_match = interest_match_lookup.get(poi_id, 0.0)
                
                if interest_match > 0.0:
                    # Add score proportional to interest match
                    # This means a 0.7 interest POI gets 70% of the score of a 1.0 interest POI
                    # Use interest_match directly as a proportional weight
                    interest_score += interest_match * 1.2  # Proportional weight
                else:
                    # Only penalize if truly 0 interest (user explicitly set to 0)
                    zero_interest_penalty += 2.0  # Reduced penalty to be less harsh
            
            base_score += interest_score
            base_score -= zero_interest_penalty
            
            # Diversity bonus: reward variety in categories
            if len(s.activities) > 1:
                categories = [act.get("category", "unknown") for act in s.activities]
                unique_categories = len(set(categories))
                diversity_bonus = 0.15 * unique_categories  # Bonus for variety
                base_score += diversity_bonus
            
            # Penalty for consecutive same categories (but only if not very close)
            if len(s.recent_categories) >= 2:
                if s.recent_categories[-1] == s.recent_categories[-2]:
                    # Apply penalty, but smaller if activities are close together
                    # (This is already handled in filtering, but add small penalty to scoring)
                    base_score -= 0.1  # Small penalty for consecutive same category
            
            return base_score

        new_beam.sort(key=score_state, reverse=True)
        beam = new_beam[:beam_width]

        # update best_state
        if score_state(beam[0]) > score_state(best_state):
            best_state = beam[0]

    return best_state


# ----------------------------------------
# Pretty-printing the itinerary
# ----------------------------------------

def format_time(t):
    """Convert float hour to HH:MM string."""
    h = int(t)
    m = int(round((t - h) * 60))
    return f"{h:02d}:{m:02d}"


def format_time_minutes(hours: float) -> str:
    """Format time in hours to 'X min' string."""
    minutes = int(round(hours * 60))
    return f"{minutes} min"


def compute_day_summary(state, day_start_hour: float = 9.0, day_end_hour: float = 21.0):
    """
    Compute per-day summary statistics.
    
    Returns:
        Dictionary with activity_time, transit_time, buffer_time, total_cost
    """
    if not state.activities:
        return {
            "activity_time": 0.0,
            "transit_time": 0.0,
            "buffer_time": 0.0,
            "total_cost": 0.0,
        }
    
    # Activity time (sum of durations)
    activity_time = sum(
        act["end_time"] - act["start_time"] for act in state.activities
    )
    
    # Transit time (sum of travel times)
    transit_time = state.total_travel_time
    
    # Buffer time (time between activities + end of day)
    buffer_time = 0.0
    if len(state.activities) > 0:
        # Time from day start to first activity
        first_start = state.activities[0]["start_time"]
        buffer_time += max(0, first_start - day_start_hour)
        
        # Time between activities
        for i in range(len(state.activities) - 1):
            curr_end = state.activities[i]["end_time"]
            next_start = state.activities[i + 1]["start_time"]
            gap = next_start - curr_end
            if gap > 0:
                buffer_time += gap
        
        # Time from last activity to day end
        last_end = state.activities[-1]["end_time"]
        buffer_time += max(0, day_end_hour - last_end)
    
    # Total cost
    total_cost = sum(act["cost"] for act in state.activities)
    
    return {
        "activity_time": activity_time,
        "transit_time": transit_time,
        "buffer_time": buffer_time,
        "total_cost": total_cost,
    }


def print_itinerary(
    state, user_id, day_start_hour: float = 9.0, day_end_hour: float = 21.0, 
    include_evaluation: bool = True
):
    """
    Print itinerary with enhanced formatting matching proposal spec.
    
    Args:
        state: ItineraryState object
        user_id: User ID
        day_start_hour: Start of day (default 9.0)
        day_end_hour: End of day (default 21.0)
        include_evaluation: Whether to include IQS evaluation
    """
    from tripcompass.beam_planner import load_users_and_pois
    
    users, _ = load_users_and_pois()
    user = users[users["user_id"] == user_id].iloc[0]
    daily_budget = user["budget"] / max(1, user["days"])
    
    print(f"\n{'='*70}")
    print(f"Day 1 Itinerary for User {user_id}")
    print(f"{'='*70}")
    
    if not state.activities:
        print("No activities chosen.")
        return
    
    # Print each activity with transport mode
    print("\nActivities:")
    for i, act in enumerate(state.activities, 1):
        category = act.get("category", "unknown")
        travel_mode = act.get("travel_mode", "walk")
        travel_min = format_time_minutes(act["travel_time_from_prev"])
        
        # Format travel leg description
        if i == 1:
            travel_desc = f"from hotel ({travel_mode}, {travel_min})"
        else:
            travel_desc = f"{travel_mode} {travel_min}"
        
        print(
            f"{i}. {format_time(act['start_time'])} - {format_time(act['end_time'])} | "
            f"{act['name']} ({category})"
        )
        if i > 1 or travel_mode != "walk":
            print(f"   → {travel_desc}")
        print(
            f"   Cost: ${act['cost']:.2f} | "
            f"Cumulative: ${act.get('cumulative_cost', 0):.2f} | "
            f"Pred. Satisfaction: {act['predicted_satisfaction']:.2f}"
        )
        print()
    
    # Per-day summary
    summary = compute_day_summary(state, day_start_hour, day_end_hour)
    print(f"{'='*70}")
    print("Day Summary:")
    print(f"  Activity Time: {summary['activity_time']:.1f} hours")
    print(f"  Transit Time: {format_time_minutes(summary['transit_time'])} ({summary['transit_time']:.2f} hours)")
    print(f"  Buffer Time: {format_time_minutes(summary['buffer_time'])} ({summary['buffer_time']:.2f} hours)")
    print(f"  Total Cost: ${summary['total_cost']:.2f} / ${daily_budget:.2f} daily budget")
    print(f"  Remaining Budget: ${state.remaining_budget:.2f}")
    print(f"  Total Predicted Satisfaction: {state.total_satisfaction:.2f}")
    print(f"{'='*70}")
    
    # Add IQS evaluation if requested
    if include_evaluation:
        try:
            from tripcompass.eval import ItineraryEvaluator
            
            evaluator = ItineraryEvaluator()
            metrics = evaluator.evaluate_itinerary(
                state, user, day_start_hour=day_start_hour, day_end_hour=day_end_hour
            )
            
            print(f"\nIQS Evaluation:")
            print(f"  IQS Score: {metrics['iqs']:.3f}")
            print(f"    - Satisfaction: {metrics['satisfaction_normalized']:.3f}")
            print(f"    - Budget Fit: {metrics['budget_fit']:.3f}")
            print(f"    - Feasibility: {metrics['feasibility_score']:.3f} ({'✓ Feasible' if metrics['is_feasible'] else '✗ Violations'})")
            print(f"    - Diversity: {metrics['diversity_score']:.3f}")
            print(f"    - Travel Efficiency: {metrics['travel_efficiency']:.3f} h/activity")
            if metrics['num_violations'] > 0:
                print(f"\n  ⚠️  {metrics['num_violations']} feasibility violation(s):")
                for violation in metrics['violations']:
                    print(f"     - {violation}")
        except Exception as e:
            print(f"\n⚠️  Could not compute IQS: {e}")


# ----------------------------------------
# Main entry point for quick testing
# ----------------------------------------

if __name__ == "__main__":
    user_id = 0  # change this to test different users
    best_day_plan = beam_search_itinerary_for_user(
        user_id=user_id,
        beam_width=10,
        max_steps=8,
        day_start_hour=9.0,
        day_end_hour=21.0,
        mode="walk",
        travel_penalty_per_hour=0.2,
    )
    print_itinerary(best_day_plan, user_id, day_start_hour=9.0, day_end_hour=21.0)
