"""Tunable weights, thresholds and paths for HeatWatch."""
import os
from pathlib import Path

def _data_dir() -> Path:
    """backend/data (Lambda package) first, then repo-level data/ (local dev)."""
    env = os.getenv("HEATWATCH_DATA_DIR")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for c in (here.parents[1] / "data", here.parents[2] / "data"):
        if c.exists():
            return c
    return here.parents[2] / "data"


DATA_DIR = _data_dir()
OFFLINE = os.getenv("HEATWATCH_OFFLINE") == "1"   # tests / demo-safe mode: no network

CITY_CENTRE = (26.9124, 75.7873)                    # Jaipur
JAIPUR_BBOX = (26.76, 75.68, 27.00, 75.90)          # south, west, north, east
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HTTP_TIMEOUT = 10
WEATHER_TTL = 3600
RESOURCE_CACHE_TTL = 86400

HEAT_WEIGHTS = {"heat_index": 0.35, "surface_temp": 0.25, "low_green": 0.15,
                "population": 0.15, "vulnerable": 0.10}
WATER_WEIGHTS = {"distance": 0.6, "scarcity": 0.4}
PRIORITY_WEIGHTS = {"heat": 0.65, "water": 0.35}
BANDS = [(25, "Low"), (50, "Moderate"), (75, "High"), (101, "Extreme")]

FEELS_LIKE_RANGE_C = (30.0, 50.0)
MAX_LST_ANOMALY_C = 5.0
MAX_WATER_DIST_M = 2000.0
MAX_POP_DENSITY = 30000.0

# Day 3: advisories and alerts
BEDROCK_ENABLED = os.getenv("BEDROCK_ENABLED") == "1" and not OFFLINE
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
ALERT_TOPIC_ARN = os.getenv("ALERT_TOPIC_ARN", "")
ALERTS_TABLE = os.getenv("ALERTS_TABLE", "")
ALERT_MIN_PRIORITY = float(os.getenv("ALERT_MIN_PRIORITY", "60"))
