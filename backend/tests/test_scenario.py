"""
VARUNEETI scenario / stress-test engine tests.

The point of these tests is that scenarios must genuinely re-solve the decision:
a shock has to move real numbers through the real engines, not return a canned
narrative.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas import OptimizeRequest
from backend.services.scenario_service import ScenarioService

client = TestClient(app)

GOLDEN = {
    "origin": "Australia",
    "destination": "Paradip",
    "cargo_quantity": 300000,
    "parcel_quantity": 75000,
    "delivery_start": "2026-10-01",
    "delivery_end": "2026-12-31",
}


@pytest.fixture(scope="module")
def analysis():
    return ScenarioService.run(OptimizeRequest(**GOLDEN))


def test_all_scenarios_returned(analysis):
    ids = [o.scenario_id for o in analysis.outcomes]
    assert ids[0] == "BASE"
    for expected in (
        "BASE",
        "HIGH_FREIGHT",
        "LOW_FREIGHT",
        "HIGH_CONGESTION",
        "LOW_AVAILABILITY",
    ):
        assert expected in ids


def test_base_case_has_zero_delta(analysis):
    base = next(o for o in analysis.outcomes if o.scenario_id == "BASE")
    assert base.cost_delta_vs_base == 0.0
    assert base.cost_pct_delta_vs_base == 0.0
    assert base.strategy_changed is False
    assert base.vessel_changed is False


def test_freight_shocks_actually_move_cost(analysis):
    """A freight shock must change the cost, or the scenario is theatre."""
    base = next(o for o in analysis.outcomes if o.scenario_id == "BASE")
    high = next(o for o in analysis.outcomes if o.scenario_id == "HIGH_FREIGHT")
    low = next(o for o in analysis.outcomes if o.scenario_id == "LOW_FREIGHT")

    assert high.cost_per_tonne > base.cost_per_tonne
    assert low.cost_per_tonne < base.cost_per_tonne
    assert high.cost_delta_vs_base > 0
    assert low.cost_delta_vs_base < 0


def test_freight_shock_direction_matches_magnitude(analysis):
    """+25% on freight must raise total cost by less than 25% (ops costs dilute it)."""
    high = next(o for o in analysis.outcomes if o.scenario_id == "HIGH_FREIGHT")
    assert 0 < high.cost_pct_delta_vs_base < 25.0


def test_congestion_shock_raises_risk(analysis):
    """More congestion must raise the risk score through the risk engine."""
    base = next(o for o in analysis.outcomes if o.scenario_id == "BASE")
    cong = next(o for o in analysis.outcomes if o.scenario_id == "HIGH_CONGESTION")
    assert cong.risk_score > base.risk_score


def test_low_availability_changes_the_vessel(analysis):
    """Removing the chosen hull must force a different, still-feasible vessel."""
    base = next(o for o in analysis.outcomes if o.scenario_id == "BASE")
    low = next(o for o in analysis.outcomes if o.scenario_id == "LOW_AVAILABILITY")

    assert low.vessel_class != base.vessel_class
    assert low.vessel_changed is True
    # A smaller replacement hull needs more voyages to lift the same cargo.
    assert low.voyages >= base.voyages


def test_robustness_verdict_is_consistent_with_outcomes(analysis):
    flipped = [o for o in analysis.outcomes if o.strategy_changed]
    assert analysis.recommendation_is_robust == (len(flipped) == 0)
    assert analysis.robustness_summary


def test_scenarios_are_not_probability_weighted(analysis):
    """We must not imply calibrated probabilities we have not validated."""
    joined = " ".join(analysis.assumptions).lower()
    assert "not calibrated" in joined or "not calibrated probabilities" in joined
    assert "must not be averaged" in joined


def test_deterministic_for_fixed_input():
    """Same input, same decision - required for a reproducible demo."""
    a = ScenarioService.run(OptimizeRequest(**GOLDEN))
    b = ScenarioService.run(OptimizeRequest(**GOLDEN))
    assert [o.strategy for o in a.outcomes] == [o.strategy for o in b.outcomes]
    assert [o.expected_cost for o in a.outcomes] == [o.expected_cost for o in b.outcomes]


# ─── API surface ─────────────────────────────────────────────────────────────


def test_scenario_endpoint_returns_200():
    r = client.post("/api/scenario", json=GOLDEN)
    assert r.status_code == 200
    d = r.json()
    assert d["base_scenario_id"] == "BASE"
    assert len(d["outcomes"]) == 5
    assert isinstance(d["recommendation_is_robust"], bool)
    assert d["robustness_summary"]
    assert d["assumptions"]


def test_scenario_endpoint_unknown_port_returns_400():
    bad = dict(GOLDEN, destination="Atlantis")
    r = client.post("/api/scenario", json=bad)
    assert r.status_code == 400


def test_scenario_endpoint_validates_body():
    r = client.post("/api/scenario", json={"origin": "Australia"})
    assert r.status_code == 422
