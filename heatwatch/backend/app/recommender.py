"""Rule-based action recommender: turns a ward's scores into concrete, local actions."""
from math import asin, cos, radians, sin, sqrt


def _m(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = radians(lat1), radians(lat2)
    a = sin((p2 - p1) / 2) ** 2 + cos(p1) * cos(p2) * sin(radians(lon2 - lon1) / 2) ** 2
    return 6371000 * 2 * asin(sqrt(a))


def nearest(row: dict, resources: list, kind: str):
    """Nearest resource of a type to the ward centre -> (resource, metres) or (None, None)."""
    best, dist = None, None
    for r in resources:
        if r.get("type") != kind:
            continue
        d = _m(row["lat"], row["lon"], r["lat"], r["lon"])
        if dist is None or d < dist:
            best, dist = r, d
    return best, (round(dist) if dist is not None else None)


def recommend(row: dict, resources: list) -> list[dict]:
    """Each action: {'level': 'urgent'|'recommended'|'info', 'text': str}."""
    band, water = row["band"], row["water"]
    hosp, hd = nearest(row, resources, "hospital")
    wp, wd = nearest(row, resources, "water")
    shelter = (f"the nearest hospital ({hosp['name']}, about {hd} m away)" if hosp
               else "a community hall or school")
    out: list[dict] = []
    if band == "Extreme":
        out += [
            {"level": "urgent", "text": f"Open a cooling shelter at {shelter} with drinking water and ORS."},
            {"level": "urgent", "text": "Stop outdoor work between 12 and 4 PM; alert contractors and labour camps."},
            {"level": "urgent", "text": "Send ward volunteers to check on elderly residents and young children."},
        ]
    elif band == "High":
        out += [
            {"level": "recommended", "text": f"Keep {shelter} ready as a cooling point from 12 to 4 PM."},
            {"level": "recommended", "text": "Ask outdoor workers to shift heavy work to early morning or evening."},
        ]
    elif band == "Moderate":
        out.append({"level": "recommended", "text": "Share a hydration and shade advisory with the ward."})
    else:
        out.append({"level": "info", "text": "No action needed. Keep monitoring the forecast."})
    if band in ("Extreme", "High") and water >= 50:
        out.append({"level": "urgent" if band == "Extreme" else "recommended",
                    "text": "Water stress is high: schedule a tanker and refill public water points before noon."})
    if wp and wd is not None and wd > 800 and band != "Low":
        out.append({"level": "info", "text": f"Nearest listed water point is {wd} m away; consider a temporary water station."})
    return out
