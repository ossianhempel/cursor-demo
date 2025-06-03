import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import requests

from weather_api import get_weather_for_location, WeatherAPIError
from weather_database import WeatherDatabase, store_weather_data

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
    .weather-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-bottom: 10px;
    }
    
    .location-header {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .temperature-display {
        font-size: 3rem;
        font-weight: bold;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def get_database():
    return WeatherDatabase()

db = get_database()

# Sidebar for location input and settings
st.sidebar.header("🌍 Location Settings")

# Location input
location = st.sidebar.text_input(
    "Enter location:", 
    value="London",
    help="Enter a city name, coordinates, or location query"
)

# Unit preferences
temperature_unit = st.sidebar.selectbox(
    "Temperature Unit:",
    ["Celsius", "Fahrenheit"],
    index=0
)

wind_unit = st.sidebar.selectbox(
    "Wind Speed Unit:",
    ["km/h", "mph"],
    index=0
)

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto-refresh data", value=False)

# Demo data button
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Demo Features")
if st.sidebar.button("📊 Generate Demo Historical Data"):
    if location:
        with st.spinner(f"Creating demo historical data for {location}..."):
            try:
                record_ids = db.create_demo_historical_data(location, days_back=7)
                st.sidebar.success(f"✅ Created {len(record_ids)} demo records for {location}!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"❌ Error creating demo data: {str(e)}")
    else:
        st.sidebar.warning("⚠️ Please enter a location first")

st.sidebar.markdown("---")

# Refresh button
if st.sidebar.button("🔄 Fetch Weather Data") or auto_refresh:
    if location:
        with st.spinner(f"Fetching weather data for {location}..."):
            try:
                # Fetch weather data
                weather_data = get_weather_for_location(location)
                
                # Store in database
                record_id = store_weather_data(weather_data)
                
                st.sidebar.success(f"✅ Data updated successfully! (Record ID: {record_id})")
                st.rerun()
                
            except WeatherAPIError as e:
                st.sidebar.error(f"❌ Weather API Error: {str(e)}")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")
    else:
        st.sidebar.warning("⚠️ Please enter a location")

# Main content
st.title("🌤️ Weather Dashboard")
st.markdown("Real-time weather data with beautiful visualizations")

# Get latest weather data for the location
if location:
    latest_weather = db.get_latest_weather_by_location(location)
    
    if latest_weather:
        # Display main weather information
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"""
            <div class="weather-card">
                <div class="location-header">{latest_weather['location_name']}, {latest_weather['country']}</div>
                <div>{latest_weather['region']}</div>
                <div class="temperature-display">
                    {latest_weather['temperature_c'] if temperature_unit == 'Celsius' else latest_weather['temperature_f']}°
                    {'C' if temperature_unit == 'Celsius' else 'F'}
                </div>
                <div style="font-size: 1.2rem;">{latest_weather['condition_text']}</div>
                <div>Feels like {latest_weather['feels_like_c'] if temperature_unit == 'Celsius' else latest_weather['feels_like_f']}°
                {'C' if temperature_unit == 'Celsius' else 'F'}</div>
                <div style="margin-top: 10px; font-size: 0.9rem;">
                    Last updated: {latest_weather['updated_at'][:19].replace('T', ' ')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.metric(
                "💧 Humidity", 
                f"{latest_weather['humidity']}%"
            )
            st.metric(
                "👁️ Visibility", 
                f"{latest_weather['visibility_km']} km" if wind_unit == "km/h" else f"{latest_weather['visibility_miles']} mi"
            )
            st.metric(
                "🌅 UV Index", 
                f"{latest_weather['uv_index']}"
            )
        
        with col3:
            st.metric(
                "💨 Wind Speed", 
                f"{latest_weather['wind_speed_kph']} km/h" if wind_unit == "km/h" else f"{latest_weather['wind_speed_mph']} mph"
            )
            st.metric(
                "🧭 Wind Direction", 
                latest_weather['wind_direction']
            )
            st.metric(
                "🌡️ Pressure", 
                f"{latest_weather['pressure_mb']} mb"
            )
        
        # Weather metrics visualization
        st.markdown("---")
        st.header("📊 Weather Metrics")
        
        # Create gauge charts
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Humidity gauge
            fig_humidity = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = latest_weather['humidity'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Humidity (%)"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "lightblue"},
                    'steps': [
                        {'range': [0, 30], 'color': "yellow"},
                        {'range': [30, 70], 'color': "lightgreen"},
                        {'range': [70, 100], 'color': "lightblue"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_humidity.update_layout(height=300)
            st.plotly_chart(fig_humidity, use_container_width=True)
        
        with col2:
            # Wind speed gauge
            max_wind = 150 if wind_unit == "km/h" else 93
            wind_value = latest_weather['wind_speed_kph'] if wind_unit == "km/h" else latest_weather['wind_speed_mph']
            
            fig_wind = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = wind_value,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': f"Wind Speed ({wind_unit})"},
                gauge = {
                    'axis': {'range': [None, max_wind]},
                    'bar': {'color': "lightgreen"},
                    'steps': [
                        {'range': [0, 20], 'color': "lightgray"},
                        {'range': [20, 60], 'color': "yellow"},
                        {'range': [60, max_wind], 'color': "red"}
                    ]
                }
            ))
            fig_wind.update_layout(height=300)
            st.plotly_chart(fig_wind, use_container_width=True)
        
        with col3:
            # UV Index gauge
            fig_uv = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = latest_weather['uv_index'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "UV Index"},
                gauge = {
                    'axis': {'range': [None, 12]},
                    'bar': {'color': "orange"},
                    'steps': [
                        {'range': [0, 3], 'color': "green"},
                        {'range': [3, 6], 'color': "yellow"},
                        {'range': [6, 8], 'color': "orange"},
                        {'range': [8, 11], 'color': "red"},
                        {'range': [11, 12], 'color': "purple"}
                    ]
                }
            ))
            fig_uv.update_layout(height=300)
            st.plotly_chart(fig_uv, use_container_width=True)
        
        # Historical data section
        st.markdown("---")
        st.header("📈 Historical Data")
        
        # Get historical data for this location
        historical_data = db.get_weather_by_location(location, limit=20)
        
        if len(historical_data) > 1:
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            df = df.sort_values('created_at')
            
            # Temperature trend
            fig_temp = px.line(
                df, 
                x='created_at', 
                y='temperature_c' if temperature_unit == 'Celsius' else 'temperature_f',
                title=f"Temperature Trend ({temperature_unit})",
                color_discrete_sequence=['#667eea']
            )
            fig_temp.update_layout(height=400)
            st.plotly_chart(fig_temp, use_container_width=True)
            
            # Multiple metrics chart
            fig_metrics = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Humidity (%)', 'Pressure (mb)', f'Wind Speed ({wind_unit})', 'UV Index'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Humidity
            fig_metrics.add_trace(
                go.Scatter(x=df['created_at'], y=df['humidity'], name='Humidity', line=dict(color='blue')),
                row=1, col=1
            )
            
            # Pressure
            fig_metrics.add_trace(
                go.Scatter(x=df['created_at'], y=df['pressure_mb'], name='Pressure', line=dict(color='green')),
                row=1, col=2
            )
            
            # Wind Speed
            wind_col = 'wind_speed_kph' if wind_unit == "km/h" else 'wind_speed_mph'
            fig_metrics.add_trace(
                go.Scatter(x=df['created_at'], y=df[wind_col], name='Wind Speed', line=dict(color='orange')),
                row=2, col=1
            )
            
            # UV Index
            fig_metrics.add_trace(
                go.Scatter(x=df['created_at'], y=df['uv_index'], name='UV Index', line=dict(color='red')),
                row=2, col=2
            )
            
            fig_metrics.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig_metrics, use_container_width=True)
        else:
            st.info("📝 Historical data will appear here after multiple weather updates for this location.")
    
    else:
        st.warning(f"⚠️ No weather data found for '{location}'. Click 'Fetch Weather Data' to get current weather information.")

else:
    st.info("👈 Enter a location in the sidebar to view weather data")

# Sidebar: All locations
st.sidebar.markdown("---")
st.sidebar.header("🗺️ All Locations")

all_locations = db.get_all_locations()
if all_locations:
    selected_location = st.sidebar.selectbox(
        "Quick select location:",
        [""] + all_locations,
        index=0
    )
    
    if selected_location and selected_location != location:
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🌤️ Weather Dashboard - Powered by WeatherAPI.com</p>
    <p>Data is automatically stored in SQLite database for historical analysis</p>
</div>
""", unsafe_allow_html=True) 