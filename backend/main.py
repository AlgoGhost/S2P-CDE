"""
VARUNEETI — Maritime Charter Decision Intelligence Engine
==========================================================

FastAPI application entry point.

Run with:
    cd backend
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.config import APP_DESCRIPTION, APP_NAME, APP_VERSION, CORS_ORIGINS
from backend.schemas import (
    ForecastRequest,
    ForecastResponse,
    HealthResponse,
    FeasibilityRequest,
    FeasibilityResponse,
    OptimizeRequest,
    OptimizeResponse,
    RiskRequest,
    RiskResponse,
    ScenarioAnalysisResponse,
)
from backend.services.forecast_service import ForecastService
from backend.services.vessel_service import VesselService
from backend.services.optimize_service import OptimizeService
from backend.services.risk_service import RiskService
from backend.services.scenario_service import ScenarioService

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Application ─────────────────────────────────────────────────────────────

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ──────────────────────────────────────────────────────────────────


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(version=APP_VERSION)


# ─── Lanes ───────────────────────────────────────────────────────────────────


@app.get("/api/lanes")
async def get_lanes():
    """Return all available shipping lanes with observation counts."""
    try:
        lanes = ForecastService.get_available_lanes()
        return {"lanes": lanes, "count": len(lanes)}
    except Exception as e:
        logger.error("Failed to load lanes: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Forecast ────────────────────────────────────────────────────────────────


@app.post("/api/forecast", response_model=ForecastResponse)
async def forecast(request: ForecastRequest):
    """
    Generate freight rate forecast for a specific shipping lane.

    The forecasting engine uses a fallback hierarchy:
        SARIMAX → SimpleMovingAverage → NaiveBaseline

    Returns point forecast, confidence intervals, trend, volatility,
    model validation metrics, and historical/forecast time series.
    """
    logger.info(
        "Forecast request: %s→%s [%s] %d days",
        request.origin,
        request.destination,
        request.vessel_type,
        request.horizon_days,
    )

    try:
        response = ForecastService.forecast(
            origin=request.origin,
            destination=request.destination,
            vessel_type=request.vessel_type,
            horizon_days=request.horizon_days,
        )
        return response
    except ValueError as e:
        logger.warning("Forecast ValueError: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
# ─── Feasibility ─────────────────────────────────────────────────────────────


@app.post("/api/feasibility", response_model=FeasibilityResponse)
async def evaluate_feasibility(request: FeasibilityRequest):
    """
    Evaluate physical and operational feasibility for a given cargo and route.
    Returns direct feasibility, conditional lightering alternatives, or infeasible status.
    """
    logger.info(
        "Feasibility request: %s→%s, qty=%s",
        request.origin,
        request.destination,
        request.cargo_quantity,
    )
    
    try:
        response = VesselService.evaluate_feasibility(request)
        return response
    except ValueError as e:
        logger.warning("Feasibility ValueError: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Feasibility error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Feasibility engine failed: {e}")

# ─── Risk (Emergency MVP) ────────────────────────────────────────────────────

@app.post("/api/risk", response_model=RiskResponse)
async def evaluate_risk(request: RiskRequest):
    """
    Emergency MVP Risk Engine.
    Combines forecast and feasibility into a top-level risk score.
    """
    logger.info("Risk request for %s→%s", request.origin, request.destination)
    try:
        response = RiskService.evaluate_risk(request)
        return response
    except Exception as e:
        logger.error("Risk error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Risk engine failed: {e}")

# ─── Optimization ────────────────────────────────────────────────────────────

@app.post("/api/optimize", response_model=OptimizeResponse)
async def optimize_strategy(request: OptimizeRequest):
    """
    Emergency MVP Charter Strategy Optimization Engine.
    Combines forecast, feasibility, and risk to recommend a strategy.
    """
    logger.info("Optimization request for %s", request.cargo_quantity)
    try:
        response = OptimizeService.optimize(request)
        return response
    except ValueError as e:
        logger.warning("Optimization ValueError: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Optimization error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Optimization engine failed: {e}")


# ─── Scenario / Stress Test ──────────────────────────────────────────────────


@app.post("/api/scenario", response_model=ScenarioAnalysisResponse)
async def analyze_scenarios(request: OptimizeRequest):
    """
    Re-solve the charter decision under a set of stress cases and report whether
    the recommendation survives.

    Runs the base case plus freight-spike, freight-fall, high-congestion and
    preferred-vessel-unavailable scenarios through the same decision path, then
    reports which of them change the recommended structure.
    """
    logger.info(
        "Scenario analysis for %s->%s, qty=%s",
        request.origin,
        request.destination,
        request.cargo_quantity,
    )
    try:
        return ScenarioService.run(request)
    except ValueError as e:
        logger.warning("Scenario ValueError: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Scenario error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scenario engine failed: {e}")
