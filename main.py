from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.health_check_routes import health_check_router
from routes.chat_routes import chat_router
from routes.event_advisor_routes import event_advisor_router
from routes.travel_advisor_routes import travel_advisor_router
import os

app = FastAPI()

# Add CORS middleware

# Get allowed origins from environment variable or use defaults
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [
    "http://localhost:8080", 
    "http://localhost:3000", 
    "http://127.0.0.1:8080", 
    "http://127.0.0.1:3000",
    "https://climeai.vercel.app",
    "https://clime-ai-frontend-u9pm98erx-vocal-vanguards.vercel.app",
    "https://*.vercel.app"
]

# For production, allow all origins if ALLOWED_ORIGINS is not set
if not os.getenv("ALLOWED_ORIGINS"):
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(health_check_router)
app.include_router(event_advisor_router)
app.include_router(travel_advisor_router)