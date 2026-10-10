"""Shared helpers: score every ward for a given forecast day."""
import json

from . import config as C
from .data import osm
from .data.wards import load_wards
from .data.weather import get_forecast
from .scoring import band, heat_risk, priority, water_stress


def score(inputs: dict, wx) -> dict:
    h = heat_risk(wx.temp_c, wx.humidity_pct, inputs)
    s = water_stress(inputs)
    p = priority(h["score"], s["score"])
    return {"date": wx.date, "temp_c": round(wx.temp_c, 1), "humidity_pct": round(wx.humidity_pct),
            "feels_like_c": h["feels_like_c"], "heat": h["score"], "water": s["score"],
            "priority": p, "band": band(p), "heat_parts": h["parts"], "water_parts": s["parts"]}


def ward_props(w: dict, wx) -> dict:
    i = w["inputs"].model_dump()
    return {**i, **score(i, wx)}


def ward_rows(day: int):
    """Returns (rows sorted as loaded, forecast days, source)."""
    days, source = get_forecast()
    return [ward_props(w, days[day]) for w in load_wards()], days, source


def get_resource_list():
    if C.OFFLINE:
        return json.loads((C.DATA_DIR / "resources.json").read_text()), "fallback"
    return osm.get_resources()
