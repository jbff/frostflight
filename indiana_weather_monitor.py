#!/usr/bin/env python3
"""
Indiana Weather Monitor for RV Travel
=====================================

This script monitors temperatures across Indiana to help RV travelers
stay ahead of frost and freezes by moving south as temperatures drop.

Features:
- Current temperatures across Indiana
- 7-day forecast with minimum temperatures
- Freeze warnings and recommendations
- Color-coded temperature display
- No API key required (uses Open-Meteo free API)
"""

import requests
import json
from datetime import datetime, timedelta
import sys
from typing import Dict, List, Tuple

# Indiana cities from north to south for temperature monitoring
INDIANA_CITIES = {
    "South Bend": {"lat": 41.6764, "lon": -86.2520, "region": "North"},
    "Gary": {"lat": 41.5934, "lon": -87.3464, "region": "North"},
    "Fort Wayne": {"lat": 41.0793, "lon": -85.1394, "region": "Northeast"},
    "Lafayette": {"lat": 40.4167, "lon": -86.8753, "region": "Northwest"},
    "Kokomo": {"lat": 40.4864, "lon": -86.1336, "region": "Central"},
    "Indianapolis": {"lat": 39.7684, "lon": -86.1581, "region": "Central"},
    "Muncie": {"lat": 40.1934, "lon": -85.3864, "region": "East Central"},
    "Terre Haute": {"lat": 39.4667, "lon": -87.4139, "region": "West Central"},
    "Bloomington": {"lat": 39.1653, "lon": -86.5264, "region": "South Central"},
    "Columbus": {"lat": 39.2014, "lon": -85.9214, "region": "South Central"},
    "Jeffersonville": {"lat": 38.2775, "lon": -85.7372, "region": "South"},
    "Evansville": {"lat": 37.9716, "lon": -87.5711, "region": "Southwest"},
    "New Albany": {"lat": 38.2856, "lon": -85.8244, "region": "South"}
}

# Temperature thresholds
FREEZE_THRESHOLD = 32  # Fahrenheit
FROST_WARNING_THRESHOLD = 35  # Fahrenheit
COMFORTABLE_THRESHOLD = 50  # Fahrenheit

class IndianaWeatherMonitor:
    def __init__(self):
        self.api_url = "https://api.open-meteo.com/v1/forecast"
        self.timezone = "America/Indiana/Indianapolis"
        
    def get_weather_data(self, city: str, coords: Dict[str, float]) -> Dict:
        """Fetch weather data for a specific city."""
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "current_weather": "true",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": self.timezone,
            "temperature_unit": "fahrenheit"
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching data for {city}: {e}")
            return None
    
    def celsius_to_fahrenheit(self, celsius: float) -> float:
        """Convert Celsius to Fahrenheit."""
        return (celsius * 9/5) + 32
    
    def get_temperature_color(self, temp: float) -> str:
        """Get color code for temperature display."""
        if temp <= FREEZE_THRESHOLD:
            return "🔴"  # Red for freezing
        elif temp <= FROST_WARNING_THRESHOLD:
            return "🟡"  # Yellow for frost warning
        elif temp <= COMFORTABLE_THRESHOLD:
            return "🟠"  # Orange for cool
        else:
            return "🟢"  # Green for comfortable
    
    def get_weather_emoji(self, temp: float) -> str:
        """Get weather emoji based on temperature."""
        if temp <= FREEZE_THRESHOLD:
            return "❄️"
        elif temp <= FROST_WARNING_THRESHOLD:
            return "🥶"
        elif temp <= COMFORTABLE_THRESHOLD:
            return "🧥"
        else:
            return "☀️"
    
    def analyze_forecast(self, daily_data: Dict) -> Dict:
        """Analyze forecast data for freeze warnings and recommendations."""
        min_temps = daily_data["temperature_2m_min"]
        max_temps = daily_data["temperature_2m_max"]
        dates = daily_data["time"]
        
        freeze_days = []
        frost_warning_days = []
        comfortable_days = []
        
        for i, (date, min_temp, max_temp) in enumerate(zip(dates, min_temps, max_temps)):
            if min_temp <= FREEZE_THRESHOLD:
                freeze_days.append((date, min_temp, max_temp))
            elif min_temp <= FROST_WARNING_THRESHOLD:
                frost_warning_days.append((date, min_temp, max_temp))
            elif min_temp >= COMFORTABLE_THRESHOLD:
                comfortable_days.append((date, min_temp, max_temp))
        
        return {
            "freeze_days": freeze_days,
            "frost_warning_days": frost_warning_days,
            "comfortable_days": comfortable_days
        }
    
    def get_recommendation(self, city: str, analysis: Dict) -> str:
        """Get travel recommendation based on forecast analysis."""
        if analysis["freeze_days"]:
            return f"⚠️  AVOID {city.upper()} - Freeze expected!"
        elif analysis["frost_warning_days"]:
            return f"⚠️  Caution in {city} - Frost warning"
        elif analysis["comfortable_days"]:
            return f"✅ Good choice: {city} - Comfortable temps"
        else:
            return f"🟡 Moderate: {city} - Cool but manageable"
    
    def display_city_weather(self, city: str, coords: Dict, region: str):
        """Display weather information for a single city."""
        print(f"\n{'='*60}")
        print(f"🌡️  {city} ({region})")
        print(f"{'='*60}")
        
        data = self.get_weather_data(city, coords)
        if not data:
            print(f"❌ Unable to fetch data for {city}")
            return
        
        # Current weather
        current = data["current_weather"]
        current_temp = current["temperature"]
        current_color = self.get_temperature_color(current_temp)
        current_emoji = self.get_weather_emoji(current_temp)
        
        print(f"Current Temperature: {current_color} {current_temp:.1f}°F {current_emoji}")
        print(f"Wind: {current['windspeed']:.1f} mph")
        print(f"Last Updated: {current['time']}")
        
        # 7-day forecast
        daily = data["daily"]
        analysis = self.analyze_forecast(daily)
        
        print(f"\n📅 7-Day Forecast:")
        print(f"{'Date':<12} {'Min':<8} {'Max':<8} {'Status':<15}")
        print("-" * 50)
        
        for i, (date, min_temp, max_temp) in enumerate(zip(daily["time"], daily["temperature_2m_min"], daily["temperature_2m_max"])):
            min_color = self.get_temperature_color(min_temp)
            max_color = self.get_temperature_color(max_temp)
            
            # Format date (remove time part if present)
            display_date = date.split('T')[0] if 'T' in date else date
            
            status = ""
            if min_temp <= FREEZE_THRESHOLD:
                status = "FREEZE"
            elif min_temp <= FROST_WARNING_THRESHOLD:
                status = "FROST WARNING"
            elif min_temp >= COMFORTABLE_THRESHOLD:
                status = "COMFORTABLE"
            else:
                status = "COOL"
            
            print(f"{display_date:<12} {min_color}{min_temp:>5.1f}°F {max_color}{max_temp:>5.1f}°F {status:<15}")
        
        # Recommendation
        recommendation = self.get_recommendation(city, analysis)
        print(f"\n{recommendation}")
    
    def display_state_summary(self):
        """Display a summary of all cities with current temperatures."""
        print(f"\n{'='*80}")
        print(f"🗺️  INDIANA WEATHER SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*80}")
        
        city_data = []
        
        for city, coords in INDIANA_CITIES.items():
            data = self.get_weather_data(city, coords)
            if data:
                current_temp = data["current_weather"]["temperature"]
                region = coords["region"]
                color = self.get_temperature_color(current_temp)
                emoji = self.get_weather_emoji(current_temp)
                
                city_data.append({
                    "city": city,
                    "region": region,
                    "temp": current_temp,
                    "color": color,
                    "emoji": emoji
                })
        
        # Sort by temperature (warmest first)
        city_data.sort(key=lambda x: x["temp"], reverse=True)
        
        print(f"{'City':<15} {'Region':<12} {'Temp':<8} {'Status':<15}")
        print("-" * 60)
        
        for data in city_data:
            status = "FREEZE" if data["temp"] <= FREEZE_THRESHOLD else \
                    "FROST WARNING" if data["temp"] <= FROST_WARNING_THRESHOLD else \
                    "COMFORTABLE" if data["temp"] >= COMFORTABLE_THRESHOLD else "COOL"
            
            print(f"{data['city']:<15} {data['region']:<12} {data['color']}{data['temp']:>5.1f}°F {data['emoji']} {status:<15}")
    
    def run_interactive_mode(self):
        """Run the interactive weather monitor."""
        while True:
            print(f"\n{'='*60}")
            print("🏕️  INDIANA RV WEATHER MONITOR")
            print(f"{'='*60}")
            print("1. View state summary")
            print("2. View detailed forecast for a city")
            print("3. View all cities (detailed)")
            print("4. Exit")
            
            choice = input("\nSelect an option (1-4): ").strip()
            
            if choice == "1":
                self.display_state_summary()
            elif choice == "2":
                print(f"\nAvailable cities:")
                for i, city in enumerate(INDIANA_CITIES.keys(), 1):
                    print(f"{i}. {city}")
                
                try:
                    city_choice = int(input("\nSelect city number: ")) - 1
                    city_name = list(INDIANA_CITIES.keys())[city_choice]
                    coords = INDIANA_CITIES[city_name]
                    region = coords["region"]
                    self.display_city_weather(city_name, coords, region)
                except (ValueError, IndexError):
                    print("Invalid selection!")
            elif choice == "3":
                for city, coords in INDIANA_CITIES.items():
                    region = coords["region"]
                    self.display_city_weather(city, coords, region)
            elif choice == "4":
                print("Safe travels! 🚐")
                break
            else:
                print("Invalid option!")

def main():
    """Main function to run the weather monitor."""
    print("🏕️  Indiana RV Weather Monitor")
    print("Monitoring temperatures across Indiana to help you stay ahead of frost!")
    print("Using Open-Meteo API (free, no key required)")
    
    monitor = IndianaWeatherMonitor()
    
    # Check if running with command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "summary":
            monitor.display_state_summary()
        elif sys.argv[1] in INDIANA_CITIES:
            city = sys.argv[1]
            coords = INDIANA_CITIES[city]
            region = coords["region"]
            monitor.display_city_weather(city, coords, region)
        else:
            print(f"Unknown city: {sys.argv[1]}")
            print(f"Available cities: {', '.join(INDIANA_CITIES.keys())}")
    else:
        # Run interactive mode
        monitor.run_interactive_mode()

if __name__ == "__main__":
    main()
