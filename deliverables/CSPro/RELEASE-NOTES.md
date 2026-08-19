# CAPI Instrument Release Notes

All notable changes to the CSEntry CAPI instruments - **F1** Facility Head Survey,
**F3** Patient Survey, **F4** Household Survey, and the **Supervisor Hub** - written
for the people who use them: testers, field staff, and data users.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), adapted
to this multi-instrument repo (one section per instrument, one entry per released
version, newest first). Versioning follows [Semantic Versioning](https://semver.org/):
**PATCH** = bug-fix deploy · **MINOR** = new/changed functionality · **MAJOR** = UAT
round close or a breaking change; entries flagged **BREAKING** change the collected
data's shape. Dates are ISO (YYYY-MM-DD) deploy dates from `versions.json` (the
version SSOT, tracked since 2026-07-02 - earlier builds predate it).

> **GENERATED file - do not hand-edit.** Rebuild: `py automation/release_notes.py regen`
> (runs automatically on every `stamp_version.py bump/set`). Curated notes live in
> `automation/release-notes-extra.json` - add them with
> `py automation/release_notes.py note F3 [--type fixed|added|...] [--breaking] "..."`
> or `stamp_version.py bump F3 --notes "..."` (typed by bump kind). Entries without
> curated notes fall back to their release commit's subject.
>
> Plain-language lane for field staff: `WHATS-NEW.md` + the portal page
> [capi.asiansocial.org/projects/uhc-y2/whats-new](https://capi.asiansocial.org/projects/uhc-y2/whats-new/)
> (`whatsnew` bullets in the same overlay; auto-published on every bump).
>
> F2 PWA (separate lane): **v2.1.0** - notes in `deliverables/F2/PWA/app/CHANGELOG.md`
> (written by the milestone-close workflow `uat-release-notes.yml`).

## Current versions

| Instrument | Version | Deployed |
|---|---|---|
| F1 - Facility Head Survey | **v3.0.0** | 2026-08-19 |
| F3 - Patient Survey | **v4.0.1** | 2026-08-19 |
| F4 - Household Survey | **v3.0.2** | 2026-08-19 |
| HUB - Supervisor Hub | **v1.1.5** | 2026-08-08 |
| F2 - Healthcare Worker Survey (PWA) | **v2.1.0** | see F2 CHANGELOG |

## Unreleased

- **F3 v4.0.1** (2026-08-19) - bumped in the working tree, not yet committed
  - Fixed: On-screen question de-duplication (R25): form field captions are now short question tags, so the question text appears once per screen instead of twice. Display only.
- **F4 v3.0.2** (2026-08-19) - bumped in the working tree, not yet committed
  - Fixed: On-screen question de-duplication (R25): form field captions are now short question tags, so the question text appears once per screen instead of twice. Display only.

## F1 - Facility Head Survey

### [v3.0.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/af9f87f5c5c62463b9bf9025437c1db581e4c7fc...88249604fd4bdf378931ca788794956b807a38f3) - 2026-08-19 · MAJOR · **BREAKING** (data shape)
#### Changed
- Aug-17 instrument rebuild, end to end. Renumbered to the 2026-08-17 printed questionnaire (Q1-Q153). Section C's 18 nine-option UHC9 items become a 23-pair two-step battery (Yes/No base + a Q<NN>.1 UHC-attribution probe on its own screen, seven with a .2 detail item); Sections D-H shift by -13. New content: the GAMOT stock-out block, the DOH-IS submission fan, the PHO protocol pair, and 18 probes. Consent gains the 4-paragraph certificate and SJREB/ASPSI contact block, byte-identical to F3/F4. Two routing defect-fixes: Q68-Q71 had NO exit at all (a 'haven't thought about it yet' respondent was walked through two other branches' questions) and Q137=Yes orphaned the Q139/Q140 PHO pair for every satisfied respondent. MAJOR version - the data shape breaks against v2.x.
_Release commit [`8824960`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/88249604fd4bdf378931ca788794956b807a38f3): aug17: F1 v3.0.0 deployed_

### [v2.1.17](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/0a93fe0f2103b7093353607875626740d8f2a2da...af9f87f5c5c62463b9bf9025437c1db581e4c7fc) - 2026-08-18 · PATCH
- aug17: F3 v4.0.0 deployed ([`af9f87f`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/af9f87f5c5c62463b9bf9025437c1db581e4c7fc))

### [v2.1.16](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/c8b6ab22377bbf318100d20437aaf062848a3180...0a93fe0f2103b7093353607875626740d8f2a2da) - 2026-08-17 · PATCH
- Adjudicate the blocked Bicolano backlog; rebuild the directive-notes layer; ship F1 v2.1.16 / F3 v3.1.13 / F4 v2.1.11 ([`0a93fe0`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/0a93fe0f2103b7093353607875626740d8f2a2da))

### [v2.1.12](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/a06dbd0b7d6cac6f9d656318cecb02426cf76d2e...c8b6ab22377bbf318100d20437aaf062848a3180) - 2026-08-17 · PATCH
- Recover translations the extractor was dropping; ship F1 v2.1.12 / F3 v3.1.9 ([`c8b6ab2`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/c8b6ab22377bbf318100d20437aaf062848a3180))

### [v2.1.10](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/ec4601c533f07b754e20f8488c303c5b2a5ec3ad...a06dbd0b7d6cac6f9d656318cecb02426cf76d2e) - 2026-08-15 · PATCH
- Build F1 v2.1.10 / F3 v3.1.8 / F4 v2.1.8 — ship the merged ICF placement ([`a06dbd0`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/a06dbd0b7d6cac6f9d656318cecb02426cf76d2e))

### [v2.1.9](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/c3220227be43bf5c53f9d31181c6fdbb4e061432...ec4601c533f07b754e20f8488c303c5b2a5ec3ad) - 2026-08-15 · MAJOR
- CAPI translations: validator-gated pipeline, ship stems, clean stored values ([`ec4601c`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/ec4601c533f07b754e20f8488c303c5b2a5ec3ad))

### [v1.2.2](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/54484ed8782244dba1d392c50f9d09a38c18d77c...c3220227be43bf5c53f9d31181c6fdbb4e061432) - 2026-08-04 · MINOR
- Sync Jul 15 - Aug 4 pretest-to-rollout work across CSPro, F2, CSWeb, and docs ([`c322022`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/c3220227be43bf5c53f9d31181c6fdbb4e061432))

### [v1.1.4](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/b7501d3b5fb3eccd57272c3589c8eec99216f2a9...54484ed8782244dba1d392c50f9d09a38c18d77c) - 2026-07-19 · PATCH
- Versions: F1 v1.1.4 / F3 v1.1.4 / F4 v1.4.4 - GPS warm-radio patch release ([`54484ed`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/54484ed8782244dba1d392c50f9d09a38c18d77c))

### [v1.1.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/f3bd20f8a0d27c65d55ccd5ed35a75e98022a45d...b7501d3b5fb3eccd57272c3589c8eec99216f2a9) - 2026-07-14 · MINOR
- Replacements: record them in CAPI and count them on the dashboard ([`b7501d3`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/b7501d3b5fb3eccd57272c3589c8eec99216f2a9))

### [v1.0.3](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/b089212a2f2a1e2b28605c1d27a6d96e883f666c...f3bd20f8a0d27c65d55ccd5ed35a75e98022a45d) - 2026-07-04 · PATCH
- F1/F3 [#830](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/830) checkbox ascending-order fix + F4 [#832](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/832)/[#833](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/833) amount-entry gate (parallel/loop sessions) ([`f3bd20f`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/f3bd20f8a0d27c65d55ccd5ed35a75e98022a45d))

### [v1.0.2](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/451a5608255479822056382fddde990567d77bf2...b089212a2f2a1e2b28605c1d27a6d96e883f666c) - 2026-07-02 · PATCH
#### Fixed
- Pretest sweep deploys via the `.csds` route: F1/F3 ship the 2026-07-02 [#450](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/450)-class pos() chunk-scan wave (v1.0.2); F4 v1.0.3 adds [#824](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/824) Q56 no-benefits hard-exclusive + [#827](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/827) Q90 skip flip (Yes→Q94; No→Q91–Q92→Q94 — reverses [#652](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/652), matches skip-logic doc §I). Patch notes in all three UAT channels.
_Release commit [`b089212`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/b089212a2f2a1e2b28605c1d27a6d96e883f666c): Data layer (Option B) + R1a refactor; DHS benchmark ingest + gap analysis; fleet version sweep_

### [v1.0.1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/451a5608255479822056382fddde990567d77bf2) - 2026-07-02 · baseline
#### Added
- HUB versioning added (app list + menu footer), deployed via the new `supervisor-hub/LoginApp.csds`, device-verified (login → menu) + announced to #supervisor-uat.
#### Fixed
- Build footer moved to the QN (first) screen — dict-first placement had landed on F3's case-end cover block. Device-verified + announced.
_Release commit [`451a560`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/451a5608255479822056382fddde990567d77bf2): feat(capi): CSEntry build versioning v1.0.1 + .csds deploy route; tabulation plan; R5 fix sweep_

## F3 - Patient Survey

### [v4.0.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/0a93fe0f2103b7093353607875626740d8f2a2da...af9f87f5c5c62463b9bf9025437c1db581e4c7fc) - 2026-08-19 · MAJOR · **BREAKING** (data shape)
#### Changed
- Aug-17 PAPI alignment (full re-key, MAJOR): renumbered instrument; Quantified Free Service payment source (Q98/Q113); Q18 income brackets; outpatient/inpatient blocks front-loaded
- F3 MAJOR: Q18 income-bracket recode (11-band 50k -> Aug-17's 7-band PSA classes, DK/RF 99/98->8/9, reverses R4/[#631](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/631)), Q10 civil-status paper-code permutation fix, and the missing Q26 dug-well item inserted (renumbers Q26/27/28) -- all declared data-shape breaks; plus the Q1_IS_PATIENT->PATIENT_TYPE skip-retarget defect-fix (Section G/H outpatient/inpatient routing was silently broken for the Q1=Yes path on every build from v3.1.8/2026-08-15 through v3.1.14). Deployed to CSWeb (auto_deploy.py, "successfully" popup confirmed).
_Release commit [`af9f87f`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/af9f87f5c5c62463b9bf9025437c1db581e4c7fc): aug17: F3 v4.0.0 deployed_

### [v3.1.13](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/c8b6ab22377bbf318100d20437aaf062848a3180...0a93fe0f2103b7093353607875626740d8f2a2da) - 2026-08-17 · PATCH
- Adjudicate the blocked Bicolano backlog; rebuild the directive-notes layer; ship F1 v2.1.16 / F3 v3.1.13 / F4 v2.1.11 ([`0a93fe0`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/0a93fe0f2103b7093353607875626740d8f2a2da))

### [v3.1.9](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/a06dbd0b7d6cac6f9d656318cecb02426cf76d2e...c8b6ab22377bbf318100d20437aaf062848a3180) - 2026-08-17 · PATCH
- Recover translations the extractor was dropping; ship F1 v2.1.12 / F3 v3.1.9 ([`c8b6ab2`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/c8b6ab22377bbf318100d20437aaf062848a3180))

### [v3.1.8](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/ec4601c533f07b754e20f8488c303c5b2a5ec3ad...a06dbd0b7d6cac6f9d656318cecb02426cf76d2e) - 2026-08-15 · PATCH
- Build F1 v2.1.10 / F3 v3.1.8 / F4 v2.1.8 — ship the merged ICF placement ([`a06dbd0`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/a06dbd0b7d6cac6f9d656318cecb02426cf76d2e))

### [v3.1.7](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/c3220227be43bf5c53f9d31181c6fdbb4e061432...ec4601c533f07b754e20f8488c303c5b2a5ec3ad) - 2026-08-15 · MAJOR
- CAPI translations: validator-gated pipeline, ship stems, clean stored values ([`ec4601c`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/ec4601c533f07b754e20f8488c303c5b2a5ec3ad))

### [v1.3.1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/8727ee828235e3472da040234291df846783d2e6...c3220227be43bf5c53f9d31181c6fdbb4e061432) - 2026-08-04 · MINOR
- Sync Jul 15 - Aug 4 pretest-to-rollout work across CSPro, F2, CSWeb, and docs ([`c322022`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/c3220227be43bf5c53f9d31181c6fdbb4e061432))

### [v1.1.5](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/54484ed8782244dba1d392c50f9d09a38c18d77c...8727ee828235e3472da040234291df846783d2e6) - 2026-07-19 · PATCH
- F3 v1.1.5: Q162 closing-block fix - rebuilt artifacts + version stamp ([`8727ee8`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/8727ee828235e3472da040234291df846783d2e6))

### [v1.1.4](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/b7501d3b5fb3eccd57272c3589c8eec99216f2a9...54484ed8782244dba1d392c50f9d09a38c18d77c) - 2026-07-19 · PATCH
- Versions: F1 v1.1.4 / F3 v1.1.4 / F4 v1.4.4 - GPS warm-radio patch release ([`54484ed`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/54484ed8782244dba1d392c50f9d09a38c18d77c))

### [v1.1.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/4b3cb14c6b315f25976d84399124cf7fc6fcf343...b7501d3b5fb3eccd57272c3589c8eec99216f2a9) - 2026-07-14 · MINOR
- Replacements: record them in CAPI and count them on the dashboard ([`b7501d3`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/b7501d3b5fb3eccd57272c3589c8eec99216f2a9))

### [v1.0.6](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/f3bd20f8a0d27c65d55ccd5ed35a75e98022a45d...4b3cb14c6b315f25976d84399124cf7fc6fcf343) - 2026-07-09 · PATCH
- Preserve in-progress CAPI work from the main checkout ([`4b3cb14`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/4b3cb14c6b315f25976d84399124cf7fc6fcf343))

### [v1.0.3](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/b089212a2f2a1e2b28605c1d27a6d96e883f666c...f3bd20f8a0d27c65d55ccd5ed35a75e98022a45d) - 2026-07-04 · PATCH
- F1/F3 [#830](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/830) checkbox ascending-order fix + F4 [#832](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/832)/[#833](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/833) amount-entry gate (parallel/loop sessions) ([`f3bd20f`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/f3bd20f8a0d27c65d55ccd5ed35a75e98022a45d))

### [v1.0.2](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/451a5608255479822056382fddde990567d77bf2...b089212a2f2a1e2b28605c1d27a6d96e883f666c) - 2026-07-02 · PATCH
#### Fixed
- Pretest sweep deploys via the `.csds` route: F1/F3 ship the 2026-07-02 [#450](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/450)-class pos() chunk-scan wave (v1.0.2); F4 v1.0.3 adds [#824](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/824) Q56 no-benefits hard-exclusive + [#827](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/827) Q90 skip flip (Yes→Q94; No→Q91–Q92→Q94 — reverses [#652](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/652), matches skip-logic doc §I). Patch notes in all three UAT channels.
_Release commit [`b089212`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/b089212a2f2a1e2b28605c1d27a6d96e883f666c): Data layer (Option B) + R1a refactor; DHS benchmark ingest + gap analysis; fleet version sweep_

### [v1.0.1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/451a5608255479822056382fddde990567d77bf2) - 2026-07-02 · baseline
#### Added
- HUB versioning added (app list + menu footer), deployed via the new `supervisor-hub/LoginApp.csds`, device-verified (login → menu) + announced to #supervisor-uat.
#### Fixed
- Build footer moved to the QN (first) screen — dict-first placement had landed on F3's case-end cover block. Device-verified + announced.
_Release commit [`451a560`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/451a5608255479822056382fddde990567d77bf2): feat(capi): CSEntry build versioning v1.0.1 + .csds deploy route; tabulation plan; R5 fix sweep_

## F4 - Household Survey

### [v3.0.1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/b721e7bb389783136f79fd424b57dab6fe590abc...1a2fb94f7b18f991229f9bd10ce76467b111123b) - 2026-08-19 · PATCH
#### Fixed
- F4 PATCH (corrective fix round, no data-shape break vs v3.0.0 which has no real collected cases yet): Q142 item 6 ("Other Donation/Charity/Assistance from Government Organization") was wrongly built with a specify-text field and a "Yes, specify:" tick label in v3.0.0, contradicting the reviewed ruling (item 6's label is category-descriptive, no write-in intended, same convention as Q133/Q134's "Other (Specify)" elsewhere in this paper) -- dropped the text field, tick label now plain "Yes". Also fixed a translation mis-key: all 7 locales stored Q76's "Not applicable" translation under the pre-migration value-set key (:9) instead of the post-migration key (:5), so it silently fell back to English in every language -- renamed the key (translated text byte-untouched) in all 7 files.
_Release commit [`1a2fb94`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/1a2fb94f7b18f991229f9bd10ce76467b111123b): aug17: F4 v3.0.1 corrective fix round 2 (Q142 item-6 + Q76 rekey)_

### [v3.0.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/af9f87f5c5c62463b9bf9025437c1db581e4c7fc...b721e7bb389783136f79fd424b57dab6fe590abc) - 2026-08-19 · MAJOR · **BREAKING** (data shape)
#### Changed
- Aug-17 PAPI alignment (full re-key, MAJOR): Q139-143 bill-decomposition rewrite incl. 16-source Q142 matrix; GAMOT block Q69-78; roster code 13 Grandfather/Grandmother
- F4 MAJOR: Q139-143 hospital-bill module rewritten to the Aug-17 paper's restructured shape (Q139 total-bill amount, Q140 bill-items checklist, Q141 payment-recall gate, Q142 new 16-source settlement matrix, Q143 no-receipt amount) -- a declared data-shape break; GAMOT Q76/77/78 options restored (Don't know the difference/Not applicable, resolving [#646](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/646)-648); Q34 relationship gained Grandfather/Grandmother (code 15); and the missing Q26 dug-well item inserted (renumbers Q27/28/29, None added to Q24/Q25) -- same class as F3's v4.0.0 Q26 fix. Deployed to CSWeb (auto_deploy.py, "Application Deployed Successfully" popup confirmed); server-side byte-verify PASSED (bytes.find UTF-16LE on 9 new-content markers incl. the version string itself, against the decompressed .pen -- all found).
_Release commit [`b721e7b`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/b721e7bb389783136f79fd424b57dab6fe590abc): aug17: F4 v3.0.0 deployed (Task 1.9)_

### [v2.2.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/0a93fe0f2103b7093353607875626740d8f2a2da...af9f87f5c5c62463b9bf9025437c1db581e4c7fc) - 2026-08-18 · MINOR
- aug17: F3 v4.0.0 deployed ([`af9f87f`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/af9f87f5c5c62463b9bf9025437c1db581e4c7fc))

### [v2.1.11](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/a06dbd0b7d6cac6f9d656318cecb02426cf76d2e...0a93fe0f2103b7093353607875626740d8f2a2da) - 2026-08-17 · PATCH
- Adjudicate the blocked Bicolano backlog; rebuild the directive-notes layer; ship F1 v2.1.16 / F3 v3.1.13 / F4 v2.1.11 ([`0a93fe0`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/0a93fe0f2103b7093353607875626740d8f2a2da))

### [v2.1.8](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/ec4601c533f07b754e20f8488c303c5b2a5ec3ad...a06dbd0b7d6cac6f9d656318cecb02426cf76d2e) - 2026-08-15 · PATCH
- Build F1 v2.1.10 / F3 v3.1.8 / F4 v2.1.8 — ship the merged ICF placement ([`a06dbd0`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/a06dbd0b7d6cac6f9d656318cecb02426cf76d2e))

### [v2.1.7](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/c3220227be43bf5c53f9d31181c6fdbb4e061432...ec4601c533f07b754e20f8488c303c5b2a5ec3ad) - 2026-08-15 · MAJOR
- CAPI translations: validator-gated pipeline, ship stems, clean stored values ([`ec4601c`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/ec4601c533f07b754e20f8488c303c5b2a5ec3ad))

### [v1.5.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/54484ed8782244dba1d392c50f9d09a38c18d77c...c3220227be43bf5c53f9d31181c6fdbb4e061432) - 2026-08-03 · MINOR
- Sync Jul 15 - Aug 4 pretest-to-rollout work across CSPro, F2, CSWeb, and docs ([`c322022`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/c3220227be43bf5c53f9d31181c6fdbb4e061432))

### [v1.4.4](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/33d1e3aaf03c9c7c9b6d5e712cf79fcce7ebb0e2...54484ed8782244dba1d392c50f9d09a38c18d77c) - 2026-07-19 · PATCH
- Versions: F1 v1.1.4 / F3 v1.1.4 / F4 v1.4.4 - GPS warm-radio patch release ([`54484ed`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/54484ed8782244dba1d392c50f9d09a38c18d77c))

### [v1.4.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/b7501d3b5fb3eccd57272c3589c8eec99216f2a9...33d1e3aaf03c9c7c9b6d5e712cf79fcce7ebb0e2) - 2026-07-14 · MINOR
- Merge worktree-f2-productivity-panel: replacements + monitoring into main ([`33d1e3a`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/33d1e3aaf03c9c7c9b6d5e712cf79fcce7ebb0e2))

### [v1.3.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/4b3cb14c6b315f25976d84399124cf7fc6fcf343...b7501d3b5fb3eccd57272c3589c8eec99216f2a9) - 2026-07-14 · PATCH
- Replacements: record them in CAPI and count them on the dashboard ([`b7501d3`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/b7501d3b5fb3eccd57272c3589c8eec99216f2a9))

### [v1.3.2](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/f3bd20f8a0d27c65d55ccd5ed35a75e98022a45d...4b3cb14c6b315f25976d84399124cf7fc6fcf343) - 2026-07-08 · MINOR
- Preserve in-progress CAPI work from the main checkout ([`4b3cb14`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/4b3cb14c6b315f25976d84399124cf7fc6fcf343))

### [v1.2.2](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/d3b184a0bfe7afb0354c0e0c2e87e47b46c67f47...f3bd20f8a0d27c65d55ccd5ed35a75e98022a45d) - 2026-07-04 · PATCH
- F1/F3 [#830](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/830) checkbox ascending-order fix + F4 [#832](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/832)/[#833](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/833) amount-entry gate (parallel/loop sessions) ([`f3bd20f`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/f3bd20f8a0d27c65d55ccd5ed35a75e98022a45d))

### [v1.2.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/b089212a2f2a1e2b28605c1d27a6d96e883f666c...d3b184a0bfe7afb0354c0e0c2e87e47b46c67f47) - 2026-07-04 · MINOR
- R2 numbered messages + R3 fmf gates + Sprint 012 close (+ F4 Option C pilot from parallel session) ([`d3b184a`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/d3b184a0bfe7afb0354c0e0c2e87e47b46c67f47))

### [v1.0.3](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/451a5608255479822056382fddde990567d77bf2...b089212a2f2a1e2b28605c1d27a6d96e883f666c) - 2026-07-03 · PATCH
#### Fixed
- Pretest sweep deploys via the `.csds` route: F1/F3 ship the 2026-07-02 [#450](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/450)-class pos() chunk-scan wave (v1.0.2); F4 v1.0.3 adds [#824](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/824) Q56 no-benefits hard-exclusive + [#827](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/827) Q90 skip flip (Yes→Q94; No→Q91–Q92→Q94 — reverses [#652](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/652), matches skip-logic doc §I). Patch notes in all three UAT channels.
_Release commit [`b089212`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/b089212a2f2a1e2b28605c1d27a6d96e883f666c): Data layer (Option B) + R1a refactor; DHS benchmark ingest + gap analysis; fleet version sweep_

### [v1.0.1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/451a5608255479822056382fddde990567d77bf2) - 2026-07-02 · baseline
#### Added
- HUB versioning added (app list + menu footer), deployed via the new `supervisor-hub/LoginApp.csds`, device-verified (login → menu) + announced to #supervisor-uat.
#### Fixed
- Build footer moved to the QN (first) screen — dict-first placement had landed on F3's case-end cover block. Device-verified + announced.
_Release commit [`451a560`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/451a5608255479822056382fddde990567d77bf2): feat(capi): CSEntry build versioning v1.0.1 + .csds deploy route; tabulation plan; R5 fix sweep_

## HUB - Supervisor Hub

### [v1.1.5](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/26fa7b4eb966e83a9452d265e37fd2c49d81fdeb...ec4601c533f07b754e20f8488c303c5b2a5ec3ad) - 2026-08-08 · PATCH
- CAPI translations: validator-gated pipeline, ship stems, clean stored values ([`ec4601c`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/ec4601c533f07b754e20f8488c303c5b2a5ec3ad))

### [v1.1.4](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/54e3510ecc916d1bd76287a84d3be08f1ca93af3...26fa7b4eb966e83a9452d265e37fd2c49d81fdeb) - 2026-07-15 · PATCH
- Hub v1.1.4: say WHY an instrument won't open instead of "The Pff does not exist" ([`26fa7b4`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/26fa7b4eb966e83a9452d265e37fd2c49d81fdeb))

### [v1.1.3](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/69f2f48f418c57ff6fc874001f02c5ee6f49e7bf...54e3510ecc916d1bd76287a84d3be08f1ca93af3) - 2026-07-15 · PATCH
- Hub v1.1.3: the coverage report was silently clobbering the assignment autoload ([`54e3510`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/54e3510ecc916d1bd76287a84d3be08f1ca93af3))

### [v1.1.2](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/cdd7cad6fa62bddfa88fad0d87c103d3e6a489e6...69f2f48f418c57ff6fc874001f02c5ee6f49e7bf) - 2026-07-15 · PATCH
- Hub v1.1.2: auto-load each enumerator's assignment - no Bluetooth needed to start ([`69f2f48`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/69f2f48f418c57ff6fc874001f02c5ee6f49e7bf))

### [v1.1.1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/e6bc277338fa5ceb5129d943e00c3dfa20dc16dc...cdd7cad6fa62bddfa88fad0d87c103d3e6a489e6) - 2026-07-15 · PATCH
- One password per enumerator; stop committing the file that leaks them ([`cdd7cad`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/cdd7cad6fa62bddfa88fad0d87c103d3e6a489e6))

### [v1.1.0](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/33d1e3aaf03c9c7c9b6d5e712cf79fcce7ebb0e2...e6bc277338fa5ceb5129d943e00c3dfa20dc16dc) - 2026-07-15 · MINOR
- Hub v1.1.0: ship the pretest assignments the field will actually use ([`e6bc277`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/e6bc277338fa5ceb5129d943e00c3dfa20dc16dc))

### [v1.0.2](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/b7501d3b5fb3eccd57272c3589c8eec99216f2a9...33d1e3aaf03c9c7c9b6d5e712cf79fcce7ebb0e2) - 2026-07-14 · PATCH
- Merge worktree-f2-productivity-panel: replacements + monitoring into main ([`33d1e3a`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/33d1e3aaf03c9c7c9b6d5e712cf79fcce7ebb0e2))

### [v1.0.1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/4b3cb14c6b315f25976d84399124cf7fc6fcf343...b7501d3b5fb3eccd57272c3589c8eec99216f2a9) - 2026-07-03 · PATCH
- Replacements: record them in CAPI and count them on the dashboard ([`b7501d3`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/b7501d3b5fb3eccd57272c3589c8eec99216f2a9))

### [v1.0.2](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/compare/b089212a2f2a1e2b28605c1d27a6d96e883f666c...4b3cb14c6b315f25976d84399124cf7fc6fcf343) - 2026-07-14 · PATCH
- Preserve in-progress CAPI work from the main checkout ([`4b3cb14`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/4b3cb14c6b315f25976d84399124cf7fc6fcf343))

### [v1.0.1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/b089212a2f2a1e2b28605c1d27a6d96e883f666c) - 2026-07-03 · baseline
- Data layer (Option B) + R1a refactor; DHS benchmark ingest + gap analysis; fleet version sweep ([`b089212`](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/commit/b089212a2f2a1e2b28605c1d27a6d96e883f666c))
