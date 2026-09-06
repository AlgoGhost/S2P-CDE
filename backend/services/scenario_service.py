"""
VARUNEETI Scenario / Stress-Test Service
========================================

Answers the question a forecast alone cannot: **does the recommendation survive
if the forecast is wrong?**

Each scenario re-runs the *same* decision path (`OptimizeService.optimize`) with
a shock applied to its inputs. No cost or feasibility logic is reimplemented
here — this module only defines the shocks, invokes the existing engines, and
compares the outcomes against the base case.

Scenario shock magnitudes are **prototype assumptions**, not calibrated
probabilities derived from market data. They are reported as such.
"""

from __future__ import annotations

import logging

from backend.schemas import (
    OptimizeRequest,
    ScenarioAnalysisResponse,
    ScenarioDefinition,
    ScenarioOutcome,
)
from backend.services.optimize_service import OptimizeService

logger = logging.getLogger(__name__)


class ScenarioService:
    BASE_ID = "BASE"

    # Shock magnitudes are stated assumptions for the prototype. They are NOT
    # fitted to observed market moves and carry no probability weighting.
    SCENARIOS: list[ScenarioDefinition] = [
        ScenarioDefinition(
            scenario_id="BASE",
            label="Base Case",
            notes="Unshocked decision using the model's own forecast.",
        ),
        ScenarioDefinition(
            scenario_id="HIGH_FREIGHT",
            label="Freight Spike +25%",
            freight_multiplier=1.25,
            notes="Freight settles 25% above the point forecast.",
        ),
        ScenarioDefinition(
            scenario_id="LOW_FREIGHT",
            label="Freight Fall -20%",
            freight_multiplier=0.80,
            notes="Freight settles 20% below the point forecast.",
        ),
        ScenarioDefinition(
            scenario_id="HIGH_CONGESTION",
            label="Port Congestion +40%",
            congestion_multiplier=1.40,
            notes="Discharge port congestion worsens by 40%, extending port time.",
        ),
        ScenarioDefinition(
            scenario_id="LOW_AVAILABILITY",
            label="Preferred Vessel Unavailable",
            notes="The recommended vessel class cannot be fixed in the window.",
        ),
    ]

    @classmethod
    def run(cls, request: OptimizeRequest) -> ScenarioAnalysisResponse:
        # ── Base case first: later scenarios are measured against it ──
        base = OptimizeService.optimize(request)
        base_rec = base.recommendation
        base_cost = base_rec.expected_cost

        outcomes: list[ScenarioOutcome] = []

        for spec in cls.SCENARIOS:
            if spec.scenario_id == cls.BASE_ID:
                result, notes = base, spec.notes
            else:
                excluded = tuple(spec.excluded_vessel_types)
                notes = spec.notes

                # LOW_AVAILABILITY is defined relative to the base outcome:
                # remove whichever class the base case actually chose.
                if spec.scenario_id == "LOW_AVAILABILITY":
                    excluded = (base_rec.vessel_class,)
                    notes = (
                        f"{base_rec.vessel_class} cannot be fixed in the delivery "
                        f"window; the fleet is re-evaluated without it."
                    )

                try:
                    result = OptimizeService.optimize(
                        request,
                        freight_multiplier=spec.freight_multiplier,
                        congestion_multiplier=spec.congestion_multiplier,
                        excluded_vessel_types=excluded,
                    )
                except Exception as exc:
                    # A scenario that cannot be solved is itself a finding —
                    # surface it rather than dropping the row.
                    logger.warning("Scenario %s failed: %s", spec.scenario_id, exc)
                    outcomes.append(
                        ScenarioOutcome(
                            scenario_id=spec.scenario_id,
                            label=spec.label,
                            status="error",
                            strategy="NONE",
                            vessel_class="NONE",
                            voyages=0,
                            lock_percentage=0.0,
                            expected_cost=0.0,
                            cost_per_tonne=0.0,
                            risk_score=100.0,
                            cost_delta_vs_base=0.0,
                            cost_pct_delta_vs_base=0.0,
                            strategy_changed=True,
                            vessel_changed=True,
                            notes=f"Scenario could not be solved: {exc}",
                        )
                    )
                    continue

            rec = result.recommendation
            delta = rec.expected_cost - base_cost
            pct = (delta / base_cost * 100.0) if base_cost else 0.0

            # An infeasible scenario has no comparable strategy/vessel.
            infeasible = result.status != "optimal"

            outcomes.append(
                ScenarioOutcome(
                    scenario_id=spec.scenario_id,
                    label=spec.label,
                    status=result.status,
                    strategy=rec.strategy,
                    vessel_class=rec.vessel_class,
                    voyages=result.voyages,
                    lock_percentage=rec.lock_percentage,
                    expected_cost=round(rec.expected_cost, 2),
                    cost_per_tonne=round(rec.cost_per_tonne, 2),
                    risk_score=rec.risk_score,
                    cost_delta_vs_base=round(delta, 2),
                    cost_pct_delta_vs_base=round(pct, 2),
                    strategy_changed=(
                        spec.scenario_id != cls.BASE_ID
                        and rec.strategy != base_rec.strategy
                    ),
                    vessel_changed=(
                        spec.scenario_id != cls.BASE_ID
                        and rec.vessel_class != base_rec.vessel_class
                    ),
                    notes=(
                        f"{notes} No feasible plan under this scenario."
                        if infeasible
                        else notes
                    ),
                )
            )

        # ── Robustness verdict ──
        flipped = [o for o in outcomes if o.strategy_changed]
        solved = [o for o in outcomes if o.status == "optimal"]
        worst = max(solved, key=lambda o: o.cost_delta_vs_base, default=None)

        robust = len(flipped) == 0
        if robust:
            summary = (
                f"{base_rec.strategy} remains the recommended structure under all "
                f"{len(outcomes) - 1} stress cases. Expected cost moves between "
                f"{min(o.cost_pct_delta_vs_base for o in solved):+.1f}% and "
                f"{max(o.cost_pct_delta_vs_base for o in solved):+.1f}%."
            )
        else:
            names = ", ".join(f"{o.label} -> {o.strategy}" for o in flipped)
            summary = (
                f"The recommendation is NOT robust: {len(flipped)} of "
                f"{len(outcomes) - 1} stress cases change the structure ({names}). "
                f"Treat {base_rec.strategy} as conditional on the base forecast holding."
            )

        return ScenarioAnalysisResponse(
            base_scenario_id=cls.BASE_ID,
            outcomes=outcomes,
            recommendation_is_robust=robust,
            robustness_summary=summary,
            worst_case_scenario_id=(
                worst.scenario_id if worst and worst.scenario_id != cls.BASE_ID else None
            ),
            assumptions=[
                "Scenario shock magnitudes are prototype assumptions, not calibrated "
                "probabilities or fitted market moves.",
                "Each scenario re-runs the full forecast/feasibility/risk/strategy path; "
                "no cost logic is duplicated in the scenario engine.",
                "Scenarios are not probability-weighted - they are independent stress "
                "cases, so their costs must not be averaged into an expected value.",
            ]
            + list(base.assumptions),
            data_status=base.data_status,
        )
