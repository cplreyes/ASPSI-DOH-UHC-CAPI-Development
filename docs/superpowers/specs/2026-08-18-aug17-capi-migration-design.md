# Aug-17 CAPI Migration — Design

**Date:** 2026-08-18 · **Status:** Approved by Carl (design presented in chat, "Approved as presented")
**Drives:** update of all four CAPI instruments (CSPro F1/F3/F4 + F2 PWA) from the Apr-20 baseline
(+June-5/UAT deltas) to the **Aug-17 updated survey instruments** — the consolidated outcome of the
pretest-results presentation (2026-08-17). English-first; translations follow in a later pass.

## Decision log (all Carl, 2026-08-18)

| # | Decision | Ruling |
|---|---|---|
| 1 | Deadline | **ASAP, no fixed date** — stage instrument-by-instrument, fastest safe delivery |
| 2 | Interim locales | **Keep carried-over translations + English fallback** for new/changed items |
| 3 | Paper defects | **Fix with documented interpretations**; ambiguous cardinality defaults to current build; one consolidated ASPSI clarification list in parallel (never block) |
| 4 | Inputs | **The four Aug-17 docx are the whole change set** (no separate presentation items) |
| 5 | Countercheck artifact | **Shareable crosswalk workbook + QA pack** (also the codebook/tabulation remap input) |
| 6 | Renumbering | **Option A — full re-key** to Aug-17 numbers (see `deliverables/CSPro/aug17-renumber-options.png`) |
| 7 | F1 consent/Secondary Data | Annex-packaged in the PAPI, **kept in the CAPI** (consent flow + Secondary Data records; Apr-20 module shape until ASPSI shares the annex) |

## Scope

**In:** English question text, options, notes/interviewer instructions, sectioning, numbering,
skip logic, validations, error/warning confirmations for F1/F2/F3/F4; the countercheck lane;
crosswalk + QA artifacts; codebook/DDI regeneration; CSWeb/PWA deployment of the new generation.

**Out (non-goals):** authoring translations (ASPSI delivers; only re-join + fallback wiring is in
scope); features beyond the paper; purging pretest data (keep-and-filter stands); redesigning the
consent/Secondary-Data capture (Apr-20 shape retained until the PAPI annex arrives); DOH comms
(Carl builds; ASPSI communicates).

## Source documents

- `raw/Survey-Instruments-2026-08-17/` (main checkout; immutable) — the four docx.
- Extraction + inventories: `deliverables/CSPro/instruments-aug17-extract/` (gitignored NDU
  derivative): `F{1..4}-extract.md` (pandoc, `{.mark}` spans = Year-2 edits), `F{1..4}-inventory.md`
  (full structural maps with line citations), `README.md`.
- Wiki synthesis: `wiki/sources/Source - Updated Survey Instruments (2026-08-17).md`.

## Architecture

### Lanes and waves

Two parallel lanes; verification gates every wave.

| Wave | Lane | Content | Why this order |
|---|---|---|---|
| 0 | shared | Normalized paper-side tables (all 4), crosswalk skeletons, ASPSI clarification list draft, divergence-register scaffold | Everything downstream consumes these |
| 1 | CSPro | **F3 + F4** — patch-scale: highlighted deltas, defect fixes, F3 front-load reorder | Fast wins; shakes down the countercheck machinery on small deltas before F1 relies on it |
| 2 | CSPro | **F1** — rebuild: full re-key, two-step battery (decimal subs), GAMOT + stock-outs, DOH-IS items, PHO probes, skip-logic rebuild, forms regen | Largest change; benefits from proven tooling |
| 3 (∥ 1–2) | PWA | **F2** — spec regen from Aug-17 inventory: re-key IDs, Section-B battery, cadre routing rewrite, E1/E2 split, Section-G gating, i18n re-join | Independent tech; runs beside the CSPro lane after Wave 0 |
| 4 | shared | Codebook + DDI regen, CSWeb dictionary updates (keep-and-filter cutover), versions stamped, smoke UAT + tablet evidence, ASPSI clarification list dispatched, translation work-order emitted | Closeout across instruments |

**Wave gate:** an instrument ships only when its crosswalk shows 100% of items at
verified status across all three tiers (§ Verification).

### Versioning — one "Aug-17 generation"

All four bump **MAJOR**: F1 → **3.0.0**, F3 → **4.0.0**, F4 → **3.0.0**, F2 PWA → **3.0.0**.
F1/F3/F4 stamped via `automation/stamp_version.py` from `versions.json` (SSOT — read current live
values from the **main checkout** at execution; the worktree copy lags, and the fleet is being
actively patched, so the plan re-baselines at its Task 0.1). F2 (not a versions.json instrument)
carries 3.0.0 in `package.json`/build-info, with the dated `LOCAL_SPEC_VERSION` as the client
force-update gate. Every screenshot and sync record then self-identifies its generation.
*(Amended 2026-08-18 after plan review.)*

### Re-key rules (Decision 6)

- Dictionary/item names follow Aug-17 numbers: `Q10_<STEM>`; decimal subs `Q10_1_<STEM>`;
  letter subs `Q71A_<STEM>`/`Q71B_<STEM>`; other-specify keeps `Q<NN>_<STEM>_OTHER_TXT`.
- Case IDs, the 12-digit PSGC case key, cover/geo structure, and lookup dictionaries do **not**
  re-key — data-shape identity of the case key is preserved.
- Value sets: codes verbatim from the paper, **ascending order** (checkbox-conversion rule);
  labels quote-sanitized (dcf-label quote crash) with byte-verified deploys.
- Translation re-join: CSPro locale stores are **name-scoped** since 2026-08-17 (`item:`/`vs:`/`val:` keys) — re-join moves keys per the item RENAME map, dropping reworded-English entries to fallback; the PWA store re-joins by **exact English match**. Never positional or longest-value re-key. *(Amended 2026-08-18 — the English-text-key description predated the name-scope migration.)*

### Source of truth and the countercheck engine

The change lane edits the existing generators (`F{n}/generate_dcf.py`, `generate_apc.py`,
`generate_qsf.py`; F2's spec → `src/generated` pipeline). The countercheck lane is **independent**:

1. **Paper-side table** per instrument, derived from the extracts: one row per item —
   new Q#, section, verbatim stem, options (code + verbatim label), notes/instructions,
   type/cardinality, skip rule, validation/range, error/warning text.
2. **Build-side table** parsed back out of the built artifacts (dcf + qsf + apc for CSPro;
   content dump for the PWA) into the same schema.
3. **Machine diff** at 100% item coverage: numbering, order, sectioning, stems, options,
   notes, cardinality — exact match modulo declared normalizations (whitespace, smart quotes,
   `~~field~~` fills).

**Approved-divergence register** (`instruments-aug17-extract/aug17-approved-divergences.md`):
every intentional paper↔build difference — defect fixes (Decision 3), CAPI adaptations (F3
front-load reorder per the paper's own "Note for CAPI Version", fills, computed `[DO NOT ASK]`
rows) — is an entry: instrument, item, class, paper text, build text, rationale. The diff **fails
on any difference not in the register**. Nothing drifts silently in either direction.

Paper-side tables and the register contain verbatim paper text → they live inside the gitignored
`instruments-aug17-extract/` folder, same NDU policy as the extracts.

### Crosswalk workbook (Decision 5)

`instruments-aug17-extract/aug17-crosswalk.xlsx` (shareable; delivered by file, not committed),
one sheet per instrument: old Q#/var name → new Q#/var name, change class
(unchanged / reworded / new / removed / renumbered-only), value-set delta, cardinality,
skip delta, and three verify-status columns (text, logic, desk) filled by the tiers.
Generated by script from the normalized tables + verify outputs — regenerable, never hand-edited.
Consumers: ASPSI/DOH change record, `generate_codebook.py` remap input, PSA-tabulation owner's
code remap, migration progress dashboard.

### Translation carry-over (Decision 2) *(mechanism amended 2026-08-18)*

CSPro locale stores migrated to **name-scoped keys** on 2026-08-17 (`_meta.format: name-scoped-v2`);
their re-join moves `item:`/`vs:`/`val:` keys per the item rename map and actively drops entries
whose English was reworded (a translation of superseded English must not show). The PWA store is
still English-text-keyed and re-joins by exact English match. Emit three lists per instrument:
**carried** (translation kept), **fell back** (English changed or codes shifted → English shown),
**new** (English only). The fell-back + new list is the ready-made ASPSI translation work order.
English text comes only from the Aug-17 paper — the translations-only-verbatim-English rule is
untouched.

## Per-instrument change surface (pointers)

Full maps in `F{n}-inventory.md`; synthesis in the wiki source page. Headlines:

- **F1** (rebuild): Q1–153 + 33 decimal subs; two-step UHC-attribution battery (C);
  GAMOT Q95–98 + stock-outs Q99–104; DOH-IS/Dashboard Q21–23; PHO probes Q139–140;
  Secondary Data + consent retained (Decision 7); 8 catalogued skip defects to fix.
- **F2** (PWA): Q1–124 continuous + subs; Section-B battery; pharmacists enter at E2;
  Section G physicians/dentists only via Q61/Q62; Q47 ZBB checklist; burnout retained;
  Apr-20 F2-Spec/skip docs stale — regenerate, don't patch; 8 ambiguous-cardinality lists
  default to current build (Decision 3).
- **F3** (patch): numbering stable; retitle; QFS payment source (Q98/Q113); Q18 income bands;
  None options; front-load G/H per the paper's CAPI note (registered divergence);
  broken `Q124-Q25` banner and Q159/Q162 gate defects fixed.
- **F4** (patch): numbering stable; Q139–143 bill-decomposition rewrite (16-source Q142, QFS,
  no ZBB line); GAMOT Q69–78; roster code 13; stale `'Yes' in 120` ref fixed (→Q45);
  sentinel families normalized to the locked missing-value standard (register the divergence).
- **Cross-cutting:** YAKAP/Konsulta dual branding everywhere; result-of-visit codes now differ
  per instrument (F1/F2 4-code; F3 6-code; F4 4-code no-Refused) → per-instrument
  BREAKOFF/CASE_DISPOSITION mapping tables; Php 100 token (F3/F4) + PhP 1,000 raffle (F2)
  consent mentions; shared consent Certificate with Paulyn Jean A. Claro contact block.

## Verification design (the countercheck lane)

| Tier | What | Tooling | Output |
|---|---|---|---|
| 1 — Text | Machine diff, 100% items, verbatim modulo register | new `aug17_diff.py` over paper/build tables | PASS/DIFF per item → crosswalk |
| 2 — Logic | Skip/validation matrix per instrument (paper rule → expected behavior), boundary + scenario execution; two-stage subagent review of generator diffs (explicit OUTPUT DISCIPLINE, line-anchored findings) | `skip_boundary_check.py`, `preflight_validate.py`, `csentry_runner/csentry_verify`, scenario matrix | logic status → crosswalk |
| 3 — Desk/tablet | Desk-test scenario matrix; tablet captures of big-change areas (F1 battery + GAMOT, F2 cadre routing, F3 payment matrices, F4 bill module); PWA vitest + Playwright e2e + a11y + locale shots | existing desk-test + uat-fix-evidence patterns → `docs/uat-fix-evidence/` | desk status → crosswalk |

Error/warning confirmations are first-class rows in the Tier-2 matrix: each validation carries its
expected severity (hard error vs warning-confirm) and message text, checked against the paper's
instructions or the registered interpretation.

## Deployment & cutover

- CSPro compile + deploy run from the **main checkout** (worktree PSGC compile trap): pywinauto
  compile driver → pen packaging → CSWeb publish gate; byte-verify uploads; paradata `.pff`
  switch preserved in regenerated .pffs; CSWeb stays 8.0.x (tandem rule). Autodeploy after
  compile-verify stands (standing instruction — no per-deploy asks).
- New-generation dictionaries go up under **keep-and-filter**: pretest cases remain server-side,
  filtered from operational reporting; no purge. Tester tablets get explicit fresh installs
  (CSEntry "Update Installed Applications" misses redeploys).
- F2 PWA: `tsc -b --force` before push; deploy **only** via `deploy-f2-pwa.ps1` (nginx
  `/opt/app/f2-www`); locale screenshots refreshed.
- GPS-last + warm-radio invariants and PROC-order independence respected through F1's form regen.

## Risks

| Risk | Mitigation |
|---|---|
| Re-key breaks a downstream consumer silently | Crosswalk is the single remap input; codebook/DDI regenerated from it; PSA-tabulation owner notified with the code map |
| Verbatim drift while re-typing paper text into generators | Tier-1 diff is independent of the change lane and fails on unregistered differences |
| Locale corruption during re-key | English-exact re-join only; carried/fell-back report audited; never longest-value re-key |
| Paper defect "fixed" into a new bug | Every fix is a register entry with rationale + ASPSI clarification item; two-stage review on generator diffs |
| Version confusion in the field | One-generation MAJOR bump; qsf footer + pff description stamped from versions.json |
| Worktree/main drift | Extraction+plan live in the worktree; compile/deploy and versions.json truth in main checkout; explicit sync step in the plan |

## Open items (planned tasks, non-blocking)

1. ASPSI clarification list (defects + cardinality defaults + BUCAS singular/plural etc.) —
   drafted Wave 0, dispatched Wave 4 (Carl sends via ASPSI channel).
2. Secondary Data PAPI annex — request via ASPSI; CAPI keeps Apr-20 module shape meanwhile.
3. Translation delivery — work order emitted from the re-join report; separate translation pass
  (existing pipeline) when ASPSI delivers.

## Artifacts index

- Decision diagram: `deliverables/CSPro/aug17-renumber-options.excalidraw` + `.png`
- Normalized tables, divergence register, crosswalk: `deliverables/CSPro/instruments-aug17-extract/`
- Evidence: `docs/uat-fix-evidence/<capture-date>-aug17-migration/` (dated per capture session, uat-fix-evidence convention)
- Implementation plan (next step): `docs/superpowers/plans/2026-08-18-aug17-capi-migration.md`
