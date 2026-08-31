# Fix evidence — F1 v4.1.9 (2026-08-31): #1355 + #1357 Cebuano Section G (Q129 stem, Q142 enumerator note)

Deployed 2026-08-31 14:51 MNL to `capi.asiansocial.org/csweb/api`. Logic (`.apc`) byte-identical to v4.1.1–4.1.8
(md5 `f548f8e81b4defd3897f559f419a31fe`); 1 Cebuano dictionary label changed (Q129) and 1 note cell added (def:142, rendered through the `.qsf`).
#1356 (Q135 = No lands on Q141) was closed as designed — Q139/Q140 are gated to public hospitals (Q7 = Public and Q8 = Level 1/2/3 Hospital) per the paper — no build change.

| file | what it proves |
|---|---|
| `01-compile-successful-4.1.9.png` | fresh Designer compile, `Compile Successful at 14:47:10` |
| `02-deploy-dialog-files-4.1.9.png` | deploy dialog with the 8 PSGC files + `FacilityHeadSurvey.dcf` ticked, CSWeb target verified |
| `03-deploy-success-4.1.9.png` | `Application Deployed Successfully` |
| `served-package-4.1.9.txt` | served zip md5, pff `v4.1.9 (2026-08-31) [DEV]`, apc unchanged |
| `byte-verify-4.1.9.txt` | served `.pen` bz2-decoded: CEB Q129 present, the def:142 Cebuano sentence occurs 1×, footer v4.1.9 — `RESULT: ALL PASS` |
| `dcf-label-proof-1355.txt` | the whole `.dcf` label diff vs v4.1.8 = the one Cebuano Q129 label |
| `1355-desk-q129-CEB.png` | Windows CSEntry, Cebuano desk pff (pilot-jump build): Q129 banner *Ngano man nga gitugotan sa pasilidad ang OOP expenses para sa basic accommodation?* |
| `1357-desk-q142-note-CEB.png` | Q142 screen: the Cebuano question with the Cebuano enumerator note (*Ang atong focus kay sa mga referral … BASAHA UG KUSOG …*) under it |
| `pilot-landing-q128-CEB.png` | the pilot jump landing on Q128 (Q128 = Yes → Q129) |
| `f1_1355_sectionG_pilot_ceb.txt` | the scenario — **pilot-jump build**: `F1_PILOT_JUMP=Q128_ALLOW_OOP_BASIC` desk-only apc (a Q1 postproc `skip to Q128`), regenerated clean and md5-checked after the capture; the label/note these frames show are the ones in the served package (byte-verify) |

Desk frames are the Windows CSEntry engine (same logic and dictionary, not tablet chrome); Section G sits ~200 fields in, beyond the
tablet-navigation cap, so the proof is desk-engine + the served-package byte-verify.
Patch note: `deliverables/CSPro/patch-notes/2026-08-31-f1-v4.1.9-uat-1355-1357.md`.
