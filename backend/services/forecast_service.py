"""
VARUNEETI Forecast Service
============================

Clean interface between the API layer and the forecasting engine.

    ForecastService.forecast(origin, destination, vessel_type, horizon_days)
        → ForecastResponse (Pydantic model)

The rest of VARUNEETI should not need to know how SARIMAX works
internally. Later model upgrades (LightGBM, ensemble, commercial
models) can be done without touching the optimizer or API layers.
"""

from __future__ import annotations

import logging

from backend.config import ABSOLUTE_MIN_OBSERVATIONS, DATA_DISCLAIMER, DATA_SOURCE_LABEL
from backend.engines.forecasting import ForecastResult, run_forecast
from backend.schemas import (
    ErrorMetrics as ErrorMetricsSchema,
    ForecastResponse,
    TimeSeriesPoint,
    TrendDirection,
    VolatilityLevel,
)
from backend.services.data_service import get_data_adapter

logger = logging.getLogger(__name__)


class ForecastService:
    """
    Stateless service that orchestrates the forecasting pipeline.

    Usage:
        response = ForecastService.forecast(
            origin="Australia",
            destination="Paradip",
            vessel_type="Panamax",
            horizon_days=30,
        )
    """

    @staticmethod
    def forecast(
        origin: str,
        destination: str,
        vessel_type: str,
        horizon_days: int = 30,
    ) -> ForecastResponse:
        """
        Run the full forecasting pipeline for a shipping lane.

        Parameters
        ----------
        origin : str
            Origin country/region.
        destination : str
            Destination port on India's East Coast.
        vessel_type : str
            Vessel class (Handysize, Supramax, Panamax, Capesize).
        horizon_days : int
            Forecast horizon in days.

        Returns
        -------
        ForecastResponse
            Complete Pydantic response model ready for API serialization.

        Raises
        ------
        ValueError
            If the lane has insufficient data.
        """
        adapter = get_data_adapter()

        # ── Load lane data ──
        lane_df = adapter.get_lane_data(origin, destination, vessel_type)

        if len(lane_df) == 0:
            raise ValueError(
                f"No data found for lane {origin}→{destination} [{vessel_type}]. "
                f"Available lanes: check GET /api/lanes."
            )

        if len(lane_df) < ABSOLUTE_MIN_OBSERVATIONS:
            raise ValueError(
                f"Insufficient data for {origin}→{destination} [{vessel_type}]: "
                f"only {len(lane_df)} observations (minimum {ABSOLUTE_MIN_OBSERVATIONS})."
            )

        # ── Extract time series ──
        series = lane_df["freight_rate"].reset_index(drop=True)
        dates = lane_df["date"].reset_index(drop=True)

        # ── Detect frequency ──
        if len(dates) >= 2:
            median_gap = dates.diff().dropna().dt.days.median()
            freq_days = max(1, int(median_gap))
        else:
            freq_days = 30

        logger.info(
            "ForecastService: %s→%s [%s], n=%d, horizon=%d days, freq=%d days",
            origin, destination, vessel_type, len(series), horizon_days, freq_days,
        )

        # ── Run engine ──
        result: ForecastResult = run_forecast(
            series=series,
            dates=dates,
            horizon_days=horizon_days,
            freq_days=freq_days,
        )

        # ── Convert to Pydantic response ──
        return ForecastResponse(
            origin=origin,
            destination=destination,
            vessel_type=vessel_type,
            horizon_days=horizon_days,
            forecast=result.forecast,
            lower_bound=result.lower_bound,
            upper_bound=result.upper_bound,
            trend=TrendDirection(result.trend),
            volatility=VolatilityLevel(result.volatility),
            confidence=result.confidence,
            model_name=result.model_name,
            baseline_error=ErrorMetricsSchema(
                mae=round(result.baseline_error.mae, 3),
                rmse=round(result.baseline_error.rmse, 3),
                mape=(
                    round(result.baseline_error.mape, 2)
                    if result.baseline_error.mape is not None
                    else None
                ),
            ),
            model_error=ErrorMetricsSchema(
                mae=round(result.model_error.mae, 3),
                rmse=round(result.model_error.rmse, 3),
                mape=(
                    round(result.model_error.mape, 2)
                    if result.model_error.mape is not None
                    else None
                ),
            ),
            model_wins=result.model_wins,
            historical_series=[
                TimeSeriesPoint(**pt) for pt in result.historical_series
            ],
            forecast_series=[
                TimeSeriesPoint(**pt) for pt in result.forecast_series
            ],
            data_source=DATA_SOURCE_LABEL,
            warnings=result.warnings,
        )

    @staticmethod
    def get_available_lanes() -> list[dict]:
        """Return all available (origin, destination, vessel_type) combinations."""
        adapter = get_data_adapter()
        return adapter.get_available_lanes()
