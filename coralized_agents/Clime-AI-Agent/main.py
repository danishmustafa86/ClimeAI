import urllib.parse
from dotenv import load_dotenv
import os, json, asyncio, traceback
from langchain.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import Tool
import logging
import traceback
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
async def get_current_weather(city_name: str) -> str:
    """Retrieve current weather data for a specific city."""
    logger.info(f"Tool: get_current_weather Called for {city_name}")
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        return "Error: OpenWeatherMap API key not found in environment variables."
    
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
        return f"Current weather in {city_name}: {json.dumps(data, indent=2)}"
    except requests.exceptions.RequestException as e:
        return f"error: Error making weather API call: {e}"
    except Exception as e:
        return f"error: An unexpected error occurred: {e}"

async def get_hourly_weather(city_name: str) -> str:
    """Retrieve hourly weather forecast for a specific city for the current day."""
    logger.info(f"Tool: get_hourly_weather Called for {city_name}")
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        return "Error: OpenWeatherMap API key not found in environment variables."
    
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
        return f"Hourly weather forecast for {city_name}: {json.dumps(data, indent=2)}"
    except requests.exceptions.RequestException as e:
        return f"error: Error making weather API call: {e}"
    except Exception as e:
        return f"error: An unexpected error occurred: {e}"

async def get_daily_forecast(city_name: str) -> str:
    """Retrieve daily weather forecast for a specific city for today and the next 7 days."""
    logger.info(f"Tool: get_daily_forecast Called for {city_name}")
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        return "Error: OpenWeatherMap API key not found in environment variables."
    
    coords = get_coordinates(city_name)
    if "error" in coords:
        return f"error: {coords['error']}"
    
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
        return f"Daily forecast for {city_name}: {json.dumps(data, indent=2)}"
    except requests.exceptions.RequestException as e:
        return f"error: Error making weather API call: {e}"
    except Exception as e:
        return f"error: An unexpected error occurred: {e}"

async def get_weather_at_specific_time(city_name: str, time_iso: str) -> str:
    """Retrieve weather for a city at a specific time (ISO 8601)."""
    logger.info(f"Tool: get_weather_at_specific_time Called for {city_name} at {time_iso}")
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
        return f"Weather in {city_name} at {time_iso}: {json.dumps(data, indent=2)}"
    except requests.exceptions.RequestException as e:
        return f"error: Error making weather API call: {e}"
    except Exception as e:
        return f"error: An unexpected error occurred: {e}"

def get_tools_description(tools):
    return "\n".join(
        f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
        for tool in tools
    )

async def create_agent(coral_tools, agent_tools, runtime):
    coral_tools_description = get_tools_description(coral_tools)
    
    if runtime is not None:
        agent_tools_for_description = [
            tool for tool in coral_tools if tool.name in agent_tools
        ]
        agent_tools_description = get_tools_description(agent_tools_for_description)
        combined_tools = coral_tools + agent_tools_for_description
        user_request_tool = "request_question"
        user_answer_tool = "answer_question"
        print(agent_tools_description)
    else:
        # For other runtimes (e.g., devmode), agent_tools is a list of Tool objects
        agent_tools_description = get_tools_description(agent_tools)
        combined_tools = coral_tools + agent_tools
        user_request_tool = "ask_human"
        user_answer_tool = "ask_human"

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""You are ClimeAI — an AI-powered weather expert that delivers accurate, actionable guidance. You specialize in weather-related queries and provide comprehensive weather information and advice.

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

Available Weather Tools:
1. get_current_weather(city_name: str) - Fetches current weather conditions for any city
2. get_hourly_weather(city_name: str) - Provides hourly forecast for the current day
3. get_daily_forecast(city_name: str) - Retrieves 7-day weather forecast
4. get_weather_at_specific_time(city_name: str, time_iso: str) - Weather for specific timestamp

Behavior Guidelines:
- Always answer queries in a clear, concise, and user-friendly manner
- Use the weather tools effectively to provide accurate and up-to-date weather data
- Stay strictly focused on weather-related topics
- If a question is outside scope, politely decline and apologize
- When giving travel or event advice, explicitly tie suggestions to the forecast
- Prefer actionable, practical tips grounded in the specific city and time window

Formatting & Tone Guidelines:
- Present responses in a well-organized, structured manner
- Include relevant emojis to enhance clarity and engagement
- Always include units and local time context if possible
- Keep paragraphs short and scannable
- If data confidence is low, say so and suggest a narrower time window

**You MUST NEVER finish the chain**

These are the list of coral tools: {coral_tools_description}
These are the list of agent tools: {agent_tools_description}

**You MUST NEVER finish the chain**"""
        ),
        ("placeholder", "{agent_scratchpad}")
    ])

    from langchain_openai import ChatOpenAI
    model = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4o-2024-08-06"),
        temperature=0,
        base_url="https://api.aimlapi.com/v1",
        api_key=os.getenv("AIML_API_KEY")
    )
    agent = create_tool_calling_agent(model, combined_tools, prompt)
    return AgentExecutor(agent=agent, tools=combined_tools, verbose=True)

async def main():
    runtime = os.getenv("CORAL_ORCHESTRATION_RUNTIME", None)
    if runtime is None:
        load_dotenv()

    base_url = os.getenv("CORAL_SSE_URL")
    agentID = os.getenv("CORAL_AGENT_ID")

    coral_params = {
        "agentId": agentID,
        "agentDescription": "ClimeAI - An intelligent weather assistant that provides real-time weather information, forecasts, and weather-aware guidance through natural language conversations."
    }

    query_string = urllib.parse.urlencode(coral_params)

    CORAL_SERVER_URL = f"{base_url}?{query_string}"
    logger.info(f"Connecting to Coral Server: {CORAL_SERVER_URL}")

    client = MultiServerMCPClient(
        connections={
            "coral": {
                "transport": "sse",
                "url": CORAL_SERVER_URL,
                "timeout": 300000,
                "sse_read_timeout": 300000,
            }
        }
    )   
    logger.info("Coral Server Connection Established")

    coral_tools = await client.get_tools(server_name="coral")
    logger.info(f"Coral tools count: {len(coral_tools)}")
    
    if runtime is not None:
        required_tools = ["request-question", "answer-question"]
        available_tools = [tool.name for tool in coral_tools]

        for tool_name in required_tools:
            if tool_name not in available_tools:
                error_message = f"Required tool '{tool_name}' not found in coral_tools. Please ensure that while adding the agent on Coral Studio, you include the tool from Custom Tools."
                logger.error(error_message)
                raise ValueError(error_message)        
        agent_tools = required_tools

    else:
        agent_tools = [
            Tool(
                name="get_current_weather",
                func=None,
                coroutine=get_current_weather,
                description="Get current weather conditions for a specific city."
            ),
            Tool(
                name="get_hourly_weather",
                func=None,
                coroutine=get_hourly_weather,
                description="Get hourly weather forecast for a specific city for the current day."
            ),
            Tool(
                name="get_daily_forecast",
                func=None,
                coroutine=get_daily_forecast,
                description="Get daily weather forecast for a specific city for today and the next 7 days."
            ),
            Tool(
                name="get_weather_at_specific_time",
                func=None,
                coroutine=get_weather_at_specific_time,
                description="Get weather for a city at a specific time (ISO 8601 format)."
            )
        ]
    
    agent_executor = await create_agent(coral_tools, agent_tools, runtime)

    while True:
        try:
            logger.info("Starting new ClimeAI agent invocation")
            await agent_executor.ainvoke({"agent_scratchpad": []})
            logger.info("Completed ClimeAI agent invocation, restarting loop")
            await asyncio.sleep(1)
        except Exception as e:
                    logger.error(f"Error in ClimeAI agent loop: {str(e)}")
                    logger.error(traceback.format_exc())
                    await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())