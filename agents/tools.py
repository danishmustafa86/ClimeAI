import requests
import json
import os
from utils.chat_agent_utils import get_coordinates

def get_current_weather(city_name: str) -> dict:
    """
    Retrieve current weather data for a specific city.
    
    Args:
        city_name (str): Name of the city to get current weather for.
    
    Returns:
        dict: Current weather data in JSON format, or an error message.
    
    Raises:
        ValueError: If the OpenWeatherMap API key is not found.
        Exception: For unexpected errors during the API call.
    """
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        raise ValueError("OpenWeatherMap API key not found in environment variables.")
    
    coords = get_coordinates(city_name)
    if "error" in coords:
        return coords
    
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        'lat': coords["latitude"],
        'lon': coords["longitude"],
        'appid': weather_api_key,
        'units': 'metric',
        'exclude': 'minutely,hourly,daily,alerts'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        print("Current weather data:::", data)
        return data
    except requests.exceptions.RequestException as e:
        return {"error": f"Error making weather API call: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

def get_hourly_weather(city_name: str) -> dict:
    """
    Retrieve hourly weather forecast for a specific city for the current day.
    
    Args:
        city_name (str): Name of the city to get hourly weather for.
    
    Returns:
        dict: Hourly weather forecast data in JSON format, or an error message.
    
    Raises:
        ValueError: If the OpenWeatherMap API key is not found.
        Exception: For unexpected errors during the API call.
    """
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        raise ValueError("OpenWeatherMap API key not found in environment variables.")
    
    coords = get_coordinates(city_name)
    if "error" in coords:
        return coords
    
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        'lat': coords["latitude"],
        'lon': coords["longitude"],
        'appid': weather_api_key,
        'units': 'metric',
        'exclude': 'current,minutely,daily,alerts'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        print("Hourly weather data:::", data)
        return data
    except requests.exceptions.RequestException as e:
        return {"error": f"Error making weather API call: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

def get_daily_forecast(city_name: str) -> dict:
    """
    Retrieve daily weather forecast for a specific city for today and the next 7 days.
    
    Args:
        city_name (str): Name of the city to get daily forecast for.
    
    Returns:
        dict: Daily weather forecast data in JSON format, or an error message.
    
    Raises:
        ValueError: If the OpenWeatherMap API key is not found.
        Exception: For unexpected errors during the API call.
    """
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        raise ValueError("OpenWeatherMap API key not found in environment variables.")
    
    coords = get_coordinates(city_name)
    if "error" in coords:
        return coords
    
    base_url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        'lat': coords["latitude"],
        'lon': coords["longitude"],
        'appid': weather_api_key,
        'units': 'metric',
        'exclude': 'current,minutely,hourly,alerts'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        print("Daily forecast data:::", data)
        return data
    except requests.exceptions.RequestException as e:
        return {"error": f"Error making weather API call: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

weather_fetching_tools = [get_current_weather, get_hourly_weather, get_daily_forecast]