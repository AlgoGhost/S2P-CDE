# VARUNEETI — Demo Readiness

**SIH 2026 · PS26006 · Ministry of Steel / SAIL**
Maritime Charter Decision Intelligence Engine

Last verified: **2026-08-25** — full loop run end-to-end in a real browser against the live backend.

---

## 1. Startup commands

Two terminals, both from the repository root (`n:\VARUNEETI`).

**Terminal 1 — backend (FastAPI, port 8000):**

```bash
python -m uvicorn backend.main:app --port 8000
```

Wait for `Application startup complete.` Verify: <http://localhost:8000/api/health> returns
`{"status":"ok","version":"0.2.0","service":"VARUNEETI"}`.

**Terminal 2 — frontend cockpit (Vite, port 5173):**

```bash
cd frontend
npm install     # first run only
npm run dev
```

Open **<http://localhost:5173>** — this is the judge-facing product.

> **Port matters.** The backend CORS allowlist (`backend/config.py`) permits only
> `localhost:5173` and `localhost:3000`. Vite is pinned to 5173 via `strictPort`. If you serve a
> production build instead, use `npx vite preview --port 3000 --strictPort`.

Optional — point the cockpit at a different engine host:

```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 2. Demo flow (rehearsed script)

1. Open <http://localhost:5173>. Header shows **● SYSTEM ONLINE** and **PROTOTYPE / PROXY** data status.
2. Click **LOAD SIH DEMO CASE** → fills Australia → Paradip, 300,000 t, 75,000 t parcels, 2026-10-01 → 2026-12-31.
3. Click **ANALYZE CHARTER**. A five-stage pipeline animates: Market Forecast → Vessel–Port Check → Risk Assessment → Charter Optimization → Decision Ready (~3–6 s; SARIMAX fit dominates).
4. The cockpit reveals, in narrative order:
   - **Charter Recommendation** — MEDIUM-TERM, Panamax, 4 voyages, MEDIUM risk, $29.15/t, $8.74M
   - **Decision Pipeline** — one headline output per engine
   - **Freight Outlook** — 56 observed points + forecast with 95% interval
   - **Vessel–Port Feasibility** — Panamax/Handysize/Supramax DIRECT, **Capesize INFEASIBLE**
   - **Decision Risk Radar** — 35/100 MEDIUM, six dimensions, top-3 drivers
   - **Charter Strategy Comparison** — four structures, Medium-Term highlighted
   - **Multi-Voyage Plan**, **Why This Decision**, **Cost Breakdown**, **Architecture**, **Data Status**

### The line that wins the room

At **Vessel–Port Feasibility**, point at the Capesize row:

> "Capesize carries the most cargo and the lowest freight per tonne. VARUNEETI refuses it — 18 m
> draft against Paradip's 14.5 m limit, plus LOA and beam. Cheaper per tonne does not mean usable.
> A forecasting model alone would have recommended it."

### Strong second scenario (shows the constraint engine really biting)

Select origin **USA** (destination auto-snaps to **Haldia**, max draft 7.5 m) → **ANALYZE CHARTER**:

- Recommendation flips to **HYBRID** — 60% locked / 40% flexible
- **Handysize** selected with **LIGHTERING** required
- **Panamax, Supramax and Capesize are all INFEASIBLE** — only 1 of 4 classes usable
- Risk rises to 59.5/100, top driver becomes **vessel availability**

This proves the recommendation is genuinely computed, not scripted.

---

## 3. What is implemented

### Fully implemented and demonstrable

| Capability | Where | Notes |
|---|---|---|
| Freight forecasting | `backend/engines/forecasting.py` | SARIMAX → moving average → naive fallback chain, walk-forward validation vs naive baseline |
| Forecast API | `POST /api/forecast` | Point forecast, 95% interval, trend, volatility, confidence, MAE/RMSE/MAPE, full historical + forecast series |
| Vessel–port feasibility | `backend/engines/vessel_port.py` | Hard draft/LOA/beam constraints, lightering evaluation, fit scoring, parcelisation, port time & cost |
| Feasibility API | `POST /api/feasibility` | All four vessel classes evaluated, ranked, recommended + alternatives |
| Risk engine | `backend/services/risk_service.py` | Six weighted dimensions → 0–100 composite + severity + ranked drivers |
| Risk API | `POST /api/risk` | Overall score, level, top drivers, all drivers, assumptions |
| Charter optimization | `backend/services/optimize_service.py` | Four structures costed on one forecast + one feasible vessel, risk penalties on long locks |
| Optimize API | `POST /api/optimize` | Recommendation, strategy comparison, voyages, decision drivers, assumptions |
| Lane discovery | `GET /api/lanes` | Drives the cockpit dropdowns |
| Decision cockpit | `frontend/` | React 18 + Vite, 10 sections, hand-built SVG charts, no chart library |
| Loading pipeline | `frontend/src/components/Cockpit.jsx` | Five stages driven by real request boundaries, not timers |
| Error handling | `frontend/src/api.js`, `App.jsx` | Operator-safe messages, retry, labelled offline snapshot |
| Demo snapshot fallback | `frontend/src/demoSnapshot.js` | Verbatim recorded live engine responses, always banner-labelled |
| Browser verification harness | `frontend/scripts/verify-demo.mjs` | Drives the real UI, asserts UI/API parity, checks console + overflow |

### Partially implemented

- **Risk dimensions** — all six are scored and contribute to the composite, but weather and delivery
  pressure are **static proxies** (not derived from weather or laycan data). The UI states this.
- **Delivery window** — accepted, passed through, and used for the indicative parcelisation display,
  but voyage-level scheduling/laycan optimization is **not modelled**.
- **Cost breakdown** — freight, port, demurrage and lightering are real engine outputs. Idle/positioning
  and an explicit risk provision are **not modelled** and are shown as "Not available in prototype".
- **Lane coverage** — the proxy dataset covers 5 origins × 6 destination pairs, not the full
  cross-product. The cockpit constrains the destination dropdown to the selected origin.

### Not implemented (do not claim)

Authentication, user management, persistence/database, live or licensed market feeds, weather feeds,
AIS/vessel tracking, port congestion feeds, OR-Tools or any MILP solver, LightGBM/ensemble models,
websockets/real-time updates, multi-user scenarios, PDF/report export, Docker packaging.

---

## 4. API reference (as actually implemented)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Liveness — drives the SYSTEM ONLINE pill |
| `/api/lanes` | GET | 24 lane/vessel combinations with observation counts |
| `/api/forecast` | POST | Freight forecast for one lane + vessel class |
| `/api/feasibility` | POST | Vessel–port feasibility across all classes |
| `/api/risk` | POST | Composite decision risk |
| `/api/optimize` | POST | Charter strategy recommendation |

Swagger at `/docs` is a **developer testing surface only** — never demo from it.

**Integration note:** `/api/optimize` does *not* nest the forecast, feasibility or risk payloads
(see `OptimizeResponse` in `backend/schemas.py`). The cockpit therefore calls all four endpoints and
assembles the view. It does **not** recompute anything the backend already computes.

**Forecast benchmark:** `OptimizeService` and `RiskService` both run their internal forecast on
**Panamax**. The cockpit requests the same lane/vessel so the chart can never contradict the
recommendation. When the feasible hull differs (e.g. Handysize at Haldia), the UI explains why.

---

## 5. Claims we can safely make

- "Forecasts freight rates using SARIMAX with a statistical fallback chain, validated walk-forward against a naive baseline." *(Model beats baseline on the demo lane: MAE 3.90 vs 4.69, MAPE 12.64%.)*
- "Enforces hard physical port constraints — draft, LOA and beam — so a vessel that cannot call is never recommended, regardless of freight economics."
- "Evaluates lightering as a conditional-feasibility path with its own cost, time and risk."
- "Scores decision risk across six weighted dimensions and exposes the ranked drivers."
- "Compares four chartering structures on a common forecast and a common feasible vessel, and recommends how much tonnage to lock versus keep flexible."
- "Every recommendation is auditable — the engines emit the decision drivers shown in the UI."
- "Decision support with a human in the loop; the chartering desk decides."
- "Architecture is layered so production feeds swap in at the data adapter without touching the engines."
- "Modelled saving vs the all-spot reference case for the demo programme is $460.2K (5.0%) **under stated prototype assumptions**."

## 6. Claims we must NOT make

- ❌ "Guaranteed savings" / "guaranteed accuracy" / "100% accurate" — everything is modelled and prototype-data-driven.
- ❌ "$460K saved" without "modelled, under prototype assumptions, versus an all-spot baseline."
- ❌ "Uses SAIL data" / "Baltic Exchange data" / "live market data" — the dataset is generated proxy data in `backend/data/`.
- ❌ "Real-time" anything — there are no live feeds and no websockets.
- ❌ "Fully autonomous procurement" — it is decision support, not execution.
- ❌ "Uses OR-Tools / LightGBM / a database" — none are in the repository.
- ❌ Quoting costs in ₹ — the dataset and every derived cost are **USD/tonne**.
- ❌ "Predicts weather / port congestion" — those risk inputs are static proxies.

---

## 7. Known limitations (own these before a judge does)

1. **Prototype data.** Generated proxy series, disclosed in the UI footer and in the panel badges.
2. **Monthly series.** A 30-day horizon resolves to one forecast period; the UI states this rather than faking a denser path.
3. **Charter multipliers are assumptions.** Spot 1.00 / Short 0.98 / Medium 0.95 / Hybrid 0.97, plus risk penalties — stated by the optimizer and surfaced verbatim in the UI.
4. **Weather and delivery-pressure risk are static proxies.**
5. **No voyage-level scheduling.** Parcelisation dates are an even spread across the delivery window, labelled indicative.
6. **Lane coverage is partial** (6 origin→destination pairs). Mitigated by constraining the dropdowns.
7. **Enum repr leak in `decision_drivers`.** The optimizer f-strings raw enums (`TrendDirection.STABLE`). The cockpit normalises this for display; the backend string is unchanged.
8. **SARIMAX convergence warnings** appear in backend logs on some lanes — the fallback chain handles them; forecasts remain valid.

---

## 8. Verification status

Run: `cd frontend && node scripts/verify-demo.mjs` (backend + `npm run dev` must be up).

| Check | Result |
|---|---|
| Backend starts, `/api/health` OK | ✅ |
| Frontend starts, cockpit loads | ✅ |
| SYSTEM ONLINE detected from live health probe | ✅ |
| Demo case loads with correct values | ✅ |
| Analyze Charter completes end-to-end | ✅ |
| Recommendation renders | ✅ |
| **UI/API parity** (strategy, voyages, cost/t, vessel match `/api/optimize` exactly) | ✅ |
| Decision pipeline — 5 stages | ✅ |
| Forecast chart + prediction interval | ✅ |
| Feasibility matrix — 4 vessels, Capesize INFEASIBLE | ✅ |
| Risk gauge + 6 dimensions + top drivers | ✅ |
| Strategy comparison — 4 cards + 2 bar charts | ✅ |
| Voyage plan — 4 voyages | ✅ |
| Decision drivers — 7 traced signals | ✅ |
| Cost breakdown with declared gaps | ✅ |
| Data transparency footer | ✅ |
| No console errors (dev **and** production build) | ✅ |
| No uncaught page errors / failed requests | ✅ |
| No horizontal overflow @1366×768 | ✅ |
| No text truncation in hero metrics @1366×768 | ✅ |
| Layout @1920×1080 | ✅ |
| Backend-down → clean error panel, **no Python traceback** | ✅ |
| Snapshot fallback renders and is banner-labelled | ✅ |
| Alternate scenario (USA→Haldia) produces a different, correct decision | ✅ |
| Backend test suite | ✅ 66 passed |

### Remaining blockers

**None for the demo.**

---

## 9. Backend changes made during this session

One change only, purely additive — no business logic touched:

- `backend/schemas.py` — added optional `RiskResponse.all_drivers` (defaults to `[]`).
- `backend/services/risk_service.py` — populates it with the already-computed driver list (one line).

This lets the Risk Radar show all six scored dimensions instead of only the top three. `top_drivers`
is unchanged, and all 66 existing tests pass. The forecasting, feasibility and optimization engines
were **not modified**.

---

## 10. Pre-demo checklist

- [ ] Backend running on 8000, `/api/health` returns ok
- [ ] Frontend running on 5173, header shows ● SYSTEM ONLINE
- [ ] Browser at 100% zoom, window maximised
- [ ] Run the demo case once before judges arrive (first SARIMAX fit is the slowest)
- [ ] Have the USA → Haldia scenario ready as the follow-up
- [ ] Close Swagger — never show `/docs`
- [ ] If the backend dies mid-demo: **Load Demo Snapshot**, and say out loud that it is recorded output
