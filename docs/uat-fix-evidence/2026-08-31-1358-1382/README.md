# Fix evidence — F3 v6.1.5 (2026-08-31): #1358–#1382 Ilocano Sections B–E + Cebuano Section B (one batched build)

Deployed 2026-08-31 14:32 MNL to `capi.asiansocial.org/csweb/api`. Logic (`.apc`) byte-identical to v6.1.2–6.1.4
(md5 `a0fb214b7868753260bb71737b2da5df`); 67 dictionary labels changed (CEB 26, ILO 37, the Q4 name label in FIL/BCL/BIS/WAR)
plus 23 note cells (section intros, notes-to-enumerator, definitions, directives) rendered through the `.qsf`.

| file | what it proves |
|---|---|
| `01-compile-successful-6.1.5.png` | fresh Designer compile, `Compile Successful at 14:28:12` |
| `02-deploy-dialog-files-6.1.5.png` | deploy dialog with the 8 PSGC files + `PatientSurvey.dcf` ticked, CSWeb target verified |
| `03-deploy-success-6.1.5.png` | `Application Deployed Successfully` |
| `served-package-6.1.5.txt` | served zip md5, pff `v6.1.5 (2026-08-31) [DEV]`, apc unchanged |
| `byte-verify-6.1.5.txt` | served `.pen` bz2-decoded: CEB Q4/Q14/Q19, ILO Q4/Q14/Q19/Q47/Q54:2/Q58, FIL/BCL/BIS/WAR Q4 probes present, footer v6.1.5 — `RESULT: ALL PASS` |
| `dcf-label-proof-1358-1382.txt` | the whole `.dcf` label diff vs v6.1.4 = the 67 labels of this build |
| `1358-desk-introB-q4-ILO.png` / `1362-desk-introB-q4-CEB.png` | Section B read-aloud intro on the Q4 screen in Ilocano / Cebuano (the ILO screen used to read `information (Sakbay … ) Note to enumerator …`); the note-to-enumerator is the second banner line |
| `1359-desk-q5-month-ILO.png`, `1359-desk-q5-year-ILO.png` / `1364-desk-q5-*-CEB.png` | Q5 month and year boxes: paper question + box label (`— Bulan` / `— Tawen`; `— Buwan` / `— Tuig`) |
| `1360-desk-q14-ILO.png` / `1370-desk-q14-CEB.png` | Q14 PWD-card question stem + option list; the PWD-card enumerator instruction is the second banner line |
| `1361-desk-q15-options-ILO.png` | Q15 popup: rows 02/03 without the stray parentheses, 05/06 in Ilocano |
| `1363-desk-q16-options-ILO.png` | Q16 popup: row 2 *Adda ababa a panawen, panawen, kassual a trabaho/negosio* |
| `1365-desk-q18-amount-ILO.png`, `1365-desk-q18-bracket-ILO.png`, `1365-desk-q19-ILO.png` | Q18 amount stem, Q18 bracket screen (label + its enumerator note), Q19 stem (+ def:19 note) |
| `1366-desk-q8-CEB.png`, `1368-desk-q9-CEB.png` | Q8 stem without the glued English directive (the READ-ONE directive is the Cebuano second banner line), Q9 stem |
| `1373-desk-q15-CEB.png`, `1375-desk-q16-CEB.png`, `1377-desk-q17-CEB.png` | Q15/Q16/Q17 stems in Cebuano (options were already Cebuano); Q17's extended directive is the second banner line |
| `1379-desk-q18-amount-CEB.png`, `1379-desk-q18-bracket-CEB.png`, `1381-desk-q19-CEB.png` | Q18 amount stem, Q18 bracket, Q19 stem (+ def:19) |
| `1367-desk-q33-ILO.png` | Q33 stem + options (pilot-jump walk) |
| `1382-desk-q34-CEB.png` | Q34 stem + options; the directive + definition (def:34) is the second banner line |
| `1369-desk-introC-q35-ILO.png` / `proactive-desk-introC-q35-CEB.png` | Section C intro on the Q35 screen (note def:35 on the second line) |
| `1371-desk-q47-physician-ILO.png`, `1371-desk-q47-diagnostic-ILO.png` | Q47 battery: shared stem + per-item label |
| `1372-desk-q50-ILO.png` | Q50 stem (no stray parenthesis) + Check Box popup |
| `1374-desk-introE-q53-ILO.png` / `proactive-desk-introE-q53-CEB.png` | Section E intro on the Q53 screen, Q53 stem in the popup title |
| `1376-desk-q54-options-ILO.png` / `proactive-desk-q54-options-CEB.png` | Q54 options 1/2 |
| `1378-desk-q58-days-ILO.png`, `1378-desk-q58-minutes-ILO.png` | Q58 Days / Minutes stems |
| `1380-desk-q59-ILO.png` | Q59 stem + options 01/03/04; SELECT-ALL directive on the second banner line |
| `proactive-desk-q47-physician-CEB.png` | Q47 CEB battery (fixed on sight, same class) |
| `f3_1362_sectionB_ceb.txt`, `f3_1358_sectionB_ilo.txt` | the Section B walks (sequential, no pilot) |
| `f3_pilot_q33_*.txt`, `f3_pilot_q47_*.txt` | the Sections C–E walks — **pilot-jump builds** (`F3_PILOT_JUMP=Q33_DECISION_MAKER` / `Q47_PHYSICIAN_CHECKUP`, desk-only apc), regenerated clean and md5-checked after the captures; the labels these frames show are the ones in the served package (byte-verify) |

Desk frames are the Windows CSEntry engine (same logic and dictionary as the tablet, not tablet chrome). The question banner shows
its first line in full and clips the second (note) line — every note cell is also proven by the `.qsf` text and the byte-verify.
Patch note: `deliverables/CSPro/patch-notes/2026-08-31-f3-v6.1.5-uat-1358-1382.md`.
