# UAT R7 fix evidence — Facility Head Survey (F1) v5.0.1, tickets #1415–#1425 (10 tickets), 2026-09-01

Build chain on the day: v5.0.0 (Carl's #840 major + 4.1.10 tenure fix) → v5.0.1 (the wave). **v5.0.1 is the served build.** Patch note: `deliverables/CSPro/patch-notes/2026-09-01-f1-v5.0.1-uat-1415-1425.md`.

## What each file is

**Build + deploy record** (one set per build on the day; the highest version is the one served):

- `01-compile-successful-5.0.1.png`
- `02-deploy-dialog-files-5.0.1.png`
- `03-deploy-success-5.0.1.png`
- `byte-verify-5.0.1.txt`
- `map-write-proof-5.0.1.txt`

- `01-compile-successful-<ver>.png` — the fresh Designer compile (Ctrl+L) that preceded the publish.
- `02-deploy-dialog-files-<ver>.png` — the CSPro Deploy Application dialog after `auto_deploy.py` added the 8 PSGC files (package name locked to this instrument).
- `03-deploy-success-<ver>.png` / `03-deploy-progress-<ver>.png` — the driver's last frame of the deploy (`Application Deployed Successfully` / the upload in progress); the driver's own log line `result: deploy succeeded` and the byte-verify below are the proof the package landed.
- `byte-verify-<ver>.txt` — the served `<App>.zip` pulled from CSWeb, its `.pen` bz2-decompressed and every wave-changed map value searched as UTF-16LE bytes; `OK` = present. The `RESULT: FAIL` line is the tool's all-seven-locales rule (locales the wave did not write carry no wave-changed probe) — read the per-probe lines and the `0 FAIL` count.
- `map-write-proof-<ver>.txt` — the `apply_aug21.py --apply` record, one line per key written/removed.

**Desk-engine frames** (`<ticket>-desk-<question>_<LOCALE>.png`, Windows CSEntry on the instrument's `<App>_desktest_<LOC>.pff` — the same CSPro engine as the tablet, not tablet chrome; captured by `automation/csentry_runner.py` from the scenario files copied here):

- Tagalog Section D walk (`f1_wave0901_sectionD_fil.txt`): frames `1418-desk-q43_FIL.png`, `1418-desk-q44_FIL.png`, `1419-desk-q45_FIL.png`, `1420-desk-q49_FIL.png`, `1420-desk-q50_FIL.png` — DESK-ONLY pilot-jump build (`F1_PILOT_JUMP=Q43_YK_REG_BOTH`); the apc was regenerated clean and md5-checked (`1cd2cbb99e7efb8b20abeebeffc4efdc`) — the pilot build was never deployed. Q43 reads English by design (paper prints it in English).

5 frames: `1418-desk-q43_FIL.png`, `1418-desk-q44_FIL.png`, `1419-desk-q45_FIL.png`, `1420-desk-q49_FIL.png`, `1420-desk-q50_FIL.png`

**Deployed-content render cards** (`<ticket>-render-<INST>-<LOC>.png`, 10 cards — one per ticket): the built dictionary labels of the served v5.0.1 package (English vs the ticket's language) for every key the ticket covers, plus the note cells it concerns. Clearly stamped *DEPLOYED-CONTENT RENDER — not a device capture*; these are the lower evidence tier for tickets without a desk frame. A card row that reads *(no locale label - renders the English above)* is a row that stays English by rule (paper prints English / no distinct translation) — see the patch note's *Not changed* list.

## Per-ticket index

| ticket | locale | scope | map keys written | rows removed (→ English) | evidence tier |
|---|---|---|---|---|---|
| #1415 | FIL | F1_TAGALOG_Section B_Q8 | 0 | 1 | render card |
| #1416 | FIL | F1_TAGALOG_Section C_Q30.1 | 2 | 0 | render card |
| #1417 | FIL | F1_TAGALOG_Section D_Q39 | 2 | 0 | render card |
| #1418 | FIL | F1_TAGALOG_Section D_Q43&Q44 | 1 | 0 | desk frame + render |
| #1419 | FIL | F1_TAGALOG_Section D_Q45 | 1 | 0 | desk frame + render |
| #1420 | FIL | F1_TAGALOG_Section D_Q49&Q50 | 2 | 0 | desk frame + render |
| #1421 | FIL | F1_TAGALOG_Section D_Q53-Q61 | 16 | 0 | render card |
| #1422 | FIL | F1_TAGALOG_Section F_Q107 | 1 | 0 | render card |
| #1423 | FIL | F1_TAGALOG_Section F_Q111-Q121 | 20 | 0 | render card |
| #1425 | FIL | F1_TAGALOG_Section G_Q127 | 3 | 0 | render card |

Scenario files: `f1_wave0901_sectionD_fil.txt`.

Capture tier: the itel tablet was not connected and the `capi_tablet` AVD was not used for this wave (the pilot cases on it are labelled DO NOT SYNC); tier 3 (desk engine) and tier 4 (render) as the skill allows, stated on every ticket comment.
