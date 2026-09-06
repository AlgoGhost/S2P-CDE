"""
VARUNEETI Charter Optimization Service (Emergency MVP)
======================================================
Combines Forecast, Feasibility, and Risk to provide a simple, reliable decision.
"""
import math
import logging
from backend.schemas import (
    OptimizeRequest, OptimizeResponse, StrategyComparison, 
    RecommendationDetails, FeasibilityRequest, ForecastRequest, FeasibilityStatus
)
from backend.services.forecast_service import ForecastService
from backend.services.vessel_service import VesselService

logger = logging.getLogger(__name__)

class OptimizeService:
    # PROTOTYPE ASSUMPTIONS
    SPOT_MULTIPLIER = 1.00
    SHORT_TERM_MULTIPLIER = 0.98
    MEDIUM_TERM_MULTIPLIER = 0.95
    HYBRID_MULTIPLIER = 0.97
    
    @classmethod
    def optimize(cls, request: OptimizeRequest) -> OptimizeResponse:
        drivers = []
        assumptions = [
            "Cost multipliers (Spot=1.0, Short=0.98, Medium=0.95, Hybrid=0.97) are prototype assumptions.",
            "Risk score is a synthesized proxy for MVP demonstration."
        ]
        
        # 1. FORECAST
        try:
            forecast_data = ForecastService.forecast(
                origin=request.origin,
                destination=request.destination,
                vessel_type="Panamax", # Generic check for trend
                horizon_days=30
            )
            trend = forecast_data.trend
            volatility = forecast_data.volatility
            freight_base = forecast_data.forecast
        except Exception as e:
            raise ValueError(f"Failed to get forecast: {e}")

        # 2. FEASIBILITY
        v_req = FeasibilityRequest(
            origin=request.origin,
            destination=request.destination,
            cargo_quantity=request.cargo_quantity,
            parcel_quantity=request.parcel_quantity
        )
        feas_data = VesselService.evaluate_feasibility(v_req)
        
        if not feas_data.recommended_vessel:
            return OptimizeResponse(
                status="infeasible",
                recommendation=RecommendationDetails(
                    strategy="NONE", vessel_class="NONE", locked_tonnage=0, flexible_tonnage=0,
                    lock_percentage=0, expected_cost=0, cost_per_tonne=0, risk_score=100
                ),
                strategy_comparison=[],
                voyages=0,
                decision_drivers=["No feasible vessel found."],
                assumptions=assumptions,
                data_status={"status": "infeasible"}
            )
            
        vessel = feas_data.recommended_vessel
        voyages = vessel.voyages_required
        
        # Operational base cost from feasibility
        ops_cost = vessel.total_operational_cost
        
        # 3. RISK (Using the new RiskService)
        from backend.services.risk_service import RiskService
        from backend.schemas import RiskRequest
        
        r_req = RiskRequest(
            origin=request.origin,
            destination=request.destination,
            cargo_quantity=request.cargo_quantity,
            parcel_quantity=request.parcel_quantity,
            delivery_start=request.delivery_start,
            delivery_end=request.delivery_end
        )
        try:
            risk_data = RiskService.evaluate_risk(r_req)
            risk_score = risk_data.overall_score
            drivers.extend([f"Risk Driver: {d.explanation}" for d in risk_data.top_drivers])
        except Exception as e:
            logger.warning(f"Failed to calculate risk, defaulting to 50. Error: {e}")
            risk_score = 50.0
        
        # Base expected freight cost for total cargo
        total_freight_cost = freight_base * request.cargo_quantity
        
        # 4. STRATEGY CALCULATION
        # SPOT
        spot_cost = (total_freight_cost + ops_cost) * cls.SPOT_MULTIPLIER
        
        # SHORT TERM
        short_cost = (total_freight_cost + ops_cost) * cls.SHORT_TERM_MULTIPLIER
        # Add risk penalty for short term if risk is high
        if risk_score > 60:
            short_cost *= 1.05
            
        # MEDIUM TERM
        medium_cost = (total_freight_cost + ops_cost) * cls.MEDIUM_TERM_MULTIPLIER
        if risk_score > 40:
            medium_cost *= 1.10 # High penalty for long lock when risk is moderate/high
            
        # HYBRID
        hybrid_cost = (total_freight_cost + ops_cost) * cls.HYBRID_MULTIPLIER
        
        strats = [
            StrategyComparison(strategy="SPOT", cost=spot_cost, cost_per_tonne=spot_cost/request.cargo_quantity, lock_percentage=0, locked_tonnage=0, flexible_tonnage=request.cargo_quantity),
            StrategyComparison(strategy="SHORT_TERM", cost=short_cost, cost_per_tonne=short_cost/request.cargo_quantity, lock_percentage=100, locked_tonnage=request.cargo_quantity, flexible_tonnage=0),
            StrategyComparison(strategy="MEDIUM_TERM", cost=medium_cost, cost_per_tonne=medium_cost/request.cargo_quantity, lock_percentage=100, locked_tonnage=request.cargo_quantity, flexible_tonnage=0),
            StrategyComparison(strategy="HYBRID", cost=hybrid_cost, cost_per_tonne=hybrid_cost/request.cargo_quantity, lock_percentage=60, locked_tonnage=request.cargo_quantity*0.6, flexible_tonnage=request.cargo_quantity*0.4),
        ]
        
        # Select best strategy
        best_strat = min(strats, key=lambda x: x.cost)
        
        # Build drivers
        drivers.append(f"Forecast trend is {trend} with {volatility} volatility.")
        drivers.append(f"Vessel selected: {vessel.vessel_type} (Feasibility: {vessel.status.value}).")
        drivers.append(f"Risk score evaluated at {risk_score:.1f}/100.")
        
        if best_strat.strategy == "MEDIUM_TERM":
            drivers.append("Medium-term selected because market risk is low and cost multiplier is favorable.")
        elif best_strat.strategy == "SPOT":
            drivers.append("Spot selected to retain flexibility amidst higher market or operational risk.")
        elif best_strat.strategy == "HYBRID":
            drivers.append("Hybrid selected to balance risk and expected cost efficiency.")
        elif best_strat.strategy == "SHORT_TERM":
            drivers.append("Short-term selected as a balanced approach.")
            
        rec = RecommendationDetails(
            strategy=best_strat.strategy,
            vessel_class=vessel.vessel_type,
            locked_tonnage=best_strat.locked_tonnage,
            flexible_tonnage=best_strat.flexible_tonnage,
            lock_percentage=best_strat.lock_percentage,
            expected_cost=round(best_strat.cost, 2),
            cost_per_tonne=round(best_strat.cost_per_tonne, 2),
            risk_score=risk_score
        )
        
        return OptimizeResponse(
            status="optimal",
            recommendation=rec,
            strategy_comparison=strats,
            voyages=voyages,
            decision_drivers=drivers,
            assumptions=assumptions,
            data_status={"prototype": True}
        )
