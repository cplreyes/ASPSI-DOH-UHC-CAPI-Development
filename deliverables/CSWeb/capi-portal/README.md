# capi-portal (patched sources — worktree copy is authoritative)

Patched 2026-07-28 for the console move to capi.asiansocial.org:
- `CONSOLE` origin constant; every `/docs` link (LINKMAP incl. absolute forms +
  bare-text mentions, monitoring/data/tabulations cards, OV_DASH/OV_MAP) points at capi.
- `/csweb/` links (CSEntry sync, CSWeb app) deliberately stay on csweb.
- Administration nav group added (portal is sign-in-gated since 2026-07-28).
- `_ov_fetch_status()` prefers a local `src/status.json` (scp it before building) —
  the anonymous HTTP fetch now hits the sign-in redirect.

`src/` (40 MB ported content) and `build/` live in the MAIN checkout at
`deliverables/CSWeb/capi-portal/` — whose `build_portal.py`/`portal_shell.py` are now
BEHIND these copies. To build: place these two .py files beside that `src/`, scp a fresh
`status.json` into `src/`, run `python build_portal.py`, deploy build/ over
/opt/app/capi-www (tar, no --delete; never ship status.json/tabulations.json — gen-owned).
