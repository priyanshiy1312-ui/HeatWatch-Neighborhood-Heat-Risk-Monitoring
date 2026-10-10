"""Pure scoring functions (no I/O) so they are easy to test and explain."""
from math import sqrt
from .config import (HEAT_WEIGHTS, WATER_WEIGHTS, PRIORITY_WEIGHTS, BANDS, FEELS_LIKE_RANGE_C,
                     MAX_LST_ANOMALY_C, MAX_WATER_DIST_M, MAX_POP_DENSITY)


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def scale(x: float, lo: float, hi: float) -> float:
    """Map x from [lo, hi] to [0, 1], clamped."""
    return clamp01((x - lo) / (hi - lo)) if hi > lo else 0.0


def heat_index_c(temp_c: float, rh: float) -> float:
    """NOAA Rothfusz heat index, returned in Celsius."""
    t = temp_c * 9 / 5 + 32
    if t < 80:
        return temp_c
    r = rh
    hi = (-42.379 + 2.04901523 * t + 10.14333127 * r - 0.22475541 * t * r
          - 0.00683783 * t * t - 0.05481717 * r * r + 0.00122874 * t * t * r
          + 0.00085282 * t * r * r - 0.00000199 * t * t * r * r)
    if r < 13 and 80 <= t <= 112:
        hi -= ((13 - r) / 4) * sqrt((17 - abs(t - 95)) / 17)
    elif r > 85 and 80 <= t <= 87:
        hi += ((r - 85) / 10) * ((87 - t) / 5)
    return (hi - 32) * 5 / 9


def feels_like_c(temp_c: float, rh: float) -> float:
    """Dry heat (Jaipur) can make the formula read below air temp; never go below it."""
    return max(temp_c, heat_index_c(temp_c, rh))


def band(score: float) -> str:
    for limit, name in BANDS:
        if score < limit:
            return name
    return BANDS[-1][1]


def heat_risk(temp_c: float, rh: float, w: dict) -> dict:
    """Heat risk 0-100 plus per-factor points so the UI can explain it."""
    fl = feels_like_c(temp_c, rh)
    x = {
        "heat_index": scale(fl, *FEELS_LIKE_RANGE_C),
        "surface_temp": scale(w["lst_anomaly_c"], 0, MAX_LST_ANOMALY_C),
        "low_green": clamp01(1 - w["green_cover"]),
        "population": scale(w["pop_density"], 0, MAX_POP_DENSITY),
        "vulnerable": scale(w["vulnerable_share"], 0, 0.5),
    }
    parts = {k: round(100 * HEAT_WEIGHTS[k] * v, 1) for k, v in x.items()}
    return {"score": round(sum(parts.values()), 1), "parts": parts,
            "feels_like_c": round(fl, 1)}


def water_stress(w: dict) -> dict:
    """Water stress 0-100: far from water and few water points per resident."""
    d = scale(w["nearest_water_m"], 0, MAX_WATER_DIST_M)
    per_10k = w["water_points"] / max(w["population"], 1) * 10000
    s = 1 - scale(per_10k, 0, 5)
    parts = {"distance": round(100 * WATER_WEIGHTS["distance"] * d, 1),
             "scarcity": round(100 * WATER_WEIGHTS["scarcity"] * s, 1)}
    return {"score": round(sum(parts.values()), 1), "parts": parts}


def priority(heat: float, water: float) -> float:
    return round(PRIORITY_WEIGHTS["heat"] * heat + PRIORITY_WEIGHTS["water"] * water, 1)
