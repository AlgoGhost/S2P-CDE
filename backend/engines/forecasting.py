"""
VARUNEETI Freight Forecasting Engine
=====================================

Implements two forecasting models with a robust fallback hierarchy:

    SARIMAX → Simple Exponential Smoothing → Naive Persistence

Each model exposes:
    - fit(series)
    - predict(horizon) → (forecast, lower, upper)
    - validate(series, test_size) → ErrorMetrics

Time-series validation is walk-forward; observations are NEVER shuffled.

Uncertainty is derived from SARIMAX prediction intervals or, for
fallback models, from recent residual volatility. Intervals are never
made up arbitrarily.

Confidence is a composite heuristic score, NOT a calibrated probability.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from backend.config import (
    CONFIDENCE_WEIGHT_DATA_AMOUNT,
    CONFIDENCE_WEIGHT_HORIZON,
    CONFIDENCE_WEIGHT_VALIDATION,
    CONFIDENCE_WEIGHT_VOLATILITY,
    FORECAST_CONFIDENCE_LEVEL,
    SARIMAX_MIN_OBSERVATIONS,
    SARIMAX_ORDER,
    SARIMAX_SEASONAL_ORDER,
    TREND_THRESHOLD_PCT,
    VOLATILITY_HIGH_THRESHOLD,
    VOLATILITY_LOW_THRESHOLD,
)

logger = logging.getLogger(__name__)

# Suppress convergence warnings during SARIMAX fitting — we handle
# failures gracefully in the fallback hierarchy.
warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")
warnings.filterwarnings("ignore", category=FutureWarning, module="statsmodels")


# ─── Data Structures ────────────────────────────────────────────────────────


@dataclass
class ErrorMetrics:
    """Validation error metrics for a forecast model."""

    mae: float
    rmse: float
    mape: Optional[float] = None


@dataclass
class ForecastResult:
    """Complete result from the forecasting engine."""

    forecast: float
    lower_bound: float
    upper_bound: float
    trend: str  # RISING / FALLING / STABLE
    volatility: str  # LOW / MEDIUM / HIGH
    confidence: float  # 0–1
    model_name: str
    baseline_error: ErrorMetrics
    model_error: ErrorMetrics
    model_wins: bool
    historical_series: list[dict] = field(default_factory=list)
    forecast_series: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ─── Base Forecaster ────────────────────────────────────────────────────────


class BaseForecaster:
    """Abstract base for all forecasters."""

    name: str = "base"

    def fit(self, series: pd.Series) -> None:
        raise NotImplementedError

    def predict(
        self, horizon_steps: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Returns (forecast, lower, upper) arrays of length horizon_steps."""
        raise NotImplementedError

    def get_residuals(self) -> np.ndarray:
        """Return in-sample residuals for uncertainty estimation."""
        raise NotImplementedError


# ─── Naive Persistence Baseline ─────────────────────────────────────────────


class NaiveBaseline(BaseForecaster):
    """
    Naive persistence: forecast = last observed value.

    Uncertainty is estimated from the standard deviation of recent
    first-differences (changes between consecutive observations).
    """

    name = "NaiveBaseline"

    def __init__(self) -> None:
        self._last_value: float = 0.0
        self._residual_std: float = 0.0
        self._series: Optional[pd.Series] = None

    def fit(self, series: pd.Series) -> None:
        self._series = series.copy()
        self._last_value = float(series.iloc[-1])
        diffs = series.diff().dropna()
        self._residual_std = float(diffs.std()) if len(diffs) > 1 else float(series.std())

    def predict(
        self, horizon_steps: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        forecast = np.full(horizon_steps, self._last_value)
        # Widen uncertainty with sqrt(step) — random walk assumption
        steps = np.arange(1, horizon_steps + 1)
        margin = 1.96 * self._residual_std * np.sqrt(steps)
        lower = forecast - margin
        upper = forecast + margin
        return forecast, lower, upper

    def get_residuals(self) -> np.ndarray:
        if self._series is None or len(self._series) < 2:
            return np.array([0.0])
        # One-step-ahead residuals: actual[t] - actual[t-1]
        shifted = self._series.shift(1)
        residuals = (self._series - shifted).dropna()
        return residuals.values


# ─── SARIMAX Forecaster ─────────────────────────────────────────────────────


class SARIMAXForecaster(BaseForecaster):
    """
    Seasonal ARIMA with optional exogenous variables.

    Uses statsmodels SARIMAX. If fitting fails, raises RuntimeError
    so the caller can invoke the fallback hierarchy.

    Configuration comes from backend.config.
    """

    name = "SARIMAX"

    def __init__(
        self,
        order: tuple = SARIMAX_ORDER,
        seasonal_order: tuple = SARIMAX_SEASONAL_ORDER,
    ) -> None:
        self._order = order
        self._seasonal_order = seasonal_order
        self._model = None
        self._result = None
        self._series: Optional[pd.Series] = None

    def fit(self, series: pd.Series) -> None:
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        self._series = series.copy()

        # Determine if we have enough data for the seasonal component
        seasonal_period = self._seasonal_order[3]
        effective_seasonal_order = self._seasonal_order

        if len(series) < 2 * seasonal_period:
            # Not enough data for seasonal model — drop seasonality
            logger.warning(
                "Only %d observations (need %d for seasonality). "
                "Using non-seasonal ARIMA.",
                len(series),
                2 * seasonal_period,
            )
            effective_seasonal_order = (0, 0, 0, 0)

        try:
            model = SARIMAX(
                series,
                order=self._order,
                seasonal_order=effective_seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            self._result = model.fit(disp=False, maxiter=200)
            self._model = model
            logger.info(
                "SARIMAX fit: AIC=%.2f, order=%s, seasonal=%s, n=%d",
                self._result.aic,
                self._order,
                effective_seasonal_order,
                len(series),
            )
        except Exception as e:
            logger.error("SARIMAX fit failed: %s", e)
            raise RuntimeError(f"SARIMAX fit failed: {e}") from e

    def predict(
        self, horizon_steps: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self._result is None:
            raise RuntimeError("Model not fitted")

        forecast_obj = self._result.get_forecast(steps=horizon_steps)
        forecast = forecast_obj.predicted_mean.values

        alpha = 1 - FORECAST_CONFIDENCE_LEVEL
        ci = forecast_obj.conf_int(alpha=alpha)
        lower = ci.iloc[:, 0].values
        upper = ci.iloc[:, 1].values

        return forecast, lower, upper

    def get_residuals(self) -> np.ndarray:
        if self._result is None:
            return np.array([0.0])
        return self._result.resid.values


# ─── Simple Statistical Fallback ────────────────────────────────────────────


class SimpleMovingAverageForecaster(BaseForecaster):
    """
    Simple moving-average forecast: uses the mean of recent observations.
    Used as an intermediate fallback between SARIMAX and naive persistence.
    """

    name = "SimpleMovingAverage"

    def __init__(self, window: int = 6) -> None:
        self._window = window
        self._forecast_value: float = 0.0
        self._residual_std: float = 0.0
        self._series: Optional[pd.Series] = None

    def fit(self, series: pd.Series) -> None:
        self._series = series.copy()
        window = min(self._window, len(series))
        recent = series.iloc[-window:]
        self._forecast_value = float(recent.mean())
        # In-sample residuals from moving average
        ma = series.rolling(window=window, min_periods=1).mean()
        residuals = (series - ma).dropna()
        self._residual_std = float(residuals.std()) if len(residuals) > 1 else float(series.std())

    def predict(
        self, horizon_steps: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        forecast = np.full(horizon_steps, self._forecast_value)
        steps = np.arange(1, horizon_steps + 1)
        margin = 1.96 * self._residual_std * np.sqrt(steps)
        lower = forecast - margin
        upper = forecast + margin
        return forecast, lower, upper

    def get_residuals(self) -> np.ndarray:
        if self._series is None:
            return np.array([0.0])
        window = min(self._window, len(self._series))
        ma = self._series.rolling(window=window, min_periods=1).mean()
        return (self._series - ma).dropna().values


# ─── Validation ─────────────────────────────────────────────────────────────


def walk_forward_validate(
    series: pd.Series,
    forecaster_class: type,
    forecaster_kwargs: dict | None = None,
    test_size: int = 6,
    horizon_steps: int = 1,
) -> ErrorMetrics:
    """
    Walk-forward (rolling-origin) validation.

    Trains on data up to time t, forecasts one step ahead, repeats.
    NEVER shuffles data. Observations remain in chronological order.

    Parameters
    ----------
    series : pd.Series
        Full time series to evaluate.
    forecaster_class : type
        Class of the forecaster to evaluate.
    forecaster_kwargs : dict, optional
        Extra kwargs for the forecaster constructor.
    test_size : int
        Number of one-step-ahead forecasts to make from the end.
    horizon_steps : int
        Steps-ahead for each forecast (usually 1 for validation).

    Returns
    -------
    ErrorMetrics
    """
    if forecaster_kwargs is None:
        forecaster_kwargs = {}

    n = len(series)
    test_size = min(test_size, n // 3)  # At most 1/3 of data for test
    test_size = max(test_size, 1)

    actuals = []
    predictions = []

    for i in range(test_size):
        split_point = n - test_size + i
        train = series.iloc[:split_point]

        if len(train) < 3:
            continue

        try:
            model = forecaster_class(**forecaster_kwargs)
            model.fit(train)
            fc, _, _ = model.predict(horizon_steps)
            pred_value = float(fc[0])  # One-step-ahead
        except Exception:
            # If model fails, use last training value as prediction
            pred_value = float(train.iloc[-1])

        actual_value = float(series.iloc[split_point])
        actuals.append(actual_value)
        predictions.append(pred_value)

    actuals = np.array(actuals)
    predictions = np.array(predictions)

    if len(actuals) == 0:
        return ErrorMetrics(mae=0.0, rmse=0.0, mape=None)

    errors = actuals - predictions
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))

    # MAPE — only if no zeros in actuals
    mape = None
    if np.all(actuals != 0):
        mape = float(np.mean(np.abs(errors / actuals)) * 100)

    return ErrorMetrics(mae=mae, rmse=rmse, mape=mape)


# ─── Trend / Volatility / Confidence ────────────────────────────────────────


def calculate_trend(forecast_values: np.ndarray) -> str:
    """
    Determine trend from the forecast trajectory.

    Uses percentage change between first and last forecast point.
    If |change| < TREND_THRESHOLD_PCT → STABLE.
    """
    if len(forecast_values) < 2:
        return "STABLE"

    first = forecast_values[0]
    last = forecast_values[-1]

    if first == 0:
        return "STABLE"

    pct_change = ((last - first) / abs(first)) * 100

    if pct_change > TREND_THRESHOLD_PCT:
        return "RISING"
    elif pct_change < -TREND_THRESHOLD_PCT:
        return "FALLING"
    else:
        return "STABLE"


def calculate_volatility(series: pd.Series) -> str:
    """
    Classify volatility based on coefficient of variation (CV = std / mean)
    of the most recent 12 observations (or all if fewer exist).

    Thresholds (from config):
        CV < 5%  → LOW
        CV > 15% → HIGH
        else     → MEDIUM
    """
    recent = series.iloc[-12:] if len(series) > 12 else series
    mean = recent.mean()
    std = recent.std()

    if mean == 0 or pd.isna(mean) or pd.isna(std):
        return "MEDIUM"

    cv = abs(std / mean)

    if cv < VOLATILITY_LOW_THRESHOLD:
        return "LOW"
    elif cv > VOLATILITY_HIGH_THRESHOLD:
        return "HIGH"
    else:
        return "MEDIUM"


def calculate_confidence(
    model_error: ErrorMetrics,
    baseline_error: ErrorMetrics,
    n_observations: int,
    horizon_days: int,
    volatility: str,
) -> float:
    """
    Composite confidence score (0–1).

    Components (all normalized to 0–1, then weighted):

    1. Validation quality:  how much the model beats baseline
    2. Data sufficiency:    more data → higher confidence
    3. Horizon penalty:     longer horizons → lower confidence
    4. Volatility penalty:  higher volatility → lower confidence

    This is a HEURISTIC, not a calibrated probability.
    """
    # 1. Validation quality: ratio of model MAE to baseline MAE
    if baseline_error.mae > 0:
        improvement = 1.0 - (model_error.mae / baseline_error.mae)
        validation_score = max(0.0, min(1.0, 0.5 + improvement))
    else:
        validation_score = 0.5

    # 2. Data sufficiency: sigmoid-like ramp from 12 to 48 observations
    data_score = min(1.0, max(0.0, (n_observations - 6) / 42))

    # 3. Horizon penalty: linear decay from 7 to 90 days
    horizon_score = max(0.0, 1.0 - (horizon_days - 7) / 120)

    # 4. Volatility penalty
    vol_scores = {"LOW": 1.0, "MEDIUM": 0.6, "HIGH": 0.3}
    vol_score = vol_scores.get(volatility, 0.5)

    confidence = (
        CONFIDENCE_WEIGHT_VALIDATION * validation_score
        + CONFIDENCE_WEIGHT_DATA_AMOUNT * data_score
        + CONFIDENCE_WEIGHT_HORIZON * horizon_score
        + CONFIDENCE_WEIGHT_VOLATILITY * vol_score
    )

    return round(max(0.0, min(1.0, confidence)), 3)


# ─── Main Forecasting Interface ─────────────────────────────────────────────


def run_forecast(
    series: pd.Series,
    dates: pd.DatetimeIndex | pd.Series,
    horizon_days: int,
    freq_days: int = 30,
) -> ForecastResult:
    """
    Run the full forecasting pipeline on a single time series.

    Parameters
    ----------
    series : pd.Series
        Freight rate observations (chronological, no gaps expected).
    dates : DatetimeIndex or Series
        Corresponding dates for each observation.
    horizon_days : int
        How many days ahead to forecast.
    freq_days : int
        Approximate frequency of observations in days (default 30 for monthly).

    Returns
    -------
    ForecastResult

    Fallback hierarchy:
        SARIMAX → SimpleMovingAverage → NaiveBaseline
    """
    forecast_warnings: list[str] = []
    n_obs = len(series)

    # Convert horizon_days to steps (number of periods)
    horizon_steps = max(1, horizon_days // freq_days)

    logger.info(
        "Forecasting: n_obs=%d, horizon_days=%d, horizon_steps=%d",
        n_obs,
        horizon_days,
        horizon_steps,
    )

    if n_obs < 3:
        raise ValueError(
            f"Insufficient data: only {n_obs} observations. Need at least 3."
        )

    # ── Validation test size ──
    test_size = min(max(3, n_obs // 4), 12)

    # ── Always compute baseline ──
    baseline_metrics = walk_forward_validate(
        series, NaiveBaseline, test_size=test_size
    )

    # ── Try SARIMAX ──
    selected_model: BaseForecaster | None = None
    model_metrics: ErrorMetrics | None = None

    if n_obs >= SARIMAX_MIN_OBSERVATIONS:
        try:
            model_metrics = walk_forward_validate(
                series, SARIMAXForecaster, test_size=test_size
            )
            # Fit on full series for final forecast
            sarimax = SARIMAXForecaster()
            sarimax.fit(series)
            selected_model = sarimax
            logger.info("SARIMAX selected. MAE=%.3f", model_metrics.mae)
        except Exception as e:
            logger.warning("SARIMAX failed: %s. Trying fallback.", e)
            forecast_warnings.append(f"SARIMAX failed ({e}); using fallback.")
    else:
        forecast_warnings.append(
            f"Only {n_obs} observations (need {SARIMAX_MIN_OBSERVATIONS} for SARIMAX). "
            "Using simpler model."
        )

    # ── Fallback: SimpleMovingAverage ──
    if selected_model is None and n_obs >= 6:
        try:
            model_metrics = walk_forward_validate(
                series, SimpleMovingAverageForecaster, test_size=test_size
            )
            sma = SimpleMovingAverageForecaster()
            sma.fit(series)
            selected_model = sma
            logger.info("SimpleMovingAverage fallback. MAE=%.3f", model_metrics.mae)
        except Exception as e:
            logger.warning("SimpleMovingAverage failed: %s", e)
            forecast_warnings.append(f"SMA fallback failed ({e}).")

    # ── Final fallback: NaiveBaseline ──
    if selected_model is None:
        naive = NaiveBaseline()
        naive.fit(series)
        selected_model = naive
        model_metrics = baseline_metrics
        forecast_warnings.append("Using NaiveBaseline (final fallback).")
        logger.info("NaiveBaseline final fallback.")

    # ── Generate forecast ──
    fc_values, fc_lower, fc_upper = selected_model.predict(horizon_steps)

    # Ensure bounds are sensible (lower <= forecast <= upper)
    fc_lower = np.minimum(fc_lower, fc_values)
    fc_upper = np.maximum(fc_upper, fc_values)

    # Ensure non-negative freight rates
    fc_values = np.maximum(fc_values, 0.0)
    fc_lower = np.maximum(fc_lower, 0.0)
    fc_upper = np.maximum(fc_upper, 0.0)

    # ── Build forecast dates ──
    last_date = pd.Timestamp(dates.iloc[-1]) if hasattr(dates, "iloc") else pd.Timestamp(dates[-1])
    forecast_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=freq_days),
        periods=horizon_steps,
        freq=f"{freq_days}D",
    )

    # ── Trend ──
    trend = calculate_trend(fc_values)

    # ── Volatility ──
    volatility = calculate_volatility(series)

    # ── Confidence ──
    confidence = calculate_confidence(
        model_error=model_metrics,
        baseline_error=baseline_metrics,
        n_observations=n_obs,
        horizon_days=horizon_days,
        volatility=volatility,
    )

    # ── Model wins? ──
    model_wins = model_metrics.mae < baseline_metrics.mae

    # ── Build series for response ──
    historical = [
        {"date": str(d.date()) if hasattr(d, "date") else str(d), "value": round(float(v), 2)}
        for d, v in zip(dates, series)
    ]

    forecast_list = [
        {
            "date": str(d.date()),
            "value": round(float(v), 2),
            "lower": round(float(lo), 2),
            "upper": round(float(hi), 2),
        }
        for d, v, lo, hi in zip(forecast_dates, fc_values, fc_lower, fc_upper)
    ]

    # Use the mean of forecast values as the point forecast
    point_forecast = round(float(fc_values.mean()), 2)
    bound_lower = round(float(fc_lower.mean()), 2)
    bound_upper = round(float(fc_upper.mean()), 2)

    return ForecastResult(
        forecast=point_forecast,
        lower_bound=bound_lower,
        upper_bound=bound_upper,
        trend=trend,
        volatility=volatility,
        confidence=confidence,
        model_name=selected_model.name,
        baseline_error=baseline_metrics,
        model_error=model_metrics,
        model_wins=model_wins,
        historical_series=historical,
        forecast_series=forecast_list,
        warnings=forecast_warnings,
    )
