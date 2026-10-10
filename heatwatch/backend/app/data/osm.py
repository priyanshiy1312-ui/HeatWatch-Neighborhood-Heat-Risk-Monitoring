"""Water points, hospitals and parks from OpenStreetMap (Overpass), with sample fallback."""
import json
import logging
import time

import httpx

from .. import config as C

log = logging.getLogger("heatwatch.osm")
_cache: dict = {"ts": 0.0, "value": None}


def _query() -> str:
    s, w, n, e = C.JAIPUR_BBOX
    box = f"{s},{w},{n},{e}"
    return f"""[out:json][timeout:20];
(
  node["amenity"="drinking_water"]({box});
  node["amenity"="hospital"]({box});
  way["amenity"="hospital"]({box});
  way["leisure"="park"]({box});
);
out center 400;"""


def _live() -> list[dict]:
    resp = httpx.post(C.OVERPASS_URL, data={"data": _query()}, timeout=C.HTTP_TIMEOUT + 10)
    resp.raise_for_status()
    items = []
    for el in resp.json().get("elements", []):
        tags = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        if tags.get("amenity") == "drinking_water":
            kind = "water"
        elif tags.get("amenity") == "hospital":
            kind = "hospital"
        elif tags.get("leisure") == "park":
            kind = "park"
        else:
            continue
        items.append({"type": kind, "name": tags.get("name", kind.title()), "lat": lat, "lon": lon, "source": "osm"})
    if not items:
        raise ValueError("Overpass returned no features")
    return items


def get_resources() -> tuple[list[dict], str]:
    now = time.time()
    if _cache["value"] and now - _cache["ts"] < C.RESOURCE_CACHE_TTL:
        return _cache["value"]
    try:
        value = (_live(), "live")
    except Exception as exc:
        log.warning("Overpass unavailable (%s); using sample resources", exc)
        value = (json.loads((C.DATA_DIR / "resources.json").read_text()), "fallback")
    _cache.update(ts=now, value=value)
    return value
