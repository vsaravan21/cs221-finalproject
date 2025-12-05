"""
Itinerary Quality Score (IQS) and evaluation metrics.

Implements the evaluation metrics from the proposal:
- Total predicted satisfaction
- Budget fit
- Time feasibility
- Category diversity
- Combined IQS score
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


class ItineraryEvaluator:
    """
    Evaluates itinerary quality using multiple metrics.
    """

    def __init__(
        self,
        satisfaction_weight: float = 0.4,
        budget_weight: float = 0.2,
        feasibility_weight: float = 0.3,
        diversity_weight: float = 0.1,
    ):
        """
        Initialize evaluator with weights for IQS components.
        
        Args:
            satisfaction_weight: Weight for total satisfaction (default 0.4)
            budget_weight: Weight for budget fit (default 0.2)
            feasibility_weight: Weight for feasibility (default 0.3)
            diversity_weight: Weight for category diversity (default 0.1)
        """
        self.satisfaction_weight = satisfaction_weight
        self.budget_weight = budget_weight
        self.feasibility_weight = feasibility_weight
        self.diversity_weight = diversity_weight

    def compute_total_satisfaction(self, itinerary_state) -> float:
        """
        Compute total predicted satisfaction for the itinerary.
        
        Args:
            itinerary_state: ItineraryState object from beam planner
            
        Returns:
            Total satisfaction score
        """
        return float(itinerary_state.total_satisfaction)

    def compute_budget_fit(
        self, itinerary_state, total_budget: float, daily_budget: float
    ) -> float:
        """
        Compute budget fit score.
        
        Score is higher when:
        - Budget is used efficiently (not too little, not too much)
        - Remaining budget is reasonable
        
        Args:
            itinerary_state: ItineraryState object
            total_budget: Total trip budget
            daily_budget: Daily budget allocation
            
        Returns:
            Budget fit score in [0, 1]
        """
        spent = daily_budget - itinerary_state.remaining_budget
        budget_utilization = spent / daily_budget if daily_budget > 0 else 0.0

        # Ideal utilization is around 70-90%
        if 0.7 <= budget_utilization <= 0.9:
            fit_score = 1.0
        elif 0.5 <= budget_utilization < 0.7:
            fit_score = 0.7 + 0.3 * (budget_utilization - 0.5) / 0.2
        elif 0.9 < budget_utilization <= 1.0:
            fit_score = 1.0 - 0.3 * (budget_utilization - 0.9) / 0.1
        else:
            fit_score = max(0.0, budget_utilization * 0.7)

        return float(fit_score)

    def check_feasibility(
        self,
        itinerary_state,
        day_start_hour: float = 9.0,
        day_end_hour: float = 21.0,
    ) -> Tuple[bool, List[str]]:
        """
        Check time feasibility of the itinerary.
        
        Args:
            itinerary_state: ItineraryState object
            day_start_hour: Start of day (default 9.0)
            day_end_hour: End of day (default 21.0)
            
        Returns:
            Tuple of (is_feasible, list_of_violations)
        """
        violations = []

        if not itinerary_state.activities:
            return True, []

        # Check each activity
        for i, act in enumerate(itinerary_state.activities):
            start_time = act["start_time"]
            end_time = act["end_time"]
            open_start = act.get("open_start", 0.0)
            open_end = act.get("open_end", 24.0)

            # Check if activity starts before day start
            if start_time < day_start_hour:
                violations.append(
                    f"Activity {i+1} ({act['name']}) starts before day start ({start_time:.2f} < {day_start_hour})"
                )

            # Check if activity ends after day end
            if end_time > day_end_hour:
                violations.append(
                    f"Activity {i+1} ({act['name']}) ends after day end ({end_time:.2f} > {day_end_hour})"
                )

            # Check if activity is within opening hours
            if start_time < open_start:
                violations.append(
                    f"Activity {i+1} ({act['name']}) starts before opening hours ({start_time:.2f} < {open_start})"
                )

            if end_time > open_end:
                violations.append(
                    f"Activity {i+1} ({act['name']}) ends after closing hours ({end_time:.2f} > {open_end})"
                )

            # Check if activity duration is reasonable
            duration = end_time - start_time
            if duration <= 0:
                violations.append(
                    f"Activity {i+1} ({act['name']}) has invalid duration ({duration:.2f})"
                )

        # Check for overlapping activities (shouldn't happen but good to verify)
        for i in range(len(itinerary_state.activities) - 1):
            curr_end = itinerary_state.activities[i]["end_time"]
            next_start = itinerary_state.activities[i + 1]["start_time"]
            if next_start < curr_end:
                violations.append(
                    f"Activities {i+1} and {i+2} overlap in time"
                )

        # Check total travel time (shouldn't be excessive)
        total_time = itinerary_state.current_time - day_start_hour
        activity_time = sum(
            act["end_time"] - act["start_time"]
            for act in itinerary_state.activities
        )
        travel_time = itinerary_state.total_travel_time

        if travel_time > activity_time * 0.5:  # Travel > 50% of activity time
            violations.append(
                f"Excessive travel time: {travel_time:.2f}h vs activity time {activity_time:.2f}h"
            )

        is_feasible = len(violations) == 0
        return is_feasible, violations

    def compute_feasibility_score(
        self,
        itinerary_state,
        day_start_hour: float = 9.0,
        day_end_hour: float = 21.0,
    ) -> float:
        """
        Compute feasibility score (0 = many violations, 1 = no violations).
        
        Args:
            itinerary_state: ItineraryState object
            day_start_hour: Start of day
            day_end_hour: End of day
            
        Returns:
            Feasibility score in [0, 1]
        """
        is_feasible, violations = self.check_feasibility(
            itinerary_state, day_start_hour, day_end_hour
        )

        if is_feasible:
            return 1.0

        # Penalize based on number of violations
        # Each violation reduces score by 0.2, minimum 0.0
        penalty = min(1.0, len(violations) * 0.2)
        return max(0.0, 1.0 - penalty)

    def compute_category_diversity(self, itinerary_state) -> float:
        """
        Compute category diversity score using entropy.
        
        Higher diversity = more unique categories visited.
        
        Args:
            itinerary_state: ItineraryState object
            
        Returns:
            Diversity score in [0, 1]
        """
        if not itinerary_state.activities:
            return 0.0

        # Extract categories from activities
        categories = [
            act.get("category", "unknown") for act in itinerary_state.activities
        ]

        if not categories:
            return 0.0

        # Count category frequencies
        category_counts = Counter(categories)
        n_activities = len(categories)
        n_categories = len(category_counts)

        # Maximum diversity: all activities are different categories
        max_diversity = min(n_activities, 10.0)  # Cap at 10 categories

        # Simple diversity: ratio of unique categories to activities
        diversity_ratio = n_categories / n_activities

        # Entropy-based diversity (normalized)
        if n_categories == 1:
            entropy = 0.0
        else:
            probs = [count / n_activities for count in category_counts.values()]
            entropy = -sum(p * np.log2(p) for p in probs if p > 0)
            max_entropy = np.log2(n_categories)
            entropy = entropy / max_entropy if max_entropy > 0 else 0.0

        # Combine ratio and entropy
        diversity_score = 0.6 * diversity_ratio + 0.4 * entropy

        return float(np.clip(diversity_score, 0.0, 1.0))

    def compute_travel_efficiency(self, itinerary_state) -> float:
        """
        Compute travel efficiency (transit minutes per activity).
        
        Lower is better (less travel per activity).
        
        Args:
            itinerary_state: ItineraryState object
            
        Returns:
            Travel efficiency: hours of travel per activity
        """
        n_activities = len(itinerary_state.activities)
        if n_activities == 0:
            return 0.0

        travel_per_activity = itinerary_state.total_travel_time / n_activities
        return float(travel_per_activity)

    def compute_iqs(
        self,
        itinerary_state,
        total_budget: float,
        daily_budget: float,
        day_start_hour: float = 9.0,
        day_end_hour: float = 21.0,
        normalize_satisfaction: bool = True,
    ) -> Dict[str, float]:
        """
        Compute complete Itinerary Quality Score (IQS).
        
        Args:
            itinerary_state: ItineraryState object
            total_budget: Total trip budget
            daily_budget: Daily budget allocation
            day_start_hour: Start of day
            day_end_hour: End of day
            normalize_satisfaction: Whether to normalize satisfaction to [0,1]
            
        Returns:
            Dictionary with all metrics and combined IQS score
        """
        # Component scores
        total_satisfaction = self.compute_total_satisfaction(itinerary_state)
        budget_fit = self.compute_budget_fit(
            itinerary_state, total_budget, daily_budget
        )
        feasibility_score = self.compute_feasibility_score(
            itinerary_state, day_start_hour, day_end_hour
        )
        diversity_score = self.compute_category_diversity(itinerary_state)
        travel_efficiency = self.compute_travel_efficiency(itinerary_state)

        # Normalize satisfaction (assuming max possible is ~50 for a day)
        if normalize_satisfaction:
            satisfaction_normalized = min(1.0, total_satisfaction / 50.0)
        else:
            satisfaction_normalized = total_satisfaction

        # Combined IQS score (weighted sum)
        iqs = (
            self.satisfaction_weight * satisfaction_normalized
            + self.budget_weight * budget_fit
            + self.feasibility_weight * feasibility_score
            + self.diversity_weight * diversity_score
        )

        # Check feasibility
        is_feasible, violations = self.check_feasibility(
            itinerary_state, day_start_hour, day_end_hour
        )

        return {
            "iqs": float(iqs),
            "total_satisfaction": float(total_satisfaction),
            "satisfaction_normalized": float(satisfaction_normalized),
            "budget_fit": float(budget_fit),
            "feasibility_score": float(feasibility_score),
            "is_feasible": bool(is_feasible),
            "num_violations": len(violations),
            "diversity_score": float(diversity_score),
            "travel_efficiency": float(travel_efficiency),
            "travel_hours": float(itinerary_state.total_travel_time),
            "num_activities": len(itinerary_state.activities),
            "budget_used": float(daily_budget - itinerary_state.remaining_budget),
            "budget_remaining": float(itinerary_state.remaining_budget),
        }

    def evaluate_itinerary(
        self,
        itinerary_state,
        user_profile: pd.Series,
        day_start_hour: float = 9.0,
        day_end_hour: float = 21.0,
    ) -> Dict[str, object]:
        """
        Complete evaluation of an itinerary.
        
        Args:
            itinerary_state: ItineraryState object
            user_profile: User profile (pandas Series)
            day_start_hour: Start of day
            day_end_hour: End of day
            
        Returns:
            Complete evaluation dictionary
        """
        total_budget = float(user_profile.get("budget", 1000.0))
        days = max(1, int(user_profile.get("days", 1)))
        daily_budget = total_budget / days

        metrics = self.compute_iqs(
            itinerary_state, total_budget, daily_budget, day_start_hour, day_end_hour
        )

        # Add feasibility details
        is_feasible, violations = self.check_feasibility(
            itinerary_state, day_start_hour, day_end_hour
        )
        metrics["violations"] = violations

        # Add category breakdown
        if itinerary_state.activities:
            categories = [
                act.get("category", "unknown")
                for act in itinerary_state.activities
            ]
            metrics["category_breakdown"] = dict(Counter(categories))

        return metrics


def compute_ndcg_at_k(
    y_true: np.ndarray, y_pred: np.ndarray, k: int = 10
) -> float:
    """
    Compute Normalized Discounted Cumulative Gain at k.
    
    Used for ranking evaluation - measures how well the model ranks
    top activities by satisfaction.
    
    Args:
        y_true: True satisfaction scores
        y_pred: Predicted satisfaction scores
        k: Number of top items to consider
        
    Returns:
        NDCG@k score in [0, 1]
    """
    # Get top k indices by predicted scores
    top_k_pred = np.argsort(y_pred)[-k:][::-1]
    top_k_true = np.argsort(y_true)[-k:][::-1]

    # Compute DCG for predicted ranking
    dcg = 0.0
    for i, idx in enumerate(top_k_pred):
        rel = y_true[idx]
        dcg += rel / np.log2(i + 2)  # i+2 because log2(1) = 0

    # Compute IDCG (ideal DCG)
    idcg = 0.0
    for i, idx in enumerate(top_k_true):
        rel = y_true[idx]
        idcg += rel / np.log2(i + 2)

    if idcg == 0:
        return 0.0

    return float(dcg / idcg)


def save_evaluation_report(
    evaluation_results: Dict[str, object], output_path: str | Path
) -> None:
    """
    Save evaluation results to JSON file.
    
    Args:
        evaluation_results: Dictionary of evaluation metrics
        output_path: Path to save the report
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert numpy types to native Python types for JSON serialization
    def convert_to_json_serializable(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_json_serializable(item) for item in obj]
        return obj

    serializable_results = convert_to_json_serializable(evaluation_results)
    output_path.write_text(json.dumps(serializable_results, indent=2))


if __name__ == "__main__":
    # Example usage
    print("Itinerary Quality Score (IQS) Evaluation Module")
    print("=" * 70)
    print("\nThis module provides:")
    print("  - Total predicted satisfaction")
    print("  - Budget fit score")
    print("  - Time feasibility checks")
    print("  - Category diversity metric")
    print("  - Combined IQS score")
    print("  - Travel efficiency")
    print("\nImport and use ItineraryEvaluator to evaluate itineraries.")

