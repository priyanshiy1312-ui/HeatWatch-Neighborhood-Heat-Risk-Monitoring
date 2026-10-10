"""HeatWatch API. Run: uvicorn app.main:app --reload --port 8000"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import alerts
from .advisories import get_advisory
from .data.wards import load_wards
from .data.weather import get_forecast
from .recommender import recommend
from .service import get_resource_list, score, ward_props, ward_rows

app = FastAPI(title="HeatWatch API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])


def _find(ward_id: str, day: int) -> dict:
    rows, _, _ = ward_rows(day)
    for r in rows:
        if r["id"] == ward_id:
            return r
    raise HTTPException(404, "Ward not found")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/wards")
def wards(day: int = Query(0, ge=0, le=2)):
    days, source = get_forecast()
    return {"type": "FeatureCollection",
            "features": [{"type": "Feature", "geometry": w["geometry"],
                          "properties": ward_props(w, days[day])} for w in load_wards()],
            "meta": {"day": day, "source": source,
                     "days": [d.model_dump() for d in days], "ward_data": "sample/proxy values"}}


@app.get("/api/wards/{ward_id}")
def ward(ward_id: str, day: int = Query(0, ge=0, le=2)):
    days, source = get_forecast()
    for w in load_wards():
        if w["inputs"].id == ward_id:
            row = ward_props(w, days[day])
            resources, _ = get_resource_list()
            return {"ward": row, "source": source, "actions": recommend(row, resources),
                    "trend": [score(w["inputs"].model_dump(), d) for d in days]}
    raise HTTPException(404, "Ward not found")


@app.get("/api/wards/{ward_id}/advisory")
def advisory(ward_id: str, day: int = Query(0, ge=0, le=2), lang: str = Query("en", pattern="^(en|hi)$")):
    row = _find(ward_id, day)
    resources, _ = get_resource_list()
    return get_advisory(row, lang, day, resources)


@app.get("/api/top")
def top(n: int = Query(5, ge=1, le=16), day: int = Query(0, ge=0, le=2)):
    rows, _, source = ward_rows(day)
    return {"day": day, "source": source, "wards": sorted(rows, key=lambda r: -r["priority"])[:n]}


@app.get("/api/resources")
def resources():
    items, source = get_resource_list()
    return {"source": source, "resources": items}


@app.post("/api/alerts/send/{ward_id}")
def send(ward_id: str, day: int = Query(0, ge=0, le=2)):
    """Manual alert (demo button). Always sends, even if already alerted."""
    row = _find(ward_id, day)
    resources, _ = get_resource_list()
    return alerts.send_alert(row, day, resources, force=True)


@app.post("/api/alerts/check")
def check(day: int = Query(1, ge=0, le=2)):
    rows, _, _ = ward_rows(day)
    resources, _ = get_resource_list()
    return {"alerts": alerts.check_and_alert(rows, day, resources)}


@app.get("/api/alerts/log")
def alert_log():
    return {"alerts": list(reversed(alerts.LOG))}


try:  # AWS Lambda entry point: handler = app.main.handler
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:  # pragma: no cover
    pass
