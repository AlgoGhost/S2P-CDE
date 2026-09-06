# VARUNEETI — IMPLEMENTATION STATUS

**SIH 2026 · PS26006 · Ministry of Steel / SAIL**
Last verified: 2026-09-06 · 100 tests passing · golden demo verified in-browser

This file is the **source of truth** for what is built. Where it disagrees with
`VARUNEETI_MASTER_BUILD_BLUEPRINT.pdf`, this file is correct — the blueprint
describes a target architecture that was never implemented (see
`docs/CURRENT_STATE_AUDIT.md` §0).

---

## Implemented and verified

| Capability | Where | Verified by |
|---|---|---|
| Freight forecasting: SARIMAX → moving average → naive fallback, walk-forward validation, 95% prediction interval, trend/volatility/confidence | `backend/engines/forecasting.py`, `services/forecast_service.py` | `test_forecasting.py`, `test_api.py` |
| No look-ahead leakage; model compared against a naive baseline on MAE | same | `test_forecasting.py` |
| Vessel–port feasibility: draft, LOA, beam and parcel-capacity constraints with explicit pass/fail reason codes | `backend/engines/vessel_port.py`, `services/vessel_service.py` | `test_feasibility.py`, `test_api.py` |
| Lightering evaluation with capacity limit, incremental cost and days | `backend/engines/vessel_port.py` | `test_feasibility.py` |
| Risk scoring: 6 weighted factors → composite 0–100 with severity and per-driver contribution | `backend/services/risk_service.py` | `test_risk.py`, `test_api.py` |
| Delivery-window pressure computed from the requested window vs. modelled port time | `backend/services/risk_service.py` | `test_api.py` |
| Charter structure comparison: SPOT / SHORT_TERM / MEDIUM_TERM / HYBRID on one cost basis | `backend/services/optimize_service.py` | `test_optimize.py`, `test_api.py` |
| Recommendation provably derived from the comparison, not hardcoded | same | `test_api.py::test_optimize_recommendation_is_the_cheapest_compared_option` |
| **Scenario stress testing**: 5 cases re-solve the full decision; reports whether the recommendation flips | `backend/services/scenario_service.py` | `test_scenario.py` (13 tests) |
| FastAPI service, 7 endpoints, typed contracts, no business logic in routes | `backend/main.py`, `schemas.py` | `test_api.py` |
| React decision cockpit, 11 sections | `frontend/src/**` | `frontend/scripts/verify-demo.mjs` |
| Deterministic and reproducible for fixed input | — | `test_scenario.py::test_deterministic_for_fixed_input` |
| Runs fully offline | — | no network calls in any engine |

### API

```
GET  /api/health        service status
GET  /api/lanes         24 lanes with observation counts
POST /api/forecast      freight forecast + prediction interval
POST /api/feasibility   vessel-port constraint evaluation
POST /api/risk          6-factor composite risk
POST /api/optimize      charter structure comparison + recommendation
POST /api/scenario      stress test: re-solve under 5 shock cases
```

---

## Implemented with stated limitations

| Item | Limitation | Disclosed where |
|---|---|---|
| Charter structure costs | Multipliers (SPOT 1.00 / SHORT 0.98 / MEDIUM 0.95 / HYBRID 0.97) are **prototype assumptions**, not observed market spreads | `OptimizeResponse.assumptions`, cockpit callout |
| Scenario shocks | Magnitudes are **stated assumptions**, not calibrated probabilities; cases are **not probability-weighted** | `ScenarioAnalysisResponse.assumptions`, cockpit callout |
| Delivery pressure | Compares the window against **port time only** — voyage sailing time is not modelled (the dataset has no route distances), so it understates true pressure | `RiskResponse.assumptions` |
| Seasonal risk | Calendar proxy for Bay of Bengal cyclone season and SW monsoon; **not a meteorological forecast** | `RiskResponse.assumptions` |
| Port congestion | Proxy derived from the port-master congestion index | `RiskResponse.assumptions` |
| Hybrid lock split | Fixed at 60% — not optimised | `OptimizeResponse.assumptions` |
| Demurrage | Threshold (1.5× handling time) is not reached at any port in the dataset, so it evaluates to 0 | `docs/CURRENT_STATE_AUDIT.md` B-5 |
| Voyage schedule dates | Cockpit spreads voyages evenly across the window; **voyage-level scheduling is not modelled** | cockpit callout, labelled "indicative" |
| Forecast resolution | Prototype series is monthly, so a 30-day horizon yields one projected period | cockpit callout |
| All data | Generated prototype/proxy dataset — no SAIL data, no Baltic Exchange data, no licensed feed | `README.md`, cockpit footer, `data_source: prototype_proxy` |

---

## NOT implemented

| Item | Status |
|---|---|
| **PuLP / MILP optimizer** | **Not implemented.** `optimize_service.py` is a cost comparison over four structures — no decision variables, no constraints, no solver. Must not be described as a MILP. |
| Streamlit UI | Not implemented — deliberately replaced by the React cockpit. |
| LightGBM / quantile models | Not implemented. Baseline + SARIMAX only. |
| `POST /api/v1/decision` single orchestration endpoint | Not implemented; the cockpit composes four endpoints. |
| Vessel availability windows | `vessels.csv` has no `available_from`/`available_to`; no laycan overlap check. |
| Explanation as a separate module | Decision drivers are generated inside `optimize_service.py`. |
| PostgreSQL, Docker, CI | Not implemented. |
| `backend/app/**` tree from the blueprint | Not implemented; see `docs/CURRENT_STATE_AUDIT.md` §0. |

---

## Test coverage

```
backend/tests/test_forecasting.py    forecast engine, bounds, leakage
backend/tests/test_feasibility.py    constraint boundaries, lightering
backend/tests/test_risk.py           composite scoring, driver ordering
backend/tests/test_optimize.py       strategy costing, recommendation
backend/tests/test_scenario.py       shocks move real numbers; robustness verdict
backend/tests/test_api.py            all 7 endpoints, validation, edge cases

100 passed in ~75 s, fully offline (FastAPI TestClient — no server required)
```
