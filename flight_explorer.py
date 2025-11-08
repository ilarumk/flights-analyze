import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Flight Prices Explorer",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and preprocess flight data"""
    with open('flight_prices_worldwide.json', 'r') as f:
        data = json.load(f)

    # Extract metadata
    metadata = data['metadata']

    # Convert routes to DataFrame
    df = pd.DataFrame(data['routes'])

    # Convert dates
    df['travel_date'] = pd.to_datetime(df['travel_date'])
    df['scraped_at'] = pd.to_datetime(df['scraped_at'])

    return df, metadata

# Load data
try:
    df, metadata = load_data()

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

    st.sidebar.markdown(f"**Filtered Routes:** {len(filtered_df)}")

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Price Analysis",
        "🗺️ Route Explorer",
        "✈️ Airlines",
        "📅 Booking Timing",
        "📋 Data Table"
    ])

    # Tab 1: Price Analysis
    with tab1:
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

    # Tab 2: Route Explorer
    with tab2:
        st.header("Route Explorer")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top Origins by Route Count")
            origin_counts = filtered_df['origin'].value_counts().head(15)
            fig = px.bar(
                x=origin_counts.values,
                y=origin_counts.index,
                orientation='h',
                labels={'x': 'Number of Routes', 'y': 'Origin Airport'},
                title='Most Popular Origin Airports'
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Top Destinations by Route Count")
            dest_counts = filtered_df['destination'].value_counts().head(15)
            fig = px.bar(
                x=dest_counts.values,
                y=dest_counts.index,
                orientation='h',
                labels={'x': 'Number of Routes', 'y': 'Destination Airport'},
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

    # Tab 3: Airlines
    with tab3:
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

    # Tab 4: Booking Timing
    with tab4:
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

    # Tab 5: Data Table
    with tab5:
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
    st.markdown("**Data Source:** Google Flights (fast-flights) | **Last Updated:** " + metadata['scraped_at'])

except FileNotFoundError:
    st.error("❌ Error: flight_prices_worldwide.json not found in the current directory")
    st.info("Please make sure the file is in the same directory as this script.")
except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.exception(e)
