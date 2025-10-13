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
import os
from datetime import datetime, timedelta
import sys
from typing import Dict, List, Tuple
from tqdm import tqdm

# Indiana cities from north to south for temperature monitoring

INDIANA_CITIES = {
  "Evansville": {
    "lat": 37.973585,
    "lon": -87.567388,
    "county": "Vanderburgh",
    "region": "Southwest"
  },
  "Petersburg": {
    "lat": 38.491567,
    "lon": -87.278844,
    "county": "Pike",
    "region": "Southwest"
  },
  "Washington": {
    "lat": 38.659387,
    "lon": -87.171883,
    "county": "Daviess",
    "region": "South Central"
  },
  "Vincennes": {
    "lat": 38.676353,
    "lon": -87.526877,
    "county": "Knox",
    "region": "Southwest"
  },
  "Columbus": {
    "lat": 39.201702,
    "lon": -85.920033,
    "county": "Bartholomew",
    "region": "South Central"
  },
  "Franklin": {
    "lat": 39.479841,
    "lon": -86.05618,
    "county": "Johnson",
    "region": "Central"
  },
  "Jeffersonville": {
    "lat": 38.356805,
    "lon": -85.663803,
    "county": "Clark",
    "region": "Southeast"
  },
  "Bloomington": {
    "lat": 39.170616,
    "lon": -86.53731,
    "county": "Monroe",
    "region": "South Central"
  },
  "Madison": {
    "lat": 38.735975,
    "lon": -85.376773,
    "county": "Jefferson",
    "region": "Southeast"
  },
  "Terre Haute": {
    "lat": 39.460198,
    "lon": -87.415872,
    "county": "Vigo",
    "region": "West Central"
  },
  "Marion": {
    "lat": 40.557644,
    "lon": -85.658192,
    "county": "Grant",
    "region": ""
  },
  "Winchester": {
    "lat": 40.172062,
    "lon": -84.98193,
    "county": "Randolph",
    "region": "East Central"
  },
  "Jasper": {
    "lat": 38.391426,
    "lon": -86.930831,
    "county": "Dubois",
    "region": "Southwest"
  },
  "Bluffton": {
    "lat": 40.738931,
    "lon": -85.173575,
    "county": "Wells",
    "region": "Northeast"
  },
  "Bedford": {
    "lat": 38.861572,
    "lon": -86.483193,
    "county": "Lawrence",
    "region": "South Central"
  },
  "Noblesville": {
    "lat": 40.046067,
    "lon": -86.015338,
    "county": "Hamilton",
    "region": "Central"
  },
  "Rockport": {
    "lat": 37.882624,
    "lon": -87.046678,
    "county": "Spencer",
    "region": "Southwest"
  },
  "Auburn": {
    "lat": 41.366455,
    "lon": -85.055219,
    "county": "DeKalb",
    "region": "North"
  },
  "Rochester": {
    "lat": 41.06547,
    "lon": -86.215113,
    "county": "Rochester",
    "region": ""
  },
  "La Porte": {
    "lat": 41.612116,
    "lon": -86.722873,
    "county": "La Porte",
    "region": ""
  },
  "Albion": {
    "lat": 41.396074,
    "lon": -85.424633,
    "county": "Albion",
    "region": ""
  },
  "Boonville": {
    "lat": 38.049512,
    "lon": -87.274983,
    "county": "Boonville",
    "region": ""
  },
  "Anderson": {
    "lat": 40.107484,
    "lon": -85.67866,
    "county": "Anderson",
    "region": ""
  },
  "Winamac": {
    "lat": 41.050849,
    "lon": -86.603337,
    "county": "Winamac",
    "region": ""
  },
  "Peru": {
    "lat": 40.754415,
    "lon": -86.06898,
    "county": "Peru",
    "region": ""
  },
  "Williamsport": {
    "lat": 40.287966,
    "lon": -87.293833,
    "county": "Williamsport",
    "region": ""
  },
  "Kokomo": {
    "lat": 40.488083,
    "lon": -86.130915,
    "county": "Kokomo",
    "region": ""
  },
  "Decatur": {
    "lat": 40.828114,
    "lon": -84.925398,
    "county": "Decatur",
    "region": ""
  },
  "Columbia City": {
    "lat": 41.157283,
    "lon": -85.490833,
    "county": "Columbia City",
    "region": ""
  },
  "Crown Point": {
    "lat": 41.447993,
    "lon": -87.369939,
    "county": "Crown Point",
    "region": ""
  },
  "Delphi": {
    "lat": 40.586365,
    "lon": -86.674796,
    "county": "Delphi",
    "region": ""
  },
  "Connersville": {
    "lat": 39.64082,
    "lon": -85.140563,
    "county": "Connersville",
    "region": ""
  },
  "Crawfordsville": {
    "lat": 40.064128,
    "lon": -86.912914,
    "county": "Crawfordsville",
    "region": ""
  },
  "Greensburg": {
    "lat": 39.337218,
    "lon": -85.483475,
    "county": "Greensburg",
    "region": ""
  },
  "Goshen": {
    "lat": 41.587421,
    "lon": -85.838177,
    "county": "Goshen",
    "region": ""
  },
  "Greencastle": {
    "lat": 39.644373,
    "lon": -86.864968,
    "county": "Greencastle",
    "region": ""
  },
  "Hartford City": {
    "lat": 40.45175,
    "lon": -85.367962,
    "county": "Hartford City",
    "region": ""
  },
  "Monticello": {
    "lat": 40.745219,
    "lon": -86.7627,
    "county": "Monticello",
    "region": ""
  },
  "Logansport": {
    "lat": 40.754712,
    "lon": -86.366868,
    "county": "Logansport",
    "region": ""
  },
  "Lawrenceburg": {
    "lat": 39.09131,
    "lon": -84.850352,
    "county": "Lawrenceburg",
    "region": ""
  },
  "Knox": {
    "lat": 41.299536,
    "lon": -86.622246,
    "county": "Knox",
    "region": "Southwest"
  },
  "Lafayette": {
    "lat": 40.417991,
    "lon": -86.894521,
    "county": "Lafayette",
    "region": ""
  },
  "Muncie": {
    "lat": 40.194241,
    "lon": -85.38731,
    "county": "Muncie",
    "region": ""
  },
  "Martinsville": {
    "lat": 39.425218,
    "lon": -86.428927,
    "county": "Martinsville",
    "region": ""
  },
  "Lebanon": {
    "lat": 40.048642,
    "lon": -86.468507,
    "county": "Lebanon",
    "region": ""
  },
  "New Castle": {
    "lat": 39.930436,
    "lon": -85.371398,
    "county": "New Castle",
    "region": ""
  },
  "Portland": {
    "lat": 40.433888,
    "lon": -84.978766,
    "county": "Portland",
    "region": ""
  },
  "Salem": {
    "lat": 38.605672,
    "lon": -86.100769,
    "county": "Salem",
    "region": ""
  },
  "Rensselaer": {
    "lat": 40.935868,
    "lon": -87.150941,
    "county": "Rensselaer",
    "region": ""
  },
  "Sullivan": {
    "lat": 39.094888,
    "lon": -87.407705,
    "county": "Sullivan",
    "region": ""
  },
  "Shelbyville": {
    "lat": 39.521333,
    "lon": -85.778476,
    "county": "Shelbyville",
    "region": ""
  },
  "South Bend": {
    "lat": 41.675147,
    "lon": -86.252761,
    "county": "South Bend",
    "region": ""
  },
  "Plymouth": {
    "lat": 41.34391,
    "lon": -86.310502,
    "county": "Plymouth",
    "region": ""
  },
  "Richmond": {
    "lat": 39.828148,
    "lon": -84.895686,
    "county": "Richmond",
    "region": ""
  },
  "Rising Sun": {
    "lat": 38.950084,
    "lon": -84.856561,
    "county": "Rising Sun",
    "region": ""
  },
  "Rushville": {
    "lat": 39.607846,
    "lon": -85.444067,
    "county": "Rushville",
    "region": ""
  },
  "Tipton": {
    "lat": 40.281656,
    "lon": -86.040734,
    "county": "Tipton",
    "region": "Central"
  },
  "Tell City": {
    "lat": 37.961778,
    "lon": -86.750593,
    "county": "Tell City",
    "region": ""
  },
  "Bloomfield": {
    "lat": 39.02627,
    "lon": -86.937899,
    "county": "Bloomfield",
    "region": ""
  },
  "Wabash": {
    "lat": 40.798336,
    "lon": -85.821408,
    "county": "Wabash",
    "region": ""
  },
  "Warsaw": {
    "lat": 41.238597,
    "lon": -85.857273,
    "county": "Warsaw",
    "region": ""
  },
  "Huntington": {
    "lat": 40.881106,
    "lon": -85.493463,
    "county": "Huntington",
    "region": "Northeast"
  },
  "New Albany": {
    "lat": 38.284347,
    "lon": -85.8249,
    "county": "New Albany",
    "region": ""
  },
  "Scottsburg": {
    "lat": 38.685286,
    "lon": -85.769592,
    "county": "Scottsburg",
    "region": ""
  },
  "Covington": {
    "lat": 40.137062,
    "lon": -87.3971,
    "county": "Covington",
    "region": ""
  },
  "Frankfort": {
    "lat": 40.280136,
    "lon": -86.508923,
    "county": "Frankfort",
    "region": ""
  },
  "Brownstown": {
    "lat": 38.87845,
    "lon": -86.041372,
    "county": "Brownstown",
    "region": ""
  },
  "Brazil": {
    "lat": 39.524505,
    "lon": -87.119396,
    "county": "Brazil",
    "region": ""
  },
  "Princeton": {
    "lat": 38.355724,
    "lon": -87.568071,
    "county": "Princeton",
    "region": ""
  },
  "Corydon": {
    "lat": 38.2044,
    "lon": -86.123276,
    "county": "Corydon",
    "region": ""
  },
  "Spencer": {
    "lat": 39.285572,
    "lon": -86.761875,
    "county": "Spencer",
    "region": "Southwest"
  },
  "Greenfield": {
    "lat": 39.784096,
    "lon": -85.767908,
    "county": "Greenfield",
    "region": ""
  },
  "LaGrange": {
    "lat": 41.645144,
    "lon": -85.419063,
    "county": "LaGrange",
    "region": "North"
  },
  "Fort Wayne": {
    "lat": 41.07892,
    "lon": -85.137058,
    "county": "Fort Wayne",
    "region": ""
  },
  "Valparaiso": {
    "lat": 41.466504,
    "lon": -87.062868,
    "county": "Valparaiso",
    "region": ""
  },
  "Angola": {
    "lat": 41.631996,
    "lon": -84.998467,
    "county": "Angola",
    "region": ""
  },
  "Rockville": {
    "lat": 39.762054,
    "lon": -87.228344,
    "county": "Rockville",
    "region": ""
  },
  "Brookville": {
    "lat": 39.425832,
    "lon": -85.010104,
    "county": "Brookville",
    "region": ""
  },
  "Danville": {
    "lat": 39.761286,
    "lon": -86.519812,
    "county": "Danville",
    "region": ""
  },
  "Shoals": {
    "lat": 38.665281,
    "lon": -86.793076,
    "county": "Shoals",
    "region": ""
  },
  "Vernon": {
    "lat": 38.985719,
    "lon": -85.607907,
    "county": "Vernon",
    "region": ""
  },
  "Vevay": {
    "lat": 38.747067,
    "lon": -85.068968,
    "county": "Vevay",
    "region": ""
  },
  "Paoli": {
    "lat": 38.555711,
    "lon": -86.466317,
    "county": "Paoli",
    "region": ""
  },
  "Fowler": {
    "lat": 40.617171,
    "lon": -87.315713,
    "county": "Fowler",
    "region": ""
  },
  "Kentland": {
    "lat": 40.76961,
    "lon": -87.444434,
    "county": "Kentland",
    "region": ""
  },
  "Nashville": {
    "lat": 39.208799,
    "lon": -86.245583,
    "county": "Nashville",
    "region": ""
  },
  "Indianapolis": {
    "lat": 39.767919,
    "lon": -86.153621,
    "county": "Indianapolis",
    "region": ""
  },
  "Liberty": {
    "lat": 39.635035,
    "lon": -84.930296,
    "county": "Liberty",
    "region": ""
  },
  "Versailles": {
    "lat": 39.073037,
    "lon": -85.251607,
    "county": "Versailles",
    "region": ""
  },
  "English": {
    "lat": 38.352803,
    "lon": -86.446609,
    "county": "English",
    "region": ""
  },
  "Mount Vernon": {
    "lat": 37.93115,
    "lon": -87.894319,
    "county": "Mount Vernon",
    "region": ""
  },
  "Newport": {
    "lat": 39.884803,
    "lon": -87.409189,
    "county": "Newport",
    "region": ""
  }
}

#INDIANA_CITIES = {
#    "South Bend": {"lat": 41.6764, "lon": -86.2520, "region": "North"},
#    "Gary": {"lat": 41.5934, "lon": -87.3464, "region": "North"},
#    "Fort Wayne": {"lat": 41.0793, "lon": -85.1394, "region": "Northeast"},
#    "Lafayette": {"lat": 40.4167, "lon": -86.8753, "region": "Northwest"},
#    "Kokomo": {"lat": 40.4864, "lon": -86.1336, "region": "Central"},
#    "Indianapolis": {"lat": 39.7684, "lon": -86.1581, "region": "Central"},
#    "Muncie": {"lat": 40.1934, "lon": -85.3864, "region": "East Central"},
#    "Terre Haute": {"lat": 39.4667, "lon": -87.4139, "region": "West Central"},
#    "Bloomington": {"lat": 39.1653, "lon": -86.5264, "region": "South Central"},
#    "Columbus": {"lat": 39.2014, "lon": -85.9214, "region": "South Central"},
#    "Jeffersonville": {"lat": 38.2775, "lon": -85.7372, "region": "South"},
#    "Evansville": {"lat": 37.9716, "lon": -87.5711, "region": "Southwest"},
#    "New Albany": {"lat": 38.2856, "lon": -85.8244, "region": "South"}
#}

# County ID to name mapping (from county_list.csv)
COUNTY_MAPPING = {
    0: "Adams", 1: "Allen", 2: "Bartholomew", 3: "Benton", 4: "Blackford", 5: "Boone",
    6: "Brown", 7: "Carroll", 8: "Cass", 9: "Clark", 10: "Clay", 11: "Clinton",
    12: "Crawford", 13: "Daviess", 14: "Dearborn", 15: "Decatur", 16: "DeKalb", 17: "Delaware",
    18: "Dubois", 19: "Elkhart", 20: "Fayette", 21: "Floyd", 22: "Fountain", 23: "Franklin",
    24: "Fulton", 25: "Gibson", 26: "Grant", 27: "Greene", 28: "Hamilton", 29: "Hancock",
    30: "Harrison", 31: "Hendricks", 32: "Henry", 33: "Howard", 34: "Huntington", 35: "Jackson",
    36: "Jasper", 37: "Jay", 38: "Jefferson", 39: "Jennings", 40: "Johnson", 41: "Knox",
    42: "Kosciusko", 43: "LaGrange", 44: "Lake", 45: "LaPorte", 46: "Lawrence", 47: "Madison",
    48: "Marion", 49: "Marshall", 50: "Martin", 51: "Miami", 52: "Monroe", 53: "Montgomery",
    54: "Morgan", 55: "Newton", 56: "Noble", 57: "Ohio", 58: "Orange", 59: "Owen",
    60: "Parke", 61: "Perry", 62: "Pike", 63: "Porter", 64: "Posey", 65: "Pulaski",
    66: "Putnam", 67: "Randolph", 68: "Ripley", 69: "Rush", 70: "Scott", 71: "Shelby",
    72: "Spencer", 73: "St. Joseph", 74: "Starke", 75: "Steuben", 76: "Sullivan", 77: "Switzerland",
    78: "Tippecanoe", 79: "Tipton", 80: "Union", 81: "Vanderburgh", 82: "Vermillion", 83: "Vigo",
    84: "Wabash", 85: "Warren", 86: "Warrick", 87: "Washington", 88: "Wayne", 89: "Wells",
    90: "White", 91: "Whitley"
}

# City to correct county name mapping (fixing the incorrect county names in INDIANA_CITIES)
CITY_TO_COUNTY_MAPPING = {
    "Evansville": "Vanderburgh", "Petersburg": "Pike", "Washington": "Daviess", "Vincennes": "Knox",
    "Columbus": "Bartholomew", "Franklin": "Johnson", "Jeffersonville": "Clark", "Bloomington": "Monroe",
    "Madison": "Jefferson", "Terre Haute": "Vigo", "Marion": "Grant", "Winchester": "Randolph",
    "Jasper": "Dubois", "Bluffton": "Wells", "Bedford": "Lawrence", "Noblesville": "Hamilton",
    "Rockport": "Spencer", "Auburn": "DeKalb", "Rochester": "Fulton", "La Porte": "LaPorte",
    "Albion": "Noble", "Boonville": "Warrick", "Anderson": "Madison", "Winamac": "Pulaski",
    "Peru": "Miami", "Williamsport": "Warren", "Kokomo": "Howard", "Decatur": "Adams",
    "Columbia City": "Whitley", "Crown Point": "Lake", "Delphi": "Carroll", "Connersville": "Fayette",
    "Crawfordsville": "Montgomery", "Greensburg": "Decatur", "Goshen": "Elkhart", "Greencastle": "Putnam",
    "Hartford City": "Blackford", "Monticello": "White", "Logansport": "Cass", "Lawrenceburg": "Dearborn",
    "Knox": "Starke", "Lafayette": "Tippecanoe", "Muncie": "Delaware", "Martinsville": "Morgan",
    "Lebanon": "Boone", "New Castle": "Henry", "Portland": "Jay", "Salem": "Washington",
    "Rensselaer": "Jasper", "Sullivan": "Sullivan", "Shelbyville": "Shelby", "South Bend": "St. Joseph",
    "Plymouth": "Marshall", "Richmond": "Wayne", "Rising Sun": "Ohio", "Rushville": "Rush",
    "Tipton": "Tipton", "Tell City": "Perry", "Bloomfield": "Greene", "Wabash": "Wabash",
    "Warsaw": "Kosciusko", "Huntington": "Huntington", "New Albany": "Floyd", "Scottsburg": "Scott",
    "Covington": "Fountain", "Frankfort": "Clinton", "Brownstown": "Jackson", "Brazil": "Clay",
    "Princeton": "Gibson", "Corydon": "Harrison", "Spencer": "Owen", "Greenfield": "Hancock",
    "LaGrange": "LaGrange", "Fort Wayne": "Allen", "Valparaiso": "Porter", "Angola": "Steuben",
    "Rockville": "Parke", "Brookville": "Franklin", "Danville": "Hendricks", "Shoals": "Martin",
    "Vernon": "Jennings", "Vevay": "Switzerland", "Paoli": "Orange", "Fowler": "Benton",
    "Kentland": "Newton", "Nashville": "Brown", "Indianapolis": "Marion", "Liberty": "Union",
    "Versailles": "Ripley", "English": "Crawford", "Mount Vernon": "Posey", "Newport": "Vermillion"
}

# Indiana map grid (from indiana_map.csv) - -1 represents blank spaces
INDIANA_MAP_GRID = [
    [-1, -1, -1, 44, 63, 45, 73, 19, 43, 75, 75],
    [-1, -1, -1, 44, 63, 45, 49, 42, 56, 16, 16],
    [-1, -1, -1, 44, 63, 74, 49, 42, 91, 1, 1],
    [-1, -1, -1, 55, 36, 65, 24, 84, 34, 89, 0],
    [-1, -1, -1, 55, 36, 90, 8, 51, 26, 4, 37],
    [-1, -1, -1, 3, 3, 78, 7, 33, 47, 17, 67],
    [-1, -1, -1, 82, 85, 78, 11, 79, 47, 17, 67],
    [-1, -1, -1, 82, 22, 53, 5, 28, 47, 32, 88],
    [-1, -1, -1, 60, 66, 31, 48, 29, 69, 20, 80],
    [-1, -1, -1, 83, 66, 54, 40, 71, 69, 23, 23],
    [-1, -1, -1, 83, 10, 59, 52, 6, 2, 15, 23],
    [-1, -1, -1, 76, 27, 27, 46, 35, 39, 68, 14],
    [-1, -1, -1, 41, 13, 50, 46, 87, 39, 68, 57],
    [-1, -1, 41, 41, 13, 50, 58, 87, 70, 38, 77],
    [-1, 25, 25, 62, 18, 12, 30, 21, 9, -1, -1],
    [64, 81, 86, 72, 61, -1, 30, -1, -1, -1, -1]
]

# Temperature thresholds for frost risk assessment
SEVERE_FREEZE_THRESHOLD = 20  # Fahrenheit - Severe freeze risk
FREEZE_THRESHOLD = 32  # Fahrenheit - Freeze risk
FROST_WARNING_THRESHOLD = 40  # Fahrenheit - Frost warning
MILD_THRESHOLD = 60  # Fahrenheit - Mild conditions
WARM_THRESHOLD = 70  # Fahrenheit - Warm conditions
HOT_THRESHOLD = 85  # Fahrenheit - Hot conditions

class IndianaWeatherMonitor:
    def __init__(self):
        self.api_url = "https://api.open-meteo.com/v1/forecast"
        self.timezone = "America/Indiana/Indianapolis"
        self.weather_data = {}  # Cache for weather data
        self.data_fetched = False
        self.cache_file = "weather_cache.json"
        self.cache_max_age_hours = 6  # Cache expires after 6 hours
        
    def is_cache_valid(self) -> bool:
        """Check if cache file exists and is not too old."""
        if not os.path.exists(self.cache_file):
            return False
        
        try:
            # Check file modification time
            cache_time = os.path.getmtime(self.cache_file)
            current_time = datetime.now().timestamp()
            age_hours = (current_time - cache_time) / 3600
            
            return age_hours < self.cache_max_age_hours
        except OSError:
            return False
    
    def load_cache(self) -> bool:
        """Load weather data from cache file."""
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            self.weather_data = cache_data.get('weather_data', {})
            self.data_fetched = True
            
            cache_timestamp = cache_data.get('timestamp', 'Unknown')
            print(f"📁 Loaded weather data from cache (cached at {cache_timestamp})")
            return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"❌ Failed to load cache: {e}")
            return False
    
    def save_cache(self):
        """Save weather data to cache file."""
        try:
            cache_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'weather_data': self.weather_data
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"💾 Weather data cached to {self.cache_file}")
        except Exception as e:
            print(f"❌ Failed to save cache: {e}")
    
    def clear_cache(self):
        """Delete the cache file."""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                print(f"🗑️  Cache file {self.cache_file} deleted")
        except OSError as e:
            print(f"❌ Failed to delete cache: {e}")
        
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
    
    def fetch_all_weather_data(self, force_refresh=False):
        """Fetch weather data for all Indiana cities and cache it."""
        if self.data_fetched and not force_refresh:
            return
        
        # Try to load from cache first (unless force refresh)
        if not force_refresh and self.is_cache_valid():
            if self.load_cache():
                return
        
        # If force refresh, clear the cache
        if force_refresh:
            self.clear_cache()
            self.data_fetched = False
            self.weather_data = {}
            
        print("🌡️  Fetching weather data for all Indiana cities...")
        print("This may take a moment...")
        
        # Use tqdm for progress bar with county names in the bar
        pbar = tqdm(INDIANA_CITIES.items(), desc="Fetching weather data", unit="county")
        for city, coords in pbar:
            county_name = CITY_TO_COUNTY_MAPPING.get(city, "Unknown")
            pbar.set_description(f"Fetching {county_name} County")
            data = self.get_weather_data(city, coords)
            if data:
                self.weather_data[city] = data
            else:
                tqdm.write(f"  ❌ Failed to fetch data for {city} ({county_name} County)")
        
        self.data_fetched = True
        print("✅ Weather data fetch complete!")
        
        # Save to cache
        self.save_cache()
        print()
    
    def celsius_to_fahrenheit(self, celsius: float) -> float:
        """Convert Celsius to Fahrenheit."""
        return (celsius * 9/5) + 32
    
    def get_temperature_color(self, temp: float) -> str:
        """Get color code for temperature display."""
        if temp <= SEVERE_FREEZE_THRESHOLD:
            return "🟪"  # Purple square for severe freeze
        elif temp <= FREEZE_THRESHOLD:
            return "🟦"  # Light blue square for freezing
        elif temp <= FROST_WARNING_THRESHOLD:
            return "🟫"  # Brown square for frost warning
        elif temp <= MILD_THRESHOLD:
            return "🟩"  # Green square for mild
        elif temp <= WARM_THRESHOLD:
            return "🟨"  # Yellow square for warm
        elif temp <= HOT_THRESHOLD:
            return "🟧"  # Orange square for hot
        else:
            return "🟥"  # Red square for very hot
    
    def get_weather_emoji(self, temp: float) -> str:
        """Get weather emoji based on temperature."""
        if temp <= SEVERE_FREEZE_THRESHOLD:
            return "🥶"
        elif temp <= FREEZE_THRESHOLD:
            return "❄️"
        elif temp <= FROST_WARNING_THRESHOLD:
            return "🥶"
        elif temp <= MILD_THRESHOLD:
            return "🧥"
        else:
            return "☀️"
    
    def get_county_id_from_name(self, county_name: str) -> int:
        """Get county ID from county name."""
        for county_id, name in COUNTY_MAPPING.items():
            if name == county_name:
                return county_id
        return -1  # Not found
    
    def get_county_temperature_data(self):
        """Get temperature data mapped by county ID."""
        if not self.data_fetched:
            self.fetch_all_weather_data()
        
        county_temps = {}
        
        for city, data in self.weather_data.items():
            if not data:
                continue
                
            # Use the correct county mapping instead of the incorrect one in INDIANA_CITIES
            county_name = CITY_TO_COUNTY_MAPPING.get(city, "Unknown")
            county_id = self.get_county_id_from_name(county_name)
            
            if county_id == -1:
                continue  # County not found in mapping
            
            # Get the minimum temperature for the next 7 days
            min_temps = data["daily"]["temperature_2m_min"]
            coldest_temp = min(min_temps)
            
            county_temps[county_id] = {
                "county_name": county_name,
                "coldest_temp": coldest_temp,
                "city": city
            }
        
        return county_temps
    
    def get_county_today_high_data(self):
        """Get today's high temperature data mapped by county ID."""
        if not self.data_fetched:
            self.fetch_all_weather_data()
        
        county_temps = {}
        
        for city, data in self.weather_data.items():
            if not data:
                continue
                
            # Use the correct county mapping instead of the incorrect one in INDIANA_CITIES
            county_name = CITY_TO_COUNTY_MAPPING.get(city, "Unknown")
            county_id = self.get_county_id_from_name(county_name)
            
            if county_id == -1:
                continue  # County not found in mapping
            
            # Get today's maximum temperature (first day in forecast)
            today_max_temp = data["daily"]["temperature_2m_max"][0]
            
            county_temps[county_id] = {
                "county_name": county_name,
                "high_temp": today_max_temp,
                "city": city
            }
        
        return county_temps
    
    def get_map_color(self, temp: float) -> str:
        """Get color code for map visualization based on temperature (cool to warm)."""
        if temp <= SEVERE_FREEZE_THRESHOLD:
            return "🟪"  # Purple square for severe freeze (≤20°F)
        elif temp <= FREEZE_THRESHOLD:
            return "🟦"  # Light blue square for freeze (≤32°F)
        elif temp <= FROST_WARNING_THRESHOLD:
            return "🟫"  # Brown square for frost warning (≤40°F)
        elif temp <= MILD_THRESHOLD:
            return "🟩"  # Green square for mild (40-60°F)
        elif temp <= WARM_THRESHOLD:
            return "🟨"  # Yellow square for warm (60-70°F)
        elif temp <= HOT_THRESHOLD:
            return "🟧"  # Orange square for hot (70-85°F)
        else:
            return "🟥"  # Red square for very hot (>85°F)
    
    def display_indiana_map(self):
        """Display Indiana map with temperature-based coloring for frost risk assessment."""
        county_temps = self.get_county_temperature_data()
        
        print(f"\n{'='*80}")
        print(f"🗺️  INDIANA FROST RISK MAP - Next 7 Days Coldest Temperatures")
        print(f"{'='*80}")
        print("TEMPERATURE LEGEND (Coldest temperature each county will reach in next 7 days):")
        print("🟪 Purple = Severe Freeze (≤20°F) - AVOID")
        print("🟦 Light Blue = Freeze (≤32°F) - AVOID") 
        print("🟫 Brown = Frost Warning (≤40°F) - CAUTION")
        print("🟩 Green = Mild (40-60°F) - WATCH")
        print("🟨 Yellow = Warm (60-70°F) - GOOD")
        print("🟧 Orange = Hot (70-85°F) - COMFORTABLE")
        print("🟥 Red = Very Hot (>85°F) - HOT")
        print(f"{'='*80}")
        
        # Display the map
        for row in INDIANA_MAP_GRID:
            map_line = ""
            for county_id in row:
                if county_id == -1:
                    map_line += " "  # Space for blank areas
                elif county_id in county_temps:
                    temp = county_temps[county_id]["coldest_temp"]
                    color = self.get_map_color(temp)
                    map_line += color
                else:
                    map_line += " "  # Space for no data
            print(map_line)
        
        print(f"{'='*80}")
        print(f"Map shows {len(county_temps)} counties with weather data")
        print("Use other menu options for detailed temperature information")
    
    def display_indiana_today_high_map(self):
        """Display Indiana map with today's high temperature coloring."""
        county_temps = self.get_county_today_high_data()
        
        print(f"\n{'='*80}")
        print(f"🗺️  INDIANA TODAY'S HIGH TEMPERATURE MAP")
        print(f"{'='*80}")
        print("TEMPERATURE LEGEND (Today's high temperature for each county):")
        print("🟪 Purple = Severe Freeze (≤20°F) - AVOID")
        print("🟦 Light Blue = Freeze (≤32°F) - AVOID") 
        print("🟫 Brown = Frost Warning (≤40°F) - CAUTION")
        print("🟩 Green = Mild (40-60°F) - WATCH")
        print("🟨 Yellow = Warm (60-70°F) - GOOD")
        print("🟧 Orange = Hot (70-85°F) - COMFORTABLE")
        print("🟥 Red = Very Hot (>85°F) - HOT")
        print(f"{'='*80}")
        
        # Display the map
        for row in INDIANA_MAP_GRID:
            map_line = ""
            for county_id in row:
                if county_id == -1:
                    map_line += " "  # Space for blank areas
                elif county_id in county_temps:
                    temp = county_temps[county_id]["high_temp"]
                    color = self.get_map_color(temp)
                    map_line += color
                else:
                    map_line += " "  # Space for no data
            print(map_line)
        
        print(f"{'='*80}")
        print(f"Map shows {len(county_temps)} counties with weather data")
        print("Use other menu options for detailed temperature information")
    
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
            elif min_temp >= MILD_THRESHOLD:
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
    
    def analyze_today_freezing(self):
        """Analyze which regions have freezing temperatures today vs above freezing."""
        if not self.data_fetched:
            self.fetch_all_weather_data()
        
        freezing_today = []
        above_freezing_today = []
        
        for city, data in self.weather_data.items():
            if not data:
                continue
                
            # Get today's minimum temperature (first day in forecast)
            today_min_temp = data["daily"]["temperature_2m_min"][0]
            region = INDIANA_CITIES[city]["region"]
            
            city_info = {
                "city": city,
                "region": region,
                "min_temp": today_min_temp,
                "max_temp": data["daily"]["temperature_2m_max"][0]
            }
            
            if today_min_temp <= FREEZE_THRESHOLD:
                freezing_today.append(city_info)
            else:
                above_freezing_today.append(city_info)
        
        return freezing_today, above_freezing_today
    
    def analyze_week_freezing(self):
        """Analyze which regions have freezing temperatures in the next week."""
        if not self.data_fetched:
            self.fetch_all_weather_data()
        
        freezing_this_week = []
        no_freezing_this_week = []
        
        for city, data in self.weather_data.items():
            if not data:
                continue
                
            min_temps = data["daily"]["temperature_2m_min"]
            region = INDIANA_CITIES[city]["region"]
            
            # Check if any day in the next 7 days has freezing temps
            has_freezing = any(temp <= FREEZE_THRESHOLD for temp in min_temps)
            
            city_info = {
                "city": city,
                "region": region,
                "min_temps": min_temps,
                "max_temps": data["daily"]["temperature_2m_max"],
                "dates": data["daily"]["time"]
            }
            
            if has_freezing:
                freezing_this_week.append(city_info)
            else:
                no_freezing_this_week.append(city_info)
        
        return freezing_this_week, no_freezing_this_week
    
    def display_today_freezing_analysis(self):
        """Display analysis of today's freezing vs above-freezing regions."""
        freezing_today, above_freezing_today = self.analyze_today_freezing()
        
        print(f"\n{'='*80}")
        print(f"❄️  TODAY'S FREEZING ANALYSIS - {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'='*80}")
        
        print(f"\n🔴 REGIONS WITH FREEZING TEMPERATURES TODAY ({len(freezing_today)} cities):")
        if freezing_today:
            print(f"{'City':<15} {'Region':<12} {'Min Temp':<10} {'Max Temp':<10} {'Status'}")
            print("-" * 70)
            for city_info in sorted(freezing_today, key=lambda x: x['min_temp']):
                status = "FREEZE" if city_info['min_temp'] <= FREEZE_THRESHOLD else "FROST WARNING"
                print(f"{city_info['city']:<15} {city_info['region']:<12} {city_info['min_temp']:>7.1f}°F {city_info['max_temp']:>7.1f}°F {status}")
        else:
            print("  ✅ No cities with freezing temperatures today!")
        
        print(f"\n🟢 REGIONS ABOVE FREEZING TODAY ({len(above_freezing_today)} cities):")
        if above_freezing_today:
            print(f"{'City':<15} {'Region':<12} {'Min Temp':<10} {'Max Temp':<10} {'Status'}")
            print("-" * 70)
            for city_info in sorted(above_freezing_today, key=lambda x: x['min_temp'], reverse=True):
                status = "WARM" if city_info['min_temp'] >= MILD_THRESHOLD else "MILD"
                print(f"{city_info['city']:<15} {city_info['region']:<12} {city_info['min_temp']:>7.1f}°F {city_info['max_temp']:>7.1f}°F {status}")
        else:
            print("  ❌ All cities have freezing temperatures today!")
    
    def display_week_freezing_analysis(self):
        """Display analysis of freezing temperatures in the next week."""
        freezing_this_week, no_freezing_this_week = self.analyze_week_freezing()
        
        print(f"\n{'='*80}")
        print(f"📅 NEXT WEEK FREEZING ANALYSIS")
        print(f"{'='*80}")
        
        print(f"\n🔴 REGIONS WITH FREEZING TEMPERATURES THIS WEEK ({len(freezing_this_week)} cities):")
        if freezing_this_week:
            print(f"{'City':<15} {'Region':<12} {'Freeze Days':<15} {'Details'}")
            print("-" * 80)
            for city_info in freezing_this_week:
                freeze_days = []
                for i, (date, min_temp) in enumerate(zip(city_info['dates'], city_info['min_temps'])):
                    if min_temp <= FREEZE_THRESHOLD:
                        display_date = date.split('T')[0] if 'T' in date else date
                        freeze_days.append(f"{display_date}({min_temp:.1f}°F)")
                
                freeze_details = ", ".join(freeze_days[:3])  # Show first 3 freeze days
                if len(freeze_days) > 3:
                    freeze_details += f" (+{len(freeze_days)-3} more)"
                
                print(f"{city_info['city']:<15} {city_info['region']:<12} {len(freeze_days):<15} {freeze_details}")
        else:
            print("  ✅ No cities with freezing temperatures this week!")
        
        print(f"\n🟢 REGIONS WITHOUT FREEZING THIS WEEK ({len(no_freezing_this_week)} cities):")
        if no_freezing_this_week:
            print(f"{'City':<15} {'Region':<12} {'Warmest Min':<12} {'Coldest Min':<12}")
            print("-" * 60)
            for city_info in sorted(no_freezing_this_week, key=lambda x: min(x['min_temps']), reverse=True):
                warmest_min = max(city_info['min_temps'])
                coldest_min = min(city_info['min_temps'])
                print(f"{city_info['city']:<15} {city_info['region']:<12} {warmest_min:>9.1f}°F {coldest_min:>9.1f}°F")
        else:
            print("  ❌ All cities have freezing temperatures this week!")
    
    def display_city_weather(self, city: str, coords: Dict, region: str):
        """Display weather information for a single city."""
        print(f"\n{'='*60}")
        print(f"🌡️  {city} ({region})")
        print(f"{'='*60}")
        
        if not self.data_fetched:
            self.fetch_all_weather_data()
        
        data = self.weather_data.get(city)
        if not data:
            print(f"❌ No data available for {city}")
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
            elif min_temp >= MILD_THRESHOLD:
                status = "WARM"
            else:
                status = "COOL"
            
            print(f"{display_date:<12} {min_color}{min_temp:>5.1f}°F {max_color}{max_temp:>5.1f}°F {status:<15}")
        
        # Recommendation
        recommendation = self.get_recommendation(city, analysis)
        print(f"\n{recommendation}")
    
    def display_state_summary(self):
        """Display a summary of all cities with current temperatures."""
        if not self.data_fetched:
            self.fetch_all_weather_data()
            
        print(f"\n{'='*80}")
        print(f"🗺️  INDIANA WEATHER SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*80}")
        
        city_data = []
        
        for city, coords in INDIANA_CITIES.items():
            data = self.weather_data.get(city)
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
            status = "SEVERE FREEZE" if data["temp"] <= SEVERE_FREEZE_THRESHOLD else \
                    "FREEZE" if data["temp"] <= FREEZE_THRESHOLD else \
                    "FROST WARNING" if data["temp"] <= FROST_WARNING_THRESHOLD else \
                    "MILD" if data["temp"] <= MILD_THRESHOLD else \
                    "WARM" if data["temp"] <= WARM_THRESHOLD else \
                    "HOT" if data["temp"] <= HOT_THRESHOLD else "VERY HOT"
            
            print(f"{data['city']:<15} {data['region']:<12} {data['color']}{data['temp']:>5.1f}°F {data['emoji']} {status:<15}")
    
    def run_interactive_mode(self):
        """Run the interactive weather monitor."""
        # Automatically fetch data on startup
        self.fetch_all_weather_data()
        
        while True:
            print(f"\n{'='*60}")
            print("🏕️  INDIANA RV WEATHER MONITOR")
            print(f"{'='*60}")
            print("1. View state summary")
            print("2. View detailed forecast for a city")
            print("3. View all cities (detailed)")
            print("4. Today's freezing analysis")
            print("5. Next week freezing analysis")
            print("6. Indiana temperature map (7-day coldest)")
            print("7. Indiana temperature map (today's high)")
            print("8. Refresh weather data (from cache)")
            print("9. Force refresh weather data (from API)")
            print("10. Exit")
            
            choice = input("\nSelect an option (1-10): ").strip()
            
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
                self.display_today_freezing_analysis()
            elif choice == "5":
                self.display_week_freezing_analysis()
            elif choice == "6":
                self.display_indiana_map()
            elif choice == "7":
                self.display_indiana_today_high_map()
            elif choice == "8":
                print("🔄 Refreshing weather data from cache...")
                self.data_fetched = False
                self.weather_data = {}
                self.fetch_all_weather_data()
            elif choice == "9":
                print("🔄 Force refreshing weather data from API...")
                self.fetch_all_weather_data(force_refresh=True)
            elif choice == "10":
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
        elif sys.argv[1] == "today":
            monitor.display_today_freezing_analysis()
        elif sys.argv[1] == "week":
            monitor.display_week_freezing_analysis()
        elif sys.argv[1] == "map":
            monitor.display_indiana_map()
        elif sys.argv[1] == "todaymap":
            monitor.display_indiana_today_high_map()
        elif sys.argv[1] in INDIANA_CITIES:
            city = sys.argv[1]
            coords = INDIANA_CITIES[city]
            region = coords["region"]
            monitor.display_city_weather(city, coords, region)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print(f"Available options: summary, today, week, map, todaymap, or city name")
            print(f"Available cities: {', '.join(INDIANA_CITIES.keys())}")
    else:
        # Run interactive mode
        monitor.run_interactive_mode()

if __name__ == "__main__":
    main()
