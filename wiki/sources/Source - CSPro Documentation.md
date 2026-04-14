---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Documentations/CSPro Documentation]]"
date_ingested: 2026-04-09
tags: [cspro, csentry, documentation, reference, official]
---

# Source - CSPro Documentation

Web clipping of the [official CSPro documentation index](https://www.census.gov/data/software/cspro/documentation.html) maintained by the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/US Census Bureau|US Census Bureau]] (page last revised 2024-01-30). This is a navigation page — it links to the canonical PDFs but does not contain their content.

## What's on the page

### Built-in help
- The CSPro desktop application ships with an in-app help system. Press **F1** or use the **Help** menu from the main program or any tool to open it.
- The desktop help system is the primary reference for designing census/survey applications, including those targeting CSEntry Android (see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro|CSPro]] for the Android/CAPI role in this project).

### Official PDF guides (CSPro 8.0)
| Guide | Purpose | URL |
|---|---|---|
| Getting Started Guide | Orientation for new users | https://www2.census.gov/software/cspro/documentation/start80.pdf |
| Complete User's Guide (incl. Logic Reference) | Authoritative reference for the desktop tools and CSPro logic language | https://www2.census.gov/software/cspro/documentation/cspro80.pdf |
| Data Entry User's Guide | CSEntry desktop data entry | https://www2.census.gov/software/cspro/documentation/csent80.pdf |
| Data Entry User's Guide for Android | CSEntry on Android phones/tablets | https://www.census.gov/data/software/cspro/documentation/android-user-guide.html |
| CSPro Android CAPI – Getting Started | Building a tablet CAPI app end-to-end | https://www2.census.gov/software/cspro/documentation/cspro-capi-getting-started.pdf |
| CSPro Android – Data Transfer Guide | Sync between tablets and the server (CSWeb / Dropbox / Bluetooth) | https://www2.census.gov/software/cspro/documentation/cspro-synchronization-help.pdf |
| CSPro 8.0.0 Release Notes | What changed in 8.0.0 | https://www2.census.gov/software/cspro/documentation/readme.txt |

A sample CAPI application is downloadable at https://www2.census.gov/software/cspro/documentation/cspro-mycapi-sample.zip.

### Other resources
- **Video instruction** — CSPro E-Learning Videos on the Census Bureau site and the `uscensusbureau` YouTube channel.
- **Email support** — `cspro@lists.census.gov`. The team accepts questions in English, French, or Spanish, and asks that supporting programs/data files be attached.

## Why this matters for the project

CSPro 8.0 is the chosen platform for the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]] CAPI build (see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro|CSPro]] concept page for the rationale vs SurveyCTO). This source pins the canonical references Carl will rely on for:

1. **Dictionary and form authoring** — Complete User's Guide, especially the Logic Reference, is the source of truth for skip logic, validations, and the CSPro logic language used in F1–F4 dictionaries.
2. **Tablet CAPI build** — CSPro Android CAPI Getting Started is the closest official walkthrough to what Carl is building for F1, F3, and F4.
3. **CSWeb sync** — Data Transfer Guide governs how completed interviews move from enumerator tablets to the server (relevant to [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]] deployment).
4. **Version pinning** — Project is on CSPro 8.0; the 8.0.0 release notes are the reference for any version-specific behavior.

## Notes and caveats

- The clipping is a *links page*, not the actual documentation content. To capture the substantive material (logic reference, CAPI walkthrough, sync protocol), the linked PDFs need to be fetched and ingested separately.
- Page last revised 2024-01-30 — links should be considered current as of that date. CSPro is past 8.0 in the wild (8.0.x patches, possibly newer minors); confirm the project is locked to 8.0 before treating these guides as the only reference.
- The desktop F1 help system contains material that may not appear in the PDFs at all — for advanced questions, the in-app help is the more complete source.
