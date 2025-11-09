"""
AI Trip Planning Assistant - Conversational Flight Search
"""
import streamlit as st
import pandas as pd
import json
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="AI Trip Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Trip Planning Assistant")
st.markdown("Chat naturally about your travel plans - I'll help you find the perfect flights!")

# Load flight data
@st.cache_data
def load_flight_data():
    """Load flight data for agent to search"""
    # Get the base directory (parent of pages/)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    try:
        data_file = os.path.join(base_dir, 'flight_prices_worldwide_enriched.json')
        with open(data_file, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data['routes'])
        df['travel_date'] = pd.to_datetime(df['travel_date'])

        # Load destinations
        try:
            dest_file = os.path.join(base_dir, 'destinations_with_climate.json')
            with open(dest_file, 'r') as f:
                dest_data = json.load(f)
        except:
            dest_file = os.path.join(base_dir, 'destinations.json')
            with open(dest_file, 'r') as f:
                dest_data = json.load(f)

        airport_to_dest = {}
        for dest in dest_data['destinations']:
            for airport in dest['airports']:
                airport_to_dest[airport] = dest

        return df, airport_to_dest
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.error(f"Looking in: {base_dir}")
        return None, None

# Load data
df, airport_to_dest = load_flight_data()

if df is None:
    st.error("⚠️ Could not load flight data. Please check your data files.")
    st.stop()

# Initialize agent
if 'tool_agent' not in st.session_state:
    try:
        from gemini_tool_calling import GeminiToolCallingAgent
        st.session_state.tool_agent = GeminiToolCallingAgent(df, airport_to_dest)
        st.session_state.agent_ready = True
    except Exception as e:
        st.error(f"""
        ⚠️ **AI Assistant not available**

        {str(e)}

        **Setup required:**
        1. Add your GEMINI_API_KEY to `.streamlit/secrets.toml`
        2. See `SECRETS_SETUP.md` for instructions

        Get a free API key at: https://aistudio.google.com/app/apikey
        """)
        st.session_state.agent_ready = False

if st.session_state.get('agent_ready', False):
    # Show example queries
    with st.expander("💡 Example Questions", expanded=False):
        st.markdown("""
        **Try asking:**
        - "I want a beach vacation with my family during summer break"
        - "Find cheap flights from Sydney to Asia under $800"
        - "Looking for ski destinations from New York in December"
        - "Romantic honeymoon trip, budget $2000 per person"
        - "Direct flights to Europe for 2 adults in business class"
        """)

    # Initialize chat history
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
        # Add welcome message
        st.session_state.chat_messages.append({
            'role': 'assistant',
            'content': "👋 Hi! I'm your AI travel assistant. Tell me about your dream trip and I'll help you find the best flights!"
        })

    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

            # If this message has flight results, display them
            if 'flight_results' in msg:
                results = msg['flight_results']
                st.success(f"✈️ Found {results['found']} flights!")

                if results['flights']:
                    st.markdown("### Top Flight Options:")

                    for i, flight in enumerate(results['flights'], 1):
                        with st.container():
                            col1, col2, col3 = st.columns([3, 2, 2])

                            with col1:
                                dest_name = flight.get('destination', 'Unknown')
                                country = flight.get('country', '')
                                if country:
                                    st.markdown(f"**{i}. {dest_name}, {country}**")
                                else:
                                    st.markdown(f"**{i}. {dest_name}**")

                            with col2:
                                price = flight.get('price', 0)
                                st.metric("Price", f"${price}")

                                total = price * results.get('total_travelers', 1)
                                if results.get('total_travelers', 1) > 1:
                                    st.caption(f"Total: ${total:,}")

                            with col3:
                                cabin = flight.get('cabin', 'economy').title()
                                st.write(f"**Class:** {cabin}")

                                if flight.get('travel_date'):
                                    st.caption(f"📅 {flight['travel_date']}")

                            st.markdown("---")

    # Chat input
    user_input = st.chat_input("What kind of trip are you planning?", key="chat_input")

    if user_input:
        # Add user message
        st.session_state.chat_messages.append({
            'role': 'user',
            'content': user_input
        })

        # Get agent response
        with st.spinner("🔍 Searching flights..."):
            response = st.session_state.tool_agent.chat(user_input)

        # Prepare assistant message
        assistant_msg = {
            'role': 'assistant',
            'content': response.get('message', 'I encountered an issue. Please try again.')
        }

        # If tool was called and we have results, attach them
        if response.get('tool_called') and 'function_result' in response:
            assistant_msg['flight_results'] = response['function_result']

        st.session_state.chat_messages.append(assistant_msg)

        # Rerun to show updated chat
        st.rerun()

    # Sidebar with controls
    with st.sidebar:
        st.markdown("### Chat Controls")

        if st.button("🔄 Start New Conversation", use_container_width=True):
            st.session_state.chat_messages = []
            st.session_state.tool_agent.conversation_history = []
            st.rerun()

        st.markdown("---")
        st.markdown("### About")
        st.info("""
        This AI assistant uses **Gemini 2.0 Flash** to understand your travel preferences
        and search through real flight data.

        It can:
        ✅ Understand natural language
        ✅ Ask clarifying questions
        ✅ Search actual flight prices
        ✅ Consider trip type, seasons, budget
        """)

        # Show dataset info
        st.markdown("### Dataset")
        st.metric("Total Routes", f"{len(df):,}")
        st.metric("Origins", df['origin'].nunique())
        st.metric("Destinations", df['destination'].nunique())

else:
    st.warning("⚠️ AI Assistant is not configured. Please add your API key to continue.")
