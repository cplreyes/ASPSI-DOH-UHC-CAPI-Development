# Aug-21 translations — F1 render evidence (v4.1.0 2026-08-26, v4.1.1 2026-08-27)

**Driver:** ASPSI revised Deliverable 2 (Aug-21), 7 translated F1 questionnaires. **Ships as:** F1 v4.1.1 (DEV channel), a patch on v4.1.0.
**Method:** deployed package pulled from CSWeb (`files/apps/FacilityHeadSurvey.zip`), sideloaded to the `capi_tablet` AVD with the PSGC lookups copied on-device, language switched in CSEntry's language menu, `adb shell screencap`.

**Package proven (v4.1.1):** `/opt/app/lamp/www/csweb/files/apps/FacilityHeadSurvey.zip` md5
`6e87ebd897b79bee2a88cf458b153b08`, 1,634,552 bytes, server mtime 2026-08-26 23:45:08 UTC =
2026-08-27 07:45:08 +08. The `FacilityHeadSurvey.pen` **on the device** md5
`43ea2c5f6d51bb99479f325c406e93c7` — byte-identical to the `.pen` inside that served zip and to
`package.json`'s signature for it — and the served `.pff` reads
`Description=Facility Head Survey (F1) - v4.1.1 (2026-08-27) [DEV]`. So the app-list frame below is
the deployed package, not a local build.

| file | what it shows |
|---|---|
| `00-deploy-result.png` | CSWeb deploy dialog, v4.1.0 publish run |
| `01-app-list-v4.1.0.png` | CSEntry app list showing `Facility Head Survey (F1) - v4.1.0 (2026-08-26) [DEV]` |
| `02-q20-fil.png` | Q20 (`item:Q20_EMR_USE`) stem in Filipino — a key the Aug-21 wave added |
| `03-q20-ilo.png` | the same Q20 stem in Ilocano |
| `04-q11-1-options-fil.png` | Q11.1 with its option list open in Filipino (`val:Q11_1_UHC_ATTRIB_VS1`, wave-changed in fil) |
| `05-icf-fil.png` | ICF screen 1 in Filipino (Aug-21 consent paragraphs + 08/21/2026 stamp) |
| `byte-verify.txt` | v4.1.0 served .pen probed for map values (UTF-16LE) + v4.1.0 footer |
| `00-deploy-result-4.1.1.png` | the v4.1.1 publish run's `Application Deployed Successfully` dialog. The dialog's own `Description` field is blank — CSDeploy never fills it — so this frame proves *a* deploy succeeded and nothing more; the version proof is the app-list frame plus the byte-verify |
| `01-app-list-v4.1.1.png` | CSEntry app list showing `Facility Head Survey (F1) - v4.1.1 (2026-08-27) [DEV]` |
| `byte-verify-4.1.1.txt` | v4.1.1 byte-verify with `--baseline` (the v4.1.0 maps) — `RESULT: ALL PASS`, exit 0, 5 probe keys × 7 locales, a `v4.1.1` footer probe and 9 `0×` counts |
| `dcf-removal-proof-4.1.1.txt` | the half a byte count structurally cannot do — see below |

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
The v4.1.1 pass opened **no case at all** and synced nothing.

## The row-inheritance repair (v4.1.1, Task 49b)

The whole-branch review found a defect class the per-task reviews structurally could not see: an
option row that silently carries a NEIGHBOURING row's translation is well-formed and in the right
language, so no flag fires — but two codes of one value set then read **identically on the tablet**,
and the analyst cannot tell the two answers apart afterwards. `anchor_extract.py` now holds such a
row instead of writing it, and `apply_aug21.py` carries a permanent `duplicate-label` gate over the
map an apply would leave behind (Task 48).

F1 v4.1.0 shipped two of them. Neither has a distinct translation anywhere on the Aug-21 paper, so
each map row was **deleted** — an English option label beats a wrong one — and the tablet renders
English until the translators supply text:

| locale | value set / code | English | v4.1.0 shipped | v4.1.1 |
|---|---|---|---|---|
| bcl | `Q83_NOT_RECEIVED_REASONS_VS1` **03** | Difficulties in verifying patient enrollment (PhilHealth) | `Pagka-antala sa tracking kan patient enrollment` — code **02**'s text | English |
| fil | `Q45_PERF_INDICATORS_VS1` **04** | Beneficiaries received noncommunicable disease (NCD) medicine as prescribed by their primary care doctor | `Ang mga benepisyaryo ay nakatanggap ng antibiotics …` — code **03**'s text | English |

The sibling that legitimately owns each string keeps it: bcl `…:02` still reads
`Pagka-antala sa tracking kan patient enrollment`, fil `…:03` still reads the antibiotics sentence.

**Why `dcf-removal-proof-4.1.1.txt` exists.** The `.pen`'s string table is **pooled**: a string that
one code loses and its sibling keeps occurs exactly **once** before and after, so
`--count "<removed string>" 0` would be a lie and `--count … 1` would prove nothing (measured: both
strings are 1× in the v4.1.0 pen and 1× in the v4.1.1 pen). The per-CODE evidence therefore comes
from the built `FacilityHeadSurvey.dcf` — the dictionary Designer compiled this package's `.pen`
from — where every value carries one label per language. The proof file asserts, for each removed
row, that the locale's label now *is* the English label; that the accepted span and both kept
siblings are intact; and that **no value set in any of the seven languages has two codes with the
same label**. The 9 `0×` counts in `byte-verify-4.1.1.txt` are the strings v4.1.0 carried and this
build no longer does (one per locale), which is what ties the proof to the served bytes.
