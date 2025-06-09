"""
Weather data pipeline - Integration module that combines fetching and database operations
"""
from typing import Dict, List, Optional, Tuple
import time
from weather_fetcher import WeatherFetcher, get_current_weather
from weather_database import WeatherDatabase, upsert_weather_data
import json

class WeatherPipeline:
    """Complete weather data pipeline with fetching and storage"""
    
    def __init__(self, db_path: str = "weather_data.db"):
        """
        Initialize the weather pipeline
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.weather_fetcher = WeatherFetcher()
        self.database = WeatherDatabase(db_path)
    
    def fetch_and_store_weather(self, location: str, units: str = "metric") -> Tuple[Optional[int], bool, Optional[Dict]]:
        """
        Fetch weather data and store it in the database
        
        Args:
            location (str): City name, state code and country code divided by comma
            units (str): Temperature units (metric, imperial, kelvin)
            
        Returns:
            Tuple[Optional[int], bool, Optional[Dict]]: (record_id, was_inserted, weather_data)
                - record_id: Database record ID if successful, None if failed
                - was_inserted: True if new record, False if updated existing
                - weather_data: The fetched weather data dictionary
        """
        try:
            # Fetch weather data
            weather_data = self.weather_fetcher.fetch_current_weather(location, units)
            
            if not weather_data:
                print(f"Failed to fetch weather data for {location}")
                return None, False, None
            
            # Store in database (upsert operation)
            record_id, was_inserted = self.database.upsert_weather_record(weather_data)
            
            action = "Inserted" if was_inserted else "Updated"
            print(f"{action} weather record for {weather_data['location']}, {weather_data['country']} (ID: {record_id})")
            
            return record_id, was_inserted, weather_data
            
        except Exception as e:
            print(f"Error in weather pipeline for {location}: {e}")
            return None, False, None
    
    def batch_fetch_and_store(self, locations: List[str], units: str = "metric", delay: float = 1.0) -> List[Dict]:
        """
        Fetch and store weather data for multiple locations
        
        Args:
            locations (List[str]): List of location strings
            units (str): Temperature units
            delay (float): Delay between API calls to avoid rate limiting
            
        Returns:
            List[Dict]: List of results with success/failure info
        """
        results = []
        
        for location in locations:
            result = {
                'location': location,
                'success': False,
                'record_id': None,
                'was_inserted': False,
                'weather_data': None,
                'error': None
            }
            
            try:
                record_id, was_inserted, weather_data = self.fetch_and_store_weather(location, units)
                
                if record_id:
                    result['success'] = True
                    result['record_id'] = record_id
                    result['was_inserted'] = was_inserted
                    result['weather_data'] = weather_data
                else:
                    result['error'] = "Failed to fetch or store weather data"
                    
            except Exception as e:
                result['error'] = str(e)
            
            results.append(result)
            
            # Add delay to avoid API rate limiting
            if delay > 0 and location != locations[-1]:  # Don't delay after last item
                time.sleep(delay)
        
        return results
    
    def get_weather_summary(self, location: str, country: str = None) -> Dict:
        """
        Get a summary of weather data for a location
        
        Args:
            location (str): Location name
            country (str): Country code (optional)
            
        Returns:
            Dict: Weather summary with recent data and statistics
        """
        records = self.database.get_weather_by_location(location, country, limit=10)
        
        if not records:
            return {
                'location': location,
                'country': country,
                'records_found': 0,
                'message': 'No weather data found for this location'
            }
        
        latest_record = records[0]
        
        # Calculate basic statistics if we have multiple records
        if len(records) > 1:
            temperatures = [r['temperature_current'] for r in records]
            humidity_values = [r['humidity'] for r in records if r['humidity']]
            
            temp_stats = {
                'avg_temperature': sum(temperatures) / len(temperatures),
                'min_temperature': min(temperatures),
                'max_temperature': max(temperatures)
            }
            
            if humidity_values:
                temp_stats['avg_humidity'] = sum(humidity_values) / len(humidity_values)
        else:
            temp_stats = {}
        
        return {
            'location': latest_record['location'],
            'country': latest_record['country'],
            'records_found': len(records),
            'latest_record': latest_record,
            'statistics': temp_stats,
            'all_records': records
        }

# Convenience functions for direct usage
def fetch_and_store_weather(location: str, units: str = "metric", db_path: str = "weather_data.db") -> Tuple[Optional[int], bool, Optional[Dict]]:
    """
    Convenience function to fetch and store weather data
    
    Args:
        location (str): City name, state code and country code divided by comma
        units (str): Temperature units
        db_path (str): Database file path
        
    Returns:
        Tuple[Optional[int], bool, Optional[Dict]]: (record_id, was_inserted, weather_data)
    """
    pipeline = WeatherPipeline(db_path)
    return pipeline.fetch_and_store_weather(location, units)

def batch_weather_update(locations: List[str], units: str = "metric", db_path: str = "weather_data.db") -> List[Dict]:
    """
    Convenience function for batch weather updates
    
    Args:
        locations (List[str]): List of location strings
        units (str): Temperature units
        db_path (str): Database file path
        
    Returns:
        List[Dict]: List of results
    """
    pipeline = WeatherPipeline(db_path)
    return pipeline.batch_fetch_and_store(locations, units)

if __name__ == "__main__":
    # Example usage
    pipeline = WeatherPipeline()
    
    # Test with a few major cities
    test_locations = [
        "London,UK",
        "New York,US",
        "Tokyo,JP",
        "Sydney,AU"
    ]
    
    print("Starting batch weather data collection...")
    results = pipeline.batch_fetch_and_store(test_locations, delay=0.5)
    
    print("\n=== Results Summary ===")
    for result in results:
        if result['success']:
            weather = result['weather_data']
            print(f"✅ {result['location']}: {weather['temperature']['current']}°C, {weather['weather']['description']}")
        else:
            print(f"❌ {result['location']}: {result['error']}")
    
    print(f"\n=== Database Stats ===")
    stats = pipeline.database.get_database_stats()
 