from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import PromptTemplate
from langchain.schema import HumanMessage
from typing import TypedDict, Optional
from agents.agent_utils import get_weather_at_timestamp
from dotenv import load_dotenv
from utils.llm import get_llm_instance

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

# Node: Event Advisor
def event_advisor(state: EventState) -> EventState:
    chat_model = get_llm_instance(temperature=0.7)
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
except:
    raise Exception("Error building event advisor graph")

# Example usage
if __name__ == "__main__":
    input_state = {
        "longitude": -73.935242,
        "latitude": 40.730610,
        "from_time": "2024-11-01T10:00:00",
        "to_time": "2024-11-01T15:00:00",
        "event_type": "outdoor music festival",
        "event_details": "The event is a music festival with a lineup of popular artists.",
        "weather_data_at_start_time": None,
        "weather_data_at_end_time": None,
        "advice": None,
    }

    result = graph.invoke(input_state)
    print("Advice:\n", result["advice"])
