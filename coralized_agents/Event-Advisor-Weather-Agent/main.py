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

# Define the shared state schema
class EventState(TypedDict):
    longitude: float
    latitude: float
    from_time: str
    to_time: str
    event_type: Optional[str]  # indoor/outdoor/optional text
    event_details: Optional[str]
    weather_data_at_start_time: Optional[str]
    weather_data_at_end_time: Optional[str]
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

# Prompt template for the EventAdvisor node
prompt_template = PromptTemplate.from_template(
    """
You are an event weather advisor. Given the weather data and event details, provide detailed advice and suggestions.

Event details:
- Location: latitude {latitude}, longitude {longitude}
- Time range: from {from_time} to {to_time}
- Event type: {event_type}
- Event details: {event_details}

Weather data at the start of the event:
{weather_data_at_start_time}

Weather data at the end of the event:
{weather_data_at_end_time}

Please provide detailed advice and suggestions for the event considering the weather.
"""
)

# Node: Weather Fetcher
def weather_fetcher(state: EventState) -> EventState:
    # Fetch weather at start and end times using ISO datetimes
    start_weather = get_weather_at_timestamp(state["longitude"], state["latitude"], state["from_time"])
    end_weather = get_weather_at_timestamp(state["longitude"], state["latitude"], state["to_time"])
    return {**state, "weather_data_at_start_time": start_weather, "weather_data_at_end_time": end_weather}

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

# Node: Event Advisor
def event_advisor(state: EventState) -> EventState:
    chat_model = get_llm_instance_with_tools(tools=coral_tools)
    prompt_text = prompt_template.format(
        latitude=state["latitude"],
        longitude=state["longitude"],
        from_time=state["from_time"],
        to_time=state["to_time"],
        event_type=state.get("event_type", "outdoor"),
        event_details=state.get("event_details", "No event details available."),
        weather_data_at_start_time=state.get("weather_data_at_start_time", "No weather data available."),
        weather_data_at_end_time=state.get("weather_data_at_end_time", "No weather data available."),
    )
    human_message = HumanMessage(content=prompt_text)
    print("Prompt to Event Advisor:::", human_message)
    response = chat_model.invoke([human_message])
    return {**state, "advice": response}

# Build the graph
try:
    builder = StateGraph(EventState)
    builder.add_node("weather_fetcher", weather_fetcher)
    builder.add_node("event_advisor", event_advisor)

    # Define edges: Start -> Weather Fetcher -> Event Advisor -> End
    builder.add_edge(START, "weather_fetcher")
    builder.add_edge("weather_fetcher", "event_advisor")
    builder.add_edge("event_advisor", END)

    # Compile the graph
    graph = builder.compile()
except Exception as e:
    raise Exception(f"Error building event advisor graph: {e}")

# Example usage
if __name__ == "__main__":
    input_state = {
        "longitude": -73.935242,
        "latitude": 40.730610,
        "from_time": "2024-11-01T10:00:00Z",
        "to_time": "2024-11-01T15:00:00Z",
        "event_type": "outdoor music festival",
        "event_details": "The event is a music festival with a lineup of popular artists.",
        "weather_data_at_start_time": None,
        "weather_data_at_end_time": None,
        "advice": None,
    }

    result = graph.invoke(input_state)
    print("Advice:\n", result["advice"])
