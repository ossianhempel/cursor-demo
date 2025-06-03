# 🌤️ Weather API Pipeline with Data Visualization

A beautiful weather dashboard that fetches real-time weather data, stores it in SQLite, and provides interactive visualizations using Streamlit.

## 🚀 Features

- **Real-time Weather Data**: Fetch current weather information for any location using WeatherAPI.com
- **SQLite Database**: Automatic storage and management of historical weather data
- **Interactive Dashboard**: Beautiful Streamlit interface with:
  - Current weather display with gradient cards
  - Interactive gauge charts for humidity, wind speed, and UV index
  - Historical trend charts
  - Unit conversion (Celsius/Fahrenheit, km/h/mph)
  - Location quick-select from database
- **Comprehensive Testing**: Full test coverage for API and database functionality
- **Error Handling**: Robust error handling for API calls and database operations

## 📋 Requirements

- Python 3.8+
- WeatherAPI.com API key (free tier available)

## 🛠️ Setup Instructions

1. **Clone and navigate to the project:**
   ```bash
   cd working-example
   ```

2. **Install dependencies using UV:**
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Set up your API key:**
   Create a `.env` file in the working-example directory:
   ```env
   WEATHER_API_KEY=your_weather_api_key_here
   ```
   
   Get your free API key at: https://www.weatherapi.com/

4. **Run the Streamlit app:**
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Access the dashboard:**
   Open your browser and go to `http://localhost:8501`

## 🧪 Running Tests

Run all tests:
```bash
python -m pytest -v
```

Run specific test files:
```bash
python -m pytest test_weather_api.py -v
python -m pytest test_weather_database.py -v
```

## 📁 Project Structure

```
working-example/
├── streamlit_app.py           # Main Streamlit dashboard
├── weather_api.py             # Weather API functionality
├── weather_database.py        # SQLite database management
├── config.py                  # Configuration and environment variables
├── test_weather_api.py        # Tests for weather API
├── test_weather_database.py   # Tests for database functionality
├── weather_data_model.md      # Database schema documentation
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── weather_data.db           # SQLite database (created automatically)
```

## 🎯 Usage

### Dashboard Features

1. **Location Input**: Enter any city name, coordinates, or location query in the sidebar
2. **Fetch Data**: Click "Fetch Weather Data" to get current weather and store it in the database
3. **Unit Preferences**: Choose between Celsius/Fahrenheit and km/h/mph
4. **Historical Data**: View trend charts when multiple data points are available for a location
5. **Quick Location Select**: Choose from previously searched locations
6. **Demo Data**: Generate sample historical data to see charts in action

### Key Features

- **Smart Data Storage**: New weather records are created every hour, allowing for historical tracking
- **Demo Mode**: Generate sample historical data to test chart functionality
- **Auto-refresh**: Optional automatic data fetching
- **Unit Conversion**: Toggle between metric and imperial units

### API Usage

```python
from weather_api import get_weather_for_location
from weather_database import store_weather_data

# Fetch weather data
weather_data = get_weather_for_location("London")

# Store in database
record_id = store_weather_data(weather_data)
```

### Database Usage

```python
from weather_database import WeatherDatabase

# Initialize database
db = WeatherDatabase()

# Get latest weather for a location
weather = db.get_latest_weather_by_location("London")

# Get all locations
locations = db.get_all_locations()

# Get historical data
history = db.get_weather_by_location("London", limit=10)
```

## 📊 Database Schema

The SQLite database stores comprehensive weather information:

- **Location Data**: Name, region, country, coordinates
- **Weather Metrics**: Temperature, humidity, pressure, wind, visibility, UV index
- **Timestamps**: Creation and update times for tracking
- **Indexes**: Optimized for location and time-based queries

See `weather_data_model.md` for the complete schema diagram.

## 🎨 Dashboard Screenshots

The dashboard features:
- **Weather Cards**: Beautiful gradient cards showing current conditions
- **Gauge Charts**: Interactive humidity, wind speed, and UV index gauges
- **Trend Charts**: Historical temperature and weather metrics
- **Responsive Design**: Works on desktop and mobile devices

## 🧩 API Reference

### Weather API Functions

- `fetch_weather_data(location)`: Fetch raw weather data from API
- `extract_weather_info(data)`: Extract and normalize weather information
- `get_weather_for_location(location)`: High-level function to get weather data

### Database Functions

- `upsert_weather_data(data)`: Insert or update weather data
- `get_weather_by_location(location, limit)`: Get historical weather data
- `get_latest_weather_by_location(location)`: Get most recent weather data
- `get_all_locations()`: Get list of all stored locations

## 🔧 Configuration

Environment variables (set in `.env` file):
- `WEATHER_API_KEY`: Your WeatherAPI.com API key (required)

## 📝 Todo List Status

- [x] Function that fetches current weather data for a given location using WeatherAPI
- [x] Add 1-3 simple tests for the data fetching function
- [x] Create data model based on the weather data, visualize it in mermaid diagram, and then create it in SQLite
- [x] Function that takes fetched weather data and upserts it to SQLite
- [x] Add 1-3 simple tests for the upsert functionality
- [x] Visualize the current weather data in Streamlit appropriately
- [x] Allow users to input desired location in Streamlit and have it fetch for that query (and store in SQLite of course)

## 🤝 Contributing

1. Run tests before submitting changes
2. Follow the existing code style and documentation patterns
3. Add tests for new functionality
4. Update documentation as needed

## 📄 License

This project is for demonstration purposes. Weather data provided by WeatherAPI.com. 