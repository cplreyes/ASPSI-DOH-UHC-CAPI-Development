# Aug-21 translations — F1 v4.1.0 render evidence (2026-08-26)

**Driver:** ASPSI revised Deliverable 2 (Aug-21), 7 translated F1 questionnaires. **Ships as:** F1 v4.1.0 (DEV channel).
**Method:** deployed package pulled from CSWeb (`files/apps/FacilityHeadSurvey.zip`), sideloaded to the `capi_tablet` AVD with the PSGC lookups copied on-device, language switched in CSEntry's language menu, `adb shell screencap`.

| file | what it shows |
|---|---|
| `00-deploy-result.png` | CSWeb deploy dialog, v4.1.0 |
| `01-app-list-v4.1.0.png` | CSEntry app list showing `Facility Head Survey (F1) - v4.1.0 (2026-08-26) [DEV]` |
| `02-q20-fil.png` | Q20 (`item:Q20_EMR_USE`) stem in Filipino — a key the Aug-21 wave added |
| `03-q20-ilo.png` | the same Q20 stem in Ilocano |
| `04-q11-1-options-fil.png` | Q11.1 with its option list open in Filipino (`val:Q11_1_UHC_ATTRIB_VS1`, wave-changed in fil) |
| `05-icf-fil.png` | ICF screen 1 in Filipino (Aug-21 consent paragraphs + 08/21/2026 stamp) |
| `byte-verify.txt` | served .pen probed for map values (UTF-16LE) + v4.1.0 footer |

**Why not Q75.** The plan's first cut asked for Q75 shots. Q75 is `label-condensed` and was
ratified as **held** this build: it renders the emphasised English in bis/war/ilo and the
pre-wave June-5 text in fil/bcl/ceb/hil, so a Q75 screenshot proves nothing about the Aug-21
import. The reworded English Q75 stem is proven instead by the regenerated `.ent.qsf`
(Task 18). `item:Q20_EMR_USE` and `val:Q11_1_UHC_ATTRIB_VS1` were chosen in its place because
`byte-verify.txt` labels them **wave-changed** — they carry a value this wave wrote.

**The test case.** Shots 02–05 were taken inside one throwaway case on the AVD, key
`010280001901` (Bangui District Hospital, Ilocos Norte), answered only as far as Q20 with
placeholder values. It is **partial-saved and deliberately left unsynced** — it must never
reach CSWeb. Delete it from the emulator, not from the server, when the AVD is next reset.
