"""
Conversational Trip Planning Agent
Extracts user intent and asks clarifying questions before filtering flights

This is a PLACEHOLDER implementation for the agentic system.
Replace with actual LLM/agent framework later.
"""

class TripPlannerAgent:
    """
    Conversational agent that helps users plan trips by asking questions
    and extracting structured data from natural language
    """

    def __init__(self):
        self.conversation_history = []
        self.extracted_params = {
            'origin': None,
            'budget': None,
            'adults': None,
            'children': None,
            'cabin_class': None,
            'trip_type': None,
            'travel_period': None,
            'origin_season': None,
            'dest_season': None,
            'school_calendar': None,
            'stops': None
        }

    def parse_user_input(self, user_message):
        """
        Parse user message and extract trip parameters

        TODO: Replace with actual LLM/agent that:
        - Uses embeddings or NER to extract entities
        - Understands context and intent
        - Asks intelligent follow-up questions

        For now, this is a simple keyword-based parser
        """
        message_lower = user_message.lower()

        # Extract trip type (beach, ski, culture, etc.)
        trip_types = ['beach', 'ski', 'skiing', 'culture', 'food', 'adventure',
                      'shopping', 'nature', 'romance', 'honeymoon', 'luxury']
        for tt in trip_types:
            if tt in message_lower:
                self.extracted_params['trip_type'] = tt
                break

        # Extract season preferences
        if 'summer' in message_lower:
            self.extracted_params['origin_season'] = 'Summer ☀️'
        elif 'winter' in message_lower:
            self.extracted_params['origin_season'] = 'Winter ❄️'
        elif 'spring' in message_lower:
            self.extracted_params['origin_season'] = 'Spring 🌸'
        elif 'fall' in message_lower or 'autumn' in message_lower:
            self.extracted_params['origin_season'] = 'Fall 🍂'

        # Extract family indicators
        if 'family' in message_lower or 'kids' in message_lower or 'children' in message_lower:
            if not self.extracted_params['adults']:
                self.extracted_params['adults'] = 2  # Default assumption
            if not self.extracted_params['children']:
                self.extracted_params['children'] = 2  # Default assumption

        # Extract budget keywords
        if 'cheap' in message_lower or 'budget' in message_lower:
            self.extracted_params['budget'] = 500
        elif 'luxury' in message_lower or 'premium' in message_lower:
            self.extracted_params['budget'] = 2000

        # Extract cabin class
        if 'business class' in message_lower or 'business' in message_lower:
            self.extracted_params['cabin_class'] = 'business'
        elif 'first class' in message_lower:
            self.extracted_params['cabin_class'] = 'first'
        else:
            self.extracted_params['cabin_class'] = 'economy'

        # Extract direct flight preference
        if 'direct' in message_lower or 'nonstop' in message_lower:
            self.extracted_params['stops'] = 'Direct only'

        # Extract school break keywords
        if 'school break' in message_lower or 'summer vacation' in message_lower:
            self.extracted_params['school_calendar'] = 'US/Canada: Summer Break'
        elif 'spring break' in message_lower:
            self.extracted_params['school_calendar'] = 'US/Canada: Spring Break'
        elif 'winter break' in message_lower or 'christmas' in message_lower:
            self.extracted_params['school_calendar'] = 'US/Canada: Winter Break'

        return self.extracted_params

    def get_missing_params(self):
        """
        Identify which required parameters are still missing
        Returns list of missing parameter names
        """
        required = ['origin', 'budget', 'adults']
        missing = []

        for param in required:
            if self.extracted_params[param] is None:
                missing.append(param)

        return missing

    def generate_clarifying_question(self):
        """
        Generate next question to ask user based on missing params

        TODO: Replace with LLM-generated contextual questions
        """
        missing = self.get_missing_params()

        if not missing:
            return None  # All required params collected

        # Ask questions in priority order
        if 'origin' in missing:
            return {
                'question': "Where will you be flying from?",
                'param': 'origin',
                'type': 'text',
                'examples': ['Sydney', 'New York', 'London', 'Tokyo']
            }

        if 'budget' in missing:
            current_params = self._summarize_current_params()
            return {
                'question': f"What's your budget per person for flights? {current_params}",
                'param': 'budget',
                'type': 'number',
                'examples': ['$500', '$1000', '$2000']
            }

        if 'adults' in missing:
            return {
                'question': "How many adults are traveling?",
                'param': 'adults',
                'type': 'number',
                'examples': ['1', '2', '4']
            }

        return None

    def _summarize_current_params(self):
        """Summarize what we know so far"""
        parts = []
        if self.extracted_params['trip_type']:
            parts.append(f"{self.extracted_params['trip_type']} trip")
        if self.extracted_params['origin_season']:
            parts.append(f"during {self.extracted_params['origin_season']}")
        if self.extracted_params['children'] and self.extracted_params['children'] > 0:
            parts.append(f"with {self.extracted_params['children']} children")

        return f"({', '.join(parts)})" if parts else ""

    def generate_response(self, user_message):
        """
        Main conversation handler

        Returns:
            dict with 'message', 'ready_to_search' (bool), 'params' (dict)
        """
        self.conversation_history.append({'role': 'user', 'content': user_message})

        # Parse user input
        self.parse_user_input(user_message)

        # Check if we have all required params
        missing = self.get_missing_params()

        if not missing:
            # Ready to search!
            summary = self._generate_search_summary()
            return {
                'message': f"Perfect! {summary}\n\nLet me find the best flights for you...",
                'ready_to_search': True,
                'params': self.extracted_params
            }
        else:
            # Ask next question
            next_q = self.generate_clarifying_question()
            return {
                'message': next_q['question'],
                'ready_to_search': False,
                'params': self.extracted_params,
                'next_question': next_q
            }

    def _generate_search_summary(self):
        """Generate human-readable summary of search params"""
        p = self.extracted_params
        parts = []

        if p['adults']:
            travelers = f"{p['adults']} adult{'s' if p['adults'] > 1 else ''}"
            if p['children']:
                travelers += f" + {p['children']} child{'ren' if p['children'] > 1 else ''}"
            parts.append(travelers)

        if p['origin']:
            parts.append(f"from {p['origin']}")

        if p['trip_type']:
            parts.append(f"for a {p['trip_type']} trip")

        if p['budget']:
            parts.append(f"within ${p['budget']}/person budget")

        if p['origin_season']:
            parts.append(f"during {p['origin_season']}")

        return "I'll search for " + ", ".join(parts) + "."

    def set_param_from_answer(self, param_name, value):
        """
        Manually set a parameter from user's answer to clarifying question
        """
        self.extracted_params[param_name] = value


# Example usage and testing
if __name__ == "__main__":
    print("=== Trip Planning Agent Test ===\n")

    agent = TripPlannerAgent()

    # Test conversation flow
    test_messages = [
        "I want a beach vacation with my family during summer break",
        "Sydney",  # Answer to "where from?"
        "1200",    # Answer to "budget?"
        "2"        # Answer to "how many adults?"
    ]

    print("User: " + test_messages[0])
    for i, msg in enumerate(test_messages):
        response = agent.generate_response(msg)
        print(f"\nAgent: {response['message']}")
        print(f"Ready to search: {response['ready_to_search']}")
        print(f"Extracted params: {response['params']}")

        if response['ready_to_search']:
            print("\n✅ All parameters collected! Ready to filter flights.")
            break

        if i + 1 < len(test_messages):
            print(f"\nUser: {test_messages[i + 1]}")
