# ✈️ Flight Explorer - Insights & Value Features

## 🎉 What We Built

### Data Sources Combined:
1. **Your Flight Prices** - Real-time scraped data from Google Flights
2. **OpenFlights** - 7,698 airports with coordinates, timezones, countries
3. **Custom Destinations** - 20 curated cities with trip types, budgets, descriptions

### New "💎 Insights & Value" Tab

This comprehensive page combines ALL OpenFlights insights in one place:

#### 📊 Overall Statistics
- Average distance across all routes
- Average price per mile (value metric)
- Number of regions and countries covered

#### 🏆 Best Value Flights (Price per Mile)
- **Interactive scatter plot**: Distance vs Price (bubble size = price/mile)
- **Top 10 Best Deals**: Sorted by lowest cost per mile
- Example: "$0.045/mile to Bangkok" = amazing deal!

#### 📏 Distance Distribution
- **Pie chart**: Short-haul, Medium-haul, Long-haul, Ultra long-haul
- **Bar chart**: Average price by distance category
- Helps users find the right flight duration for their needs

#### 🌍 Regional Insights
- **Bar chart**: Compare average prices across regions
- **Summary table**: Europe vs Asia vs Americas pricing
- See which regions offer better value

#### 🕐 Jet Lag Indicator
- **Histogram**: Timezone differences distribution
- **Jet lag severity guide**:
  - 😊 Minimal (≤2 hours)
  - 😐 Moderate (3-5 hours)
  - 😫 Significant (6-8 hours)
  - 🥱 Severe (>8 hours)
- Tip: Filter for minimal jet lag trips!

#### 🗺️ Route Network Visualization
- Top 50 cheapest routes with color-coded prices
- Shows origin city → destination city with distance

## 🚀 How to Use

### Run the enrichment (one-time):
```bash
python3 enrich_with_openflights.py
```

### Launch the app:
```bash
streamlit run flight_explorer.py
```

### Navigate to "💎 Insights & Value" tab
All the insights are on ONE page - scroll through to explore!

## 💡 Product Ideas This Enables

1. **Value Hunter**: Find flights with best price-per-mile ratio
2. **Distance Seeker**: "I want a long-haul adventure under $1000"
3. **Jet Lag Avoider**: Filter routes with minimal timezone difference
4. **Regional Explorer**: Compare Asia vs Europe pricing
5. **Smart Traveler**: See all metrics at once to make informed decisions

## 📁 Files Added

- `enrich_with_openflights.py` - Enrichment script
- `airports_openflights.csv` - Airport database (7,698 airports)
- `airlines_openflights.csv` - Airlines database
- `flight_prices_worldwide_enriched.json` - Enriched flight data (2.9MB)
- `destinations_enriched.json` - Destinations with coordinates

## 🎯 Key Metrics Added to Each Route

```json
{
  "distance_miles": 4757,
  "distance_km": 7655,
  "price_per_mile": 0.126,
  "origin_city": "Seattle",
  "origin_country": "United States",
  "dest_city": "Tokyo",
  "dest_country": "Japan",
  "timezone_diff": 16,
  "origin_region": "North America",
  "dest_region": "Asia"
}
```

## 🌟 What Makes This Product-Ready

Instead of just showing "$600 to Paris", we now show:
- Paris, France (5,001 miles away)
- $0.12/mile = great value!
- 8-hour timezone difference (moderate jet lag)
- Europe region avg: $650
- Medium-haul flight (3-6k miles)

This transforms raw data into **actionable travel intelligence**! 🚀
