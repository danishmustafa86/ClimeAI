import logging
from dotenv import load_dotenv
from langchain.schema import SystemMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.mongodb import MongoDBSaver
from configurations.db import mongodb_client
from utils.llm import get_llm_instance_with_tools
from agents.tools import weather_fetching_tools

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Only log errors and above
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

llm_with_tools = get_llm_instance_with_tools(tools=weather_fetching_tools)

sys_msg = SystemMessage(content="""
You are ClimeAI, an intelligent weather assistant.

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

Behavior Guidelines:
- Always answer queries in a clear, concise, and user-friendly manner.
- Use the tools effectively to provide accurate and up-to-date weather data.
- Stay strictly focused on weather-related topics.
- If a question is outside scope, politely decline and apologize.
 - When giving travel or event advice, explicitly tie suggestions to the forecast (e.g., "Rain likely after 3 PM, consider starting earlier or carrying rain gear").
 - Prefer actionable, practical tips grounded in the specific city and time window the user mentions.
""")

def generate(state: MessagesState):
    """
    Generates a response based on the user's message history.

    Parameters:
        state (MessagesState): The state of the conversation, containing past messages.

    Returns:
        dict: A dictionary containing the generated message.
    """
    try:
        return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"][-6:])]}
    except Exception as e:
        logger.error(f"Error during response generation: {e}")
        raise

# Build graph
try:
    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node(generate)
    graph_builder.add_node("tools", ToolNode(weather_fetching_tools))
    graph_builder.add_edge(START, "generate")
    graph_builder.add_conditional_edges("generate", tools_condition)
    graph_builder.add_edge("tools", "generate")

    memory = MongoDBSaver(mongodb_client)
    graph = graph_builder.compile(checkpointer=memory)
except Exception as e:
    logger.error(f"Error building state graph: {e}")
    raise