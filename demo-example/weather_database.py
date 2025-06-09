"""
Weather database module for SQLite operations
"""
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

class WeatherDatabase:
    """Class for managing weather data in SQLite database"""
    
    def __init__(self, db_path: str = "weather_data.db"):
        """
        Initialize database connection and create tables if they don't exist
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.create_tables()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory for dict-like access"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_tables(self):
        """Create database tables and indexes"""
        with self.get_connection() as conn:
            # Create locations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    first_recorded DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    record_count INTEGER DEFAULT 0,
                    UNIQUE(location_name, country)
                )
            """)
            
            # Create weather_records table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weather_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_id INTEGER NOT NULL,
                    location TEXT NOT NULL,
                    country TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    weather_main TEXT NOT NULL,
                    weather_description TEXT NOT NULL,
                    weather_icon TEXT,
                    temperature_current REAL NOT NULL,
                    temperature_feels_like REAL,
                    temperature_min REAL,
                    temperature_max REAL,
                    pressure INTEGER,
                    humidity INTEGER,
                    visibility INTEGER,
                    wind_speed REAL,
                    wind_direction INTEGER,
                    clouds INTEGER,
                    timestamp INTEGER NOT NULL,
                    timezone INTEGER,
                    units TEXT DEFAULT 'metric',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (location_id) REFERENCES locations (id)
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_locations_name_country ON locations(location_name, country)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_weather_location_id ON weather_records(location_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_records(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_weather_created_at ON weather_records(created_at)")
            
            conn.commit()
    
    def get_or_create_location(self, location_name: str, country: str, latitude: float, longitude: float) -> int:
        """
        Get location ID or create new location if it doesn't exist
        
        Args:
            location_name (str): Name of the location
            country (str): Country code
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            
        Returns:
            int: Location ID
        """
        with self.get_connection() as conn:
            # Try to find existing location
            cursor = conn.execute(
                "SELECT id FROM locations WHERE location_name = ? AND country = ?",
                (location_name, country)
            )
            result = cursor.fetchone()
            
            if result:
                # Update last_updated timestamp
                conn.execute(
                    "UPDATE locations SET last_updated = CURRENT_TIMESTAMP WHERE id = ?",
                    (result['id'],)
                )
                return result['id']
            else:
                # Create new location
                cursor = conn.execute("""
                    INSERT INTO locations (location_name, country, latitude, longitude)
                    VALUES (?, ?, ?, ?)
                """, (location_name, country, latitude, longitude))
                return cursor.lastrowid
    
    def insert_weather_record(self, weather_data: Dict) -> int:
        """
        Insert a weather record into the database
        
        Args:
            weather_data (Dict): Weather data dictionary from weather_fetcher
            
        Returns:
            int: ID of inserted record
        """
        # Get or create location
        location_id = self.get_or_create_location(
            weather_data['location'],
            weather_data['country'],
            weather_data['coordinates']['latitude'],
            weather_data['coordinates']['longitude']
        )
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO weather_records (
                    location_id, location, country, latitude, longitude,
                    weather_main, weather_description, weather_icon,
                    temperature_current, temperature_feels_like, temperature_min, temperature_max,
                    pressure, humidity, visibility, wind_speed, wind_direction,
                    clouds, timestamp, timezone, units
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                location_id,
                weather_data['location'],
                weather_data['country'],
                weather_data['coordinates']['latitude'],
                weather_data['coordinates']['longitude'],
                weather_data['weather']['main'],
                weather_data['weather']['description'],
                weather_data['weather']['icon'],
                weather_data['temperature']['current'],
                weather_data['temperature']['feels_like'],
                weather_data['temperature']['min'],
                weather_data['temperature']['max'],
                weather_data['pressure'],
                weather_data['humidity'],
                weather_data['visibility'],
                weather_data['wind']['speed'],
                weather_data['wind']['direction'],
                weather_data['clouds'],
                weather_data['timestamp'],
                weather_data['timezone'],
                weather_data['units']
            ))
            
            record_id = cursor.lastrowid
            
            # Update location record count
            conn.execute("""
                UPDATE locations 
                SET record_count = (SELECT COUNT(*) FROM weather_records WHERE location_id = ?),
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (location_id, location_id))
            
            return record_id
    
    def upsert_weather_record(self, weather_data: Dict) -> Tuple[int, bool]:
        """
        Insert or update a weather record (upsert operation)
        Updates if a record exists for the same location within the last hour
        
        Args:
            weather_data (Dict): Weather data dictionary from weather_fetcher
            
        Returns:
            Tuple[int, bool]: (record_id, was_inserted)
        """
        # Check if recent record exists (within last hour)
        one_hour_ago = weather_data['timestamp'] - 3600
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id FROM weather_records 
                WHERE location = ? AND country = ? AND timestamp > ?
                ORDER BY timestamp DESC LIMIT 1
            """, (weather_data['location'], weather_data['country'], one_hour_ago))
            
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Update existing record
                conn.execute("""
                    UPDATE weather_records SET
                        weather_main = ?, weather_description = ?, weather_icon = ?,
                        temperature_current = ?, temperature_feels_like = ?, 
                        temperature_min = ?, temperature_max = ?,
                        pressure = ?, humidity = ?, visibility = ?,
                        wind_speed = ?, wind_direction = ?, clouds = ?,
                        timestamp = ?, timezone = ?, units = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    weather_data['weather']['main'],
                    weather_data['weather']['description'],
                    weather_data['weather']['icon'],
                    weather_data['temperature']['current'],
                    weather_data['temperature']['feels_like'],
                    weather_data['temperature']['min'],
                    weather_data['temperature']['max'],
                    weather_data['pressure'],
                    weather_data['humidity'],
                    weather_data['visibility'],
                    weather_data['wind']['speed'],
                    weather_data['wind']['direction'],
                    weather_data['clouds'],
                    weather_data['timestamp'],
                    weather_data['timezone'],
                    weather_data['units'],
                    existing_record['id']
                ))
                return existing_record['id'], False
            else:
                # Insert new record
                record_id = self.insert_weather_record(weather_data)
                return record_id, True
    
    def get_latest_weather_records(self, limit: int = 10) -> List[Dict]:
        """Get the latest weather records"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM weather_records 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_weather_by_location(self, location: str, country: str = None, limit: int = 10) -> List[Dict]:
        """Get weather records for a specific location"""
        with self.get_connection() as conn:
            if country:
                cursor = conn.execute("""
                    SELECT * FROM weather_records 
                    WHERE location = ? AND country = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (location, country, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM weather_records 
                    WHERE location LIKE ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (f"%{location}%", limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_locations(self) -> List[Dict]:
        """Get all unique locations in the database"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM locations 
                ORDER BY record_count DESC, location_name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            stats = {}
            
            # Total records
            cursor = conn.execute("SELECT COUNT(*) as count FROM weather_records")
            stats['total_records'] = cursor.fetchone()['count']
            
            # Total locations
            cursor = conn.execute("SELECT COUNT(*) as count FROM locations")
            stats['total_locations'] = cursor.fetchone()['count']
            
            # Date range
            cursor = conn.execute("""
                SELECT 
                    MIN(created_at) as earliest_record,
                    MAX(created_at) as latest_record
                FROM weather_records
            """)
            date_range = cursor.fetchone()
            stats['earliest_record'] = date_range['earliest_record']
            stats['latest_record'] = date_range['latest_record']
            
            return stats

# Convenience functions
def save_weather_data(weather_data: Dict, db_path: str = "weather_data.db") -> int:
    """
    Convenience function to save weather data to database
    
    Args:
        weather_data (Dict): Weather data from weather_fetcher
        db_path (str): Database file path
        
    Returns:
        int: Record ID
    """
    db = WeatherDatabase(db_path)
    return db.insert_weather_record(weather_data)

def upsert_weather_data(weather_data: Dict, db_path: str = "weather_data.db") -> Tuple[int, bool]:
    """
    Convenience function to upsert weather data to database
    
    Args:
        weather_data (Dict): Weather data from weather_fetcher
        db_path (str): Database file path
        
    Returns:
        Tuple[int, bool]: (record_id, was_inserted)
    """
    db = WeatherDatabase(db_path)
    return db.upsert_weather_record(weather_data)

if __name__ == "__main__":
    # Example usage
    db = WeatherDatabase()
    print("Database initialized successfully!")
    print("Stats:", json.dumps(db.get_database_stats(), indent=2)) 