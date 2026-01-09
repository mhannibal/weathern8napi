"""
Weather Map Generation Service

A standalone service for generating weather map visualizations.
Can be used independently from the REST API or integrated into other applications.
"""

import io
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from dataclasses import dataclass

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use


# ===============================
# CONFIGURATION
# ===============================

# Weather code to emoji/icon mapping (WMO Weather interpretation codes)
# Based on WMO Weather interpretation codes (WW)
# Reference: https://open-meteo.com/en/docs
WEATHER_ICONS = {
    0: "☀️",      # Clear sky
    1: "🌤",      # Mainly clear
    2: "⛅",      # Partly cloudy
    3: "☁️",      # Overcast
    45: "🌫",     # Fog
    48: "🌫",     # Depositing rime fog
    51: "🌦",     # Drizzle: Light
    53: "🌦",     # Drizzle: Moderate
    55: "🌧",     # Drizzle: Dense intensity
    56: "🌧❄️",   # Freezing Drizzle: Light
    57: "🌧❄️",   # Freezing Drizzle: Dense
    61: "🌧",     # Rain: Slight intensity
    63: "🌧",     # Rain: Moderate intensity
    65: "🌧🌧",   # Rain: Heavy intensity
    66: "🌧❄️",   # Freezing Rain: Light
    67: "🌧❄️",   # Freezing Rain: Heavy
    71: "🌨",     # Snow fall: Slight intensity
    73: "🌨",     # Snow fall: Moderate intensity
    75: "🌨❄️",   # Snow fall: Heavy intensity
    77: "❄️",     # Snow grains
    80: "🌦",     # Rain showers: Slight
    81: "🌧",     # Rain showers: Moderate
    82: "🌧🌧",   # Rain showers: Violent
    85: "🌨",     # Snow showers: Slight
    86: "🌨❄️",   # Snow showers: Heavy
    95: "⛈",     # Thunderstorm: Slight or moderate
    96: "⛈🧊",   # Thunderstorm with slight hail
    99: "⛈🧊",   # Thunderstorm with heavy hail
}


# ===============================
# DATA MODELS
# ===============================

@dataclass
class DailyData:
    """Daily weather data for a location."""
    time: List[str]
    weather_code: List[int]
    temperature_2m_max: List[float]
    temperature_2m_min: List[float]
    precipitation_sum: List[float]
    wind_speed_10m_max: List[float]
    cloud_cover_min: Optional[List[int]] = None
    cloud_cover_max: Optional[List[int]] = None


@dataclass
class WeatherLocation:
    """Weather data for a specific location."""
    latitude: float
    longitude: float
    name: str
    display_name: str
    daily: DailyData
    priority: int = 1


# ===============================
# WEATHER MAP SERVICE
# ===============================

class WeatherMapService:
    """Service for generating weather map visualizations."""
    
    def __init__(
        self,
        maps_folder: Path = Path("./maps"),
        output_folder: Path = Path("./meteo")
    ):
        """
        Initialize the Weather Map Service.
        
        Args:
            maps_folder: Path to folder containing GeoJSON map files
            output_folder: Path to folder where generated maps will be saved
        """
        self.maps_folder = Path(maps_folder)
        self.output_folder = Path(output_folder)
        self.supported_countries: Dict[str, str] = {}
        
        # Load available maps
        self._load_available_maps()
    
    def _load_available_maps(self):
        """Load all available country maps from the maps folder."""
        if not self.maps_folder.exists():
            self.maps_folder.mkdir(parents=True, exist_ok=True)
            print(f"⚠️ Created maps folder at {self.maps_folder}")
            return
        
        for map_file in self.maps_folder.glob("*.json"):
            country_code = map_file.stem.lower()
            self.supported_countries[country_code] = str(map_file)
        
        if self.supported_countries:
            print(f"📍 Loaded {len(self.supported_countries)} country maps: {list(self.supported_countries.keys())}")
    
    def get_available_countries(self) -> List[str]:
        """Get list of available country codes."""
        return list(self.supported_countries.keys())
    
    @staticmethod
    def get_weather_icon(weather_code: int) -> str:
        """Get emoji icon for WMO weather code."""
        return WEATHER_ICONS.get(weather_code, "❓")
    
    def generate_map(
        self,
        meteo_data: List[WeatherLocation],
        country_code: str,
        title: Optional[str] = None,
        day_index: int = 0,
        map_type: str = "general",
        save_to_disk: bool = True
    ) -> Tuple[io.BytesIO, Optional[str]]:
        """
        Generate a weather map image from meteo data.
        
        Args:
            meteo_data: List of weather data for locations
            country_code: Country code to load map for
            title: Optional title for the map
            day_index: Which day's data to display (0 = first day)
            map_type: Type of map to generate (general, maxtemp, mintemp, sun, wind)
            save_to_disk: Whether to save the map to disk
        
        Returns:
            Tuple of (BytesIO buffer containing PNG image, output file path or None)
        
        Raises:
            ValueError: If country map not found or meteo data is invalid
        """
        # Validate inputs
        if not meteo_data:
            raise ValueError("No meteo data provided")
        
        # Load country GeoJSON
        map_path = self.supported_countries.get(country_code.lower())
        if not map_path:
            raise ValueError(
                f"Map not found for country: {country_code}. "
                f"Available: {list(self.supported_countries.keys())}"
            )
        
        country = gpd.read_file(map_path).to_crs("EPSG:4326")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 11))
        
        # Plot base map
        country.plot(
            ax=ax,
            color="#e8f4e8",  # Light green background
            edgecolor="#333333",
            linewidth=0.8
        )
        
        # Get the date from first location's data
        date_str = None
        if meteo_data and meteo_data[0].daily.time:
            if day_index < len(meteo_data[0].daily.time):
                date_str = meteo_data[0].daily.time[day_index]
        
        # Sort by priority (lower = more important = rendered last = on top)
        sorted_data = sorted(meteo_data, key=lambda x: x.priority or 99, reverse=True)
        
        # Plot weather data for each location
        for item in sorted_data:
            self._plot_location(ax, item, day_index, map_type)
        
        # Set title
        title_prefix = self._get_title_prefix(map_type)
        if title:
            map_title = title
        elif date_str:
            map_title = f"{title_prefix} — {date_str}"
        else:
            map_title = f"{title_prefix} — {datetime.now().strftime('%Y-%m-%d')}"
        
        ax.set_title(map_title, fontsize=18, fontweight='bold', pad=20)
        ax.axis("off")
        
        # Remove borders
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Save to disk if requested
        output_path = None
        if save_to_disk:
            output_path = self._save_to_disk(country_code, map_type, fig)
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        buffer.seek(0)
        plt.close(fig)
        
        return buffer, output_path
    
    def generate_all_maps(
        self,
        meteo_data: List[WeatherLocation],
        country_code: str,
        day_index: int = 0
    ) -> Dict[str, str]:
        """
        Generate all 4 weather map types at once.
        
        Args:
            meteo_data: List of weather data for locations
            country_code: Country code to load map for
            day_index: Which day's data to display
        
        Returns:
            Dictionary mapping map_type to output file path
        """
        map_types = ["maxtemp", "mintemp", "wind", "sun"]
        generated_files = {}
        
        for map_type in map_types:
            _, output_path = self.generate_map(
                meteo_data=meteo_data,
                country_code=country_code,
                day_index=day_index,
                map_type=map_type,
                save_to_disk=True
            )
            if output_path:
                generated_files[map_type] = output_path
        
        return generated_files
    
    def _plot_location(
        self,
        ax,
        location: WeatherLocation,
        day_index: int,
        map_type: str
    ):
        """Plot a single location on the map."""
        lon = location.longitude
        lat = location.latitude
        name = location.display_name or location.name
        daily = location.daily
        
        # Get data for the specified day index
        idx = min(day_index, len(daily.temperature_2m_max) - 1)
        
        tmax = daily.temperature_2m_max[idx]
        tmin = daily.temperature_2m_min[idx]
        rain = daily.precipitation_sum[idx]
        wind = daily.wind_speed_10m_max[idx]
        weather_code = daily.weather_code[idx]
        
        cloud_max = None
        if daily.cloud_cover_max and idx < len(daily.cloud_cover_max):
            cloud_max = daily.cloud_cover_max[idx]
        
        # Calculate sunshine percentage
        sunshine = 100 - cloud_max if cloud_max is not None else None
        
        # Get weather icon
        icon = self.get_weather_icon(weather_code)
        
        # City marker color based on map type
        marker_color = self._get_marker_color(map_type, tmax, tmin, wind, sunshine)
        ax.plot(lon, lat, "o", color=marker_color, markersize=6, zorder=5)
        
        # Build label based on map type
        label, _ = self._build_label(
            map_type, name, tmax, tmin, rain, wind, cloud_max, sunshine, icon
        )
        
        # Determine label position based on priority
        priority = location.priority or 1
        x_offset = 0.2 if priority <= 2 else 0.15
        y_offset = 0.2 if priority <= 2 else 0.15
        fontsize = 10 if priority == 1 else 9 if priority == 2 else 8
        
        ax.text(
            lon + x_offset,
            lat + y_offset,
            label,
            fontsize=fontsize,
            ha="left",
            va="top",
            zorder=10,
            bbox=dict(
                boxstyle="round,pad=0.3",
                fc="white",
                ec="#666666",
                alpha=0.92,
                linewidth=1
            )
        )
    
    @staticmethod
    def _get_marker_color(
        map_type: str,
        tmax: float,
        tmin: float,
        wind: float,
        sunshine: Optional[float]
    ) -> str:
        """Get marker color based on map type and weather data."""
        if map_type == "maxtemp":
            return "#ff5722" if tmax > 25 else "#ff9800" if tmax > 15 else "#2196f3"
        elif map_type == "mintemp":
            return "#2196f3" if tmin < 5 else "#03a9f4" if tmin < 15 else "#ff9800"
        elif map_type == "wind":
            return "#d32f2f" if wind > 30 else "#ff9800" if wind > 20 else "#4caf50"
        elif map_type == "sun":
            if sunshine is not None:
                return "#fdd835" if sunshine > 70 else "#ffb300" if sunshine > 40 else "#90a4ae"
            return "#90a4ae"
        else:
            return "#d32f2f"
    
    @staticmethod
    def _build_label(
        map_type: str,
        name: str,
        tmax: float,
        tmin: float,
        rain: float,
        wind: float,
        cloud_max: Optional[int],
        sunshine: Optional[float],
        icon: str
    ) -> Tuple[str, str]:
        """Build label text and title prefix based on map type."""
        if map_type == "maxtemp":
            return f"{name}\n🌡 {tmax}°C", "Maximum Temperature"
        elif map_type == "mintemp":
            return f"{name}\n🌡 {tmin}°C", "Minimum Temperature"
        elif map_type == "wind":
            return f"{name}\n💨 {wind} km/h", "Wind Speed"
        elif map_type == "sun":
            sun_emoji = "☀️" if sunshine and sunshine > 70 else "⛅" if sunshine and sunshine > 40 else "☁️"
            label = f"{name}\n{sun_emoji} {sunshine}%" if sunshine is not None else f"{name}\n❓"
            return label, "Sunshine"
        else:
            # General map with all data
            label_parts = [name, f"{icon} {tmax}° / {tmin}°"]
            if rain > 0:
                label_parts.append(f"🌧 {rain} mm")
            if wind > 15:
                label_parts.append(f"💨 {wind} km/h")
            if cloud_max is not None and cloud_max > 50:
                label_parts.append(f"☁ {cloud_max}%")
            return "\n".join(label_parts), "Weather Forecast"
    
    @staticmethod
    def _get_title_prefix(map_type: str) -> str:
        """Get title prefix for map type."""
        prefixes = {
            "maxtemp": "Maximum Temperature",
            "mintemp": "Minimum Temperature",
            "wind": "Wind Speed",
            "sun": "Sunshine",
            "general": "Weather Forecast"
        }
        return prefixes.get(map_type, "Weather Forecast")
    
    def _save_to_disk(
        self,
        country_code: str,
        map_type: str,
        fig
    ) -> str:
        """Save the figure to disk and return the file path."""
        # Create output directory structure
        today_date = datetime.now().strftime('%Y-%m-%d')
        output_dir = self.output_folder / country_code.lower() / today_date
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename based on map type
        if map_type in ["maxtemp", "mintemp", "wind", "sun"]:
            filename = f"{map_type}.png"
        else:
            timestamp = datetime.now().strftime('%H%M%S')
            filename = f"weather_map_{timestamp}.png"
        
        output_path = output_dir / filename
        
        # Save to file
        plt.savefig(output_path, format='png', dpi=200, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        
        print(f"📁 Saved map to: {output_path}")
        
        return str(output_path)


# ===============================
# HELPER FUNCTIONS
# ===============================

def create_weather_location_from_dict(data: dict) -> WeatherLocation:
    """
    Create a WeatherLocation instance from a dictionary.
    
    Args:
        data: Dictionary containing weather location data
    
    Returns:
        WeatherLocation instance
    """
    daily_data = DailyData(
        time=data["daily"]["time"],
        weather_code=data["daily"]["weather_code"],
        temperature_2m_max=data["daily"]["temperature_2m_max"],
        temperature_2m_min=data["daily"]["temperature_2m_min"],
        precipitation_sum=data["daily"]["precipitation_sum"],
        wind_speed_10m_max=data["daily"]["wind_speed_10m_max"],
        cloud_cover_min=data["daily"].get("cloud_cover_min"),
        cloud_cover_max=data["daily"].get("cloud_cover_max")
    )
    
    return WeatherLocation(
        latitude=data["latitude"],
        longitude=data["longitude"],
        name=data["name"],
        display_name=data.get("display_name", data["name"]),
        daily=daily_data,
        priority=data.get("priority", 1)
    )
