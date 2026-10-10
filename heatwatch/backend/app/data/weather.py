"""3-day Open-Meteo forecast (daily peak temp + humidity at that hour), cached, with fallback."""
import json
import time
from datetime import date, timedelta

import httpx

from .. import config as C
from ..models import DayWeather

_cache: dict = {"ts": 0.0, "value": None}


def _fallback() -> tuple[list[DayWeather], str]:
    raw = json.loads((C.DATA_DIR / "fallback_weather.json").read_text())
    today = date.today()
    days = [DayWeather(date=(today + timedelta(days=i)).isoformat(), **d)
            for i, d in enumerate(raw["days"])]
    return days, "fallback"


def _live() -> list[DayWeather]:
    lat, lon = C.CITY_CENTRE
    r = httpx.get(C.OPEN_METEO_URL, timeout=C.HTTP_TIMEOUT, params={
        "latitude": lat, "longitude": lon, "forecast_days": 3, "timezone": "Asia/Kolkata",
        "hourly": "temperature_2m,relative_humidity_2m"})
    r.raise_for_status()
    h = r.json()["hourly"]
    days = []
    for d in range(3):
        idx = range(d * 24, (d + 1) * 24)
        i = max(idx, key=lambda k: h["temperature_2m"][k])
        days.append(DayWeather(date=h["time"][i][:10], temp_c=h["temperature_2m"][i],
                               humidity_pct=h["relative_humidity_2m"][i]))
    return days


def get_forecast() -> tuple[list[DayWeather], str]:
    if C.OFFLINE:
        return _fallback()
    if _cache["value"] and time.time() - _cache["ts"] < C.WEATHER_TTL:
        return _cache["value"]
    try:
        value = (_live(), "live")
    except Exception:
        return _fallback()
    _cache.update(ts=time.time(), value=value)
    return value
