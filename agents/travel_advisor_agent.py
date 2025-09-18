from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import PromptTemplate
from langchain.schema import HumanMessage
from typing import TypedDict, Optional
from agents.agent_utils import get_weather_at_timestamp
from dotenv import load_dotenv
from utils.llm import get_llm_instance

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

# Node: Travel Advisor

def travel_advisor(state: TravelState) -> TravelState:
	chat_model = get_llm_instance(temperature=0.7)
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
except Exception:
	raise Exception("Error building travel advisor graph")
