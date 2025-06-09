"""
Tests for weather_database module
"""
import pytest
import os
import tempfile
from datetime import datetime
from weather_database import WeatherDatabase, save_weather_data, upsert_weather_data

# Sample weather data for testing
SAMPLE_WEATHER_DATA = {
    'location': 'London',
    'country': 'GB',
    'coordinates': {
        'latitude': 51.5074,
        'longitude': -0.1278
    },
    'weather': {
        'main': 'Clear',
        'description': 'clear sky',
        'icon': '01d'
    },
    'temperature': {
        'current': 20.5,
        'feels_like': 19.8,
        'min': 18.0,
        'max': 23.0
    },
    'pressure': 1013,
    'humidity': 65,
    'visibility': 10000,
    'wind': {
        'speed': 3.5,
        'direction': 180
    },
    'clouds': 75,
    'timestamp': 1634567890,
    'timezone': 3600,
    'units': 'metric'
}

class TestWeatherDatabase:
    """Test cases for WeatherDatabase class"""
    
    def setup_method(self):
        """Setup for each test - create temporary database"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.db_path = self.temp_file.name
        self.db = WeatherDatabase(self.db_path)
    
    def teardown_method(self):
        """Cleanup after each test"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_database_initialization(self):
        """Test that database tables are created correctly"""
        # Check that database file exists
        assert os.path.exists(self.db_path)
        
        # Check that tables exist
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'locations' in tables
            assert 'weather_records' in tables
    
    def test_insert_weather_record(self):
        """Test inserting a weather record"""
        record_id = self.db.insert_weather_record(SAMPLE_WEATHER_DATA)
        
        assert record_id is not None
        assert isinstance(record_id, int)
        assert record_id > 0
        
        # Verify the record was inserted
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM weather_records WHERE id = ?", (record_id,))
            record = cursor.fetchone()
            
            assert record is not None
            assert record['location'] == SAMPLE_WEATHER_DATA['location']
            assert record['country'] == SAMPLE_WEATHER_DATA['country']
            assert record['temperature_current'] == SAMPLE_WEATHER_DATA['temperature']['current']
    
    def test_location_creation_and_reuse(self):
        """Test that locations are created and reused correctly"""
        # Insert first record
        record_id1 = self.db.insert_weather_record(SAMPLE_WEATHER_DATA)
        
        # Insert second record for same location
        modified_data = SAMPLE_WEATHER_DATA.copy()
        modified_data['temperature']['current'] = 25.0
        record_id2 = self.db.insert_weather_record(modified_data)
        
        # Both records should exist
        assert record_id1 != record_id2
        
        # But should reference the same location
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT location_id FROM weather_records WHERE id IN (?, ?)", (record_id1, record_id2))
            location_ids = [row[0] for row in cursor.fetchall()]
            
            assert len(set(location_ids)) == 1  # Both records have same location_id
            
        # Check location record count is updated
        locations = self.db.get_all_locations()
        assert len(locations) == 1
        assert locations[0]['record_count'] == 2
    
    def test_upsert_functionality_insert(self):
        """Test upsert operation when no existing record"""
        record_id, was_inserted = self.db.upsert_weather_record(SAMPLE_WEATHER_DATA)
        
        assert record_id is not None
        assert was_inserted is True
        
        # Verify record exists
        records = self.db.get_latest_weather_records(1)
        assert len(records) == 1
        assert records[0]['id'] == record_id
    
    def test_upsert_functionality_update(self):
        """Test upsert operation when existing record should be updated"""
        # Insert initial record
        record_id1, was_inserted1 = self.db.upsert_weather_record(SAMPLE_WEATHER_DATA)
        assert was_inserted1 is True
        
        # Create slightly newer data (within 1 hour)
        newer_data = SAMPLE_WEATHER_DATA.copy()
        newer_data['timestamp'] = SAMPLE_WEATHER_DATA['timestamp'] + 1800  # 30 minutes later
        newer_data['temperature']['current'] = 25.0  # Different temperature
        
        # Upsert should update existing record
        record_id2, was_inserted2 = self.db.upsert_weather_record(newer_data)
        
        assert record_id2 == record_id1  # Same record ID
        assert was_inserted2 is False     # Was updated, not inserted
        
        # Verify temperature was updated
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT temperature_current FROM weather_records WHERE id = ?", (record_id1,))
            temp = cursor.fetchone()[0]
            assert temp == 25.0
    
    def test_upsert_functionality_new_record_after_time_gap(self):
        """Test upsert creates new record when time gap is large"""
        # Insert initial record
        record_id1, was_inserted1 = self.db.upsert_weather_record(SAMPLE_WEATHER_DATA)
        assert was_inserted1 is True
        
        # Create data from 2 hours later (outside 1-hour window)
        later_data = SAMPLE_WEATHER_DATA.copy()
        later_data['timestamp'] = SAMPLE_WEATHER_DATA['timestamp'] + 7200  # 2 hours later
        later_data['temperature']['current'] = 25.0
        
        # Should create new record
        record_id2, was_inserted2 = self.db.upsert_weather_record(later_data)
        
        assert record_id2 != record_id1  # Different record ID
        assert was_inserted2 is True      # Was inserted, not updated
        
        # Verify both records exist
        records = self.db.get_latest_weather_records(10)
        assert len(records) == 2

class TestDatabaseQueries:
    """Test database query functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.db_path = self.temp_file.name
        self.db = WeatherDatabase(self.db_path)
        
        # Insert test data
        self.db.insert_weather_record(SAMPLE_WEATHER_DATA)
        
        # Insert data for different location
        paris_data = SAMPLE_WEATHER_DATA.copy()
        paris_data['location'] = 'Paris'
        paris_data['country'] = 'FR'
        paris_data['coordinates'] = {'latitude': 48.8566, 'longitude': 2.3522}
        self.db.insert_weather_record(paris_data)
    
    def teardown_method(self):
        """Cleanup after each test"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_get_latest_weather_records(self):
        """Test retrieving latest weather records"""
        records = self.db.get_latest_weather_records(5)
        
        assert len(records) == 2
        assert records[0]['created_at'] >= records[1]['created_at']  # Most recent first
    
    def test_get_weather_by_location(self):
        """Test retrieving weather by location"""
        london_records = self.db.get_weather_by_location('London', 'GB')
        paris_records = self.db.get_weather_by_location('Paris', 'FR')
        
        assert len(london_records) == 1
        assert len(paris_records) == 1
        assert london_records[0]['location'] == 'London'
        assert paris_records[0]['location'] == 'Paris'
    
    def test_get_all_locations(self):
        """Test retrieving all locations"""
        locations = self.db.get_all_locations()
        
        assert len(locations) == 2
        location_names = [loc['location_name'] for loc in locations]
        assert 'London' in location_names
        assert 'Paris' in location_names
    
    def test_get_database_stats(self):
        """Test database statistics"""
        stats = self.db.get_database_stats()
        
        assert 'total_records' in stats
        assert 'total_locations' in stats
        assert 'earliest_record' in stats
        assert 'latest_record' in stats
        
        assert stats['total_records'] == 2
        assert stats['total_locations'] == 2

class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.db_path = self.temp_file.name
    
    def teardown_method(self):
        """Cleanup after each test"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_save_weather_data_function(self):
        """Test save_weather_data convenience function"""
        record_id = save_weather_data(SAMPLE_WEATHER_DATA, self.db_path)
        
        assert record_id is not None
        assert isinstance(record_id, int)
        
        # Verify record was saved
        db = WeatherDatabase(self.db_path)
        records = db.get_latest_weather_records(1)
        assert len(records) == 1
        assert records[0]['id'] == record_id
    
    def test_upsert_weather_data_function(self):
        """Test upsert_weather_data convenience function"""
        record_id1, was_inserted1 = upsert_weather_data(SAMPLE_WEATHER_DATA, self.db_path)
        
        assert was_inserted1 is True
        
        # Try upserting again with recent timestamp
        modified_data = SAMPLE_WEATHER_DATA.copy()
        modified_data['timestamp'] = SAMPLE_WEATHER_DATA['timestamp'] + 1800  # 30 min later
        modified_data['temperature']['current'] = 25.0
        
        record_id2, was_inserted2 = upsert_weather_data(modified_data, self.db_path)
        
        assert record_id2 == record_id1
        assert was_inserted2 is False

if __name__ == "__main__":
    # Run tests with: python -m pytest test_weather_database.py -v
    pytest.main([__file__, '-v']) 