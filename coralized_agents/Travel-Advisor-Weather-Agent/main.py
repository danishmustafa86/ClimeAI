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
from typing import TypedDict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Weather at timestamp utility
async def get_weather_at_timestamp(longitude: float, latitude: float, time_iso: str) -> str:
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

# Travel advisor tool
async def get_travel_advice(from_longitude: float, from_latitude: float, to_longitude: float, to_latitude: float, from_time: str, to_time: str, vehicle_type: str = "car", travel_details: str = "No additional details provided.") -> str:
    """Get comprehensive weather-aware travel guidance for a specific route and time window."""
    logger.info(f"Tool: get_travel_advice Called from ({from_latitude}, {from_longitude}) to ({to_latitude}, {to_longitude}) from {from_time} to {to_time}")
    
    try:
        # Fetch weather at origin (departure time) and destination (arrival time)
        origin_weather = await get_weather_at_timestamp(from_longitude, from_latitude, from_time)
        destination_weather = await get_weather_at_timestamp(to_longitude, to_latitude, to_time)
        
        # Create a comprehensive travel advice prompt
        prompt_text = f"""
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
{origin_weather}

- Weather at destination around arrival time:
{destination_weather}

Guidance Requirements:
- Summarize expected travel conditions succinctly
- Safety advisories (visibility, precipitation, wind, thunderstorms, flooding, heat/cold risk)
- Timing recommendations (leave earlier/later, buffer time, likely delays)
- Route/transport tips (alternate routes/modes if conditions are risky)
- Vehicle-specific tips (e.g., for {vehicle_type}: traction, braking distance, crosswind caution, hydration/AC usage)
- Packing checklist tied to conditions (e.g., rain gear, sunscreen, water, chains, blankets)
- Local considerations for origin and destination (e.g., urban drainage, coastal winds, mountain passes)
- Clear callouts if forecast confidence seems low; suggest re-check time window

Output Format:
- Use short headings and bullet points where helpful
- Include temperatures and units if available; state times clearly
- Keep the tone calm, practical, and traveler-friendly
"""
        
        # Use the LLM to generate advice
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4o-2024-08-06"),
            temperature=0.7,
            base_url="https://api.aimlapi.com/v1",
            api_key=os.getenv("AIML_API_KEY")
        )
        
        response = await model.ainvoke(prompt_text)
        return f"Travel Weather Advice:\n{response.content}"
        
    except Exception as e:
        return f"Error generating travel advice: {str(e)}"

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
            f"""You are a Travel Weather Advisor — a specialized AI agent that provides comprehensive weather-aware travel guidance by analyzing conditions at origin and destination locations, offering transportation-specific recommendations and safety advisories for optimal travel planning.

Your primary responsibility is to evaluate weather conditions at departure and arrival locations to provide practical, safety-focused travel guidance, including:
- Multi-location weather analysis (origin and destination)
- Transportation-specific guidance (car, flight, train, bus, motorcycle, bicycle, walking)
- Safety-first approach with risk assessment and mitigation
- Timing recommendations and optimal scheduling
- Route optimization and weather-aware suggestions
- Packing checklists and weather-appropriate gear
- Local considerations and regional weather patterns
- Delay predictions and weather-related disruptions

You must always remain focused on weather-related travel planning. 
If a user asks something outside the scope of weather-aware travel planning, politely decline and respond with an apology, such as:
"I'm sorry, but I can only assist with weather-related travel planning questions."

Available Travel Planning Tools:
1. get_travel_advice(from_longitude, from_latitude, to_longitude, to_latitude, from_time, to_time, vehicle_type, travel_details) - Get comprehensive weather-aware travel guidance

Input Parameters:
- from_longitude: Origin longitude (required)
- from_latitude: Origin latitude (required)
- to_longitude: Destination longitude (required)
- to_latitude: Destination latitude (required)
- from_time: Departure time in ISO 8601 format (required)
- to_time: Arrival time in ISO 8601 format (required)
- vehicle_type: Transportation mode (car/flight/train/bus/motorcycle/bicycle/walking) (optional)
- travel_details: Additional travel context and requirements (optional)

Supported Transportation Modes:
- Car: Highway driving, road conditions, fuel stops
- Flight: Airport weather, turbulence, delays
- Train: Rail conditions, station weather
- Bus: Public transport, route conditions
- Motorcycle: Wind conditions, visibility, gear requirements
- Bicycle: Wind, precipitation, temperature comfort
- Walking: Pedestrian safety, visibility, comfort

Output Features:
- Weather analysis at origin and destination
- Safety assessment and risk evaluation
- Timing recommendations
- Route guidance and optimization
- Vehicle-specific tips and considerations
- Packing lists and gear recommendations
- Local insights and regional patterns

Behavior Guidelines:
- Always provide practical, actionable travel advice
- Consider both departure and arrival weather conditions
- Include safety-first recommendations
- Suggest alternatives when weather is unfavorable
- Provide specific, location-aware guidance
- Include confidence levels in weather forecasts
- Consider transportation mode-specific factors

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
        "agentDescription": "Travel Advisor Weather Agent - Provides comprehensive weather-aware travel guidance by analyzing conditions at origin and destination locations, offering transportation-specific recommendations and safety advisories for optimal travel planning."
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
                name="get_travel_advice",
                func=None,
                coroutine=get_travel_advice,
                description="Get comprehensive weather-aware travel guidance for a specific route and time window. Parameters: from_longitude (float), from_latitude (float), to_longitude (float), to_latitude (float), from_time (str ISO 8601), to_time (str ISO 8601), vehicle_type (str optional), travel_details (str optional)."
            )
        ]
    
    agent_executor = await create_agent(coral_tools, agent_tools, runtime)

    while True:
        try:
            logger.info("Starting new Travel Advisor agent invocation")
            await agent_executor.ainvoke({"agent_scratchpad": []})
            logger.info("Completed Travel Advisor agent invocation, restarting loop")
            await asyncio.sleep(1)
except Exception as e:
            logger.error(f"Error in Travel Advisor agent loop: {str(e)}")
            logger.error(traceback.format_exc())
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())