"""
Test script for IQS evaluation metrics.
"""

from tripcompass.beam_planner import beam_search_itinerary_for_user, load_users_and_pois
from tripcompass.eval import ItineraryEvaluator, save_evaluation_report

def test_iqs_evaluation():
    """Test IQS evaluation on sample itineraries."""
    print("Testing IQS Evaluation")
    print("=" * 70)
    
    evaluator = ItineraryEvaluator()
    users, _ = load_users_and_pois()
    
    # Test on multiple users
    test_users = [0, 1, 2]
    all_results = {}
    
    for user_id in test_users:
        print(f"\n{'='*70}")
        print(f"Testing User {user_id}")
        print(f"{'='*70}")
        
        user = users[users["user_id"] == user_id].iloc[0]
        
        # Generate itinerary
        itinerary = beam_search_itinerary_for_user(
            user_id=user_id,
            beam_width=10,
            max_steps=8,
            day_start_hour=9.0,
            day_end_hour=21.0,
            mode="walk",
            travel_penalty_per_hour=0.2,
        )
        
        # Evaluate
        metrics = evaluator.evaluate_itinerary(
            itinerary, user, day_start_hour=9.0, day_end_hour=21.0
        )
        
        # Print results
        print(f"\nIQS Score: {metrics['iqs']:.3f}")
        print(f"  Total Satisfaction: {metrics['total_satisfaction']:.2f}")
        print(f"  Budget Fit: {metrics['budget_fit']:.3f} (used ${metrics['budget_used']:.2f} of ${user['budget']/user['days']:.2f})")
        print(f"  Feasibility: {metrics['feasibility_score']:.3f} ({'✓ Feasible' if metrics['is_feasible'] else '✗ Violations'})")
        print(f"  Diversity: {metrics['diversity_score']:.3f}")
        print(f"  Travel Efficiency: {metrics['travel_efficiency']:.3f} h/activity")
        print(f"  Activities: {metrics['num_activities']}")
        
        if metrics['category_breakdown']:
            print(f"  Categories: {dict(metrics['category_breakdown'])}")
        
        if metrics['num_violations'] > 0:
            print(f"\n  ⚠️  Violations:")
            for violation in metrics['violations']:
                print(f"     - {violation}")
        
        all_results[f"user_{user_id}"] = metrics
    
    # Summary statistics
    print(f"\n{'='*70}")
    print("Summary Statistics")
    print(f"{'='*70}")
    
    iqs_scores = [r['iqs'] for r in all_results.values()]
    feasibility_rates = [1.0 if r['is_feasible'] else 0.0 for r in all_results.values()]
    
    print(f"Average IQS: {sum(iqs_scores)/len(iqs_scores):.3f}")
    print(f"Feasibility Rate: {sum(feasibility_rates)/len(feasibility_rates)*100:.1f}%")
    print(f"Average Travel Efficiency: {sum(r['travel_efficiency'] for r in all_results.values())/len(all_results):.3f} h/activity")
    
    # Save results
    summary = {
        "summary": {
            "avg_iqs": float(sum(iqs_scores)/len(iqs_scores)),
            "feasibility_rate": float(sum(feasibility_rates)/len(feasibility_rates)),
            "avg_travel_efficiency": float(sum(r['travel_efficiency'] for r in all_results.values())/len(all_results)),
        },
        "per_user": all_results
    }
    
    save_evaluation_report(summary, "reports/iqs_evaluation_report.json")
    print(f"\n✅ Saved evaluation report to reports/iqs_evaluation_report.json")
    
    return all_results

if __name__ == "__main__":
    test_iqs_evaluation()

