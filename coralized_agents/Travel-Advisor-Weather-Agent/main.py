import os
import requests
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from typing import TypedDict, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment variables
load_dotenv()

# Define the shared state schema for the Travel Advisor
class TravelState(TypedDict):
    from_longitude: float
    from_latitude: float
    to_longitude: float
    to_latitude: float
    from_time: str
    to_time: str
    vehicle_type: Optional[str]
    travel_details: Optional[str]
    weather_at_departure_origin: Optional[str]
    weather_at_arrival_destination: Optional[str]
    advice: Optional[str]

# Geocoding utility
def get_coordinates(city_name: str) -> dict:
    opencage_api_key = os.getenv("OPENCAGE_API_KEY")
    if not opencage_api_key:
        raise ValueError("OpenCage API key not found in environment variables.")
    
    url = f"https://api.opencagedata.com/geocode/v1/json?q={city_name}&key={opencage_api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                latitude = results[0]["geometry"]["lat"]
                longitude = results[0]["geometry"]["lng"]
                return {"latitude": latitude, "longitude": longitude}
            else:
                return {"error": "No results found for the provided city."}
        else:
            return {"error": f"Request failed with status code {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Error making geocoding API call: {e}"}

# Weather at timestamp utility
def get_weather_at_timestamp(longitude: float, latitude: float, time_iso: str) -> str:
    """Get weather data for a specific location at a specific timestamp."""
    try:
        # Convert ISO time to timestamp
        dt = datetime.fromisoformat(time_iso.replace('Z', '+00:00'))
        timestamp = int(dt.timestamp())
    except Exception as e:
        return f"Error: Invalid time format. Use ISO 8601 format (e.g., 2025-09-21T17:00:00Z). Error: {e}"

    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        return "Error: OpenWeatherMap API key not found."

    base_url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine"
    params = {
        'lat': latitude,
        'lon': longitude,
        'dt': timestamp,
        'appid': weather_api_key,
        'units': 'metric'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract key weather information
        current = data.get('data', [{}])[0] if data.get('data') else {}
        weather_info = {
            'temperature': current.get('temp', 'N/A'),
            'feels_like': current.get('feels_like', 'N/A'),
            'humidity': current.get('humidity', 'N/A'),
            'pressure': current.get('pressure', 'N/A'),
            'wind_speed': current.get('wind_speed', 'N/A'),
            'wind_direction': current.get('wind_deg', 'N/A'),
            'visibility': current.get('visibility', 'N/A'),
            'weather_description': current.get('weather', [{}])[0].get('description', 'N/A') if current.get('weather') else 'N/A',
            'clouds': current.get('clouds', 'N/A'),
            'uv_index': current.get('uvi', 'N/A')
        }
        
        return f"Weather at {time_iso}: {json.dumps(weather_info, indent=2)}"
    except requests.exceptions.RequestException as e:
        return f"Error: Weather API call failed: {e}"
    except Exception as e:
        return f"Error: An unexpected error occurred: {e}"

# LLM instance
def get_llm_instance(temperature=0.7, max_tokens=1500, **kwargs):
    model = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4o-2024-08-06"),
        temperature=temperature,
        base_url="https://api.aimlapi.com/v1",
        api_key=os.getenv("AIML_API_KEY")
    )
    return model

def get_llm_instance_with_tools(tools=[], **kwargs):
    llm = get_llm_instance(**kwargs)
    return llm.bind_tools(tools)

# Prompt template for the TravelAdvisor node
prompt_template = PromptTemplate.from_template(
    """
You are a travel weather advisor. Provide practical, safety-focused, and concise travel guidance based on the user's itinerary and forecasted weather.

Trip Overview:
- Origin: latitude {from_latitude}, longitude {from_longitude}
- Destination: latitude {to_latitude}, longitude {to_longitude}
- Planned departure time (origin local/ISO): {from_time}
- Planned arrival time (destination local/ISO): {to_time}
- Vehicle type: {vehicle_type}
- Traveler details/context: {travel_details}

Weather Snapshot:
- Weather at origin around departure time:
{weather_at_departure_origin}

- Weather at destination around arrival time:
{weather_at_arrival_destination}

Guidance Requirements:
- Summarize expected travel conditions succinctly.
- Safety advisories (visibility, precipitation, wind, thunderstorms, flooding, heat/cold risk).
- Timing recommendations (leave earlier/later, buffer time, likely delays).
- Route/transport tips (alternate routes/modes if conditions are risky).
- Vehicle-specific tips (e.g., for {vehicle_type}: traction, braking distance, crosswind caution, hydration/AC usage).
- Packing checklist tied to conditions (e.g., rain gear, sunscreen, water, chains, blankets).
- Local considerations for origin and destination (e.g., urban drainage, coastal winds, mountain passes).
- Clear callouts if forecast confidence seems low; suggest re-check time window.

Output Format:
- Use short headings and bullet points where helpful.
- Include temperatures and units if available; state times clearly.
- Keep the tone calm, practical, and traveler-friendly.
"""
)

# Node: Weather Fetcher
# Fetch weather at origin at departure time and at destination at arrival time

def weather_fetcher(state: TravelState) -> TravelState:
    origin_weather = get_weather_at_timestamp(
        state["from_longitude"], state["from_latitude"], state["from_time"]
    )
    destination_weather = get_weather_at_timestamp(
        state["to_longitude"], state["to_latitude"], state["to_time"]
    )
    return {
        **state,
        "weather_at_departure_origin": origin_weather,
        "weather_at_arrival_destination": destination_weather,
    }

client = MultiServerMCPClient(
        connections={
            "coral": {
                "transport": "sse",
                "url": CORAL_SERVER_URL,
                "timeout": timeout,
                "sse_read_timeout": timeout,
            } 
        }
    )


coral_tools = await client.get_tools(server_name="coral")

def travel_advisor(state: TravelState) -> TravelState:
    chat_model = get_llm_instance_with_tools(toosl= coral_tools)
    prompt_text = prompt_template.format(
        from_latitude=state["from_latitude"],
        from_longitude=state["from_longitude"],
        to_latitude=state["to_latitude"],
        to_longitude=state["to_longitude"],
        from_time=state["from_time"],
        to_time=state["to_time"],
        vehicle_type=state.get("vehicle_type", "car"),
        travel_details=state.get("travel_details", "No additional details provided."),
        weather_at_departure_origin=state.get("weather_at_departure_origin", "No weather data available."),
        weather_at_arrival_destination=state.get("weather_at_arrival_destination", "No weather data available."),
    )
    human_message = HumanMessage(content=prompt_text)
    print("Prompt to Travel Advisor:::", human_message)
    response = chat_model.invoke([human_message])
    return {**state, "advice": response}

# Build the graph
try:
    builder = StateGraph(TravelState)
    builder.add_node("weather_fetcher", weather_fetcher)
    builder.add_node("travel_advisor", travel_advisor)

    # Define edges: Start -> Weather Fetcher -> Travel Advisor -> End
    builder.add_edge(START, "weather_fetcher")
    builder.add_edge("weather_fetcher", "travel_advisor")
    builder.add_edge("travel_advisor", END)

    # Compile the graph
    graph = builder.compile()
except Exception as e:
    raise Exception(f"Error building travel advisor graph: {e}")

# Example usage
if __name__ == "__main__":
    input_state = {
        "from_longitude": 74.3587,
        "from_latitude": 31.5204,
        "to_longitude": 73.0479,
        "to_latitude": 33.6844,
        "from_time": "2025-09-21T06:30:00Z",
        "to_time": "2025-09-21T10:30:00Z",
        "vehicle_type": "car",
        "travel_details": "Early morning highway drive with two passengers and luggage.",
        "weather_at_departure_origin": None,
        "weather_at_arrival_destination": None,
        "advice": None,
    }

    result = graph.invoke(input_state)
    print("Advice:\n", result["advice"])
