from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from agents.travel_advisor_agent import graph


travel_advisor_router = APIRouter()


class TravelAdvisorRequest(BaseModel):
    from_longitude: float
    from_latitude: float
    to_longitude: float
    to_latitude: float
    from_time: str  # ISO 8601 preferred (e.g., 2025-09-21T06:30:00Z)
    to_time: str    # ISO 8601 preferred
    vehicle_type: Optional[str] = None
    travel_details: Optional[str] = None


@travel_advisor_router.post("/api/travel-advisor")
async def get_travel_advice(payload: TravelAdvisorRequest):
    try:
        state = {
            "from_longitude": payload.from_longitude,
            "from_latitude": payload.from_latitude,
            "to_longitude": payload.to_longitude,
            "to_latitude": payload.to_latitude,
            "from_time": payload.from_time,
            "to_time": payload.to_time,
            "vehicle_type": payload.vehicle_type,
            "travel_details": payload.travel_details,
            "weather_at_departure_origin": None,
            "weather_at_arrival_destination": None,
            "advice": None,
        }

        result = graph.invoke(state)
        advice = result.get("advice")
        advice_text = getattr(advice, "content", advice)
        return JSONResponse(status_code=200, content={"advice": advice_text})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Unable to get travel advice.", "details": str(e)})
