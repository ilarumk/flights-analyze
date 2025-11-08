"""
Weather Service using Open-Meteo API
Fetches historical climate averages for destinations
No API key required - free and unlimited
"""
import requests
import json
from datetime import datetime
from pathlib import Path

# Cache file to avoid repeated API calls
CACHE_FILE = Path('weather_cache.json')

def load_cache():
    """Load cached weather data"""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Save weather data to cache"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def get_monthly_climate(latitude, longitude, month):
    """
    Get historical climate averages for a specific month

    Args:
        latitude: Location latitude
        longitude: Location longitude
        month: Month number (1-12)

    Returns:
        dict with avg_temp, min_temp, max_temp, description
    """
    cache = load_cache()
    cache_key = f"{latitude},{longitude},{month}"

    # Check cache first
    if cache_key in cache:
        return cache[cache_key]

    # Open-Meteo Climate API endpoint
    # Uses 30-year climate normals (1991-2020)
    url = "https://archive-api.open-meteo.com/v1/archive"

    # Get data for the specific month from recent years
    # We'll use 2023 as reference year (complete data available)
    year = 2023
    start_date = f"{year}-{month:02d}-01"

    # Determine last day of month
    if month in [1, 3, 5, 7, 8, 10, 12]:
        last_day = 31
    elif month in [4, 6, 9, 11]:
        last_day = 30
    else:  # February
        last_day = 28

    end_date = f"{year}-{month:02d}-{last_day}"

    params = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date,
        'end_date': end_date,
        'daily': 'temperature_2m_mean,temperature_2m_max,temperature_2m_min',
        'timezone': 'auto'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Calculate monthly averages
        temps_mean = data['daily']['temperature_2m_mean']
        temps_max = data['daily']['temperature_2m_max']
        temps_min = data['daily']['temperature_2m_min']

        avg_temp = round(sum(temps_mean) / len(temps_mean), 1)
        max_temp = round(sum(temps_max) / len(temps_max), 1)
        min_temp = round(sum(temps_min) / len(temps_min), 1)

        # Generate description based on temperature
        description = get_temp_description(avg_temp, max_temp)

        result = {
            'avg': avg_temp,
            'max': max_temp,
            'min': min_temp,
            'desc': description,
            'source': 'Open-Meteo',
            'fetched_at': datetime.now().isoformat()
        }

        # Cache the result
        cache[cache_key] = result
        save_cache(cache)

        return result

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_temp_description(avg_temp, max_temp):
    """
    Generate human-readable temperature description

    Args:
        avg_temp: Average temperature in Celsius
        max_temp: Maximum temperature in Celsius

    Returns:
        str: Description like "Hot & Humid", "Cold & Dry", etc.
    """
    if avg_temp >= 30:
        if max_temp >= 38:
            return "Extremely Hot"
        elif max_temp >= 35:
            return "Very Hot"
        else:
            return "Hot & Humid"
    elif avg_temp >= 25:
        return "Hot & Dry" if max_temp >= 32 else "Warm"
    elif avg_temp >= 20:
        return "Pleasant"
    elif avg_temp >= 15:
        return "Mild"
    elif avg_temp >= 10:
        return "Cool"
    elif avg_temp >= 5:
        return "Cold"
    elif avg_temp >= 0:
        return "Very Cold"
    else:
        return "Freezing"

def get_climate_type(latitude):
    """
    Determine climate type based on latitude
    Simplified climate classification
    """
    abs_lat = abs(latitude)

    if abs_lat >= 60:
        return "Polar/Subarctic"
    elif abs_lat >= 45:
        return "Continental"
    elif abs_lat >= 35:
        return "Temperate"
    elif abs_lat >= 23.5:
        return "Subtropical"
    else:
        return "Tropical"

def is_ski_suitable(latitude, avg_winter_temp):
    """
    Determine if destination is suitable for skiing

    Args:
        latitude: Location latitude
        avg_winter_temp: Average winter temperature in Celsius

    Returns:
        bool: True if ski suitable
    """
    # Ski resorts typically need temperatures below 5°C
    # and sufficient altitude/latitude
    abs_lat = abs(latitude)
    return avg_winter_temp < 5 and abs_lat > 30

# Test function
if __name__ == "__main__":
    print("=== Testing Open-Meteo Weather Service ===\n")

    test_locations = [
        {"name": "Bali, Indonesia", "lat": -8.748, "lon": 115.167, "month": 12},
        {"name": "Tokyo, Japan", "lat": 35.765, "lon": 140.386, "month": 1},
        {"name": "Paris, France", "lat": 49.013, "lon": 2.55, "month": 7},
        {"name": "Dubai, UAE", "lat": 25.253, "lon": 55.364, "month": 8},
        {"name": "Iceland (Reykjavik)", "lat": 64.147, "lon": -21.942, "month": 2},
    ]

    for loc in test_locations:
        print(f"\n📍 {loc['name']} - Month {loc['month']}")
        climate = get_monthly_climate(loc['lat'], loc['lon'], loc['month'])

        if climate:
            temp_f = int(climate['avg'] * 9/5 + 32)
            print(f"   🌡️  {climate['avg']}°C / {temp_f}°F")
            print(f"   📊 Range: {climate['min']}°C to {climate['max']}°C")
            print(f"   ☁️  {climate['desc']}")
            print(f"   📅 Source: {climate['source']}")
        else:
            print("   ❌ Failed to fetch data")

    print("\n✅ Weather cache saved to weather_cache.json")
