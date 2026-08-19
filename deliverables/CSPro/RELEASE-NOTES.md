# CAPI Instrument Release Notes

> **GENERATED file - do not hand-edit.** Rebuild: `py automation/release_notes.py regen`
> (runs automatically on every `stamp_version.py bump/set`). Add richer bullets with
> `py automation/release_notes.py note F3 "..."` or `stamp_version.py bump F3 --notes "..."`;
> they live in `automation/release-notes-extra.json` and survive regeneration.
>
> Versions SSOT: `versions.json` (semver; PATCH = bug-fix deploy, MINOR = new/changed
> functionality, MAJOR = UAT round close / breaking change). History reconstructed from
> git history of versions.json (SSOT since 2026-07-02; earlier builds predate it).
>
> F2 PWA (separate lane): **v2.1.0** - notes in `deliverables/F2/PWA/app/CHANGELOG.md`
> (written by the milestone-close workflow `uat-release-notes.yml`).

## Current versions

| Instrument | Version | Date |
|---|---|---|
| F1 - Facility Head Survey | **v2.1.17** | 2026-08-18 |
| F3 - Patient Survey | **v4.0.0** | 2026-08-19 |
| F4 - Household Survey | **v3.0.1** | 2026-08-19 |
| HUB - Supervisor Hub | **v1.1.5** | 2026-08-08 |
| F2 - Healthcare Worker Survey (PWA) | **v2.1.0** | see F2 CHANGELOG |

## F1 - Facility Head Survey

### v2.1.17 - 2026-08-18 · `af9f87f`
- aug17: F3 v4.0.0 deployed

### v2.1.16 - 2026-08-17 · `0a93fe0`
- Adjudicate the blocked Bicolano backlog; rebuild the directive-notes layer; ship F1 v2.1.16 / F3 v3.1.13 / F4 v2.1.11

### v2.1.12 - 2026-08-17 · `c8b6ab2`
- Recover translations the extractor was dropping; ship F1 v2.1.12 / F3 v3.1.9

### v2.1.10 - 2026-08-15 · `a06dbd0`
- Build F1 v2.1.10 / F3 v3.1.8 / F4 v2.1.8 — ship the merged ICF placement

### v2.1.9 - 2026-08-15 · `ec4601c`
- CAPI translations: validator-gated pipeline, ship stems, clean stored values

### v1.2.2 - 2026-08-04 · `c322022`
- Sync Jul 15 - Aug 4 pretest-to-rollout work across CSPro, F2, CSWeb, and docs

### v1.1.4 - 2026-07-19 · `54484ed`
- Versions: F1 v1.1.4 / F3 v1.1.4 / F4 v1.4.4 - GPS warm-radio patch release

### v1.1.0 - 2026-07-14 · `b7501d3`
- Replacements: record them in CAPI and count them on the dashboard

### v1.0.3 - 2026-07-04 · `f3bd20f`
- F1/F3 #830 checkbox ascending-order fix + F4 #832/#833 amount-entry gate (parallel/loop sessions)

### v1.0.2 - 2026-07-02 · `b089212`
- Pretest sweep deploys via the `.csds` route: F1/F3 ship the 2026-07-02 #450-class pos() chunk-scan wave (v1.0.2); F4 v1.0.3 adds #824 Q56 no-benefits hard-exclusive + #827 Q90 skip flip (Yes→Q94; No→Q91–Q92→Q94 — reverses #652, matches skip-logic doc §I). Patch notes in all three UAT channels.
- Data layer (Option B) + R1a refactor; DHS benchmark ingest + gap analysis; fleet version sweep

### v1.0.1 - 2026-07-02 · `451a560`
- HUB versioning added (app list + menu footer), deployed via the new `supervisor-hub/LoginApp.csds`, device-verified (login → menu) + announced to #supervisor-uat.
- Build footer moved to the QN (first) screen — dict-first placement had landed on F3's case-end cover block. Device-verified + announced.
- feat(capi): CSEntry build versioning v1.0.1 + .csds deploy route; tabulation plan; R5 fix sweep

## F3 - Patient Survey

### v4.0.0 - 2026-08-19 · `af9f87f`
- Aug-17 PAPI alignment (full re-key, MAJOR): renumbered instrument; Quantified Free Service payment source (Q98/Q113); Q18 income brackets; outpatient/inpatient blocks front-loaded
- F3 MAJOR: Q18 income-bracket recode (11-band 50k -> Aug-17's 7-band PSA classes, DK/RF 99/98->8/9, reverses R4/#631), Q10 civil-status paper-code permutation fix, and the missing Q26 dug-well item inserted (renumbers Q26/27/28) -- all declared data-shape breaks; plus the Q1_IS_PATIENT->PATIENT_TYPE skip-retarget defect-fix (Section G/H outpatient/inpatient routing was silently broken for the Q1=Yes path on every build from v3.1.8/2026-08-15 through v3.1.14). Deployed to CSWeb (auto_deploy.py, "successfully" popup confirmed).
- aug17: F3 v4.0.0 deployed

### v3.1.13 - 2026-08-17 · `0a93fe0`
- Adjudicate the blocked Bicolano backlog; rebuild the directive-notes layer; ship F1 v2.1.16 / F3 v3.1.13 / F4 v2.1.11

### v3.1.9 - 2026-08-17 · `c8b6ab2`
- Recover translations the extractor was dropping; ship F1 v2.1.12 / F3 v3.1.9

### v3.1.8 - 2026-08-15 · `a06dbd0`
- Build F1 v2.1.10 / F3 v3.1.8 / F4 v2.1.8 — ship the merged ICF placement

### v3.1.7 - 2026-08-15 · `ec4601c`
- CAPI translations: validator-gated pipeline, ship stems, clean stored values

### v1.3.1 - 2026-08-04 · `c322022`
- Sync Jul 15 - Aug 4 pretest-to-rollout work across CSPro, F2, CSWeb, and docs

### v1.1.5 - 2026-07-19 · `8727ee8`
- F3 v1.1.5: Q162 closing-block fix - rebuilt artifacts + version stamp

### v1.1.4 - 2026-07-19 · `54484ed`
- Versions: F1 v1.1.4 / F3 v1.1.4 / F4 v1.4.4 - GPS warm-radio patch release

### v1.1.0 - 2026-07-14 · `b7501d3`
- Replacements: record them in CAPI and count them on the dashboard

### v1.0.6 - 2026-07-09 · `4b3cb14`
- Preserve in-progress CAPI work from the main checkout

### v1.0.3 - 2026-07-04 · `f3bd20f`
- F1/F3 #830 checkbox ascending-order fix + F4 #832/#833 amount-entry gate (parallel/loop sessions)

### v1.0.2 - 2026-07-02 · `b089212`
- Pretest sweep deploys via the `.csds` route: F1/F3 ship the 2026-07-02 #450-class pos() chunk-scan wave (v1.0.2); F4 v1.0.3 adds #824 Q56 no-benefits hard-exclusive + #827 Q90 skip flip (Yes→Q94; No→Q91–Q92→Q94 — reverses #652, matches skip-logic doc §I). Patch notes in all three UAT channels.
- Data layer (Option B) + R1a refactor; DHS benchmark ingest + gap analysis; fleet version sweep

### v1.0.1 - 2026-07-02 · `451a560`
- HUB versioning added (app list + menu footer), deployed via the new `supervisor-hub/LoginApp.csds`, device-verified (login → menu) + announced to #supervisor-uat.
- Build footer moved to the QN (first) screen — dict-first placement had landed on F3's case-end cover block. Device-verified + announced.
- feat(capi): CSEntry build versioning v1.0.1 + .csds deploy route; tabulation plan; R5 fix sweep

## F4 - Household Survey

### v3.0.1 - 2026-08-19 · `1a2fb94`
- F4 PATCH (corrective fix round, no data-shape break vs v3.0.0 which has no real collected cases yet): Q142 item 6 ("Other Donation/Charity/Assistance from Government Organization") was wrongly built with a specify-text field and a "Yes, specify:" tick label in v3.0.0, contradicting the reviewed ruling (item 6's label is category-descriptive, no write-in intended, same convention as Q133/Q134's "Other (Specify)" elsewhere in this paper) -- dropped the text field, tick label now plain "Yes". Also fixed a translation mis-key: all 7 locales stored Q76's "Not applicable" translation under the pre-migration value-set key (:9) instead of the post-migration key (:5), so it silently fell back to English in every language -- renamed the key (translated text byte-untouched) in all 7 files.
- aug17: F4 v3.0.1 corrective fix round 2 (Q142 item-6 + Q76 rekey)

### v3.0.0 - 2026-08-19 · `b721e7b`
- Aug-17 PAPI alignment (full re-key, MAJOR): Q139-143 bill-decomposition rewrite incl. 16-source Q142 matrix; GAMOT block Q69-78; roster code 13 Grandfather/Grandmother
- F4 MAJOR: Q139-143 hospital-bill module rewritten to the Aug-17 paper's restructured shape (Q139 total-bill amount, Q140 bill-items checklist, Q141 payment-recall gate, Q142 new 16-source settlement matrix, Q143 no-receipt amount) -- a declared data-shape break; GAMOT Q76/77/78 options restored (Don't know the difference/Not applicable, resolving #646-648); Q34 relationship gained Grandfather/Grandmother (code 15); and the missing Q26 dug-well item inserted (renumbers Q27/28/29, None added to Q24/Q25) -- same class as F3's v4.0.0 Q26 fix. Deployed to CSWeb (auto_deploy.py, "Application Deployed Successfully" popup confirmed); server-side byte-verify PASSED (bytes.find UTF-16LE on 9 new-content markers incl. the version string itself, against the decompressed .pen -- all found).
- aug17: F4 v3.0.0 deployed (Task 1.9)

### v2.2.0 - 2026-08-18 · `af9f87f`
- aug17: F3 v4.0.0 deployed

### v2.1.11 - 2026-08-17 · `0a93fe0`
- Adjudicate the blocked Bicolano backlog; rebuild the directive-notes layer; ship F1 v2.1.16 / F3 v3.1.13 / F4 v2.1.11

### v2.1.8 - 2026-08-15 · `a06dbd0`
- Build F1 v2.1.10 / F3 v3.1.8 / F4 v2.1.8 — ship the merged ICF placement

### v2.1.7 - 2026-08-15 · `ec4601c`
- CAPI translations: validator-gated pipeline, ship stems, clean stored values

### v1.5.0 - 2026-08-03 · `c322022`
- Sync Jul 15 - Aug 4 pretest-to-rollout work across CSPro, F2, CSWeb, and docs

### v1.4.4 - 2026-07-19 · `54484ed`
- Versions: F1 v1.1.4 / F3 v1.1.4 / F4 v1.4.4 - GPS warm-radio patch release

### v1.4.0 - 2026-07-14 · `33d1e3a`
- Merge worktree-f2-productivity-panel: replacements + monitoring into main

### v1.3.0 - 2026-07-14 · `b7501d3`
- Replacements: record them in CAPI and count them on the dashboard

### v1.3.2 - 2026-07-08 · `4b3cb14`
- Preserve in-progress CAPI work from the main checkout

### v1.2.2 - 2026-07-04 · `f3bd20f`
- F1/F3 #830 checkbox ascending-order fix + F4 #832/#833 amount-entry gate (parallel/loop sessions)

### v1.2.0 - 2026-07-04 · `d3b184a`
- R2 numbered messages + R3 fmf gates + Sprint 012 close (+ F4 Option C pilot from parallel session)

### v1.0.3 - 2026-07-03 · `b089212`
- Pretest sweep deploys via the `.csds` route: F1/F3 ship the 2026-07-02 #450-class pos() chunk-scan wave (v1.0.2); F4 v1.0.3 adds #824 Q56 no-benefits hard-exclusive + #827 Q90 skip flip (Yes→Q94; No→Q91–Q92→Q94 — reverses #652, matches skip-logic doc §I). Patch notes in all three UAT channels.
- Data layer (Option B) + R1a refactor; DHS benchmark ingest + gap analysis; fleet version sweep

### v1.0.1 - 2026-07-02 · `451a560`
- HUB versioning added (app list + menu footer), deployed via the new `supervisor-hub/LoginApp.csds`, device-verified (login → menu) + announced to #supervisor-uat.
- Build footer moved to the QN (first) screen — dict-first placement had landed on F3's case-end cover block. Device-verified + announced.
- feat(capi): CSEntry build versioning v1.0.1 + .csds deploy route; tabulation plan; R5 fix sweep

## HUB - Supervisor Hub

### v1.1.5 - 2026-08-08 · `ec4601c`
- CAPI translations: validator-gated pipeline, ship stems, clean stored values

### v1.1.4 - 2026-07-15 · `26fa7b4`
- Hub v1.1.4: say WHY an instrument won't open instead of "The Pff does not exist"

### v1.1.3 - 2026-07-15 · `54e3510`
- Hub v1.1.3: the coverage report was silently clobbering the assignment autoload

### v1.1.2 - 2026-07-15 · `69f2f48`
- Hub v1.1.2: auto-load each enumerator's assignment - no Bluetooth needed to start

### v1.1.1 - 2026-07-15 · `cdd7cad`
- One password per enumerator; stop committing the file that leaks them

### v1.1.0 - 2026-07-15 · `e6bc277`
- Hub v1.1.0: ship the pretest assignments the field will actually use

### v1.0.2 - 2026-07-14 · `33d1e3a`
- Merge worktree-f2-productivity-panel: replacements + monitoring into main

### v1.0.1 - 2026-07-03 · `b7501d3`
- Replacements: record them in CAPI and count them on the dashboard

### v1.0.2 - 2026-07-14 · `4b3cb14`
- Preserve in-progress CAPI work from the main checkout

### v1.0.1 - 2026-07-03 · `b089212`
- Data layer (Option B) + R1a refactor; DHS benchmark ingest + gap analysis; fleet version sweep

