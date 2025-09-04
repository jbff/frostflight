# Indiana RV Weather Monitor 🏕️

A Python application to monitor temperatures across Indiana, helping RV travelers stay ahead of frost and freezes by moving south as temperatures drop.

## Features

- **Current temperatures** across 13 key Indiana cities
- **7-day forecasts** with minimum/maximum temperatures
- **Freeze warnings** and travel recommendations
- **Color-coded display** for easy temperature assessment
- **No API key required** (uses free Open-Meteo API)
- **Interactive mode** for easy navigation
- **Command-line options** for quick checks

## Cities Monitored

The app monitors these cities from north to south across Indiana:

**North Region:**
- South Bend
- Gary

**Northeast Region:**
- Fort Wayne

**Northwest Region:**
- Lafayette

**Central Region:**
- Kokomo
- Indianapolis
- Muncie

**West Central Region:**
- Terre Haute

**South Central Region:**
- Bloomington
- Columbus

**South Region:**
- Jeffersonville
- New Albany

**Southwest Region:**
- Evansville

## Installation

1. Install Python 3.7 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Interactive Mode (Recommended)
```bash
python indiana_weather_monitor.py
```

This will start an interactive menu where you can:
- View a state-wide temperature summary
- Get detailed forecasts for specific cities
- View all cities with detailed information

### Command Line Options

**Quick state summary:**
```bash
python indiana_weather_monitor.py summary
```

**Detailed forecast for a specific city:**
```bash
python indiana_weather_monitor.py "Indianapolis"
python indiana_weather_monitor.py "Evansville"
```

## Temperature Thresholds

- 🔴 **FREEZE** (≤32°F): Avoid these areas
- 🟡 **FROST WARNING** (33-35°F): Exercise caution
- 🟠 **COOL** (36-49°F): Manageable but chilly
- 🟢 **COMFORTABLE** (≥50°F): Good RV weather

## Understanding the Output

### State Summary
Shows all cities sorted by current temperature (warmest first) with:
- Current temperature
- Region
- Status indicator
- Weather emoji

### Detailed City Forecast
For each city, you'll see:
- Current temperature and conditions
- 7-day forecast with min/max temperatures
- Freeze warnings and recommendations
- Color-coded temperature indicators

## Travel Recommendations

The app provides recommendations based on forecast analysis:
- ⚠️ **AVOID** - Freeze expected
- ⚠️ **Caution** - Frost warning
- ✅ **Good choice** - Comfortable temperatures
- 🟡 **Moderate** - Cool but manageable

## Data Source

This app uses the [Open-Meteo API](https://open-meteo.com/), which provides:
- Free access (no API key required)
- Accurate weather data from national weather services
- Current conditions and 7-day forecasts
- Data in Fahrenheit for easy understanding

## Tips for RV Travel

1. **Check daily** - Run the app each morning to plan your day
2. **Look ahead** - Use the 7-day forecast to plan your route
3. **Follow the warmth** - Generally move south as temperatures drop
4. **Watch for freezes** - Avoid areas with freezing temperatures
5. **Plan ahead** - Book campgrounds in warmer areas before they fill up

## Troubleshooting

**No internet connection:**
- The app requires internet to fetch weather data
- Check your connection and try again

**API errors:**
- The Open-Meteo API is generally very reliable
- If you encounter errors, wait a few minutes and try again

**City not found:**
- Make sure you're using the exact city name from the list
- Check spelling and capitalization

## Contributing

Feel free to suggest improvements or additional features! This app is designed to be simple and focused on helping RV travelers stay comfortable during their Indiana journey.

## License

This project is open source and available under the MIT License.
