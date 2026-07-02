---
type: source-summary
source: "Gmail thread 19eab54cbdef2859 — aspsi.doh.uhc.survey2@gmail.com → clreyes6@up.edu.ph, 2026-06-09"
date_ingested: 2026-06-28
tags: [capi, survey-design, philhealth, f3-patient, f4-household, reinstatement, doh-decision]
---

# Source - PhilHealth Reinstatement Email (Kidd 2026-06-09)

**Email, ASPSI (Kidd, via `aspsi.doh.uhc.survey2@gmail.com`) → Carl (`clreyes6@up.edu.ph`), 2026-06-09 07:41 UTC.** Subject: *"Questions for the Patient and Household Survey."* cc: `spprt.aspsi.doh.uhc.survey2@gmail.com`, `cjrocamora@gmail.com` (Juvy). Fetched 2026-06-28 via the UP-account Gmail connector. This is the authoritative instruction to **reinstate two PhilHealth-registration sub-questions** on the **Patient (F3)** and **Household (F4)** instruments. Tracked in scrum as **E2-F3-PHILHEALTH / E2-F4-PHILHEALTH**.

## The decision / backstory

While organizing files, ASPSI reviewed a recording of a previous DOH meeting and realized the team had **agreed to reinstate additional PhilHealth-registration questions that were previously omitted following comments from OAAED**. DOH wanted these items included given their **intended use of the information**, and their importance was emphasized by **Sir LJ** (LJ Villarante, DOH). The questions were **not reinserted into the survey instruments as agreed** — ASPSI flagged this as their oversight and apologized. Both questions are **conditional** and can be incorporated "with minimal disruption."

> [!note] This is a DOH-originated, ASPSI-relayed questionnaire change — not a tester finding. It belongs to Epic 2 (questionnaire design) feeding Epic 3 (build), and rides the patch loop once the value sets are in hand. Carl produces the CAPI; ASPSI is the DOH interface ([[feedback_carl_produces_capi_no_doh_comms]]).

## The reinstated questions (verbatim from the email)

### Patient Survey (F3) — Section D, after Q38 ("Are you currently registered with PhilHealth?")

| New Q | Wording (verbatim) | Asked of |
|---|---|---|
| **Q38.1** | *When did you register and receive your PhilHealth PIN?* | Respondents **currently registered** (Q38 = Yes) |
| **Q38.2** | *Why are you not registered with PhilHealth?* | Respondents **not currently registered** (Q38 = No) |

### Household Survey (F4) — after Q45 ("Are you currently registered with PhilHealth?")

| New Q | Wording (verbatim) | Asked of |
|---|---|---|
| **Q45.1** | *When did you register and receive your PhilHealth PIN?* | **Registered** (Q45 = Yes) |
| **Q45.2** | *Why are you not registered with PhilHealth?* | **Not registered** (Q45 = No) |

The F3 and F4 stems are **identical**; only the host-instrument question numbers differ.

## The value sets (the 3 attached PNGs) — NOT YET CAPTURED

The email carries **3 inline PNG attachments** (yellow-highlighted in the body) that contain the **response-option lists** for these questions — i.e. the answer codes/labels Q38.1/Q38.2/Q45.1/Q45.2 must offer:

1. `0-02-08-fb37984e…_fcbc90fcc7574688.png` (453×358) — Patient-survey insertion mock-up / options.
2. `0-02-08-aef6f334…_811af2c664163898.png` (453×297) — Household-survey insertion mock-up / options.
3. `be5fe15d-a2e8-4bb0-a8c2-b2cbb0bd22af.png` (449×473) — the longer options table (likely the "why not registered" reasons list).

> [!warning] Connector limitation — images not downloadable
> The claude.ai Gmail MCP exposes the email **body + attachment IDs** but has **no attachment-download tool** ([[reference_drive_gmail_connector_limits]]). The question **stems and routing are now captured** (above), but the **exact response options remain in the images only**. The CAPI build cannot be coded accurately without them (you cannot guess a value set — verbatim rule). **Unblock:** Carl downloads the 3 PNGs from this email and drops them into the repo (e.g. `deliverables/CSPro/_philhealth-valuesets/`); they can then be read directly and the build completed.

## Routing & build implications

- **Q38.1 / Q45.1** ("when registered") — a date/timing field; **the response format is in image 1/2** (free date vs. year vs. categorical — to confirm from the image).
- **Q38.2 / Q45.2** ("why not registered") — a reasons list; **options in image 3** (to confirm; F3 already has an analogous "why-no-PhilHealth" list at Q114 `Q114_NO_PH` — do **not** assume they match).
- **F3** insertion is on the single patient; per the pre-test design ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/PRETEST-READINESS-2026-06-27|pretest-readiness]]): Q38=Yes → Q38.1 → skip the registration-assistance items Q43/Q44; Q38=No → Q38.2 → Q43.
- **F4** caveat — **Q45 lives inside the Section-C per-member household roster**. Whether Q45.1/Q45.2 are asked **per member** (literal "after Q45") or once for the respondent is a **scope question to confirm** before building, since it materially changes the roster.
- **Build footprint** (once value sets land): `dcf` (new fields + value sets) + `apc` (gates/skip) + `qsf` (question text) **× F3 and F4**, regenerate → verify → Designer compile → Publish → deploy to CSWeb → patch notes → **harmonization codebook ripple** (new fields). ~3h.

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire]] — host instrument for Q38.1/Q38.2.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire]] — host instrument for Q45.1/Q45.2.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD]] — originating client; decision emphasized by Sir LJ (LJ Villarante).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI]] — relaying party (Kidd).
- `deliverables/CSPro/F3/F3-Skip-Logic-and-Validations.md` · `deliverables/CSPro/F4/F4-Skip-Logic-and-Validations.md` — specs updated 2026-06-28 with the reinstated questions (value sets pending).
