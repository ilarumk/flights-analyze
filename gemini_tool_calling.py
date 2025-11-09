"""
Gemini Tool Calling Agent
Uses Gemini's function calling to directly interact with flight data
"""
import json
import requests
import os
import pandas as pd

# Get API key
try:
    import streamlit as st
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
except:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


# Define tools (functions) that Gemini can call
FLIGHT_SEARCH_TOOL = {
    "name": "search_flights",
    "description": "Search for flights based on user preferences. Returns matching flight routes with prices, airlines, and details.",
    "parameters": {
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "description": "Origin airport code (e.g., 'SYD', 'JFK') or city name (e.g., 'Sydney', 'New York')"
            },
            "budget_per_person": {
                "type": "number",
                "description": "Maximum budget per person in USD"
            },
            "adults": {
                "type": "integer",
                "description": "Number of adult travelers",
                "default": 1
            },
            "children": {
                "type": "integer",
                "description": "Number of children",
                "default": 0
            },
            "cabin_class": {
                "type": "string",
                "enum": ["economy", "business", "first"],
                "description": "Cabin class preference",
                "default": "economy"
            },
            "trip_type": {
                "type": "string",
                "description": "Type of trip: beach, ski, culture, food, adventure, shopping, nature, romance, honeymoon, luxury"
            },
            "origin_season": {
                "type": "string",
                "enum": ["Summer ☀️", "Winter ❄️", "Spring 🌸", "Fall 🍂"],
                "description": "Season when traveling from home"
            },
            "dest_season": {
                "type": "string",
                "enum": ["Summer ☀️", "Winter ❄️", "Spring 🌸", "Fall 🍂"],
                "description": "Desired season/weather at destination"
            },
            "stops": {
                "type": "string",
                "enum": ["All", "Direct only", "1 stop max", "2+ stops OK"],
                "description": "Flight stops preference",
                "default": "All"
            }
        },
        "required": ["origin", "budget_per_person"]
    }
}


class GeminiToolCallingAgent:
    """Agent that uses Gemini function calling to search flights"""

    def __init__(self, flight_data_df, airport_to_dest=None):
        """
        Initialize with flight data

        Args:
            flight_data_df: Pandas DataFrame with flight data
            airport_to_dest: Dict mapping airport codes to destination info
        """
        self.api_key = GEMINI_API_KEY
        self.df = flight_data_df
        self.airport_to_dest = airport_to_dest or {}
        self.conversation_history = []

    def search_flights(self, **params):
        """
        Actual function to search flights - called by Gemini

        This implements the flight filtering logic
        """
        print(f"🔧 Tool called: search_flights with params: {params}")

        # Start with full dataset
        results = self.df.copy()

        # Filter by origin
        if 'origin' in params:
            origin = params['origin'].upper()
            # Try to match airport code or city name
            results = results[
                (results['origin'] == origin) |
                (results.get('origin_city', '').str.contains(params['origin'], case=False, na=False))
            ]

        # Filter by budget
        if 'budget_per_person' in params:
            results = results[results['price_avg'] <= params['budget_per_person']]

        # Filter by cabin class
        if 'cabin_class' in params:
            results = results[results['cabin_class'] == params['cabin_class']]

        # Filter by trip type
        if 'trip_type' in params and self.airport_to_dest:
            filtered_destinations = []
            for airport_code, dest_info in self.airport_to_dest.items():
                if params['trip_type'] in dest_info.get('categories', []):
                    filtered_destinations.append(airport_code)
            if filtered_destinations:
                results = results[results['destination'].isin(filtered_destinations)]

        # Sort by price
        results = results.sort_values('price_avg').head(10)

        # Format results for agent
        flight_list = []
        for _, row in results.iterrows():
            flight_list.append({
                'destination': row.get('dest_city', row['destination']),
                'country': row.get('dest_country', ''),
                'price': int(row['price_avg']),
                'cabin': row['cabin_class'],
                'airline': row.get('airlines', [''])[0] if row.get('airlines') else '',
                'travel_date': str(row.get('travel_date', ''))[:10]
            })

        return {
            'found': len(flight_list),
            'flights': flight_list[:5],  # Return top 5
            'total_travelers': params.get('adults', 1) + params.get('children', 0)
        }

    def chat(self, user_message):
        """
        Chat with user and use tool calling to search flights

        Returns:
            dict with message, tool_called, results, etc.
        """
        # Add user message to history
        self.conversation_history.append({
            'role': 'user',
            'parts': [{'text': user_message}]
        })

        # Prepare request with function calling
        payload = {
            'contents': self.conversation_history,
            'tools': [{
                'function_declarations': [FLIGHT_SEARCH_TOOL]
            }],
            'generationConfig': {
                'temperature': 0.7
            }
        }

        try:
            response = requests.post(
                GEMINI_ENDPOINT,
                headers={
                    'Content-Type': 'application/json',
                    'X-goog-api-key': self.api_key
                },
                json=payload,
                timeout=15
            )

            response.raise_for_status()
            result = response.json()

            candidate = result['candidates'][0]
            content = candidate['content']

            # Check if Gemini wants to call a function
            if 'parts' in content and len(content['parts']) > 0:
                part = content['parts'][0]

                if 'functionCall' in part:
                    # Gemini is calling the search_flights function!
                    function_call = part['functionCall']
                    function_name = function_call['name']
                    function_args = function_call['args']

                    print(f"📞 Gemini calling function: {function_name}")
                    print(f"   Arguments: {function_args}")

                    # Execute the function
                    if function_name == 'search_flights':
                        function_result = self.search_flights(**function_args)

                        # Send function result back to Gemini
                        self.conversation_history.append({
                            'role': 'model',
                            'parts': [{'functionCall': function_call}]
                        })

                        self.conversation_history.append({
                            'role': 'function',
                            'parts': [{
                                'functionResponse': {
                                    'name': function_name,
                                    'response': function_result
                                }
                            }]
                        })

                        # Get Gemini's response after seeing the results
                        second_response = requests.post(
                            GEMINI_ENDPOINT,
                            headers={
                                'Content-Type': 'application/json',
                                'X-goog-api-key': self.api_key
                            },
                            json={
                                'contents': self.conversation_history,
                                'tools': [{'function_declarations': [FLIGHT_SEARCH_TOOL]}]
                            },
                            timeout=15
                        )

                        second_response.raise_for_status()
                        second_result = second_response.json()

                        # Get the final text response
                        final_text = second_result['candidates'][0]['content']['parts'][0].get('text', '')

                        return {
                            'message': final_text,
                            'tool_called': True,
                            'function_name': function_name,
                            'function_args': function_args,
                            'function_result': function_result
                        }

                elif 'text' in part:
                    # Regular text response (no function call needed yet)
                    return {
                        'message': part['text'],
                        'tool_called': False
                    }

        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                'message': f"Sorry, I encountered an error: {str(e)}",
                'tool_called': False,
                'error': str(e)
            }

# Test
if __name__ == "__main__":
    # Create sample data
    data = {
        'origin': ['SYD', 'SYD', 'LAX'],
        'destination': ['DPS', 'BKK', 'CDG'],
        'price_avg': [300, 400, 800],
        'cabin_class': ['economy', 'economy', 'economy'],
        'dest_city': ['Denpasar', 'Bangkok', 'Paris'],
        'dest_country': ['Indonesia', 'Thailand', 'France']
    }
    df = pd.DataFrame(data)

    agent = GeminiToolCallingAgent(df)

    print("Testing Gemini Tool Calling\n")
    response = agent.chat("Find me flights from Sydney under $500")
    print(f"\n🤖 {response['message']}")
    if response['tool_called']:
        print(f"\n✅ Tool was called!")
        print(f"Results: {response['function_result']}")
