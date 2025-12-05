# TripCompass UI Prototype

A simple HTML/CSS/JavaScript prototype demonstrating the TripCompass itinerary creator interface.

## Features

### ✅ Implemented
- **Profile Setup Form**
  - Trip details (destination, duration, budget)
  - Travel pace selector (Slow/Moderate/Fast)
  - Interest sliders (Food, Museums, Outdoors, etc.)
  - Real-time budget calculation

- **Timeline View**
  - Vertical timeline with activity cards
  - Color-coded categories
  - Transport mode indicators
  - Satisfaction scores
  - Cost tracking (per activity + cumulative)

- **Day Summary**
  - Activity time, transit time, buffer time
  - Daily cost vs budget
  - Feasibility status

- **Trip Overview**
  - Total cost, IQS score, satisfaction
  - Activity count

- **Interactive Elements**
  - Click activities to see details (modal)
  - Navigation between Itinerary and Summary views
  - Loading animation during generation

## How to Use

1. **Open the prototype:**
   ```bash
   # Simply open index.html in your web browser
   open ui/index.html
   ```

2. **Fill out the profile form:**
   - Adjust trip duration and budget
   - Select your travel pace
   - Set your interest levels using sliders

3. **Generate itinerary:**
   - Click "Generate Itinerary"
   - Watch the loading animation
   - View your personalized timeline

4. **Explore the itinerary:**
   - Click any activity card to see details
   - View day summary statistics
   - Switch to Summary view for trip overview

## File Structure

```
ui/
├── index.html      # Main HTML structure
├── styles.css      # All styling
├── script.js       # Interactive functionality
└── README.md       # This file
```

## Design Highlights

- **Modern, clean design** with blue primary color
- **Responsive layout** that works on mobile and desktop
- **Smooth animations** and transitions
- **Intuitive timeline** showing chronological flow
- **Visual indicators** for categories, transport modes, satisfaction

## Next Steps

To connect this to your Python backend:

1. **Create API endpoints** (FastAPI/Flask)
   - POST `/api/generate` - Generate itinerary
   - GET `/api/pois` - Get POI list
   - POST `/api/evaluate` - Evaluate itinerary

2. **Replace sample data** in `script.js` with API calls

3. **Add real-time features:**
   - Live POI search
   - Dynamic itinerary updates
   - Real map integration (Mapbox/Google Maps)

## Customization

- **Colors:** Edit CSS variables in `styles.css` (`:root` section)
- **Sample data:** Modify `sampleItinerary` object in `script.js`
- **Layout:** Adjust grid/flex layouts in `styles.css`

