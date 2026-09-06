# VARUNEETI — Maritime Charter Decision Intelligence Engine

**SIH 2026 · PS26006 · Ministry of Steel / SAIL**
*Development of an Intelligent Freight Forecasting Model for Optimized Vessel Chartering and Bulk
Cargo Procurement from overseas to the East Coast of India*

> **From freight prediction to charter decision.**
> Forecast the market. Respect the port. Quantify the risk. Optimize the charter.

VARUNEETI does not stop at forecasting freight rates. It converts market uncertainty into an
auditable charter decision that respects real vessel and port constraints — then shows its reasoning.

**Repository:** `S2P-CDE` — SAIL Spot-to-Period Charter Decision Engine.
VARUNEETI is the engine and cockpit implemented in this repository: it analyses freight rates,
vessel availability and port conditions to recommend how much tonnage SAIL should commit under a
period charter versus leave open to spot.

**Status:** see [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md) for what is
actually built, [`docs/FINAL_SIH_READINESS.md`](docs/FINAL_SIH_READINESS.md) for the demo
runbook, and [`docs/CURRENT_STATE_AUDIT.md`](docs/CURRENT_STATE_AUDIT.md) for the engineering
audit. The optimizer compares four charter structures on a common cost basis — it is **not**
a MILP, and must not be described as one.

> **DISCLAIMER** — All data in this repository is **prototype/proxy data** generated for
> demonstration. It contains no proprietary SAIL data and no Baltic Exchange data. All costs are
> **modelled expected values under stated assumptions**, in **USD/tonne** — not quotes, and not
> guaranteed savings.

---

## Quick start

Two terminals, from the repository root.

```bash
# Terminal 1 — decision engine (FastAPI)
python -m uvicorn backend.main:app --port 8000

# Terminal 2 — decision cockpit (React + Vite)
cd frontend
npm install        # first run only
npm run dev
```

Open **<http://localhost:5173>**, click **LOAD SIH DEMO CASE**, then **ANALYZE CHARTER**.

`/docs` (Swagger) is a developer testing surface only — the product is the cockpit.

> The backend CORS allowlist permits `localhost:5173` and `localhost:3000` only. To serve a
> production build: `npm run build && npx vite preview --port 3000 --strictPort`.

If the prototype dataset is missing, regenerate it:

```bash
python backend/data/generate_data.py
python backend/data/generate_vessel_port_data.py
```

---

## The decision loop

```
INPUT  →  FORECAST  →  VESSEL × PORT  →  RISK  →  OPTIMIZER  →  DECISION
```

| Stage | Engine | Output |
|---|---|---|
| Forecast | SARIMAX → moving average → naive fallback, walk-forward validated | Point forecast, 95% interval, trend, volatility, confidence |
| Vessel × Port | Deterministic hard-constraint checks (draft / LOA / beam) + lightering | DIRECT · LIGHTERING · INFEASIBLE per vessel class, fit score, parcelisation |
| Risk | Six weighted dimensions | 0–100 composite, level, ranked drivers |
| Optimizer | Four charter structures on one forecast + one feasible vessel | Recommended structure, lock/flex split, expected cost, decision drivers |

**The core insight the demo makes visible:** the cheapest vessel per tonne is not automatically a
usable vessel. At Paradip (14.5 m max draft) an 18 m Capesize is rejected outright — a forecasting
model alone would have recommended it.

---

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Liveness |
| `/api/lanes` | GET | Available origin/destination/vessel lanes |
| `/api/forecast` | POST | Freight forecast for a lane |
| `/api/feasibility` | POST | Vessel–port feasibility across all classes |
| `/api/risk` | POST | Composite decision risk |
| `/api/optimize` | POST | Charter strategy recommendation |
| `/api/scenario` | POST | Stress test: re-solves the decision under 5 shock cases |

`/api/optimize` returns the recommendation and strategy comparison but does not nest the forecast,
feasibility or risk payloads — the cockpit calls all four endpoints and assembles the view.

---

## Project layout

```
backend/
  main.py            FastAPI app and routes
  schemas.py         Pydantic request/response models
  config.py          Constants, thresholds, CORS, data paths
  engines/           forecasting.py, vessel_port.py
  services/          forecast, vessel, risk, optimize, data adapter
  data/              Prototype proxy CSVs + generators
  tests/             66 tests
frontend/
  src/
    api.js           Engine client + decision loop orchestration
    lib/format.js    Formatting and derived-value helpers
    components/      Cockpit sections
  scripts/
    verify-demo.mjs  Browser harness: drives the real UI, asserts UI/API parity
docs/                Architecture, assumptions, data sources
DEMO_READINESS.md    Demo script, claims we can/cannot make, verification status
```

---

## Verification

```bash
python -m pytest backend/tests -q        # 66 passed

cd frontend && node scripts/verify-demo.mjs
# Drives the real cockpit in a real browser against the live backend:
# demo case -> analyze -> asserts every section rendered, UI figures match
# /api/optimize exactly, no console errors, no overflow at 1366×768.
```

See **[DEMO_READINESS.md](DEMO_READINESS.md)** for the demo script, implemented vs. planned
features, known limitations, and the claims we can and cannot defend.
