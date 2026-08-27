# Fix evidence — F1 v4.1.3 (2026-08-27): #1322 Cebuano "Not applicable" fragment

Deployed 2026-08-27 14:16 MNL to `capi.asiansocial.org/csweb/api`. Logic (`.apc`) byte-identical to v4.1.1/4.1.2; two Cebuano
option labels changed in the dictionary (Q10.1 code 9, Q12.2 code 9 → English "Not applicable"), 24 stale Cebuano map keys retired.

| file | what it proves |
|---|---|
| `01-compile-successful-4.1.3.png` | fresh Designer compile, `Compile Successful at 14:12:37` |
| `02-deploy-dialog-files-4.1.3.png` | deploy dialog with the 8 PSGC files + `FacilityHeadSurvey.dcf` ticked, CSWeb target verified |
| `03-deploy-success-4.1.3.png` | `Application Deployed Successfully` |
| `served-package-4.1.3.txt` | served zip md5 `4d2a72bb3860c8efe4ee46df38da4558` (1 634 818 bytes), pff `v4.1.3 (2026-08-27) [DEV]`, apc unchanged |
| `byte-verify-4.1.3.txt` | served `.pen` bz2-decoded: `sa primary care facilities>` **0×**; Cebuano Q10.1 stem + code 1 present; footer v4.1.3 — `RESULT: ALL PASS` |
| `dcf-label-proof-1322.txt` | the whole `.dcf` diff vs 4.1.2 = the two `Not applicable` labels |
| `1322-desk-q10_1-options-CEB_code9-Not-applicable.png` | Windows CSEntry, Cebuano desk pff (`f1_1322_q10_1_ceb.txt`): Q10.1's option list — codes 1–5, 8 in Cebuano, **9 Not applicable** (English by design) |
| `1322-desk-q11-base-options-CEB.png` | next field, Q11 base (Oo / Wala) — the base questions have no code 9, so the 19 base-question keys were stale |
| `f1_1322_q10_1_ceb.txt` | the desk scenario (copy of `automation/scenarios/`), driven on the new `F1/FacilityHeadSurvey_desktest_CEB.pff` |

Desk frames are the Windows CSEntry engine (same logic and dictionary, not tablet chrome); Q10.1 sits past Section B
on a Cebuano case, beyond the tablet-navigation cap, so the proof is desk-engine + the served-package byte-verify.
Patch note: `deliverables/CSPro/patch-notes/2026-08-27-f1-v4.1.3-uat-1322.md`.
