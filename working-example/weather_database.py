import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from contextlib import contextmanager


class WeatherDatabase:
    """SQLite database manager for weather data."""
    
    def __init__(self, db_path: str = "weather_data.db"):
        """
        Initialize the weather database.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create the weather_records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_name TEXT NOT NULL,
                    region TEXT,
                    country TEXT,
                    latitude REAL,
                    longitude REAL,
                    local_time TEXT,
                    temperature_c REAL,
                    temperature_f REAL,
                    condition_text TEXT,
                    condition_icon TEXT,
                    humidity INTEGER,
                    wind_speed_kph REAL,
                    wind_speed_mph REAL,
                    wind_direction TEXT,
                    pressure_mb REAL,
                    pressure_in REAL,
                    feels_like_c REAL,
                    feels_like_f REAL,
                    visibility_km REAL,
                    visibility_miles REAL,
                    uv_index REAL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_location_name 
                ON weather_records(location_name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON weather_records(created_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_location_time 
                ON weather_records(location_name, created_at)
            """)
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        try:
            yield conn
        finally:
            conn.close()
    
    def upsert_weather_data(self, weather_data: Dict[str, Any]) -> int:
        """
        Insert or update weather data for a location.
        
        Args:
            weather_data (Dict[str, Any]): Weather data dictionary from the API
            
        Returns:
            int: The ID of the inserted/updated record
        """
        now = datetime.now().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if we have recent data for this location (within the last hour)
            cursor.execute("""
                SELECT id, created_at FROM weather_records 
                WHERE location_name = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (weather_data['location_name'],))
            
            existing_record = cursor.fetchone()
            
            # Only update if the last record is within the last hour, otherwise create new record
            should_update = False
            if existing_record:
                last_update = datetime.fromisoformat(existing_record['created_at'])
                time_diff = datetime.now() - last_update
                should_update = time_diff.total_seconds() < 3600  # 1 hour
            
            if should_update:
                # Update existing record
                cursor.execute("""
                    UPDATE weather_records SET
                        region = ?, country = ?, latitude = ?, longitude = ?,
                        local_time = ?, temperature_c = ?, temperature_f = ?,
                        condition_text = ?, condition_icon = ?, humidity = ?,
                        wind_speed_kph = ?, wind_speed_mph = ?, wind_direction = ?,
                        pressure_mb = ?, pressure_in = ?, feels_like_c = ?,
                        feels_like_f = ?, visibility_km = ?, visibility_miles = ?,
                        uv_index = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    weather_data['region'], weather_data['country'],
                    weather_data['latitude'], weather_data['longitude'],
                    weather_data['local_time'], weather_data['temperature_c'],
                    weather_data['temperature_f'], weather_data['condition_text'],
                    weather_data['condition_icon'], weather_data['humidity'],
                    weather_data['wind_speed_kph'], weather_data['wind_speed_mph'],
                    weather_data['wind_direction'], weather_data['pressure_mb'],
                    weather_data['pressure_in'], weather_data['feels_like_c'],
                    weather_data['feels_like_f'], weather_data['visibility_km'],
                    weather_data['visibility_miles'], weather_data['uv_index'],
                    now, existing_record['id']
                ))
                record_id = existing_record['id']
            else:
                # Insert new record (either no existing record or last one is older than 1 hour)
                cursor.execute("""
                    INSERT INTO weather_records (
                        location_name, region, country, latitude, longitude,
                        local_time, temperature_c, temperature_f, condition_text,
                        condition_icon, humidity, wind_speed_kph, wind_speed_mph,
                        wind_direction, pressure_mb, pressure_in, feels_like_c,
                        feels_like_f, visibility_km, visibility_miles, uv_index,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    weather_data['location_name'], weather_data['region'],
                    weather_data['country'], weather_data['latitude'],
                    weather_data['longitude'], weather_data['local_time'],
                    weather_data['temperature_c'], weather_data['temperature_f'],
                    weather_data['condition_text'], weather_data['condition_icon'],
                    weather_data['humidity'], weather_data['wind_speed_kph'],
                    weather_data['wind_speed_mph'], weather_data['wind_direction'],
                    weather_data['pressure_mb'], weather_data['pressure_in'],
                    weather_data['feels_like_c'], weather_data['feels_like_f'],
                    weather_data['visibility_km'], weather_data['visibility_miles'],
                    weather_data['uv_index'], now, now
                ))
                record_id = cursor.lastrowid
            
            conn.commit()
            return record_id
    
    def get_weather_by_location(self, location_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get weather records for a specific location.
        
        Args:
            location_name (str): Name of the location
            limit (int): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: List of weather records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM weather_records 
                WHERE location_name = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (location_name, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_latest_weather_by_location(self, location_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent weather record for a location.
        
        Args:
            location_name (str): Name of the location
            
        Returns:
            Optional[Dict[str, Any]]: Latest weather record or None if not found
        """
        records = self.get_weather_by_location(location_name, limit=1)
        return records[0] if records else None
    
    def get_all_locations(self) -> List[str]:
        """
        Get a list of all unique locations in the database.
        
        Returns:
            List[str]: List of location names
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT location_name 
                FROM weather_records 
                ORDER BY location_name
            """)
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_all_weather_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all weather records.
        
        Args:
            limit (int): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: List of all weather records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM weather_records 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_old_records(self, days_old: int = 30) -> int:
        """
        Delete weather records older than specified days.
        
        Args:
            days_old (int): Number of days after which records should be deleted
            
        Returns:
            int: Number of records deleted
        """
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM weather_records 
                WHERE created_at < ?
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
    
    def create_demo_historical_data(self, location_name: str, days_back: int = 7) -> List[int]:
        """
        Create demo historical data for a location for testing purposes.
        
        Args:
            location_name (str): Name of the location
            days_back (int): Number of days of historical data to create
            
        Returns:
            List[int]: List of record IDs created
        """
        import random
        
        record_ids = []
        base_temp = 20.0
        
        for i in range(days_back):
            # Create data for each day going back
            timestamp = (datetime.now() - timedelta(days=days_back - i, hours=random.randint(0, 23))).isoformat()
            
            # Simulate realistic weather variations
            temp_variation = random.uniform(-5, 5)
            humidity_variation = random.randint(-10, 10)
            wind_variation = random.uniform(-5, 5)
            pressure_variation = random.uniform(-20, 20)
            
            demo_data = {
                'location_name': location_name,
                'region': 'Demo Region',
                'country': 'Demo Country',
                'latitude': 51.5 + random.uniform(-0.1, 0.1),
                'longitude': -0.1 + random.uniform(-0.1, 0.1),
                'local_time': timestamp,
                'temperature_c': base_temp + temp_variation,
                'temperature_f': (base_temp + temp_variation) * 9/5 + 32,
                'condition_text': random.choice(['Sunny', 'Partly cloudy', 'Cloudy', 'Light rain', 'Overcast']),
                'condition_icon': '//cdn.weatherapi.com/weather/64x64/day/116.png',
                'humidity': max(30, min(90, 60 + humidity_variation)),
                'wind_speed_kph': max(0, 15 + wind_variation),
                'wind_speed_mph': max(0, (15 + wind_variation) * 0.621371),
                'wind_direction': random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']),
                'pressure_mb': 1013 + pressure_variation,
                'pressure_in': (1013 + pressure_variation) * 0.02953,
                'feels_like_c': base_temp + temp_variation + random.uniform(-2, 2),
                'feels_like_f': (base_temp + temp_variation + random.uniform(-2, 2)) * 9/5 + 32,
                'visibility_km': random.uniform(8, 15),
                'visibility_miles': random.uniform(5, 9),
                'uv_index': random.uniform(0, 8)
            }
            
            # Manually insert with specific timestamp
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO weather_records (
                        location_name, region, country, latitude, longitude,
                        local_time, temperature_c, temperature_f, condition_text,
                        condition_icon, humidity, wind_speed_kph, wind_speed_mph,
                        wind_direction, pressure_mb, pressure_in, feels_like_c,
                        feels_like_f, visibility_km, visibility_miles, uv_index,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    demo_data['location_name'], demo_data['region'],
                    demo_data['country'], demo_data['latitude'],
                    demo_data['longitude'], demo_data['local_time'],
                    demo_data['temperature_c'], demo_data['temperature_f'],
                    demo_data['condition_text'], demo_data['condition_icon'],
                    demo_data['humidity'], demo_data['wind_speed_kph'],
                    demo_data['wind_speed_mph'], demo_data['wind_direction'],
                    demo_data['pressure_mb'], demo_data['pressure_in'],
                    demo_data['feels_like_c'], demo_data['feels_like_f'],
                    demo_data['visibility_km'], demo_data['visibility_miles'],
                    demo_data['uv_index'], timestamp, timestamp
                ))
                record_ids.append(cursor.lastrowid)
                conn.commit()
        
        return record_ids


def store_weather_data(weather_data: Dict[str, Any], db_path: str = "weather_data.db") -> int:
    """
    Convenience function to store weather data in the database.
    
    Args:
        weather_data (Dict[str, Any]): Weather data from the API
        db_path (str): Path to the database file
        
    Returns:
        int: ID of the stored record
    """
    db = WeatherDatabase(db_path)
    return db.upsert_weather_data(weather_data) 