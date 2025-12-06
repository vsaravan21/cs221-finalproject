# TripCompass: Personalized, Budget and Time-Aware Itineraries

## Data Pipeline

### Prerequisites
Install dependencies:
```bash
pip install -r requirements.txt
```

## Data Pipeline

### Important Note About Data

Please delete the existing `tripcompass/data/` folder in the repository before running the pipeline.  
The data files were too large to store on GitHub, which caused incomplete and duplicate data in earlier commits.

After deleting the folder:

1. Download `data.zip` (provided on Gradescope).
2. Unzip it.
3. Drag the entire unzipped contents into:

```text
tripcompass/data/
### Building the POI Catalog

1. **Download additional datasets (optional):**
   ```bash
   python3 -m tripcompass.data.download_additional_sources
   ```
   This will download datasets from SF Open Data Portal (e.g., film locations).

2. **Build the enriched POI catalog:**
   ```bash
   python3 -m tripcompass.data.build_pois
   ```
   
   **Inputs:** Raw CSV files in `tripcompass/data/`:
   - `pois_sf.csv` (base POIs)
   - `Recreation_and_Parks_Properties_20251122.csv` (parks)
   - `Registered_Business_Locations_-_San_Francisco_20251122.csv` (restaurants/businesses)
   - `Muni_Stops_20251122.csv` (transit stops)
   - `City_Facilities_-_Airport_(SFO)_Jurisdiction_or_Leased_20251122.csv` (airport)
   - `Film_Locations_in_San_Francisco.csv` (optional - film locations)
   
   **Outputs:**
   - `tripcompass/data/pois_sf_enriched.csv` - Combined and enriched POI catalog
   - `reports/data_reports/data_quality.json` - Validation report
   - `tripcompass/data/data_sources.json` - Data source manifest

3. **Inspect validation report** to confirm there are no blocking issues before training models.

## UI Prototype

The UI prototype is located in the `ui/` directory. To use it with live itinerary generation:

1. **Start the API server:**
   ```bash
   python -m tripcompass.api_server
   ```
   The server will run on `http://localhost:5000`

2. **Open the UI:**
   - Open `ui/index.html` in your web browser
   - Or use a local server: `python -m http.server 8000` then visit `http://localhost:8000/ui/`

3. **Use the interface:**
   - Adjust preferences (budget, days, pace, interests) using the sliders
   - Click "Generate Itinerary"
   - The itinerary will update based on your preferences!

**Note:** If the API server is not running, the UI will fall back to sample data. Make sure the server is running for live itinerary generation.

### Data Sources

The pipeline combines multiple data sources:

- **Base POIs** - Existing POI catalog
- **Curated Landmarks** - Major SF attractions (museums, landmarks, viewpoints) - 40+ entries including:
  - Museums: SFMOMA, de Young, California Academy of Sciences, Asian Art Museum, Exploratorium, etc.
  - Landmarks: Golden Gate Bridge, Alcatraz, Fisherman's Wharf, Coit Tower, etc.
  - Parks: Golden Gate Park, Presidio, Lands End, Dolores Park, etc.
  - Markets: Ferry Building, Chinatown, Union Square
- **SF Recreation & Parks** - Public parks and recreation facilities (~500 sampled)
- **Registered Businesses** - Restaurants and food services (~600 sampled)
- **Muni Stops** - Public transit stops (~400 sampled)
- **SFO Facilities** - Airport facilities (~80 sampled)
- **Film Locations** - Movie filming locations (if downloaded)

The pipeline automatically:
- Deduplicates POIs by name and coordinates
- Fills missing values with category-specific defaults
- Validates data quality (coordinates, hours, costs)
- Generates comprehensive reports
