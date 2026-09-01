# UAT R7 fix evidence — Patient Survey (F3) v7.0.3, tickets #1383–#1455 (43 tickets), 2026-09-01

Build chain on the day: v7.0.0 (Carl's #840 major) → v7.0.1 (the wave) → v7.0.2 (Ilocano Q149:06 + Q93:12) → v7.0.3 (Ilocano Q142 stem, per-locale force). **v7.0.3 is the served build.** Patch note: `deliverables/CSPro/patch-notes/2026-09-01-f3-v7.0.3-uat-1383-1455.md`.

## What each file is

**Build + deploy record** (one set per build on the day; the highest version is the one served):

- `01-compile-successful-7.0.1.png`
- `01-compile-successful-7.0.2.png`
- `01-compile-successful-7.0.3.png`
- `02-deploy-dialog-files-7.0.1.png`
- `02-deploy-dialog-files-7.0.2.png`
- `02-deploy-dialog-files-7.0.3.png`
- `03-deploy-progress-7.0.2.png`
- `03-deploy-progress-7.0.3.png`
- `03-deploy-success-7.0.1.png`
- `byte-verify-7.0.1.txt`
- `byte-verify-7.0.2.txt`
- `byte-verify-7.0.3.txt`
- `map-write-proof-7.0.1.txt`
- `map-write-proof-7.0.3.txt`

- `01-compile-successful-<ver>.png` — the fresh Designer compile (Ctrl+L) that preceded the publish.
- `02-deploy-dialog-files-<ver>.png` — the CSPro Deploy Application dialog after `auto_deploy.py` added the 8 PSGC files (package name locked to this instrument).
- `03-deploy-success-<ver>.png` / `03-deploy-progress-<ver>.png` — the driver's last frame of the deploy (`Application Deployed Successfully` / the upload in progress); the driver's own log line `result: deploy succeeded` and the byte-verify below are the proof the package landed.
- `byte-verify-<ver>.txt` — the served `<App>.zip` pulled from CSWeb, its `.pen` bz2-decompressed and every wave-changed map value searched as UTF-16LE bytes; `OK` = present. The `RESULT: FAIL` line is the tool's all-seven-locales rule (locales the wave did not write carry no wave-changed probe) — read the per-probe lines and the `0 FAIL` count.
- `map-write-proof-<ver>.txt` — the `apply_aug21.py --apply` record, one line per key written/removed.

**Desk-engine frames** (`<ticket>-desk-<question>_<LOCALE>.png`, Windows CSEntry on the instrument's `<App>_desktest_<LOC>.pff` — the same CSPro engine as the tablet, not tablet chrome; captured by `automation/csentry_runner.py` from the scenario files copied here):

- Cebuano Section B–D walk (`f3_wave0901_sectionCD_ceb.txt`): frames `1424-desk-q36-CEB.png` … `1437-desk-q48-CEB.png`, `1427-desk-introC-q35-CEB.png`, `1427-desk-introD-q38-CEB.png` — sequential from the case key, no pilot build.
- Ilocano + Tagalog Section G / J / K walks (`f3_wave0901_section{G,J,K}_{ilo,fil}.txt`): frames `13xx-desk-*_ILO.png` / `14xx-desk-*_FIL.png` — DESK-ONLY pilot-jump builds (`F3_PILOT_JUMP=Q92_SOURCES` / `Q131_AMEN_WAITING` / `Q148_CONDITIONS` at `generate_apc.py` time); the apc was regenerated clean and md5-checked (`ae6f26453f37191bcc561f14b85e1d97`) before every deploy — no pilot build was ever deployed.

59 frames: `1383-desk-q92_pay_amt_ILO.png`, `1383-desk-q92_sources_ILO.png`, `1384-desk-q94_lab_amt_ILO.png`, `1384-desk-q94_lab_pay_ILO.png`, `1385-desk-q96_pay_amt_ILO.png`, `1385-desk-q96_sources_ILO.png`, `1386-desk-q971_pay_amt_ILO.png`, `1386-desk-q971_sources_ILO.png`, `1386-desk-q97_final_ILO.png`, `1387-desk-q131_ILO.png`, `1387-desk-q132_ILO.png`, `1387-desk-q133_ILO.png`, `1387-desk-q134_ILO.png`, `1388-desk-q136_ILO.png`, `1388-desk-q137_ILO.png`, `1388-desk-q138_ILO.png`, `1388-desk-q139_ILO.png`, `1388-desk-q140_ILO.png`, `1389-desk-q142_ILO.png`, `1390-desk-q144_ILO.png`, `1391-desk-q148_ILO.png`, `1392-desk-q150_hh_ILO.png`, `1392-desk-q150_mm_ILO.png`, `1393-desk-q156_ILO.png`, `1424-desk-q36-CEB.png`, `1426-desk-q37-CEB.png`, `1427-desk-introC-q35-CEB.png`, `1427-desk-introD-q38-CEB.png`, `1429-desk-q39-CEB.png`, `1430-desk-q40-CEB.png`, `1431-desk-q41-CEB.png`, `1433-desk-q42-CEB.png`, `1434-desk-q45-CEB.png`, `1435-desk-q46-CEB.png`, `1437-desk-q48-CEB.png`, `1445-desk-q92_pay_amt_FIL.png`, `1445-desk-q92_sources_FIL.png`, `1447-desk-q94_lab_amt_FIL.png`, `1447-desk-q94_lab_pay_FIL.png`, `1448-desk-q96_pay_amt_FIL.png`, `1448-desk-q96_sources_FIL.png`, `1449-desk-q971_pay_amt_FIL.png`, `1449-desk-q971_sources_FIL.png`, `1449-desk-q97_final_FIL.png`, `1450-desk-q131_FIL.png`, `1450-desk-q132_FIL.png`, `1450-desk-q133_FIL.png`, `1450-desk-q134_FIL.png`, `1451-desk-q136_FIL.png`, `1451-desk-q137_FIL.png`, `1451-desk-q138_FIL.png`, `1451-desk-q139_FIL.png`, `1451-desk-q140_FIL.png`, `1452-desk-q142_FIL.png`, `1452-desk-q144_FIL.png`, `1453-desk-q148_FIL.png`, `1454-desk-q150_hh_FIL.png`, `1454-desk-q150_mm_FIL.png`, `1455-desk-q156_FIL.png`

**Deployed-content render cards** (`<ticket>-render-<INST>-<LOC>.png`, 43 cards — one per ticket): the built dictionary labels of the served v7.0.3 package (English vs the ticket's language) for every key the ticket covers, plus the note cells it concerns. Clearly stamped *DEPLOYED-CONTENT RENDER — not a device capture*; these are the lower evidence tier for tickets without a desk frame. A card row that reads *(no locale label - renders the English above)* is a row that stays English by rule (paper prints English / no distinct translation) — see the patch note's *Not changed* list.

## Per-ticket index

| ticket | locale | scope | map keys written | rows removed (→ English) | evidence tier |
|---|---|---|---|---|---|
| #1383 | ILO | F3_ILOCANO_Section G_Q92 | 5 | 0 | desk frame + render |
| #1384 | ILO | F3_ILOCANO_Section G_Q94 | 4 | 1 | desk frame + render |
| #1385 | ILO | F3_ILOCANO_Section G_Q96 | 4 | 0 | desk frame + render |
| #1386 | ILO | F3_ILOCANO_Section G_Q97 | 5 | 0 | desk frame + render |
| #1387 | ILO | F3_ILOCANO_Section J_Q131-Q134 | 8 | 0 | desk frame + render |
| #1388 | ILO | F3_ILOCANO_Section J_Q136-Q140 | 25 | 0 | desk frame + render |
| #1389 | ILO | F3_ILOCANO_Section J_Q142 | 1 | 0 | desk frame + render |
| #1390 | ILO | F3_ILOCANO_Section J_Q144 | 2 | 0 | desk frame + render |
| #1391 | ILO | F3_ILOCANO_Section K_Q148 | 3 | 1 | desk frame + render |
| #1392 | ILO | F3_ILOCANO_Section K_Q150 | 2 | 0 | desk frame + render |
| #1393 | ILO | F3_ILOCANO_Section K_Q156 | 1 | 0 | desk frame + render |
| #1394 | ILO | F3_ILOCANO_Section L_Q175 | 2 | 0 | render card |
| #1424 | CEB | F3_Cebuano_Section B_Q36 | 1 | 0 | desk frame + render |
| #1426 | CEB | F3_Cebuano_Section C_Q37 | 1 | 0 | desk frame + render |
| #1427 | CEB | F3_Cebuano_Q38 | 0 | 0 | desk frame + render (no map change — see note) |
| #1428 | FIL | F3_TAGALOG_Section B_Q5 | 2 | 0 | render card |
| #1429 | CEB | F3_Cebuano_Section D_Q39 | 1 | 0 | desk frame + render |
| #1430 | CEB | F3_Cebuano_Section D_Q40 | 2 | 0 | desk frame + render |
| #1431 | CEB | F3_Cebuano_Section D_Q41 | 1 | 0 | desk frame + render |
| #1432 | FIL | F3_TAGALOG_Section B_Q18&Q19 | 2 | 0 | render card |
| #1433 | CEB | F3_Cebuano_Section D_Q42 | 2 | 0 | desk frame + render |
| #1434 | CEB | F3_Cebuano_Section D_Q45 | 2 | 0 | desk frame + render |
| #1435 | CEB | F3_Cebuano_Section D_Q46 | 1 | 0 | desk frame + render |
| #1436 | FIL | F3_TAGALOG_Section C_Q36 | 2 | 0 | render card |
| #1437 | CEB | F3_Cebuano_Section D_Q48 | 1 | 0 | desk frame + render |
| #1438 | FIL | F3_TAGALOG_Section D_Q38.1 | 2 | 0 | render card |
| #1439 | FIL | F3_TAGALOG_Section D_Q40 | 2 | 0 | render card |
| #1440 | FIL | F3_TAGALOG_Section D_Q47 | 8 | 0 | render card |
| #1441 | FIL | F3_TAGALOG_Section E_Q58 | 2 | 0 | render card |
| #1442 | FIL | F3_TAGALOG_Section E_Q60-Q62 | 4 | 0 | render card |
| #1443 | FIL | F3_TAGALOG_Section E_Q69 | 1 | 0 | render card |
| #1444 | FIL | F3_TAGALOG_Section E_Q70&Q71 | 3 | 0 | render card |
| #1445 | FIL | F3_TAGALOG_Section G_Q92 | 3 | 0 | desk frame + render |
| #1446 | FIL | F3_TAGALOG_Section G_Q93 | 0 | 1 | render card |
| #1447 | FIL | F3_TAGALOG_Section G_Q94 | 3 | 1 | desk frame + render |
| #1448 | FIL | F3_TAGALOG_Section G_Q96 | 2 | 0 | desk frame + render |
| #1449 | FIL | F3_TAGALOG_Section G_Q97 | 4 | 0 | desk frame + render |
| #1450 | FIL | F3_TAGALOG_Section J_Q131-Q134 | 8 | 0 | desk frame + render |
| #1451 | FIL | F3_TAGALOG_Section J_Q136-Q140 | 10 | 0 | desk frame + render |
| #1452 | FIL | F3_TAGALOG_Section J_Q141-Q144 | 5 | 0 | desk frame + render |
| #1453 | FIL | F3_TAGALOG_Section K_Q148 | 1 | 1 | desk frame + render |
| #1454 | FIL | F3_TAGALOG_Section K_Q150 | 2 | 0 | desk frame + render |
| #1455 | FIL | F3_TAGALOG_Section K_Q156 | 1 | 0 | desk frame + render |

Scenario files: `f3_wave0901_sectionCD_ceb.txt`, `f3_wave0901_sectionG_fil.txt`, `f3_wave0901_sectionG_ilo.txt`, `f3_wave0901_sectionJ_fil.txt`, `f3_wave0901_sectionJ_ilo.txt`, `f3_wave0901_sectionK_fil.txt`, `f3_wave0901_sectionK_ilo.txt`.

Capture tier: the itel tablet was not connected and the `capi_tablet` AVD was not used for this wave (the pilot cases on it are labelled DO NOT SYNC); tier 3 (desk engine) and tier 4 (render) as the skill allows, stated on every ticket comment.
