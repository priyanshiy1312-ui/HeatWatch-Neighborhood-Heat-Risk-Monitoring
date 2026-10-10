import json

from fastapi.testclient import TestClient

from app import alerts, config as C
from app.advisories import template_advisory
from app.main import app
from app.recommender import recommend
from app.service import ward_rows

client = TestClient(app)
RES = json.loads((C.DATA_DIR / "resources.json").read_text())


def _row(band, water=70):
    return {"id": "walled-city", "name": "Walled City", "lat": 26.9239, "lon": 75.8267, "band": band,
            "water": water, "priority": 80, "temp_c": 44.0, "feels_like_c": 45.0, "date": "2026-10-11"}


def test_extreme_gets_urgent_actions_and_low_gets_info():
    assert any(a["level"] == "urgent" for a in recommend(_row("Extreme"), RES))
    assert [a["level"] for a in recommend(_row("Low", 10), RES)] == ["info"]


def test_template_advisory_languages():
    en = template_advisory(_row("Extreme"), "en", 1, RES)
    hi = template_advisory(_row("Extreme"), "hi", 1, RES)
    assert "Walled City" in en and "tomorrow" in en
    assert any("\u0900" <= ch <= "\u097f" for ch in hi)


def test_alert_dry_run_and_dedupe():
    alerts._seen.clear()
    rows, _, _ = ward_rows(2)
    first = alerts.check_and_alert(rows, 2, RES, min_priority=0)
    assert first and all(a["status"] == "dry-run" for a in first)
    again = alerts.check_and_alert(rows, 2, RES, min_priority=0)
    assert all(a["status"] == "skipped-duplicate" for a in again)


def test_api_actions_advisory_and_alert():
    d = client.get("/api/wards/walled-city?day=1").json()
    assert d["actions"] and len(d["trend"]) == 3
    a = client.get("/api/wards/walled-city/advisory?day=1&lang=hi").json()
    assert a["source"] == "template" and a["lang"] == "hi"
    r = client.post("/api/alerts/send/walled-city?day=1").json()
    assert r["status"] == "dry-run" and "Walled City" in r["message"]
    assert client.get("/api/alerts/log").json()["alerts"]
    assert client.get("/api/wards/walled-city/advisory?lang=fr").status_code == 422
