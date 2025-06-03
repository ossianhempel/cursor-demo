import os
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
WEATHER_API_BASE_URL = 'https://api.weatherapi.com/v1/current.json'

if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY environment variable is required. Please set it in your .env file.") 