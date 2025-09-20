import logging
import copy
import os
import requests
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from pymongo import MongoClient
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MongoDB connection
def get_mongodb_client():
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    return MongoClient(mongodb_uri)

mongodb_client = get_mongodb_client()

# LLM instance
def get_llm_instance(temperature=0.7, max_tokens=1500, **kwargs):
    model = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4o-2024-08-06"),
        temperature=0,
        base_url="https://api.aimlapi.com/v1",
        api_key=os.getenv("AIML_API_KEY")
    )
    return model

def get_llm_instance_with_tools(tools=[], **kwargs):
    llm = get_llm_instance(**kwargs)
    return llm.bind_tools(tools)

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

# Weather tools
@tool
def get_current_weather(city_name: str) -> str:
    """Retrieve current weather data for a specific city."""
    print("Tool: get_current_weather Called")
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        raise ValueError("OpenWeatherMap API key not found in environment variables.")
    
    coords = get_coordinates(city_name)
    if isinstance(coords, dict) and "error" in coords:
        return f"error: {coords['error']}"
    
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        'lat': coords["latitude"],
        'lon': coords["longitude"],
        'appid': weather_api_key,
        'units': 'metric',
        'exclude': 'minutely,hourly,daily,alerts'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        data = f"""Weather Data: {data}"""
        print("Current weather data:::", data)
        return data
    except requests.exceptions.RequestException as e:
        return f"error: Error making weather API call: {e}"
    except Exception as e:
        return f"error: An unexpected error occurred: {e}"

@tool
def get_hourly_weather(city_name: str) -> str:
    """Retrieve hourly weather forecast for a specific city for the current day."""
    print("Tool: get_hourly_weather Called")
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        raise ValueError("OpenWeatherMap API key not found in environment variables.")
    
    coords = get_coordinates(city_name)
    if isinstance(coords, dict) and "error" in coords:
        return f"error: {coords['error']}"
    
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        'lat': coords["latitude"],
        'lon': coords["longitude"],
        'appid': weather_api_key,
        'units': 'metric',
        'exclude': 'current,minutely,daily,alerts'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        data = f"""Weather Data: \n {data}"""
        print("Hourly weather data:::", data)
        return data
    except requests.exceptions.RequestException as e:
        return f"error: Error making weather API call: {e}"
    except Exception as e:
        return f"error: An unexpected error occurred: {e}"

@tool
def get_daily_forecast(city_name: str) -> str:
    """Retrieve daily weather forecast for a specific city for today and the next 7 days."""
    print("Tool: get_daily_forecast Called")
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        raise ValueError("OpenWeatherMap API key not found in environment variables.")
    
    coords = get_coordinates(city_name)
    if "error" in coords:
        return coords
    
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        'lat': coords["latitude"],
        'lon': coords["longitude"],
        'appid': weather_api_key,
        'units': 'metric',
        'exclude': 'current,minutely,hourly,alerts'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        data = f"""Weather Data: \n {data}"""
        print("Daily forecast data:::", data)
        return data
    except requests.exceptions.RequestException as e:
        return f"error: Error making weather API call: {e}"
    except Exception as e:
        return f"error: An unexpected error occurred: {e}"

@tool
def get_weather_at_specific_time(city_name: str, time_iso: str) -> str:
    """Retrieve weather for a city at a specific time (ISO 8601)."""
    print("Tool: get_weather_at_specific_time Called")
    coords = get_coordinates(city_name)
    
    try:
        longitude = coords["longitude"]
        latitude = coords["latitude"]
    except Exception:
        return "Error: Unable to resolve coordinates for the provided city."

    # Convert ISO time to timestamp
    try:
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
        data = f"""Weather Data: \n {data}"""
        return data
    except requests.exceptions.RequestException as e:
        return f"error: Error making weather API call: {e}"
    except Exception as e:
        return f"error: An unexpected error occurred: {e}"

# Weather fetching tools list
agent_tools = [get_current_weather, get_hourly_weather, get_daily_forecast, get_weather_at_specific_time]

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

combined_tools = agent_tools + coral_tools

# Initialize LLM with tools
llm_with_tools = get_llm_instance_with_tools(tools=combined_tools)

# System message
sys_msg = SystemMessage(content="""
You are ClimeAI — an AI-powered weather expert that delivers accurate, actionable guidance. Introduce yourself to the users and tell them what do you offer in detail.

Your primary responsibility is to help users with all queries directly or indirectly related to weather, such as:
- Current weather conditions
- Hourly forecasts
- Daily forecasts for upcoming days
- Weather-related insights (temperature, rainfall, storms, humidity, wind, etc.)
- Weather-aware travel guidance (best time to travel, packing advice, flight delay risk, road conditions, destination comparisons by weather)
- Weather-aware event guidance (outdoor event suitability, timing suggestions, contingency plans, safety advisories, attire recommendations, indoor alternatives)

You must always remain strictly within the domain of weather. 
If a user asks something outside the scope of weather, politely decline and respond with an apology, such as:
"I'm sorry, but I can only assist with weather-related questions."

Available Tools:
1. get_current_weather(city_name: str)
   - Fetches the current weather conditions for a given city.
   - Returns live data such as temperature, humidity, pressure, and other real-time atmospheric information.

2. get_hourly_weather(city_name: str)
   - Provides the hourly weather forecast for the current day in a specific city.
   - Useful for short-term planning, such as knowing if it might rain in the next few hours.

3. get_daily_forecast(city_name: str)
   - Retrieves the daily weather forecast for today and the next 7 days.
   - Ideal for medium-term planning, such as weekly travel, events, or agriculture activities.

4. get_weather_at_specific_time(city_name: str, time_iso: str)
   - Retrieves weather for a specific city at an exact datetime (ISO 8601).
   - Internally converts the datetime to a Unix timestamp and calls the One Call 3.0 timemachine endpoint.
   - Useful for event/travel advice tied to a specific time window.

Behavior Guidelines:
- Always answer queries in a clear, concise, and user-friendly manner.
- Use the tools effectively to provide accurate and up-to-date weather data.
- Stay strictly focused on weather-related topics.
- If a question is outside scope, politely decline and apologize.
 - When giving travel or event advice, explicitly tie suggestions to the forecast (e.g., "Rain likely after 3 PM, consider starting earlier or carrying rain gear").
 - Prefer actionable, practical tips grounded in the specific city and time window the user mentions.

Formatting & Tone Guidelines:
- Present responses in a well-organized, structured manner (use brief headings or bullets when helpful)—avoid rigid templates.
- Include relevant emojis to enhance clarity and engagement; use them tastefully and contextually.
- Always include units and local time context if possible.
- Keep paragraphs short and scannable.
- If data confidence is low, say so and suggest a narrower time window or a follow-up check.
""")

def generate(state: MessagesState):
    """Generates a response based on the user's message history."""
    try:
        print("msgs::", state["messages"][-6:])

        # Build provider-compatible messages:
        # - Ensure content is not None
        # - Convert tool role messages into plain HumanMessages containing tool outputs
        # - Drop assistant messages that only contain tool_calls (AIML rejects null content on tool-calls)
        def _to_provider_messages(messages):
            converted = []
            for message in messages:
                msg_copy = copy.deepcopy(message)
                # Normalize content
                if getattr(msg_copy, "content", None) is None:
                    try:
                        msg_copy.content = ""
                    except Exception:
                        pass
                # Detect tool output messages (have tool_call_id attribute)
                if hasattr(msg_copy, "tool_call_id"):
                    tool_name = getattr(msg_copy, "name", "tool")
                    converted.append(
                        HumanMessage(content=f"Tool {tool_name} result:\n{getattr(msg_copy, 'content', '')}")
                    )
                    continue
                # Detect assistant tool-call messages (additional_kwargs.tool_calls present) and drop them
                try:
                    if hasattr(msg_copy, "additional_kwargs") and isinstance(msg_copy.additional_kwargs, dict):
                        if msg_copy.additional_kwargs.get("tool_calls"):
                            # Skip adding this message; the following tool result will be added as HumanMessage
                            continue
                except Exception:
                    pass
                converted.append(msg_copy)
            return converted

        recent_messages = state["messages"][-6:]
        provider_messages = _to_provider_messages(recent_messages)
        invoke_messages = [sys_msg] + provider_messages

        return {"messages": [llm_with_tools.invoke(invoke_messages)]}
    except Exception as e:
        logger.error(f"Error during response generation: {e}")
        raise

# Build graph
try:
    from langgraph.checkpoint.mongodb import MongoDBSaver
    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node(generate)
    graph_builder.add_node("tools", ToolNode(weather_fetching_tools))
    graph_builder.add_edge(START, "generate")
    graph_builder.add_conditional_edges("generate", tools_condition)
    graph_builder.add_edge("tools", "generate")

    memory = MongoDBSaver(mongodb_client)
    graph = graph_builder.compile(checkpointer=memory)
except Exception as e:
    logger.error(f"Error building climeai graph: {e}")
    raise

# Example usage
if __name__ == "__main__":
    # Test the agent
    config = {"configurable": {"thread_id": "test_user"}}
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "What's the weather in New York?"}]},
        config=config
    )
    print("Response:", result)
