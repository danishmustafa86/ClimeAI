from fastapi import FastAPI
from routes.health_check_routes import health_check_router
from routes.chat_routes import chat_router
from routes.event_advisor_routes import event_advisor_router
from routes.travel_advisor_routes import travel_advisor_router

app = FastAPI()
app.include_router(chat_router)
app.include_router(health_check_router)
app.include_router(event_advisor_router)
app.include_router(travel_advisor_router)