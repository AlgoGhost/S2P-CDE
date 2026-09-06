# VARUNEETI — AI AGENT RULES

**Read before editing:** `docs/CURRENT_STATE_AUDIT.md`, then the module you are
changing. `docs/IMPLEMENTATION_STATUS.md` is the source of truth for what is
actually built.

## The architecture that exists

This repository does **not** use the `backend/app/{api,core,...}` tree described
in the original build blueprint, and it has no PuLP MILP and no Streamlit UI.
The real structure is:

```
backend/
  main.py                 FastAPI, 7 endpoints, no business logic
  schemas.py              Pydantic v2 contracts (the shared boundary)
  config.py               constants, thresholds, CORS
  engines/                pure computation, no I/O
    forecasting.py        SARIMAX -> moving average -> naive
    vessel_port.py        draft/LOA/beam constraints, lightering
  services/               orchestration over engines
    forecast_service.py   memoised entry point
    vessel_service.py     feasibility ranking
    risk_service.py       6-factor weighted composite
    optimize_service.py   4 charter structures, cost comparison
    scenario_service.py   re-solves the decision under shocks
  tests/                  100 tests, all offline
frontend/                 React 18 + Vite decision cockpit
```

## Hard rules

- **Never fabricate** SAIL data, official port limits, forecast accuracy or
  savings percentages. Proxy values must be labelled as such in the response.
- **Never call the optimizer a MILP.** It compares four charter structures using
  configured cost multipliers. There are no decision variables and no solver.
- **Never duplicate engine logic.** The scenario engine re-invokes
  `OptimizeService.optimize()` with shock arguments; it does not re-implement
  costing. Follow that pattern.
- **Never put business logic in `main.py` or in the React frontend.** Routes
  validate and delegate; the cockpit renders what the API returns.
- **Never delete tests to make the suite pass.**
- Preserve `schemas.py` contracts. Changing one is a deliberate, announced act.
- Keep the project runnable **offline**. No new network calls.
- Preserve units. Costs are **USD/tonne** throughout — never render them with a
  `₹` symbol.

## Working method

1. Inspect the existing implementation before editing.
2. Make the smallest coherent change.
3. Add or update tests for it.
4. Run `python -m pytest backend/tests -q`.
5. Report files changed, tests run, assumptions made, and anything unresolved.

## Golden scenario (must always work)

Australia → Paradip, 300,000 t, 75,000 t parcels, Oct–Dec 2026.
Expected: MEDIUM_TERM · Panamax · 4 voyages · ~$29.15/t · risk ~34 MEDIUM,
with Capesize rejected as INFEASIBLE on draft/LOA/beam.
