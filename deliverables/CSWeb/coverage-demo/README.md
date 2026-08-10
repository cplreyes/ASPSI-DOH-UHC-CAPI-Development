# Coverage % choropleth — real-denominator demo (illustration only)

Built 2026-07-15 to answer "do we have a way to fix the Coverage % choropleth?"
**Decision: keep as a demo. The live generator was NOT changed.** Revisit when
ASPSI hands over the real EA/assignment plan, or when fieldwork actually starts.

## What this shows

`csweb-map-gen.py` run **off-box** in `--sample` mode (no MySQL, no prod) with a
**real F1 denominator** — one target per province = count of sampled facilities from
`../../CSPro/F1/facility_lookup.dat` (1,521 facilities = the survey's stated sample).
Proves a real national F1 coverage choropleth is buildable today with no ASPSI
dependency. See `coverage-map-demo.png`.

- **Real:** province polygons, the pipeline, and every province's denominator
  (Bulacan 53, Batangas 42, Pangasinan 37, Laguna 34, …). 80 provinces matched cleanly.
- **Illustrative:** the shading colours — completed counts are fabricated to show the
  red→amber→green gradient. Fieldwork hasn't started, so the real numerator is ≈0 today
  (the honest live map right now would be almost all red/grey).
- **Caveat:** NCR/HUC cities aren't provinces in the faeldon 2011 boundaries, so ~41 of
  121 provinces have no polygon and don't shade. Known vintage limit; provincial coverage
  is unaffected.

## The two options this demo was weighing (see ../coverage-real-denominator-fork.png)

- **A (F1-real):** point the denominator at `facility_lookup.dat`; make `plan.provisional`
  per-instrument so F1 reads REAL while F3/F4 stay provisional. No ASPSI dependency.
- **B (all three):** also derive F3 (67 OP + 45 IP = 112/province) and F4 from the Apr-28
  manual. Faster to full colour but leans on unconfirmed working-version quotas.

## Regenerate (all local, public GitHub fetch only)

```bash
# 1. province polygons (patch OUT to a local path first)
python gen-ph-boundaries.py            # -> ph-areas.json  (from ../gen-ph-boundaries.py)
# 2. real F1 targets + illustrative completed fixture
python build_demo_inputs.py            # -> targets-demo.json, fixture-demo.json
# 3. the real map, sample mode
python ../csweb-map-gen.py --sample fixture-demo.json --targets targets-demo.json \
       --areas ph-areas.json --out coverage-map-demo.html
# open coverage-map-demo.html (asset paths point at the public csweb.asiansocial.org)
```
