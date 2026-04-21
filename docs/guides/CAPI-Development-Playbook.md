---
type: guide
audience: internal (developer-owned; supervisor/data-manager/PM touchpoints called out per-section)
scope: Generic CAPI-in-CSPro playbook, with this project's artifacts cited as concrete examples.
last_updated: 2026-04-21
---

# CAPI Development Playbook — CSPro / CSEntry / CSWeb

A step-by-step guide for designing, building, deploying, and maintaining a CAPI (Computer-Assisted Personal Interviewing) system using the CSPro toolchain. Written as a reusable playbook; where useful, cites this project's artifacts (F1/F3/F4 DCFs, `generate_dcf.py`, `PSGC-Cascade.apc`, etc.) as concrete examples.

---

## Table of Contents

0. [Orientation — the three tools and how they fit together](#0-orientation)
1. [Lifecycle at a glance — the 12 phases](#1-lifecycle)
2. [Project context and standing rules](#2-project-context)
3. [Environment & repository setup](#3-environment-setup)
4. [Authoring the data dictionary (`.dcf`)](#4-authoring-the-dcf)
5. [Skip logic, validation, and runtime behaviour (`.app`)](#5-skip-logic-and-validation)
6. [Value sets — bake vs. externalize](#6-value-sets)
7. [Form design for tablets](#7-form-design)
7a. [Media, geolocation, and map capture (GPS, photos, files)](#7a-media)
8. [Local testing on desktop CSEntry](#8-local-testing)
9. [Packaging for Android CSEntry](#9-packaging)
10. [CSWeb — what it is, sizing, and deployment](#10-csweb-deployment)
11. [CSWeb ↔ CSEntry integration (registration, sync, packages)](#11-integration)
11a. [Supervisor-app pattern (Popstan reference)](#11a-supervisor-app)
12. [Field sync architecture (this project's tiered model)](#12-field-sync)
13. [Mid-field update protocol](#13-update-protocol)
14. [Data export, QC, and reporting](#14-data-export)
15. [Roles & responsibilities](#15-roles)
16. [Checklists](#16-checklists)
17. [Appendices (VPS provisioning, Nginx, backups, troubleshooting)](#17-appendices)

---

## 0. Orientation — the three tools <a id="0-orientation"></a>

### Mental model

```
   +------------------+       authoring artifacts        +-------------------+
   |      CSPro       | -------------------------------> |     CSEntry       |
   | (desktop, Win)   |   .dcf / .fmf / .app / .pff      | (Android / Win /  |
   |   Designer +     |   .ent (bundled) / .pen (pkg)    |    Web runtime)   |
   |   Logic / Tables |                                  +---------+---------+
   +--------+---------+                                            |
            |                                                      | HTTPS sync
            |   authors + analyses                                 | (cases, logs)
            v                                                      v
   +------------------+   deploys packages / collects   +-------------------+
   |   Git repo +     | <----------------------------   |       CSWeb       |
   |   Python/Excel   |   exports (CSV, SPSS, Stata)    | (Tomcat + MySQL)  |
   +------------------+                                 +-------------------+
```

### Who does what

| Tool | Role | Runs on | What you do there |
|---|---|---|---|
| **CSPro** | The **authoring suite**. Opens `.dcf` (data dictionaries), `.fmf` (form files), `.app` (applications), `.ent` (bundles). Includes CSCode Logic editor, Designer, Tables. | Windows desktop only (runs under Wine on macOS/Linux in limited fashion). | Write schemas, draw forms, author skip logic/validation, run Tables for QC, build deployment packages. |
| **CSEntry** | The **runtime**. Opens the compiled application and walks an interviewer/enumerator through a case. | Windows desktop, **Android tablet/phone** (primary for this project), iOS (limited), and as a web module inside CSWeb. | Field enumerator's interface. Where actual data is captured. |
| **CSWeb** | The **server** — Tomcat webapp + MySQL/MariaDB. Hosts a sync endpoint for CSEntry, manages users/devices, provides dashboards, distributes application packages. | Linux VPS with public HTTPS endpoint. | Receive cases, push new app versions, monitor progress, export data. |

Rule of thumb: CSPro is where **you build**, CSEntry is where **they run**, CSWeb is where **it all meets**.

### Key artifact types

| Extension | Contents | Owned by |
|---|---|---|
| `.dcf` | Data dictionary — records, items, value sets. JSON under the hood as of v8. | Generator script (project rule: never hand-edit in Designer — see `feedback_f1_dcf_generator_source_of_truth`). |
| `.fmf` | Form file — rosters, layout, widget types. | Designer, hand-tuned. |
| `.app` | Application — ties dictionary + forms + logic together. | Designer + CSCode editor. |
| `.ent` | Entry bundle — `.dcf + .fmf + .app` compiled into one file for CSEntry. | CSPro builds this. |
| `.pen` | Package for CSEntry Android distribution. | CSPro → CSWeb. |
| `.pff` | Parameter file — which app to open, which data file to use, settings. | Hand-written or auto-generated per deployment. |

---

## 1. Lifecycle at a glance — the 12 phases <a id="1-lifecycle"></a>

This project follows a 12-phase reusable CAPI workflow (see `concepts/capi-development-workflow.md`):

| # | Phase | Output | Gate |
|---|---|---|---|
| 1 | **Ingest source questionnaire** | `raw/` → `wiki/sources/Source - <Annex>.md` | Source summary exists |
| 2 | **Extract structured spec (CSV)** | `deliverables/CSPro/F<n>/inputs/*.csv` | Items enumerated, VS listed |
| 3 | **Generate DCF** | `deliverables/CSPro/F<n>/F<n>Survey.dcf` via `generate_dcf.py` | DCF opens cleanly in Designer |
| 4 | **Spec skip logic & validation** | `deliverables/CSPro/F<n>/logic/<N>*.md` | Sign-off from Carl |
| 5 | **Fix schema gaps found in step 4** | `generate_dcf.py` patches | All LSS items resolved |
| 6 | **Build forms** | `.fmf` via Designer | Forms render, keyboard types correct |
| 7 | **Build `.app` + compile logic** | `.app` with skip/validation | `.ent` builds without errors |
| 8 | **Bench test** | Synthetic cases on desktop CSEntry | Golden-path + edge cases pass |
| 9 | **Package for Android** | `.pen` file | Installs on tablet |
| 10 | **Pilot test in field** | Pilot cases + issue log | Pilot sign-off |
| 11 | **Deploy to full fleet via CSWeb** | Packages module loaded | All 100 tablets on same version |
| 12 | **Monitor + patch** | Mid-field updates | See §13 |

Phases 1–8 are local (developer machine + git). Phase 9 transitions to distribution. Phases 10–12 are live-field operations.

> Related project rules (already established):
> - **Logic-pass before build** (phase 4 before 6) — `concepts/logic-pass-before-build.md`
> - **Generator over hand-edit** — `concepts/generator-over-hand-edit.md`
> - **Phases ≠ Epics** — 12 phases are sequential workflow; 13 epics are parallel workstreams (`concepts/phases-vs-epics.md`)

---

## 2. Project context and standing rules <a id="2-project-context"></a>

Rules already decided for this engagement; don't relitigate without reason:

| Rule | Ref |
|---|---|
| Android tablet is the primary CSEntry platform; desktop CSEntry is developer-only. | Inception Report §V.E |
| Daily data sync before 10 PM; weekly extract for QC. | Inception Report §V.E |
| Verbatim questionnaire labels in DCF (exact source wording, original question numbers). | `feedback_verbatim_questionnaire_labels` |
| NA code = highest value at field width: NA=9 (len-1), 99 (len-2), 999 (len-3). | `feedback_na_code_convention` |
| Generator script (Python) is source of truth for DCFs. Never hand-edit in Designer. | `feedback_f1_dcf_generator_source_of_truth` |
| PSGC value sets live in `shared/psgc_*.dcf` external lookups + `PSGC-Cascade.apc` at runtime. | `project_aspsi_psgc_value_sets` |
| F2 has 3 capture paths — Google Forms primary, paper→Forms fallback, CSPro CAPI optional. | `project_f2_capture_modes` |
| F2 self-admin window = 3 days; self-admin is primary model. | `project_f2_self_admin_window`, `feedback_f2_admin_model_self_admin_first` |
| Forward-only sign-off; test bugs loop back to owning stage's source doc. | `feedback_forward_signoff_loopback_bugs` |
| Quality is the anchor, not tranche payment deadlines. | `feedback_quality_over_deadline` |

---

## 3. Environment & repository setup <a id="3-environment-setup"></a>

### Developer workstation

- **OS:** Windows 10/11 (CSPro Designer is Windows-native).
- **CSPro version:** 8.0+ (fixed per project; upgrading mid-project is a breaking change).
- **Python:** 3.11+ with `openpyxl`, `pandas`. Used by `generate_dcf.py`, `parse_psgc.py`, `build_psgc_lookups.py`, `export_dcf_to_xlsx.py`.
- **Git:** commits signed (Ed25519 — see `concepts/git-commit-signing.md`).
- **Encoding:** force UTF-8 when reading/writing files from PowerShell/Python — see `windows_utf8_gotcha`. Em-dashes and bullets silently mojibake otherwise.
- **Editor hygiene:** `endOfLine: auto` in `.prettierrc` on Windows — see `feedback_prettier_endofline_auto`.

### Repository layout (PARA + LLM Wiki)

```
1_Projects/ASPSI-DOH-CAPI-CSPro-Development/
├── raw/                         — Source documents (questionnaires, annexes). IMMUTABLE.
├── wiki/                        — Knowledge pages (sources, entities, concepts, analyses).
├── deliverables/CSPro/          — Authored CAPI artifacts.
│   ├── cspro_helpers.py         — Shared DCF-emitter helpers (numeric, alpha, build_geo_id, etc.)
│   ├── shared/                  — Cross-form shared assets.
│   │   ├── psgc_*.dcf/.dat      — PSGC external lookup dictionaries.
│   │   ├── build_psgc_lookups.py
│   │   └── PSGC-Cascade.apc     — Reusable cascade logic module.
│   ├── F1/ F3/ F4/              — Per-instrument folders.
│   │   ├── inputs/              — CSVs, source xlsx.
│   │   ├── generate_dcf.py      — Source of truth for DCF.
│   │   ├── <Form>Survey.dcf     — Generated; checked in.
│   │   ├── <Form>.fmf           — Hand-built in Designer.
│   │   ├── <Form>.app           — Hand-built in Designer + logic.
│   │   ├── export_dcf_to_xlsx.py — Review export.
│   │   └── <Form> - Data Dictionary and Value Sets.xlsx — Review output.
│   └── F2/                      — F2 artifacts (Google Forms primary; CSPro optional fallback).
├── docs/
│   ├── guides/                  — Internal guides (this file).
│   └── superpowers/             — Plans, specs produced by plan/execute skills.
├── templates/                   — Reusable CSV templates.
├── index.md                     — Content catalog.
├── log.md                       — Chronological operations log.
└── CLAUDE.md                    — Project wiki schema.
```

### What to check in vs. ignore

- **Commit:** `.dcf`, `.fmf`, `.app`, generator scripts, input CSVs, review xlsx (reviewers pull from git), `shared/*.dat` (small).
- **Ignore:** compiled `.ent`, transient `.pff` from local runs, CSPro auto-backup `.bak` files, `~$*.xlsx` lock files, `__pycache__`, `.venv`.

---

## 4. Authoring the data dictionary (`.dcf`) <a id="4-authoring-the-dcf"></a>

The DCF is the schema. Everything else hangs off it.

### The generator pattern (non-negotiable rule)

**Every revisionable field-layout decision lives in `generate_dcf.py`, never in Designer's GUI.** The GUI is a viewer. Editing the GUI directly means the next regeneration nukes your change.

Pattern:

```python
# F<n>/generate_dcf.py
from cspro_helpers import numeric, alpha, build_geo_id, dictionary

def build_record_A():
    return record("REC_A", items=[
        numeric("RESP_AGE", "Age at last birthday (years)", length=3,
                value_set_options=[("Don't know", 998), ("Not applicable", 999)]),
        numeric("RESP_SEX", "Sex", length=1,
                value_set_options=[("Male", 1), ("Female", 2), ("Not applicable", 9)]),
        alpha("RESP_NAME", "Full name", length=80),
        ...
    ])

def main():
    dcf = dictionary(
        name="F1_SURVEY",
        records=[build_geo_id("facility"), build_record_A(), ...],
        label="F1 — Facility Head Survey",
    )
    write_dcf(dcf, OUTPUT_DCF)

if __name__ == "__main__":
    main()
```

### Per-item decisions

For every item, decide upfront:

1. **Name** — ALL_CAPS, underscores, ≤32 chars. Use stable semantic names (`RESP_AGE`, not `Q7`).
2. **Type** — `numeric` or `alpha`. Avoid `decimal` unless unit-critical (GPS, prices).
3. **Length** — fixed. **NA code convention dictates length minimum**: if the largest NA code is 99, length must be ≥2. See `feedback_na_code_convention`.
4. **Zero-fill** — `zero_fill=True` for codes where leading zeros matter (PSGC — always length 10).
5. **Value set** — see §6.
6. **Label** — **verbatim from source questionnaire including the original question number** (project rule).
7. **Occurrence** — single or repeated; for repeating, define max occurs.

### Records and blocks

Group items into records by real-world entity/repetition pattern:

- One-to-one with the case → items on the **ID-or-master record**.
- Repeating rosters (household members, children, staff matrix) → **repeating records** with max-occurs.
- Shared blocks (geographic ID, cover page) → build once in `cspro_helpers.build_geo_id(mode)` and reuse.

### Testing the DCF

After every regeneration:

```bash
python F<n>/generate_dcf.py
python F<n>/export_dcf_to_xlsx.py --all   # review xlsx for Carl/Sean
```

Then open the `.dcf` in CSPro Designer and confirm:

- ✔ All records present, item count matches baseline.
- ✔ Open any item with an external lookup VS — it shows the 1-entry placeholder (not bloated).
- ✔ `.dcf` file size on disk matches expectation (F1 ≈ 0.9 MB; if suddenly 17 MB, PSGC was re-baked — audit for stray `load_psgc_value_set` calls).

---

## 5. Skip logic, validation, and runtime behaviour (`.app`) <a id="5-skip-logic-and-validation"></a>

This is **CSPro Logic** (sometimes called CSCode). Think "BASIC with survey primitives."

### Where logic lives

| Scope | Procedure event | Used for |
|---|---|---|
| **Application-level** | `PROC GLOBAL` | Constants, helper functions, shared state. |
| **Form-level** | `PROC <FORM>` | Flow control at form boundaries. |
| **Record-level** | `PROC <RECORD>` | Per-record validation, defaults. |
| **Item-level** | `PROC <ITEM>` | The workhorse. Fires on entry, leave, keypress. |

### Key events

| Event | When it fires | Typical use |
|---|---|---|
| `preproc` | Before the item is shown. | Default values, conditional visibility. |
| `postproc` | After the item is left (with a valid entry). | Skip logic (`skip to <ITEM>`), cross-item validation, `errmsg()`. |
| `onfocus` | **Every** time the item receives focus — including reverse navigation. | Dynamic value sets (see §6, cascade pattern). **Not `preproc` for cascade** (Users Guide p.188 Logic Tip #4). |
| `onkey` | Keystroke. | Custom keyboard handling. Rare in tablet CAPI. |

### Canonical skip-logic pattern

```
PROC RESP_SEX
postproc
    if RESP_SEX = 2 then                 { female }
        { continue — next item asks about pregnancy }
    else
        skip to HH_HEAD_RELATION;        { male — skip pregnancy block }
    endif;
```

### Cross-field validation

```
PROC RESP_AGE
postproc
    if RESP_AGE < 18 and MARITAL_STATUS = 2 then
        errmsg("Inconsistency: age < 18 but marital status = 'Married'. Please reconcile.");
        reenter;
    endif;
```

### External function modules (`.apc`)

Reusable logic — write once, include in each form's app. Example: `shared/PSGC-Cascade.apc` exposes 4 functions used by F1, F3 facility block, F3 patient block, and F4.

Include pattern in the `.app`:

```
#include "../shared/PSGC-Cascade.apc"
```

Then wire at the consuming site:

```
PROC REGION            onfocus  FillRegionValueSet(REGION);
PROC PROVINCE_HUC      onfocus  FillProvinceValueSet(PROVINCE_HUC, REGION);
PROC CITY_MUNICIPALITY onfocus  FillCityValueSet(CITY_MUNICIPALITY, PROVINCE_HUC);
PROC BARANGAY          onfocus  FillBarangayValueSet(BARANGAY, CITY_MUNICIPALITY);
```

### Anti-patterns (caught in review)

- ❌ Copy-pasting skip chains across forms — extract to `.apc` or use sub-form pattern.
- ❌ Hard-coded value-set codes inside logic (`if SEX = 2` becomes wrong if VS is re-coded). Prefer symbolic constants or rely on value-set labels.
- ❌ Using `preproc` to populate dynamic value sets. Use `onfocus` so reverse-navigation still repopulates.
- ❌ `errmsg()` without `reenter` — user can just tab past.

---

## 6. Value sets — bake vs. externalize <a id="6-value-sets"></a>

### Decision matrix

| Value set size | Duplicated across forms? | Strategy |
|---|---|---|
| < 50 entries, one form | No | **Bake into `.dcf`** (normal value set). |
| < 50 entries, multiple forms | Yes | Bake into DCF in each form; keep a CSV source-of-truth for copy-paste hygiene. |
| 50–500, one form | No | Bake into DCF; acceptable on tablets. |
| 50–500, multiple forms **or** potentially cascading | Either | **Externalize**: one `shared/<name>.dcf` + `.dat` lookup; placeholder VS in main DCF; populate at runtime via `setvalueset()` on `onfocus`. |
| > 500, always | Always externalize | Same. Also: **cascade** by parent if the list has hierarchy (PSGC = 42k barangays, filtered to ~25 per city). |

### Externalized + cascade (reference implementation: PSGC)

This project's PSGC refactor (Apr 2026) is the template. Four levels: Region → Province/HUC → City/Municipality → Barangay.

```
deliverables/CSPro/shared/
├── psgc_region.dcf / .dat           (18 rows)
├── psgc_province.dcf / .dat         (117 rows)
├── psgc_city.dcf / .dat             (1,658 rows)
├── psgc_barangay.dcf / .dat         (42,010 rows)
├── build_psgc_lookups.py            — rebuilds the 4 pairs from CSV
└── PSGC-Cascade.apc                 — runtime cascade functions
```

Main DCF items carry a **1-entry placeholder value set** (best practice per Users Guide p.188). At runtime, each item's `onfocus` calls into `PSGC-Cascade.apc`, which uses `loadcase()` on the relevant external dict to pull the parent's children, then `setvalueset()` to replace the placeholder.

Outcome (this project): F1 DCF 17 MB → 0.9 MB; F3 33 MB → 1.0 MB; F4 17 MB → 0.8 MB; review xlsx VS sheets 46k–90k rows → 2k–2.6k.

### Reference: Popstan Census CAPI

US Census Bureau's canonical example lives in `3_Resources/Tools-and-Software/CSPro/Examples 8.0/1 - Data Entry/CAPI Census/`. Read their AREA_DICT pattern — it's the blueprint the PSGC implementation mirrors.

---

## 7. Form design for tablets <a id="7-form-design"></a>

Forms live in `.fmf` and are built in Designer. Principles:

### Tablet-specific rules

- **One concept per screen.** Don't cram. Scrolling is OK but modal-hiding is not.
- **Touch targets ≥ 44px.** Designer's default widget sizes may be desktop-scaled — check on the actual tablet, not the emulator.
- **Numeric inputs → numeric keyboard.** Set `Capture Type = Numeric` in Designer so Android pops the 10-key keyboard.
- **Pickers over free text** wherever possible — reduces typos, speeds entry.
- **Skip tabs** — one "Back" and one "Next" per screen, always in the same position. Do not let Designer auto-layout them.
- **Cascading dropdowns** — use the PSGC pattern (§6) for any hierarchical picker.
- **Minimal required-field friction** — allow enumerators to save partial cases and resume.

### Multi-language

Filipino/Tagalog, Ilocano, Bicolano, Ilonggo, Waray, Bisaya, Cebuano (per Inception Report). Languages are attached to items in the DCF as alternate labels. Per-tablet default language is set at CSEntry install time; enumerator can toggle mid-case.

Workflow:
1. Finalize English source wording (frozen).
2. Translators fill a CSV with one column per language, keyed by item name.
3. `generate_dcf.py` reads the CSV and emits the alternate labels into the DCF.
4. Translators review the generated review xlsx.

---

## 7a. Media, geolocation, and map capture <a id="7a-media"></a>

CSPro 8.0 introduced first-class support for **GPS, images, maps, geometry, and document/file attachments**. These are Android-only features; desktop CSEntry does not have camera/GPS hardware access. Audio and video are partial/unsupported — see capability matrix below.

### Capability matrix (CSPro 8.0)

| Capability | Supported? | Platform | Dictionary item type | Logic primitive | Syncs to CSWeb? |
|---|---|---|---|---|---|
| GPS (lat/long/altitude/accuracy) | ✅ Production | Android | numeric/alpha items (store components) | `gps(open/read/close)` + `gps(latitude/longitude/accuracy/altitude/satellites/readtime)` | ✅ (as normal data) |
| Photo capture | ✅ Production | Android | **Image** (binary, experimental) | `Image obj; obj.takePhoto("msg"); obj.resample(...); obj.save(file)` | ✅ (binary items sync) |
| QR/Barcode generation | ✅ | Android | Image | `Image.createQRCode()`, `Barcode.createQRCode()` | ✅ |
| Map display on tablet | ✅ Production | Android (needs Google Play Services + network) | n/a — runtime-only `Map` object | `Map m; m.show(); m.addGeometry(g); m.addTextButton(...)` | n/a (display only) |
| Polygon/line tracing (area/perimeter) | ✅ Production | Android | **Geometry** (binary) + GeoJSON files | `Geometry g; g.tracePolygon(map); g.save(file); g.area(); g.perimeter()` | ✅ (Geometry items sync) |
| Document/file attachment | ✅ | Android / Windows | **Document** (binary, experimental) | String → Document object assignment; experimental logic support | ✅ |
| Audio recording | ❌ **Not supported in 8.0** | — | `Audio` item type exists but capture is not available | — | — |
| Video recording | ❌ Not officially supported | — | — | Workaround: launch device camera via `execsystem("camera:...")` — unofficial; test before relying | — |

> **About binary item types** (Image/Geometry/Audio/Document): these are new in 8.0 and flagged as **experimental**. They **cannot be placed on a form** (no on-screen widget), but they **are supported throughout the rest of CSPro, including synchronization**. Workflow: capture into a runtime object in logic → assign to the binary item → it syncs with the case to CSWeb → reviewable in CSWeb case detail view.

### GPS — canonical capture block

Pattern lifted from `Examples 8.0/1 - Data Entry/CAPI Census/Household/Household.ent.apc:171-240`.

Dictionary (main DCF):

```
alpha  HH_GPS_LATITUDE    len 12
alpha  HH_GPS_LONGITUDE   len 12
alpha  HH_GPS_ALTITUDE    len 10
numeric HH_GPS_ACCURACY   len 3        { metres, lower = better }
numeric HH_GPS_SATELLITES len 2
alpha  HH_GPS_READTIME    len 19       { ISO timestamp }
```

Logic (app):

```
function captureGPS()
    numeric max_time = 120;            { seconds }
    numeric desired_accuracy = 20;     { metres }

    if gps(open) then
        numeric result = gps(read, max_time, desired_accuracy);
        if result = 1 then
            if gps(accuracy) > HH_GPS_ACCURACY then
                errmsg("Could not achieve %d-m accuracy — got %d m.",
                       HH_GPS_ACCURACY, gps(accuracy));
            endif;
            HH_GPS_LATITUDE   = gps(latitude);
            HH_GPS_LONGITUDE  = gps(longitude);
            HH_GPS_ALTITUDE   = gps(altitude);
            HH_GPS_ACCURACY   = gps(accuracy);
            HH_GPS_SATELLITES = gps(satellites);
            HH_GPS_READTIME   = gps(readtime);
        else
            errmsg("GPS read failed or timed out.");
        endif;
        gps(close);
    else
        errmsg("GPS hardware unavailable.");
    endif;
end;
```

Wire from a "Capture GPS" button/item's `onfocus` or `postproc`. **Always pair `gps(open)` with `gps(close)`** — leaked handles drain battery.

### Photo capture

Android only. Minimal pattern:

```
Image facility_photo;
if facility_photo.takePhoto("Take a photo of the facility signage.") then
    facility_photo.resample(maxWidth := 1600, maxHeight := 1200);   { keeps file small }
    facility_photo.save(maketext("%s-facility.jpg", CASE_ID), quality := 90);
    { then assign to the binary Image item in the dictionary so it syncs }
    FACILITY_PHOTO_BIN = facility_photo;
endif;
```

**Operational rules:**
- Always `resample()` before `save()` — raw tablet photos are 3–8 MB each; a 100-tablet × 10-photo-per-case × 1500-case survey easily hits terabytes unresampled. Target ≤ 200 KB per image.
- Store one filename convention: `<CASE_ID>-<role>.jpg`.
- **Camera permissions** must be granted per-tablet on first use — include in enumerator training.
- Photos can be taken as **file-on-disk** (via `save`) for lightweight workflows, or as **binary dictionary items** for sync-with-case. Binary items sync automatically with the case; file-on-disk needs a separate sync routine (see Synchronization Overview in CSPro docs).

### Map display on tablet

Requires Android + Google Play Services + network. Pattern from `Examples 8.0/1 - Data Entry/Geometry/Geometry.ent.apc`:

```
PROC GLOBAL
Map myMap;

function hideMap()
    myMap.hide();
end;

PROC SOME_FORM
preproc
    myMap.addTextButton("Quit", hideMap());
    myMap.show();
```

And polygon capture (land-parcel / facility-footprint / service-area boundary):

```
Geometry polygon;
if polygon.tracePolygon(myMap) then
    polygon.save(maketext("%d-%d.geojson", sysdate("yyyymmdd"), systime("hhMMss")));
    errmsg("Area = %0.1f m^2, Perimeter = %0.1f m",
           polygon.area(), polygon.perimeter());
endif;
```

### Files / documents

New `Document` binary item type. Use when an enumerator needs to attach an existing file (scanned consent form, referral letter, lab result). String expressions assign into a Document object; it syncs with the case.

> **Limitation:** binary items can't appear on forms. UX pattern: on a "Attach consent form" button press, use logic to pick a file from tablet storage or trigger the camera, then assign to the Document/Image item. It won't render on the form but it will sync and be visible in CSWeb's case detail view.

### CSWeb-side visibility

- **GPS coordinates** — CSWeb's Cases view includes a **map tab** that plots cases by their lat/long items (configurable which items map to lat/long). Data Manager sees geographic distribution of completion in real time.
- **Images / Documents** — CSWeb's per-case detail view renders attached `Image` items inline (thumbnail + full view) and provides a download link for `Document` items.
- **Exports** — CSV/SPSS/Stata exports include coordinate items as plain columns. Binary items (images/documents) export as file references; the actual blobs live on the CSWeb server and can be bulk-downloaded via the Packages/Files UI or server filesystem.

### What this means for F1/F3/F4

- **F4** already has `LATITUDE` / `LONGITUDE` items (length 12 alpha) from `build_geo_id("household", extra_items=[...])`. Next step: add a `CaptureGPS` button/PROC that invokes the block above; currently those items are manual-entry.
- **F1 (facility survey)** — candidate for facility signage photo + facility GPS. Add `FACILITY_PHOTO` (Image binary) + `FACILITY_GPS_*` items.
- **F3 (patient survey)** — likely avoid photos for privacy; GPS at patient-home level is already in the DCF (`P_REGION` etc.), can add precise `P_HOME_GPS_*` if ethics approval permits.
- **Audio-recorded interviews for QC** — not achievable in CSPro 8.0. If required, use a separate recorder app on the tablet and attach files as Document binary items.

---

## 8. Local testing on desktop CSEntry <a id="8-local-testing"></a>

Build and run on the developer machine before packaging for Android.

### Build the .ent

In CSPro Designer: `File → Build Application` (or `Ctrl+Shift+B`). Produces `.ent`.

### Bench test matrix

For every form, exercise:

| Case | Scenario | Expected |
|---|---|---|
| 1 | Golden path — all items normal values | Complete case, no errors. |
| 2 | All NA (age = 999, sex = 9, etc.) | Accepts but flags as unusable in Tables. |
| 3 | Skip logic — each branch | All branches reachable; no dead ends. |
| 4 | Boundary values | Min/max length, leading zeros, whitespace. |
| 5 | Reverse navigation | Back button across every form boundary; value sets re-populate (this is why `onfocus` not `preproc` for cascade). |
| 6 | Partial save and resume | Case reloads mid-form with correct state. |
| 7 | Cross-field validation failures | Every `errmsg()` fires on its trigger condition. |
| 8 | Language toggle | All labels switch; no English bleed-through. |
| 9 | Cascade | Region change clears Province/City/Barangay? (Decide: this project currently does not cascade-clear on parent change; QA with Sean.) |

Keep a **test-case spreadsheet** under `deliverables/CSPro/F<n>/test-cases/` with columns: ID, scenario, inputs, expected, pass/fail, last-run-date.

---

## 9. Packaging for Android CSEntry <a id="9-packaging"></a>

### The .pen file

CSPro Designer: `File → Deploy → Create .pen file`. The `.pen` bundles the `.ent` + all external dicts referenced (for this project: `shared/psgc_*.dcf + .dat`, totalling ~1.2 MB) + any referenced `.apc` includes.

### Distribution paths

| Path | When | Steps |
|---|---|---|
| **USB/ADB direct install** | Dev testing, small pilots. | Copy `.pen` to tablet storage → open with CSEntry → app installs into CSEntry. |
| **CSWeb Packages module** | Production. | Upload `.pen` to CSWeb → tablets pull on next sync → users see "New version available" prompt. |
| **Bluetooth supervisor → enumerator** | Emergency field patch, poor connectivity. | Supervisor downloads via laptop, sideloads to each tablet. Risky — easy to lose version parity. |

### Version every package

Stamp a version into the app name or a visible banner item (`APP_VERSION = "2.3.1"`). This is the single most useful field when debugging "my tablet behaves differently."

---

## 10. CSWeb — what it is, sizing, and deployment <a id="10-csweb-deployment"></a>

### What CSWeb actually is

A Java webapp (WAR file) that runs in **Apache Tomcat**, backed by **MySQL** or **MariaDB**. It provides:

- HTTPS sync endpoint for CSEntry tablets.
- Admin UI for users, roles, devices, applications (packages), and cases.
- Dashboards: progress by cluster/region/facility, response rates, enumerator performance, quality alerts (missing data, sync delays, duplicate entries, unusual interview durations).
- **Map view** — case points plotted on a base map using GPS items captured by CSEntry (§7a). Data Manager sees geographic distribution in near real time.
- **Case detail view** — renders attached **Image** items inline (thumbnail + full view) and provides download links for **Document** / Geometry / other binary items. All binary items sync automatically with the case.
- Export: CSV, SPSS (.sav), Stata (.dta). Binary attachments export as file references; blobs live on the CSWeb server and can be bulk-downloaded.

### System requirements

| Component | Minimum (pilot) | Production (100 tablets) |
|---|---|---|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 2 GB | 4–8 GB |
| Disk | 20 GB SSD | 80–160 GB SSD (case files + DB) |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Java | OpenJDK 11 | OpenJDK 17 |
| Tomcat | 9.x | 9.x or 10.x (match CSWeb version) |
| DB | MySQL 8 or MariaDB 10.6+ | Same, with separate data disk + daily backup |
| Network | Public IPv4, HTTPS | Same + optional CDN for package downloads |

### Hosting options — generic VPS vs. Elestio

**Short answer: a standard Linux VPS (Hostinger, DigitalOcean, Hetzner, Linode, Vultr, AWS Lightsail) is entirely sufficient for CSWeb. Elestio saves you the sysadmin work but costs more and gives you less control; it's fine for pilots, less ideal for a 100-tablet national survey.**

| Option | Pros | Cons | When to pick |
|---|---|---|---|
| **Generic VPS** — Hostinger / DigitalOcean / Hetzner / Linode / Vultr | Full root, any stack version, cheapest ($10–40/mo for the sizes you need), easy migration, your backups your rules. | You install/patch/secure Tomcat, MySQL, Nginx, certbot yourself. Oncall is you. | **Default choice** for this project — DOH data, ~100 tablets, months of fieldwork, data sovereignty matters. |
| **Elestio** (managed app hosting) | One-click Tomcat + MySQL, managed TLS, automated backups, monitoring dashboard. | ~1.5–2× VPS price. Less root control. Migration = re-export + re-import. No CSWeb-native image (you still deploy the WAR yourself to their Tomcat). | Pilot, demo, or if you genuinely don't want to touch Linux. |
| **DOH-provided server** | Inside the DOH security perimeter; matches data-sovereignty posture. | Access/change control ceremonies; slower iteration. | If DOH mandates it. Confirm before deploying elsewhere. |
| **AWS/Azure/GCP** | Enterprise-grade everything. | Over-engineered for this scale; pricing surprises. | Not worth it here. |

### Recommended minimum VPS spec (this project)

- **Hetzner CPX21** (3 vCPU, 4 GB RAM, 80 GB SSD, ~€8/mo) or **DigitalOcean Premium 4 GB** (~$24/mo) or **Hostinger KVM 2** (~$7/mo promo, ~$13/mo renewal).
- Ubuntu 22.04 LTS.
- One DNS name pointing at it (e.g., `csweb.<domain>.ph`).
- HTTPS via Let's Encrypt.

### Deployment outline (bare-VPS)

1. Provision VPS, Ubuntu 22.04. Assign DNS. SSH in.
2. Install OpenJDK 17, Tomcat 9, MySQL 8, Nginx, certbot.
3. Secure: UFW firewall (allow 22, 80, 443 only), fail2ban, disable password SSH, enforce key-only login.
4. Create MySQL user + database for CSWeb.
5. Download CSWeb WAR from Census Bureau site (version must match your CSPro Designer version).
6. Drop WAR into `/var/lib/tomcat9/webapps/`. Tomcat auto-deploys.
7. Configure CSWeb via its web UI: DB connection, admin user, site name.
8. Configure Nginx as HTTPS reverse proxy to Tomcat's 8080.
9. `certbot --nginx -d csweb.<domain>.ph` for TLS.
10. Schedule daily MySQL backup (cron → S3 or Backblaze B2).

Full provisioning script template → Appendix A.

---

## 11. CSWeb ↔ CSEntry integration (registration, sync, packages) <a id="11-integration"></a>

### Registration handshake

1. CSWeb admin creates a **user** and a **role** (Enumerator, Supervisor, Data Manager, Admin).
2. CSWeb admin creates a **device** entry OR allows the user to self-register on first sync.
3. Enumerator opens CSEntry on the tablet → `Settings → Server → <CSWeb URL> → login with user + password`.
4. CSEntry pulls the **current application package** and the list of cases assigned to this device (if any pre-assignment model is in use).
5. From then on, every sync pushes new/updated cases to CSWeb and pulls any application updates.

### The sync protocol

- HTTPS POST of **case files** (serialized, item-level granularity).
- Server responds with **acks + any pending application package updates**.
- Incremental: only changed cases sync. If a case is edited after sync, the next sync pushes the updated version; server keeps revision history.
- **Conflict resolution:** last-write-wins by timestamp. For CAPI (single-enumerator per case), conflicts are rare. For multi-device editing (supervisors reviewing), design the workflow so only one device holds "authority" at a time.

### Packages module (how app updates flow)

1. Developer builds a new `.pen` on their Windows box.
2. Developer uploads `.pen` to CSWeb's **Applications** or **Packages** page; picks a version label.
3. CSWeb marks it as the "active" version.
4. On each tablet's next sync, CSEntry detects the new version and prompts the user: "New version available — install?"
5. User installs; CSEntry restarts the app; in-progress cases are preserved if the DCF schema hasn't changed (see §13 for what's safe).

### Dashboards & alerts (per Inception Report §V.E)

CSWeb's built-in dashboards cover progress (vs target by cluster/region/facility), response rates, enumerator performance, quality indicators. Configure automated alerts for:

- Missing data patterns.
- Sync delays (device quiet > 36 h).
- Duplicate entries (same facility + same enumerator + same day).
- Enumerator-level non-response patterns.
- Unusual interview durations (too short → skipping; too long → confusion).

Data Manager + Assistant Data Managers own daily monitoring.

---

## 11a. Supervisor-app pattern (Popstan reference) <a id="11a-supervisor-app"></a>

The US Census Bureau ships an official CAPI reference architecture as part of CSPro 8.0 — the **Popstan CAPI Census** sample. It's not a separate "CSEntry Supervisor" binary; it's a **three-application composition** that implements role-based supervisor vs. interviewer workflows inside the ordinary CSEntry runtime. **Recommended as the scaffold for this project's field deployment.**

Location of the reference: `3_Resources/Tools-and-Software/CSPro/Examples 8.0/1 - Data Entry/CAPI Census/` (and upstream at `github.com/CSProDevelopment/examples`).

### Architecture — three cooperating apps + shared dictionaries

```
                         +-------------------+
                         |    Login.ent      |
                         | username + PIN    |
                         | writes persistent |
                         | login_supervisor  |
                         | login_interviewer |
                         +---------+---------+
                                   |
                                   v
                         +-------------------+
                         |    Menu.ent       |
                         | reads persistent  |
                         | role, branches:   |
                         +---------+---------+
                          /                  \
                         v                    v
           +--------------------+   +----------------------+
           | M_SUPERVISOR_MENU  |   | M_INTERVIEWER_MENU   |
           |  - create intvrs   |   |  - select assignment |
           |  - assign EAs      |   |  - collect cases     |
           |  - sync w/ intvrs  |   |  - sync w/ super     |
           |  - sync w/ HQ      |   |    (BT)              |
           |  - status report   |   |  - logout            |
           +---------+----------+   +----------+-----------+
                     |                         |
                     v                         v
           +--------------------+   +----------------------+
           |  (sync operations) |   |  Household.ent       |
           +--------------------+   |  (F1/F3/F4 for us)   |
                                    +----------------------+
```

Shared dictionaries drive role logic:

| Dictionary | Purpose | Key items |
|---|---|---|
| `PSC_STAFF_DICT` | Who is who | staff_code (UUID), username, PIN, **role**, **S_SUPERVISOR_STAFF_CODE** (links interviewer→their supervisor) |
| `PSC_ASSIGNMENTS_DICT` | Who does what where | province, district, EA, staff_code, **A_ROLE** (1=interviewer, 2=supervisor) |
| `PSC_GEOCODES_DICT` | Geographic hierarchy | **In our project, replaced with the four `shared/psgc_*.dcf` externals already built.** |

### The role-branching logic (from the sample)

`Menu.ent.apc` (simplified from lines 47–114 and 259–262):

```
numeric isInterviewer;
if login_interviewer <> "" then
    saved_staff_code = login_interviewer;
    isInterviewer = true;
elseif login_supervisor <> "" then
    saved_staff_code = login_supervisor;
    isInterviewer = false;
endif;

{ ... load the assignment's A_ROLE from PSC_ASSIGNMENTS_DICT ... }

if A_ROLE = 1 then
    skip to M_INTERVIEWER_MENU;
elseif A_ROLE = 2 then
    skip to M_SUPERVISOR_MENU;
endif;
```

Both menus live in the same `Menu.fmf`; enumerators and supervisors install the same `.pen` package but see different UI.

### Supervisor-only functions

From the Popstan sample's supervisor menu:

| Function | What it does |
|---|---|
| **Create interviewers** | Adds rows to `PSC_STAFF_DICT` with role=1, linked to this supervisor's staff_code. First-time setup or replacement-enumerator onboarding. |
| **Assign enumeration areas** | Adds rows to `PSC_ASSIGNMENTS_DICT` mapping EA to staff_code. Field manager enforces per Annex D replacement protocol. |
| **Sync with interviewer (Bluetooth)** | Push new/updated assignments down; pull completed cases up. Tablet-to-laptop, offline. |
| **Sync with headquarters (Internet)** | Push aggregated cases up to CSWeb; pull any new app version down. |
| **Interviewer status report** | Renders `Interviewer-Status-Report.html` (template in `Menu/`) showing per-enumerator completion counts, last sync time, QC flags. |
| **Change assignment** | Switch between supervised EAs if a supervisor covers multiple areas. |
| **Logout** | Clears persistent role vars. |

### Interviewer-only functions

| Function | What it does |
|---|---|
| **Select assignment** | Pick from EAs assigned to this user. |
| **Collect cases** | Launch the data-entry app (`Household.ent` in Popstan; **F1 / F3 / F4** in our project). |
| **Sync with supervisor (Bluetooth)** | Push new cases up; pull any updated app/assignment down. |
| **Change assignment / Logout** | Same as supervisor but without admin functions. |

### Mapping Popstan → this project

| Popstan component | This project equivalent | Notes |
|---|---|---|
| `Login/` | Reuse as-is | No change needed. |
| `Menu/` with `M_SUPERVISOR_MENU` + `M_INTERVIEWER_MENU` | Customize labels + add F2 Google Forms launch button for the interviewer menu | F2 is self-admin Google Forms primarily; interviewer menu can offer "Open F2 link" that calls `execsystem("https://...")`. |
| `Household/` (single app) | Three launch buttons: **F1 Facility**, **F3 Patient**, **F4 Household** — each calls the corresponding `.ent` via `execpff` | Menu item visible to an enumerator depends on their assignment type. |
| `PSC_GEOCODES_DICT` | `shared/psgc_*.dcf` externals + `PSGC-Cascade.apc` | Already built. |
| `PSC_STAFF_DICT` | Seed from ASPSI's roster — 20 supervisors, 100 enumerators | CSV → seed script. |
| `PSC_ASSIGNMENTS_DICT` | Seed from cluster allocation plan | From the Survey Manager's fieldwork map. |
| `Interviewer-Status-Report.html` | Customize KPIs for F-series: cases completed by form type, daily rate, replacement protocol flags | Live dashboard for supervisors in the field. |
| Bluetooth sync | Keep as-is | Matches Inception Report's tiered model. |
| Dropbox for HQ sync | **Replace with CSWeb** | Per Popstan readme: "for a census CSWeb would be a more appropriate solution." |

### Recommended adoption path

1. Clone the `CAPI Census/` sample into `deliverables/CSPro/supervisor_scaffold/` (keep original read-only in `3_Resources/`).
2. Replace `PSC_GEOCODES_DICT` references with our PSGC externals; wire `PSGC-Cascade.apc`.
3. Strip Popstan-specific Household form; replace with three launch buttons → F1/F3/F4 `.ent` files via `execpff`.
4. Seed `PSC_STAFF_DICT` from ASPSI HR list (use a Python seeder, not hand-typed).
5. Customize `Interviewer-Status-Report.html` for F-series KPIs.
6. Swap Dropbox sync for CSWeb sync endpoints.
7. Package the full bundle (`Login` + `Menu` + 3× F-app) as one `.pen`; deploy through CSWeb Packages.
8. Train supervisors on first-run setup (supervisor password → create supervisor PIN → create enumerator usernames).

### Open decisions (flag before implementing)

- [ ] Single `PSC_STAFF_DICT` across F1/F3/F4, or per-form? (Recommend single — same enumerator may work multiple forms.)
- [ ] Should F2 launch from the same menu? (F2 is Google Forms; a "Launch F2" link is trivial via `execsystem`.)
- [ ] What KPIs belong on the supervisor dashboard? (Discuss with Marriz + Airyne.)
- [ ] Supervisor password rotation policy — fixed or per-wave?

---

## 12. Field sync architecture (this project's tiered model) <a id="12-field-sync"></a>

Per Inception Report: CAPI via Android tablets; daily sync before 10 PM; weekly extract for QC. 20 supervisors, 100 enumerators (≈5 enumerators per supervisor).

### The tiered model

```
    Enumerator tablet ──(USB/Bluetooth, daily)──▶  Supervisor laptop
                                                          │
                                                          │ (HTTPS, daily <10pm)
                                                          ▼
                                                     CSWeb central
                                                          │
                                                          │ (weekly export)
                                                          ▼
                                                   Data Manager + ADMs
                                                          │
                                                          ▼
                                                  Stata / SPSS / reports
```

### Why tiered and not direct tablet → CSWeb?

- **Connectivity.** Field sites often have poor data; the supervisor's laptop aggregates over a local hotspot or waits for reliable connectivity.
- **Supervisor QC gate.** Supervisor reviews each case for completeness/plausibility **before** pushing upstream. This is where surprise checks and spot-check corrections happen.
- **Device troubleshooting.** When a tablet has issues, the supervisor has the local tools to fix it without blocking the central server.
- **Data integrity.** The local laptop holds the last "clean" copy; if a tablet is lost/stolen, cases aren't.

### Daily field workflow

| Time | Actor | Action |
|---|---|---|
| 07:00 | Enumerator | Start tablet, verify app version, verify assigned cases for the day. |
| 07:30–18:00 | Enumerator | Conduct interviews; save each case at completion; save-partial if interrupted. |
| 18:30 | Enumerator | Meet supervisor; handoff tablet for sync. |
| 19:00 | Supervisor | Bluetooth/USB sync tablet → laptop; supervisor reviews day's cases. |
| 19:30 | Supervisor | Apply corrections/flags (via case-level tool), sync laptop → CSWeb over HTTPS. |
| 21:00 | Supervisor | Final sync deadline; cases locked-in for the day. |
| 22:00 | Data Manager | Pulls up CSWeb dashboard; reviews alerts; follows up with supervisors on anomalies. |

### Weekly workflow

- **Friday afternoon**: Data Manager + ADMs run weekly extract → cleaning/validation scripts → QC report.
- **Friday check-in** (per Inception Report §QC): Survey Manager + Data Manager + ADMs + RAs + field supervisors. Issues → hot-patch queue for Monday deploy.

---

## 13. Mid-field update protocol <a id="13-update-protocol"></a>

**The most dangerous part of the lifecycle.** A bad mid-field update can corrupt or lose collected data. Read this twice.

### Classify the change before touching anything

| Change type | Safe? | Notes |
|---|---|---|
| Fix a label/translation typo | ✅ Safe | Deploy any time. |
| Add a new value-set option | ✅ Safe | Deploy any time; existing cases ignore new option. |
| Tighten a validation rule (`errmsg` where there was none) | ⚠ Usually safe | Existing cases remain valid; new cases flagged. If retroactive, run a post-hoc QC pass instead. |
| Loosen a validation rule | ✅ Safe | Deploy any time. |
| Change skip logic | ⚠ Partial risk | New cases follow new flow. Existing cases retain old answers for skipped-then-un-skipped items → will look like missing data. Document. |
| Fix a skip bug that caused data to be stored at wrong item | 🔴 Data-repair job | Deploy AND write a data-migration script for the already-collected cases. |
| Add a new item to an existing record | ⚠ Risky | DCF schema change. Existing cases will have NULL for the new item — fine if NA-coded, not fine if the analysis assumes presence. |
| Remove an item | 🔴 Never mid-field | Either keep the column and mark it deprecated, or wait for the next major version between fieldwork waves. |
| Change an item's length or type | 🔴 Never mid-field | Schema-breaking; existing cases will fail to load. |
| Change a value-set code | 🔴 Never mid-field | Old code in existing cases becomes meaningless. |

**Golden rule: never change the dictionary schema (item length, type, or value codes) during active fieldwork.** If you must, treat it as a new wave: close out the current wave, migrate the data, start fresh.

### Release cadence

- **Freeze:** Friday 17:00 — no merges into main for field-deployed code.
- **Deploy:** Monday 09:00 — push new package to CSWeb; tablets auto-pull during morning sync.
- **Notify:** Friday 17:00 — announce in #capi-scrum and Viber, 48 h lead time for supervisors.
- **Emergency hotfix:** Same-day deploy allowed only for data-loss or data-corruption bugs. Requires Carl sign-off + post-hoc announcement.

### Deploy flow (step-by-step)

1. **Branch & PR.** Never commit fixes directly to `main`. Open PR, tag Sean for QA.
2. **Regenerate.** `python generate_dcf.py`; if PSGC or shared: `python shared/build_psgc_lookups.py`.
3. **Bench-test on desktop CSEntry.** Repeat the applicable rows of §8's matrix.
4. **Pilot-test on one tablet.** Supervisor's spare tablet, offline sync, confirm install + case reload works.
5. **Bump version number.** Update `APP_VERSION` item or equivalent.
6. **Build `.pen`.** CSPro Designer → Deploy.
7. **Upload to CSWeb Packages.** Mark active; keep previous 2 versions available for rollback.
8. **Announce.** #capi-scrum: version, changelog, rollout window.
9. **Monitor morning sync.** Data Manager watches dashboard 09:00–12:00 Monday for install failures or anomaly spikes.
10. **Rollback trigger.** If > 5% of tablets fail install or a new regression surfaces → revert package pointer to previous version; tablets pull old version on next sync.

### Rollback plan

- CSWeb keeps the last 3 `.pen` versions.
- To roll back: in Packages UI, mark the previous version as active.
- Collected cases on the current version remain valid as long as schema was unchanged.
- If schema was changed and must be reverted → schema-migration script on CSWeb's DB; treat as incident.

### Change log discipline

Every deploy gets an entry in `deliverables/CSPro/CHANGELOG.md`:

```markdown
## v2.3.1 — 2026-05-04
- Fix: PROVINCE_HUC onfocus handler crashed when REGION was blank (E2-F1-023).
- Tweak: NA code 999 added to RESP_INCOME value set.
- No schema changes.
```

---

## 14. Data export, QC, and reporting <a id="14-data-export"></a>

### From CSWeb

- **CSV export** — for ad-hoc QC in Python/R/Excel.
- **SPSS / Stata export** — for the project's primary analysis stack (ASPSI uses Stata per Inception Report).
- **CSPro-native export** — `.dat` fixed-width + the live `.dcf`; round-trips cleanly into CSPro Tables.

### QC pipeline (weekly)

1. Data Manager pulls Stata/SPSS extract Friday morning.
2. Validation script (Stata `.do` or Python): completeness, range, cross-field, outlier checks.
3. Issues → issue log → supervisor follow-up next week.
4. QC report generated (consistency rates, completion %, outlier counts per enumerator).

### Reporting cadence

| Cadence | Audience | Content |
|---|---|---|
| Daily | Data Manager + Carl | Dashboard glance — sync counts, alerts, anomalies. |
| Weekly (Fri) | Survey Manager + Data Manager + ADMs + Supervisors | Progress vs target, QC flags, unresolved issues. |
| Biweekly | DOH counterparts | Progress report: % completion by region, quality indicators, blockers. |
| Tranche deliverables | DOH (contractual) | Progress Report at Month 11 (Tranche 3 — see `concepts/aspsi-doh-tranche-structure.md`). |

---

## 15. Roles & responsibilities <a id="15-roles"></a>

### Developer (Carl)

**Owns:** Phases 1–9, 11 (deploys). Mid-field hot-patches.
**Tools:** CSPro Designer (Windows), Python generators, Git, CSWeb Admin console.
**Deliverables:** DCFs, apps, packages, changelog, dev guide (this doc).
**Does not own:** DOH-facing comms (per `feedback_comms_lane_discipline`).

### QA Tester (Sean)

**Owns:** Bench testing, regression testing on each release, bug logging.
**Tools:** Desktop CSEntry, Android tablet, bug tracker in vault.
**Cadence:** Every PR before merge; every release before CSWeb upload.

### Field Supervisor (×20 in the field)

**Owns:** Daily sync with their 5 enumerators; case-level QC before upstream push; device troubleshooting.
**Tools:** CSEntry on tablet (for their own observation cases), supervisor laptop with sync tool, Bluetooth.
**Does not own:** Schema changes, logic fixes — those loop back to developer.

### Data Manager (Marriz Garciano)

**Owns:** CSWeb admin, daily alert review, weekly extracts, QC report.
**Tools:** CSWeb admin UI, Stata/SPSS, dashboard tool.
**Escalates to:** Carl (tech issues), Survey Manager (process issues), ASPSI PM (staffing).

### Assistant Data Managers (×3)

**Owns:** Daily monitoring in CSWeb; first-line supervisor support; duplicate/missing-data triage.

### Survey Manager

**Owns:** End-to-end project accountability; chairs Friday check-in.

### Field Manager (Airyne Almendral)

**Owns:** Supervisor performance, logistics, replacement-protocol decisions (Annex D).

### Project Director

**Owns:** ASPSI contractual commitments with DOH; escalations.

### For the bosses (stakeholder reporting)

Template for a weekly one-pager to PMs / DOH:

> **Week of YYYY-MM-DD — F1/F3/F4 CAPI progress**
> - Cases collected this week: N (cumulative N / target N, %)
> - Regions active: [list]
> - Completion rate: X% (cases submitted / cases assigned)
> - Key quality indicators: [missing-data %, duplicate %, avg interview duration]
> - Top 3 issues + mitigation
> - Upcoming: [next week's plan, any release scheduled]

---

## 16. Checklists <a id="16-checklists"></a>

### Pre-field freeze (right before training + pilot)

- [ ] All 12 phases of the workflow completed through phase 8 for each instrument.
- [ ] Pilot run on ≥ 1 tablet per supervisor region; all golden-path + 3 edge cases pass.
- [ ] Translations reviewed by native speakers in each of the 7 languages.
- [ ] PSA SSRCS clearance received.
- [ ] SJREB ethics approval received.
- [ ] Annex H (ICF) wording mirrored in CAPI intro screens.
- [ ] CSWeb provisioned, HTTPS live, admin + data-manager accounts created.
- [ ] Daily backup cron running, tested with a restore drill.
- [ ] CHANGELOG.md started, v1.0.0 tagged.
- [ ] Enumerator user accounts created (matching roster).
- [ ] Packages module has v1.0.0 marked active.
- [ ] Training Part I (supervisors/RAs, Los Baños) — 5 days complete.
- [ ] Training Part II (enumerators, regional) — complete.
- [ ] Field manual distributed; supervisor laptop sync-tool installed & tested.
- [ ] Supervisor-app scaffold (§11a) built; `PSC_STAFF_DICT` + `PSC_ASSIGNMENTS_DICT` seeded; supervisor/interviewer login tested per tablet.
- [ ] Tablet permissions pre-provisioned on every device: **Camera**, **Location (GPS)**, **Storage**, **Bluetooth**.
- [ ] GPS capture tested outdoors on ≥ 1 tablet per region; accuracy achievable within 20 m.
- [ ] Photo capture tested; `resample()` applied; per-photo size ≤ 200 KB verified.
- [ ] CSWeb map tab configured — lat/long items correctly mapped; test case shows on map.
- [ ] CSWeb case detail view tested with attached Image/Document items; binary blobs accessible to Data Manager role.
- [ ] Storage-quota plan for binary attachments (estimate: avg cases × avg photos × ~200 KB; confirm VPS disk headroom).

### Per-release deploy (mid-field update)

- [ ] Change classified (safe / risky / never) per §13.
- [ ] PR reviewed; Sean QA'd.
- [ ] Changelog updated with version + date.
- [ ] Bench test + pilot-tablet test green.
- [ ] Friday 17:00 announcement posted to #capi-scrum + Viber.
- [ ] Previous version kept in Packages for rollback.
- [ ] Monday 09:00 — upload + mark active.
- [ ] Monday 09:00–12:00 — Data Manager monitors install success.
- [ ] Tuesday — retrospective: any regressions? log them.

### Incident response (field-reported bug)

- [ ] Supervisor logs bug with: tablet ID, version, case ID, steps to reproduce, screenshot.
- [ ] Data Manager triages severity (data loss? data corruption? cosmetic?).
- [ ] Developer reproduces on bench.
- [ ] If data-loss/corruption: emergency hotfix lane (same-day deploy OK).
- [ ] If cosmetic: queue for next scheduled release.
- [ ] If schema-breaking: escalate, do NOT deploy — decide with Survey Manager.

### Field close-out

- [ ] All tablets synced a final time; confirm case counts match CSWeb.
- [ ] Final export (CSV + SPSS + Stata + CSPro-native) taken and archived.
- [ ] Database snapshot + WAR version archived to cold storage (B2 / S3 Glacier).
- [ ] Tablets wiped of enumerator credentials before collection.
- [ ] CSWeb admin disables enumerator logins; keeps data-manager + archive-read-only roles.
- [ ] Final QC report delivered to DOH.
- [ ] Post-mortem: what to change for next wave.

---

## 17. Appendices <a id="17-appendices"></a>

### Appendix A — VPS provisioning (Ubuntu 22.04, Tomcat 9 + MySQL 8)

Run as root on a fresh Ubuntu 22.04 VPS (any provider):

```bash
# --- system basics ---
apt update && apt upgrade -y
apt install -y ufw fail2ban unattended-upgrades
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# --- Java + Tomcat ---
apt install -y openjdk-17-jdk tomcat9 tomcat9-admin
systemctl enable --now tomcat9

# --- MySQL ---
apt install -y mysql-server
mysql_secure_installation   # interactive — set root password, remove anonymous users

# --- CSWeb DB + user ---
mysql -u root -p <<'SQL'
CREATE DATABASE csweb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'csweb'@'localhost' IDENTIFIED BY 'REPLACE_WITH_STRONG_PW';
GRANT ALL PRIVILEGES ON csweb.* TO 'csweb'@'localhost';
FLUSH PRIVILEGES;
SQL

# --- Nginx reverse proxy + TLS ---
apt install -y nginx certbot python3-certbot-nginx
# (drop the Nginx config from Appendix B into /etc/nginx/sites-available/csweb, enable, test, reload)
certbot --nginx -d csweb.<your-domain>.ph

# --- Deploy CSWeb WAR ---
# Download the WAR matching your CSPro version from https://www.csprousers.org/
cp csweb-<version>.war /var/lib/tomcat9/webapps/csweb.war
systemctl restart tomcat9
# First boot auto-creates tables; then visit https://csweb.<domain>.ph/csweb and complete setup wizard.

# --- Backups ---
# see Appendix C
```

### Appendix B — Nginx reverse-proxy config

`/etc/nginx/sites-available/csweb`:

```nginx
server {
    listen 80;
    server_name csweb.<your-domain>.ph;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name csweb.<your-domain>.ph;

    ssl_certificate     /etc/letsencrypt/live/csweb.<your-domain>.ph/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/csweb.<your-domain>.ph/privkey.pem;

    client_max_body_size 100M;   # case uploads can be large

    location / {
        proxy_pass         http://127.0.0.1:8080;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

Enable: `ln -s /etc/nginx/sites-available/csweb /etc/nginx/sites-enabled/` → `nginx -t` → `systemctl reload nginx`.

### Appendix C — Daily backup cron

`/etc/cron.d/csweb-backup`:

```cron
# Daily at 02:30 — dump MySQL, compress, ship to B2 (or S3).
30 2 * * * root /usr/local/bin/csweb-backup.sh >> /var/log/csweb-backup.log 2>&1
```

`/usr/local/bin/csweb-backup.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d-%H%M%S)
OUT=/var/backups/csweb-$TS.sql.gz
mysqldump --single-transaction --routines --triggers -u csweb -p"${CSWEB_DB_PW}" csweb | gzip -9 > "$OUT"
# ship — pick one:
# b2 upload-file <bucket> "$OUT" "csweb/$TS.sql.gz"
# aws s3 cp "$OUT" "s3://<bucket>/csweb/$TS.sql.gz"
# rclone copyto "$OUT" "remote:csweb/$TS.sql.gz"
find /var/backups -name 'csweb-*.sql.gz' -mtime +14 -delete
```

Retain 14 days local + forever in cold storage. **Do a restore drill at least once before fieldwork starts** — an untested backup is not a backup.

### Appendix D — Troubleshooting

| Symptom | Likely cause | First check |
|---|---|---|
| Tablet stuck on sync, spinner forever | DNS or TLS issue on CSWeb side | `curl https://csweb.<domain>.ph` from a laptop on same network |
| "Application failed to load" on tablet after update | Schema-breaking change deployed | Check CHANGELOG; revert package; treat as incident |
| Cascade dropdown empty | External dict not bundled in `.pen`, OR `onfocus` handler not wired | Open `.pen` contents; verify `psgc_*.dat` present; check `.app` for `onfocus` procs |
| Case count in CSWeb < sum of tablet counts | Tablet has unsynced cases, or sync rejected on validation | Check CSWeb sync logs for 4xx/5xx; check tablet's outbox |
| CSPro Designer refuses to open `.dcf` | Likely corrupted by manual edit + regeneration collision | Regenerate from `generate_dcf.py`; never hand-edit |
| Duplicate cases showing in dashboard | Same case synced twice with different IDs | Usually tablet time-drift; confirm NTP on tablets |
| Enumerator "can't see new version" | Version not marked active, OR sync happened before upload | Confirm Packages module active version; force manual sync |
| Em-dash / bullet characters look like `â€”` in exports | UTF-8 / CP1252 mojibake on Windows | Force UTF-8 in the generator script (`encoding="utf-8"`) — see `windows_utf8_gotcha` |
| `gps(read, ...)` always returns 0 | Permission denied, indoors, or GPS disabled | Check tablet Location permission for CSEntry; test outdoors with clear sky; confirm "High accuracy" mode on Android |
| `Image.takePhoto()` returns 0 immediately | Camera permission not granted OR user cancelled | Grant permission in tablet Settings → Apps → CSEntry → Permissions |
| Uploaded photos fill CSWeb disk | `resample()` omitted before `save()` | Add `obj.resample(maxWidth:=1600, maxHeight:=1200)` before every `.save()`; bump disk on VPS |
| CSWeb map tab shows no cases | Lat/long items not configured in CSWeb's map settings, OR items stored as numeric with wrong decimal scale | Map settings → pick the right item names; confirm lat/long captured as signed decimal degrees |
| Map object doesn't render on tablet | Google Play Services missing/old, or offline | Update Play Services via Play Store; confirm tablet has network (Map requires online tiles) |
| Supervisor sees interviewer menu (or vice versa) | `login_supervisor` / `login_interviewer` persistent vars not cleared on logout | Audit Login.ent.apc — logout must set both vars to `""` |

---

## Glossary

| Term | Meaning |
|---|---|
| **CAPI** | Computer-Assisted Personal Interviewing — face-to-face interview captured on a tablet. |
| **CSPro** | The authoring suite from the US Census Bureau. Windows desktop. |
| **CSEntry** | The runtime. Android is primary here. |
| **CSWeb** | The server. Tomcat + MySQL webapp. |
| **DCF** | Data dictionary file — the schema. |
| **`.pen`** | Deployable package for CSEntry Android. |
| **PSGC** | Philippine Standard Geographic Code (PSA's authoritative geo list). |
| **VS** | Value set — the enumerated choices for a coded item. |
| **Cascade** | Parent-filtered child value sets (region → province → city → barangay). |
| **Sync** | Transfer of cases and packages between CSEntry and CSWeb. |
| **Packages module** | CSWeb's application-distribution mechanism. |
| **Tranche** | Contractual payment milestone (this project: 15%, 40%, 25%, 20% across 4 tranches). |

---

*This is a living document. When field experience invalidates a rule, update it here — don't rely on memory.*
