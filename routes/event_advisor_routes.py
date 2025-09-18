from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from agents.event_advisor_agent import graph


event_advisor_router = APIRouter()


class EventAdvisorRequest(BaseModel):
    longitude: float
    latitude: float
    from_time: str  # ISO 8601 preferred (e.g., 2025-09-21T17:00:00Z)
    to_time: str    # ISO 8601 preferred
    event_type: Optional[str] = None
    event_details: Optional[str] = None


@event_advisor_router.post("/api/event-advisor")
async def get_event_advice(payload: EventAdvisorRequest):
    try:
        state = {
            "longitude": payload.longitude,
            "latitude": payload.latitude,
            "from_time": payload.from_time,
            "to_time": payload.to_time,
            "event_type": payload.event_type,
            "event_details": payload.event_details,
            "weather_data_at_start_time": None,
            "weather_data_at_end_time": None,
            "advice": None,
        }

        result = graph.invoke(state)
        advice = result.get("advice")
        # advice may be a langchain AIMessage or a plain string
        advice_text = getattr(advice, "content", advice)
        return JSONResponse(status_code=200, content={"advice": advice_text})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Unable to get event advice.", "details": str(e)})
