import requests
import json
import os
from utils.chat_agent_utils import get_coordinates
from agents.agent_utils import get_weather_at_timestamp
from langchain_core.tools import tool

@tool
def get_current_weather(city_name: str) -> str:
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
    print("Tool: get_current_weather Called")
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        raise ValueError("OpenWeatherMap API key not found in environment variables.")
    
    coords = get_coordinates(city_name)
    if isinstance(coords, dict) and "error" in coords:
        return f"error: {coords['error']}"
    
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
        data = f"""Weather Data: {data}"""
        print("Current weather data:::", data)
        return data
    except requests.exceptions.RequestException as e:
        return f"error: Error making weather API call: {e}"
    except Exception as e:
        return f"error: An unexpected error occurred: {e}"

@tool
def get_hourly_weather(city_name: str) -> str:
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
    print("Tool: get_hourly_weather Called")
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        raise ValueError("OpenWeatherMap API key not found in environment variables.")
    
    coords = get_coordinates(city_name)
    if isinstance(coords, dict) and "error" in coords:
        return f"error: {coords['error']}"
    
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
        data = f"""Weather Data: \n {data}"""
        print("Hourly weather data:::", data)
        return data
    except requests.exceptions.RequestException as e:
        return f"error: Error making weather API call: {e}"
    except Exception as e:
        return f"error: An unexpected error occurred: {e}"

@tool
def get_daily_forecast(city_name: str) -> str:
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
    print("Tool: get_daily_forecast Called")
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
        data = f"""Weather Data: \n {data}"""
        print("Daily forecast data:::", data)
        return data
    except requests.exceptions.RequestException as e:
        return f"error: Error making weather API call: {e}"
    except Exception as e:
        return f"error: An unexpected error occurred: {e}"

@tool
def get_weather_at_specific_time(city_name: str, time_iso: str) -> str:
    """
    Retrieve weather for a city at a specific time (ISO 8601),
    converting to coordinates and timestamp under the hood.

    Args:
        city_name (str): City to geocode.
        time_iso (str): ISO 8601 datetime (e.g., "2025-09-21T17:00:00Z").

    Returns:
        str: Human-readable weather summary, or error message.
    """
    print("Tool: get_weather_at_specific_time Called")
    coords = get_coordinates(city_name)
    
    try:
        longitude = coords["longitude"]
        latitude = coords["latitude"]
    except Exception:
        return "Error: Unable to resolve coordinates for the provided city."

    data = get_weather_at_timestamp(longitude, latitude, time_iso)
    data = f"""Weather Data: \n {data}"""
    return data
weather_fetching_tools = [get_current_weather, get_hourly_weather, get_daily_forecast, get_weather_at_specific_time]


# if __name__ == "__main__":
#     import sys
#     import pprint

#     city = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TEST_CITY", "Seattle")
#     print(f"Testing weather tools for city: {city}\n")

#     try:
#         print("== get_current_weather ==")
#         current_str = get_current_weather(city)
#         print(current_str)
#     except Exception as e:
#         print("get_current_weather error:", e)

#     print()
#     try:
#         print("== get_hourly_weather ==")
#         hourly_str = get_hourly_weather(city)
#         print(hourly_str)
#     except Exception as e:
#         print("get_hourly_weather error:", e)

#     print()
#     try:
#         print("== get_daily_forecast ==")
#         daily = get_daily_forecast(city)
#         daily_list = daily.get("daily") if isinstance(daily, dict) else None
#         print("daily count:", len(daily_list) if isinstance(daily_list, list) else "N/A")
#         if isinstance(daily_list, list) and daily_list:
#             first = daily_list[0]
#             first_dt = first.get("dt")
#             tz_offset_seconds = int((first.get("timezone_offset") or 0)) if isinstance(first, dict) else 0
#             print(json.dumps(first, indent=2)[:500])
#     except Exception as e:
#         print("get_daily_forecast error:", e)

#     print()
#     try:
#         print("== get_weather_at_specific_time ==")
#         iso_time = sys.argv[2] if len(sys.argv) > 2 else os.getenv("TEST_ISO_TIME", "2025-09-21T17:00:00Z")
#         summary = get_weather_at_specific_time(city, iso_time)
#         print(summary)
#     except Exception as e:
#         print("get_weather_at_specific_time error:", e)

#     print("\nDone.")