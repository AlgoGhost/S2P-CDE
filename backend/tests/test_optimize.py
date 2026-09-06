"""
VARUNEETI Emergency MVP Optimization Tests
==========================================
Minimal tests to ensure /api/optimize endpoint and logic works.
"""

import pytest
from backend.schemas import OptimizeRequest
from backend.services.optimize_service import OptimizeService

def test_optimize_success():
    req = OptimizeRequest(
        origin="Australia",
        destination="Paradip",
        cargo_quantity=300000,
        parcel_quantity=75000,
        delivery_start="2026-10-01",
        delivery_end="2026-12-31"
    )
    res = OptimizeService.optimize(req)
    
    assert res.status == "optimal"
    assert res.recommendation is not None
    assert res.recommendation.expected_cost > 0
    assert len(res.strategy_comparison) == 4
    assert res.voyages == 4 # 300,000 / 75,000
    
    # Cost per tonne should be correct
    assert res.recommendation.cost_per_tonne == pytest.approx(res.recommendation.expected_cost / 300000, 0.01)

def test_optimize_rejects_infeasible_vessel():
    # Gopalpur has a 12.5m draft limit. Capesize is 18m.
    # The optimizer should NOT recommend a Capesize.
    req = OptimizeRequest(
        origin="Australia",
        destination="Gopalpur", # Handysize/Supramax feasible, Capesize/Panamax infeasible
        cargo_quantity=300000,
        parcel_quantity=50000,
        delivery_start="2026-10-01",
        delivery_end="2026-12-31"
    )
    # We must mock ForecastService to return a dummy forecast because Australia->Gopalpur forecast lane doesn't exist
    from backend.schemas import ForecastResponse, TrendDirection, VolatilityLevel, ErrorMetrics
    from backend.services.forecast_service import ForecastService
    
    original_forecast = ForecastService.forecast
    
    def mock_forecast(*args, **kwargs):
        from backend.schemas import TimeSeriesPoint
        return ForecastResponse(
            origin="Australia", destination="Gopalpur", vessel_type="Panamax", horizon_days=30,
            forecast=20.0, lower_bound=15.0, upper_bound=25.0, trend=TrendDirection.STABLE,
            volatility=VolatilityLevel.MEDIUM, confidence=0.8, model_name="Mock",
            baseline_error=ErrorMetrics(mae=1, rmse=1, mape=1),
            model_error=ErrorMetrics(mae=1, rmse=1, mape=1),
            model_wins=True, historical_series=[], forecast_series=[], data_source="mock", warnings=[]
        )
    
    ForecastService.forecast = mock_forecast
    try:
        res = OptimizeService.optimize(req)
        
        assert res.status == "optimal"
        assert res.recommendation.vessel_class != "Capesize"
        assert res.recommendation.vessel_class != "Panamax"
        assert res.recommendation.vessel_class in ["Handysize", "Supramax"]
    finally:
        ForecastService.forecast = original_forecast
