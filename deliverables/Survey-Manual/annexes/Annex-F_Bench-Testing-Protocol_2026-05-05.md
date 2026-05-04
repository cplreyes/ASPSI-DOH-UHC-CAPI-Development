# Annex F — Bench Testing Protocol

**Audience:** Data Programmer, Research Associates, Survey Manager
**Purpose:** Describes how each CAPI application is tested at the ASPSI office before deployment to the field, in fulfillment of Protocol §XI's bench testing requirement.

---

## Scope

Bench testing is conducted for every CAPI application before any version is deployed to the field:

- F0 — Field Supervisor App
- F1 — Facility Head Survey
- F3a — Patient Listing
- F3b — Patient Interview
- F4a — Household Listing
- F4b — Household Interview

Bench testing is also conducted for every **substantive amendment** to a deployed application, as defined in Annex G (CAPI Versioning and Amendment Log).

## When bench testing occurs

| Event | Bench test required |
|---|---|
| Initial development of a new module | Full bench test |
| Substantive amendment (question wording, response options, skip patterns, item add/remove) | Targeted bench test on the affected sections + integration check |
| Minor amendment (typo fixes, display tweaks, range-check corrections without methodological impact) | Smoke test only — confirm the change works and nothing else broke |
| Pre-pilot deployment | Full bench test |

## Roles

- **Data Programmer** — present throughout; applies fixes as they are identified; signs off the bench test log when complete.
- **Research Associate (×2 minimum per module)** — simulate respondents independently; do not coordinate answers; cover the full question set.
- **Survey Manager** — final sign-off authority; reviews the bench test log and confirms readiness for deployment.

## Procedure

### Preparation

1. The Data Programmer compiles the test plan listing every question, every skip-pattern branch, every numeric range boundary, and every value-set option that triggers routing.
2. The Data Programmer publishes the application to a test instance of CSWeb (separate from production).
3. RAs install the test instance on their own tablets via the test CSWeb URL.

### Execution

1. Each RA works through the entire questionnaire as if interviewing a respondent, exercising every skip path. RAs do not see each other's entries.
2. Findings are recorded in the **Bench Testing Log** (template below) keyed by question ID, with: date, module, question ID, problem description, fix applied, re-test result.
3. As findings are raised, the Data Programmer applies fixes and pushes a new build to the test instance. RAs re-test the affected sections.
4. The application's data syncs to the test CSWeb instance and is verified to land correctly with all version stamps.

### Sign-off

The bench test is complete only when **all five** of these are true:

1. Every skip pattern routes to the correct destination.
2. Every range check accepts valid entries and rejects invalid ones.
3. Every looping structure (roster) executes correctly in both single-row and many-row cases.
4. A completed test record successfully syncs to CSWeb.
5. The version stamp, GPS auto-capture, and verification photo (where applicable) all behave correctly.

The Data Programmer signs off the bench test log; the Survey Manager countersigns. The signed-off version becomes the authoritative baseline for production deployment.

## Bench Testing Log template

| # | Date | Module | Version | Question ID | Problem | Fix Applied | Re-test Result | RA | DP Initial |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |  |  |
| ... |  |  |  |  |  |  |  |  |  |

**Closing summary:**

| Field | Value |
|---|---|
| Module | (e.g., F0) |
| Version tested | (e.g., F0_v1.0.0) |
| Bench test start date |  |
| Bench test sign-off date |  |
| Total findings | (count) |
| Open findings at sign-off | (must be 0) |
| Data Programmer sign-off |  |
| Survey Manager sign-off |  |

## Critical bench-test cases (illustrative)

The following are minimum bench-test cases per module type. The Data Programmer prepares an exhaustive list per actual questionnaire content.

### F0a Facility Visit Log

1. Happy path — courtesy call approved with head present; all letters delivered; HCW list captured; verification photo; departure stamped.
2. Refused courtesy — `COURTESY_OUTCOME=3`; reason captured; HEAD_* fields skipped.
3. Authorized representative — `COURTESY_OUTCOME=2`; HEAD_* fields point to the representative.
4. Sub-6-month tenure warning — `HEAD_TENURE_MONTHS=4`; warning fires; supervisor can override with note.
5. GPS unavailable — `getlocation()` returns null; case warns but proceeds.
6. BHW exclusion not confirmed — case blocks until corrected (per Protocol §VIII).
7. Same-day re-entry — partial save restores correctly.
8. Sync test — case + roster + photo all sync to CSWeb test instance.

### F1 Facility Head Survey, F3a/b, F4a/b

The Data Programmer prepares per-module test plans matching the questionnaire's logic specification.

## Roll-up to the project record

Signed-off bench test logs are filed in the project's quality-assurance archive and referenced in the CAPI Versioning and Amendment Log (Annex G) for the corresponding version.
