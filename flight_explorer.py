import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Import weather service
try:
    from weather_service import get_monthly_climate
    WEATHER_API_AVAILABLE = True
except ImportError:
    WEATHER_API_AVAILABLE = False
    print("Weather service not available - using static data only")

# Page configuration
st.set_page_config(
    page_title="Flight Prices Explorer",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling - optimized for tablets/iPads
st.markdown("""
<style>
    /* Reduce overall font sizes for better tablet/iPad viewing */
    html, body, [class*="css"] {
        font-size: 14px !important;
    }

    .main-header {
        font-size: 1.8rem !important;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .metric-card {
        background-color: #f0f2f6;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }

    /* Make headings smaller */
    h1 { font-size: 1.6rem !important; }
    h2 { font-size: 1.3rem !important; }
    h3 { font-size: 1.1rem !important; }

    /* Reduce spacing */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }

    /* Make metrics more compact */
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
    }

    /* Reduce caption size */
    .caption, .stCaption {
        font-size: 0.75rem !important;
    }

    /* Make buttons and inputs smaller */
    .stButton button {
        font-size: 0.85rem !important;
        padding: 0.4rem 0.8rem !important;
    }

    .stSelectbox label, .stNumberInput label, .stMultiSelect label {
        font-size: 0.85rem !important;
    }

    /* Reduce tab font size */
    .stTabs [data-baseweb="tab"] {
        font-size: 0.9rem !important;
        padding: 0.5rem 1rem !important;
    }

    /* Make expanders more compact */
    .streamlit-expanderHeader {
        font-size: 0.9rem !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    """Load and preprocess flight data"""
    # Try to load enriched data first, fallback to regular data
    try:
        with open('flight_prices_worldwide_enriched.json', 'r') as f:
            data = json.load(f)
        enriched = True
        st.sidebar.success("✅ Using enriched data with city names")
    except FileNotFoundError:
        with open('flight_prices_worldwide.json', 'r') as f:
            data = json.load(f)
        enriched = False
        st.sidebar.warning("⚠️ Using basic data (no city names)")

    # Extract metadata
    metadata = data['metadata']

    # Convert routes to DataFrame
    df = pd.DataFrame(data['routes'])

    # Convert dates
    df['travel_date'] = pd.to_datetime(df['travel_date'])
    df['scraped_at'] = pd.to_datetime(df['scraped_at'])

    # Load destination metadata with climate data if available
    try:
        # Try climate-enriched version first
        try:
            with open('destinations_with_climate.json', 'r') as f:
                dest_data = json.load(f)
        except FileNotFoundError:
            with open('destinations.json', 'r') as f:
                dest_data = json.load(f)

        destinations_dict = {d['id']: d for d in dest_data['destinations']}
        # Create airport to destination mapping
        airport_to_dest = {}
        for dest in dest_data['destinations']:
            for airport in dest['airports']:
                airport_to_dest[airport] = dest
    except FileNotFoundError:
        destinations_dict = {}
        airport_to_dest = {}

    return df, metadata, destinations_dict, airport_to_dest, enriched

# Load data
try:
    df, metadata, destinations_dict, airport_to_dest, enriched = load_data()

    # Header
    st.markdown('<div class="main-header">✈️ Global Flight Prices Explorer</div>', unsafe_allow_html=True)

    # Metadata section
    with st.expander("📊 Dataset Information", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Routes", metadata['total_routes'])
        with col2:
            st.metric("Economy Routes", metadata['economy_routes'])
        with col3:
            st.metric("Business Routes", metadata['business_routes'])
        with col4:
            st.metric("Scraped At", metadata['scraped_at'][:10])

    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # Cabin class filter
    cabin_classes = st.sidebar.multiselect(
        "Cabin Class",
        options=df['cabin_class'].unique(),
        default=df['cabin_class'].unique()
    )

    # Origin filter
    origins = st.sidebar.multiselect(
        "Origin Airport",
        options=sorted(df['origin'].unique()),
        default=[]
    )

    # Destination filter
    destinations = st.sidebar.multiselect(
        "Destination Airport",
        options=sorted(df['destination'].unique()),
        default=[]
    )

    # Price level filter
    price_levels = st.sidebar.multiselect(
        "Price Level",
        options=df['price_level'].unique(),
        default=df['price_level'].unique()
    )

    # Days ahead filter
    days_ahead_options = sorted(df['days_ahead'].unique())
    days_ahead = st.sidebar.multiselect(
        "Days Ahead",
        options=days_ahead_options,
        default=days_ahead_options
    )

    # Price range filter
    price_min = int(df['price_min'].min())
    price_max = int(df['price_max'].max())
    price_range = st.sidebar.slider(
        "Price Range (Min Price)",
        min_value=price_min,
        max_value=price_max,
        value=(price_min, price_max)
    )

    # Airline filter - extract all unique airlines
    all_airlines_set = set()
    for airlines_list in df['airlines']:
        if airlines_list:
            for airline in airlines_list:
                all_airlines_set.update([a.strip() for a in airline.split(',')])

    all_airlines_sorted = sorted(list(all_airlines_set))

    selected_airlines = st.sidebar.multiselect(
        "Airlines",
        options=all_airlines_sorted,
        default=[]
    )

    # Apply filters
    filtered_df = df[
        (df['cabin_class'].isin(cabin_classes)) &
        (df['price_level'].isin(price_levels)) &
        (df['days_ahead'].isin(days_ahead)) &
        (df['price_min'] >= price_range[0]) &
        (df['price_min'] <= price_range[1])
    ]

    if origins:
        filtered_df = filtered_df[filtered_df['origin'].isin(origins)]
    if destinations:
        filtered_df = filtered_df[filtered_df['destination'].isin(destinations)]
    if selected_airlines:
        # Filter rows where at least one selected airline is in the airlines list
        def has_selected_airline(airlines_list):
            if not airlines_list:
                return False
            for airline_str in airlines_list:
                airlines = [a.strip() for a in airline_str.split(',')]
                if any(airline in selected_airlines for airline in airlines):
                    return True
            return False

        filtered_df = filtered_df[filtered_df['airlines'].apply(has_selected_airline)]

    st.sidebar.markdown(f"**Filtered Routes:** {len(filtered_df)}")

    # Main content tabs
    if enriched:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
            "🎯 Trip Planner",
            "🤖 AI Assistant",
            "💵 Deals",
            "💎 Insights & Value",
            "📈 Price Analysis",
            "🗺️ Route Explorer",
            "✈️ Airlines",
            "📅 Booking Timing",
            "📋 Data Table"
        ])
    else:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "🎯 Trip Planner",
            "🤖 AI Assistant",
            "💵 Deals",
            "📈 Price Analysis",
            "🗺️ Route Explorer",
            "✈️ Airlines",
            "📅 Booking Timing",
            "📋 Data Table"
        ])

    # Tab 1: Trip Planner
    with tab1:
        st.header("🎯 Trip Planner")
        st.markdown("Plan your perfect trip with smart recommendations")

        # Add conversational mode toggle
        mode = st.radio(
            "Choose your planning method:",
            ["💬 Chat with AI Assistant", "📝 Fill Out Form"],
            horizontal=True,
            key="planning_mode"
        )

        if mode == "💬 Chat with AI Assistant":
            st.markdown("### 🤖 AI Trip Planning Assistant")
            st.info("💡 Try: 'I want a beach vacation with my family during summer break' or 'Find me cheap flights to Europe in December'")

            # Initialize agent in session state
            if 'trip_agent' not in st.session_state:
                try:
                    from gemini_agent import GeminiTripAgent
                    st.session_state.trip_agent = GeminiTripAgent()
                    st.session_state.agent_available = True
                except Exception as e:
                    st.session_state.agent_available = False
                    st.error(f"⚠️ AI Assistant not available: {str(e)}\n\nPlease add GEMINI_API_KEY to .streamlit/secrets.toml (see SECRETS_SETUP.md)")

            if st.session_state.get('agent_available', False):
                # Chat interface
                if 'chat_history' not in st.session_state:
                    st.session_state.chat_history = []

                # Display chat history
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg['role']):
                        st.write(msg['content'])

                # Chat input
                user_input = st.chat_input("What kind of trip are you planning?")

                if user_input:
                    # Add user message to history
                    st.session_state.chat_history.append({'role': 'user', 'content': user_input})

                    # Get agent response
                    with st.spinner("Thinking..."):
                        response = st.session_state.trip_agent.chat(user_input)

                    # Add assistant message to history
                    st.session_state.chat_history.append({'role': 'assistant', 'content': response['message']})

                    # Rerun to show updated chat
                    st.rerun()

            st.markdown("---")
            st.markdown("**Or use the form below:**")

        # Integrated search interface
        st.subheader("Your Trip Details")

        # Create origin mapping: airport code -> "City, Country" (or just code if not enriched)
        if enriched and 'origin_city' in filtered_df.columns:
            origin_mapping = filtered_df[['origin', 'origin_city', 'origin_country']].drop_duplicates('origin')
            origin_display = {}
            origin_reverse = {}  # "City, Country" -> code
            for _, row in origin_mapping.iterrows():
                display_name = f"{row['origin_city']}, {row['origin_country']}" if row['origin_city'] else row['origin']
                origin_display[row['origin']] = display_name
                origin_reverse[display_name] = row['origin']
            origin_options = sorted(origin_display.values())
        else:
            origin_options = sorted(df['origin'].unique())
            origin_reverse = {code: code for code in origin_options}

        # Row 1: Travel Party & Origin
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_origin_display = st.selectbox(
                "📍 Flying From",
                options=origin_options,
                key="planner_origin"
            )
            # Get actual airport code
            planner_origin = origin_reverse[selected_origin_display]

        with col2:
            num_adults = st.number_input("👤 Adults", min_value=1, max_value=9, value=1, key="num_adults")

        with col3:
            num_children = st.number_input("👶 Children", min_value=0, max_value=9, value=0, key="num_children")

        # Row 2: Budget & Preferences
        col1, col2, col3 = st.columns(3)

        total_travelers = num_adults + num_children

        with col1:
            planner_budget = st.number_input(
                "💰 Budget per Person ($)",
                min_value=0,
                max_value=10000,
                value=500,
                step=50,
                help="Flight budget per traveler"
            )
            if total_travelers > 1:
                st.caption(f"Total for {total_travelers} travelers: ${planner_budget * total_travelers:,.0f}")

        with col2:
            planner_cabin = st.selectbox(
                "🪑 Cabin Class",
                options=df['cabin_class'].unique(),
                key="planner_cabin"
            )

        with col3:
            # Extract all trip types from destinations
            all_categories = set()
            for dest in airport_to_dest.values():
                all_categories.update(dest.get('categories', []))

            trip_type = st.selectbox(
                "🌴 Trip Type",
                options=['All'] + sorted(list(all_categories)),
                key="trip_type"
            )

        # Row 3: Advanced Filters
        st.markdown("**Advanced Filters**")
        adv_col1, adv_col2, adv_col3, adv_col4, adv_col5 = st.columns(5)

        with adv_col1:
            planner_stops = st.selectbox(
                "🛬 Flight Stops",
                options=['All', 'Direct only', '1 stop max', '2+ stops OK'],
                key="planner_stops"
            )

        with adv_col2:
            planner_travel_period = st.selectbox(
                "📅 Travel Period",
                options=['All Months', 'Next 3 Months', 'Next 6 Months', 'After 6 Months'],
                key="planner_travel_period"
            )

        with adv_col3:
            planner_origin_season = st.selectbox(
                "🌤️ Travel During (Origin)",
                options=['All Seasons', 'Summer ☀️', 'Winter ❄️', 'Spring 🌸', 'Fall 🍂'],
                key="planner_origin_season",
                help="When you want to travel from home (e.g., during summer vacation)"
            )

        with adv_col4:
            planner_dest_season = st.selectbox(
                "🌡️ Destination Weather",
                options=['All Seasons', 'Summer ☀️', 'Winter ❄️', 'Spring 🌸', 'Fall 🍂'],
                key="planner_dest_season",
                help="What weather you want at your destination"
            )

        with adv_col5:
            planner_school_region = st.selectbox(
                "📚 School Calendar",
                options=['All Periods',
                         'US/Canada: School Days', 'US/Canada: Summer Break', 'US/Canada: Winter Break', 'US/Canada: Spring Break',
                         'Australia: School Days', 'Australia: Summer Break (Dec-Jan)', 'Australia: Winter Break (Jun-Jul)',
                         'Europe: School Days', 'Europe: Summer Holiday (Jul-Aug)', 'Europe: Winter Holiday (Dec-Jan)',
                         'Asia: School Days', 'Asia: Summer Break (Jun-Aug)'],
                key="planner_school",
                help="When kids are off school at your home location"
            )

        st.markdown("---")

        # Filter based on planner inputs (use filtered_df to respect sidebar filters)
        planner_df = filtered_df[
            (filtered_df['origin'] == planner_origin) &
            (filtered_df['cabin_class'] == planner_cabin) &
            (filtered_df['price_avg'] <= planner_budget)
        ].copy()

        # Filter by trip type if specified
        if trip_type != 'All':
            filtered_destinations = []
            for airport_code, dest_info in airport_to_dest.items():
                if trip_type in dest_info.get('categories', []):
                    filtered_destinations.append(airport_code)
            planner_df = planner_df[planner_df['destination'].isin(filtered_destinations)]

        # Apply advanced filters
        # Stops filter
        if planner_stops != 'All':
            planner_df = planner_df[planner_df['sample_flight'].notna()]
            if planner_stops == 'Direct only':
                planner_df = planner_df[planner_df['sample_flight'].apply(
                    lambda x: x.get('stops', 99) == 0 if isinstance(x, dict) else False
                )]
            elif planner_stops == '1 stop max':
                planner_df = planner_df[planner_df['sample_flight'].apply(
                    lambda x: x.get('stops', 99) <= 1 if isinstance(x, dict) else False
                )]

        # Travel period filter
        if planner_travel_period != 'All Months':
            today = pd.Timestamp.now()
            if planner_travel_period == 'Next 3 Months':
                planner_df = planner_df[planner_df['travel_date'] <= today + pd.Timedelta(days=90)]
            elif planner_travel_period == 'Next 6 Months':
                planner_df = planner_df[planner_df['travel_date'] <= today + pd.Timedelta(days=180)]
            elif planner_travel_period == 'After 6 Months':
                planner_df = planner_df[planner_df['travel_date'] > today + pd.Timedelta(days=180)]

        # Calculate seasons for both origin and destination (considering hemisphere)
        def get_season(date, country):
            """Get season at location based on hemisphere"""
            month = date.month

            # Southern Hemisphere countries (opposite seasons)
            southern_countries = ['Australia', 'New Zealand', 'Argentina', 'Chile', 'Brazil',
                                 'South Africa', 'Uruguay', 'Paraguay', 'Peru', 'Bolivia']

            is_southern = country in southern_countries if country else False

            if is_southern:
                # Opposite seasons for Southern Hemisphere
                if month in [12, 1, 2]:
                    return "Summer ☀️"
                elif month in [3, 4, 5]:
                    return "Fall 🍂"
                elif month in [6, 7, 8]:
                    return "Winter ❄️"
                else:
                    return "Spring 🌸"
            else:
                # Northern Hemisphere (default)
                if month in [12, 1, 2]:
                    return "Winter ❄️"
                elif month in [3, 4, 5]:
                    return "Spring 🌸"
                elif month in [6, 7, 8]:
                    return "Summer ☀️"
                else:
                    return "Fall 🍂"

        if enriched and 'dest_country' in planner_df.columns and 'origin_country' in planner_df.columns:
            # Calculate destination season
            planner_df['dest_season'] = planner_df.apply(
                lambda row: get_season(row['travel_date'], row.get('dest_country')),
                axis=1
            )

            # Calculate origin season
            planner_df['origin_season'] = planner_df.apply(
                lambda row: get_season(row['travel_date'], row.get('origin_country')),
                axis=1
            )

            # Filter by origin season if specified
            if planner_origin_season != 'All Seasons':
                planner_df = planner_df[planner_df['origin_season'] == planner_origin_season]

            # Filter by destination season if specified
            if planner_dest_season != 'All Seasons':
                planner_df = planner_df[planner_df['dest_season'] == planner_dest_season]

        # School period filter
        if planner_school_region != 'All Periods':
            def check_school_period(date, period_type):
                month, day = date.month, date.day

                # US/Canada calendars
                if 'US/Canada: Summer Break' in period_type:
                    return (month == 6 and day >= 15) or month == 7 or (month == 8 and day <= 20)
                elif 'US/Canada: Winter Break' in period_type:
                    return (month == 12 and day >= 20) or (month == 1 and day <= 5)
                elif 'US/Canada: Spring Break' in period_type:
                    return month == 3 and 15 <= day <= 31
                elif 'US/Canada: School Days' in period_type:
                    # Exclude all US/Canada holidays
                    us_holidays = ((month == 6 and day >= 15) or month == 7 or (month == 8 and day <= 20) or
                                   (month == 12 and day >= 20) or (month == 1 and day <= 5) or
                                   (month == 3 and 15 <= day <= 31) or (month == 11 and 20 <= day <= 27))
                    return not us_holidays

                # Australia calendars (opposite seasons)
                elif 'Australia: Summer Break' in period_type:
                    return (month == 12 and day >= 15) or month == 1 or (month == 2 and day <= 10)
                elif 'Australia: Winter Break' in period_type:
                    return (month == 6 and day >= 20) or (month == 7 and day <= 10)
                elif 'Australia: School Days' in period_type:
                    aus_holidays = ((month == 12 and day >= 15) or month == 1 or (month == 2 and day <= 10) or
                                    (month == 6 and day >= 20) or (month == 7 and day <= 10) or
                                    (month == 4 and 1 <= day <= 14) or (month == 9 and 20 <= day <= 30))
                    return not aus_holidays

                # Europe calendars
                elif 'Europe: Summer Holiday' in period_type:
                    return month == 7 or month == 8
                elif 'Europe: Winter Holiday' in period_type:
                    return (month == 12 and day >= 20) or (month == 1 and day <= 6)
                elif 'Europe: School Days' in period_type:
                    eu_holidays = (month in [7, 8] or (month == 12 and day >= 20) or (month == 1 and day <= 6))
                    return not eu_holidays

                # Asia calendars (varies but using general pattern)
                elif 'Asia: Summer Break' in period_type:
                    return month in [7, 8]
                elif 'Asia: School Days' in period_type:
                    asia_holidays = (month in [7, 8] or (month == 12 and day >= 25) or (month == 1 and day <= 5))
                    return not asia_holidays

                return False

            planner_df['matches_period'] = planner_df['travel_date'].apply(
                lambda x: check_school_period(x, planner_school_region)
            )
            planner_df = planner_df[planner_df['matches_period'] == True]

        # Add destination metadata
        planner_df['dest_info'] = planner_df['destination'].map(airport_to_dest)
        planner_df['dest_name'] = planner_df['dest_info'].apply(lambda x: x.get('name', 'Unknown') if isinstance(x, dict) else 'Unknown')
        planner_df['dest_country'] = planner_df['dest_info'].apply(lambda x: x.get('country', '') if isinstance(x, dict) else '')
        planner_df['dest_categories'] = planner_df['dest_info'].apply(lambda x: ', '.join(x.get('categories', [])) if isinstance(x, dict) else '')
        planner_df['budget_per_day'] = planner_df['dest_info'].apply(lambda x: x.get('budget_per_day', {}).get('moderate', 0) if isinstance(x, dict) else 0)
        planner_df['description'] = planner_df['dest_info'].apply(lambda x: x.get('description', '') if isinstance(x, dict) else '')

        if not planner_df.empty:
            st.success(f"✅ Found {len(planner_df)} affordable routes from {planner_origin}")

            # Best deals - comparing price to average for similar routes
            planner_df['value_score'] = 100 - ((planner_df['price_avg'] / planner_df['price_avg'].max()) * 100)
            planner_df = planner_df.sort_values('value_score', ascending=False)

            # Top recommendations
            st.subheader("🌟 Top Recommendations")

            # Calculate total travelers
            total_travelers = num_adults + num_children if 'num_adults' in locals() else 1

            top_deals = planner_df.head(10)

            for idx, row in top_deals.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

                    with col1:
                        # Show destination name if available, otherwise airport code
                        dest_display = f"{row['dest_name']}" if row['dest_name'] != 'Unknown' else row['destination']
                        if row['dest_country']:
                            dest_display += f", {row['dest_country']}"
                        st.markdown(f"### {dest_display}")

                        # Show categories if available
                        if row['dest_categories']:
                            st.caption(f"🏷️ {row['dest_categories']}")

                    with col2:
                        st.metric("Flight Price", f"${row['price_avg']:.0f}")
                        if total_travelers > 1:
                            st.caption(f"${row['price_avg'] * total_travelers:.0f} for {total_travelers} travelers")

                    with col3:
                        st.metric("Price Range", f"${row['price_min']:.0f} - ${row['price_max']:.0f}")

                    with col4:
                        st.metric("Value Score", f"{row['value_score']:.0f}/100")

                    # Show description if available
                    if row['description']:
                        st.markdown(f"*{row['description']}*")

                    # Key booking information
                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.markdown(f"**📅 Travel Date:** {row['travel_date'].strftime('%b %d, %Y')}")
                        st.markdown(f"**⏰ Book By:** {(row['travel_date'] - pd.Timedelta(days=row['days_ahead'])).strftime('%b %d, %Y')} ({row['days_ahead']} days ahead)")

                    with col_b:
                        # Extract and show airlines
                        airlines_display = "Various airlines"
                        if row['airlines'] and len(row['airlines']) > 0:
                            airlines_list = [a.strip() for a in row['airlines'][0].split(',')]
                            airlines_display = ', '.join(airlines_list[:3])  # Show up to 3 airlines
                            if len(airlines_list) > 3:
                                airlines_display += f" +{len(airlines_list)-3} more"

                        st.markdown(f"**✈️ Airlines:** {airlines_display}")
                        st.markdown(f"**🎫 Cabin:** {row['cabin_class'].title()} | **💰 Level:** {row['price_level'].title()}")

                        # Show seasons and temperature with clear location context
                        season_parts = []
                        if 'origin_season' in row and row['origin_season']:
                            origin_loc = row.get('origin_city', 'Origin')
                            season_parts.append(f"🏠 {origin_loc}: {row['origin_season']}")
                        if 'dest_season' in row and row['dest_season']:
                            dest_loc = row.get('dest_city', 'Destination')
                            dest_airport = row.get('destination')

                            # Try to get temperature info for destination
                            temp_info = ""
                            if dest_airport in airport_to_dest:
                                dest_data = airport_to_dest[dest_airport]

                                # Try static data first
                                if 'climate' in dest_data and 'monthly_temps' in dest_data['climate']:
                                    travel_month = row['travel_date'].strftime('%b')
                                    month_temps = dest_data['climate']['monthly_temps'].get(travel_month, {})
                                    if month_temps:
                                        avg_temp = month_temps['avg']
                                        temp_desc = month_temps['desc']
                                        temp_f = int(avg_temp * 9/5 + 32)
                                        temp_info = f" ({avg_temp}°C/{temp_f}°F - {temp_desc})"

                                # Fallback to Open-Meteo API if static data not available
                                elif WEATHER_API_AVAILABLE and 'coordinates' in dest_data:
                                    try:
                                        coords = dest_data['coordinates']
                                        travel_month_num = row['travel_date'].month
                                        climate_data = get_monthly_climate(
                                            coords['latitude'],
                                            coords['longitude'],
                                            travel_month_num
                                        )
                                        if climate_data:
                                            avg_temp = climate_data['avg']
                                            temp_desc = climate_data['desc']
                                            temp_f = int(avg_temp * 9/5 + 32)
                                            temp_info = f" ({avg_temp}°C/{temp_f}°F - {temp_desc})"
                                    except Exception as e:
                                        pass  # Silently fail if API unavailable

                            season_parts.append(f"🎯 {dest_loc}: {row['dest_season']}{temp_info}")

                        if season_parts:
                            st.markdown(f"**🌤️ Climate:** {' → '.join(season_parts)}")

                    # Show family pricing summary if applicable
                    if total_travelers > 1:
                        st.info(f"👨‍👩‍👧‍👦 **Total for {total_travelers} travelers:** ${row['price_avg'] * total_travelers:.0f} flights only")

                    # Flight Details Section
                    if 'sample_flight' in row and row['sample_flight']:
                        with st.expander("✈️ Flight Details & Route Information"):
                            flight_info = row['sample_flight']

                            detail_col1, detail_col2, detail_col3 = st.columns(3)

                            with detail_col1:
                                st.markdown("**⏱️ Flight Duration**")
                                if isinstance(flight_info, dict) and 'duration' in flight_info:
                                    st.info(flight_info['duration'])
                                else:
                                    st.caption("Duration not available")

                            with detail_col2:
                                st.markdown("**🛬 Stops & Connections**")
                                if isinstance(flight_info, dict) and 'stops' in flight_info:
                                    stops = flight_info['stops']
                                    if stops == 0:
                                        st.success("Direct flight ✓")
                                    elif stops == 1:
                                        st.info("1 stop")
                                    else:
                                        st.warning(f"{stops} stops")
                                else:
                                    st.caption("Stop info not available")

                            with detail_col3:
                                st.markdown("**🎫 Sample Fare**")
                                if isinstance(flight_info, dict) and 'price' in flight_info:
                                    st.metric("From", f"${flight_info['price']}")
                                    if isinstance(flight_info, dict) and 'airline' in flight_info:
                                        st.caption(f"via {flight_info['airline']}")

                            # Route information
                            st.markdown("---")
                            st.markdown("**📍 Route Information**")
                            route_col1, route_col2 = st.columns(2)

                            with route_col1:
                                origin_name = row.get('origin_city', row['origin'])
                                dest_name = row.get('dest_city', row['destination'])
                                st.markdown(f"**Routing:** {origin_name} → {dest_name}")

                                # Show distance if available
                                if 'distance_miles' in row:
                                    st.caption(f"Total distance: {row['distance_miles']:,} miles ({row.get('distance_km', 0):,} km)")

                            with route_col2:
                                # Travel period info
                                st.markdown(f"**Travel Period:** {row['travel_date'].strftime('%B %Y')}")

                                # Best booking window
                                days_to_book = row['days_ahead']
                                if days_to_book < 14:
                                    st.warning(f"⚡ Book immediately ({days_to_book} days)")
                                elif days_to_book < 30:
                                    st.info(f"🏃 Book within {days_to_book} days")
                                else:
                                    st.success(f"✓ Book by {days_to_book} days ahead")

                            # Stopover insights (if multiple stops)
                            if isinstance(flight_info, dict) and flight_info.get('stops', 0) > 0:
                                st.markdown("---")
                                st.markdown("**🌍 Stopover Opportunities**")

                                # Extract likely stopover cities from airline combinations
                                if row['airlines'] and len(row['airlines']) > 0:
                                    common_hubs = {
                                        'Qatar': 'Doha (DOH) - Explore the Pearl of the Gulf',
                                        'Emirates': 'Dubai (DXB) - Luxury shopping & modern architecture',
                                        'Etihad': 'Abu Dhabi (AUH) - Cultural attractions & beaches',
                                        'Turkish': 'Istanbul (IST) - East meets West, rich history',
                                        'Singapore Airlines': 'Singapore (SIN) - Garden city & culinary paradise',
                                        'Cathay': 'Hong Kong (HKG) - Vibrant city & harbor views',
                                        'ANA': 'Tokyo (NRT/HND) - Japanese culture & technology',
                                        'Lufthansa': 'Frankfurt (FRA) or Munich (MUC) - German efficiency',
                                        'Air France': 'Paris (CDG) - The City of Lights',
                                        'KLM': 'Amsterdam (AMS) - Canals & museums',
                                        'British Airways': 'London (LHR) - Historic landmarks',
                                        'Korean Air': 'Seoul (ICN) - K-culture & innovation'
                                    }

                                    airlines_str = ', '.join(row['airlines'][:3])
                                    possible_hubs = []
                                    for airline, hub_info in common_hubs.items():
                                        if airline.lower() in airlines_str.lower():
                                            possible_hubs.append(f"• {hub_info}")

                                    if possible_hubs:
                                        st.markdown("**Likely stopover cities:**")
                                        for hub in possible_hubs[:2]:  # Show max 2
                                            st.caption(hub)
                                    else:
                                        st.caption("Stopover cities vary by airline - check with carrier for details")

                            # Important notes
                            st.markdown("---")
                            st.caption("💡 **Note:** Flight details based on sample fares. Actual routing, duration, and connections may vary. Always verify with airline before booking.")

                    # Price calendar - show all available dates for this destination
                    dest_routes = planner_df[
                        (planner_df['destination'] == row['destination']) &
                        (planner_df['cabin_class'] == row['cabin_class'])
                    ].sort_values('travel_date')

                    if len(dest_routes) > 1:
                        with st.expander(f"📅 Compare all {len(dest_routes)} available dates & airlines"):
                            # Create price calendar visualization
                            dest_routes_chart = dest_routes.copy()
                            dest_routes_chart['date_str'] = dest_routes_chart['travel_date'].dt.strftime('%b %d')
                            dest_routes_chart['month'] = dest_routes_chart['travel_date'].dt.strftime('%b %Y')

                            # Bar chart showing price by date
                            fig_dates = px.bar(
                                dest_routes_chart,
                                x='date_str',
                                y='price_avg',
                                color='price_avg',
                                color_continuous_scale='RdYlGn_r',
                                labels={'date_str': 'Travel Date', 'price_avg': 'Price ($)'},
                                title=f'Price Calendar - {row["cabin_class"].title()} Class',
                                hover_data={
                                    'price_avg': ':$.0f',
                                    'price_min': ':$.0f',
                                    'price_max': ':$.0f',
                                    'days_ahead': True
                                }
                            )
                            fig_dates.update_layout(
                                height=300,
                                showlegend=False,
                                xaxis_tickangle=-45
                            )
                            st.plotly_chart(fig_dates, use_container_width=True, key=f"price_cal_{row['destination']}_{idx}")

                            # Detailed comparison table with all booking options
                            st.markdown("**📋 Complete Booking Options**")

                            # Helper functions for family travel insights
                            def get_season(date):
                                month = date.month
                                if month in [12, 1, 2]:
                                    return "Winter ❄️"
                                elif month in [3, 4, 5]:
                                    return "Spring 🌸"
                                elif month in [6, 7, 8]:
                                    return "Summer ☀️"
                                else:
                                    return "Fall 🍂"

                            def is_school_holiday(date):
                                month, day = date.month, date.day
                                # Summer break (June 15 - Aug 20)
                                if (month == 6 and day >= 15) or month == 7 or (month == 8 and day <= 20):
                                    return "🎒 Summer Break"
                                # Winter holidays (Dec 20 - Jan 5)
                                elif (month == 12 and day >= 20) or (month == 1 and day <= 5):
                                    return "🎄 Winter Break"
                                # Spring break (March 15-31)
                                elif month == 3 and 15 <= day <= 31:
                                    return "🌴 Spring Break"
                                # Thanksgiving week
                                elif month == 11 and 20 <= day <= 27:
                                    return "🦃 Thanksgiving"
                                else:
                                    return "📚 School Days"

                            def get_booking_window_advice(days):
                                if days < 14:
                                    return "⚡ Last Minute"
                                elif days < 30:
                                    return "🏃 Book Soon"
                                elif days < 60:
                                    return "✓ Good Window"
                                elif days < 120:
                                    return "⭐ Early Bird"
                                else:
                                    return "🔮 Far Advance"

                            def get_day_type(date):
                                day_name = date.strftime('%A')
                                if day_name in ['Saturday', 'Sunday']:
                                    return f"🎉 {day_name}"
                                else:
                                    return f"📅 {day_name}"

                            # Prepare detailed table
                            comparison_data = []
                            today = pd.Timestamp.now()

                            for idx, route in dest_routes_chart.iterrows():
                                # Extract airlines
                                airlines_str = "Various"
                                if route['airlines'] and len(route['airlines']) > 0:
                                    airlines_list = [a.strip() for a in route['airlines'][0].split(',')]
                                    airlines_str = ', '.join(airlines_list)

                                # Calculate days until departure
                                days_until = (route['travel_date'] - today).days

                                comparison_data.append({
                                    'Travel Date': route['travel_date'].strftime('%b %d, %Y'),
                                    'Day': get_day_type(route['travel_date']),
                                    'Season': get_season(route['travel_date']),
                                    'Period': is_school_holiday(route['travel_date']),
                                    'Departs In': f"{days_until} days" if days_until > 0 else "Past",
                                    'Book Window': get_booking_window_advice(route['days_ahead']),
                                    'Airlines': airlines_str,
                                    'Avg Price': f"${route['price_avg']:.0f}",
                                    'Price Range': f"${route['price_min']:.0f} - ${route['price_max']:.0f}",
                                    'Price Level': route['price_level'].title()
                                })

                            comparison_df = pd.DataFrame(comparison_data)
                            st.dataframe(comparison_df, use_container_width=True, hide_index=True)

                            # Show monthly summary and best deals
                            col_cal1, col_cal2 = st.columns(2)

                            with col_cal1:
                                st.markdown("**📊 Monthly Price Trends**")
                                monthly_avg = dest_routes_chart.groupby('month').agg({
                                    'price_avg': 'mean',
                                    'travel_date': 'count'
                                }).round(0)
                                monthly_avg.columns = ['Avg Price ($)', 'Dates Available']
                                st.dataframe(monthly_avg, use_container_width=True)

                            with col_cal2:
                                # Find best deal
                                cheapest = dest_routes_chart.loc[dest_routes_chart['price_avg'].idxmin()]
                                most_expensive = dest_routes_chart.loc[dest_routes_chart['price_avg'].idxmax()]
                                savings = most_expensive['price_avg'] - cheapest['price_avg']

                                st.markdown("**💡 Best Deal**")

                                # Show airlines for cheapest option
                                cheapest_airlines = "Various airlines"
                                if cheapest['airlines'] and len(cheapest['airlines']) > 0:
                                    airlines_list = [a.strip() for a in cheapest['airlines'][0].split(',')]
                                    cheapest_airlines = ', '.join(airlines_list[:2])
                                    if len(airlines_list) > 2:
                                        cheapest_airlines += f" +{len(airlines_list)-2} more"

                                st.success(f"**{cheapest['travel_date'].strftime('%b %d, %Y')}** - **${cheapest['price_avg']:.0f}**")
                                st.caption(f"✈️ {cheapest_airlines}")
                                st.caption(f"📅 Book by: {(cheapest['travel_date'] - pd.Timedelta(days=cheapest['days_ahead'])).strftime('%b %d, %Y')}")

                                if savings > 50:
                                    st.markdown(f"💰 Save **${savings:.0f}** vs most expensive date")
                                    if total_travelers > 1:
                                        st.caption(f"**${savings * total_travelers:.0f}** total savings for {total_travelers} travelers")

                            # Family Travel Insights
                            st.markdown("---")
                            st.markdown("**👨‍👩‍👧‍👦 Family Travel Insights**")

                            # Analyze patterns
                            school_days = sum(1 for d in comparison_data if d['Period'] == '📚 School Days')
                            weekdays = sum(1 for d in comparison_data if '📅' in d['Day'])
                            summer_routes = sum(1 for d in comparison_data if 'Summer' in d['Season'])

                            insight_col1, insight_col2, insight_col3 = st.columns(3)

                            with insight_col1:
                                st.markdown("**💰 Best Savings Tips**")
                                if school_days > 0:
                                    school_day_prices = [float(d['Avg Price'].replace('$','')) for d in comparison_data if d['Period'] == '📚 School Days']
                                    holiday_prices = [float(d['Avg Price'].replace('$','')) for d in comparison_data if d['Period'] != '📚 School Days']
                                    if holiday_prices and school_day_prices:
                                        avg_savings = np.mean(holiday_prices) - np.mean(school_day_prices)
                                        if avg_savings > 50:
                                            st.success(f"Save ~${avg_savings:.0f}/person by traveling during school days")
                                            if total_travelers > 1:
                                                st.caption(f"💸 ${avg_savings * total_travelers:.0f} total family savings!")
                                        else:
                                            st.info("Prices similar across school/holiday periods")
                                    else:
                                        st.info("Mix of school days and holiday dates available")
                                else:
                                    st.info("All dates are during school holidays")

                                if weekdays > 0:
                                    st.caption(f"📅 {weekdays} weekday departures available (often cheaper)")

                            with insight_col2:
                                # Analyze airline patterns
                                all_airlines = set()
                                for route in dest_routes_chart.itertuples():
                                    if route.airlines and len(route.airlines) > 0:
                                        airlines = [a.strip() for a in route.airlines[0].split(',')]
                                        all_airlines.update(airlines)

                                st.markdown(f"**✈️ Airlines:** {len(all_airlines)} options")
                                if all_airlines:
                                    st.caption(', '.join(sorted(list(all_airlines))[:4]))
                                    if len(all_airlines) > 4:
                                        st.caption(f"...+{len(all_airlines)-4} more")

                            with insight_col3:
                                st.markdown("**📅 Best Time to Book**")
                                # Find cheapest date characteristics
                                cheapest_route = min(comparison_data, key=lambda x: float(x['Avg Price'].replace('$','')))
                                st.info(f"{cheapest_route['Period']}")
                                st.caption(f"{cheapest_route['Day']}")
                                st.caption(f"{cheapest_route['Season']}")

                            # Additional family-focused insights
                            st.markdown("---")
                            st.markdown("**🎯 Travel Planning Tips**")

                            tip_col1, tip_col2 = st.columns(2)

                            with tip_col1:
                                st.markdown("**📚 School Calendar Awareness**")
                                period_counts = {}
                                for d in comparison_data:
                                    period = d['Period']
                                    period_counts[period] = period_counts.get(period, 0) + 1

                                for period, count in sorted(period_counts.items(), key=lambda x: -x[1]):
                                    st.caption(f"{period}: {count} dates")

                            with tip_col2:
                                st.markdown("**⏰ Booking Urgency**")
                                urgent = sum(1 for d in comparison_data if '⚡' in d['Book Window'] or '🏃' in d['Book Window'])
                                good = sum(1 for d in comparison_data if '✓' in d['Book Window'])
                                early = sum(1 for d in comparison_data if '⭐' in d['Book Window'] or '🔮' in d['Book Window'])

                                if urgent > 0:
                                    st.warning(f"⚡ {urgent} dates need immediate booking")
                                if good > 0:
                                    st.success(f"✓ {good} dates in optimal booking window")
                                if early > 0:
                                    st.info(f"⭐ {early} dates for early planners")

                    # Calculate total trip cost if we have daily budget
                    if row['budget_per_day'] > 0:
                        for duration in [5, 7, 10]:
                            if total_travelers > 1:
                                total_cost = (row['price_avg'] * total_travelers) + (duration * row['budget_per_day'] * total_travelers)
                                if 'total_budget' in locals() and total_cost <= total_budget * 1.5:
                                    st.caption(f"💡 {duration} days for {total_travelers} people: ~${total_cost:.0f} total (flights + accommodation/food)")
                                    break
                            else:
                                total_cost = row['price_avg'] + (duration * row['budget_per_day'])
                                if total_cost <= planner_budget * 2:
                                    st.caption(f"💡 {duration} days total: ~${total_cost:.0f} (flight + accommodation/food)")
                                    break

                    st.markdown("---")

            # Flexible Dates View
            st.subheader("📅 Flexible Dates Explorer")
            st.markdown("See how prices vary across different travel dates for your selected origin")

            # Group by destination and show date options
            if not planner_df.empty:
                # Get top 3 destinations
                top_destinations = planner_df.groupby('destination').agg({
                    'price_avg': 'min'
                }).nsmallest(3, 'price_avg').index.tolist()

                for dest in top_destinations:
                    dest_routes = planner_df[planner_df['destination'] == dest].sort_values('travel_date')

                    if len(dest_routes) > 1:  # Only show if multiple dates available
                        dest_name = dest_routes.iloc[0]['dest_name'] if dest_routes.iloc[0]['dest_name'] != 'Unknown' else dest
                        dest_country = dest_routes.iloc[0]['dest_country']

                        with st.expander(f"✈️ {dest_name}, {dest_country} - {len(dest_routes)} dates available"):
                            # Create a date comparison table
                            date_comparison = dest_routes[['travel_date', 'price_min', 'price_avg', 'price_max', 'days_ahead', 'cabin_class']].copy()
                            date_comparison['travel_date'] = date_comparison['travel_date'].dt.strftime('%b %d, %Y')
                            date_comparison.columns = ['Travel Date', 'Min Price', 'Avg Price', 'Max Price', 'Book In (days)', 'Class']

                            # Highlight cheapest
                            cheapest_idx = dest_routes['price_avg'].idxmin()
                            cheapest_date = dest_routes.loc[cheapest_idx, 'travel_date'].strftime('%b %d, %Y')
                            cheapest_price = dest_routes.loc[cheapest_idx, 'price_avg']

                            st.success(f"💰 Cheapest: {cheapest_date} at ${cheapest_price:.0f}")

                            # Show table
                            st.dataframe(date_comparison, use_container_width=True, hide_index=True)

                            # If family pricing
                            if total_travelers > 1:
                                st.caption(f"Family of {total_travelers}: ${cheapest_price * total_travelers:.0f} total for cheapest date")

            st.markdown("---")

            # Destination insights
            st.subheader("📊 Destination Insights")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🏆 Best Value Destinations**")
                # Create display name: "City, Country" or fallback to airport code
                planner_df['dest_display'] = planner_df.apply(
                    lambda x: f"{x['dest_name']}, {x['dest_country']}" if x['dest_name'] != 'Unknown' else x['destination'],
                    axis=1
                )
                best_value = planner_df.groupby('dest_display').agg({
                    'price_avg': 'min',
                    'value_score': 'max'
                }).sort_values('price_avg').head(10)

                fig = px.bar(
                    x=best_value['price_avg'].values,
                    y=best_value.index,
                    orientation='h',
                    labels={'x': 'Average Price ($)', 'y': 'Destination'},
                    title='Cheapest Destinations Within Budget',
                    color=best_value['price_avg'].values,
                    color_continuous_scale='RdYlGn_r'
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("**📅 Best Booking Windows**")
                booking_analysis = planner_df.groupby('days_ahead').agg({
                    'price_avg': 'mean',
                    'destination': 'count'
                }).sort_values('price_avg')

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=booking_analysis.index,
                    y=booking_analysis['price_avg'],
                    mode='lines+markers',
                    name='Avg Price',
                    line=dict(color='blue', width=3),
                    marker=dict(size=10)
                ))
                fig.update_layout(
                    title='Average Price by Booking Window',
                    xaxis_title='Days in Advance',
                    yaxis_title='Average Price ($)',
                    hovermode='x'
                )
                st.plotly_chart(fig, use_container_width=True)

            # Budget breakdown
            st.subheader("💡 Budget Optimization Tips")

            col1, col2, col3 = st.columns(3)

            cheapest_route = planner_df.nsmallest(1, 'price_min').iloc[0]
            best_value_route = planner_df.nlargest(1, 'value_score').iloc[0]
            best_timing = planner_df.groupby('days_ahead')['price_avg'].mean().idxmin()

            # Format destination names
            cheapest_dest = f"{cheapest_route['dest_name']}, {cheapest_route['dest_country']}" if cheapest_route['dest_name'] != 'Unknown' else cheapest_route['destination']
            best_value_dest = f"{best_value_route['dest_name']}, {best_value_route['dest_country']}" if best_value_route['dest_name'] != 'Unknown' else best_value_route['destination']

            with col1:
                st.info(f"""
                **🎯 Cheapest Option**
                - Destination: {cheapest_dest}
                - Price: ${cheapest_route['price_min']:.0f}
                - Savings: ${planner_budget - cheapest_route['price_min']:.0f}
                """)

            with col2:
                st.success(f"""
                **⭐ Best Value**
                - Destination: {best_value_dest}
                - Price: ${best_value_route['price_avg']:.0f}
                - Value Score: {best_value_route['value_score']:.0f}/100
                """)

            with col3:
                st.warning(f"""
                **📆 Optimal Booking**
                - Book {best_timing} days ahead
                - Avg savings: ${planner_df['price_avg'].mean() - planner_df[planner_df['days_ahead']==best_timing]['price_avg'].mean():.0f}
                """)

        else:
            st.warning(f"😔 No routes found from {planner_origin} within ${planner_budget} budget for {planner_cabin} class.")
            st.info("💡 Try increasing your budget or selecting a different origin airport.")

    # Tab 2: AI Assistant
    with tab2:
        st.header("🤖 AI Trip Assistant")
        st.markdown("Chat naturally about your travel plans - I'll search real flights for you!")

        # Initialize AI agent
        if 'ai_agent' not in st.session_state:
            try:
                from gemini_tool_calling import GeminiToolCallingAgent
                st.session_state.ai_agent = GeminiToolCallingAgent(filtered_df, airport_to_dest)
                st.session_state.ai_ready = True
            except Exception as e:
                st.session_state.ai_ready = False
                st.error(f"""
                ⚠️ **AI Assistant not available:** {str(e)}

                **To enable:**
                1. Add `GEMINI_API_KEY` to `.streamlit/secrets.toml`
                2. See `SECRETS_SETUP.md` for instructions
                3. Get free key at: https://aistudio.google.com/app/apikey
                """)

        if st.session_state.get('ai_ready', False):
            # Example prompts
            with st.expander("💡 Example Questions", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""
                    - "Beach vacation from Sydney under $800"
                    - "Ski trip from New York in December"
                    - "Romantic honeymoon, budget $2000"
                    """)
                with col2:
                    st.markdown("""
                    - "Family trip during summer break"
                    - "Direct flights to Europe"
                    - "Cheap flights to Asia next month"
                    """)

            # Chat history
            if 'ai_chat' not in st.session_state:
                st.session_state.ai_chat = []
                st.session_state.ai_chat.append({
                    'role': 'assistant',
                    'content': "👋 Hi! Tell me about your dream trip and I'll search real flights for you!"
                })

            # Display chat
            for msg in st.session_state.ai_chat:
                with st.chat_message(msg['role']):
                    st.write(msg['content'])

                    # Display flight results if present
                    if 'results' in msg and msg['results']:
                        results = msg['results']
                        st.success(f"✅ Found {results['found']} matching flights!")

                        if results['flights']:
                            st.markdown("### Top Flight Options:")
                            for idx, flight in enumerate(results['flights'], 1):
                                with st.container():
                                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

                                    with col1:
                                        dest = flight.get('destination', 'Unknown')
                                        country = flight.get('country', '')
                                        if country:
                                            st.markdown(f"### {dest}, {country}")
                                        else:
                                            st.markdown(f"### {dest}")

                                    with col2:
                                        price = flight.get('price', 0)
                                        st.metric("Price", f"${price}")
                                        if results.get('total_travelers', 1) > 1:
                                            total = price * results['total_travelers']
                                            st.caption(f"Total: ${total:,}")

                                    with col3:
                                        cabin = flight.get('cabin', 'economy').title()
                                        st.metric("Class", cabin)

                                    with col4:
                                        if flight.get('travel_date'):
                                            st.metric("Travel Date", flight['travel_date'])

                                    st.markdown("---")

            # Chat input
            user_msg = st.chat_input("What kind of trip are you planning?", key="ai_chat_input")

            if user_msg:
                # Add user message
                st.session_state.ai_chat.append({'role': 'user', 'content': user_msg})

                # Get AI response
                with st.spinner("🔍 Searching flights..."):
                    response = st.session_state.ai_agent.chat(user_msg)

                # Prepare assistant message
                assistant_msg = {
                    'role': 'assistant',
                    'content': response.get('message', 'Sorry, I encountered an error.')
                }

                # Attach results if tool was called
                if response.get('tool_called') and 'function_result' in response:
                    assistant_msg['results'] = response['function_result']

                st.session_state.ai_chat.append(assistant_msg)
                st.rerun()

            # Clear button in sidebar
            if st.button("🔄 New Conversation", key="ai_clear"):
                st.session_state.ai_chat = []
                st.session_state.ai_agent.conversation_history = []
                st.rerun()

    # Tab 3: Deals
    with tab3:
        st.header("Flight Deals")
        st.markdown("Find the best fares by filtering on your preferences")

        # Filters - Multiple rows for better organization
        st.subheader("Your Preferences")

        # Row 1: Basic filters
        filter_row1_col1, filter_row1_col2, filter_row1_col3 = st.columns(3)

        with filter_row1_col1:
            # Departure city filter
            if enriched and 'origin_city' in filtered_df.columns:
                origin_options = sorted(filtered_df['origin_city'].unique())
                selected_departure = st.selectbox(
                    "📍 Departure City",
                    options=['All'] + origin_options,
                    key="deals_departure"
                )
            else:
                origin_options = sorted(filtered_df['origin'].unique())
                selected_departure = st.selectbox(
                    "📍 Departure Airport",
                    options=['All'] + origin_options,
                    key="deals_departure"
                )

        with filter_row1_col2:
            # Cabin class filter
            selected_cabin = st.selectbox(
                "🪑 Cabin Class",
                options=['All', 'Economy', 'Business'],
                key="deals_cabin"
            )

        with filter_row1_col3:
            # Number of stops filter
            selected_stops = st.selectbox(
                "🛬 Flight Stops",
                options=['All', 'Direct only', '1 stop max', '2+ stops OK'],
                key="deals_stops"
            )

        # Row 2: Advanced filters
        filter_row2_col1, filter_row2_col2, filter_row2_col3 = st.columns(3)

        with filter_row2_col1:
            # Price range
            max_price = st.number_input(
                "💰 Max Price per Person",
                min_value=0,
                max_value=20000,
                value=10000,
                step=500,
                key="deals_max_price"
            )

        with filter_row2_col2:
            # Sort by
            sort_by = st.selectbox(
                "📊 Sort By",
                options=['Lowest Price', 'Best Value ($/mile)', 'Shortest Duration', 'Fewest Stops'],
                key="deals_sort"
            )

        with filter_row2_col3:
            # Travel period
            travel_period = st.selectbox(
                "📅 Travel Period",
                options=['All Months', 'Next 3 Months', 'Next 6 Months', 'After 6 Months'],
                key="deals_period"
            )

        # Apply filters
        deals_df = filtered_df.copy()

        # Departure filter
        if selected_departure != 'All':
            if enriched and 'origin_city' in deals_df.columns:
                deals_df = deals_df[deals_df['origin_city'] == selected_departure]
            else:
                deals_df = deals_df[deals_df['origin'] == selected_departure]

        # Cabin class filter
        if selected_cabin != 'All':
            deals_df = deals_df[deals_df['cabin_class'] == selected_cabin.lower()]

        # Price filter
        deals_df = deals_df[deals_df['price_avg'] <= max_price]

        # Stops filter
        if selected_stops != 'All':
            deals_df = deals_df[deals_df['sample_flight'].notna()]
            if selected_stops == 'Direct only':
                deals_df = deals_df[deals_df['sample_flight'].apply(
                    lambda x: x.get('stops', 99) == 0 if isinstance(x, dict) else False
                )]
            elif selected_stops == '1 stop max':
                deals_df = deals_df[deals_df['sample_flight'].apply(
                    lambda x: x.get('stops', 99) <= 1 if isinstance(x, dict) else False
                )]

        # Travel period filter
        if travel_period != 'All Months':
            today = pd.Timestamp.now()
            if travel_period == 'Next 3 Months':
                deals_df = deals_df[deals_df['travel_date'] <= today + pd.Timedelta(days=90)]
            elif travel_period == 'Next 6 Months':
                deals_df = deals_df[deals_df['travel_date'] <= today + pd.Timedelta(days=180)]
            elif travel_period == 'After 6 Months':
                deals_df = deals_df[deals_df['travel_date'] > today + pd.Timedelta(days=180)]

        # Apply sorting
        if sort_by == 'Lowest Price':
            deals_df = deals_df.sort_values('price_avg')
        elif sort_by == 'Best Value ($/mile)' and 'price_per_mile' in deals_df.columns:
            deals_df = deals_df.sort_values('price_per_mile')
        elif sort_by == 'Shortest Duration':
            # Extract duration in minutes for sorting
            deals_df = deals_df[deals_df['sample_flight'].notna()]
            def parse_duration(flight_info):
                if isinstance(flight_info, dict) and 'duration' in flight_info:
                    duration_str = flight_info['duration']
                    # Parse "12 hr 15 min" format
                    hours = 0
                    minutes = 0
                    if 'hr' in duration_str:
                        hours = int(duration_str.split('hr')[0].strip())
                    if 'min' in duration_str:
                        min_part = duration_str.split('hr')[-1] if 'hr' in duration_str else duration_str
                        minutes = int(min_part.replace('min', '').strip())
                    return hours * 60 + minutes
                return 9999
            deals_df['duration_minutes'] = deals_df['sample_flight'].apply(parse_duration)
            deals_df = deals_df.sort_values('duration_minutes')
        elif sort_by == 'Fewest Stops':
            deals_df = deals_df[deals_df['sample_flight'].notna()]
            deals_df['stops_count'] = deals_df['sample_flight'].apply(
                lambda x: x.get('stops', 99) if isinstance(x, dict) else 99
            )
            deals_df = deals_df.sort_values('stops_count')

        st.markdown("---")

        # Show filter results summary
        if len(deals_df) == 0:
            st.warning("😔 No flights match your criteria. Try adjusting the filters.")
        else:
            st.success(f"✓ Found {len(deals_df)} flights matching your preferences")

        # Region selector (only if we have results)
        if len(deals_df) > 0:
            st.subheader("Select Your Destination Region")

        region_cols = st.columns(4)
        regions = []

        if enriched and 'dest_region' in deals_df.columns:
            regions = sorted(deals_df['dest_region'].unique())

        if regions:
            # Region icons mapping
            region_icons = {
                'Europe': '🇪🇺',
                'North America': '🇺🇸',
                'South America': '🦜',
                'Asia': '🏯',
                'Africa': '🦁',
                'Middle East': '🕌',
                'Oceania': '🐧',
                'Other': '🌍'
            }

            selected_regions = []
            for i, region in enumerate(regions):
                col_idx = i % 4
                with region_cols[col_idx]:
                    icon = region_icons.get(region, '🌍')
                    # Default first region to True
                    if st.checkbox(f"{icon} {region}", value=(len(selected_regions)==0 and i==0), key=f"region_{region}"):
                        selected_regions.append(region)

            # Ensure at least one region is selected
            if not selected_regions and regions:
                selected_regions = [regions[0]]

            if selected_regions:
                st.markdown("---")

                # Filter by selected regions
                region_df = deals_df[deals_df['dest_region'].isin(selected_regions)]

                # Show deals for each cabin class
                for cabin in ['economy', 'business']:
                    if cabin not in region_df['cabin_class'].unique():
                        continue

                    cabin_df = region_df[region_df['cabin_class'] == cabin].copy()

                    if len(cabin_df) == 0:
                        continue

                    # Get top deals by value score
                    cabin_df['value_score'] = ((cabin_df['price_avg'].max() - cabin_df['price_avg']) / cabin_df['price_avg'].max() * 100)
                    top_deals = cabin_df.nlargest(15, 'value_score')

                    st.subheader(f"{'💼 Business Class' if cabin == 'business' else '✈️ Economy Class'} Fares")
                    st.caption(f"Showing top {len(top_deals)} deals to {', '.join(selected_regions)}")

                    # Group by destination for cleaner display
                    deal_groups = {}
                    for _, deal in top_deals.iterrows():
                        dest_key = deal.get('dest_city', deal['destination'])
                        if dest_key not in deal_groups or deal['price_avg'] < deal_groups[dest_key]['price_avg']:
                            deal_groups[dest_key] = deal

                    # Display in cards
                    for dest, deal in sorted(deal_groups.items(), key=lambda x: x[1]['price_avg'])[:10]:
                        with st.container():
                                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

                                with col1:
                                    dest_display = deal['dest_city'] if deal.get('dest_city') else deal['destination']
                                    country = deal.get('dest_country', '')
                                    if country:
                                        st.markdown(f"### {dest_display}, {country}")
                                    else:
                                        st.markdown(f"### {dest_display}")

                                    # Show airlines
                                    if deal['airlines'] and len(deal['airlines']) > 0:
                                        airlines_list = [a.strip() for a in deal['airlines'][0].split(',')]
                                        airlines_display = ', '.join(airlines_list[:2])
                                        if len(airlines_list) > 2:
                                            airlines_display += f" +{len(airlines_list)-2} more"
                                        st.caption(f"✈️ {airlines_display}")

                                with col2:
                                    st.metric("From", f"${deal['price_avg']:.0f}")
                                    st.caption(f"Range: ${deal['price_min']:.0f}-${deal['price_max']:.0f}")

                                with col3:
                                    if enriched and 'distance_miles' in deal:
                                        st.metric("Distance", f"{deal['distance_miles']:,} mi")
                                        st.caption(f"${deal.get('price_per_mile', 0):.3f}/mile")

                                with col4:
                                    # Flight info from sample
                                    if deal.get('sample_flight') and isinstance(deal['sample_flight'], dict):
                                        flight_info = deal['sample_flight']
                                        if 'duration' in flight_info:
                                            st.metric("Duration", flight_info['duration'])
                                        if 'stops' in flight_info:
                                            stops = flight_info['stops']
                                            if stops == 0:
                                                st.caption("✓ Direct flight")
                                            else:
                                                st.caption(f"🛬 {stops} stop{'s' if stops > 1 else ''}")
                                    else:
                                        st.metric("Travel", deal['travel_date'].strftime('%b %Y'))
                                        booking_status = "⚡ Book Now" if deal['days_ahead'] < 30 else "✓ Available"
                                        st.caption(booking_status)

                                # Show specific travel date
                                travel_info_cols = st.columns(2)
                                with travel_info_cols[0]:
                                    st.caption(f"📅 **Travel:** {deal['travel_date'].strftime('%b %d, %Y')}")
                                with travel_info_cols[1]:
                                    book_by_date = deal['travel_date'] - pd.Timedelta(days=deal['days_ahead'])
                                    st.caption(f"⏰ **Book by:** {book_by_date.strftime('%b %d, %Y')}")

                                # Additional details
                                details_cols = st.columns(3)
                                with details_cols[0]:
                                    if enriched and 'timezone_diff' in deal:
                                        tz_diff = abs(deal['timezone_diff'])
                                        if tz_diff <= 2:
                                            st.caption("😊 Minimal jet lag")
                                        elif tz_diff <= 5:
                                            st.caption("😐 Moderate jet lag")
                                        else:
                                            st.caption(f"😫 {tz_diff}hr time difference")

                                with details_cols[1]:
                                    if 'origin_city' in deal:
                                        st.caption(f"📍 From {deal['origin_city']}")

                                with details_cols[2]:
                                    st.caption(f"🎫 {deal['price_level'].title()} fare")

                                # Flight Details expander
                                if 'sample_flight' in deal and deal['sample_flight']:
                                    with st.expander("✈️ View Flight Details"):
                                        flight_info = deal['sample_flight']

                                        fd_col1, fd_col2, fd_col3 = st.columns(3)

                                        with fd_col1:
                                            if isinstance(flight_info, dict) and 'duration' in flight_info:
                                                st.metric("⏱️ Duration", flight_info['duration'])

                                        with fd_col2:
                                            if isinstance(flight_info, dict) and 'stops' in flight_info:
                                                stops = flight_info['stops']
                                                if stops == 0:
                                                    st.metric("🛬 Stops", "Direct ✓")
                                                else:
                                                    st.metric("🛬 Stops", stops)

                                        with fd_col3:
                                            if isinstance(flight_info, dict) and 'airline' in flight_info:
                                                st.caption("Sample Route")
                                                st.caption(f"✈️ {flight_info['airline']}")

                                        # Stopover info if applicable
                                        if isinstance(flight_info, dict) and flight_info.get('stops', 0) > 0:
                                            st.markdown("**🌍 Possible Stopovers:**")
                                            common_hubs = {
                                                'Qatar': 'Doha', 'Emirates': 'Dubai', 'Etihad': 'Abu Dhabi',
                                                'Turkish': 'Istanbul', 'Singapore': 'Singapore', 'Cathay': 'Hong Kong',
                                                'ANA': 'Tokyo', 'Lufthansa': 'Frankfurt/Munich', 'Air France': 'Paris',
                                                'KLM': 'Amsterdam', 'British Airways': 'London'
                                            }

                                            airlines_str = ', '.join(deal['airlines'][:3]) if deal['airlines'] else ''
                                            hubs = [hub for airline, hub in common_hubs.items() if airline.lower() in airlines_str.lower()]
                                            if hubs:
                                                st.caption(', '.join(hubs[:2]))

                                st.markdown("---")

                st.markdown("")
        else:
            st.info("Region data not available. Showing all destinations...")

            # Fallback: show best deals without regional grouping
            for cabin in ['economy', 'business']:
                cabin_df = deals_df[deals_df['cabin_class'] == cabin].copy()
                if len(cabin_df) == 0:
                    continue

                st.subheader(f"{'💼 Business Class' if cabin == 'business' else '✈️ Economy Class'} - Best Deals")

                top_deals = cabin_df.nsmallest(10, 'price_avg')

                for idx, deal in top_deals.iterrows():
                    col1, col2, col3 = st.columns([3, 2, 2])

                    with col1:
                        st.markdown(f"**{deal['destination']}**")
                        if deal['airlines']:
                            st.caption(f"✈️ {deal['airlines'][0][:50]}")

                    with col2:
                        st.metric("Price", f"${deal['price_avg']:.0f}")

                    with col3:
                        st.metric("Travel", deal['travel_date'].strftime('%b %Y'))

                    st.markdown("---")

    # Tab 3: Insights & Value (only if enriched data available)
    if enriched:
        with tab3:
            st.header("💎 Insights & Value Analysis")
            st.markdown("Discover the best deals, hidden gems, and data-driven insights")

            # Key metrics overview
            st.subheader("📊 Overall Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                avg_distance = filtered_df['distance_miles'].mean() if 'distance_miles' in filtered_df.columns else 0
                st.metric("Avg Distance", f"{avg_distance:,.0f} mi")

            with col2:
                avg_price_per_mile = filtered_df['price_per_mile'].mean() if 'price_per_mile' in filtered_df.columns else 0
                st.metric("Avg Price/Mile", f"${avg_price_per_mile:.2f}")

            with col3:
                num_regions = filtered_df['dest_region'].nunique() if 'dest_region' in filtered_df.columns else 0
                st.metric("Regions Covered", num_regions)

            with col4:
                num_countries = filtered_df['dest_country'].nunique() if 'dest_country' in filtered_df.columns else 0
                st.metric("Countries", num_countries)

            # Best Value Rankings
            st.subheader("🏆 Best Value Flights (Price per Mile)")

            if 'price_per_mile' in filtered_df.columns:
                value_df = filtered_df.nsmallest(20, 'price_per_mile')[
                    ['origin_city', 'dest_city', 'dest_country', 'distance_miles',
                     'price_avg', 'price_per_mile', 'cabin_class', 'travel_date', 'days_ahead', 'airlines']
                ].copy()

                col1, col2 = st.columns([2, 1])

                with col1:
                    # Interactive chart
                    fig = px.scatter(
                        value_df,
                        x='distance_miles',
                        y='price_avg',
                        size='price_per_mile',
                        color='price_per_mile',
                        hover_data=['origin_city', 'dest_city', 'cabin_class'],
                        title='Price vs Distance (Size = Price per Mile)',
                        labels={'distance_miles': 'Distance (miles)', 'price_avg': 'Average Price ($)'},
                        color_continuous_scale='RdYlGn_r'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.markdown("**Top 10 Best Deals**")
                    for idx, row in value_df.head(10).iterrows():
                        st.markdown(f"**{row['origin_city']} → {row['dest_city']}, {row['dest_country']}**")

                        # Extract airline names
                        airlines_display = "Various"
                        if row['airlines'] and len(row['airlines']) > 0:
                            airlines_list = [a.strip() for a in row['airlines'][0].split(',')]
                            airlines_display = ', '.join(airlines_list[:2])  # Show first 2 airlines
                            if len(airlines_list) > 2:
                                airlines_display += f" +{len(airlines_list)-2} more"

                        st.write(f"${row['price_avg']:.0f} | {row['distance_miles']:,} mi | {row['cabin_class'].title()}")
                        st.write(f"{row['travel_date'].strftime('%b %d, %Y')} | Book in {row['days_ahead']} days")
                        st.write(f"Airlines: {airlines_display}")
                        st.write(f"Value: ${row['price_per_mile']:.3f}/mile")
                        st.divider()

            # Distance Analysis
            st.subheader("📏 Distance Distribution")

            if 'distance_miles' in filtered_df.columns:
                col1, col2 = st.columns(2)

                with col1:
                    # Distance categories
                    def categorize_distance(miles):
                        if miles < 1000: return "Short-haul (<1000 mi)"
                        elif miles < 3000: return "Medium-haul (1000-3000 mi)"
                        elif miles < 6000: return "Long-haul (3000-6000 mi)"
                        else: return "Ultra long-haul (>6000 mi)"

                    filtered_df['distance_category'] = filtered_df['distance_miles'].apply(categorize_distance)
                    dist_counts = filtered_df['distance_category'].value_counts()

                    fig = px.pie(
                        values=dist_counts.values,
                        names=dist_counts.index,
                        title='Flight Distance Categories'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Average price by distance
                    dist_price = filtered_df.groupby('distance_category')['price_avg'].mean().sort_values()

                    fig = px.bar(
                        x=dist_price.values,
                        y=dist_price.index,
                        orientation='h',
                        title='Average Price by Distance Category',
                        labels={'x': 'Average Price ($)', 'y': 'Category'},
                        color=dist_price.values,
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Regional Analysis
            st.subheader("🌍 Regional Insights")

            if 'dest_region' in filtered_df.columns:
                col1, col2 = st.columns(2)

                with col1:
                    regional_stats = filtered_df.groupby('dest_region').agg({
                        'price_avg': 'mean',
                        'destination': 'count'
                    }).round(0)
                    regional_stats.columns = ['Avg Price ($)', 'Routes']
                    regional_stats = regional_stats.sort_values('Avg Price ($)')

                    fig = px.bar(
                        regional_stats,
                        x=regional_stats.index,
                        y='Avg Price ($)',
                        title='Average Price by Region',
                        color='Avg Price ($)',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.markdown("**Regional Summary**")
                    for region, data in regional_stats.iterrows():
                        st.markdown(f"""
                        **{region}**
                        💰 Avg: ${data['Avg Price ($)']:.0f} | ✈️ {int(data['Routes'])} routes
                        """)

            # Timezone Analysis
            st.subheader("🕐 Jet Lag Indicator")

            if 'timezone_diff' in filtered_df.columns:
                col1, col2 = st.columns(2)

                with col1:
                    tz_dist = filtered_df['timezone_diff'].value_counts().sort_index()

                    fig = px.bar(
                        x=tz_dist.index,
                        y=tz_dist.values,
                        title='Timezone Differences (hours)',
                        labels={'x': 'Time Difference (hours)', 'y': 'Number of Routes'},
                        color=abs(tz_dist.index),
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.markdown("**🌙 Jet Lag Guide**")

                    # Categorize by jet lag severity
                    def jet_lag_level(tz_diff):
                        abs_diff = abs(tz_diff)
                        if abs_diff <= 2: return "😊 Minimal"
                        elif abs_diff <= 5: return "😐 Moderate"
                        elif abs_diff <= 8: return "😫 Significant"
                        else: return "🥱 Severe"

                    filtered_df['jet_lag'] = filtered_df['timezone_diff'].apply(jet_lag_level)
                    jet_lag_counts = filtered_df['jet_lag'].value_counts()

                    for level, count in jet_lag_counts.items():
                        st.markdown(f"{level}: {count} routes")

                    st.info("💡 Tip: Flights with <3 hour time difference cause minimal jet lag")

            # Interactive Map (if plotly express supports it)
            st.subheader("🗺️ Route Network Visualization")

            if 'origin_city' in filtered_df.columns and 'dest_city' in filtered_df.columns:
                # Sample top routes for visualization
                map_df = filtered_df.nsmallest(50, 'price_avg')[
                    ['origin_city', 'dest_city', 'price_avg', 'distance_miles', 'cabin_class']
                ].copy()

                st.info(f"Showing top 50 cheapest routes (out of {len(filtered_df)} filtered routes)")

                # Display as a table
                st.dataframe(
                    map_df,
                    use_container_width=True,
                    hide_index=True
                )

            # Seasonal Trends & Travel Agent Insights
            st.subheader("📅 Seasonal Pricing Trends")

            # Add month column
            filtered_df_seasonal = filtered_df.copy()
            filtered_df_seasonal['month'] = filtered_df_seasonal['travel_date'].dt.month
            filtered_df_seasonal['month_name'] = filtered_df_seasonal['travel_date'].dt.strftime('%B')

            col1, col2 = st.columns(2)

            with col1:
                # Average price by month
                monthly_avg = filtered_df_seasonal.groupby('month_name').agg({
                    'price_avg': 'mean',
                    'destination': 'count'
                }).round(0)

                # Sort by month order
                month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']
                monthly_avg = monthly_avg.reindex([m for m in month_order if m in monthly_avg.index])

                fig = px.bar(
                    monthly_avg,
                    x=monthly_avg.index,
                    y='price_avg',
                    title='Average Price by Month',
                    labels={'price_avg': 'Avg Price ($)', 'month_name': 'Month'},
                    color='price_avg',
                    color_continuous_scale='RdYlGn_r'
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Find cheapest and most expensive months
                if not monthly_avg.empty:
                    cheapest_month = monthly_avg['price_avg'].idxmin()
                    expensive_month = monthly_avg['price_avg'].idxmax()
                    cheapest_price = monthly_avg.loc[cheapest_month, 'price_avg']
                    expensive_price = monthly_avg.loc[expensive_month, 'price_avg']
                    savings = expensive_price - cheapest_price

                    st.markdown("**Seasonal Insights**")
                    st.success(f"**Best Month to Travel:** {cheapest_month}")
                    st.write(f"Average price: ${cheapest_price:.0f}")

                    st.error(f"**Most Expensive Month:** {expensive_month}")
                    st.write(f"Average price: ${expensive_price:.0f}")

                    st.info(f"**Potential Savings:** ${savings:.0f} ({savings/expensive_price*100:.0f}%)")
                    st.write(f"Traveling in {cheapest_month} instead of {expensive_month}")

            # Customer Segment Recommendations
            st.subheader("👥 Customer Segment Recommendations")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("**💰 Budget Travelers**")
                budget_flights = filtered_df.nsmallest(5, 'price_avg')[['origin_city', 'dest_city', 'price_avg', 'cabin_class']]
                for idx, row in budget_flights.iterrows():
                    st.write(f"{row['origin_city']} → {row['dest_city']}")
                    st.caption(f"${row['price_avg']:.0f} ({row['cabin_class']})")

            with col2:
                st.markdown("**✈️ Business Travelers**")
                # Business class or direct flights
                business_flights = filtered_df[filtered_df['cabin_class'] == 'business'].nsmallest(5, 'price_avg')[
                    ['origin_city', 'dest_city', 'price_avg', 'cabin_class']
                ]
                if not business_flights.empty:
                    for idx, row in business_flights.iterrows():
                        st.write(f"{row['origin_city']} → {row['dest_city']}")
                        st.caption(f"${row['price_avg']:.0f} (Business)")
                else:
                    st.caption("No business class in filtered results")

            with col3:
                st.markdown("**👨‍👩‍👧‍👦 Families**")
                # Economy class, popular family destinations
                family_flights = filtered_df[filtered_df['cabin_class'] == 'economy'].nsmallest(5, 'price_avg')[
                    ['origin_city', 'dest_city', 'price_avg']
                ]
                for idx, row in family_flights.iterrows():
                    st.write(f"{row['origin_city']} → {row['dest_city']}")
                    family_total = row['price_avg'] * 4  # Family of 4
                    st.caption(f"${row['price_avg']:.0f}/person (${family_total:.0f} for 4)")

            with col4:
                st.markdown("**💎 Luxury Travelers**")
                # Best value business class
                luxury_flights = filtered_df[filtered_df['cabin_class'] == 'business'].nsmallest(5, 'price_per_mile')[
                    ['origin_city', 'dest_city', 'price_avg', 'price_per_mile']
                ] if 'price_per_mile' in filtered_df.columns and len(filtered_df[filtered_df['cabin_class'] == 'business']) > 0 else pd.DataFrame()

                if not luxury_flights.empty:
                    for idx, row in luxury_flights.iterrows():
                        st.write(f"{row['origin_city']} → {row['dest_city']}")
                        st.caption(f"${row['price_avg']:.0f} (${row['price_per_mile']:.3f}/mi)")
                else:
                    st.caption("No business class in filtered results")

    # Tab 3: Price Analysis
    price_tab = tab4 if enriched else tab3
    with price_tab:
        st.header("Price Analysis")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Min Price", f"${filtered_df['price_min'].mean():.0f}")
        with col2:
            st.metric("Avg Max Price", f"${filtered_df['price_max'].mean():.0f}")
        with col3:
            st.metric("Cheapest Flight", f"${filtered_df['price_min'].min():.0f}")
        with col4:
            st.metric("Most Expensive", f"${filtered_df['price_max'].max():.0f}")

        # Price distribution by cabin class
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Price Distribution by Cabin Class")
            fig = px.box(
                filtered_df,
                x='cabin_class',
                y='price_avg',
                color='cabin_class',
                title='Average Price Distribution'
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Price Level Distribution")
            price_level_counts = filtered_df['price_level'].value_counts()
            fig = px.pie(
                values=price_level_counts.values,
                names=price_level_counts.index,
                title='Price Levels'
            )
            st.plotly_chart(fig, use_container_width=True)

        # Price range analysis
        st.subheader("Price Range Analysis (Min to Max)")
        top_routes = filtered_df.nlargest(20, 'price_max')[['origin', 'destination', 'cabin_class', 'price_min', 'price_avg', 'price_max']].copy()
        top_routes['route'] = top_routes['origin'] + ' → ' + top_routes['destination'] + ' (' + top_routes['cabin_class'] + ')'

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Min Price',
            x=top_routes['route'],
            y=top_routes['price_min'],
            marker_color='lightblue'
        ))
        fig.add_trace(go.Bar(
            name='Avg Price',
            x=top_routes['route'],
            y=top_routes['price_avg'],
            marker_color='blue'
        ))
        fig.add_trace(go.Bar(
            name='Max Price',
            x=top_routes['route'],
            y=top_routes['price_max'],
            marker_color='darkblue'
        ))

        fig.update_layout(
            title='Top 20 Most Expensive Routes',
            xaxis_tickangle=-45,
            barmode='group',
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

    # Tab 4: Route Explorer
    route_tab = tab5 if enriched else tab4
    with route_tab:
        st.header("Route Explorer")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top Origins by Route Count")
            # Use city names if available in enriched data
            if 'origin_city' in filtered_df.columns and 'origin_country' in filtered_df.columns:
                filtered_df['origin_display'] = filtered_df['origin_city'] + ', ' + filtered_df['origin_country']
                origin_counts = filtered_df['origin_display'].value_counts().head(15)
            else:
                origin_counts = filtered_df['origin'].value_counts().head(15)

            fig = px.bar(
                x=origin_counts.values,
                y=origin_counts.index,
                orientation='h',
                labels={'x': 'Number of Routes', 'y': 'Origin'},
                title='Most Popular Origin Cities'
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Top Destinations by Route Count")
            # Use city names if available in enriched data
            if 'dest_city' in filtered_df.columns and 'dest_country' in filtered_df.columns:
                filtered_df['dest_display_full'] = filtered_df['dest_city'] + ', ' + filtered_df['dest_country']
                dest_counts = filtered_df['dest_display_full'].value_counts().head(15)
            else:
                dest_counts = filtered_df['destination'].value_counts().head(15)

            fig = px.bar(
                x=dest_counts.values,
                y=dest_counts.index,
                orientation='h',
                labels={'x': 'Number of Routes', 'y': 'Destination'},
                title='Most Popular Destinations'
            )
            st.plotly_chart(fig, use_container_width=True)

        # Route-specific analysis
        st.subheader("Specific Route Analysis")
        col1, col2 = st.columns(2)

        with col1:
            selected_origin = st.selectbox(
                "Select Origin",
                options=['All'] + sorted(filtered_df['origin'].unique().tolist())
            )

        with col2:
            if selected_origin != 'All':
                dest_options = sorted(filtered_df[filtered_df['origin'] == selected_origin]['destination'].unique().tolist())
            else:
                dest_options = sorted(filtered_df['destination'].unique().tolist())

            selected_dest = st.selectbox(
                "Select Destination",
                options=['All'] + dest_options
            )

        if selected_origin != 'All' and selected_dest != 'All':
            route_data = filtered_df[
                (filtered_df['origin'] == selected_origin) &
                (filtered_df['destination'] == selected_dest)
            ]

            if not route_data.empty:
                st.subheader(f"Route: {selected_origin} → {selected_dest}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Available Options", len(route_data))
                with col2:
                    st.metric("Cheapest Price", f"${route_data['price_min'].min():.0f}")
                with col3:
                    st.metric("Avg Price", f"${route_data['price_avg'].mean():.0f}")

                # Show the cheapest option details
                cheapest_option = route_data.nsmallest(1, 'price_min').iloc[0]
                st.info(f"""
                **💰 Cheapest Option Details:**
                - **Price:** ${cheapest_option['price_min']:.0f} - ${cheapest_option['price_max']:.0f} (Avg: ${cheapest_option['price_avg']:.0f})
                - **Cabin Class:** {cheapest_option['cabin_class'].title()}
                - **Travel Date:** {cheapest_option['travel_date'].strftime('%Y-%m-%d')}
                - **Book in Advance:** {cheapest_option['days_ahead']} days
                - **Airlines:** {', '.join([a.strip() for a in cheapest_option['airlines'][0].split(',')]) if cheapest_option['airlines'] else 'N/A'}
                - **Price Level:** {cheapest_option['price_level'].title()}
                """)

                # Show all options in a table
                st.subheader("All Available Options")
                display_route_data = route_data.copy()
                display_route_data['airlines_display'] = display_route_data['airlines'].apply(
                    lambda x: ', '.join([a.strip() for a in x[0].split(',')][:2]) if x else 'N/A'
                )
                display_route_data = display_route_data[[
                    'cabin_class', 'airlines_display', 'travel_date', 'days_ahead',
                    'price_min', 'price_avg', 'price_max', 'price_level'
                ]]
                display_route_data.columns = [
                    'Cabin Class', 'Airlines', 'Travel Date', 'Days Ahead',
                    'Min Price', 'Avg Price', 'Max Price', 'Price Level'
                ]
                display_route_data = display_route_data.sort_values('Min Price')
                st.dataframe(display_route_data, use_container_width=True, hide_index=True)

                # Price comparison by cabin class and booking time
                fig = px.bar(
                    route_data,
                    x='days_ahead',
                    y='price_avg',
                    color='cabin_class',
                    barmode='group',
                    title='Price by Booking Time and Cabin Class',
                    labels={'days_ahead': 'Days in Advance', 'price_avg': 'Average Price ($)'}
                )
                st.plotly_chart(fig, use_container_width=True)

    # Tab 5: Airlines
    airlines_tab = tab6 if enriched else tab5
    with airlines_tab:
        st.header("Airlines Analysis")

        # Extract all airlines
        all_airlines = []
        for airlines_list in filtered_df['airlines']:
            if airlines_list:
                for airline in airlines_list:
                    all_airlines.extend([a.strip() for a in airline.split(',')])

        airline_counts = pd.Series(all_airlines).value_counts().head(20)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top 20 Airlines by Route Count")
            fig = px.bar(
                x=airline_counts.values,
                y=airline_counts.index,
                orientation='h',
                labels={'x': 'Number of Routes', 'y': 'Airline'},
                title='Most Common Airlines'
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Sample Flight Details")
            # Extract sample flight info
            sample_flights = filtered_df[filtered_df['sample_flight'].notna()].copy()
            if not sample_flights.empty:
                sample_flights['sample_airline'] = sample_flights['sample_flight'].apply(lambda x: x.get('airline', 'N/A') if isinstance(x, dict) else 'N/A')
                sample_flights['sample_stops'] = sample_flights['sample_flight'].apply(lambda x: x.get('stops', 'N/A') if isinstance(x, dict) else 'N/A')

                stops_dist = sample_flights['sample_stops'].value_counts()
                fig = px.pie(
                    values=stops_dist.values,
                    names=stops_dist.index,
                    title='Distribution of Stops'
                )
                st.plotly_chart(fig, use_container_width=True)

    # Tab 6: Booking Timing
    booking_tab = tab7 if enriched else tab6
    with booking_tab:
        st.header("Booking Timing Analysis")

        st.subheader("Price Trends by Booking Time")

        # Average prices by days ahead
        timing_analysis = filtered_df.groupby(['days_ahead', 'cabin_class']).agg({
            'price_min': 'mean',
            'price_avg': 'mean',
            'price_max': 'mean'
        }).reset_index()

        fig = px.line(
            timing_analysis,
            x='days_ahead',
            y='price_avg',
            color='cabin_class',
            title='Average Price by Days in Advance',
            labels={'days_ahead': 'Days in Advance', 'price_avg': 'Average Price ($)'},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Economy Class Pricing")
            economy_data = timing_analysis[timing_analysis['cabin_class'] == 'economy']
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=economy_data['days_ahead'], y=economy_data['price_min'],
                                    mode='lines+markers', name='Min Price', line=dict(color='lightgreen')))
            fig.add_trace(go.Scatter(x=economy_data['days_ahead'], y=economy_data['price_avg'],
                                    mode='lines+markers', name='Avg Price', line=dict(color='green')))
            fig.add_trace(go.Scatter(x=economy_data['days_ahead'], y=economy_data['price_max'],
                                    mode='lines+markers', name='Max Price', line=dict(color='darkgreen')))
            fig.update_layout(title='Economy Price Range by Booking Time',
                            xaxis_title='Days in Advance', yaxis_title='Price ($)')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Business Class Pricing")
            business_data = timing_analysis[timing_analysis['cabin_class'] == 'business']
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=business_data['days_ahead'], y=business_data['price_min'],
                                    mode='lines+markers', name='Min Price', line=dict(color='lightblue')))
            fig.add_trace(go.Scatter(x=business_data['days_ahead'], y=business_data['price_avg'],
                                    mode='lines+markers', name='Avg Price', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=business_data['days_ahead'], y=business_data['price_max'],
                                    mode='lines+markers', name='Max Price', line=dict(color='darkblue')))
            fig.update_layout(title='Business Price Range by Booking Time',
                            xaxis_title='Days in Advance', yaxis_title='Price ($)')
            st.plotly_chart(fig, use_container_width=True)

        # Best time to book analysis
        st.subheader("💡 Best Time to Book Insights")
        best_time = filtered_df.groupby('days_ahead')['price_avg'].mean().idxmin()
        worst_time = filtered_df.groupby('days_ahead')['price_avg'].mean().idxmax()

        col1, col2 = st.columns(2)
        with col1:
            st.success(f"**Best Booking Time:** {best_time} days in advance")
            st.info(f"Average Price: ${filtered_df[filtered_df['days_ahead'] == best_time]['price_avg'].mean():.0f}")
        with col2:
            st.warning(f"**Most Expensive Booking Time:** {worst_time} days in advance")
            st.info(f"Average Price: ${filtered_df[filtered_df['days_ahead'] == worst_time]['price_avg'].mean():.0f}")

    # Tab 7: Data Table
    data_tab = tab8 if enriched else tab7
    with data_tab:
        st.header("Raw Data Explorer")

        # Display options
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox(
                "Sort by",
                options=['price_min', 'price_avg', 'price_max', 'travel_date', 'days_ahead']
            )
        with col2:
            sort_order = st.radio("Sort order", ['Ascending', 'Descending'])

        # Prepare display dataframe
        display_df = filtered_df[[
            'origin', 'destination', 'cabin_class', 'travel_date',
            'days_ahead', 'price_min', 'price_avg', 'price_max',
            'price_level'
        ]].copy()

        display_df = display_df.sort_values(
            by=sort_by,
            ascending=(sort_order == 'Ascending')
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            height=600
        )

        # Download button
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name="filtered_flight_data.csv",
            mime="text/csv"
        )

    # Footer
    st.markdown("---")
    st.markdown("**Last Updated:** " + metadata['scraped_at'])

except FileNotFoundError:
    st.error("❌ Error: flight_prices_worldwide.json not found in the current directory")
    st.info("Please make sure the file is in the same directory as this script.")
except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.exception(e)
