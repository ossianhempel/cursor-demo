import pytest
import requests
from unittest.mock import patch, Mock
from weather_api import (
    fetch_weather_data, 
    extract_weather_info, 
    get_weather_for_location,
    WeatherAPIError
)


# Mock data for testing
MOCK_WEATHER_RESPONSE = {
    "location": {
        "name": "London",
        "region": "City of London, Greater London",
        "country": "United Kingdom",
        "lat": 51.52,
        "lon": -0.11,
        "localtime": "2023-12-07 15:30"
    },
    "current": {
        "temp_c": 8.0,
        "temp_f": 46.4,
        "condition": {
            "text": "Partly cloudy",
            "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png"
        },
        "humidity": 82,
        "wind_kph": 11.2,
        "wind_mph": 7.0,
        "wind_dir": "WSW",
        "pressure_mb": 1015.0,
        "pressure_in": 29.97,
        "feelslike_c": 6.1,
        "feelslike_f": 43.0,
        "vis_km": 10.0,
        "vis_miles": 6.0,
        "uv": 2.0
    }
}


class TestFetchWeatherData:
    """Test cases for fetch_weather_data function."""
    
    def test_fetch_weather_data_success(self):
        """Test successful weather data fetch."""
        with patch('weather_api.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_WEATHER_RESPONSE
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = fetch_weather_data("London")
            
            assert result == MOCK_WEATHER_RESPONSE
            mock_get.assert_called_once()
            
    def test_fetch_weather_data_empty_location(self):
        """Test fetch with empty location raises ValueError."""
        with pytest.raises(ValueError, match="Location cannot be empty"):
            fetch_weather_data("")
            
        with pytest.raises(ValueError, match="Location cannot be empty"):
            fetch_weather_data("   ")
            
    def test_fetch_weather_data_api_error(self):
        """Test API error response handling."""
        error_response = {
            "error": {
                "code": 1006,
                "message": "No matching location found."
            }
        }
        
        with patch('weather_api.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = error_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with pytest.raises(WeatherAPIError, match="API Error: No matching location found."):
                fetch_weather_data("InvalidLocation123")
                
    def test_fetch_weather_data_timeout(self):
        """Test timeout handling."""
        with patch('weather_api.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            with pytest.raises(WeatherAPIError, match="Request timeout"):
                fetch_weather_data("London")
                
    def test_fetch_weather_data_connection_error(self):
        """Test connection error handling."""
        with patch('weather_api.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()
            
            with pytest.raises(WeatherAPIError, match="Connection error"):
                fetch_weather_data("London")


class TestExtractWeatherInfo:
    """Test cases for extract_weather_info function."""
    
    def test_extract_weather_info_success(self):
        """Test successful weather info extraction."""
        result = extract_weather_info(MOCK_WEATHER_RESPONSE)
        
        expected_keys = [
            'location_name', 'region', 'country', 'latitude', 'longitude',
            'local_time', 'temperature_c', 'temperature_f', 'condition_text',
            'condition_icon', 'humidity', 'wind_speed_kph', 'wind_speed_mph',
            'wind_direction', 'pressure_mb', 'pressure_in', 'feels_like_c',
            'feels_like_f', 'visibility_km', 'visibility_miles', 'uv_index'
        ]
        
        assert all(key in result for key in expected_keys)
        assert result['location_name'] == "London"
        assert result['temperature_c'] == 8.0
        assert result['condition_text'] == "Partly cloudy"
        assert result['humidity'] == 82
        
    def test_extract_weather_info_missing_location(self):
        """Test extraction with missing location data."""
        incomplete_data = {"current": MOCK_WEATHER_RESPONSE["current"]}
        
        with pytest.raises(WeatherAPIError, match="Missing expected field"):
            extract_weather_info(incomplete_data)
            
    def test_extract_weather_info_missing_current(self):
        """Test extraction with missing current weather data."""
        incomplete_data = {"location": MOCK_WEATHER_RESPONSE["location"]}
        
        with pytest.raises(WeatherAPIError, match="Missing expected field"):
            extract_weather_info(incomplete_data)


class TestGetWeatherForLocation:
    """Test cases for get_weather_for_location function."""
    
    def test_get_weather_for_location_integration(self):
        """Test the complete flow from API call to normalized data."""
        with patch('weather_api.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_WEATHER_RESPONSE
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = get_weather_for_location("London")
            
            assert result['location_name'] == "London"
            assert result['temperature_c'] == 8.0
            assert 'latitude' in result
            assert 'longitude' in result 