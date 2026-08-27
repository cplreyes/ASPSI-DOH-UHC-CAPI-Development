# Fix evidence — F1 v4.1.6 (2026-08-27): #1328 #1329 #1330 #1331 #1332 #1333 #1334 Ilocano Section D/E labels (batched)

Deployed 2026-08-27 16:12 MNL to `capi.asiansocial.org/csweb/api`. Logic (`.apc`) byte-identical to v4.1.1–4.1.5
(md5 `f548f8e81b4defd3897f559f419a31fe`); 42 dictionary labels changed (24 Ilocano stems + 18 option rows, incl. the Q62 option-02/05 cleanup in all
seven locales.

| file | what it proves |
|---|---|
| `01-compile-successful-4.1.6.png` | fresh Designer compile, `Compile Successful at 16:08:22` |
| `02-deploy-dialog-files-4.1.6.png` | deploy dialog with the 8 PSGC files + `FacilityHeadSurvey.dcf` ticked, CSWeb target verified |
| `03-deploy-success-4.1.6.png` | `Application Deployed Successfully` |
| `served-package-4.1.6.txt` | served zip md5 `48d7e62bd0efcd74688fa864ee3aaea5` (1 636 740 bytes), pff `v4.1.6 (2026-08-27) [DEV]`, apc unchanged |
| `byte-verify-4.1.6.txt` | served `.pen` bz2-decoded: all ten Ilocano probe keys present, `Month, Day, Year` / `ken/wenno)` / `b(Pannakaammo` 0×, 16× `Apay a narigat ti agtungpal kadagiti: `, footer v4.1.6 — `RESULT: ALL PASS` (92 OK / 0 MISS) |
| `dcf-label-proof-1328-1334.txt` | the whole `.dcf` label diff vs v4.1.5 = 42 labels (24 Ilocano stems + 18 option rows) |
| `1328-desk-q49-num-ILO.png` / `1328-desk-q50-num-ILO.png` | Windows CSEntry, Ilocano desk pff: Q49 / Q50 *No. of Days* banners *Iti promedio … pasilidad? — No. of Days* / *Mano nga adlaw … akreditasion? — No. of Days* (`Field = Q49_TRANCHE_INTERVAL_NUM` / `Q50_ACCRED_WAIT_NUM`) |
| `1329-desk-q53-stem-ILO.png` | Q53 banner + popup title *Apay a narigat ti agtungpal kadagiti: Kabaelan ti mangisayangkat …* |
| `1330-desk-q54-stem-ILO.png` | Q54 banner + popup title *Apay a narigat ti agtungpal kadagiti: Kabaelan ti mangipaay …* (Q55–Q61 carry the same shape; dcf diff + byte-verify) |
| `1331-desk-q62-options-ILO.png` | Q62 popup: *Bukod nga inisiatiba dagiti pasiente / Dagiti pasilidad / LGU / Sabali pay / PhilHealth / Saan ko nga ammo / Dadduma pay (ibaga)* |
| `1332-desk-q65-options-ILO.png` | Q65 popup with option 02 *Awan ti kinatulok ti pasiente (…)* and option 03 without the stray full stop |
| `1333-desk-q75-stem-ILO.png` | Q75 banner: the condensed Ilocano stem ending *Maibatay iti praktismo, umdasen kadi daytoy?* |
| `1334-desk-q98-stem-ILO.png` | Section E Q98 banner + popup *Iti assessment-yo, ania dagiti kangrunaan a makaapektar …*, option 03 *Pannakaammo ti pasiente iti programa* — **pilot-jump build** (`f1_1334_q98_pilot_ilo.txt`: `F1_PILOT_JUMP=Q88_HEARD_BUCAS` desk-only apc, regenerated clean + md5-checked before any publish; labels identical to the served 4.1.6 — the working tree at capture time already carried the 4.1.7 map changes, none of which touch Q98, see `../2026-08-27-1335-1346/dcf-label-proof-1335-1346.txt`) |
| `f1_1328_sectionDE_ilo.txt` | the desk scenario (copy of `automation/scenarios/`), driven on `F1/FacilityHeadSurvey_desktest_ILO.pff` — six runs: exploratory 1–5 fixed the Check Box popup anchors; the frames come from runs 2–6 (Q98: pilot-jump run, `f1_1334_q98_pilot_ilo.txt`) |

Desk frames are the Windows CSEntry engine (same logic and dictionary, not tablet chrome); Section D/E sits past Sections A–C
(~110+ fields), beyond the tablet-navigation cap, so the proof is desk-engine + the served-package byte-verify.
Patch note: `deliverables/CSPro/patch-notes/2026-08-27-f1-v4.1.6-uat-1328-1334.md`.
