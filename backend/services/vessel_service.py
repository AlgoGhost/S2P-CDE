"""
VARUNEETI Vessel Service
==========================

Orchestrates the vessel-port feasibility evaluation.
Loads data, filters based on request, and ranks the candidates.
"""

import logging
import pandas as pd
from pathlib import Path
from backend.config import DATA_DIR
from backend.schemas import FeasibilityRequest, FeasibilityResponse, FeasibilityStatus, VesselCandidate
from backend.engines.vessel_port import evaluate_vessel_candidate

logger = logging.getLogger(__name__)

class VesselService:
    _vessels_df = None
    _ports_df = None

    @classmethod
    def _load_data(cls):
        if cls._vessels_df is None:
            cls._vessels_df = pd.read_csv(DATA_DIR / "vessels.csv")
        if cls._ports_df is None:
            cls._ports_df = pd.read_csv(DATA_DIR / "ports.csv")

    @classmethod
    def evaluate_feasibility(
        cls,
        request: FeasibilityRequest,
        congestion_multiplier: float = 1.0,
        excluded_vessel_types: tuple[str, ...] | None = None,
    ) -> FeasibilityResponse:
        """
        Evaluate every vessel class against the destination port.

        `congestion_multiplier` and `excluded_vessel_types` exist so the scenario
        engine can re-run this same evaluation under a shock without any of the
        feasibility logic being duplicated elsewhere. Defaults reproduce the
        unshocked base case exactly.
        """
        cls._load_data()
        
        # ─── Find Port ───
        port_match = cls._ports_df[cls._ports_df['port'].str.lower() == request.destination.lower()]
        if port_match.empty:
            raise ValueError(f"Unknown destination port: {request.destination}")
        port_dict = port_match.iloc[0].to_dict()

        if congestion_multiplier != 1.0:
            port_dict = dict(port_dict)
            port_dict["congestion_index"] = round(
                port_dict["congestion_index"] * congestion_multiplier, 4
            )

        excluded = {v.lower() for v in (excluded_vessel_types or ())}

        candidates = []
        # ─── Evaluate all vessels ───
        for _, vessel_row in cls._vessels_df.iterrows():
            v_dict = vessel_row.to_dict()
            if v_dict["vessel_type"].lower() in excluded:
                continue
            candidate = evaluate_vessel_candidate(
                vessel=v_dict,
                port=port_dict,
                cargo_quantity=request.cargo_quantity,
                parcel_quantity=request.parcel_quantity
            )
            candidates.append(candidate)

        # ─── Rank Candidates ───
        # Prefer DIRECT_FEASIBLE over CONDITIONALLY_FEASIBLE
        # Then sort by fit_score (desc) and operational cost (asc)
        
        def rank_key(c: VesselCandidate):
            status_rank = 0 if c.status == FeasibilityStatus.DIRECT_FEASIBLE else \
                          1 if c.status == FeasibilityStatus.CONDITIONALLY_FEASIBLE else 2
            
            return (status_rank, -c.fit_score, c.total_operational_cost)

        candidates.sort(key=rank_key)

        recommended = None
        alternatives = []
        if candidates and candidates[0].status != FeasibilityStatus.INFEASIBLE:
            recommended = candidates[0]
            alternatives = [c for c in candidates[1:] if c.status != FeasibilityStatus.INFEASIBLE]

        assumptions = [
            "Data source marked as 'prototype_assumption'",
            "Lightering ratio based on draft exceedance approximation",
            "Port waiting costs and handling rates are synthetic baselines"
        ]

        return FeasibilityResponse(
            origin=request.origin,
            destination=request.destination,
            cargo_quantity=request.cargo_quantity,
            parcel_quantity=request.parcel_quantity,
            loading_port=request.loading_port,
            port=port_dict,
            vessels=candidates,
            recommended_vessel=recommended,
            alternatives=alternatives,
            assumptions=assumptions
        )
