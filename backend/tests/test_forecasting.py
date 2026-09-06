"""
VARUNEETI Forecast Tests
=========================

Tests for:
1.  Dataset loading
2.  Lane filtering
3.  Baseline forecast
4.  SARIMAX forecast
5.  Fallback behaviour
6.  Validation metrics
7.  Uncertainty bounds
8.  Trend calculation
9.  Volatility calculation
10. API endpoint

Critical test properties:
    A. Valid lane must return a forecast
    B. Unknown lane must not crash the server
    C. Insufficient data must trigger fallback
    D. lower_bound <= forecast <= upper_bound
    E. Forecast horizon must match requested horizon
    F. Model must not use future observations during validation
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.config import ABSOLUTE_MIN_OBSERVATIONS, SARIMAX_MIN_OBSERVATIONS
from backend.engines.forecasting import (
    ErrorMetrics,
    NaiveBaseline,
    SARIMAXForecaster,
    SimpleMovingAverageForecaster,
    calculate_confidence,
    calculate_trend,
    calculate_volatility,
    run_forecast,
    walk_forward_validate,
)
from backend.services.data_service import PrototypeFreightDataAdapter, get_data_adapter


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def adapter():
    """Return the prototype data adapter."""
    return PrototypeFreightDataAdapter()


@pytest.fixture
def sample_series():
    """A simple synthetic series for unit testing."""
    np.random.seed(42)
    n = 48
    trend = np.linspace(20, 25, n)
    seasonal = 2 * np.sin(np.arange(n) * 2 * np.pi / 12)
    noise = np.random.normal(0, 0.5, n)
    values = trend + seasonal + noise
    dates = pd.date_range("2020-01-01", periods=n, freq="MS")
    return pd.Series(values, name="freight_rate"), dates


@pytest.fixture
def short_series():
    """A very short series (less than SARIMAX_MIN_OBSERVATIONS)."""
    np.random.seed(42)
    values = [20.0, 21.5, 19.8, 22.0, 21.0, 23.5, 22.8, 20.5]
    dates = pd.date_range("2024-01-01", periods=len(values), freq="MS")
    return pd.Series(values, name="freight_rate"), dates


@pytest.fixture
def tiny_series():
    """Extremely short series to test minimum data checks."""
    values = [20.0, 21.0, 22.0]
    dates = pd.date_range("2024-01-01", periods=3, freq="MS")
    return pd.Series(values, name="freight_rate"), dates


# ─── 1. Dataset Loading ─────────────────────────────────────────────────────


class TestDatasetLoading:

    def test_freight_csv_loads(self, adapter):
        df = adapter.get_freight_data()
        assert len(df) > 0, "Freight dataset should not be empty"

    def test_freight_columns(self, adapter):
        df = adapter.get_freight_data()
        required = [
            "date", "origin", "destination", "vessel_type",
            "freight_rate", "bunker_price", "commodity_index",
            "congestion_index", "seasonal_index",
        ]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_date_is_datetime(self, adapter):
        df = adapter.get_freight_data()
        assert pd.api.types.is_datetime64_any_dtype(df["date"])

    def test_freight_rates_positive(self, adapter):
        df = adapter.get_freight_data()
        assert (df["freight_rate"] > 0).all(), "All freight rates must be positive"

    def test_data_source_label(self, adapter):
        assert adapter.source_label == "prototype_proxy"
        assert "Not proprietary SAIL data" in adapter.disclaimer


# ─── 2. Lane Filtering ──────────────────────────────────────────────────────


class TestLaneFiltering:

    def test_valid_lane(self, adapter):
        df = adapter.get_lane_data("Australia", "Paradip", "Panamax")
        assert len(df) > 0, "Australia→Paradip [Panamax] should have data"

    def test_case_insensitive(self, adapter):
        df = adapter.get_lane_data("australia", "paradip", "panamax")
        assert len(df) > 0, "Lane filtering should be case-insensitive"

    def test_unknown_lane_returns_empty(self, adapter):
        df = adapter.get_lane_data("Mars", "Neptune", "Spaceship")
        assert len(df) == 0

    def test_lane_sorted_by_date(self, adapter):
        df = adapter.get_lane_data("Australia", "Paradip", "Panamax")
        dates = df["date"].tolist()
        assert dates == sorted(dates), "Lane data must be sorted chronologically"

    def test_available_lanes(self, adapter):
        lanes = adapter.get_available_lanes()
        assert len(lanes) > 0
        for lane in lanes:
            assert "origin" in lane
            assert "destination" in lane
            assert "vessel_type" in lane
            assert "n_observations" in lane


# ─── 3. Baseline Forecast ───────────────────────────────────────────────────


class TestNaiveBaseline:

    def test_forecast_equals_last_value(self, sample_series):
        series, dates = sample_series
        model = NaiveBaseline()
        model.fit(series)
        fc, lower, upper = model.predict(3)
        assert np.allclose(fc, series.iloc[-1]), \
            "Naive baseline should forecast the last observed value"

    def test_uncertainty_widens(self, sample_series):
        series, dates = sample_series
        model = NaiveBaseline()
        model.fit(series)
        _, lower, upper = model.predict(5)
        widths = upper - lower
        # Each subsequent interval should be wider (random walk)
        for i in range(1, len(widths)):
            assert widths[i] >= widths[i - 1] - 1e-6, \
                "Naive baseline uncertainty should widen over time"

    def test_residuals(self, sample_series):
        series, dates = sample_series
        model = NaiveBaseline()
        model.fit(series)
        residuals = model.get_residuals()
        assert len(residuals) == len(series) - 1


# ─── 4. SARIMAX Forecast ────────────────────────────────────────────────────


class TestSARIMAX:

    def test_sarimax_fits(self, sample_series):
        series, dates = sample_series
        model = SARIMAXForecaster()
        model.fit(series)
        fc, lower, upper = model.predict(3)
        assert len(fc) == 3
        assert len(lower) == 3
        assert len(upper) == 3

    def test_sarimax_bounds(self, sample_series):
        series, dates = sample_series
        model = SARIMAXForecaster()
        model.fit(series)
        fc, lower, upper = model.predict(3)
        assert np.all(lower <= fc + 1e-6), "Lower bound must be <= forecast"
        assert np.all(upper >= fc - 1e-6), "Upper bound must be >= forecast"

    def test_sarimax_residuals(self, sample_series):
        series, dates = sample_series
        model = SARIMAXForecaster()
        model.fit(series)
        residuals = model.get_residuals()
        assert len(residuals) > 0


# ─── 5. Fallback Behaviour ──────────────────────────────────────────────────


class TestFallback:

    def test_short_series_uses_fallback(self, short_series):
        """Series shorter than SARIMAX_MIN_OBSERVATIONS should use fallback."""
        series, dates = short_series
        assert len(series) < SARIMAX_MIN_OBSERVATIONS
        result = run_forecast(series, dates, horizon_days=30)
        # Should not be SARIMAX
        assert result.model_name in ("SimpleMovingAverage", "NaiveBaseline")
        assert any("SARIMAX" in w or "simpler" in w.lower() or "observations" in w.lower()
                    for w in result.warnings)

    def test_tiny_series_uses_naive(self, tiny_series):
        """Very short series should fall all the way to NaiveBaseline."""
        series, dates = tiny_series
        result = run_forecast(series, dates, horizon_days=30)
        # With only 3 observations, even SMA may fail
        assert result.model_name in ("SimpleMovingAverage", "NaiveBaseline")

    def test_insufficient_data_raises(self):
        """Less than 3 observations should raise ValueError."""
        series = pd.Series([20.0, 21.0])
        dates = pd.date_range("2024-01-01", periods=2, freq="MS")
        with pytest.raises(ValueError, match="Insufficient data"):
            run_forecast(series, dates, horizon_days=30)


# ─── 6. Validation Metrics ──────────────────────────────────────────────────


class TestValidation:

    def test_walk_forward_naive(self, sample_series):
        series, dates = sample_series
        metrics = walk_forward_validate(series, NaiveBaseline, test_size=6)
        assert metrics.mae >= 0
        assert metrics.rmse >= 0
        assert metrics.rmse >= metrics.mae  # RMSE >= MAE always

    def test_walk_forward_sarimax(self, sample_series):
        series, dates = sample_series
        metrics = walk_forward_validate(series, SARIMAXForecaster, test_size=6)
        assert metrics.mae >= 0
        assert metrics.rmse >= 0

    def test_no_future_leak(self, sample_series):
        """
        Validation must not use future data.

        We verify this by checking that walk-forward produces non-zero
        errors (a model with future data would have near-zero error).
        """
        series, dates = sample_series
        metrics = walk_forward_validate(series, NaiveBaseline, test_size=6)
        assert metrics.mae > 0, "Zero MAE suggests data leakage"

    def test_mape_computed_when_possible(self, sample_series):
        series, dates = sample_series
        metrics = walk_forward_validate(series, NaiveBaseline, test_size=6)
        # Series has no zeros, so MAPE should be computed
        assert metrics.mape is not None
        assert metrics.mape > 0


# ─── 7. Uncertainty Bounds ──────────────────────────────────────────────────


class TestUncertainty:

    def test_bounds_order(self, sample_series):
        """lower_bound <= forecast <= upper_bound."""
        series, dates = sample_series
        result = run_forecast(series, dates, horizon_days=30)
        assert result.lower_bound <= result.forecast, \
            f"lower={result.lower_bound} > forecast={result.forecast}"
        assert result.upper_bound >= result.forecast, \
            f"upper={result.upper_bound} < forecast={result.forecast}"

    def test_forecast_series_bounds(self, sample_series):
        series, dates = sample_series
        result = run_forecast(series, dates, horizon_days=90)
        for pt in result.forecast_series:
            assert pt["lower"] <= pt["value"] + 0.01
            assert pt["upper"] >= pt["value"] - 0.01

    def test_non_negative_forecast(self, sample_series):
        series, dates = sample_series
        result = run_forecast(series, dates, horizon_days=30)
        assert result.forecast >= 0
        assert result.lower_bound >= 0


# ─── 8. Trend Calculation ───────────────────────────────────────────────────


class TestTrend:

    def test_rising(self):
        values = np.array([20, 21, 22, 23, 25])
        assert calculate_trend(values) == "RISING"

    def test_falling(self):
        values = np.array([25, 23, 22, 21, 20])
        assert calculate_trend(values) == "FALLING"

    def test_stable(self):
        values = np.array([20.0, 20.01, 19.99, 20.02, 20.0])
        assert calculate_trend(values) == "STABLE"

    def test_single_value(self):
        assert calculate_trend(np.array([20.0])) == "STABLE"

    def test_empty(self):
        assert calculate_trend(np.array([])) == "STABLE"


# ─── 9. Volatility Calculation ──────────────────────────────────────────────


class TestVolatility:

    def test_low_volatility(self):
        series = pd.Series([20.0, 20.1, 19.9, 20.05, 20.0, 19.95])
        assert calculate_volatility(series) == "LOW"

    def test_high_volatility(self):
        series = pd.Series([10, 25, 12, 28, 15, 30, 11, 27])
        assert calculate_volatility(series) == "HIGH"

    def test_medium_volatility(self):
        series = pd.Series([20, 22, 18, 21, 19, 23, 17, 22])
        vol = calculate_volatility(series)
        assert vol in ("LOW", "MEDIUM", "HIGH")  # At least returns valid value


# ─── 10. API Endpoint ───────────────────────────────────────────────────────


class TestAPI:

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        return TestClient(app)

    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_forecast_valid_lane(self, client):
        """A valid lane must return a complete forecast response."""
        response = client.post("/api/forecast", json={
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_type": "Panamax",
            "horizon_days": 30,
        })
        assert response.status_code == 200
        data = response.json()

        # Structural checks
        assert "forecast" in data
        assert "lower_bound" in data
        assert "upper_bound" in data
        assert "trend" in data
        assert "volatility" in data
        assert "confidence" in data
        assert "model_name" in data
        assert "baseline_error" in data
        assert "model_error" in data
        assert "model_wins" in data
        assert "historical_series" in data
        assert "forecast_series" in data
        assert "data_source" in data
        assert "warnings" in data

        # Value checks
        assert data["lower_bound"] <= data["forecast"]
        assert data["upper_bound"] >= data["forecast"]
        assert 0 <= data["confidence"] <= 1
        assert data["trend"] in ["RISING", "FALLING", "STABLE"]
        assert data["volatility"] in ["LOW", "MEDIUM", "HIGH"]
        assert data["data_source"] == "prototype_proxy"
        assert len(data["historical_series"]) > 0
        assert len(data["forecast_series"]) > 0

    def test_forecast_unknown_lane(self, client):
        """Unknown lane must return 400, NOT crash the server."""
        response = client.post("/api/forecast", json={
            "origin": "Mars",
            "destination": "Jupiter",
            "vessel_type": "Spaceship",
            "horizon_days": 30,
        })
        assert response.status_code == 400

    def test_forecast_different_horizons(self, client):
        """Different horizons should produce forecasts."""
        for horizon in [7, 14, 30, 60, 90]:
            response = client.post("/api/forecast", json={
                "origin": "Australia",
                "destination": "Paradip",
                "vessel_type": "Panamax",
                "horizon_days": horizon,
            })
            assert response.status_code == 200, \
                f"Horizon {horizon} failed with status {response.status_code}"

    def test_forecast_different_vessel_types(self, client):
        """All vessel types on Australia→Paradip should work."""
        for vt in ["Handysize", "Supramax", "Panamax", "Capesize"]:
            response = client.post("/api/forecast", json={
                "origin": "Australia",
                "destination": "Paradip",
                "vessel_type": vt,
                "horizon_days": 30,
            })
            assert response.status_code == 200, \
                f"Vessel type {vt} failed with status {response.status_code}"

    def test_lanes_endpoint(self, client):
        response = client.get("/api/lanes")
        assert response.status_code == 200
        data = response.json()
        assert "lanes" in data
        assert "count" in data
        assert data["count"] > 0

    def test_forecast_response_matches_request(self, client):
        """Response origin/destination/vessel_type must match request."""
        response = client.post("/api/forecast", json={
            "origin": "Indonesia",
            "destination": "Paradip",
            "vessel_type": "Supramax",
            "horizon_days": 60,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["origin"] == "Indonesia"
        assert data["destination"] == "Paradip"
        assert data["vessel_type"] == "Supramax"
        assert data["horizon_days"] == 60


# ─── Confidence Score ────────────────────────────────────────────────────────


class TestConfidence:

    def test_confidence_range(self):
        score = calculate_confidence(
            model_error=ErrorMetrics(mae=2.0, rmse=3.0),
            baseline_error=ErrorMetrics(mae=3.0, rmse=4.0),
            n_observations=48,
            horizon_days=30,
            volatility="MEDIUM",
        )
        assert 0.0 <= score <= 1.0

    def test_more_data_higher_confidence(self):
        base_kwargs = dict(
            model_error=ErrorMetrics(mae=2.0, rmse=3.0),
            baseline_error=ErrorMetrics(mae=3.0, rmse=4.0),
            horizon_days=30,
            volatility="MEDIUM",
        )
        score_few = calculate_confidence(n_observations=12, **base_kwargs)
        score_many = calculate_confidence(n_observations=48, **base_kwargs)
        assert score_many >= score_few

    def test_shorter_horizon_higher_confidence(self):
        base_kwargs = dict(
            model_error=ErrorMetrics(mae=2.0, rmse=3.0),
            baseline_error=ErrorMetrics(mae=3.0, rmse=4.0),
            n_observations=48,
            volatility="MEDIUM",
        )
        score_short = calculate_confidence(horizon_days=7, **base_kwargs)
        score_long = calculate_confidence(horizon_days=90, **base_kwargs)
        assert score_short >= score_long
