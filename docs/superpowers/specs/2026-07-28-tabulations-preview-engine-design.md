# Tabulations — deepened preview engine (Phase 1)

- **Date:** 2026-07-28
- **Author:** Carl Patrick Reyes (with Claude)
- **Status:** SHIPPED 2026-07-28 — Phase 1 (this spec) AND Phase 2 both live. Phase 2 note:
  the portal Tabulations page is now emitted by `csweb-tabulations-gen.py::build_page()`
  (hourly, portal_shell chrome, search/status chips/collapsible annexes, per-table preview
  expander fetching the gated tidy JSON; 401 → staff-tier message). The static
  `capi-portal/build_portal.py` no longer writes that page.
- **Surface:** `deliverables/CSWeb/csweb-tabulations-gen.py` (on-box hourly cron) + the public
  `capi.asiansocial.org/projects/uhc-y2/tabulations/` page (Phase 2 consumes this phase's outputs)
- **Approach chosen:** **B — Hybrid** (plan-driven engine + a small hand-built lane for the
  marquee tables the auto-engine can't do cleanly). Options were diagrammed and B was selected.

## 1. Context & problem

The Tabulations feature v1 is already live and honest:

- The public page lists the full **197 PSA-committed tables** (`tabulation-plan.csv`), all marked
  *planned*, plus a KPI strip (197 planned · 0 built · 10 preview).
- 10 **preview tables** — unweighted, pretest-only frequencies (F1×4, F3×3, F4×3) — are generated
  as downloadable `.xlsx`, correctly stamped *"PRETEST / PREVIEW / NOT the official weighted tables."*
- The official **weighted** tables are out of scope by design — they are produced in ASPSI's
  Stata 12 lane (handed over 2026-07-13). This phase never claims a committed weighted number.

The gaps: the previews are thin (10 hand-picked plain frequencies, raw codes, no breakdowns, no
F2, download-only), and they are **disconnected from the 197 committed table numbers**, so the
catalog can't say which committed tables have a preview.

**Goal (this phase):** deepen the previews so they read like real interim pretest findings and are
tied to specific committed table numbers — laying the data foundation for the Phase-2 page UX rework.

**Non-goals:** weighted estimates; official table production; any change to the Stata lane; the
Phase-2 page redesign (separate spec); enumerator/PII exposure.

## 2. Grounded facts (verified 2026-07-28)

- **Join works by case-fold.** Plan `source_variables` are DCF names in UPPERCASE
  (`Q51_YK_ACCRED`); the responses-CSV columns are the same DCF names lowercased by MySQL
  (`q51_yk_accred`). Lowercasing the plan var matches the CSV column.
- **Coverage:** 118 / 197 rows are cleanly auto-previewable — `mapped` + a single categorical
  source var that resolves to a CSV column + not checkbox-multi. Breakdown by instrument:
  **F1 20 · F3 70 · F4 28.** The rest: checkbox-multi, `partial`, `gap`, and F2 (20, answers in
  `values_json`).
- **Breakdown variables exist.** All three CSVs carry a readable `province_name` column (+
  `region_name`); F1 carries `q7_ownership` and `q8_service_level` as in-survey facility-type
  proxies. True facility type (RHU / gov hosp / private hosp) is a masterlist attribute applied in
  the weighted lane, not an in-survey field.
- **Multi-code storage** is a concatenated fixed-width (2-char) code string:
  `q149_lgu_support_forms = "01020304"` → options 01·02·03·04; `q65_accred_difficult = "0205"` →
  02·05, `"90"` → 90. Tally = chunk into 2-char codes, drop blanks/`00`, label, count.
- **Codebook labels are reusable.** `csweb-spss-gen.py` already parses the three CSPro `.dcf`
  dictionaries (JSON, CSPro 8.0) staged flat at `/opt/spss-meta` into item + value labels, and
  handles F2 via `f2-item-labels.json`. This phase reuses that parser (extracted to a shared helper).
- **Phase column exists.** Responses CSVs carry `phase` (+ `activity`); previews filter to
  `phase == "pretest"` (the reference phase; training/survey never mix in).

## 3. Architecture — one engine, two lanes, three outputs

### Lane 1 — plan-driven (the ~118)

For each `tabulation-plan.csv` row, classify:

| class | rule | preview action |
|---|---|---|
| `previewable` | `mapping_status == mapped` AND single source var resolves to a CSV column AND not checkbox-multi | tabulate (Lane 1) |
| `multi` | source var is a checkbox/multi field | multiple-response tally (Lane 2) |
| `partial` | `mapping_status == partial` | status-only in catalog/manifest |
| `gap` | `mapping_status == gap` | status-only ("no source item") |
| `f2` | annex 4 / instrument F2 | F2 path (values_json explode) |

For `previewable` rows:
1. Load `<inst>_responses.csv`, filter `phase == pretest`.
2. Frequency of the source variable, **crossed by the committed breakdown**:
   - breakdown "by province" → `province_name`.
   - breakdown "by facility type" (F1) → `q7_ownership` (fallback `q8_service_level`), rendered
     with an explicit *"proxy — true facility-type split applied in the weighted lane"* note.
   - "none stated" / unmapped breakdown → total-only.
3. **Label codes as words** via the DCF codebook (`/opt/spss-meta`); fall back to the raw code if a
   value has no label. Category order follows the codebook value-set order where available.
4. Emit the cell set tagged with the plan `no` (e.g. `1.7`), `description`, `n`, and the stamp.

### Lane 2 — curated add-ons (the B part)

A small hand-built module for marquee tables the auto-lane marks status-only:

- **Checkbox-multi tally (general technique, covers several committed tables):** split the
  fixed-width alpha multi-code field into 2-char option codes, drop `00`/blank, map each to its
  codebook label, and report a **multiple-response** table — n respondents and % of respondents
  selecting each option (percentages sum > 100 by design; stated explicitly). Target tables include
  Q149 LGU support forms (1.3), Q65 accreditation barriers (1.8), Q151 dissatisfaction reasons
  (1.5), and any other checkbox-multi rows the classifier flags.
- **F3 catastrophic expenditure (25% / 40%) — DEFERRED this phase.** Per approved default #2, the
  escape hatch triggers: the F3 OOP/capacity variables are fragmented (`q127_maifip_oop`,
  `q18_income_amount`/`q18_income_bracket`, `q97_final_amount` — no clean OOP-total ÷ capacity-to-pay
  pair) and the indicator's definition is a documented alignment problem
  (`deliverables/tabulation-plan/CTP-catastrophic-expenditure-alignment-2026-07-06.md`). Faking a
  number would violate the honesty principle, so these tables render **status-only** ("derived
  indicator — see CTP alignment / weighted lane"). Revisit when the CTP definition is settled.

Every Lane-2 table is still keyed to its plan `no` and carries the identical unweighted/pretest stamp.

### F2 path (Annex 4)

Explode `f2_responses.csv` `values_json` into per-item columns using `f2-item-labels.json` (same
technique as `csweb-spss-gen.py::prep_f2`), then tabulate a curated handful of headline items:
respondent sex, staffing gap, satisfaction, attrition intent (Annex-4 marquee indicators). F2 has
no province frame yet, so F2 previews are total-only.

### Three outputs

1. **Per-instrument `.xlsx`** (gated, data room `/docs/data/tabulations/`, as today): hyperlinked
   TOC + one sheet per previewed table, sheet named by table no (`T1.7`); each sheet = title +
   stamp + crosstab. F1/F3/F4/F2.
2. **Tidy preview JSON** `tabulations-preview.json` (gated): flat rows of
   `{table_no, instrument, annex, title, breakdown, category, group, n, pct, status}` — the machine
   contract that Phase-2's in-page viewer and per-row "preview ready" flags read.
3. **Manifest + public catalog:**
   - `tabulations-manifest.json` (gated) gains a per-table `status` and the preview→`table_no` map,
     alongside the existing file list. **Status is terminal (does a preview exist?), not the input
     class:** `preview` = a table was rendered (Lane 1 frequency, a Lane 2 multi-response tally, or
     F2) · `partial` = `mapping_status=partial`, no preview · `gap` = no source item · `deferred` =
     a known-hard derived indicator intentionally not computed (catastrophic expenditure). Thus a
     checkbox-multi table that gets its Lane-2 tally is `preview`, not `multi`.
   - `tabulations.json` (public, portal docroot) gains per-annex preview counts and the set of
     `table_no`s that have a preview — **counts only, no numbers** (titles are public commitments;
     numbers stay gated).

## 4. Honesty guards (unchanged principles)

- Pretest phase only (`phase == pretest`); unweighted; prominent bold small-n / unweighted caveat
  on every sheet and in the tidy JSON `status`.
- Every previewable table is shown even at small n (approved default #1) — it is a pipeline
  preview, not inference; the caveat carries the honesty.
- Official weighted tables excluded; no preview claims a committed weighted number.
- Atomic writes (tempfile + `os.replace`); any missing input → exit nonzero, previous outputs stay.
- Runs in `/opt/venvs/spss` (pandas + openpyxl); hourly cron already installed
  (`7 * * * *`, flock `/tmp/csweb-tabulations.lock`).

## 5. Code structure

- Rework `csweb-tabulations-gen.py` into: input load + classify → Lane 1 tabulate → Lane 2 curated
  → F2 → package (xlsx + tidy JSON + manifest + public catalog).
- Extract shared plan-classification + DCF-label helpers into `tabulation_lib.py` **only if** the
  logic warrants it (keep the DCF label parse reusable with `csweb-spss-gen.py`; prefer importing
  the existing parser over duplicating it).
- stdlib + pandas + openpyxl only; no new on-box deps.

## 6. Deploy & verify

- `scp` the reworked gen (+ `tabulation_lib.py` if created) to `/opt/`; reuse on-box
  `/opt/spss-meta` codebooks and the already-present `/opt/tabulation-plan.csv`.
- Back up the current on-box gen; **md5-verify** worktree == prod after upload.
- Run once on box under the flock lock; confirm the workbooks, tidy JSON, manifest and public
  catalog regenerate; **headless-check** a workbook's sheet count/labels and validate the tidy JSON
  shape before calling it done.
- Do NOT overwrite any RA-owned data-room files; only the tabulations outputs + the gen change.

## 7. Success criteria

- ≥ ~118 previewable tables render with word-labeled categories and their committed breakdown,
  each labeled "Preview of Table X.Y" and tied to its plan `no`.
- Checkbox-multi marquee tables render as multiple-response tallies (≥ the LGU/accreditation set).
- F2 headline previews render from `values_json`.
- `tabulations-preview.json` + manifest expose per-table `status` and the preview→`table_no` map,
  ready for Phase 2.
- Catastrophic-expenditure tables are honestly `deferred`, not faked.
- All outputs stamped unweighted/pretest; official weighted lane untouched; 401 gate on the data
  room intact.

## 8. Open items / risks

- **DCF label parser reuse:** confirm the SPSS gen's parser is importable as-is (or extract cleanly)
  without pulling in pyreadstat-only code paths.
- **Multi-code width:** assumed 2-char fixed width from observed values; confirm against each
  checkbox field's value-set code width at implementation (some sets may be 2-digit throughout — if
  a field uses a different width, read it from the codebook rather than hard-coding 2).
- **Small pretest n** makes many cells 0–2; acceptable and caveated, but the tidy JSON should carry
  `n` so the Phase-2 viewer can visually de-emphasize tiny tables.
- **Phase 2** (page UX: collapsible annexes, search, in-page numbers, "preview ready" flags) is a
  separate spec that consumes `tabulations-preview.json`.

## 9. Related

- Memory: `project_aspsi_tabulation_list_ssrcs` (the 197-table SSRCS §II-9 catalog; ASPSI owns
  weighted production), `project_aspsi_csweb_reporting_layer`, `project_aspsi_capi_portal`,
  `project_aspsi_official_codebook`.
- Plan folder: `deliverables/tabulation-plan/` (`tabulation-plan.csv`, the CTP alignment doc,
  findings brief, decision tracker).
