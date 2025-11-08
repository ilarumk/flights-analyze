"""
Enrich flight data with OpenFlights geographic data
"""
import pandas as pd
import json
from math import radians, sin, cos, sqrt, asin

def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance between two points in miles and km"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    miles = km * 0.621371
    return miles, km

# Load OpenFlights airport data
airport_cols = ['airport_id', 'name', 'city', 'country', 'iata', 'icao',
                'latitude', 'longitude', 'altitude', 'timezone', 'dst',
                'tz_database', 'type', 'source']

print("Loading OpenFlights data...")
airports = pd.read_csv('airports_openflights.csv', names=airport_cols, na_values=['\\N'])
# Drop duplicates and keep first occurrence
airports = airports.dropna(subset=['iata']).drop_duplicates(subset=['iata'], keep='first')
airports_dict = airports.set_index('iata').to_dict('index')

# Load flight prices
print("Loading flight data...")
with open('flight_prices_worldwide.json', 'r') as f:
    flight_data = json.load(f)

def classify_region(country):
    """Classify country into region"""
    regions = {
        'Europe': ['United Kingdom', 'France', 'Spain', 'Italy', 'Greece', 'Iceland',
                   'Netherlands', 'Germany', 'Turkey'],
        'Asia': ['Japan', 'Thailand', 'Singapore', 'Hong Kong', 'China', 'Indonesia',
                 'Maldives', 'India', 'South Korea', 'Vietnam'],
        'North America': ['United States', 'Canada', 'Mexico'],
        'South America': ['Brazil', 'Argentina', 'Chile', 'Peru', 'Colombia'],
        'Middle East': ['United Arab Emirates', 'Qatar', 'Saudi Arabia', 'Israel'],
        'Oceania': ['Australia', 'New Zealand', 'Fiji'],
        'Africa': ['South Africa', 'Egypt', 'Morocco', 'Kenya']
    }

    for region, countries in regions.items():
        if country in countries:
            return region
    return 'Other'

# Enrich each route with distance and geographic info
print("Enriching routes with distance data...")
enriched_count = 0
for route in flight_data['routes']:
    origin = route['origin']
    dest = route['destination']

    if origin in airports_dict and dest in airports_dict:
        origin_info = airports_dict[origin]
        dest_info = airports_dict[dest]

        # Calculate distance
        miles, km = haversine(
            origin_info['longitude'], origin_info['latitude'],
            dest_info['longitude'], dest_info['latitude']
        )

        route['distance_miles'] = int(miles)
        route['distance_km'] = int(km)
        route['price_per_mile'] = round(route['price_avg'] / miles, 2) if miles > 0 else 0

        # Add origin/destination metadata
        route['origin_city'] = origin_info['city']
        route['origin_country'] = origin_info['country']
        route['dest_city'] = dest_info['city']
        route['dest_country'] = dest_info['country']

        # Timezone difference
        origin_tz = origin_info.get('timezone', 0) or 0
        dest_tz = dest_info.get('timezone', 0) or 0
        route['timezone_diff'] = int(dest_tz - origin_tz)

        # Regional classification
        route['origin_region'] = classify_region(origin_info['country'])
        route['dest_region'] = classify_region(dest_info['country'])

        enriched_count += 1

print(f"Enriched {enriched_count}/{len(flight_data['routes'])} routes")

# Save enriched data
output_file = 'flight_prices_worldwide_enriched.json'
print(f"Saving enriched data to {output_file}...")
with open(output_file, 'w') as f:
    json.dump(flight_data, f, indent=2)

print("✅ Done! Enriched data saved.")
print(f"\nAdded fields:")
print("- distance_miles, distance_km")
print("- price_per_mile")
print("- origin_city, origin_country, dest_city, dest_country")
print("- timezone_diff")
print("- origin_region, dest_region")
