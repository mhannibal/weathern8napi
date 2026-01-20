"""
Weather Map REST API Server

A REST API service that generates weather map images from meteo data.
Receives weather data, detects the country, loads the GeoJSON map,
and produces a weather visualization image.
"""

import json
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Import the weather map service
from weather_map_service import WeatherMapService, create_weather_location_from_dict

# Import Pydantic models
from models import MeteoRequest


# ===============================
# CONFIGURATION
# ===============================

# Initialize the weather map service
weather_service: Optional[WeatherMapService] = None
METEO_FOLDER = Path("./meteo")


# ===============================
# LIFESPAN EVENT HANDLER
# ===============================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup the weather map service."""
    global weather_service
    
    # Initialize the weather map service
    weather_service = WeatherMapService()
    
    yield  # Server runs here
    
    # Cleanup on shutdown (if needed)
    print("🛑 Server shutting down...")


# ===============================
# FASTAPI APP
# ===============================

app = FastAPI(
    title="Weather Map API",
    description="REST API that generates weather map images from meteo data",
    version="1.0.0",
    lifespan=lifespan
)

# Ensure meteo folder exists
METEO_FOLDER.mkdir(parents=True, exist_ok=True)

# Mount the meteo folder as static files for HTTP browsing
app.mount("/meteo", StaticFiles(directory=str(METEO_FOLDER), html=True), name="meteo")


# ===============================
# API ENDPOINTS
# ===============================

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "Weather Map API",
        "version": "1.0.0",
        "endpoints": {
            "POST /generate": "Generate weather map from meteo data",
            "POST /generate/raw": "Generate weather map (simplified)",
            "POST /generate/all": "Generate all 4 map types (maxtemp, mintemp, wind, sun)",
            "GET /countries": "List available country maps",
            "GET /meteo/files": "List all generated weather maps",
            "GET /health": "Health check"
        },
        "static_files": {
            "/meteo/{country}/{date}/{filename}": "Download generated weather maps (static files)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "maps_loaded": len(weather_service.get_available_countries()) if weather_service else 0
    }


@app.get("/countries")
async def list_countries():
    """List all available country maps."""
    if not weather_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    return {
        "available_countries": weather_service.get_available_countries(),
        "count": len(weather_service.get_available_countries())
    }


@app.get("/meteo/files")
async def list_generated_files():
    """
    List all generated weather map files organized by country and date.
    
    Returns a structured list of all available weather maps.
    """
    if not METEO_FOLDER.exists():
        return {"countries": {}, "total_files": 0}
    
    result = {}
    total_files = 0
    
    # Iterate through country folders
    for country_folder in METEO_FOLDER.iterdir():
        if country_folder.is_dir():
            country_code = country_folder.name
            result[country_code] = {}
            
            # Iterate through date folders
            for date_folder in country_folder.iterdir():
                if date_folder.is_dir():
                    date = date_folder.name
                    files = []
                    
                    # List all PNG files in this date folder
                    for file in sorted(date_folder.glob("*.png")):
                        files.append({
                            "name": file.name,
                            "url": f"/meteo/{country_code}/{date}/{file.name}",
                            "size_kb": round(file.stat().st_size / 1024, 2)
                        })
                        total_files += 1
                    
                    if files:
                        result[country_code][date] = files
    
    return {
        "countries": result,
        "total_files": total_files
    }


@app.post("/generate")
async def generate_map(request: MeteoRequest):
    """
    Generate a weather map image from meteo data.
    
    The API will:
    1. Detect the country from the meteo data (using 'capital' field)
    2. Load the corresponding GeoJSON map
    3. Generate a weather visualization
    4. Return the image as PNG
    
    Example request body:
    ```json
    {
        "meteo_data": [...],  // Array of meteo location data
        "title": "Optional custom title",
        "day_index": 0  // Which forecast day to display
    }
    ```
    """
    if not weather_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    if not request.meteo_data:
        raise HTTPException(status_code=400, detail="No meteo data provided")
    
    # Detect country from first location's capital field
    country_code = request.meteo_data[0].capital
    
    if not country_code:
        raise HTTPException(
            status_code=400,
            detail="Country code (capital field) is required in meteo data"
        )
    
    if country_code.lower() not in weather_service.get_available_countries():
        raise HTTPException(
            status_code=404,
            detail=f"Map not found for country: {country_code}. Available: {weather_service.get_available_countries()}"
        )
    
    try:
        # Convert Pydantic models to service dataclasses
        weather_locations = [
            create_weather_location_from_dict(loc.model_dump())
            for loc in request.meteo_data
        ]
        
        # Generate the map image using the service
        image_buffer, saved_path = weather_service.generate_map(
            meteo_data=weather_locations,
            country_code=country_code,
            title=request.title,
            day_index=request.day_index or 0
        )
        
        return StreamingResponse(
            image_buffer,
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename=weather_map_{country_code}.png",
                "X-Saved-Path": saved_path if saved_path else ""
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating map: {str(e)}")


@app.post("/generate/raw")
async def generate_map_raw(request: Request):
    """
    Simplified endpoint - just send array of meteo locations directly.
    
    Example: POST with body being the raw meteo JSON array.
    Accepts both raw JSON array or {"json": "..."} wrapped format.
    """
    if not weather_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        # Get raw body
        body = await request.json()
        
        # Handle wrapped format {"json": "[...]"}
        if isinstance(body, dict) and "json" in body:
            if isinstance(body["json"], str):
                # Parse string JSON
                meteo_data = json.loads(body["json"])
            else:
                meteo_data = body["json"]
        else:
            # Direct array format
            meteo_data = body
        
        # Validate it's a list
        if not isinstance(meteo_data, list):
            raise HTTPException(status_code=400, detail="Data must be a list of weather locations")
        
        if not meteo_data:
            raise HTTPException(status_code=400, detail="No meteo data provided")
        
        # Get country code
        if "capital" not in meteo_data[0]:
            raise HTTPException(status_code=400, detail="Country code (capital field) is required")
        
        country_code = meteo_data[0]["capital"]
        
        if country_code.lower() not in weather_service.get_available_countries():
            raise HTTPException(
                status_code=404,
                detail=f"Map not found for country: {country_code}"
            )
        
        # Convert to service dataclasses
        weather_locations = [create_weather_location_from_dict(item) for item in meteo_data]
        
        # Generate map using service
        image_buffer, saved_path = weather_service.generate_map(
            meteo_data=weather_locations,
            country_code=country_code
        )
        
        return StreamingResponse(
            image_buffer,
            media_type="image/png",
            headers={
                "X-Saved-Path": saved_path if saved_path else ""
            }
        )
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating map: {str(e)}")


@app.post("/generate/all")
async def generate_all_maps(request: Request):
    """
    Generate all 4 weather map types at once:
    - maxtemp.png - Maximum temperature map
    - mintemp.png - Minimum temperature map
    - wind.png - Wind speed map
    - sun.png - Sunshine percentage map
    
    Returns a JSON response with paths to all generated files.
    Accepts both raw JSON array or {"json": "..."} wrapped format.
    """
    if not weather_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        # Get raw body
        body = await request.json()
        
        # Handle wrapped format {"json": "[...]"}
        if isinstance(body, dict) and "json" in body:
            if isinstance(body["json"], str):
                # Parse string JSON
                meteo_data = json.loads(body["json"])
            else:
                meteo_data = body["json"]
        else:
            # Direct array format
            meteo_data = body
        
        # Validate it's a list
        if not isinstance(meteo_data, list):
            raise HTTPException(status_code=400, detail="Data must be a list of weather locations")
        
        if not meteo_data:
            raise HTTPException(status_code=400, detail="No meteo data provided")
        
        # Get country code
        if "capital" not in meteo_data[0]:
            raise HTTPException(status_code=400, detail="Country code (capital field) is required")
        
        country_code = meteo_data[0]["capital"]
        
        if country_code.lower() not in weather_service.get_available_countries():
            raise HTTPException(
                status_code=404,
                detail=f"Map not found for country: {country_code}"
            )
        
        # Convert to service dataclasses
        weather_locations = [create_weather_location_from_dict(item) for item in meteo_data]
        
        # Generate all maps using service
        generated_files = weather_service.generate_all_maps(
            meteo_data=weather_locations,
            country_code=country_code
        )
        
        return JSONResponse({
            "status": "success",
            "country": country_code,
            "generated_files": generated_files,
            "count": len(generated_files)
        })
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating maps: {str(e)}")


# ===============================
# MAIN ENTRY POINT
# ===============================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
