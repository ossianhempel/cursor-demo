"""
Weather data fetching module using WeatherAPI.com
"""
import os
import requests
from dotenv import load_dotenv
from typing import Dict, Optional
import json

# Load environment variables
load_dotenv()

class WeatherFetcher:
    """Class for fetching weather data from WeatherAPI.com"""
    
    def __init__(self):
        self.api_key = os.getenv('WEATHER_API_KEY')  # Changed from OPENWEATHER_API_KEY
        self.base_url = "https://api.weatherapi.com/v1/current.json"  # WeatherAPI endpoint
        
        if not self.api_key:
            raise ValueError("WEATHER_API_KEY not found in environment variables")
    
    def fetch_current_weather(self, location: str, units: str = "metric") -> Optional[Dict]:
        """
        Fetch current weather data for a given location
        
        Args:
            location (str): City name, state code and country code divided by comma
            units (str): Temperature units (metric, imperial, kelvin) - Note: WeatherAPI returns both C and F
            
        Returns:
            Dict: Weather data dictionary or None if request fails
        """
        try:
            params = {
                'key': self.api_key,  # WeatherAPI uses 'key' parameter
                'q': location,
                'aqi': 'no'  # Don't include air quality data
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Extract and structure the relevant data from WeatherAPI response
            current = weather_data['current']
            location_data = weather_data['location']
            
            # Convert temperature based on units preference
            if units == "metric":
                temp_current = current['temp_c']
                temp_feels_like = current['feelslike_c']
            elif units == "imperial":
                temp_current = current['temp_f']
                temp_feels_like = current['feelslike_f']
            else:  # kelvin
                temp_current = current['temp_c'] + 273.15
                temp_feels_like = current['feelslike_c'] + 273.15
            
            structured_data = {
                'location': location_data['name'],
                'country': location_data['country'],
                'coordinates': {
                    'latitude': location_data['lat'],
                    'longitude': location_data['lon']
                },
                'weather': {
                    'main': current['condition']['text'],
                    'description': current['condition']['text'],
                    'icon': current['condition']['icon'].split('/')[-1].replace('.png', '')  # Extract icon code
                },
                'temperature': {
                    'current': temp_current,
                    'feels_like': temp_feels_like,
                    'min': temp_current,  # WeatherAPI doesn't provide min/max in current, using current
                    'max': temp_current
                },
                'pressure': current.get('pressure_mb', None),
                'humidity': current.get('humidity', None),
                'visibility': current.get('vis_km', None) * 1000 if current.get('vis_km') else None,  # Convert km to meters
                'wind': {
                    'speed': current.get('wind_kph', None) / 3.6 if current.get('wind_kph') else None,  # Convert kph to m/s
                    'direction': current.get('wind_degree', None)
                },
                'clouds': current.get('cloud', None),
                'timestamp': location_data.get('localtime_epoch', None),
                'timezone': None,  # WeatherAPI doesn't provide timezone offset directly
                'units': units
            }
            
            return structured_data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None
        except KeyError as e:
            print(f"Error parsing weather data: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

# Convenience function for direct usage
def get_current_weather(location: str, units: str = "metric") -> Optional[Dict]:
    """
    Convenience function to fetch current weather data
    
    Args:
        location (str): City name, state code and country code divided by comma
        units (str): Temperature units (metric, imperial, kelvin)
        
    Returns:
        Dict: Weather data dictionary or None if request fails
    """
    fetcher = WeatherFetcher()
    return fetcher.fetch_current_weather(location, units)

if __name__ == "__main__":
    # Example usage
    weather = get_current_weather("London,UK")
    if weather:
        print(json.dumps(weather, indent=2))
    else:
        print("Failed to fetch weather data") 