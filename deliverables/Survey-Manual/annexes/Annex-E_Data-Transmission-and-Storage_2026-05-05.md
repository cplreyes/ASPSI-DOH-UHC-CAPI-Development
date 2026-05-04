# Annex E — Data Transmission and Storage

**Audience:** ASPSI management, DOH-PMSMD technical reviewers, SJREB
**Purpose:** Description of how survey data move from the field tablet to the analytic dataset, how the data are stored and protected, and who has access at each stage.

---

## Architecture overview

```
   Field tablet (CSEntry)                       F2 PWA (HCW devices)
           |                                              |
           | encrypted sync (HTTPS)                       | encrypted submission (HTTPS)
           v                                              v
   ASPSI CSWeb server  <----------- read-only ----  F2 backend
   (private VPS, PH/SG zone)                       (Worker JWT proxy + staging DB)
           |                                              |
           +------------ analytic data warehouse ---------+
                          (joined by FACILITY_ID + LISTING_DATE)
                                       |
                                       v
                           Data Programmer + Analysts
```

## CSWeb server

- **Hosting:** Private virtual private server (VPS) in a Philippine or nearby Southeast Asian zone for low-latency sync from field tablets.
- **Software:** CSPro's CSWeb application running on Apache Tomcat with a MariaDB or MySQL backend, in the standard CSPro deployment configuration.
- **TLS:** All transmissions are encrypted with TLS 1.2 or higher. The server presents a Let's Encrypt certificate on a project subdomain.
- **Authentication:** Each enumerator and Field Supervisor has a unique CSWeb account with a generated password issued at training. Read-only "Supervisor" accounts allow Field Supervisors to view dashboards without altering data.
- **Authorization:** Account roles: Enumerator (write own cases), Supervisor (read all in coverage), Data Programmer (admin), Analyst (read-only export).

## F2 backend

The F2 PWA submits to a separate Worker JWT proxy (Cloudflare Workers) that authenticates submissions via short-lived tokens issued at survey start. The proxy writes to the F2 staging database. The staging DB is read-only to the Data Programmer for daily extraction; HCW responses are joined to the CSWeb dataset by FACILITY_ID and LISTING_DATE during analysis.

## Sync schedule

| Trigger | Frequency | Initiated by |
|---|---|---|
| Per case completion | Whenever a case is marked complete with network available | CSEntry automatically |
| End of field day | Once daily at lodging | Enumerator and Field Supervisor manually |
| On-demand | Any time, for diagnostic or recovery purposes | Field Supervisor |

The Data Programmer monitors the CSWeb dashboard daily for transmission gaps and reconciles missing cases with the field team within 24 hours.

## Backup

| Backup | Frequency | Retention | Storage |
|---|---|---|---|
| CSWeb database snapshot | Daily, automated | 30 days rolling | VPS local + off-site copy |
| Off-site copy | Weekly, automated | 90 days rolling | Encrypted archive in a separate jurisdiction |
| F2 staging DB snapshot | Daily, automated | 30 days rolling | Cloudflare R2 |
| Project archive | At project close | 5 years per ASPSI/DOH retention policy | Encrypted offline media |

## Data privacy

- The deployment complies with the **Data Privacy Act of 2012 (RA 10173)**.
- Personally identifying information (PII) — patient and household contact details collected during listing — is segregated from analytic variables and accessible only to the Data Programmer and field-team supervisors with an operational need.
- The dataset shared with DOH-PMSMD and SJREB for review is a de-identified analytic dataset; no PII is included in any deliverable analytic file.
- The CSWeb server's logs do not record question-level responses; only sync metadata (timestamps, case IDs, version stamps).

## Access controls

- Only the Data Programmer holds VPS administrative access. Credentials are rotated quarterly and at project handoff.
- CSWeb account passwords are user-changeable at first login.
- All write operations to the production data are audit-logged.
- Read-only analytic exports are produced by the Data Programmer and shared with analysts via authenticated download links; raw production access is not granted to analysts.

## Incident response

In the event of a confirmed data exposure or unauthorized access:

1. The Data Programmer notifies the Project Lead and Survey Manager within 1 hour of confirmation.
2. The Project Lead notifies DOH-PMSMD and SJREB within 24 hours per the ICF disclosures.
3. A written incident report is filed within 72 hours (per RA 10173) and the National Privacy Commission is notified if applicable.
4. The CSWeb server is isolated; logs are preserved; affected respondents are notified per the ICF commitment.

## Project close

At the close of the engagement:

1. Final dataset is extracted, de-identified, and delivered to DOH-PMSMD per the contract.
2. The CSWeb server is wiped after the contractual data-retention window.
3. Encrypted archival copies are retained per ASPSI's record-retention policy.
