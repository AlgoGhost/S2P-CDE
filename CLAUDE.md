# Claude project context — VARUNEETI

Charter decision-support prototype for SIH 2026 (PS26006, Ministry of Steel / SAIL).

**Read `AGENTS.md` first**, then `docs/CURRENT_STATE_AUDIT.md`.

Key things that are easy to get wrong here:

- The build blueprint PDF describes an architecture this repo does **not** use.
  Trust the code and `docs/IMPLEMENTATION_STATUS.md`, not the blueprint.
- The optimizer is a **cost comparison over four charter structures**, not a
  MILP. Do not describe it as one.
- All money is **USD**, never INR.
- `ForecastService.forecast` is memoised (`lru_cache`). It is a pure function of
  the CSV dataset; if you ever make the dataset mutable at runtime, that cache
  must be invalidated.
- Tests run fully offline via FastAPI `TestClient`. Do not reintroduce tests
  that require a manually started server.

Run: `python -m pytest backend/tests -q` (100 tests, ~75 s).
