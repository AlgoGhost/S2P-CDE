"""
VARUNEETI Risk Service (Emergency MVP)
======================================
Minimum viable risk engine for the end-to-end demo.
"""

import logging
from datetime import date, datetime

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
    def evaluate_risk(
        cls,
        request: RiskRequest,
        congestion_multiplier: float = 1.0,
        excluded_vessel_types: tuple[str, ...] | None = None,
    ) -> RiskResponse:
        assumptions = [
            "Factor weights are centralized prototype assumptions, not calibrated values.",
            "Port congestion is a proxy derived from the port master congestion index.",
            "Delivery pressure compares the requested window against the port time the "
            "feasibility engine computes for the selected vessel. Voyage sailing time is "
            "NOT modelled - the prototype dataset carries no route distances - so this "
            "understates true schedule pressure.",
            "Seasonal risk is a calendar proxy for Bay of Bengal cyclone season and the "
            "southwest monsoon. It is not a meteorological forecast.",
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
        feas_data = VesselService.evaluate_feasibility(
            v_req,
            congestion_multiplier=congestion_multiplier,
            excluded_vessel_types=excluded_vessel_types,
        )
        
        vessel = feas_data.recommended_vessel

        window_start = cls._parse_date(request.delivery_start)
        window_end = cls._parse_date(request.delivery_end)
        
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
            
        # D. Seasonal / Weather exposure, derived from the requested delivery months.
        w_score, w_exp = cls._score_weather(window_start, window_end)
        factors["weather"] = (w_score, w_exp)

        # E. Delivery Pressure: does the requested window absorb the port time the
        #    feasibility engine actually computed for the selected vessel?
        d_score, d_exp = cls._score_delivery_pressure(window_start, window_end, vessel)
        factors["delivery_pressure"] = (d_score, d_exp)
        
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


    # ─── Factor helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _parse_date(value) -> date | None:
        """Accept an ISO date string or a date; return None if unparseable."""
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if not value:
            return None
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            logger.warning("Unparseable delivery date: %r", value)
            return None

    # Bay of Bengal calendar proxy. Peak cyclone activity on India's East Coast
    # falls in Oct-Dec (post-monsoon) with a secondary Apr-May peak; the
    # southwest monsoon runs Jun-Sep. Stated as a modelling assumption, not a
    # weather forecast, and never presented as observed meteorological data.
    _CYCLONE_MONTHS = {10, 11, 12}
    _PRE_MONSOON_MONTHS = {4, 5}
    _MONSOON_MONTHS = {6, 7, 8, 9}

    @classmethod
    def _months_in_window(cls, start: date | None, end: date | None) -> list[int]:
        if not start or not end or end < start:
            return []
        months, y, m = [], start.year, start.month
        while (y, m) <= (end.year, end.month) and len(months) < 36:
            months.append(m)
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        return months

    @classmethod
    def _score_weather(cls, start: date | None, end: date | None) -> tuple[float, str]:
        months = cls._months_in_window(start, end)
        if not months:
            return 40.0, ("Delivery window unavailable; baseline seasonal risk proxy applied.")

        per_month = []
        for m in months:
            if m in cls._CYCLONE_MONTHS:
                per_month.append(70.0)
            elif m in cls._PRE_MONSOON_MONTHS:
                per_month.append(55.0)
            elif m in cls._MONSOON_MONTHS:
                per_month.append(50.0)
            else:
                per_month.append(25.0)

        score = round(sum(per_month) / len(per_month), 1)
        exposed = sorted({m for m in months if m in cls._CYCLONE_MONTHS})
        if exposed:
            names = ", ".join(date(2000, m, 1).strftime("%b") for m in exposed)
            exp = (
                f"Delivery window spans Bay of Bengal cyclone season ({names}); "
                f"seasonal calendar proxy, not a weather forecast."
            )
        elif any(m in cls._MONSOON_MONTHS for m in months):
            exp = "Delivery window overlaps the southwest monsoon; seasonal calendar proxy."
        else:
            exp = "Delivery window falls outside peak cyclone and monsoon periods."
        return score, exp

    @classmethod
    def _score_delivery_pressure(
        cls, start: date | None, end: date | None, vessel
    ) -> tuple[float, str]:
        """
        Schedule pressure = requested window vs. modelled port time.

        Port time comes from the feasibility engine (handling + waiting +
        lightering, summed across all required voyages). Sailing time is not
        modelled, so this is a lower bound on true pressure - stated in the
        response assumptions.
        """
        if not start or not end:
            return 50.0, "Delivery window could not be parsed; neutral pressure assumed."

        window_days = (end - start).days
        if window_days <= 0:
            return 100.0, (
                f"Delivery window is not positive ({start} to {end}); "
                f"no feasible schedule exists."
            )

        if vessel is None:
            return 100.0, "No feasible vessel, so no deliverable schedule exists."

        required_days = float(vessel.port_time_days or 0.0)
        slack_days = window_days - required_days
        slack_ratio = slack_days / window_days

        if slack_ratio < 0:
            score = 100.0
        elif slack_ratio < 0.1:
            score = 85.0
        elif slack_ratio < 0.3:
            score = 70.0
        elif slack_ratio < 0.5:
            score = 50.0
        elif slack_ratio < 0.7:
            score = 30.0
        else:
            score = 15.0

        if slack_ratio < 0:
            detail = (
                f"{window_days}-day window cannot absorb {required_days:.1f} days of "
                f"modelled port time across {vessel.voyages_required} voyages."
            )
        else:
            detail = (
                f"{window_days}-day window against {required_days:.1f} days of modelled "
                f"port time across {vessel.voyages_required} voyages "
                f"({slack_ratio:.0%} slack, sailing time excluded)."
            )
        return score, detail
