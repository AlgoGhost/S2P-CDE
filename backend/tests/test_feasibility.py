"""
VARUNEETI Feasibility Tests
============================

10 required test cases for physical and operational constraints.
"""

import pytest
from backend.schemas import FeasibilityRequest, FeasibilityStatus
from backend.services.vessel_service import VesselService

@pytest.fixture(autouse=True)
def setup_data():
    VesselService._load_data()

def test_valid_direct_match():
    # Australia -> Paradip for 75000 qty
    # Panamax should be DIRECT_FEASIBLE
    req = FeasibilityRequest(origin="Australia", destination="Paradip", cargo_quantity=75000)
    res = VesselService.evaluate_feasibility(req)
    
    panamax = next(v for v in res.vessels if v.vessel_type == "Panamax")
    assert panamax.status == FeasibilityStatus.DIRECT_FEASIBLE
    assert panamax.direct_feasible is True
    assert panamax.conditional_feasible is False
    assert "draft" in panamax.passed_constraints
    assert len(panamax.failed_constraints) == 0

def test_draft_exceeds_port_limit():
    # Capesize (18m draft) to Gopalpur (12.5m draft, no lightering)
    req = FeasibilityRequest(origin="Australia", destination="Gopalpur", cargo_quantity=150000)
    res = VesselService.evaluate_feasibility(req)
    
    cape = next(v for v in res.vessels if v.vessel_type == "Capesize")
    assert cape.status == FeasibilityStatus.INFEASIBLE
    assert "draft" in cape.failed_constraints

def test_loa_exceeds_port_limit():
    # Capesize (290m LOA) to Gopalpur (225m LOA limit)
    req = FeasibilityRequest(origin="Australia", destination="Gopalpur", cargo_quantity=150000)
    res = VesselService.evaluate_feasibility(req)
    
    cape = next(v for v in res.vessels if v.vessel_type == "Capesize")
    assert "loa" in cape.failed_constraints
    assert cape.status == FeasibilityStatus.INFEASIBLE

def test_beam_exceeds_port_limit():
    # Capesize (45m beam) to Gopalpur (32m beam limit)
    req = FeasibilityRequest(origin="Australia", destination="Gopalpur", cargo_quantity=150000)
    res = VesselService.evaluate_feasibility(req)
    
    cape = next(v for v in res.vessels if v.vessel_type == "Capesize")
    assert "beam" in cape.failed_constraints

def test_cargo_exceeds_vessel_capacity():
    # Total cargo 300,000 to Paradip. A Panamax holds 75k.
    # It should NOT be infeasible. It should just take multiple voyages.
    req = FeasibilityRequest(origin="Australia", destination="Paradip", cargo_quantity=300000)
    res = VesselService.evaluate_feasibility(req)
    
    panamax = next(v for v in res.vessels if v.vessel_type == "Panamax")
    assert panamax.voyages_required == 4
    assert panamax.status == FeasibilityStatus.DIRECT_FEASIBLE

def test_lightering_conditional_match():
    # Capesize (18m draft) to Haldia (7.5m draft), lightering available (15k cap).
    # Wait, 18 - 7.5 = 10.5 excess draft.
    # Proportion lightered: 10.5 / 18 = 0.5833
    # Lightered qty: 0.5833 * 150000 = ~87500.
    # Haldia lightering capacity is 15000.
    # This will exceed lightering capacity, so it should be INFEASIBLE.
    
    # Let's test a Panamax (13.5m) to Haldia (7.5m).
    # Excess 6m. Proportion: 6 / 13.5 = 0.444
    # Lightered qty: 0.444 * 75000 = ~33333.
    # Still exceeds 15000 capacity. INFEASIBLE.
    
    # Let's test Supramax (11.5m) to Haldia (7.5m).
    # Excess 4m. Proportion: 4 / 11.5 = 0.347
    # Lightered qty = 0.347 * 55000 = 19130. Exceeds 15k. INFEASIBLE.

    # Handysize (10m) to Haldia (7.5m).
    # Excess 2.5m. Proportion: 2.5 / 10 = 0.25
    # Lightered qty = 0.25 * 35000 = 8750. <= 15000.
    # Should be CONDITIONALLY_FEASIBLE!
    req = FeasibilityRequest(origin="USA", destination="Haldia", cargo_quantity=35000)
    res = VesselService.evaluate_feasibility(req)
    
    handy = next(v for v in res.vessels if v.vessel_type == "Handysize")
    assert handy.status == FeasibilityStatus.CONDITIONALLY_FEASIBLE
    assert handy.conditional_feasible is True
    assert handy.lightering is not None
    assert handy.lightering.required is True
    assert handy.lightering.lightering_quantity > 0
    assert handy.lightering.incremental_cost > 0

def test_lightering_unavailable():
    # Panamax (13.5m draft) to Gopalpur (12.5m limit). No lightering available.
    req = FeasibilityRequest(origin="Australia", destination="Gopalpur", cargo_quantity=75000)
    res = VesselService.evaluate_feasibility(req)
    
    panamax = next(v for v in res.vessels if v.vessel_type == "Panamax")
    assert panamax.status == FeasibilityStatus.INFEASIBLE
    assert "draft" in panamax.failed_constraints

def test_ranking_logic():
    # Handysize vs Panamax to Paradip for 75,000 qty.
    # Panamax is 1 voyage, Handysize is 3 voyages (ceil(75000/35000) = 3).
    # Operational costs for Panamax should be lower, fit score better.
    req = FeasibilityRequest(origin="Australia", destination="Paradip", cargo_quantity=75000)
    res = VesselService.evaluate_feasibility(req)
    
    # Recommended should be Panamax
    assert res.recommended_vessel is not None
    assert res.recommended_vessel.vessel_type == "Panamax"
    assert res.recommended_vessel.voyages_required == 1
    
def test_multi_voyage_parcelization():
    # Test a very large quantity
    req = FeasibilityRequest(origin="Australia", destination="Visakhapatnam", cargo_quantity=1_500_000)
    res = VesselService.evaluate_feasibility(req)
    
    cape = next(v for v in res.vessels if v.vessel_type == "Capesize")
    # Visakhapatnam max draft is 14.0. Capesize draft is 18.0. No lightering.
    assert cape.status == FeasibilityStatus.INFEASIBLE
    
    panamax = next(v for v in res.vessels if v.vessel_type == "Panamax")
    # Visakhapatnam draft is 14.0, Panamax draft is 13.5. Feasible!
    assert panamax.status == FeasibilityStatus.DIRECT_FEASIBLE
    assert panamax.voyages_required == 20 # 1,500,000 / 75,000

def test_unknown_port():
    req = FeasibilityRequest(origin="Australia", destination="Atlantis", cargo_quantity=75000)
    with pytest.raises(ValueError, match="Unknown destination port"):
        VesselService.evaluate_feasibility(req)
