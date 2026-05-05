# Annex 2 — Technical Reference

This annex provides the technical reference behind the Survey Manual's CAPI sections. It is organized in five sections.

| Section | Topic |
|---|---|
| 2.1 — Data Transmission and Storage | Server architecture, synchronization, backup, data privacy, access controls |
| 2.2 — Bench Testing Protocol | Pre-deployment quality assurance for CAPI applications |
| 2.3 — Versioning and Amendment Log | Version stamping, change governance, amendment audit trail |
| 2.4 — Refusal and Replacement Logging | Reason codes, replacement chain, daily report |
| 2.5 — CAPI Application Architecture Reference | Module map, data flow, identifier scheme |

---

# Section 2.1 — Data Transmission and Storage

## Architecture overview

Field tablets running CSEntry sync completed cases to the project's CSWeb server, hosted on a virtual private server managed by ASPSI. The Healthcare Worker Survey, which is web-based, submits to its own backend through a secure proxy that authenticates each submission with a short-lived token. Both data streams are joined at analysis time using the facility identifier and the listing date.

## CSWeb server

- **Hosting.** Private virtual private server in a Philippine or nearby Southeast Asian zone for low-latency synchronization from field tablets.
- **Software.** The CSPro CSWeb application running on the standard Apache Tomcat plus MariaDB or MySQL configuration recommended by the U.S. Census Bureau.
- **Encryption.** All transmissions are encrypted with TLS 1.2 or higher. The server presents a Let's Encrypt certificate on a project-specific subdomain.
- **Authentication.** Each enumerator and Field Supervisor has a unique account with a password issued at training. Read-only "Supervisor" accounts allow Field Supervisors to view dashboards without altering data.
- **Authorization.** Account roles are: Enumerator (write own cases), Supervisor (read all cases in coverage area), Data Programmer (administrative), and Analyst (read-only export).

## Healthcare Worker Survey backend

The Healthcare Worker Survey submits to a separate proxy that authenticates submissions through short-lived tokens issued at survey start. The proxy writes to the Healthcare Worker Survey staging database. The staging database is read-only to the Data Programmer for daily extraction; HCW responses are joined to the CSWeb dataset by facility identifier and listing date during analysis.

## Synchronization schedule

| Trigger | Frequency | Initiated by |
|---|---|---|
| Per case completion | Whenever a case is marked complete with network available | CSEntry, automatic |
| End of field day | Once daily, at the team's lodging | Enumerator and Field Supervisor manually |
| On demand | Any time, for diagnostic or recovery purposes | Field Supervisor |

The Data Programmer monitors the CSWeb dashboard daily for transmission gaps and reconciles any missing cases with the field team within 24 hours.

## Backup

| Backup | Frequency | Retention | Storage |
|---|---|---|---|
| CSWeb database snapshot | Daily, automated | 30 days, rolling | VPS local |
| Off-site copy | Weekly, automated | 90 days, rolling | Encrypted archive in a separate jurisdiction |
| Healthcare Worker Survey staging snapshot | Daily, automated | 30 days, rolling | Encrypted object storage |
| Project archive | At project close | 5 years per ASPSI and DOH retention policy | Encrypted offline media |

## Data privacy

The deployment complies with the Data Privacy Act of 2012 (Republic Act No. 10173). Personally identifying information collected during patient and household listing is segregated from analytic variables and accessible only to the Data Programmer and the field-team supervisors with an operational need. The dataset shared with DOH-PMSMD and SJREB for review is a de-identified analytic dataset; no personally identifying information is included in any deliverable analytic file. The CSWeb server's logs do not record question-level responses, only sync metadata such as timestamps, case identifiers, and version stamps.

## Access controls

Only the Data Programmer holds administrative access to the virtual private server. Credentials are rotated quarterly and at any project-staffing handoff. CSWeb account passwords are user-changeable at first login. All write operations to the production data are audit-logged. Read-only analytic exports are produced by the Data Programmer and shared with analysts via authenticated download links; raw production access is not granted to analysts.

## Incident response

In the event of a confirmed data exposure or unauthorized access, the Data Programmer notifies the Project Lead and Survey Manager within 1 hour of confirmation. The Project Lead notifies DOH-PMSMD and SJREB within 24 hours, consistent with the disclosures in the Informed Consent Forms. A written incident report is filed within 72 hours per the Data Privacy Act, and the National Privacy Commission is notified if applicable. The CSWeb server is isolated, logs are preserved, and affected respondents are notified per the commitment in the consent forms.

## Project close

At the close of the engagement, the final dataset is extracted, de-identified, and delivered to DOH-PMSMD per the contract. The CSWeb server is wiped after the contractual data-retention window. Encrypted archival copies are retained per ASPSI's record-retention policy.

---

# Section 2.2 — Bench Testing Protocol

## Scope

Bench testing is conducted for every CAPI application — the Facility Head Survey, Patient Listing, Patient Interview, Household Listing, Household Interview, and the Supervisor App — before any version is deployed to the field. Bench testing is also conducted for every substantive amendment to a deployed application.

## When bench testing occurs

| Event | Bench test required |
|---|---|
| Initial development of a new module | Full bench test |
| Substantive amendment (question wording, response options, skip patterns, item add or remove) | Targeted bench test on the affected sections, plus an integration check |
| Minor amendment (typographical fix, display tweak, range-check correction without methodological impact) | Smoke test only |
| Pre-pilot deployment | Full bench test |

## Roles

- **Data Programmer.** Present throughout. Applies fixes as discrepancies are identified. Signs off the bench testing log when complete.
- **Research Associate (two minimum per module).** Simulate respondents independently. Do not coordinate answers. Cover the full question set.
- **Survey Manager.** Final sign-off authority. Reviews the bench testing log and confirms readiness for deployment.

## Procedure

**Preparation.** The Data Programmer compiles the test plan, listing every question, every skip-pattern branch, every numeric range boundary, and every value-set option that triggers routing. The Data Programmer publishes the application to a test instance of the project server, separate from production. Research Associates install the test instance on their own tablets via the test server URL.

**Execution.** Each Research Associate works through the entire questionnaire as if interviewing a respondent, exercising every skip path. Research Associates do not see each other's entries. Findings are recorded in the Bench Testing Log keyed by question identifier, with date, module, question identifier, problem description, fix applied, and re-test result. As findings are raised, the Data Programmer applies fixes and pushes a new build to the test instance. Research Associates re-test the affected sections. The application's data syncs to the test instance and is verified to land correctly with all version stamps.

**Sign-off.** The bench test is complete only when all five of the following conditions are met:

1. Every skip pattern routes to the correct destination.
2. Every range check accepts valid entries and rejects invalid ones.
3. Every roster executes correctly in both single-row and many-row cases.
4. A completed test record successfully syncs to the project server.
5. The version stamp, GPS auto-capture, and verification photo, where applicable, all behave correctly.

The Data Programmer signs off the bench testing log; the Survey Manager countersigns. The signed-off version becomes the authoritative baseline for production deployment.

## Bench Testing Log template

| # | Date | Module | Version | Question ID | Problem | Fix Applied | Re-test Result | RA initials | DP initials |
|---|---|---|---|---|---|---|---|---|---|
|   |   |   |   |   |   |   |   |   |   |

**Closing summary.** Module, version tested, bench test start date, sign-off date, total findings, open findings (must be zero), Data Programmer sign-off, Survey Manager sign-off.

## Roll-up

Signed-off bench testing logs are filed in the project's quality-assurance archive and referenced in the Versioning and Amendment Log (Section 2.3) for the corresponding version.

---

# Section 2.3 — Versioning and Amendment Log

## Why versioning matters

Every dataset extracted from the project server must be traceable to the exact CAPI application version that produced it. Without versioning, methodological changes mid-fieldwork are invisible in the final analysis, and audit replication becomes impossible. Versioning protects DOH's analytic conclusions and SJREB's ethics-approval scope.

## Version stamping

Every deployed CAPI application carries a version number embedded in a hidden identifier on every case it produces. The version follows semantic versioning: a major version, a minor version, and a patch version. Examples are version 1.0.0, version 2.1.3, version 1.5.0.

When a case is uploaded to the project server, the version is preserved with the data. Datasets exported for analysis carry the version in every record, so the exact instrument behind any observation is traceable.

## Change categories

| Category | Examples | Authorization | Bench test scope |
|---|---|---|---|
| Substantive | Question wording change, response option add or remove, skip-pattern change, item add or remove, eligibility logic change | DOH-PMSMD concurrence required; Survey Manager and Project Lead sign-off | Full or targeted bench test |
| Minor | Typographical fix, display tweak, range-check correction without methodological impact | Data Programmer; notification to Survey Manager | Smoke test |

A change that is methodologically material but presented as "minor" must always be classified as substantive. When in doubt, escalate.

## Version increment rules

| Increment | Trigger |
|---|---|
| Major (1.0.0 → 2.0.0) | Architectural change, such as splitting a module into two; new module added |
| Minor (1.0.0 → 1.1.0) | Substantive amendment to an existing module |
| Patch (1.0.0 → 1.0.1) | Minor amendment |

Pre-deployment versions use the 0.x.y major and are never used in production data collection.

## Amendment log

Maintained as a single rolling document, with one row per amendment per module.

### Log fields

| Field | Description |
|---|---|
| Amendment identifier | Sequential within the project |
| Date | Date the amendment was authorized |
| Module | The CAPI application affected |
| Version before | Version superseded |
| Version after | New version |
| Category | Substantive or Minor |
| Description | What changed, in plain language |
| Reason | Why the change was needed |
| Authorization basis | Who approved (DOH-PMSMD email date, Survey Manager initials, and so on) |
| Files affected | Which dictionary, logic, or external dictionary files were modified |
| Bench tested | Yes (full, targeted, or smoke) or No |
| Deployed to field | Date of deployment |
| Notification sent | Date Field Supervisors were notified |

## Authorization workflow

**Substantive change.** An issue is identified — by bench testing, field report, methodology team, or DOH-PMSMD. The Data Programmer drafts the change specification with rationale and impact analysis. The Survey Manager and Project Lead review. The Project Lead requests DOH-PMSMD concurrence. On concurrence, the Data Programmer implements, bench-tests, and deploys. The amendment log is updated, and Field Supervisors are notified through the Issue Ticket channel. If the change is methodologically material to the ethics-approved protocol, an SJREB notification is filed.

**Minor change.** An issue is identified. The Data Programmer implements and smoke-tests. The Survey Manager is notified by email. The amendment log is updated, and Field Supervisors are notified through the Issue Ticket channel.

## Field deployment

After authorization and bench testing, the new version is published to the production server. Field Supervisors prompt enumerators to update their applications at the next sync. The previous version remains valid for in-progress cases until they are completed; new cases use the new version. The dashboard tracks the version distribution across active cases; the Data Programmer monitors for any tablet still on an old version after a 48-hour grace window.

## Roll-up at project close

The complete amendment log is included in the final project deliverable to DOH-PMSMD as part of the methodology audit trail. The signed-off version of every CAPI application is archived with the project's source code repository.

---

# Section 2.4 — Refusal and Replacement Logging

## Why this matters

Refusals and replacements influence the final sampling weights. Without structured documentation, the analyst cannot adjust weights correctly, and the survey's representativeness claims become indefensible. Every refusal and every replacement must be auditable from the analytic dataset back to the field decision that produced it.

## Where logging happens

All facility-level and case-level non-response is logged inside CSPro on a structured form, separate from the main case record:

- The **Refusal and Replacement Log** of the Supervisor App, for facility-level coordination, replacement decisions, and contact-attempt tracking.
- The **non-response forms** inside the Facility Head Survey, Patient Listing, Patient Interview, Household Listing, and Household Interview applications, for case-specific reasons such as refused listing, refused interview, or ineligible at point of contact.

The two are joined by case identifier during analysis.

## Reason codes

| Code | Reason | When used |
|---|---|---|
| 01 | Refused listing | Patient or household refused to be listed at the intercept stage |
| 02 | Refused interview | Listed respondent refused at the interview stage |
| 03 | Ineligible at listing | Failed eligibility screening at intercept (residency, age, completed-consultation, and so on) |
| 04 | Ineligible at interview | Eligibility issue surfaced after listing |
| 05 | Unreachable | Three contact attempts exhausted with no response |
| 06 | Infectious or grave case | Patient health status precludes interview; visited last per the Protocol |
| 07 | Cognitive limitation | Respondent cannot understand or respond |
| 08 | Companion unavailable | Required companion for a minor, elderly, or infirm patient was not available |
| 09 | Logistical (security, weather) | Field conditions prevented contact |
| 10 | Other | Free text; flagged for analyst review |
| 99 | Not applicable | Internal use |

## Contact-attempt protocol

Per the Protocol, three contact attempts at three different days and times are required before classifying a household or facility head as non-responsive. The Refusal and Replacement Log captures each attempt:

| Field | Description |
|---|---|
| Date | Date of the attempt |
| Time | Approximate time |
| Method | In-person visit, phone, SMS, or Viber |
| Outcome | Responded, no answer, declined, or scheduled callback |
| Note | Free text |

The form blocks classification of a case as "unreachable" until at least three attempts are recorded with three distinct dates.

## Replacement chain

Every replacement case is linked to the original it replaces, populated automatically when the Field Supervisor draws a replacement.

```
Original case (refused or unreachable) → Replacement 1 → (if also refused) → Replacement 2 → ...
```

The chain is visible in the analytic dataset and is used by the analyst to apply non-response weights.

## Replacement rules

- Replacement comes from the same stratum (UHC Integration Site or non-UHC Integration Site, facility type, geographic area).
- Replacement is randomly selected from the pre-approved reserve list.
- Replacement rates are limited to 5 to 10 percent.
- Sampling weights are adjusted accordingly.

## Replacement-rate exceedance escalation

The Field Supervisor monitors the running replacement rate per facility daily through the Daily Response Monitor.

| Threshold | Action |
|---|---|
| 8% reached | Issue Ticket escalation to Survey Manager and Project Lead |
| 10% cap reached | Issue Ticket escalation to Project Lead; data flagged for downweighting or exclusion (decision made jointly by the Project Lead, Survey Manager, and DOH-PMSMD focal person) |

## Daily replacement report

Generated each morning by the Data Programmer from the project server's Refusal and Replacement Log records. Distribution is to Field Supervisors (their own coverage), the Survey Manager (all), and the Project Lead (all).

| Column | Source |
|---|---|
| Date of report | Run date |
| Facility identifier | Refusal and Replacement Log |
| Facility name | Facility master |
| Original case count | Log |
| Refusals in last 24 hours | Log |
| Replacements drawn in last 24 hours | Log |
| Cumulative replacement count | Running total |
| Cumulative replacement rate (%) | Running, versus target sample |
| Threshold flag | None, 8% warning, or 10% cap exceeded |
| Last action taken | Log or Issue Ticket |

## Analyst handoff

At the close of fieldwork, the analyst receives the full Refusal and Replacement Log, the per-module non-response forms, the replacement chain joined to the analytic dataset, and the signed-off version of each CAPI application. The analyst applies non-response weights using the procedure documented in the project's Sampling Weight SOP.

---

# Section 2.5 — CAPI Application Architecture Reference

## Module map

| Module | Platform | Role | Administered by | Site |
|---|---|---|---|---|
| Supervisor App | CSPro / CSEntry | Facility visit, HCW master list, response monitor, refusal and replacement, issue tickets | Field Supervisor | Facility |
| Facility Head Survey | CSPro / CSEntry | Facility-level questionnaire | Enumerator | Facility |
| Healthcare Worker Survey | Web (browser-based) | HCW self-administered | HCW (or Data Encoder for paper) | Facility or personal device |
| Patient Listing | CSPro / CSEntry | Intercept and list patients at OPD or discharge | Enumerator | Facility |
| Patient Interview | CSPro / CSEntry | Patient questionnaire at the patient's household | Enumerator | Household |
| Household Listing | CSPro / CSEntry | Listing of households within selected barangays | Enumerator | Barangay |
| Household Interview | CSPro / CSEntry | Household-level questionnaire | Enumerator | Household |

## Cross-application data flow

The Supervisor App's Facility Visit Log captures the master Healthcare Worker list, which is read by the Healthcare Worker Survey administration portal as the response-rate denominator. The Facility Visit Log also feeds the facility identifier and Field Supervisor metadata to the enumerator-administered modules.

The Patient Listing application captures eligible patients at the facility and writes them to a listing dictionary. Each listed case is later opened in the Patient Interview application, with the patient's identifier prefilled. The Household Listing and Household Interview applications follow the same pattern at the household level.

## Identifier scheme

All identifiers are managed centrally so that records from any module can be joined for analysis.

| Identifier | Format | Generated by | Used in |
|---|---|---|---|
| Facility identifier | 8-digit numeric, derived from the National Health Facility Registry | Pre-loaded master | All modules referencing a facility |
| Enumerator code | 3-digit numeric | Issued at training | All modules; auto-stamped per case |
| Supervisor code | 3-digit numeric | Issued at training | Supervisor App; cross-stamped on enumerator cases under the supervisor's coverage |
| Listing date | YYYYMMDD | Auto-captured | Patient Listing, Household Listing |
| Patient listing identifier | Sequential within facility | Patient Listing | Patient Listing → Patient Interview |
| Household listing identifier | Sequential within barangay | Household Listing | Household Listing → Household Interview |
| HCW response identifier | Universally unique identifier | Healthcare Worker Survey | Healthcare Worker Survey staging; joined to master via facility identifier and role |
| Replacement-for identifier | Original case identifier | Refusal and Replacement Log | All replacement cases |
| CAPI version | Module name plus semantic version | Build process | Every case |

## Listing-to-interview launch pattern

For Patient and Household modules, the listing application launches the corresponding interview application and prefills identifiers via parameters. The interview application's preprocess step reads the parameters, populates the identifier fields automatically, and protects them against editing.

## Shared value sets

To preserve cross-module joinability, the following value sets are sourced from a single authoritative file and reused across all modules where applicable: Region, Province or Highly Urbanized City, City or Municipality, and Barangay codes from the Philippine Standard Geographic Code (1st quarter 2026 reference); Facility Type and Facility Ownership from the National Health Facility Registry; Integration Status from the DOH Bureau of Local Health Systems Development list; HCW role from the project's canonical list; and the reason codes from Section 2.4.

## Project server deployment structure

Each CAPI application is deployed on the project server as a separate folder containing the parameter file, the data dictionary, and the logic file. A menu application is the launcher visible to enumerators and supervisors after install. Field tablets pull each module via CSEntry's "Add Application from server" flow.

## Healthcare Worker Survey architecture

The Healthcare Worker Survey is delivered as a web application served from a content delivery network. Submissions go through a secure proxy that authenticates each submission with a short-lived token and writes to the staging database. The web application carries its own version stamp on every submission, separate from the CAPI application version stamps.

## Joining the Healthcare Worker Survey with the CAPI modules

At analysis time, the Healthcare Worker Survey responses are joined to the master Healthcare Worker list captured in the Supervisor App's Facility Visit Log via facility identifier and role. The Patient Listing and Patient Interview are joined via the patient listing identifier; the Household Listing and Household Interview are joined via the household listing identifier.

## Source-of-truth rules

- The Facility Head Survey's data dictionary is generated from a Python script that serves as the source of truth. Hand-edits to the data dictionary in the CSPro Designer are not permitted; any change is made by patching the generator script and regenerating.
- The Philippine Standard Geographic Code value sets are self-served from the PSA 1st-quarter 2026 publication; they are not an external dependency on ASPSI.
- The master Healthcare Worker roster captured in the Supervisor App is the canonical denominator for response-rate monitoring. The Healthcare Worker Survey administration portal reads from it.

## Module ownership

All modules are built and maintained by the Data Programmer with two Research Associates assisting in bench testing. The Healthcare Worker Survey has already been verified end-to-end on the project's staging environment.

## At project close

The full source repository, with all module versions and the amendment log, is delivered to DOH-PMSMD per the contract. Successor Data Programmers can rebuild and redeploy the system from the repository alone.
