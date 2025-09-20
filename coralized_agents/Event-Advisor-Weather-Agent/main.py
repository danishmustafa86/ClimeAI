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

# Event advisor tool
async def get_event_advice(longitude: float, latitude: float, from_time: str, to_time: str, event_type: str = "outdoor", event_details: str = "No event details available.") -> str:
    """Get weather-aware event planning advice for a specific location and time window."""
    logger.info(f"Tool: get_event_advice Called for location ({latitude}, {longitude}) from {from_time} to {to_time}")
    
    try:
        # Fetch weather at start and end times
        start_weather = await get_weather_at_timestamp(longitude, latitude, from_time)
        end_weather = await get_weather_at_timestamp(longitude, latitude, to_time)
        
        # Create a comprehensive event advice prompt
        prompt_text = f"""
You are an event weather advisor. Given the weather data and event details, provide detailed advice and suggestions.

Event details:
- Location: latitude {latitude}, longitude {longitude}
- Time range: from {from_time} to {to_time}
- Event type: {event_type}
- Event details: {event_details}

Weather data at the start of the event:
{start_weather}

Weather data at the end of the event:
{end_weather}

Please provide detailed advice and suggestions for the event considering the weather. Include:
1. Weather summary and conditions
2. Safety advisories
3. Timing recommendations
4. Event setup considerations
5. Attendee guidance
6. Contingency plans
7. Attire suggestions
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
        return f"Event Weather Advice:\n{response.content}"
        
    except Exception as e:
        return f"Error generating event advice: {str(e)}"

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
            f"""You are an Event Weather Advisor — a specialized AI agent that provides weather-aware guidance for event planning. You help organizers make informed decisions about outdoor and indoor events based on forecasted weather conditions.

Your primary responsibility is to analyze weather conditions for specific locations and time windows to provide comprehensive event planning advice, including:
- Weather suitability assessment for event types
- Safety considerations and risk evaluation
- Timing recommendations and optimal scheduling
- Contingency planning for weather changes
- Attendee guidance and attire suggestions
- Event setup considerations
- Indoor/outdoor alternatives

You must always remain focused on weather-related event planning. 
If a user asks something outside the scope of weather-aware event planning, politely decline and respond with an apology, such as:
"I'm sorry, but I can only assist with weather-related event planning questions."

Available Event Planning Tools:
1. get_event_advice(longitude, latitude, from_time, to_time, event_type, event_details) - Get comprehensive weather-aware event planning advice

Input Parameters:
- longitude: Event location longitude (required)
- latitude: Event location latitude (required)  
- from_time: Event start time in ISO 8601 format (required)
- to_time: Event end time in ISO 8601 format (required)
- event_type: Type of event (indoor/outdoor/hybrid) (optional)
- event_details: Additional event context and requirements (optional)

Output Features:
- Weather analysis during event window
- Safety assessment and risk evaluation
- Timing recommendations
- Event setup instructions
- Attendee guidance
- Contingency planning
- Attire suggestions

Behavior Guidelines:
- Always provide practical, actionable advice
- Consider both start and end time weather conditions
- Include safety-first recommendations
- Suggest alternatives when weather is unfavorable
- Provide specific, location-aware guidance
- Include confidence levels in weather forecasts

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
        "agentDescription": "Event Advisor Weather Agent - Provides weather-aware guidance for event planning, helping organizers make informed decisions about outdoor and indoor events based on forecasted weather conditions."
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
                name="get_event_advice",
                func=None,
                coroutine=get_event_advice,
                description="Get weather-aware event planning advice for a specific location and time window. Parameters: longitude (float), latitude (float), from_time (str ISO 8601), to_time (str ISO 8601), event_type (str optional), event_details (str optional)."
            )
        ]
    
    agent_executor = await create_agent(coral_tools, agent_tools, runtime)

    while True:
        try:
            logger.info("Starting new Event Advisor agent invocation")
            await agent_executor.ainvoke({"agent_scratchpad": []})
            logger.info("Completed Event Advisor agent invocation, restarting loop")
            await asyncio.sleep(1)
except Exception as e:
            logger.error(f"Error in Event Advisor agent loop: {str(e)}")
            logger.error(traceback.format_exc())
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())