"""Generate labelled SAMPLE data for the Jaipur MVP.

Writes data/wards.geojson, data/resources.json and data/fallback_weather.json.
Ward shapes are approximate circles-ish zones, not official ward boundaries, and the
socio-economic / land values are plausible placeholders. Replace with real datasets
(Census, WorldPop, MODIS, OSM) as time allows. Re-run: python scripts/build_sample_data.py
"""
import json
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data"
random.seed(7)

# id, name, lat, lon, population, density/km2, green, built_up, lst_anomaly, vulnerable, water_pts, hospitals
WARDS = [
    ("walled-city", "Walled City", 26.9239, 75.8267, 118000, 27000, .04, .93, 4.6, .42, 5, 3),
    ("bani-park", "Bani Park", 26.9340, 75.7900, 62000, 14000, .14, .74, 2.1, .30, 8, 2),
    ("c-scheme", "C-Scheme", 26.9050, 75.8006, 38000, 9000, .26, .62, 0.4, .22, 12, 4),
    ("raja-park", "Raja Park", 26.8990, 75.8300, 71000, 17500, .12, .80, 2.8, .30, 9, 2),
    ("malviya-nagar", "Malviya Nagar", 26.8550, 75.8100, 96000, 15500, .16, .76, 2.2, .28, 11, 3),
    ("vaishali-nagar", "Vaishali Nagar", 26.9120, 75.7280, 105000, 13500, .15, .72, 1.6, .26, 10, 2),
    ("mansarovar", "Mansarovar", 26.8500, 75.7600, 150000, 19000, .13, .79, 2.5, .29, 9, 2),
    ("sanganer", "Sanganer", 26.8200, 75.7950, 88000, 11000, .17, .66, 2.9, .38, 4, 1),
    ("jhotwara", "Jhotwara", 26.9500, 75.7450, 92000, 16000, .09, .82, 3.4, .39, 3, 1),
    ("murlipura", "Murlipura", 26.9850, 75.7650, 78000, 14500, .08, .78, 3.0, .40, 3, 1),
    ("vidhyadhar-nagar", "Vidhyadhar Nagar", 26.9600, 75.7850, 69000, 10500, .18, .64, 1.2, .24, 8, 1),
    ("amer-road", "Amer Road", 26.9650, 75.8400, 54000, 8000, .22, .55, 1.0, .33, 4, 1),
    ("sodala", "Sodala", 26.9020, 75.7650, 66000, 12000, .19, .68, 1.4, .25, 8, 2),
    ("gopalpura", "Gopalpura", 26.8700, 75.7800, 83000, 13000, .15, .73, 2.0, .27, 7, 2),
    ("jagatpura", "Jagatpura", 26.8300, 75.8500, 74000, 7500, .21, .52, 1.5, .29, 5, 1),
    ("sitapura", "Sitapura", 26.7900, 75.8300, 46000, 4500, .12, .45, 3.8, .36, 2, 0),
]
KM_PER_DEG = 111.0


def km_to_dlat(km):
    return km / KM_PER_DEG


def km_to_dlon(km, lat):
    return km / (KM_PER_DEG * math.cos(math.radians(lat)))


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(a))


def polygon(lat, lon, radius_km, sides=10):
    pts = []
    for i in range(sides):
        ang = 2 * math.pi * i / sides + random.uniform(-0.12, 0.12)
        r = radius_km * random.uniform(0.9, 1.05)
        pts.append([round(lon + km_to_dlon(r * math.cos(ang), lat), 5),
                    round(lat + km_to_dlat(r * math.sin(ang)), 5)])
    pts.append(pts[0])
    return pts


def scatter(lat, lon, radius_km, n, kind, name, ward_id):
    out = []
    for _ in range(n):
        r = radius_km * 0.85 * math.sqrt(random.random())
        a = random.uniform(0, 2 * math.pi)
        out.append({
            "type": kind, "name": name, "ward": ward_id,
            "lat": round(lat + km_to_dlat(r * math.sin(a)), 5),
            "lon": round(lon + km_to_dlon(r * math.cos(a), lat), 5),
            "source": "sample",
        })
    return out


features, resources = [], []
for wid, name, lat, lon, pop, dens, green, built, lst, vuln, wp, hosp in WARDS:
    radius = 0.85 * math.sqrt((pop / dens) / math.pi)
    water = scatter(lat, lon, radius, wp, "water", "Water point (sample)", wid)
    hospitals = scatter(lat, lon, radius, hosp, "hospital", "Hospital (sample)", wid)
    nearest = min((haversine_m(lat, lon, p["lat"], p["lon"]) for p in water), default=2500.0)
    resources += water + hospitals
    features.append({
        "type": "Feature",
        "properties": {
            "id": wid, "name": name, "lat": lat, "lon": lon, "population": pop,
            "pop_density": dens, "green_cover": green, "built_up": built,
            "lst_anomaly_c": lst, "vulnerable_share": vuln, "water_points": wp,
            "nearest_water_m": round(nearest), "data_quality": "sample",
        },
        "geometry": {"type": "Polygon", "coordinates": [polygon(lat, lon, radius)]},
    })

OUT.mkdir(exist_ok=True)
(OUT / "wards.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}))
(OUT / "resources.json").write_text(json.dumps(resources, indent=1))
(OUT / "fallback_weather.json").write_text(json.dumps({
    "label": "sample forecast (offline fallback)",
    "days": [{"temp_c": 41.0, "humidity_pct": 24}, {"temp_c": 43.0, "humidity_pct": 20},
             {"temp_c": 44.5, "humidity_pct": 17}],
}, indent=1))
print(f"wrote {len(features)} wards, {len(resources)} resources to {OUT}")
