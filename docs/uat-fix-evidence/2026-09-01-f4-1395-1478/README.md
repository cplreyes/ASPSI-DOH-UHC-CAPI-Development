# UAT R7 fix evidence — Household Survey (F4) v4.0.3, tickets #1395–#1478 (43 tickets), 2026-09-01

Build chain on the day: v4.0.0 (Carl's #840 major) → v4.0.1 (the wave) → v4.0.2 (Ilocano Q4/Q5 stems) → v4.0.3 (15 keys forced per locale: Ilocano Q29/Q31/Q34/Q39/Q89, Tagalog Q17). **v4.0.3 is the served build.** Patch note: `deliverables/CSPro/patch-notes/2026-09-01-f4-v4.0.3-uat-1395-1478.md`.

## What each file is

**Build + deploy record** (one set per build on the day; the highest version is the one served):

- `01-compile-successful-4.0.1.png`
- `01-compile-successful-4.0.2.png`
- `01-compile-successful-4.0.3.png`
- `02-deploy-dialog-files-4.0.1.png`
- `02-deploy-dialog-files-4.0.2.png`
- `02-deploy-dialog-files-4.0.3.png`
- `03-deploy-progress-4.0.2.png`
- `03-deploy-progress-4.0.3.png`
- `03-deploy-success-4.0.1.png`
- `byte-verify-4.0.1.txt`
- `byte-verify-4.0.2.txt`
- `byte-verify-4.0.3.txt`
- `map-write-proof-4.0.1.txt`
- `map-write-proof-4.0.3.txt`

- `01-compile-successful-<ver>.png` — the fresh Designer compile (Ctrl+L) that preceded the publish.
- `02-deploy-dialog-files-<ver>.png` — the CSPro Deploy Application dialog after `auto_deploy.py` added the 8 PSGC files (package name locked to this instrument).
- `03-deploy-success-<ver>.png` / `03-deploy-progress-<ver>.png` — the driver's last frame of the deploy (`Application Deployed Successfully` / the upload in progress); the driver's own log line `result: deploy succeeded` and the byte-verify below are the proof the package landed.
- `byte-verify-<ver>.txt` — the served `<App>.zip` pulled from CSWeb, its `.pen` bz2-decompressed and every wave-changed map value searched as UTF-16LE bytes; `OK` = present. The `RESULT: FAIL` line is the tool's all-seven-locales rule (locales the wave did not write carry no wave-changed probe) — read the per-probe lines and the `0 FAIL` count.
- `map-write-proof-<ver>.txt` — the `apply_aug21.py --apply` record, one line per key written/removed.

**Desk-engine frames** (`<ticket>-desk-<question>_<LOCALE>.png`, Windows CSEntry on the instrument's `<App>_desktest_<LOC>.pff` — the same CSPro engine as the tablet, not tablet chrome; captured by `automation/csentry_runner.py` from the scenario files copied here):

- Ilocano + Tagalog Section B walks (`f4_wave0901_sectionB_{ilo,fil}.txt`): frames `1395…1400-desk-*_ILO.png`, `1456…1462-desk-*_FIL.png` — sequential from the pretest case key 040341101001 (ICF → BREAKOFF → CLASSIFICATION → barangay), no pilot build; the Ilocano Q4/Q5 frames were retaken on v4.0.2.
- Sections C–P (#1401–#1414, #1463–#1478) are proven by the byte-verify of the served package + the render cards; no desk walk was scripted for the roster/expenditure sections.

20 frames: `1395-desk-name_ILO.png`, `1395-desk-q2_month_ILO.png`, `1395-desk-q2_year_ILO.png`, `1396-desk-q4_ILO.png`, `1397-desk-q5_ILO.png`, `1398-desk-q10_ILO.png`, `1399-desk-q12_ILO.png`, `1400-desk-q18_amount_ILO.png`, `1400-desk-q18_bracket_ILO.png`, `1400-desk-q19_ILO.png`, `1456-desk-name_FIL.png`, `1456-desk-q2_month_FIL.png`, `1456-desk-q2_year_FIL.png`, `1457-desk-q4_FIL.png`, `1458-desk-q5_FIL.png`, `1459-desk-q10_FIL.png`, `1460-desk-q12_FIL.png`, `1462-desk-q18_amount_FIL.png`, `1462-desk-q18_bracket_FIL.png`, `1462-desk-q19_FIL.png`

**Deployed-content render cards** (`<ticket>-render-<INST>-<LOC>.png`, 43 cards — one per ticket): the built dictionary labels of the served v4.0.3 package (English vs the ticket's language) for every key the ticket covers, plus the note cells it concerns. Clearly stamped *DEPLOYED-CONTENT RENDER — not a device capture*; these are the lower evidence tier for tickets without a desk frame. A card row that reads *(no locale label - renders the English above)* is a row that stays English by rule (paper prints English / no distinct translation) — see the patch note's *Not changed* list.

## Per-ticket index

| ticket | locale | scope | map keys written | rows removed (→ English) | evidence tier |
|---|---|---|---|---|---|
| #1395 | ILO | F4_ILOCANO_Section B_Name&Q2 | 3 | 0 | desk frame + render |
| #1396 | ILO | F4_ILOCANO_Section B_Q4 | 3 | 0 | desk frame + render |
| #1397 | ILO | F4_ILOCANO_Section B_Q5 | 2 | 0 | desk frame + render |
| #1398 | ILO | F4_ILOCANO_Section B_Q10 | 2 | 0 | desk frame + render |
| #1399 | ILO | F4_ILOCANO_Section B_Q12 | 2 | 0 | desk frame + render |
| #1400 | ILO | F4_ILOCANO_Section B_Q18&Q19 | 4 | 0 | desk frame + render |
| #1401 | ILO | F4_ILOCANO_Section B_Q29 | 3 | 0 | render card |
| #1402 | ILO | F4_ILOCANO_WHOLE SECTION C | 52 | 0 | render card |
| #1403 | ILO | F4_ILOCANO_Section G_Q65 | 3 | 2 | render card |
| #1404 | ILO | F4_ILOCANO_Section G_Q66&67 | 4 | 0 | render card |
| #1405 | ILO | F4_ILOCANO_Section G_Q70-Q73 | 5 | 0 | render card |
| #1406 | ILO | F4_ILOCANO_Section G_Q78 | 1 | 0 | render card |
| #1407 | ILO | F4_ILOCANO_Section I_Q89 | 1 | 0 | render card |
| #1408 | ILO | F4_ILOCANO_Section I_Q95&96 | 2 | 0 | render card |
| #1409 | ILO | F4_ILOCANO_Section K_Q118 | 0 | 0 | render card (no map change — see note) |
| #1410 | ILO | F4_ILOCANO_Section K_Q123 | 2 | 0 | render card |
| #1411 | ILO | F4_ILOCANO_Section M_Q139 | 1 | 0 | render card |
| #1412 | ILO | F4_ILOCANO_SECTION N_HOUSEHOLD EXPENDITURE | 42 | 0 | render card |
| #1413 | ILO | F4_ILOCANO_Section O_Q196 | 2 | 0 | render card |
| #1414 | ILO | F4_ILOCANO_Section P_Q197 | 2 | 0 | render card |
| #1456 | FIL | F4_TAGALOG_Section B_Q2 | 2 | 0 | desk frame + render |
| #1457 | FIL | F4_TAGALOG_Section B_Q4 | 2 | 0 | desk frame + render |
| #1458 | FIL | F4_TAGALOG_Section B_Q5 | 2 | 0 | desk frame + render |
| #1459 | FIL | F4_TAGALOG_Section B_Q10 | 1 | 0 | desk frame + render |
| #1460 | FIL | F4_TAGALOG_Section B_Q12 | 1 | 0 | desk frame + render |
| #1461 | FIL | F4_TAGALOG_Section B_Q17 | 1 | 0 | render card |
| #1462 | FIL | F4_TAGALOG_Section B_Q18&Q19 | 4 | 1 | desk frame + render |
| #1463 | FIL | F4_TAGALOG_WHOLE SECTION C | 21 | 0 | render card |
| #1464 | FIL | F4_TAGALOG_Section G_Q65 | 2 | 3 | render card |
| #1465 | FIL | F4_TAGALOG_Section G_Q67 | 2 | 0 | render card |
| #1466 | FIL | F4_TAGALOG_Section G_Q70 | 1 | 1 | render card |
| #1467 | FIL | F4_TAGALOG_Section G_Q71 | 1 | 0 | render card |
| #1468 | FIL | F4_TAGALOG_Section G_Q72&Q73 | 2 | 0 | render card |
| #1469 | FIL | F4_TAGALOG_Section G_Q78 | 1 | 0 | render card |
| #1470 | FIL | F4_TAGALOG_Section I_Q95&96 | 2 | 0 | render card |
| #1471 | FIL | F4_TAGALOG_Section K_Q117 | 1 | 0 | render card |
| #1472 | FIL | F4_TAGALOG_Section K_Q118 | 2 | 0 | render card |
| #1473 | FIL | F4_TAGALOG_Section M_Q136 | 2 | 0 | render card |
| #1474 | FIL | F4_TAGALOG_Section M_Q139 | 1 | 0 | render card |
| #1475 | FIL | F4_TAGALOG_Section M_Q141&142 | 21 | 0 | render card |
| #1476 | FIL | F4_TAGALOG_Section M_Q143 | 1 | 0 | render card |
| #1477 | FIL | F4_TAGALOG_SECTION N-HOUSEHOLD EXPENDITURE | 33 | 0 | render card |
| #1478 | FIL | F4_TAGALOG_Section O_Q186 | 0 | 0 | render card (no map change — see note) |

Scenario files: `f4_wave0901_sectionB_fil.txt`, `f4_wave0901_sectionB_ilo.txt`.

Capture tier: the itel tablet was not connected and the `capi_tablet` AVD was not used for this wave (the pilot cases on it are labelled DO NOT SYNC); tier 3 (desk engine) and tier 4 (render) as the skill allows, stated on every ticket comment.
