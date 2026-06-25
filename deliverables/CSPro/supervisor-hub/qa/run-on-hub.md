# On-hub QA — run the Phase-1 Supervisor-QA report on collected data (Task B8)

**Status:** the Phase-1 report tool is verified green (`15 passed`, 2026-06-25) and is **reused
UNCHANGED** — this doc only describes how to point it at the hub-collected data. The actual
collection (Bluetooth) is Task B6/B7, gated on the **C2 spike**; until then this is the procedure
of record, runnable today against any CSV export.

## What this is

The supervisor "hub" tablet accumulates the cluster's F1/F3/F4 cases (via Bluetooth collection,
B6/B7). Because the hub holds the collected `.csdb`, the **Phase-1 Supervisor-QA report runs
directly on the hub** — coverage vs plan, partials (#561), and data-quality flags — **before relay
to CSWeb**, with no CSWeb round-trip needed in a no-signal cluster. QA is **advisory** (D2): the
supervisor chases gaps verbally; the enumerator fixes on their own device. No write-back.

## The tool (reused, do NOT modify)

`deliverables/CSWeb/supervisor-app/` — the Phase-1 Python report (stdlib only). Verify it's green
before relying on it:

```
cd deliverables/CSWeb/supervisor-app
py -m pytest -q          # expect: 15 passed
```

## Run it on hub-collected data

1. **Export** each instrument's collected cases from the hub to CSV — `F1.csv`, `F3.csv`, `F4.csv` —
   via CSEntry Data Export / the desktop Data Viewer / Data Manager. (Same export the Phase-1 README
   §"Evening laptop run" describes — the only difference is the **source**: the hub-collected
   `.csdb` instead of a CSWeb pull.)
2. Maintain the cluster's `assignments.csv` (the EA → enumerator → target plan; mirrors the
   `Assignment.dat` seeded in `supervisor-hub/Assignment.dcf`). A worked example ships at
   `deliverables/CSWeb/supervisor-app/assignments.example.csv`.
3. Run the report:

```
py supervisor_qa_report.py \
    --exports ./exports \
    --assignments ./assignments.csv \
    --out ./supervisor-qa.html \
    --cluster 01028 \
    --today 20260625
```

4. Open `supervisor-qa.html` — a PII-light 3-panel report (coverage vs plan · partials · 5 QA flags).
   The only PII step is the on-site spot-check (advisory).

## Notes

- **Same tool/command as Phase 1** — only the export source differs (hub-collected vs CSWeb-pulled).
  This is deliberate: the report engine reads CSV regardless of how the cases arrived, so it is
  Bluetooth-collection-compatible with zero changes.
- The on-DEVICE per-role report (the MenuApp "view report" items, Task B2/N4) is a separate, lighter
  surface for the field; this laptop/desktop report stays the at-base authoritative pass.
- Do not `git commit` — Carl handles git.
