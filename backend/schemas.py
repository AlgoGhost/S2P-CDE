"""
VARUNEETI Pydantic Schemas
All request and response models for the API.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─── Enums ───────────────────────────────────────────────────────────────────


class TrendDirection(str, Enum):
    RISING = "RISING"
    FALLING = "FALLING"
    STABLE = "STABLE"


class VolatilityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CharterStrategy(str, Enum):
    SPOT = "SPOT"
    SHORT_TERM = "SHORT_TERM"
    MEDIUM_TERM = "MEDIUM_TERM"
    HYBRID = "HYBRID"


class FeasibilityStatus(str, Enum):
    DIRECT_FEASIBLE = "DIRECT_FEASIBLE"
    CONDITIONALLY_FEASIBLE = "CONDITIONALLY_FEASIBLE"
    INFEASIBLE = "INFEASIBLE"


# ─── Health ──────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    service: str = "VARUNEETI"


# ─── Forecast ────────────────────────────────────────────────────────────────


class ForecastRequest(BaseModel):
    origin: str = Field(..., description="Origin port/country", examples=["Australia"])
    destination: str = Field(..., description="Destination port", examples=["Paradip"])
    vessel_type: str = Field(..., description="Vessel class", examples=["Panamax"])
    horizon_days: int = Field(
        30,
        description="Forecast horizon in days",
        ge=1,
        le=365,
    )


class ErrorMetrics(BaseModel):
    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    mape: Optional[float] = Field(None, description="Mean Absolute Percentage Error (if computable)")


class TimeSeriesPoint(BaseModel):
    date: str
    value: float
    lower: Optional[float] = None
    upper: Optional[float] = None


class ForecastResponse(BaseModel):
    origin: str
    destination: str
    vessel_type: str
    horizon_days: int

    forecast: float = Field(..., description="Point forecast (USD/tonne)")
    lower_bound: float = Field(..., description="Lower prediction interval bound")
    upper_bound: float = Field(..., description="Upper prediction interval bound")

    trend: TrendDirection
    volatility: VolatilityLevel
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Model confidence score (0-1). This is a composite heuristic, "
            "not a calibrated probability."
        ),
    )

    model_name: str = Field(..., description="Name of the model that produced the forecast")
    baseline_error: ErrorMetrics
    model_error: ErrorMetrics
    model_wins: bool = Field(
        ...,
        description="True if the selected model outperforms the naive baseline on MAE",
    )

    historical_series: list[TimeSeriesPoint] = Field(
        default_factory=list,
        description="Historical observations used for the forecast",
    )
    forecast_series: list[TimeSeriesPoint] = Field(
        default_factory=list,
        description="Forecasted points with prediction intervals",
    )

    data_source: str = Field(
        "prototype_proxy",
        description="Provenance of the underlying data",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any warnings about data quality, fallback usage, etc.",
    )


# ─── Analyze (placeholder for future slices) ────────────────────────────────


class ScenarioDefinition(BaseModel):
    """A single what-if case applied to the base decision."""
    scenario_id: str
    label: str
    freight_multiplier: float = Field(1.0, description="Multiplier on the forecast point estimate")
    congestion_multiplier: float = Field(1.0, description="Multiplier on the port congestion index")
    excluded_vessel_types: list[str] = Field(default_factory=list)
    notes: str = ""


class ScenarioOutcome(BaseModel):
    """Result of re-solving the decision under one scenario."""
    scenario_id: str
    label: str
    status: str

    strategy: str
    vessel_class: str
    voyages: int
    lock_percentage: float

    expected_cost: float
    cost_per_tonne: float
    risk_score: float

    cost_delta_vs_base: float = Field(..., description="Expected cost minus base case")
    cost_pct_delta_vs_base: float
    strategy_changed: bool
    vessel_changed: bool

    notes: str = ""


class ScenarioAnalysisResponse(BaseModel):
    base_scenario_id: str
    outcomes: list[ScenarioOutcome]
    recommendation_is_robust: bool = Field(
        ..., description="True when no scenario changes the recommended strategy"
    )
    robustness_summary: str
    worst_case_scenario_id: Optional[str] = None
    assumptions: list[str]
    data_status: dict


class FeasibilityRequest(BaseModel):
    origin: str = Field(..., description="Origin port/country", examples=["Australia"])
    destination: str = Field(..., description="Destination port", examples=["Paradip"])
    cargo_quantity: float = Field(..., description="Total cargo quantity in tonnes", gt=0)
    parcel_quantity: Optional[float] = Field(None, description="Specific parcel quantity if restricted")
    loading_port: Optional[str] = Field(None, description="Specific loading port (optional)")


class LighteringDetails(BaseModel):
    required: bool = False
    lightering_quantity: float = 0.0
    incremental_cost: float = 0.0
    incremental_days: float = 0.0
    operational_risk: str = "NONE"


class VesselCandidate(BaseModel):
    vessel_type: str
    capacity: float
    draft: float
    loa: float
    beam: float
    
    parcel_capacity: float = Field(..., description="Cargo carried per voyage")
    voyages_required: int = Field(..., description="Number of voyages needed for total cargo")

    direct_feasible: bool
    conditional_feasible: bool
    status: FeasibilityStatus

    fit_score: float = Field(..., ge=0, le=100)
    fit_reasons: list[str]

    passed_constraints: list[str]
    failed_constraints: list[str]

    handling_days: float
    waiting_days: float
    port_time_days: float

    port_cost: float
    demurrage_exposure: float
    lightering_cost: float
    total_operational_cost: float
    
    lightering: Optional[LighteringDetails] = None


class FeasibilityResponse(BaseModel):
    origin: str
    destination: str
    cargo_quantity: float
    parcel_quantity: Optional[float] = None
    loading_port: Optional[str] = None
    
    port: dict = Field(..., description="Port specifications used")
    vessels: list[VesselCandidate] = Field(..., description="All evaluated vessel classes")
    recommended_vessel: Optional[VesselCandidate] = None
    alternatives: list[VesselCandidate] = Field(default_factory=list, description="Alternative feasible vessels")
    assumptions: list[str] = Field(default_factory=list, description="Explicit assumptions applied")


# ─── Risk (Emergency MVP) ──────────────────────────────────────────────────

class RiskRequest(BaseModel):
    origin: str
    destination: str
    cargo_quantity: float
    parcel_quantity: float
    delivery_start: str
    delivery_end: str

class RiskDriver(BaseModel):
    factor: str
    score: float
    weight: float
    contribution: float
    severity: str
    explanation: str

class RiskResponse(BaseModel):
    overall_score: float = Field(..., description="Overall risk score 0-100")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH")
    top_drivers: list[RiskDriver]
    all_drivers: list[RiskDriver] = Field(
        default_factory=list,
        description="Every scored risk factor (superset of top_drivers), for UI display",
    )
    assumptions: list[str]


# ─── Optimization (Emergency MVP) ──────────────────────────────────────────

class OptimizeRequest(BaseModel):
    origin: str
    destination: str
    cargo_quantity: float
    parcel_quantity: float
    delivery_start: str
    delivery_end: str

class StrategyComparison(BaseModel):
    strategy: str
    cost: float
    cost_per_tonne: float
    lock_percentage: float
    locked_tonnage: float
    flexible_tonnage: float

class RecommendationDetails(BaseModel):
    strategy: str
    vessel_class: str
    locked_tonnage: float
    flexible_tonnage: float
    lock_percentage: float
    expected_cost: float
    cost_per_tonne: float
    risk_score: float

class OptimizeResponse(BaseModel):
    status: str
    recommendation: RecommendationDetails
    strategy_comparison: list[StrategyComparison]
    voyages: int
    decision_drivers: list[str]
    assumptions: list[str]
    data_status: dict

