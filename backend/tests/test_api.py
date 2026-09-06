"""
VARUNEETI API contract tests.

Runs the FastAPI app in-process via Starlette's TestClient — no server to start,
no network, no ports. This replaces the previous test_api_live.py, which required
a manually-started uvicorn on 127.0.0.1:8000 and therefore failed on a clean
checkout.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

GOLDEN = {
    "origin": "Australia",
    "destination": "Paradip",
    "cargo_quantity": 300000,
    "parcel_quantity": 75000,
    "delivery_start": "2026-10-01",
    "delivery_end": "2026-12-31",
}


# ─── Health / lanes ──────────────────────────────────────────────────────────


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "VARUNEETI"
    assert body["version"]


def test_lanes():
    r = client.get("/api/lanes")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] > 0
    assert len(body["lanes"]) == body["count"]
    lane = body["lanes"][0]
    for key in ("origin", "destination", "vessel_type", "n_observations"):
        assert key in lane


# ─── Forecast ────────────────────────────────────────────────────────────────


def test_forecast_golden_lane():
    r = client.post(
        "/api/forecast",
        json={
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_type": "Panamax",
            "horizon_days": 30,
        },
    )
    assert r.status_code == 200
    d = r.json()

    # Prediction interval must bracket the point forecast.
    assert d["lower_bound"] <= d["forecast"] <= d["upper_bound"]
    assert d["forecast"] > 0
    assert 0.0 <= d["confidence"] <= 1.0
    assert d["trend"] in ("RISING", "FALLING", "STABLE")
    assert d["volatility"] in ("LOW", "MEDIUM", "HIGH")
    assert d["data_source"] == "prototype_proxy"
    assert len(d["historical_series"]) > 0
    assert len(d["forecast_series"]) > 0


def test_forecast_unknown_lane_returns_400_not_500():
    r = client.post(
        "/api/forecast",
        json={
            "origin": "Mars",
            "destination": "Jupiter",
            "vessel_type": "Spaceship",
            "horizon_days": 30,
        },
    )
    assert r.status_code == 400
    assert "detail" in r.json()


@pytest.mark.parametrize("horizon", [7, 14, 30, 60, 90])
def test_forecast_supported_horizons(horizon):
    r = client.post(
        "/api/forecast",
        json={
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_type": "Panamax",
            "horizon_days": horizon,
        },
    )
    assert r.status_code == 200
    assert r.json()["horizon_days"] == horizon


@pytest.mark.parametrize("vessel", ["Handysize", "Supramax", "Panamax", "Capesize"])
def test_forecast_all_vessel_classes(vessel):
    r = client.post(
        "/api/forecast",
        json={
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_type": vessel,
            "horizon_days": 30,
        },
    )
    assert r.status_code == 200
    assert r.json()["vessel_type"] == vessel


@pytest.mark.parametrize(
    "origin,destination,vessel",
    [
        ("Indonesia", "Dhamra", "Supramax"),
        ("USA", "Haldia", "Panamax"),
        ("Mozambique", "Gangavaram", "Handysize"),
        ("Russia", "Paradip", "Capesize"),
    ],
)
def test_forecast_other_lanes(origin, destination, vessel):
    r = client.post(
        "/api/forecast",
        json={
            "origin": origin,
            "destination": destination,
            "vessel_type": vessel,
            "horizon_days": 30,
        },
    )
    assert r.status_code == 200
    assert r.json()["forecast"] > 0


# ─── Feasibility ─────────────────────────────────────────────────────────────


def test_feasibility_golden_case():
    r = client.post(
        "/api/feasibility",
        json={
            "origin": "Australia",
            "destination": "Paradip",
            "cargo_quantity": 300000,
            "parcel_quantity": 75000,
        },
    )
    assert r.status_code == 200
    d = r.json()

    assert d["recommended_vessel"] is not None
    # A recommendation must never be an infeasible hull.
    assert d["recommended_vessel"]["status"] != "INFEASIBLE"

    by_type = {v["vessel_type"]: v for v in d["vessels"]}

    # Capesize (18.0 m draft) cannot enter Paradip (14.5 m limit) and lightering
    # capacity is insufficient — it must be rejected with explicit reasons.
    cape = by_type["Capesize"]
    assert cape["status"] == "INFEASIBLE"
    assert cape["failed_constraints"]
    assert cape["fit_score"] == 0.0

    # Panamax (13.5 m) clears every hard limit.
    assert by_type["Panamax"]["status"] == "DIRECT_FEASIBLE"


def test_feasibility_unknown_port_returns_400_not_500():
    r = client.post(
        "/api/feasibility",
        json={
            "origin": "Australia",
            "destination": "Atlantis",
            "cargo_quantity": 300000,
            "parcel_quantity": 75000,
        },
    )
    assert r.status_code == 400
    assert "Atlantis" in r.json()["detail"]


def test_feasibility_shallow_port_forces_lightering_or_rejection():
    """Haldia's 7.5 m draft limit is below every vessel class in the fleet."""
    r = client.post(
        "/api/feasibility",
        json={
            "origin": "Australia",
            "destination": "Haldia",
            "cargo_quantity": 300000,
            "parcel_quantity": 75000,
        },
    )
    assert r.status_code == 200
    statuses = {v["vessel_type"]: v["status"] for v in r.json()["vessels"]}
    # Nothing may come back as a clean direct call at a 7.5 m port.
    assert "DIRECT_FEASIBLE" not in statuses.values()


# ─── Risk ────────────────────────────────────────────────────────────────────


def test_risk_golden_case():
    r = client.post("/api/risk", json=GOLDEN)
    assert r.status_code == 200
    d = r.json()

    assert 0.0 <= d["overall_score"] <= 100.0
    assert d["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert 0 < len(d["top_drivers"]) <= 3
    # all_drivers must be a superset of top_drivers.
    assert len(d["all_drivers"]) >= len(d["top_drivers"])

    # Drivers are ordered by contribution, descending.
    contribs = [x["contribution"] for x in d["top_drivers"]]
    assert contribs == sorted(contribs, reverse=True)

    # Composite must reconcile with the weighted parts it reports.
    total = sum(x["contribution"] for x in d["all_drivers"])
    assert d["overall_score"] == pytest.approx(total, abs=0.5)


# ─── Optimize ────────────────────────────────────────────────────────────────


def test_optimize_golden_case():
    r = client.post("/api/optimize", json=GOLDEN)
    assert r.status_code == 200
    d = r.json()

    assert d["status"] == "optimal"
    rec = d["recommendation"]

    assert rec["strategy"] in ("SPOT", "SHORT_TERM", "MEDIUM_TERM", "HYBRID")
    assert rec["vessel_class"]
    assert rec["expected_cost"] > 0
    assert rec["cost_per_tonne"] > 0
    assert d["voyages"] >= 1
    assert d["decision_drivers"]
    assert d["assumptions"]

    # All four charter structures must be compared on the same basis.
    strategies = {s["strategy"] for s in d["strategy_comparison"]}
    assert strategies == {"SPOT", "SHORT_TERM", "MEDIUM_TERM", "HYBRID"}


def test_optimize_recommendation_is_the_cheapest_compared_option():
    """The recommendation must be derived from the comparison, not hardcoded."""
    r = client.post("/api/optimize", json=GOLDEN)
    d = r.json()
    cheapest = min(d["strategy_comparison"], key=lambda s: s["cost"])
    assert d["recommendation"]["strategy"] == cheapest["strategy"]
    assert d["recommendation"]["expected_cost"] == pytest.approx(cheapest["cost"], abs=0.01)


def test_optimize_cost_per_tonne_reconciles():
    r = client.post("/api/optimize", json=GOLDEN)
    rec = r.json()["recommendation"]
    expected = rec["expected_cost"] / GOLDEN["cargo_quantity"]
    assert rec["cost_per_tonne"] == pytest.approx(expected, rel=1e-3)


def test_optimize_tonnage_split_covers_full_cargo():
    r = client.post("/api/optimize", json=GOLDEN)
    rec = r.json()["recommendation"]
    total = rec["locked_tonnage"] + rec["flexible_tonnage"]
    assert total == pytest.approx(GOLDEN["cargo_quantity"], rel=1e-6)


def test_optimize_voyages_cover_full_cargo():
    """Voyage count x parcel size must be able to lift the whole programme."""
    opt = client.post("/api/optimize", json=GOLDEN).json()
    feas = client.post(
        "/api/feasibility",
        json={
            "origin": GOLDEN["origin"],
            "destination": GOLDEN["destination"],
            "cargo_quantity": GOLDEN["cargo_quantity"],
            "parcel_quantity": GOLDEN["parcel_quantity"],
        },
    ).json()
    parcel = feas["recommended_vessel"]["parcel_capacity"]
    assert opt["voyages"] * parcel >= GOLDEN["cargo_quantity"]


def test_optimize_decision_drivers_have_no_enum_leaks():
    """Driver strings are user-facing; Python enum reprs must not appear."""
    d = client.post("/api/optimize", json=GOLDEN).json()
    joined = " ".join(d["decision_drivers"])
    for leak in (
        "TrendDirection.",
        "VolatilityLevel.",
        "FeasibilityStatus.",
        "RiskLevel.",
        "CharterStrategy.",
    ):
        assert leak not in joined, f"enum repr leaked into decision_drivers: {leak}"


# ─── Validation / edge cases ─────────────────────────────────────────────────


def test_optimize_rejects_missing_fields():
    r = client.post("/api/optimize", json={"origin": "Australia"})
    assert r.status_code == 422


def test_forecast_rejects_wrong_types():
    r = client.post(
        "/api/forecast",
        json={
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_type": "Panamax",
            "horizon_days": "not-a-number",
        },
    )
    assert r.status_code == 422


def test_no_endpoint_returns_500_for_the_golden_case():
    """No route may surface an unhandled exception on the demo path."""
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/lanes").status_code == 200
    for path in ("/api/risk", "/api/optimize"):
        assert client.post(path, json=GOLDEN).status_code == 200
