"""
VARUNEETI Emergency MVP Risk Tests
====================================
"""

import pytest
from backend.schemas import RiskRequest
from backend.services.risk_service import RiskService

def test_risk_evaluate_success():
    req = RiskRequest(
        origin="Australia",
        destination="Paradip",
        cargo_quantity=300000,
        parcel_quantity=75000,
        delivery_start="2026-10-01",
        delivery_end="2026-12-31"
    )
    res = RiskService.evaluate_risk(req)
    
    assert res.overall_score >= 0.0
    assert res.overall_score <= 100.0
    assert res.risk_level in ["LOW", "MEDIUM", "HIGH"]
    assert len(res.top_drivers) <= 3
    assert len(res.top_drivers) > 0
    assert res.top_drivers[0].contribution >= res.top_drivers[-1].contribution

def test_risk_evaluate_unknown_destination():
    # Should fallback gracefully or raise ValueError. 
    # VesselService raises ValueError for unknown port, so it will bubble up.
    req = RiskRequest(
        origin="Australia",
        destination="Atlantis",
        cargo_quantity=300000,
        parcel_quantity=75000,
        delivery_start="2026-10-01",
        delivery_end="2026-12-31"
    )
    with pytest.raises(ValueError, match="Unknown destination"):
        RiskService.evaluate_risk(req)
