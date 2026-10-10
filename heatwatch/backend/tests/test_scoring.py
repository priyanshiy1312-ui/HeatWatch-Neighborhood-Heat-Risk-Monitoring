from app.scoring import heat_index_c, feels_like_c, band, heat_risk, water_stress, priority
from app.data.wards import load_wards

W = {w["inputs"].id: w["inputs"].model_dump() for w in load_wards()}


def test_heat_index_monotonic_in_humidity():
    assert heat_index_c(36, 70) > heat_index_c(36, 30)


def test_feels_like_never_below_air_temp():
    assert feels_like_c(44, 10) >= 44


def test_bands():
    assert [band(x) for x in (10, 30, 60, 90)] == ["Low", "Moderate", "High", "Extreme"]


def test_dense_ward_riskier_than_leafy_ward():
    hot = heat_risk(44, 15, W["walled-city"])["score"]
    cool = heat_risk(44, 15, W["c-scheme"])["score"]
    assert hot > cool + 15


def test_scores_in_range_and_parts_sum():
    h = heat_risk(48, 10, W["murlipura"])
    assert 0 <= h["score"] <= 100
    assert abs(sum(h["parts"].values()) - h["score"]) < 0.5
    assert water_stress(W["sanganer"])["score"] > water_stress(W["c-scheme"])["score"]
    assert 0 <= priority(h["score"], 60) <= 100
