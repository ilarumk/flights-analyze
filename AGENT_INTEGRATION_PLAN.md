# 🤖 Agentic Trip Planner - Integration Plan

## Overview

Add conversational AI agent to Trip Planner that:
1. Understands natural language queries
2. Asks clarifying questions when information is missing
3. Extracts structured parameters from conversation
4. Filters flights based on collected information

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  User Input (Natural Language)                          │
│  "I want a beach vacation with my family during summer" │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Agent (LLM/Custom Logic)                               │
│  - Parse intent and entities                            │
│  - Extract: trip_type=beach, travelers=family,          │
│    season=summer                                        │
│  - Identify missing: origin, budget                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Clarifying Questions (Agentic)                         │
│  "Where will you be flying from?"                       │
│  User: "Sydney"                                         │
│  "What's your budget per person?"                       │
│  User: "$1200"                                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Structured Parameters                                  │
│  {                                                       │
│    origin: "SYD",                                       │
│    budget: 1200,                                        │
│    adults: 2,                                           │
│    children: 2,                                         │
│    trip_type: "beach",                                  │
│    origin_season: "Summer ☀️"                          │
│  }                                                       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Flight Filtering (Existing Logic)                      │
│  - Filter by origin=SYD, budget<=1200, trip_type=beach │
│  - Apply season filters                                 │
│  - Return top recommendations                           │
└─────────────────────────────────────────────────────────┘
```

---

## Required Parameters

### Essential (Must Ask):
- **origin**: Flying from which city/airport
- **budget**: Budget per person (USD)
- **adults**: Number of adult travelers

### Optional (Can Infer):
- **children**: Number of children (default: 0)
- **cabin_class**: economy/business/first (default: economy)
- **trip_type**: beach/culture/ski/etc (default: All)
- **origin_season**: When traveling from home
- **dest_season**: Desired weather at destination
- **school_calendar**: School break periods
- **stops**: Direct/1 stop/2+ stops
- **travel_period**: Next 3/6 months, etc.

---

## Conversation Flow Examples

### Example 1: Complete Information

**User:** "Find me direct flights from Sydney to Bali in December for 2 adults and 1 child, economy class, budget $800 per person"

**Agent Analysis:**
- ✅ origin: Sydney (SYD)
- ✅ destination: Bali (DPS)
- ✅ month: December
- ✅ adults: 2
- ✅ children: 1
- ✅ cabin: economy
- ✅ budget: $800
- ✅ stops: direct only

**Agent:** "Perfect! Let me find direct economy flights from Sydney to Bali in December for 2 adults + 1 child within $800/person budget..."

*Shows filtered results immediately*

---

### Example 2: Missing Information (Agentic Questioning)

**User:** "I want a beach vacation with my family during summer break"

**Agent Analysis:**
- ❌ origin: Unknown
- ❌ budget: Unknown
- ✅ trip_type: beach
- ✅ travelers: family (assume 2 adults + 2 children)
- ✅ season: summer
- ✅ school_calendar: summer break

**Agent:** "Great! A family beach vacation during summer break. Where will you be flying from?"

**User:** "Sydney"

**Agent:** "Perfect! What's your budget per person for flights?"

**User:** "Around $1200"

**Agent:** "Excellent! Let me find beach destinations from Sydney during summer (Dec-Feb) for a family of 4 within $1200/person..."

*Shows filtered results*

---

### Example 3: Ambiguous Request (Smart Follow-ups)

**User:** "Show me cheap winter trips"

**Agent Analysis:**
- ❌ origin: Unknown
- ✅ budget: Low (infer ~$500)
- ✅ season: winter
- ❓ winter at origin or destination? (Ambiguous!)

**Agent:** "I can help! Just to clarify - are you looking for:
1. 🏠 Travel **during winter** at home (your winter break)
2. 🎯 Go somewhere with **winter weather** at destination (skiing, snow)
3. 🌴 **Escape winter** and go somewhere warm"

**User:** "Escape winter, go somewhere warm"

**Agent:** "Got it! Winter escape to warm destinations. Where are you flying from?"

**User:** "New York"

**Agent:** "Perfect! Let me find warm beach destinations from New York during your winter (Dec-Feb) within budget..."

---

## Agent Implementation Options

### Option 1: Simple Rule-Based (Current Placeholder)
```python
# trip_agent.py - keyword matching
if 'beach' in message: trip_type = 'beach'
if 'family' in message: adults=2, children=2
```
**Pros:** Fast, no dependencies, predictable
**Cons:** Limited understanding, can't handle complex queries

### Option 2: LLM-Based (Recommended for Production)
```python
# Use OpenAI/Anthropic/Gemini
response = llm.chat([
    {"role": "system", "content": TRIP_PLANNER_PROMPT},
    {"role": "user", "content": user_message}
])
# Extract structured JSON from LLM response
```
**Pros:** Natural conversation, understands context, flexible
**Cons:** Requires API key, costs money, slower

### Option 3: Custom AgenticX Framework (Your Plan)
```python
# Use your AgenticX framework
from agenticx import TripPlannerAgent

agent = TripPlannerAgent(
    tools=[extract_entities, ask_clarifying_questions, filter_flights],
    knowledge_base=destinations_data
)
```
**Pros:** Fully customizable, can use any LLM, agentic workflows
**Cons:** Requires building the framework

---

## UI Integration in Streamlit

### Layout:

```
┌──────────────────────────────────────────────────────┐
│  🎯 Trip Planner                                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  💬 Tell me what you're looking for:                │
│  ┌────────────────────────────────────────────────┐ │
│  │ "Beach vacation with family during summer"    │ │
│  └────────────────────────────────────────────────┘ │
│  [✨ Plan My Trip]                                  │
│                                                      │
│  ─────────────────────────────────────────────────  │
│                                                      │
│  🤖 Agent: Where will you be flying from?           │
│                                                      │
│  👤 You: Sydney                                     │
│                                                      │
│  🤖 Agent: What's your budget per person?           │
│                                                      │
│  👤 You: $1200                                      │
│                                                      │
│  🤖 Agent: Perfect! Searching for beach             │
│     destinations from Sydney...                     │
│                                                      │
│  ✅ Found 15 results                                │
│                                                      │
│  [Flight Results Display]                           │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Code Structure:

```python
# In flight_explorer.py - Trip Planner tab

if st.session_state.get('use_agent_mode', False):
    # Agent Mode - Conversational
    st.markdown("### 💬 Conversational Trip Planning")

    user_input = st.text_area(
        "Tell me what you're looking for:",
        placeholder="E.g., 'Beach vacation with family during summer break'"
    )

    if st.button("✨ Plan My Trip"):
        # TODO: Replace with actual agent
        agent = TripPlannerAgent()
        response = agent.generate_response(user_input)

        # Show conversation
        st.chat_message("assistant").write(response['message'])

        # If ready, filter and show results
        if response['ready_to_search']:
            filtered_df = filter_flights(response['params'])
            display_results(filtered_df)
else:
    # Form Mode - Current implementation
    [Existing form-based UI]
```

---

## Parameter Extraction Examples

### Entity Extraction Needed:

| User Input | Extract |
|------------|---------|
| "Sydney to Bali" | origin=SYD, destination=DPS |
| "2 adults and 1 child" | adults=2, children=1 |
| "$800 budget" | budget=800 |
| "economy class" | cabin_class=economy |
| "during summer vacation" | school_calendar=summer |
| "direct flight" | stops=direct |
| "want to go skiing" | trip_type=ski, dest_season=winter |
| "escape the cold" | dest_season=summer/warm |

---

## Next Steps

### Phase 1: UI Shell (Now)
- ✅ Create agent placeholder (`trip_agent.py`)
- ✅ Document integration plan
- ⏳ Add chat interface to Trip Planner tab
- ⏳ Wire up agent to flight filtering

### Phase 2: Simple Agent (Quick Win)
- Keyword-based entity extraction
- Basic clarifying questions
- Connect to existing filters

### Phase 3: LLM Integration (Production)
- Integrate OpenAI/Claude/Gemini
- Natural language understanding
- Context-aware follow-ups

### Phase 4: Full Agentic System (Your Framework)
- Replace with AgenticX framework
- Advanced reasoning
- Multi-turn conversations
- Memory and context

---

## Integration Points

### Files to Modify:

1. **flight_explorer.py**
   - Add chat interface in Trip Planner tab
   - Import `trip_agent.py`
   - Connect agent output to flight filters

2. **trip_agent.py** (Your Agent)
   - Replace placeholder with real LLM/logic
   - Add entity extraction
   - Improve question generation

3. **requirements.txt**
   - Add LLM dependencies when ready
   - `openai>=1.0.0` or `anthropic>=0.18.0`

---

## Sample Prompts for LLM Agent

```
You are a helpful travel planning assistant. Your job is to help users find flights.

Required information:
- Origin city/airport (where flying from)
- Budget per person (USD)
- Number of adult travelers

Optional information:
- Number of children
- Cabin class (economy/business/first)
- Trip type (beach/ski/culture/food/adventure)
- Travel season preferences
- Direct flights preference

Instructions:
1. Extract entities from user's message
2. If missing required info, ask ONE clarifying question at a time
3. Be conversational and friendly
4. Once you have all required info, output JSON with parameters

Example:
User: "I want a beach vacation with family during summer"
You: "Great! A family beach vacation sounds wonderful. Where will you be flying from?"
```

---

## Testing Scenarios

### Test 1: Complete Query
Input: "Find flights from Sydney to Bali for 2 adults, economy, budget $800"
Expected: Immediate results, no questions

### Test 2: Partial Query
Input: "Beach vacation with kids"
Expected: Ask for origin, budget, number of travelers

### Test 3: Ambiguous Query
Input: "Winter trip"
Expected: Clarify if they want winter weather or escaping winter

### Test 4: Complex Query
Input: "Cheap family ski trip from New York during Christmas break, direct flights preferred"
Expected: Extract all params, maybe ask budget

---

## Ready to Build?

The placeholder is ready. When you build your AgenticX framework, just replace the `trip_agent.py` logic with your agent implementation!

**Integration is as simple as:**
```python
from your_agent_framework import TripPlannerAgent

agent = TripPlannerAgent()
response = agent.chat(user_message)
params = response.extracted_parameters
filtered_flights = apply_filters(df, params)
```
