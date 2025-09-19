import logging
import copy
from dotenv import load_dotenv
from langchain.schema import SystemMessage, HumanMessage
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
    """
    Generates a response based on the user's message history.

    Parameters:
        state (MessagesState): The state of the conversation, containing past messages.

    Returns:
        dict: A dictionary containing the generated message.
    """
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