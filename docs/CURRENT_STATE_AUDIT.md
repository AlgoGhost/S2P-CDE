# VARUNEETI — CURRENT STATE AUDIT

**SIH 2026 · PS26006 · Ministry of Steel / SAIL**
Audit date: 2026-09-06. Execution flow traced, not judged by filenames.

---

## 0. HEADLINE: THE BLUEPRINT AND THE REPO ARE TWO DIFFERENT SYSTEMS

`VARUNEETI_MASTER_BUILD_BLUEPRINT.pdf` specifies `backend/app/{api,core,data,feasibility,
forecasting,models,optimization,risk,strategy,explanation,services}`, a **PuLP MILP**, a
**Streamlit** UI, `run_engine.py` and ~19 `docs/*.md`.

**Verified absent on disk:** `backend/app/`, `run_engine.py`, root `requirements.txt`,
`pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `frontend/streamlit_app.py`,
`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.github/`, `data/`,
`docs/{MASTER_BUILD_BLUEPRINT,MODULE_CONTRACTS,MATH_FORMULATION,IMPLEMENTATION_STATUS,00_START_HERE}.md`.
`pulp`, `streamlit`, `lightgbm` are absent from `backend/requirements.txt` and never imported.

What exists instead is a **different, working, end-to-end system**. The audit below covers
what is actually there.

**Decision taken:** keep the working architecture; close credibility gaps. Rebuilding to the
blueprint tree tonight would discard a verified demo and would not finish.

---

## 1. REAL PIPELINE (traced)

```
React cockpit (frontend/src/App.jsx)
   |  4 parallel/sequential HTTP calls -- there is no single decision endpoint
   v
FastAPI (backend/main.py)  /api/{health,lanes,forecast,feasibility,risk,optimize}
   v
ForecastService --> engines/forecasting.py   SARIMAX -> MovingAverage -> Naive
VesselService   --> engines/vessel_port.py   draft/LOA/beam + lightering
RiskService     --> 6 weighted factors (calls Forecast + Vessel internally)
OptimizeService --> calls Forecast + Vessel + Risk, applies 4 constants, min()
   v
OptimizeResponse (recommendation + strategy_comparison + decision_drivers)
```

**Integration note:** `OptimizeService` re-runs Forecast, Feasibility and Risk internally, and
the cockpit *also* calls those three endpoints directly. The same engines execute twice per
analysis (~6 s). Correct results, wasted work, and a latent risk of the panels disagreeing
with the recommendation if inputs ever diverge.

---

## 2. COMPONENT CLASSIFICATION

| Component | Status | Notes |
|---|---|---|
| Forecast engine (`engines/forecasting.py`, 643 L) | ✅ COMPLETE | SARIMAX→MA→naive fallback, walk-forward validation, 95% PI, no leakage. Beats naive (MAE 3.90 vs 4.69). |
| Forecast service | ✅ COMPLETE | Clean contract boundary. |
| Feasibility engine (`engines/vessel_port.py`) | ⭐ GOOD, IMPROVABLE | Draft/LOA/beam enforced with reason codes; lightering modelled. Capacity check is dead code; no availability window. |
| Vessel service | ✅ COMPLETE | Correct ranking: status → fit_score → cost. |
| Risk service | 🟡 PARTIAL | 4 of 6 factors real; `weather` and `delivery_pressure` are constants. |
| Optimize service | 🔴 CLAIM BROKEN | Not an optimizer. See §4 B-2. |
| Explanation | 🟡 PARTIAL | Inline f-strings inside `OptimizeService`, not a module. Leaks enum reprs. |
| Scenario engine | 🚧 MISSING | `ScenarioRequest` schema exists; no service, no endpoint. |
| FastAPI layer (`main.py`) | ✅ COMPLETE | 6 endpoints, CORS, typed, no business logic in routes. |
| Schemas (`schemas.py`, 285 L) | ⭐ GOOD | Strong contracts. `AnalyzeRequest`/`ScenarioRequest` are dead. |
| Prototype data | ✅ COMPLETE | 24 lanes × 56 obs; every row labelled `prototype_assumption`. |
| React cockpit (`frontend/src/**`) | ✅ COMPLETE | 10 sections, browser-verified, 0 console errors, 1366×768 + 1920×1080 clean. |
| Streamlit UI | 🚧 MISSING | Deliberately superseded by React. Blueprint should be updated, not the code. |
| Unit tests | ⭐ GOOD | 58 pass across forecasting/feasibility/risk/optimize. |
| `test_api_live.py` | 🔴 BROKEN | 8 failures on clean checkout. See §4 B-1. |
| MILP / PuLP | 🚧 MISSING | See §4 B-2. |

---

## 3. WHAT ACTUALLY WORKS (verified, not assumed)

- Golden case returns real engine output: **MEDIUM_TERM | Panamax | 4 voyages | $29.15/t | risk 35.0 MEDIUM**.
- Capesize correctly **INFEASIBLE** at Paradip on `draft, loa, beam` (18.0 m vs 14.5 m limit) — the core "cheapest ≠ usable" story is genuinely computed.
- Forecast genuinely drives cost: `freight_base × cargo_quantity` is the dominant cost term.
- Fresh clone runs (verified by cloning the pushed repo and executing the golden case).
- Fully offline — no network calls in any engine.

---

## 4. CRITICAL BUGS

**B-1 — `backend/tests/test_api_live.py`: 8 tests fail on a clean checkout.**
Hardcodes `BASE = "http://127.0.0.1:8000"` and requires a server it never starts.
Current suite: **58 passed, 8 failed**. Fails the "clean checkout / tests pass" bar.

**B-2 — The optimizer is not an optimizer (worst SIH exposure).**
`services/optimize_service.py` applies four constants (SPOT 1.00 / SHORT 0.98 / MEDIUM 0.95 /
HYBRID 0.97) to one cost base and takes `min()`. No decision variables, no constraints, no solver.
Because the multipliers are constant, **MEDIUM_TERM wins on every lane and every cargo size
whenever `risk_score <= 40`** — the "optimization" has exactly one branch. HYBRID's 60% lock is
hardcoded and never optimized. Calling this a MILP is indefensible under questioning.

**B-3 — Risk engine ignores the delivery window.**
`delivery_pressure = 50.0` and `weather = 40.0` are hardcoded; the source comment admits
*"In a real system, use datetime parsing."* `delivery_start`/`delivery_end` are accepted by the
API, threaded through `OptimizeService`, and **never read**. Changing a 3-month window to
3 days changes nothing. An evaluator who edits the dates will see an identical score.

**B-4 — Feasibility capacity constraint is dead code.**
`parcel_cap = min(parcel_quantity, v_cap)` executes *before* `if parcel_cap <= v_cap`, so the
branch is always true and the `else` unreachable. Requesting 75,000 t parcels silently gives
Handysize a 35,000 t parcel and 9 voyages instead of rejecting it.

**B-5 — Demurrage is structurally always zero.**
`excess_wait = max(0, total_port_time - handling_days * 1.5)`; with `congestion_index = 1.1`,
`total = 1.1 × handling < 1.5 × handling` → always 0. No port in `ports.csv` reaches 1.5
(max 1.4). The demurrage line can never carry information.

**B-6 — Enum reprs leak into the API.**
`optimize_service.py:127` emits `"Forecast trend is TrendDirection.STABLE with
VolatilityLevel.MEDIUM volatility."` Masked by the frontend; visible at `/docs` and to any
direct API consumer.

---

## 5. FAKE / PLACEHOLDER

| Item | Location | Reality |
|---|---|---|
| `weather` risk = 40.0 | `risk_service.py` | Constant. Labelled "proxy" in output — honest, but carries no signal. |
| `delivery_pressure` = 50.0 | `risk_service.py` | Constant. **Not** labelled as ignoring input — this one is misleading. |
| Strategy multipliers | `optimize_service.py` | Assumed constants. Declared in `assumptions[]` — honest. |
| HYBRID 60% lock | `optimize_service.py` | Hardcoded, never derived. |
| Demurrage | `vessel_port.py` | Always 0 (B-5). |
| `AnalyzeRequest`, `ScenarioRequest` | `schemas.py:137-152` | Dead contracts, zero references. |

No fabricated SAIL data, no invented port limits, no invented accuracy or savings claims were
found. Data provenance is labelled throughout.

---

## 6. WEAK ENGINEERING

1. Duplicate engine execution (§1) — same work done twice per analysis.
2. No single `/api/decision` orchestration endpoint; the client assembles the decision.
3. Explanation logic embedded in the optimizer instead of its own module.
4. No availability/laycan modelling anywhere (vessels have no `available_from/to`).
5. Deps only in `backend/requirements.txt`; no root install path.
6. Single `main` branch; no CI.

## 7. WEAK SIH/DEMO AREAS

1. **No scenario analysis.** The most predictable evaluator question — *"what if your forecast
   is wrong?"* — has no answer in the product today. Highest-value gap.
2. **Optimizer is a constant lookup** (B-2) — the second most likely question.
3. **Risk ignores dates** (B-3) — trivially exposed by editing an input live.
4. Currency: engines emit **USD/tonne**; any slide using `₹` is a false claim.

---

## 8. HIGHEST-IMPACT IMPROVEMENTS (priority order)

**P0 — correctness and defensibility**
1. B-1 `test_api_live.py` → `TestClient` (green suite, offline). `backend/tests/test_api_live.py`
2. B-3 Risk consumes the real delivery window. `backend/services/risk_service.py`
3. B-4 Capacity as a genuine hard constraint. `backend/engines/vessel_port.py`
4. B-6 Enum leak at source. `backend/services/optimize_service.py`
5. B-2 Either implement MILP or stop calling it one, everywhere.

**P1 — SIH value**
6. Scenario engine + `POST /api/scenario`, re-solving under freight/congestion/availability
   shocks and reporting whether the recommendation flipped.
   New `backend/services/scenario_service.py`, `backend/main.py`, `backend/schemas.py`
7. Cockpit scenario panel. `frontend/src/components/`
8. Root `requirements.txt`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`.

**P2 — polish (only after P0/P1)**
9. B-5 demurrage threshold or honest label. 10. Availability windows. 11. Explanation module.
12. `develop` branch + CI.

**P3 — post-round:** real PuLP MILP, LightGBM, `/api/v1/decision`.

---

## 9. FILES REQUIRING MODIFICATION

```
backend/tests/test_api_live.py        B-1  rewrite to TestClient
backend/services/risk_service.py      B-3  real delivery-window scoring
backend/engines/vessel_port.py        B-4  capacity hard constraint  (B-5 later)
backend/services/optimize_service.py  B-6  .value on enums
backend/schemas.py                    P1   scenario contracts
backend/services/scenario_service.py  P1   NEW
backend/main.py                       P1   POST /api/scenario
backend/tests/test_scenario.py        P1   NEW
frontend/src/components/              P1   scenario panel
requirements.txt, AGENTS.md, ...      P1   NEW at root
```

---

## 10. UNCLEAR — needs a human decision, not a guess

1. **Architecture of record** — adopt the blueprint tree, or re-scope the blueprint to the
   built system? Recommendation: re-scope the blueprint.
2. **MILP** — will the team claim it at the internal round? If yes it must be built; if no it
   must be removed from every slide and doc. There is no safe middle.
3. **Streamlit vs React** — a verified React cockpit exists. Confirm nothing in the submission
   promises Streamlit.
4. **Currency** — reconcile USD engine output against any `₹` in the deck.
