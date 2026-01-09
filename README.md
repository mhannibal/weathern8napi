# Weather Map REST API

A REST API service that generates weather map visualizations from meteorological data.

## Features

- 🗺️ Generates weather map images from GeoJSON country maps + meteo data
- 🌡️ Displays temperature, precipitation, wind speed, cloud cover
- 🎯 Auto-detects country from meteo data
- 📁 Saves generated maps to organized folder structure
- ☁️ Weather icons based on WMO weather codes

## Folder Structure

```
wetherproject/
├── app.py                  # Main REST API server
├── test_api.py            # Test suite
├── requirements.txt       # Python dependencies
├── meteo.json            # Sample meteo data
├── maps/                 # Country GeoJSON maps
│   └── dz.json          # Algeria map
└── meteo/               # Generated weather maps (auto-created)
    └── [country_code]/  # e.g., "dz" for Algeria
        └── [date]/      # e.g., "2026-01-07"
            └── weather_map_*.png
```

## Output File Organization

Generated weather maps are automatically saved to:
```
meteo/[country_id]/[YYYY-MM-DD]/[map_type].png
```

**Map Types:**
- `maxtemp.png` - Maximum temperature map
- `mintemp.png` - Minimum temperature map  
- `wind.png` - Wind speed map
- `sun.png` - Sunshine percentage map
- `weather_map_[HHMMSS].png` - General weather map with timestamp

**Example:**
- Country: Algeria (dz)
- Date: 2026-01-07
- Path: `meteo/dz/2026-01-07/maxtemp.png`

## Installation

```bash
# Activate virtual environment
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Start the Server

```bash
python app.py
```

Server will start on `http://localhost:8000`

### 2. API Documentation

- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Generate Weather Map

**Generate all 4 map types at once (recommended):**
```bash
curl -X POST "http://localhost:8000/generate/all" \
  -H "Content-Type: application/json" \
  -d @meteo.json
```

This generates:
- `maxtemp.png` - Maximum temperature
- `mintemp.png` - Minimum temperature
- `wind.png` - Wind speed
- `sun.png` - Sunshine percentage

**Simple endpoint (general weather map):**
```bash
curl -X POST "http://localhost:8000/generate/raw" \
  -H "Content-Type: application/json" \
  -d @meteo.json \
  --output weather_map.png
```

**Full endpoint (with options):**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "meteo_data": [...],
    "title": "Algeria Weather Forecast",
    "day_index": 0
  }' \
  --output weather_map.png
```

### 4. Run Tests

```bash
# Test all 4 map generation
python test_all_maps.py

# Full test suite
python test_api.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/countries` | List available country maps |
| POST | `/generate` | Generate map with options |
| POST | `/generate/raw` | Generate map (simplified) |
| POST | `/generate/all` | **Generate all 4 map types** |

### `/generate/all` Response

Returns JSON with paths to all generated files:
```json
{
  "status": "success",
  "country": "dz",
  "generated_files": {
    "maxtemp": "meteo/dz/2026-01-07/maxtemp.png",
    "mintemp": "meteo/dz/2026-01-07/mintemp.png",
    "wind": "meteo/dz/2026-01-07/wind.png",
    "sun": "meteo/dz/2026-01-07/sun.png"
  },
  "count": 4
}
```

## Meteo Data Format

```json
[
  {
    "latitude": 36.7538,
    "longitude": 3.0588,
    "capital": "dz",
    "name": "Algiers",
    "display_name": "Algiers",
    "priority": 1,
    "daily": {
      "time": ["2026-01-07"],
      "weather_code": [95],
      "temperature_2m_max": [12.4],
      "temperature_2m_min": [8.1],
      "precipitation_sum": [9.0],
      "wind_speed_10m_max": [20.2],
      "cloud_cover_max": [100]
    }
  }
]
```

## Adding More Countries

1. Download GeoJSON map for the country
2. Save as `maps/[country_code].json` (e.g., `maps/fr.json` for France)
3. Restart the server
4. Use the country code in the `capital` field of your meteo data

## Weather Icons

The API uses **WMO Weather interpretation codes (WW)** to display appropriate icons:

| Code | Description | Icon |
|------|-------------|------|
| 0 | Clear sky | ☀️ |
| 1, 2, 3 | Mainly clear, partly cloudy, and overcast | 🌤 ⛅ ☁️ |
| 45, 48 | Fog and depositing rime fog | 🌫 |
| 51, 53, 55 | Drizzle: Light, moderate, and dense | 🌦 🌦 🌧 |
| 56, 57 | Freezing Drizzle: Light and dense | 🌧❄️ |
| 61, 63, 65 | Rain: Slight, moderate and heavy | 🌧 🌧 🌧🌧 |
| 66, 67 | Freezing Rain: Light and heavy | 🌧❄️ |
| 71, 73, 75 | Snow fall: Slight, moderate, and heavy | 🌨 🌨 🌨❄️ |
| 77 | Snow grains | ❄️ |
| 80, 81, 82 | Rain showers: Slight, moderate, and violent | 🌦 🌧 🌧🌧 |
| 85, 86 | Snow showers: Slight and heavy | 🌨 🌨❄️ |
| 95 | Thunderstorm: Slight or moderate | ⛈ |
| 96, 99 | Thunderstorm with slight and heavy hail | ⛈🧊 |

## Response Headers

The API includes the saved file path in response headers:
```
X-Saved-Path: meteo/dz/2026-01-07/weather_map_143215.png
```

## License

MIT
