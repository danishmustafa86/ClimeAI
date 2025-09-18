from datetime import datetime
import os
import requests

def get_weather_at_timestamp(longitude: float, latitude: float, time: str) -> str:
    """
    Retrieve weather data for a specific longitude, latitude, and time using OpenWeatherMap One Call API 3.0.

    - Accepts input time as ISO 8601 (e.g., "2024-11-01T10:00:00" or "2024-11-01T10:00:00Z") or Unix timestamp.
    - Always renders the time in the returned string as ISO 8601.

    Args:
        longitude (float): Longitude of the location.
        latitude (float): Latitude of the location.
        time (str): ISO 8601 datetime or Unix timestamp (string or int-like).

    Returns:
        str: Formatted weather information or error message.
    """
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not weather_api_key:
        return "Error: OpenWeatherMap API key not found in environment variables."
    
    # Accept ISO 8601 or Unix timestamp; convert to Unix for API and keep ISO for display
    try:
        iso_display = None
        # ISO input
        if isinstance(time, str) and 'T' in time:
            dt = datetime.fromisoformat(time.replace('Z', '+00:00'))
            unix_timestamp = int(dt.timestamp())
            iso_display = dt.replace(microsecond=0).isoformat()
        else:
            # Unix timestamp input
            unix_timestamp = int(time)
            dt = datetime.utcfromtimestamp(unix_timestamp)
            iso_display = dt.replace(microsecond=0).isoformat() + 'Z'
    except (ValueError, TypeError):
        return (
            f"Error: Invalid time format '{time}'. Provide ISO 8601 (e.g., '2024-11-01T10:00:00Z') "
            f"or a Unix timestamp (e.g., 1643803200)."
        )
    
    base_url = "https://api.openweathermap.org/data/3.0/onecall/timemachine"
    params = {
        'lat': latitude,
        'lon': longitude,
        'dt': unix_timestamp,
        'appid': weather_api_key,
        'units': 'metric'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            weather_data = data['data'][0]
            
            # Format the weather information
            temp = weather_data.get('temp', 'N/A')
            feels_like = weather_data.get('feels_like', 'N/A')
            humidity = weather_data.get('humidity', 'N/A')
            pressure = weather_data.get('pressure', 'N/A')
            wind_speed = weather_data.get('wind_speed', 'N/A')
            wind_deg = weather_data.get('wind_deg', 'N/A')
            clouds = weather_data.get('clouds', 'N/A')
            visibility = weather_data.get('visibility', 'N/A')
            uvi = weather_data.get('uvi', 'N/A')
            
            weather_desc = "Unknown"
            if 'weather' in weather_data and len(weather_data['weather']) > 0:
                weather_desc = weather_data['weather'][0].get('description', 'Unknown')
            
            return (
                f"Weather at ({latitude}, {longitude}) on {iso_display}:\n"
                f"• Temperature: {temp}°C (feels like {feels_like}°C)\n"
                f"• Conditions: {weather_desc}\n"
                f"• Humidity: {humidity}%\n"
                f"• Pressure: {pressure} hPa\n"
                f"• Wind: {wind_speed} m/s at {wind_deg}°\n"
                f"• Cloudiness: {clouds}%\n"
                f"• Visibility: {visibility} m\n"
                f"• UV Index: {uvi}"
            )
        else:
            return f"No weather data available for ({latitude}, {longitude}) at {iso_display}"
            
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"
