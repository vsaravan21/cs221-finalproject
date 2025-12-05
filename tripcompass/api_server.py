"""
Flask API server for TripCompass UI.

Provides endpoints to generate itineraries based on user preferences.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tripcompass.beam_planner import beam_search_itinerary_for_user, load_users_and_pois
from tripcompass.eval import ItineraryEvaluator
from tripcompass.data.build_training_data import generate_user_profiles
import pandas as pd
import numpy as np

app = Flask(__name__, static_folder='../ui', static_url_path='')
# Enable CORS for frontend - allow all origins in production
CORS(app, resources={r"/api/*": {"origins": "*"}})

evaluator = ItineraryEvaluator()


def format_time(hours: float) -> str:
    """Convert float hours to HH:MM string."""
    h = int(hours)
    m = int(round((hours - h) * 60))
    return f"{h:02d}:{m:02d}"


def format_time_minutes(hours: float) -> str:
    """Format time in hours to 'X min' string."""
    minutes = int(round(hours * 60))
    return f"{minutes} min"


@app.route('/')
def index():
    """Serve the main UI page."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from the UI directory."""
    return send_from_directory(app.static_folder, path)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@app.route('/api/similar-activities', methods=['POST'])
def get_similar_activities():
    """
    Get similar activities to swap with.
    
    Expected JSON body:
    {
        "category": "museum",
        "exclude_id": "activity_id_to_exclude",
        "current_lat": 37.7749,
        "current_lon": -122.4194
    }
    """
    try:
        data = request.json
        category = data.get('category', 'museum')
        exclude_id = data.get('exclude_id', '')
        current_lat = float(data.get('current_lat', 37.7749))
        current_lon = float(data.get('current_lon', -122.4194))
        
        # Load POIs
        _, pois_df = load_users_and_pois()
        
        # Filter by category and exclude the current activity
        similar_pois = pois_df[
            (pois_df['category'] == category) & 
            (pois_df['id'] != exclude_id) &
            (pois_df['category'] != 'transport')  # Don't suggest transport as activities
        ].copy()
        
        if len(similar_pois) == 0:
            return jsonify({
                "success": True,
                "activities": []
            })
        
        # Calculate distance from current location
        import math
        def haversine_km(lat1, lon1, lat2, lon2):
            R = 6371.0
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c
        
        similar_pois['distance'] = similar_pois.apply(
            lambda row: haversine_km(current_lat, current_lon, row['lat'], row['lon']),
            axis=1
        )
        
        # Sort by distance (closer is better) and popularity
        similar_pois = similar_pois.sort_values(
            by=['distance', 'popularity'],
            ascending=[True, False]
        )
        
        # Return top 5 similar activities
        top_activities = similar_pois.head(5)
        
        activities = []
        for _, poi in top_activities.iterrows():
            activities.append({
                'id': poi['id'],
                'name': poi['name'],
                'category': poi['category'],
                'cost': float(poi['cost']),
                'duration_hours': float(poi['duration_hours']),
                'lat': float(poi['lat']),
                'lon': float(poi['lon']),
                'open_start': float(poi['open_start']),
                'open_end': float(poi['open_end']),
                'popularity': float(poi['popularity']),
                'distance': float(poi['distance']),
            })
        
        return jsonify({
            "success": True,
            "activities": activities
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/generate', methods=['POST'])
def generate_itinerary():
    """
    Generate itinerary based on user preferences.
    
    Expected JSON body:
    {
        "days": 3,
        "budget": 500,
        "pace": "moderate",
        "interests": {
            "food": 0.7,
            "museums": 0.8,
            "outdoors": 0.6,
            "parks": 0.6,
            "shopping": 0.4,
            "nightlife": 0.3,
            "culture": 0.5
        },
        "hotel_lat": 37.7749,
        "hotel_lon": -122.4194
    }
    """
    try:
        data = request.json
        
        # Extract preferences
        days = int(data.get('days', 3))
        budget = float(data.get('budget', 500))
        pace = data.get('pace', 'moderate')
        interests = data.get('interests', {})
        hotel_lat = float(data.get('hotel_lat', 37.7749))
        hotel_lon = float(data.get('hotel_lon', -122.4194))
        
        # Create temporary user profile
        user_profile = create_user_profile(
            days=days,
            budget=budget,
            pace=pace,
            interests=interests,
            hotel_lat=hotel_lat,
            hotel_lon=hotel_lon
        )
        
        # Generate itineraries for ALL requested days
        daily_budget = budget / days
        all_days = []
        total_cost = 0.0
        total_activities = 0
        visited_poi_ids = set()  # Track visited POIs across all days
        
        # Load POIs for lat/lon/duration lookup
        _, pois_df = load_users_and_pois()
        
        for day_idx in range(days):
            # Generate itinerary for this day, excluding already visited POIs
            itinerary_state = beam_search_itinerary_for_user(
                user_id=user_profile['user_id'],
                day_index=day_idx,
                beam_width=15,
                max_steps=10,
                day_start_hour=9.0,
                day_end_hour=21.0,
                mode='auto',  # Use auto mode for dynamic travel selection
                travel_penalty_per_hour=0.2,
                exclude_poi_ids=visited_poi_ids,  # Pass visited POIs to exclude
            )
            
            # Add this day's visited POIs to the set
            for act in itinerary_state.activities:
                visited_poi_ids.add(act.get('poi_id'))
            
            # Format activities for this day
            activities = []
            day_cumulative_cost = 0.0
            
            for act in itinerary_state.activities:
                # Skip transport POIs - they should not be activities
                if act.get('category', 'unknown') == 'transport':
                    continue
                    
                day_cumulative_cost += act.get('cost', 0.0)
                
                travel_mode = act.get('travel_mode', 'walk')
                travel_time = act.get('travel_time_from_prev', 0.0)
                
                # Get POI details for lat/lon/duration
                poi_row = pois_df[pois_df['id'] == act.get('poi_id')]
                lat = float(poi_row['lat'].iloc[0]) if len(poi_row) > 0 else 37.7749
                lon = float(poi_row['lon'].iloc[0]) if len(poi_row) > 0 else -122.4194
                duration_hours = float(poi_row['duration_hours'].iloc[0]) if len(poi_row) > 0 else (act['end_time'] - act['start_time'])
                
                activities.append({
                    'id': act.get('poi_id', len(activities) + 1),
                    'poi_id': act.get('poi_id', len(activities) + 1),
                    'time': f"{format_time(act['start_time'])} - {format_time(act['end_time'])}",
                    'start_time': act['start_time'],
                    'end_time': act['end_time'],
                    'name': act['name'],
                    'category': act.get('category', 'unknown'),
                    'cost': float(act.get('cost', 0.0)),
                    'cumulative_cost': float(day_cumulative_cost),
                    'travel_mode': travel_mode,
                    'travel_time': format_time_minutes(travel_time) if travel_time > 0 else None,
                    'travel_time_hours': float(travel_time),
                    'open_start': float(act.get('open_start', 0.0)),
                    'open_end': float(act.get('open_end', 24.0)),
                    'lat': lat,
                    'lon': lon,
                    'duration_hours': duration_hours,
                })
            
            # Calculate day summary
            activity_time = sum(
                act['end_time'] - act['start_time'] for act in activities
            )
            transit_time = sum(
                act['travel_time_hours'] for act in activities
            )
            
            # Calculate buffer time
            day_start = 9.0
            day_end = 21.0
            buffer_time = 0.0
            if activities:
                first_start = activities[0]['start_time']
                buffer_time += max(0, first_start - day_start)
                
                for i in range(len(activities) - 1):
                    curr_end = activities[i]['end_time']
                    next_start = activities[i + 1]['start_time']
                    gap = next_start - curr_end
                    if gap > 0:
                        buffer_time += gap
                
                last_end = activities[-1]['end_time']
                buffer_time += max(0, day_end - last_end)
            
            # Evaluate itinerary (for feasibility check only - not shown to customer)
            users_df, _ = load_users_and_pois()
            user_row = users_df[users_df['user_id'] == user_profile['user_id']].iloc[0]
            
            metrics = evaluator.evaluate_itinerary(
                itinerary_state, user_row, day_start_hour=9.0, day_end_hour=21.0
            )
            
            all_days.append({
                'day': day_idx + 1,
                'activities': activities,
                'summary': {
                    'activity_time_hours': float(activity_time),
                    'activity_time': f"{activity_time:.1f} hours",
                    'transit_time_hours': float(transit_time),
                    'transit_time': format_time_minutes(transit_time),
                    'buffer_time_hours': float(buffer_time),
                    'buffer_time': format_time_minutes(buffer_time),
                    'daily_cost': f"${day_cumulative_cost:.2f} / ${daily_budget:.2f}",
                    'cost_used': float(day_cumulative_cost),
                    'cost_remaining': float(daily_budget - day_cumulative_cost),
                    'status': '✓ Feasible' if metrics['is_feasible'] else '✗ Violations',
                    'is_feasible': metrics['is_feasible'],
                }
            })
            
            total_cost += day_cumulative_cost
            total_activities += len(activities)
        
        # Build response (customer-facing, no developer metrics)
        response = {
            'success': True,
            'days': days,
            'total_budget': budget,
            'daily_budget': daily_budget,
            'total_cost': total_cost,
            'total_activities': total_activities,
            'itineraries': all_days,
            'user_profile': user_profile  # Include for hotel location and client-side calculations
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def create_user_profile(days, budget, pace, interests, hotel_lat, hotel_lon):
    """Create a temporary user profile and add to users dataframe."""
    users_df, _ = load_users_and_pois()
    
    # Find next available user_id
    max_user_id = users_df['user_id'].max() if len(users_df) > 0 else -1
    new_user_id = int(max_user_id) + 1
    
    # All interest dimensions (must match build_training_data.py)
    INTEREST_DIMENSIONS = [
        "food",
        "museums",
        "outdoors",
        "parks",
        "shopping",
        "nightlife",
        "culture",
    ]
    
    # Create user profile
    user_profile = {
        'user_id': new_user_id,
        'pace': pace,
        'days': days,
        'budget': budget,
        'hotel_lat': hotel_lat,
        'hotel_lon': hotel_lon,
    }
    
    # Add all interest columns (use provided values or default to 0.5)
    for interest_name in INTEREST_DIMENSIONS:
        # Map 'parks' to 'outdoors' if not provided separately
        if interest_name == 'parks' and 'parks' not in interests:
            value = interests.get('outdoors', 0.5)
        else:
            value = interests.get(interest_name, 0.5)
        user_profile[f'interest_{interest_name}'] = float(value)
    
    # Add to dataframe
    new_row = pd.DataFrame([user_profile])
    users_df = pd.concat([users_df, new_row], ignore_index=True)
    
    # Save updated users (temporary - in production you'd use a database)
    from tripcompass import config
    import pathlib
    
    # Use config path for consistency
    users_path = config.DATA_DIR / "user_profiles.csv"
    if not users_path.exists():
        users_path = pathlib.Path("tripcompass/data/user_profiles.csv")
    
    users_df.to_csv(users_path, index=False)
    
    return user_profile


if __name__ == '__main__':
    # Get port from environment variable (for production) or default to 5001
    port = int(os.environ.get('PORT', 5001))
    # Set debug mode based on environment
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("Starting TripCompass API server...")
    print(f"API will be available at http://localhost:{port}")
    print(f"Frontend should connect to: http://localhost:{port}/api/generate")
    print(f"Debug mode: {debug}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)

