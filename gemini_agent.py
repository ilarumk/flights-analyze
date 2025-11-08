"""
Gemini-powered Conversational Trip Planning Agent
Uses Google Gemini 2.0 Flash for natural language understanding
"""
import json
import requests
import os

# Get API key from environment or Streamlit secrets
try:
    import streamlit as st
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
except:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

SYSTEM_PROMPT = """You are a helpful travel planning assistant for a flight search application.

Your job is to extract flight search parameters from user conversations.

Required parameters (must get from user):
- origin: City or airport code where flying from (e.g., "Sydney", "SYD", "New York")
- budget: Budget per person in USD (e.g., 500, 1200, 2000)
- adults: Number of adult travelers (default: 1)

Optional parameters:
- children: Number of children (default: 0)
- cabin_class: "economy", "business", or "first" (default: "economy")
- trip_type: "beach", "ski", "culture", "food", "adventure", "shopping", "nature", "romance", "honeymoon", "luxury"
- origin_season: "Summer ☀️", "Winter ❄️", "Spring 🌸", or "Fall 🍂" (when traveling FROM home)
- dest_season: "Summer ☀️", "Winter ❄️", "Spring 🌸", or "Fall 🍂" (desired weather AT destination)
- stops: "All", "Direct only", "1 stop max", "2+ stops OK"
- school_calendar: "US/Canada: Summer Break", "US/Canada: Winter Break", "US/Canada: Spring Break", etc.

Instructions:
1. Be conversational and friendly
2. If user provides all required info, extract it and say you're ready to search
3. If missing required info, ask ONE clarifying question at a time
4. Return a JSON response with this structure:

{
  "message": "Your conversational response to the user",
  "ready_to_search": true/false,
  "extracted_params": {
    "origin": "SYD" or null,
    "budget": 1200 or null,
    "adults": 2 or null,
    "children": 0,
    "cabin_class": "economy",
    "trip_type": "beach" or null,
    ... (include all parameters, use null if not provided)
  },
  "missing_params": ["origin", "budget"] or [],
  "next_question": "What's your budget?" or null
}

Examples:

User: "I want a beach vacation with my family during summer break"
Response:
{
  "message": "A family beach vacation during summer break sounds wonderful! Where will you be flying from?",
  "ready_to_search": false,
  "extracted_params": {
    "origin": null,
    "budget": null,
    "adults": 2,
    "children": 2,
    "cabin_class": "economy",
    "trip_type": "beach",
    "origin_season": "Summer ☀️",
    "dest_season": null,
    "stops": null,
    "school_calendar": "US/Canada: Summer Break"
  },
  "missing_params": ["origin", "budget"],
  "next_question": "Where will you be flying from?"
}

User: "From Sydney to Bali, 2 adults, budget $1200 per person, economy class"
Response:
{
  "message": "Perfect! Let me find economy flights from Sydney to Bali for 2 adults within $1200 per person...",
  "ready_to_search": true,
  "extracted_params": {
    "origin": "SYD",
    "budget": 1200,
    "adults": 2,
    "children": 0,
    "cabin_class": "economy",
    "trip_type": "beach",
    "origin_season": null,
    "dest_season": null,
    "stops": null,
    "school_calendar": null
  },
  "missing_params": [],
  "next_question": null
}

IMPORTANT: ALWAYS return valid JSON. Do not include markdown code fences or any text outside the JSON object.
"""

class GeminiTripAgent:
    """Gemini-powered conversational agent for trip planning"""

    def __init__(self, api_key=GEMINI_API_KEY):
        self.api_key = api_key
        self.conversation_history = []

    def chat(self, user_message):
        """
        Send message to Gemini and get structured response

        Returns:
            dict with message, ready_to_search, extracted_params, etc.
        """
        # Build conversation context
        full_context = SYSTEM_PROMPT + "\n\nConversation history:\n"

        for msg in self.conversation_history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            full_context += f"{role}: {msg['content']}\n"

        full_context += f"\nUser: {user_message}\n\nAssistant (respond with JSON only):"

        # Call Gemini API
        try:
            response = requests.post(
                GEMINI_ENDPOINT,
                headers={
                    'Content-Type': 'application/json',
                    'X-goog-api-key': self.api_key
                },
                json={
                    'contents': [{
                        'parts': [{'text': full_context}]
                    }],
                    'generationConfig': {
                        'temperature': 0.7,
                        'maxOutputTokens': 1024
                    }
                },
                timeout=10
            )

            response.raise_for_status()
            result = response.json()

            # Extract generated text
            generated_text = result['candidates'][0]['content']['parts'][0]['text']

            # Clean up response (remove markdown code fences if present)
            generated_text = generated_text.strip()
            if generated_text.startswith('```json'):
                generated_text = generated_text[7:]
            if generated_text.startswith('```'):
                generated_text = generated_text[3:]
            if generated_text.endswith('```'):
                generated_text = generated_text[:-3]
            generated_text = generated_text.strip()

            # Parse JSON response
            agent_response = json.loads(generated_text)

            # Update conversation history
            self.conversation_history.append({'role': 'user', 'content': user_message})
            self.conversation_history.append({'role': 'assistant', 'content': agent_response['message']})

            return agent_response

        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            # Fallback response
            return {
                'message': f"I'm having trouble understanding. Could you rephrase that? (Error: {str(e)})",
                'ready_to_search': False,
                'extracted_params': {},
                'missing_params': ['origin', 'budget', 'adults'],
                'next_question': 'Where will you be flying from?'
            }

    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []


# Test the agent
if __name__ == "__main__":
    print("=== Testing Gemini Trip Planning Agent ===\n")

    agent = GeminiTripAgent()

    test_messages = [
        "I want a beach vacation with my family during summer break",
        "From Sydney",
        "Budget is around $1200 per person",
    ]

    for msg in test_messages:
        print(f"👤 User: {msg}")
        response = agent.chat(msg)

        print(f"🤖 Agent: {response['message']}")
        print(f"   Ready to search: {response['ready_to_search']}")
        print(f"   Missing params: {response['missing_params']}")
        print(f"   Extracted: {json.dumps(response['extracted_params'], indent=2)}")
        print()

        if response['ready_to_search']:
            print("✅ All parameters collected! Ready to search flights.\n")
            print("Final parameters:")
            print(json.dumps(response['extracted_params'], indent=2))
            break
