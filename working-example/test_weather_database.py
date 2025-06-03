import pytest
import os
import tempfile
from datetime import datetime, timedelta
from weather_database import WeatherDatabase, store_weather_data


# Sample weather data for testing
SAMPLE_WEATHER_DATA = {
    'location_name': 'London',
    'region': 'City of London, Greater London',
    'country': 'United Kingdom',
    'latitude': 51.52,
    'longitude': -0.11,
    'local_time': '2023-12-07 15:30',
    'temperature_c': 8.0,
    'temperature_f': 46.4,
    'condition_text': 'Partly cloudy',
    'condition_icon': '//cdn.weatherapi.com/weather/64x64/day/116.png',
    'humidity': 82,
    'wind_speed_kph': 11.2,
    'wind_speed_mph': 7.0,
    'wind_direction': 'WSW',
    'pressure_mb': 1015.0,
    'pressure_in': 29.97,
    'feels_like_c': 6.1,
    'feels_like_f': 43.0,
    'visibility_km': 10.0,
    'visibility_miles': 6.0,
    'uv_index': 2.0
}


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create a temporary file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)  # Close the file descriptor
    
    yield db_path
    
    # Clean up the temporary file
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def weather_db(temp_db):
    """Create a WeatherDatabase instance with temporary database."""
    return WeatherDatabase(temp_db)


class TestWeatherDatabase:
    """Test cases for WeatherDatabase class."""
    
    def test_database_initialization(self, weather_db):
        """Test that database initializes correctly with proper schema."""
        # Check that the database file was created
        assert os.path.exists(weather_db.db_path)
        
        # Check that the weather_records table exists
        with weather_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='weather_records'
            """)
            table_exists = cursor.fetchone()
            assert table_exists is not None
    
    def test_upsert_new_weather_data(self, weather_db):
        """Test inserting new weather data."""
        record_id = weather_db.upsert_weather_data(SAMPLE_WEATHER_DATA)
        
        assert record_id is not None
        assert record_id > 0
        
        # Verify the data was inserted correctly
        record = weather_db.get_latest_weather_by_location('London')
        assert record is not None
        assert record['location_name'] == 'London'
        assert record['temperature_c'] == 8.0
        assert record['humidity'] == 82
    
    def test_upsert_update_existing_weather_data(self, weather_db):
        """Test updating existing weather data."""
        # Insert initial data
        initial_id = weather_db.upsert_weather_data(SAMPLE_WEATHER_DATA)
        
        # Update the temperature
        updated_data = SAMPLE_WEATHER_DATA.copy()
        updated_data['temperature_c'] = 12.0
        updated_data['temperature_f'] = 53.6
        
        # Upsert should update the existing record
        updated_id = weather_db.upsert_weather_data(updated_data)
        
        assert updated_id == initial_id  # Should be the same record
        
        # Verify the update
        record = weather_db.get_latest_weather_by_location('London')
        assert record['temperature_c'] == 12.0
        assert record['temperature_f'] == 53.6
    
    def test_get_weather_by_location(self, weather_db):
        """Test retrieving weather data by location."""
        # Insert multiple records for the same location
        weather_db.upsert_weather_data(SAMPLE_WEATHER_DATA)
        
        # Insert data for a different location
        paris_data = SAMPLE_WEATHER_DATA.copy()
        paris_data['location_name'] = 'Paris'
        weather_db.upsert_weather_data(paris_data)
        
        # Get London data
        london_records = weather_db.get_weather_by_location('London')
        assert len(london_records) == 1
        assert london_records[0]['location_name'] == 'London'
        
        # Get Paris data
        paris_records = weather_db.get_weather_by_location('Paris')
        assert len(paris_records) == 1
        assert paris_records[0]['location_name'] == 'Paris'
    
    def test_get_latest_weather_by_location(self, weather_db):
        """Test getting the most recent weather data for a location."""
        # Insert data
        weather_db.upsert_weather_data(SAMPLE_WEATHER_DATA)
        
        # Get latest record
        latest = weather_db.get_latest_weather_by_location('London')
        assert latest is not None
        assert latest['location_name'] == 'London'
        
        # Test non-existent location
        no_record = weather_db.get_latest_weather_by_location('NonExistentCity')
        assert no_record is None
    
    def test_get_all_locations(self, weather_db):
        """Test getting all unique locations."""
        # Insert data for multiple locations
        locations = ['London', 'Paris', 'New York', 'Tokyo']
        
        for location in locations:
            data = SAMPLE_WEATHER_DATA.copy()
            data['location_name'] = location
            weather_db.upsert_weather_data(data)
        
        all_locations = weather_db.get_all_locations()
        assert len(all_locations) == 4
        assert set(all_locations) == set(locations)
    
    def test_get_all_weather_records(self, weather_db):
        """Test getting all weather records."""
        # Insert data for multiple locations
        for i, location in enumerate(['London', 'Paris', 'Tokyo']):
            data = SAMPLE_WEATHER_DATA.copy()
            data['location_name'] = location
            data['temperature_c'] = 10.0 + i
            weather_db.upsert_weather_data(data)
        
        all_records = weather_db.get_all_weather_records()
        assert len(all_records) == 3
        
        # Should be ordered by created_at DESC (most recent first)
        locations_in_order = [record['location_name'] for record in all_records]
        assert 'Tokyo' in locations_in_order  # Most recently inserted
    
    def test_delete_old_records(self, weather_db):
        """Test deleting old weather records."""
        # Insert current data
        weather_db.upsert_weather_data(SAMPLE_WEATHER_DATA)
        
        # Manually insert old data by modifying the database
        old_date = (datetime.now() - timedelta(days=40)).isoformat()
        
        with weather_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weather_records (
                    location_name, region, country, temperature_c, humidity,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('OldCity', 'OldRegion', 'OldCountry', 20.0, 50, old_date, old_date))
            conn.commit()
        
        # Delete records older than 30 days
        deleted_count = weather_db.delete_old_records(30)
        assert deleted_count == 1
        
        # Verify only current data remains
        all_records = weather_db.get_all_weather_records()
        assert len(all_records) == 1
        assert all_records[0]['location_name'] == 'London'


class TestStoreWeatherDataFunction:
    """Test cases for the convenience store_weather_data function."""
    
    def test_store_weather_data_function(self, temp_db):
        """Test the convenience function for storing weather data."""
        record_id = store_weather_data(SAMPLE_WEATHER_DATA, temp_db)
        
        assert record_id is not None
        assert record_id > 0
        
        # Verify data was stored correctly
        db = WeatherDatabase(temp_db)
        record = db.get_latest_weather_by_location('London')
        assert record is not None
        assert record['location_name'] == 'London' 