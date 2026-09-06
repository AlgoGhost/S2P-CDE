# VARUNEETI — FINAL SIH READINESS

**SIH 2026 · PS26006 · Ministry of Steel / SAIL**
Prepared 2026-09-06 · 100 tests passing · golden demo verified end-to-end in a real browser

---

## 1. What was already built

A working decision pipeline existed before this session:

- Freight forecasting (SARIMAX → moving average → naive) with walk-forward
  validation and 95% prediction intervals.
- Vessel–port feasibility with draft/LOA/beam hard constraints and lightering.
- A 6-factor weighted risk score.
- A four-structure charter cost comparison (SPOT / SHORT / MEDIUM / HYBRID).
- FastAPI with 6 endpoints and typed Pydantic contracts.
- A React decision cockpit covering the whole story.
- 58 passing unit tests.

The architecture was sound. The gaps were in **integration, honesty of inputs,
and stress testing** — not in structure.

---

## 2. What was improved this session

| # | Problem found | Fix |
|---|---|---|
| 1 | **8 tests failed on a clean checkout.** `test_api_live.py` hardcoded `http://127.0.0.1:8000` and required a server it never started. | Replaced with `test_api.py` using FastAPI `TestClient` — 30 tests, no server, no network. |
| 2 | **The risk engine ignored the delivery window.** `delivery_pressure` was hardcoded to 50.0 and `weather` to 40.0; `delivery_start`/`delivery_end` were accepted by the API and never read. Changing the dates changed nothing. | Both now computed. Delivery pressure compares the requested window against the port time the feasibility engine actually calculates; seasonal risk is derived from the delivery months. A 10-day window now scores 100 with the explanation *"9-day window cannot absorb 13.2 days of modelled port time across 4 voyages."* |
| 3 | **The capacity constraint was dead code.** `parcel_cap = min(parcel, capacity)` ran before `if parcel_cap <= capacity`, making the check vacuously true. A 75,000 t parcel request silently became a 35,000 t Handysize parcel. | Capacity is now evaluated against the **requested** parcel. Vessels that cannot meet it are penalised and the shortfall is stated. Panamax now wins on fit score (100) over Supramax (84) and Handysize (68) — a meaningful ranking rather than a cost tiebreak. |
| 4 | **Python enum reprs leaked into the API.** `/api/optimize` returned `"Forecast trend is TrendDirection.STABLE…"`. | Fixed at source; a regression test asserts no enum repr appears in `decision_drivers`. |
| 5 | **No scenario analysis** — the most predictable evaluator question ("what if the forecast is wrong?") had no answer. | New scenario engine + `POST /api/scenario`. Five cases re-solve the **complete** decision path. |
| 6 | **Wasted computation.** Each decision ran the forecast several times (the optimizer and risk engine each triggered one), and scenarios repeated it five times. `/api/scenario` took **42.8 s**. | Memoised `ForecastService.forecast` — it is a pure function of the CSV dataset, which is never mutated at runtime. `/api/scenario` now returns effectively instantly; the test suite dropped from 348 s to 75 s. |
| 7 | Two dead contracts (`AnalyzeRequest`, `ScenarioRequest`) referenced nowhere. | Replaced with live scenario contracts. |
| 8 | Missing root scaffolding. | Added `requirements.txt`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`. |
| 9 | Sidebar labelled the strategy section "Scenarios". | Split into "Strategy" and "Scenarios". |

**Not touched:** the forecasting engine, the feasibility cost model, and the
strategy multipliers — all were working and were left alone.

---

## 3. What is now actually working

```
Input -> Forecast -> Feasibility -> Risk -> Strategy -> Scenario -> Decision -> Cockpit
```

Every stage contributes to the final recommendation, and every stage now
responds to input. The scenario engine closes the loop by re-running the whole
chain under stress.

---

## 4. Tests

```
100 passed in ~75 s — fully offline, no server required

test_forecasting.py   forecast engine, bounds ordering, leakage
test_feasibility.py   constraint boundaries, lightering
test_risk.py          composite scoring, driver ordering
test_optimize.py      strategy costing, recommendation derivation
test_scenario.py      shocks move real numbers, robustness verdict, determinism
test_api.py           all 7 endpoints, validation, edge cases
```

Edge cases covered: unknown port (400 not 500), unknown lane (400), invalid
window (end before start), a port too shallow for the entire fleet (Haldia),
missing fields (422), wrong types (422), and no-feasible-vessel handling.

---

## 5. Golden demo result

**Australia → Paradip · 300,000 t · 75,000 t parcels · Oct–Dec 2026**

```
RECOMMENDATION   MEDIUM_TERM · Panamax · 4 voyages · $29.15/t · $8.74M
RISK             34.2 / 100  MEDIUM

FEASIBILITY      Panamax    fit 100  DIRECT_FEASIBLE   (capacity, draft, loa, beam)
                 Supramax   fit  84  DIRECT_FEASIBLE   (below requested parcel, 6 voyages)
                 Handysize  fit  68  DIRECT_FEASIBLE   (below requested parcel, 9 voyages)
                 Capesize   fit   0  INFEASIBLE        (draft, loa, beam)

STRATEGIES       Spot $30.68/t · Short $30.07/t · Medium $29.15/t ← · Hybrid $29.76/t

STRESS TEST      Freight +25%        MEDIUM_TERM  $36.33/t  +24.6%   HOLDS
                 Freight -20%        MEDIUM_TERM  $23.40/t  -19.7%   HOLDS
                 Congestion +40%     HYBRID       $29.94/t   +2.7%   STRATEGY FLIPS
                 Panamax unavailable MEDIUM_TERM  $29.19/t   +0.1%   VESSEL CHANGES (Supramax, 6 voyages)

VERDICT          Recommendation is CONDITIONAL: 1 of 4 stress cases changes the structure.
```

**The congestion flip is the demo's strongest moment and it is entirely
computed:** congestion +40% → risk rises 34.2 → 50.2 → crosses the optimizer's
risk threshold → MEDIUM_TERM takes a penalty → HYBRID becomes cheapest. Nothing
about that chain is hardcoded.

Cockpit verification: 0 console errors, 0 failed requests, UI figures match the
API exactly, no horizontal overflow at 1366×768 or 1920×1080.

---

## 6. Remaining limitations (state these before you are asked)

1. **The optimizer is not a MILP.** It compares four charter structures using
   configured multipliers and picks the cheapest. There are no decision
   variables and no solver. Do not call it a MILP.
2. **Sailing time is not modelled.** No route distances exist in the dataset, so
   delivery pressure reflects port time only and understates true schedule risk.
3. **No vessel availability windows.** Laycan overlap is not checked.
4. **Demurrage evaluates to zero** at every port in the dataset — the 1.5×
   handling-time threshold is never reached.
5. **Hybrid's 60% lock is fixed**, not optimised. The obvious next step is
   solving for the optimal lock fraction.
6. **Scenario shocks are assumptions**, not calibrated probabilities, and are
   not probability-weighted.
7. **Forecast confidence is a composite heuristic**, not a calibrated
   probability.
8. Monthly data means a 30-day horizon yields a single projected period.

---

## 7. Data disclaimer

All data is a **generated prototype/proxy dataset** committed to
`backend/data/`. It contains **no proprietary SAIL data, no Baltic Exchange
data, and no licensed market feed**. Port and vessel values are illustrative and
marked `prototype_assumption` in the source CSVs.

All costs are **modelled expected values under stated assumptions**, in
**USD/tonne** — not quotes, not realised results, not guaranteed savings.
Any slide rendering these figures with a `₹` symbol is wrong.

A production deployment would connect representative SAIL and licensed feeds
through the existing data adapter without changing the engines.

---

## 8. Commands

```bash
# ── Backend (terminal 1, from the repository root) ──
pip install -r requirements.txt
python -m uvicorn backend.main:app --port 8000
#   health:  http://localhost:8000/api/health
#   OpenAPI: http://localhost:8000/docs      (developer tool, NOT the demo UI)

# ── Cockpit (terminal 2) ──
cd frontend
npm install          # first run only
npm run dev
#   open http://localhost:5173

# ── Tests ──
python -m pytest backend/tests -q            # 100 passed, ~75 s, offline

# ── Automated demo verification (needs both servers up) ──
cd frontend && node scripts/verify-demo.mjs
```

**Demo script:** open the cockpit → **LOAD SIH DEMO CASE** → **ANALYZE CHARTER**
→ scroll through Recommendation, Pipeline, Forecast, Feasibility, Risk,
Strategy, **Scenario Stress Test**, Voyage Plan, Why, Cost.

---

## 9. Known risks before judging

| Risk | Mitigation |
|---|---|
| **"Is this a MILP?"** — it is not. | Answer directly: it is a constraint-filtered cost comparison across four charter structures; MILP is the documented next step. Claiming otherwise is the single biggest exposure. |
| First request is slow (~1.4 s SARIMAX fit) | Run the golden case once before judges arrive to warm the forecast cache. |
| Backend not running → cockpit shows an error panel | The cockpit offers **Load Demo Snapshot**, clearly labelled as recorded output, never presented as live. |
| Currency confusion | Engines emit USD. Check the deck for `₹`. |
| Judge edits the delivery window | This now works and is a strength — a 10-day window pushes delivery pressure to 100 with a stated reason. |
| Judge asks for a lane not in the dataset | The origin/destination dropdowns are constrained to covered lanes; unknown ports return a clean 400, never a stack trace. |
| Blueprint PDF contradicts the build | `docs/CURRENT_STATE_AUDIT.md` §0 and `docs/IMPLEMENTATION_STATUS.md` state the real architecture. Do not hand judges the blueprint as a description of this system. |
