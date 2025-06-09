# Weather Data Model

## Database Schema Diagram

```mermaid
erDiagram
    WEATHER_RECORDS {
        INTEGER id PK "Primary Key"
        TEXT location "City name"
        TEXT country "Country code"
        REAL latitude "Coordinate latitude"
        REAL longitude "Coordinate longitude"
        TEXT weather_main "Main weather condition"
        TEXT weather_description "Detailed weather description"
        TEXT weather_icon "Weather icon code"
        REAL temperature_current "Current temperature"
        REAL temperature_feels_like "Feels like temperature"
        REAL temperature_min "Minimum temperature"
        REAL temperature_max "Maximum temperature"
        INTEGER pressure "Atmospheric pressure"
        INTEGER humidity "Humidity percentage"
        INTEGER visibility "Visibility in meters"
        REAL wind_speed "Wind speed"
        INTEGER wind_direction "Wind direction in degrees"
        INTEGER clouds "Cloud coverage percentage"
        INTEGER timestamp "Unix timestamp"
        INTEGER timezone "Timezone offset"
        TEXT units "Temperature units"
        DATETIME created_at "Record creation time"
        DATETIME updated_at "Record last update time"
    }
    
    LOCATIONS {
        INTEGER id PK "Primary Key"
        TEXT location_name "City name"
        TEXT country "Country code"
        REAL latitude "Coordinate latitude"
        REAL longitude "Coordinate longitude"
        DATETIME first_recorded "First weather record date"
        DATETIME last_updated "Last weather record date"
        INTEGER record_count "Total number of records"
    }
    
    WEATHER_RECORDS ||--|| LOCATIONS : "belongs_to"
```

## Table Descriptions

### WEATHER_RECORDS
The main table storing all weather data records. Each record represents a weather snapshot at a specific location and time.

### LOCATIONS
A lookup table for unique locations, providing summary information and statistics about each location.

## Data Relationships
- Each weather record belongs to one location
- Locations can have multiple weather records over time
- The relationship helps optimize queries and provides location-based analytics

## Indexing Strategy
- Primary indexes on id fields
- Composite index on (location, country) for fast location lookups
- Index on timestamp for time-based queries
- Index on created_at for recent data queries 