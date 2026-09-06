# Contributing to VARUNEETI

## Branching

- `main` — always demo-safe
- `develop` — integration
- `feature/<module>-<task>` — individual work

## Commit style

`feat:` `fix:` `test:` `docs:` `refactor:` — small, single-purpose commits.

## Before opening a PR

```bash
python -m pytest backend/tests -q          # must be 100 passed
cd frontend && npm run build               # must succeed
node scripts/verify-demo.mjs               # golden demo, needs both servers up
```

## PR must state

1. What changed and why
2. Files changed
3. Tests added/updated
4. Any contract (`backend/schemas.py`) changes
5. Any new assumptions, and whether they are labelled in the API response
6. Anything proposed rather than implemented

## Review checklist

- [ ] No fabricated data, port limits, accuracy or savings claims
- [ ] Proxy/illustrative values labelled in the response `assumptions`
- [ ] Units preserved (costs are USD/tonne)
- [ ] No business logic added to routes or the frontend
- [ ] No engine logic duplicated
- [ ] Golden scenario still produces a recommendation
- [ ] Tests pass offline
