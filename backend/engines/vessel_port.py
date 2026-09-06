"""
VARUNEETI Vessel-Port Feasibility Engine
==========================================

Evaluates physical and operational feasibility for a given cargo requirement
and route against vessel and port constraints.

Determines:
- DIRECT_FEASIBLE
- CONDITIONALLY_FEASIBLE (e.g. lightering)
- INFEASIBLE

Calculates normalized operational parameters and costs.
"""

from __future__ import annotations
import math

from backend.schemas import FeasibilityStatus, LighteringDetails, VesselCandidate


def evaluate_vessel_candidate(
    vessel: dict,
    port: dict,
    cargo_quantity: float,
    parcel_quantity: float | None = None,
) -> VesselCandidate:
    """
    Evaluate a vessel against port constraints and calculate operational estimates.
    """
    passed = []
    failed = []
    
    # Extract properties
    v_type = vessel["vessel_type"]
    v_cap = vessel["cargo_capacity"]
    v_draft = vessel["draft"]
    v_loa = vessel["loa"]
    v_beam = vessel["beam"]
    v_daily_cost = vessel["daily_cost"]

    p_draft = port["max_draft"]
    p_loa = port["max_loa"]
    p_beam = port["max_beam"]
    p_rate = port["cargo_handling_rate"]
    p_congestion = port["congestion_index"]
    
    # ─── Parcelization Logic ───
    # If a parcel_quantity is not specified or is greater than the vessel's capacity,
    # we limit it to the vessel's capacity.
    parcel_cap = min(parcel_quantity, v_cap) if parcel_quantity else v_cap
    voyages_req = math.ceil(cargo_quantity / parcel_cap)

    # ─── Hard Constraints ───
    if parcel_cap <= v_cap:
        passed.append("capacity")
    else:
        # Actually this won't happen due to min() above unless user strictly enforces oversized parcel
        pass
    
    if v_draft <= p_draft:
        passed.append("draft")
    else:
        failed.append("draft")

    if v_loa <= p_loa:
        passed.append("loa")
    else:
        failed.append("loa")

    if v_beam <= p_beam:
        passed.append("beam")
    else:
        failed.append("beam")

    # ─── Lightering Evaluation ───
    lightering = None
    direct_feasible = len(failed) == 0
    conditional_feasible = False
    status = FeasibilityStatus.DIRECT_FEASIBLE

    if not direct_feasible:
        # Is lightering available and only draft failed?
        if port.get("lightering_available", False) and failed == ["draft"]:
            light_cap = port.get("lightering_capacity", 0)
            excess_draft = v_draft - p_draft
            
            # Simple assumption: 1m draft ~ roughly 10,000t to 15,000t depending on vessel
            # For simplicity, calculate lightered amount as proportion of capacity
            proportion_to_lighter = excess_draft / v_draft
            est_lighter_qty = proportion_to_lighter * v_cap

            if est_lighter_qty <= light_cap:
                # Lightering is viable
                conditional_feasible = True
                status = FeasibilityStatus.CONDITIONALLY_FEASIBLE
                passed.append("lightering_draft")
                failed.remove("draft")
                
                l_cost = port.get("lightering_cost_per_tonne", 0) * est_lighter_qty
                l_days = est_lighter_qty / (p_rate * 0.5) # lightering is slower
                
                lightering = LighteringDetails(
                    required=True,
                    lightering_quantity=round(est_lighter_qty, 2),
                    incremental_cost=round(l_cost, 2),
                    incremental_days=round(l_days, 2),
                    operational_risk="MEDIUM"
                )
            else:
                status = FeasibilityStatus.INFEASIBLE
                failed.append("lightering_capacity_exceeded")
        else:
            status = FeasibilityStatus.INFEASIBLE

    # ─── Fit Score Calculation ───
    fit_reasons = []
    fit_score = 100.0

    if status == FeasibilityStatus.INFEASIBLE:
        fit_score = 0.0
        fit_reasons.append(f"Infeasible due to {', '.join(failed)}")
    else:
        # Utilization
        utilization = parcel_cap / v_cap
        if utilization < 0.8:
            fit_score -= (0.8 - utilization) * 100  # Penalty for unused space
            fit_reasons.append(f"Low capacity utilization ({utilization:.0%})")
        else:
            fit_reasons.append(f"Good capacity utilization ({utilization:.0%})")

        # Headroom evaluation
        if v_draft >= p_draft - 0.5 and direct_feasible:
            fit_score -= 10
            fit_reasons.append("Tight draft clearance")
        
        if v_loa >= p_loa - 10 and direct_feasible:
            fit_score -= 5
            fit_reasons.append("Tight LOA clearance")

        # Lightering penalty
        if status == FeasibilityStatus.CONDITIONALLY_FEASIBLE:
            fit_score -= 20
            fit_reasons.append("Requires lightering (added cost/risk)")
            
        fit_reasons.append(f"Capable of serving in {voyages_req} voyages")

    fit_score = max(0.0, min(100.0, fit_score))

    # ─── Port Time & Costs (Per Voyage) ───
    handling_days = parcel_cap / p_rate
    waiting_days = handling_days * (p_congestion - 1.0)
    
    lightering_cost_per_voyage = lightering.incremental_cost if lightering else 0.0
    lightering_days = lightering.incremental_days if lightering else 0.0

    total_port_time_per_voyage = handling_days + waiting_days + lightering_days
    
    port_cost_per_voyage = total_port_time_per_voyage * port.get("waiting_cost_per_day", 10000)
    
    # Demurrage estimate (simple assumption for prototype)
    excess_wait = max(0, total_port_time_per_voyage - (handling_days * 1.5))
    demurrage_per_voyage = excess_wait * (v_daily_cost * 0.5)

    total_ops_cost = (port_cost_per_voyage + demurrage_per_voyage + lightering_cost_per_voyage) * voyages_req

    return VesselCandidate(
        vessel_type=v_type,
        capacity=v_cap,
        draft=v_draft,
        loa=v_loa,
        beam=v_beam,
        parcel_capacity=parcel_cap,
        voyages_required=voyages_req,
        direct_feasible=direct_feasible,
        conditional_feasible=conditional_feasible,
        status=status,
        fit_score=round(fit_score, 2),
        fit_reasons=fit_reasons,
        passed_constraints=passed,
        failed_constraints=failed,
        handling_days=round(handling_days * voyages_req, 2),
        waiting_days=round(waiting_days * voyages_req, 2),
        port_time_days=round(total_port_time_per_voyage * voyages_req, 2),
        port_cost=round(port_cost_per_voyage * voyages_req, 2),
        demurrage_exposure=round(demurrage_per_voyage * voyages_req, 2),
        lightering_cost=round(lightering_cost_per_voyage * voyages_req, 2),
        total_operational_cost=round(total_ops_cost, 2),
        lightering=lightering
    )
