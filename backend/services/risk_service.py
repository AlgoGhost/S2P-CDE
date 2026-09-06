"""
VARUNEETI Risk Service (Emergency MVP)
======================================
Minimum viable risk engine for the end-to-end demo.
"""

import logging
from backend.schemas import (
    RiskRequest, RiskResponse, RiskDriver, 
    ForecastRequest, FeasibilityRequest, FeasibilityStatus
)
from backend.services.forecast_service import ForecastService
from backend.services.vessel_service import VesselService

logger = logging.getLogger(__name__)

class RiskService:
    # Prototype Weights
    WEIGHTS = {
        "freight_volatility": 0.25,
        "port_congestion": 0.20,
        "vessel_availability": 0.15,
        "weather": 0.15,
        "delivery_pressure": 0.15,
        "operational": 0.10
    }
    
    @classmethod
    def evaluate_risk(cls, request: RiskRequest) -> RiskResponse:
        assumptions = [
            "Weights are centralized prototype assumptions.",
            "Weather and Congestion risks are simulated proxies."
        ]
        
        # 1. FORECAST
        try:
            forecast_data = ForecastService.forecast(
                origin=request.origin,
                destination=request.destination,
                vessel_type="Panamax", # Generic check for trend
                horizon_days=30
            )
            volatility = forecast_data.volatility.value
        except Exception as e:
            # Fallback if no forecast available
            volatility = "MEDIUM"

        # 2. FEASIBILITY
        v_req = FeasibilityRequest(
            origin=request.origin,
            destination=request.destination,
            cargo_quantity=request.cargo_quantity,
            parcel_quantity=request.parcel_quantity
        )
        feas_data = VesselService.evaluate_feasibility(v_req)
        
        vessel = feas_data.recommended_vessel
        
        # Calculate Risk Factors (0-100)
        factors = {}
        
        # A. Freight Volatility
        if volatility == "HIGH":
            f_score = 85.0
            f_exp = "Forecast indicates high historical and projected volatility."
        elif volatility == "LOW":
            f_score = 15.0
            f_exp = "Forecast volatility is low."
        else:
            f_score = 50.0
            f_exp = "Forecast volatility is moderate."
        factors["freight_volatility"] = (f_score, f_exp)
            
        # B. Port Congestion (Proxy)
        congestion_index = feas_data.port.get("congestion_index", 1.0)
        c_score = min(100.0, (congestion_index - 1.0) * 200.0)
        factors["port_congestion"] = (c_score, f"Port congestion index is {congestion_index}.")
        
        # C. Vessel Availability (Proxy based on alternatives)
        alt_count = len(feas_data.alternatives)
        if alt_count == 0:
            v_score = 90.0
            v_exp = "No alternative feasible vessel classes available."
        elif alt_count == 1:
            v_score = 50.0
            v_exp = "Limited alternative vessels available."
        else:
            v_score = 20.0
            v_exp = "Multiple feasible vessel alternatives exist."
        factors["vessel_availability"] = (v_score, v_exp)
            
        # D. Weather (Static Proxy)
        # Simply assigning a baseline risk for demonstration
        w_score = 40.0
        factors["weather"] = (w_score, "Baseline seasonal weather risk proxy applied.")
        
        # E. Delivery Pressure (Proxy based on window)
        # Delivery window length is a string comparison proxy here
        # E.g., if end - start is short. In a real system, use datetime parsing.
        d_score = 50.0
        factors["delivery_pressure"] = (d_score, "Moderate delivery slack assumed.")
        
        # F. Operational
        if vessel and vessel.status == FeasibilityStatus.CONDITIONALLY_FEASIBLE:
            o_score = 80.0
            o_exp = "Lightering or operational alternative required."
        elif vessel:
            o_score = 20.0
            o_exp = "Direct discharge feasible."
        else:
            o_score = 100.0
            o_exp = "No feasible operational plan."
        factors["operational"] = (o_score, o_exp)
        
        # Aggregate
        drivers = []
        overall = 0.0
        
        for name, (score, exp) in factors.items():
            weight = cls.WEIGHTS[name]
            contribution = score * weight
            overall += contribution
            
            severity = "HIGH" if score > 60 else "MEDIUM" if score > 30 else "LOW"
            
            drivers.append(RiskDriver(
                factor=name,
                score=score,
                weight=weight,
                contribution=round(contribution, 2),
                severity=severity,
                explanation=exp
            ))
            
        # Sort by contribution
        drivers.sort(key=lambda x: x.contribution, reverse=True)
        
        overall_score = min(100.0, max(0.0, overall))
        risk_level = "HIGH" if overall_score > 60 else "MEDIUM" if overall_score > 30 else "LOW"
        
        return RiskResponse(
            overall_score=round(overall_score, 1),
            risk_level=risk_level,
            top_drivers=drivers[:3],
            all_drivers=drivers,
            assumptions=assumptions
        )
