from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_wards_geojson():
    body = client.get("/api/wards?day=0").json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 16
    assert body["meta"]["source"] == "fallback"
    assert len(body["meta"]["days"]) == 3
    for f in body["features"]:
        p = f["properties"]
        assert 0 <= p["priority"] <= 100
        assert p["band"] in {"Low", "Moderate", "High", "Extreme"}
        assert f["geometry"]["type"] == "Polygon"


def test_top_sorted_descending():
    top = client.get("/api/top?day=2&n=5").json()["wards"]
    assert len(top) == 5
    scores = [w["priority"] for w in top]
    assert scores == sorted(scores, reverse=True)


def test_later_days_are_not_cooler_in_sample_forecast():
    d0 = client.get("/api/top?day=0&n=1").json()["wards"][0]["priority"]
    d2 = client.get("/api/top?day=2&n=1").json()["wards"][0]["priority"]
    assert d2 >= d0


def test_ward_detail_and_404():
    r = client.get("/api/wards/walled-city?day=1").json()
    assert r["ward"]["name"] == "Walled City"
    assert len(r["trend"]) == 3
    assert client.get("/api/wards/nowhere").status_code == 404


def test_invalid_day_rejected():
    assert client.get("/api/wards?day=5").status_code == 422


def test_resources_fallback():
    r = client.get("/api/resources").json()
    assert r["source"] in {"fallback", "live"}
    assert len(r["resources"]) > 0
