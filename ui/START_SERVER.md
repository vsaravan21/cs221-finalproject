# Starting the TripCompass API Server

To make the UI respond to your preferences, you need to start the backend API server.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install flask flask-cors
   ```

2. **Start the API server:**
   ```bash
   python -m tripcompass.api_server
   ```

3. **Open the UI:**
   - Open `ui/index.html` in your browser
   - Or use a local server: `python -m http.server 8000` then visit `http://localhost:8000/ui/`

4. **Test it:**
   - Fill out the form with different preferences
   - Click "Generate Itinerary"
   - The itinerary should change based on your preferences!

## Troubleshooting

**If you see "API not available" in the console:**
- Make sure the Flask server is running on port 5001
- Check that there are no errors in the server terminal
- The UI will fall back to sample data if the API is unavailable

**If the server won't start:**
- Make sure all dependencies are installed
- Check that the data files exist (`tripcompass/data/user_profiles.csv`, etc.)
- Try running from the project root directory

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/generate` - Generate itinerary (expects JSON with user preferences)

**Note:** Port 5000 is often used by AirPlay on macOS, so the server uses port 5001 instead.

