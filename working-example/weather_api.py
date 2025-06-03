import requests
from typing import Dict, Any, Optional
from config import WEATHER_API_KEY, WEATHER_API_BASE_URL


class WeatherAPIError(Exception):
    """Custom exception for weather API related errors."""
    pass


def fetch_weather_data(location: str) -> Dict[str, Any]:
    """
    Fetch current weather data for a given location using weatherapi.com.
    
    Args:
        location (str): The location to fetch weather for (city name, coordinates, etc.)
        
    Returns:
        Dict[str, Any]: Weather data containing location and current weather info
        
    Raises:
        WeatherAPIError: If the API request fails or returns an error
        ValueError: If location is empty or invalid
    """
    if not location or not location.strip():
        raise ValueError("Location cannot be empty")
    
    params = {
        'key': WEATHER_API_KEY,
        'q': location.strip(),
        'aqi': 'no'  # We don't need air quality data for this demo
    }
    
    try:
        response = requests.get(WEATHER_API_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if the API returned an error
        if 'error' in data:
            raise WeatherAPIError(f"API Error: {data['error']['message']}")
            
        return data
        
    except requests.exceptions.Timeout:
        raise WeatherAPIError("Request timeout - the weather service is taking too long to respond")
    except requests.exceptions.ConnectionError:
        raise WeatherAPIError("Connection error - unable to reach the weather service")
    except requests.exceptions.HTTPError as e:
        raise WeatherAPIError(f"HTTP error {e.response.status_code}: {e.response.text}")
    except requests.exceptions.RequestException as e:
        raise WeatherAPIError(f"Request failed: {str(e)}")
    except ValueError as e:
        raise WeatherAPIError(f"Invalid response format: {str(e)}")


def extract_weather_info(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and normalize relevant weather information from the API response.
    
    Args:
        weather_data (Dict[str, Any]): Raw weather data from the API
        
    Returns:
        Dict[str, Any]: Normalized weather information
    """
    try:
        location = weather_data['location']
        current = weather_data['current']
        
        return {
            'location_name': location['name'],
            'region': location['region'],
            'country': location['country'],
            'latitude': location['lat'],
            'longitude': location['lon'],
            'local_time': location['localtime'],
            'temperature_c': current['temp_c'],
            'temperature_f': current['temp_f'],
            'condition_text': current['condition']['text'],
            'condition_icon': current['condition']['icon'],
            'humidity': current['humidity'],
            'wind_speed_kph': current['wind_kph'],
            'wind_speed_mph': current['wind_mph'],
            'wind_direction': current['wind_dir'],
            'pressure_mb': current['pressure_mb'],
            'pressure_in': current['pressure_in'],
            'feels_like_c': current['feelslike_c'],
            'feels_like_f': current['feelslike_f'],
            'visibility_km': current['vis_km'],
            'visibility_miles': current['vis_miles'],
            'uv_index': current['uv']
        }
    except KeyError as e:
        raise WeatherAPIError(f"Missing expected field in weather data: {str(e)}")


def get_weather_for_location(location: str) -> Dict[str, Any]:
    """
    High-level function to get normalized weather data for a location.
    
    Args:
        location (str): The location to fetch weather for
        
    Returns:
        Dict[str, Any]: Normalized weather information
    """
    raw_data = fetch_weather_data(location)
    return extract_weather_info(raw_data) 