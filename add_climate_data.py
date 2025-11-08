"""
Add climate and temperature data to destinations
Uses historical climate averages by month
"""
import json

# Monthly temperature ranges (°C) and climate data for each destination
# Source: Historical climate data from various sources
climate_data = {
    "bali": {
        "climate_type": "Tropical",
        "ski_suitable": False,
        "monthly_temps": {  # Average temps in Celsius
            "Jan": {"avg": 27, "min": 24, "max": 30, "desc": "Hot & Rainy"},
            "Feb": {"avg": 27, "min": 24, "max": 30, "desc": "Hot & Rainy"},
            "Mar": {"avg": 27, "min": 24, "max": 30, "desc": "Hot"},
            "Apr": {"avg": 27, "min": 24, "max": 30, "desc": "Hot & Dry"},
            "May": {"avg": 27, "min": 24, "max": 30, "desc": "Hot & Dry"},
            "Jun": {"avg": 26, "min": 23, "max": 29, "desc": "Warm & Dry"},
            "Jul": {"avg": 26, "min": 23, "max": 29, "desc": "Warm & Dry"},
            "Aug": {"avg": 26, "min": 23, "max": 29, "desc": "Warm & Dry"},
            "Sep": {"avg": 27, "min": 24, "max": 30, "desc": "Warm & Dry"},
            "Oct": {"avg": 27, "min": 24, "max": 31, "desc": "Hot"},
            "Nov": {"avg": 27, "min": 24, "max": 31, "desc": "Hot"},
            "Dec": {"avg": 27, "min": 24, "max": 30, "desc": "Hot & Rainy"}
        }
    },
    "tokyo": {
        "climate_type": "Humid Subtropical",
        "ski_suitable": False,
        "monthly_temps": {
            "Jan": {"avg": 5, "min": 1, "max": 10, "desc": "Cold & Dry"},
            "Feb": {"avg": 6, "min": 2, "max": 10, "desc": "Cold & Dry"},
            "Mar": {"avg": 9, "min": 5, "max": 14, "desc": "Cool"},
            "Apr": {"avg": 14, "min": 10, "max": 19, "desc": "Mild"},
            "May": {"avg": 19, "min": 15, "max": 23, "desc": "Pleasant"},
            "Jun": {"avg": 22, "min": 19, "max": 26, "desc": "Warm & Rainy"},
            "Jul": {"avg": 26, "min": 23, "max": 29, "desc": "Hot & Humid"},
            "Aug": {"avg": 27, "min": 24, "max": 31, "desc": "Hot & Humid"},
            "Sep": {"avg": 23, "min": 20, "max": 27, "desc": "Warm"},
            "Oct": {"avg": 17, "min": 14, "max": 22, "desc": "Pleasant"},
            "Nov": {"avg": 12, "min": 8, "max": 17, "desc": "Cool"},
            "Dec": {"avg": 7, "min": 3, "max": 12, "desc": "Cold"}
        }
    },
    "paris": {
        "climate_type": "Oceanic",
        "ski_suitable": False,
        "monthly_temps": {
            "Jan": {"avg": 5, "min": 2, "max": 7, "desc": "Cold & Damp"},
            "Feb": {"avg": 6, "min": 2, "max": 8, "desc": "Cold"},
            "Mar": {"avg": 9, "min": 5, "max": 12, "desc": "Cool"},
            "Apr": {"avg": 12, "min": 7, "max": 16, "desc": "Mild"},
            "May": {"avg": 16, "min": 11, "max": 20, "desc": "Pleasant"},
            "Jun": {"avg": 19, "min": 14, "max": 23, "desc": "Warm"},
            "Jul": {"avg": 21, "min": 16, "max": 25, "desc": "Warm"},
            "Aug": {"avg": 21, "min": 16, "max": 25, "desc": "Warm"},
            "Sep": {"avg": 18, "min": 13, "max": 22, "desc": "Pleasant"},
            "Oct": {"avg": 14, "min": 10, "max": 17, "desc": "Cool"},
            "Nov": {"avg": 9, "min": 6, "max": 11, "desc": "Cool"},
            "Dec": {"avg": 6, "min": 3, "max": 8, "desc": "Cold"}
        }
    },
    "dubai": {
        "climate_type": "Desert/Hot Arid",
        "ski_suitable": False,
        "monthly_temps": {
            "Jan": {"avg": 19, "min": 14, "max": 24, "desc": "Pleasant"},
            "Feb": {"avg": 20, "min": 15, "max": 25, "desc": "Pleasant"},
            "Mar": {"avg": 23, "min": 17, "max": 28, "desc": "Warm"},
            "Apr": {"avg": 26, "min": 20, "max": 33, "desc": "Hot"},
            "May": {"avg": 30, "min": 25, "max": 37, "desc": "Very Hot"},
            "Jun": {"avg": 33, "min": 27, "max": 39, "desc": "Very Hot"},
            "Jul": {"avg": 35, "min": 30, "max": 41, "desc": "Extremely Hot"},
            "Aug": {"avg": 35, "min": 30, "max": 41, "desc": "Extremely Hot"},
            "Sep": {"avg": 32, "min": 27, "max": 38, "desc": "Very Hot"},
            "Oct": {"avg": 28, "min": 23, "max": 35, "desc": "Hot"},
            "Nov": {"avg": 24, "min": 19, "max": 30, "desc": "Warm"},
            "Dec": {"avg": 21, "min": 16, "max": 26, "desc": "Pleasant"}
        }
    },
    "iceland": {
        "climate_type": "Subarctic",
        "ski_suitable": True,
        "monthly_temps": {
            "Jan": {"avg": -1, "min": -3, "max": 2, "desc": "Very Cold"},
            "Feb": {"avg": 0, "min": -2, "max": 3, "desc": "Very Cold"},
            "Mar": {"avg": 0, "min": -2, "max": 3, "desc": "Cold"},
            "Apr": {"avg": 3, "min": 1, "max": 6, "desc": "Cold"},
            "May": {"avg": 7, "min": 4, "max": 10, "desc": "Cool"},
            "Jun": {"avg": 10, "min": 7, "max": 13, "desc": "Cool"},
            "Jul": {"avg": 12, "min": 9, "max": 15, "desc": "Mild"},
            "Aug": {"avg": 11, "min": 8, "max": 14, "desc": "Mild"},
            "Sep": {"avg": 8, "min": 5, "max": 11, "desc": "Cool"},
            "Oct": {"avg": 4, "min": 2, "max": 7, "desc": "Cold"},
            "Nov": {"avg": 1, "min": -1, "max": 4, "desc": "Very Cold"},
            "Dec": {"avg": 0, "min": -2, "max": 3, "desc": "Very Cold"}
        }
    },
    "maldives": {
        "climate_type": "Tropical",
        "ski_suitable": False,
        "monthly_temps": {
            "Jan": {"avg": 28, "min": 26, "max": 30, "desc": "Hot & Dry"},
            "Feb": {"avg": 28, "min": 26, "max": 30, "desc": "Hot & Dry"},
            "Mar": {"avg": 29, "min": 26, "max": 31, "desc": "Hot & Dry"},
            "Apr": {"avg": 29, "min": 27, "max": 31, "desc": "Hot"},
            "May": {"avg": 28, "min": 26, "max": 31, "desc": "Hot & Wet"},
            "Jun": {"avg": 28, "min": 26, "max": 30, "desc": "Hot & Wet"},
            "Jul": {"avg": 28, "min": 25, "max": 30, "desc": "Hot & Wet"},
            "Aug": {"avg": 28, "min": 25, "max": 30, "desc": "Hot & Wet"},
            "Sep": {"avg": 28, "min": 25, "max": 30, "desc": "Hot & Wet"},
            "Oct": {"avg": 28, "min": 25, "max": 30, "desc": "Hot"},
            "Nov": {"avg": 28, "min": 26, "max": 30, "desc": "Hot & Dry"},
            "Dec": {"avg": 28, "min": 26, "max": 30, "desc": "Hot & Dry"}
        }
    },
    "sydney": {
        "climate_type": "Humid Subtropical",
        "ski_suitable": False,
        "monthly_temps": {
            "Jan": {"avg": 23, "min": 19, "max": 27, "desc": "Warm"},
            "Feb": {"avg": 23, "min": 19, "max": 27, "desc": "Warm"},
            "Mar": {"avg": 21, "min": 17, "max": 25, "desc": "Pleasant"},
            "Apr": {"avg": 18, "min": 14, "max": 22, "desc": "Mild"},
            "May": {"avg": 15, "min": 11, "max": 19, "desc": "Cool"},
            "Jun": {"avg": 13, "min": 9, "max": 17, "desc": "Cool"},
            "Jul": {"avg": 12, "min": 8, "max": 17, "desc": "Cool"},
            "Aug": {"avg": 13, "min": 9, "max": 18, "desc": "Cool"},
            "Sep": {"avg": 16, "min": 11, "max": 20, "desc": "Mild"},
            "Oct": {"avg": 18, "min": 14, "max": 22, "desc": "Pleasant"},
            "Nov": {"avg": 20, "min": 16, "max": 24, "desc": "Pleasant"},
            "Dec": {"avg": 22, "min": 18, "max": 26, "desc": "Warm"}
        }
    },
    "cancun": {
        "climate_type": "Tropical Savanna",
        "ski_suitable": False,
        "monthly_temps": {
            "Jan": {"avg": 24, "min": 20, "max": 28, "desc": "Warm & Dry"},
            "Feb": {"avg": 25, "min": 21, "max": 29, "desc": "Warm & Dry"},
            "Mar": {"avg": 26, "min": 22, "max": 30, "desc": "Hot & Dry"},
            "Apr": {"avg": 28, "min": 24, "max": 32, "desc": "Hot & Dry"},
            "May": {"avg": 29, "min": 25, "max": 33, "desc": "Hot"},
            "Jun": {"avg": 29, "min": 26, "max": 33, "desc": "Hot & Humid"},
            "Jul": {"avg": 29, "min": 25, "max": 33, "desc": "Hot & Humid"},
            "Aug": {"avg": 29, "min": 25, "max": 33, "desc": "Hot & Humid"},
            "Sep": {"avg": 29, "min": 25, "max": 32, "desc": "Hot & Rainy"},
            "Oct": {"avg": 27, "min": 24, "max": 31, "desc": "Hot & Rainy"},
            "Nov": {"avg": 26, "min": 22, "max": 29, "desc": "Warm"},
            "Dec": {"avg": 25, "min": 21, "max": 28, "desc": "Warm"}
        }
    }
}

# Load existing destinations
with open('destinations_enriched.json', 'r') as f:
    destinations = json.load(f)

# Add climate data to each destination
enriched_count = 0
for dest in destinations['destinations']:
    dest_id = dest['id']
    if dest_id in climate_data:
        dest['climate'] = climate_data[dest_id]
        enriched_count += 1
        print(f"✅ Added climate data for {dest['name']}")
    else:
        print(f"⚠️  No climate data for {dest['name']} (ID: {dest_id})")

# Save enriched data
with open('destinations_with_climate.json', 'w') as f:
    json.dump(destinations, f, indent=2)

print(f"\n✅ Enriched {enriched_count}/{len(destinations['destinations'])} destinations with climate data")
print("Saved to: destinations_with_climate.json")

print("\n=== Climate Types Available ===")
climate_types = set()
for dest in destinations['destinations']:
    if 'climate' in dest:
        climate_types.add(dest['climate']['climate_type'])
for ct in sorted(climate_types):
    count = sum(1 for d in destinations['destinations'] if d.get('climate', {}).get('climate_type') == ct)
    print(f"  - {ct}: {count} destinations")
