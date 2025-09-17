from fastapi import FastAPI
from routes.health_check_routes import health_check_router
from routes.chat_routes import chat_router

app = FastAPI()
app.include_router(chat_router)
app.include_router(health_check_router)