"""
Tests for weather_fetcher module
"""
import pytest
import json
from unittest.mock import patch, Mock
from weather_fetcher import WeatherFetcher, get_current_weather


class TestWeatherFetcher:
    """Test cases for WeatherFetcher class"""
    
    def test_init_without_api_key(self):
        """Test that WeatherFetcher raises ValueError when API key is missing"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="WEATHER_API_KEY not found"):
                WeatherFetcher()
    
    def test_init_with_api_key(self):
        """Test that WeatherFetcher initializes correctly with API key"""
        with patch.dict('os.environ', {'WEATHER_API_KEY': 'test_key'}):
            fetcher = WeatherFetcher()
            assert fetcher.api_key == 'test_key'
            assert fetcher.base_url == "https://api.weatherapi.com/v1/current.json"
    
    @patch('weather_fetcher.requests.get')
    def test_fetch_current_weather_success(self, mock_get):
        """Test successful weather data fetching"""
        # Mock response data for WeatherAPI.com
        mock_response_data = {
            'location': {
                'name': 'London',
                'country': 'United Kingdom',
                'lat': 51.5074,
                'lon': -0.1278,
                'localtime_epoch': 1634567890
            },
            'current': {
                'temp_c': 20.5,
                'temp_f': 68.9,
                'feelslike_c': 19.8,
                'feelslike_f': 67.6,
                'condition': {
                    'text': 'Clear',
                    'icon': 'https://cdn.weatherapi.com/weather/64x64/day/113.png'
                },
                'wind_kph': 12.6,
                'wind_degree': 180,
                'pressure_mb': 1013,
                'humidity': 65,
                'cloud': 0,
                'vis_km': 10.0
            }
        }
        
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test with mock API key
        with patch.dict('os.environ', {'WEATHER_API_KEY': 'test_key'}):
            fetcher = WeatherFetcher()
            result = fetcher.fetch_current_weather('London,UK')
        
        # Assertions
        assert result is not None
        assert result['location'] == 'London'
        assert result['country'] == 'United Kingdom'
        assert result['coordinates']['latitude'] == 51.5074
        assert result['coordinates']['longitude'] == -0.1278
        assert result['weather']['main'] == 'Clear'
        assert result['temperature']['current'] == 20.5
        assert result['pressure'] == 1013
        assert result['humidity'] == 65
        assert result['units'] == 'metric'
        
        # Verify API call was made with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://api.weatherapi.com/v1/current.json"
        assert call_args[1]['params']['q'] == 'London,UK'
        assert call_args[1]['params']['key'] == 'test_key'
        assert call_args[1]['params']['aqi'] == 'no'
    
    @patch('weather_fetcher.requests.get')
    def test_fetch_current_weather_api_error(self, mock_get):
        """Test handling of API request errors"""
        # Setup mock to raise an exception
        mock_get.side_effect = Exception("API Error")
        
        with patch.dict('os.environ', {'WEATHER_API_KEY': 'test_key'}):
            fetcher = WeatherFetcher()
            result = fetcher.fetch_current_weather('InvalidCity')
        
        assert result is None
    
    @patch('weather_fetcher.requests.get')
    def test_fetch_current_weather_invalid_response(self, mock_get):
        """Test handling of invalid response data"""
        # Mock response with missing required fields
        mock_response = Mock()
        mock_response.json.return_value = {'invalid': 'data'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch.dict('os.environ', {'WEATHER_API_KEY': 'test_key'}):
            fetcher = WeatherFetcher()
            result = fetcher.fetch_current_weather('London,UK')
        
        assert result is None


class TestConvenienceFunction:
    """Test cases for the convenience function"""
    
    @patch('weather_fetcher.WeatherFetcher')
    def test_get_current_weather(self, mock_weather_fetcher_class):
        """Test the convenience function get_current_weather"""
        # Setup mock
        mock_fetcher_instance = Mock()
        mock_weather_data = {'location': 'London', 'temperature': {'current': 20.5}}
        mock_fetcher_instance.fetch_current_weather.return_value = mock_weather_data
        mock_weather_fetcher_class.return_value = mock_fetcher_instance
        
        # Test the function
        result = get_current_weather('London,UK', 'imperial')
        
        # Assertions
        assert result == mock_weather_data
        mock_weather_fetcher_class.assert_called_once()
        mock_fetcher_instance.fetch_current_weather.assert_called_once_with('London,UK', 'imperial')


# Integration test (requires actual API key and internet connection)
@pytest.mark.integration
def test_real_api_call():
    """
    Integration test with real API call - only runs if API key is available
    Mark with @pytest.mark.integration and run with: pytest -m integration
    """
    import os
    if not os.getenv('WEATHER_API_KEY'):
        pytest.skip("WEATHER_API_KEY not available for integration test")
    
    result = get_current_weather('London,UK')
    
    if result:  # Only test if API call was successful
        assert 'location' in result
        assert 'temperature' in result
        assert 'weather' in result
        assert isinstance(result['temperature']['current'], (int, float))


if __name__ == "__main__":
    # Run tests with: python -m pytest test_weather_fetcher.py -v
    pytest.main([__file__, '-v']) 