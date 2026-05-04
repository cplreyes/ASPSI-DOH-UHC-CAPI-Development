# Annex G — CAPI Versioning and Amendment Log

**Audience:** Data Programmer, Survey Manager, Project Lead, DOH-PMSMD technical reviewers
**Purpose:** Defines how CAPI applications are versioned, how changes are categorized and authorized, and how the amendment log is maintained, in fulfillment of Protocol §XI's version-control requirement.

---

## Why versioning matters

Every dataset extracted from CSWeb must be traceable to the exact CAPI application version that produced it. Without versioning, methodological changes mid-fieldwork are invisible in the final analysis, and audit replication becomes impossible. Versioning protects DOH's analytic conclusions and SJREB's ethics-approval scope.

## Version stamping

Every deployed CAPI application carries a version number embedded in a hidden ID item, `CAPI_VERSION`, on every case it produces. The version follows semantic versioning conventions:

```
<MODULE>_v<MAJOR>.<MINOR>.<PATCH>
```

Examples: `F0_v1.0.0`, `F1_v2.1.3`, `F3a_v1.5.0`.

When a case is uploaded to CSWeb, the version is preserved with the data. Datasets exported for analysis carry the version in every record, so the exact instrument behind any observation is traceable.

## Change categories

| Category | Examples | Authorization | Bench test scope |
|---|---|---|---|
| **Substantive** | Question wording change, response option add/remove, skip-pattern change, item add/remove, eligibility logic change | DOH-PMSMD concurrence required; Survey Manager and Project Lead sign-off | Full or targeted bench test |
| **Minor** | Typographical fix, display tweak, range-check correction without methodological impact | Data Programmer; notification to Survey Manager | Smoke test |

A change that is methodologically material but presented as "minor" must always be classified as substantive — when in doubt, escalate.

## Version increment rules

| Increment | Trigger |
|---|---|
| **MAJOR** (e.g., 1.0.0 → 2.0.0) | Architectural change (e.g., F3 split into F3a + F3b); new module added |
| **MINOR** (e.g., 1.0.0 → 1.1.0) | Substantive amendment to an existing module |
| **PATCH** (e.g., 1.0.0 → 1.0.1) | Minor amendment |

Pre-deployment versions use the `0.x.y` major and are never used in production data collection.

## Amendment log

Maintained as a single rolling document, one row per amendment per module.

### Log fields

| Field | Description |
|---|---|
| `Amendment ID` | Sequential within the project (e.g., AMD-001, AMD-002) |
| `Date` | Date the amendment was authorized |
| `Module` | F0, F1, F3a, F3b, F4a, F4b |
| `Version before` | Version superseded |
| `Version after` | New version |
| `Category` | Substantive / Minor |
| `Description` | What changed, in plain language |
| `Reason` | Why the change was needed (e.g., bench test finding, field issue, methodology update from Protocol Vx, DOH-PMSMD request) |
| `Authorization basis` | Who approved (DOH-PMSMD email date, Survey Manager initials, etc.) |
| `Files affected` | Which DCF, logic, or external dictionary files were modified |
| `Bench tested` | Yes (full / targeted / smoke) / No |
| `Deployed to field` | Date of deployment |
| `Notification sent` | Date Field Supervisors were notified |

### Log template

| AMD ID | Date | Module | Ver. Before | Ver. After | Category | Description | Reason | Authorization | Files | Bench | Deployed | Notified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AMD-001 | 2026-05-XX | F0 | — | F0_v1.0.0 | (initial) | Initial release | Bench-test sign-off | Survey Mgr 2026-05-XX | F0.dcf, F0.apc | Full | 2026-05-XX | 2026-05-XX |
| AMD-002 |  |  |  |  |  |  |  |  |  |  |  |  |
| ... |  |  |  |  |  |  |  |  |  |  |  |  |

## Authorization workflow

### Substantive change

1. Issue is identified — by bench testing, field report, methodology team, or DOH-PMSMD.
2. Data Programmer drafts the change spec with rationale and impact analysis.
3. Survey Manager and Project Lead review.
4. Project Lead requests DOH-PMSMD concurrence (email or formal letter as appropriate).
5. On concurrence, Data Programmer implements, bench-tests, and deploys.
6. Amendment log updated; Field Supervisors notified through the F0e ticket channel.
7. SJREB notification filed if the change is methodologically material to the ethics-approved protocol.

### Minor change

1. Issue is identified.
2. Data Programmer implements and smoke-tests.
3. Survey Manager is notified (email or Slack).
4. Amendment log updated; Field Supervisors notified through the F0e channel.

## Field deployment

After authorization and bench testing, the new version is published to the production CSWeb. Field Supervisors prompt enumerators to update their applications at the next sync. The previous version remains valid for in-progress cases until they are completed; new cases use the new version.

The dashboard tracks the version distribution across active cases; the Data Programmer monitors for any tablet still on an old version after a 48-hour grace window.

## Roll-up at project close

The complete amendment log is included in the final project deliverable to DOH-PMSMD as part of the methodology audit trail. The signed-off version of every CAPI application is archived with the project's source code repository.
