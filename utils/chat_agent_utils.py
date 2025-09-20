from configurations.db import chat_collection
from datetime import datetime, timezone
from langchain.schema import AIMessage
import requests
import json
import os

def load_history(user_id: str):
    """Load user history from MongoDB."""
    try:
        record = chat_collection.find_one({"user_id": user_id})
        if record and "history" in record:
            return record["history"]
        return []
    except Exception as e:
        raise Exception(f"Error loading chat history: {e}")

def save_history(user_id: str, user_message: str, bot_messages: str, audio_url: str = None):
    """Save user history to MongoDB."""
    try:
        messages =load_history(user_id)
        created_at_time=datetime.now(timezone.utc)
        messages.append({"role": "user", "content": user_message, "created_at":created_at_time})
        bot_message = {"role": "bot", "content": bot_messages, "created_at":created_at_time}
        if audio_url:
            bot_message["audio_url"] = audio_url
        messages.append(bot_message)
        chat_collection.update_one({"user_id": user_id}, {"$set": {"history": messages}}, upsert=True)
    except Exception as e:
        raise Exception(f"Error saving chat history: {e}")

async def respond(user_id: str, user_message: str):
    try:
        # Local import to avoid circular dependency with agents.climeai_agent
        from agents.climeai_agent import graph
        config = {"configurable": {"thread_id": user_id}}
        combined_response = ""
        for step in graph.stream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode="values",
            config=config,
            ):
    
            if "messages" in step and step["messages"]:
                last_message = step["messages"][-1]
                if isinstance(last_message, AIMessage) and hasattr(last_message, "content"):
                    combined_response += last_message.content + "\n"
        return combined_response
    except Exception as e:
        raise Exception(f"Error generating response: {e}")

def get_coordinates(city_name: str) -> dict:
    """
    Retrieve latitude and longitude for a given city using OpenCageData Geocoding API.
    
    Args:
        city_name (str): Name of the city to geocode.
    
    Returns:
        dict: Dictionary containing latitude and longitude, or an error message.
    """
    opencage_api_key = os.getenv("OPENCAGE_API_KEY")
    if not opencage_api_key:
        raise ValueError("OpenCage API key not found in environment variables.")
    
    url = f"https://api.opencagedata.com/geocode/v1/json?q={city_name}&key={opencage_api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                latitude = results[0]["geometry"]["lat"]
                longitude = results[0]["geometry"]["lng"]
                return {"latitude": latitude, "longitude": longitude}
            else:
                return {"error": "No results found for the provided city."}
        else:
            return {"error": f"Request failed with status code {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Error making geocoding API call: {e}"}
