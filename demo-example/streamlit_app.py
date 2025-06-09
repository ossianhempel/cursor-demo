"""
Weather Dashboard - Streamlit Application
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from weather_fetcher import get_current_weather
from weather_database import WeatherDatabase
from weather_pipeline import WeatherPipeline
import time

# Page configuration
st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .weather-icon {
        font-size: 3rem;
        text-align: center;
    }
    .temperature-big {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
    }
    .location-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
        text-align: center;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def get_weather_icon_emoji(icon_code):
    """Convert OpenWeather icon code to emoji"""
    icon_map = {
        '01d': '☀️', '01n': '🌙',  # clear sky
        '02d': '⛅', '02n': '☁️',  # few clouds
        '03d': '☁️', '03n': '☁️',  # scattered clouds
        '04d': '☁️', '04n': '☁️',  # broken clouds
        '09d': '🌧️', '09n': '🌧️',  # shower rain
        '10d': '🌦️', '10n': '🌧️',  # rain
        '11d': '⛈️', '11n': '⛈️',  # thunderstorm
        '13d': '❄️', '13n': '❄️',  # snow
        '50d': '🌫️', '50n': '🌫️',  # mist
    }
    return icon_map.get(icon_code, '🌤️')

def display_current_weather(weather_data):
    """Display current weather in a nice card format"""
    if not weather_data:
        st.error("No weather data available")
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div class="location-title">
            📍 {weather_data['location']}, {weather_data['country']}
        </div>
        """, unsafe_allow_html=True)
        
        # Weather icon and temperature
        icon_emoji = get_weather_icon_emoji(weather_data['weather']['icon'])
        st.markdown(f"""
        <div class="weather-icon">{icon_emoji}</div>
        <div class="temperature-big">{weather_data['temperature']['current']}°C</div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="text-align: center; font-size: 1.2rem; margin: 1rem 0;">
            {weather_data['weather']['description'].title()}
        </div>
        """, unsafe_allow_html=True)
    
    # Weather details in columns
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🌡️ Feels Like",
            value=f"{weather_data['temperature']['feels_like']}°C"
        )
        st.metric(
            label="💧 Humidity",
            value=f"{weather_data['humidity']}%"
        )
    
    with col2:
        st.metric(
            label="📉 Min Temp",
            value=f"{weather_data['temperature']['min']}°C"
        )
        st.metric(
            label="🌪️ Wind Speed",
            value=f"{weather_data['wind']['speed']} m/s"
        )
    
    with col3:
        st.metric(
            label="📈 Max Temp",
            value=f"{weather_data['temperature']['max']}°C"
        )
        st.metric(
            label="🧭 Wind Direction",
            value=f"{weather_data['wind']['direction']}°" if weather_data['wind']['direction'] else "N/A"
        )
    
    with col4:
        st.metric(
            label="🌊 Pressure",
            value=f"{weather_data['pressure']} hPa"
        )
        st.metric(
            label="☁️ Clouds",
            value=f"{weather_data['clouds']}%"
        )

def create_temperature_chart(records):
    """Create temperature trend chart"""
    if not records:
        return None
    
    df = pd.DataFrame(records)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df = df.sort_values('created_at')
    
    fig = go.Figure()
    
    # Add temperature line
    fig.add_trace(go.Scatter(
        x=df['created_at'],
        y=df['temperature_current'],
        mode='lines+markers',
        name='Temperature',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Temperature Trend",
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        hovermode='x unified',
        showlegend=False,
        height=400
    )
    
    return fig

def create_weather_metrics_chart(records):
    """Create chart for various weather metrics"""
    if not records:
        return None
    
    df = pd.DataFrame(records)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df = df.sort_values('created_at')
    
    fig = go.Figure()
    
    # Add humidity
    fig.add_trace(go.Scatter(
        x=df['created_at'],
        y=df['humidity'],
        mode='lines+markers',
        name='Humidity (%)',
        line=dict(color='#2ca02c'),
        yaxis='y'
    ))
    
    # Add pressure on secondary y-axis
    fig.add_trace(go.Scatter(
        x=df['created_at'],
        y=df['pressure'],
        mode='lines+markers',
        name='Pressure (hPa)',
        line=dict(color='#d62728'),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Weather Metrics Over Time",
        xaxis_title="Time",
        yaxis=dict(title="Humidity (%)", side="left"),
        yaxis2=dict(title="Pressure (hPa)", side="right", overlaying="y"),
        hovermode='x unified',
        height=400
    )
    
    return fig

def display_database_table(db, limit=50):
    """Display weather records in a table"""
    records = db.get_latest_weather_records(limit)
    
    if not records:
        st.info("No weather records found in database")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(records)
    
    # Select relevant columns for display
    display_columns = [
        'location', 'country', 'weather_main', 'weather_description',
        'temperature_current', 'humidity', 'pressure', 'wind_speed',
        'created_at'
    ]
    
    df_display = df[display_columns].copy()
    df_display.columns = [
        'Location', 'Country', 'Weather', 'Description',
        'Temperature (°C)', 'Humidity (%)', 'Pressure (hPa)', 'Wind (m/s)',
        'Recorded At'
    ]
    
    # Format datetime
    df_display['Recorded At'] = pd.to_datetime(df_display['Recorded At']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    st.dataframe(
        df_display,
        use_container_width=True,
        height=400
    )

def main():
    """Main Streamlit application"""
    st.title("🌤️ Weather Dashboard")
    st.markdown("Real-time weather data with historical tracking")
    
    # Initialize database
    db = WeatherDatabase("weather_data.db")
    pipeline = WeatherPipeline("weather_data.db")
    
    # Sidebar for controls
    st.sidebar.header("🎛️ Controls")
    
    # Location input
    location_input = st.sidebar.text_input(
        "Enter Location",
        value="London,UK",
        help="Format: City,Country (e.g., London,UK or New York,US)"
    )
    
    # Units selection
    units = st.sidebar.selectbox(
        "Temperature Units",
        ["metric", "imperial", "kelvin"],
        index=0,
        help="metric: Celsius, imperial: Fahrenheit, kelvin: Kelvin"
    )
    
    # Fetch button
    if st.sidebar.button("🔄 Fetch Weather", type="primary"):
        with st.spinner("Fetching weather data..."):
            try:
                record_id, was_inserted, weather_data = pipeline.fetch_and_store_weather(location_input, units)
                
                if weather_data:
                    st.session_state['current_weather'] = weather_data
                    st.session_state['last_location'] = location_input
                    action = "New data fetched" if was_inserted else "Data updated"
                    st.sidebar.success(f"✅ {action}")
                else:
                    st.sidebar.error("❌ Failed to fetch weather data")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)")
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Display current weather
    if 'current_weather' in st.session_state:
        st.header("🌤️ Current Weather")
        display_current_weather(st.session_state['current_weather'])
    
    # Historical data section
    st.header("📊 Historical Data")
    
    # Database stats
    stats = db.get_database_stats()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", stats['total_records'])
    with col2:
        st.metric("Unique Locations", stats['total_locations'])
    with col3:
        if stats['earliest_record']:
            earliest = datetime.fromisoformat(stats['earliest_record']).strftime('%Y-%m-%d')
            st.metric("First Record", earliest)
    with col4:
        if stats['latest_record']:
            latest = datetime.fromisoformat(stats['latest_record']).strftime('%Y-%m-%d')
            st.metric("Latest Record", latest)
    
    # Location selector for historical data
    locations = db.get_all_locations()
    if locations:
        location_options = [f"{loc['location_name']}, {loc['country']}" for loc in locations]
        selected_location = st.selectbox(
            "Select location for historical view",
            location_options,
            index=0 if location_options else None
        )
        
        if selected_location:
            location_name, country = selected_location.split(', ')
            historical_records = db.get_weather_by_location(location_name, country, limit=20)
            
            if historical_records:
                col1, col2 = st.columns(2)
                
                with col1:
                    temp_chart = create_temperature_chart(historical_records)
                    if temp_chart:
                        st.plotly_chart(temp_chart, use_container_width=True)
                
                with col2:
                    metrics_chart = create_weather_metrics_chart(historical_records)
                    if metrics_chart:
                        st.plotly_chart(metrics_chart, use_container_width=True)
    
    # Database table view
    st.header("🗄️ Database Records")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Recent Weather Records")
    with col2:
        table_limit = st.number_input("Records to show", min_value=10, max_value=200, value=20)
    
    display_database_table(db, table_limit)
    
    # Footer
    st.markdown("---")
    st.markdown("🔗 Built with Streamlit • Weather data from OpenWeatherMap API")

if __name__ == "__main__":
    main() 