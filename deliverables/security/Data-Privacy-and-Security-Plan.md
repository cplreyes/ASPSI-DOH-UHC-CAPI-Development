# Data Privacy & Security Plan — ASPSI-DOH UHC Survey (Year 2)

**Instruments:** F1 Facility Head · F2 Healthcare Worker (PWA) · F3 Patient · F4 Household
**Governing law:** RA 10173 (Data Privacy Act of 2012) + IRR; NPC circulars; DOH data-governance issuances; the engagement Non-Disclosure Undertaking (NDU).
**Owner:** Carl (Data Programmer / system) · ASPSI (Personal Information Controller interface) · DOH (Personal Information Controller).
**Status:** v0.1 draft — 2026-06-02. Sections flagged **⟨DECISION⟩** need ASPSI/DOH sign-off (values recommended, not assumed).

> **Roles under RA 10173.** DOH is the **Personal Information Controller (PIC)** — it determines the purpose of processing. ASPSI is a **Personal Information Processor (PIP)** acting on DOH's instructions; Carl/the system is a sub-processor. A written outsourcing/processing agreement between DOH and ASPSI (NPC-compliant, with the §IRR Rule IV data-sharing/outsourcing clauses) is a prerequisite — **⟨DECISION⟩ confirm this agreement exists and name the DOH Data Protection Officer.**

This document is the single source of truth for the E9 security epic. Each section maps to its issue(s).

---

## 1. PII inventory per instrument  ·  *(closes #210)*

Extracted directly from the instrument dictionaries (`.dcf`) + the F2 survey schema — not a generic list. Classification per RA 10173 §3(g) *personal information* (PI) and §3(l) *sensitive personal information* (SPI).

### 1.1 Collected by every instrument (operational / provenance)
| Field(s) | Type | Class |
|---|---|---|
| `INTERVIEWER_ID`, `ENUMERATOR_S_NAME`, `SURVEY_TEAM_LEADER_S_NAME` | identity of field staff | **PI** (staff) |
| `REGION` / `PROVINCE_HUC` / `CITY_MUNICIPALITY` / `BARANGAY` | geographic | PI in combination |
| `FACILITY_NAME`, `FACILITY_ADDRESS` | facility identity | PI (org) |
| Facility GPS (`*_GPS_LATITUDE/LONGITUDE/...`) + capture trigger | precise geolocation | **PI** |
| `VERIFICATION_PHOTO_FILENAME` + the photo object | image | **PI / potentially SPI** (may show faces/premises) |
| Timestamps (start/end/duration), device fingerprint | provenance | PI in combination |

### 1.2 F1 — Facility Head (respondent = the facility head/HCW)
- **Direct identifiers:** `Q1_NAME` (full name), `RESP_NAME` (**name + signature**), `RESP_POSITION`, `RESP_EMAIL`, `RESP_MOBILE`.
- **Demographics:** `Q3_AGE`, `Q4_SEX`.
- The remainder is institutional/operational opinion data about the facility (not respondent SPI), but is attributable to a named, contactable individual → treat the record as identifiable PI.

### 1.3 F2 — Healthcare Worker (PWA, self-administered)
- Enrollment binds an `hcw_id` to a `facility_id` (PI in combination). Survey content is HCW profile + opinion. **⟨DECISION⟩ confirm whether F2 collects HCW name/contact** — if responses are pseudonymous (hcw_id only), document that explicitly as a minimization control (see §2). Backend stores responses in Google Sheets + a device fingerprint; admin audit log records actor + IP **hash**.

### 1.4 F3 — Patient (respondent = patient or proxy)
- **Direct identifiers:** `Q4_NAME` (patient full name), `Q2_RELATIONSHIP` (if proxy).
- **Demographics/SPI:** `Q5_BIRTH_MONTH`+`Q5_BIRTH_YEAR` (**date of birth**), `Q6_AGE`, `Q7_SEX`, `Q9_GROUP` (**ethnic/IP identity → SPI**), `Q10_CIVIL_STATUS`, `Q11_PWD`/`Q13_PWD_CARD` (**disability → SPI; PWD card = government ID**).
- **Precise location of a private individual:** patient home region/province/city/barangay (`P_*`) **+ patient-home GPS** (`P_HOME_GPS_*`). This is high-sensitivity — home coordinates of an identified patient.
- **Health data (SPI):** the entire instrument concerns the patient's health-seeking, conditions, and PhilHealth use → **SPI under §3(l)(1)**.

### 1.5 F4 — Household (respondent + full member roster)
- **Direct identifiers:** `RESPONDENT_NAME`; per roster member `Q30_NAME`.
- **Demographics/SPI per member:** birth month/year + age, sex, `Q34_RELATIONSHIP`, `Q35_HAS_DISABILITY` (**SPI**), `Q5_GROUP`/`Q14_IP_MEMBER` (**ethnic/IP → SPI**), `Q6_CIVIL_STATUS`, `Q11_EDUCATION`.
- **Financial:** `Q13_INCOME_SOURCE`, `Q18_INCOME_AMOUNT`/`Q18_INCOME_BRACKET` (sensitive financial PI).
- **Precise location:** `HH_ADDRESS` + household GPS (`LATITUDE`/`LONGITUDE`/`HH_GPS_*`).
- **Health/welfare (SPI):** disability, healthcare utilization, PhilHealth membership across all members.

> **Bottom line:** All four instruments collect **identifiable + sensitive personal information** (names + precise home/facility geolocation + health/disability/ethnicity + financial). The strictest RA 10173 SPI safeguards apply (§13 — SPI processing requires consent and heightened security). F3 and F4 are the highest-risk (patient/household home coordinates tied to named individuals + health status).

---

## 2. Data minimization review  ·  *(closes #211)*

Principle (§11(c)): collect only what is adequate, relevant, and not excessive for the declared purpose (UHC implementation evaluation).

| Field | Necessity | Recommendation |
|---|---|---|
| Respondent **name** (Q1/Q4/Q30/RESP_NAME) | Needed for callback/verification/de-dup during fieldwork; **not** needed for analysis | **⟨DECISION⟩** Drop name from the analysis dataset; keep only in the field-ops linkage table, destroyed at project close (§9). |
| **Home GPS** (F3 `P_HOME_GPS_*`, F4 GPS) | Justify against purpose — is patient/household *home* coordinate analytically required, or is barangay sufficient? | **⟨DECISION⟩** If only catchment analysis is needed, **collect barangay only** and drop home GPS, or truncate coordinates. High-sensitivity; strong minimization candidate. |
| `RESP_EMAIL` / `RESP_MOBILE` (F1) | Field callback only | Keep in field-ops table only; exclude from analysis export. |
| Verification **photo** | Fieldwork QA (proof of visit) | Retain only through QA sign-off; destroy at project close. Confirm it does not capture respondent faces unnecessarily. |
| PWD card **view** (F3 Q13 / F4 Q9) | Eligibility confirmation | Confirm the card is *viewed to verify*, **not imaged/stored**. Store only the boolean "verified", never the card number/image. |
| Full birth date (month+year) | Age is the analytic variable | Consider storing **age only** post-collection; birth month/year enables re-identification. **⟨DECISION⟩** |

The analysis dataset must be a **de-identified extract** (no name, no contact, no precise GPS, no photo); identifiers live only in the operational linkage table with a separate, shorter lifecycle.

---

## 3. PII handling protocol — in transit, at rest, in analysis  ·  *(closes #212)*

### 3.1 In transit
- **F1/F3/F4 (CSPro/CSEntry → CSWeb):** sync over **HTTPS/TLS 1.2+ only**; CSWeb server presents a valid certificate; reject plaintext HTTP. See §6.2.
- **F2 (PWA → Cloudflare Worker → Apps Script → Sheets/R2):** browser→Worker over TLS (Cloudflare-managed); Worker→Apps Script authenticated by **HMAC-SHA256** envelope; admin session via short-lived **JWT** (Bearer, in-memory only). No PII in URLs/query strings or logs.

### 3.2 At rest
- **Tablet:** CSEntry `.csdb` on device-encrypted storage (§6.4); no PII on removable media; auto-lock (§6.4).
- **CSWeb server:** see §6.1 (at-rest encryption) + §6.3 (access control). DB + file store on encrypted volume.
- **F2 backend:** responses in Google Sheets, files in Cloudflare R2 (provider-side encryption at rest). Admin passwords are **PBKDF2-SHA256, 100k iters, per-user salt** — never plaintext. Audit log stores a **hash** of client IP, not the raw IP.

### 3.3 In analysis
- Work only from the **de-identified extract** (§2). Identifiers never enter analysis notebooks/dashboards.
- Access on a need-to-know basis (§6.3); analysts under the NDU (§12).
- No copying of identifiable data to personal machines, email, or unmanaged cloud. Any export logged (§5).

---

## 4. Consent & data-subject rights

### 4.1 Consent-form wording review  ·  *(closes #214)*
The informed-consent screen (F1 `CONSENT_GIVEN`, and the equivalents in F3/F4/F2) must, to satisfy §3(b) *consent* + §16 *transparency*, clearly state in language the respondent understands:
1. **Who** is collecting (DOH as PIC; ASPSI as processor) and DOH's DPO contact.
2. **What** is collected — explicitly name the sensitive categories (health, disability, ethnicity, location, financial) and that a **photo + GPS** are taken.
3. **Why** (UHC implementation evaluation) and the legal basis (consent for SPI per §13(a)).
4. **Who it's shared with** and that it crosses into a unified analysis store (data-sharing per IRR Rule IV).
5. **How long** it's kept (§8) and that it will be de-identified/destroyed thereafter.
6. **Their rights** (§4.2) and how to exercise them.
7. That consent is **voluntary**, can be **refused or withdrawn** without consequence to their care, and that refusal ends the interview (F1 already codes refusal → disposition + `endlevel`).
8. For **proxies/minors/roster members:** authority of the respondent to consent on others' behalf; special handling for minors' data.

**⟨DECISION⟩** Have ASPSI's/DOH's DPO review the final wording; the current CAPI consent text should be checked line-by-line against this list and the PSA/DOH-approved questionnaire consent block.

### 4.2 Data-subject rights procedure (RA 10173 §16–18)  ·  *(closes #213)*
Respondents may exercise: **right to be informed, to object, to access, to rectification, to erasure/blocking, to damages, and to data portability.** Procedure:
- **During fieldwork:** the enumerator can stop/withdraw on request; the partial record is marked refused/withdrawn and not used.
- **After fieldwork:** a respondent contacts the **named DPO** (on the consent leaflet) with a verifiable request. Because records are name-linked via the operational linkage table, a request can be located by name + facility/area + date.
- **SLA:** acknowledge within **⟨DECISION⟩ (recommend 5 working days)**, resolve within the NPC-expected window. Log every request + action in the rights-request register.
- **Erasure caveat:** balance against the research/archival purpose and any DOH statutory retention; document the basis if a request is declined.
- **⟨DECISION⟩** Name the contact point (DOH DPO vs ASPSI DPO) and publish it on the consent material.

---

## 5. Audit trail design  ·  *(closes #219)*
**What is logged (data-access + mutation events), and where:**
- **F2 backend (built):** `F2_Audit` records `event_type`, actor username, actor JWT `jti`, actor role, target resource, **hashed** client IP, request_id, timestamps. Auth events (login/logout/password-change/session-revoke), and every admin mutation (user/role/file/settings/DLQ/encode/**kill-switch**) emit an audit row, success-gated. Reads of bulk response data are **⟨DECISION⟩** — decide whether dashboard reads of identifiable data should also be audited (recommend: yes for any identifiable export).
- **CSWeb (to configure):** enable CSWeb's operator/audit logging — who synced, who exported, who logged in, from where. See §6.3.
- **Tablet:** CSEntry paradata (operator, timestamps) retained for QA.

**Minimum event set to capture for identifiable data:** login/logout, failed-login, role/permission change, password change, **data export/download**, record edit/delete, kill-switch toggle, backup/restore actions.

---

## 6. Security controls

### 6.1 Encryption at rest  ·  *(closes #215)*
- **Tablet:** full-disk/file-based encryption enforced via MDM (§6.4); CSEntry data partition encrypted.
- **CSWeb server:** host volume encryption (LUKS/BitLocker per OS) **⟨DECISION⟩ (host OS TBD with #233)**; the CSWeb application DB and uploaded files on the encrypted volume; DB credentials in a secrets store, not in source.
- **F2 backend:** Google (Sheets) + Cloudflare (R2) provide AES-256 at rest by default; admin secrets (JWT signing key, HMAC secret) held as Cloudflare Worker **secrets**, never in `wrangler.toml`/source; passwords PBKDF2-hashed.

### 6.2 Encryption in transit  ·  *(closes #216)*
- TLS 1.2+ everywhere; HSTS on web surfaces; no mixed content. CSWeb sync endpoint **HTTPS only** with a CA-valid cert (not self-signed in production). F2 Worker↔Apps Script additionally HMAC-signed. Certificate renewal owner + expiry monitoring **⟨DECISION⟩**.

### 6.3 Server access control + authentication model  ·  *(closes #217, #218)*
**Roles (least privilege):**
| Role | F1/F3/F4 (CSWeb) | F2 (Admin Portal) |
|---|---|---|
| **Enumerator** | sync own cases only; no export | n/a |
| **Supervisor / STL** | review team's cases; no bulk PII export | n/a |
| **Data Manager / Admin** | full data + export (audited) | `dash_data`, `dash_report`, `dash_apps` per RBAC |
| **User/Role Admin** | manage accounts | `dash_users`, `dash_roles` |

- **F2 (built):** per-user PBKDF2 auth; JWT with `role_version` invalidation + per-user session revocation on password change (a `revoked_user` timestamp in KV rejects all pre-change tokens); 4h TTL; two-axis login throttle; RBAC `requirePerm` server-enforced; forced password rotation; kill-switch. Role-aware nav gating (FX-002) shipped.
- **CSWeb (to configure, #236):** create individual named accounts (no shared logins), assign the least-privilege role above, enforce strong passwords + lockout, restrict export to Data Manager/Admin, restrict admin console to known IPs/VPN where feasible. Quarterly access review. → **Provisioning pack** (CSWeb-accurate 2-axis role design + bulk-import CSV): `CSWeb/CSWeb-User-Management-and-RBAC-Provisioning-Pack.md`. *(Reconciles the row-level aspiration above with CSWeb's real capability: field roles get no `data` dashboard; supervisors get `report`-only.)*
- **⟨DECISION⟩** confirm who holds Admin on CSWeb and the export-approval workflow.

### 6.4 Device (tablet) policy  ·  *(closes #220)*
- Screen lock with PIN/biometric, **auto-lock ≤ 2 min**, max failed attempts → wipe.
- Device encryption **on** (verified at imaging, #181).
- MDM-enrolled; remote-wipe capability for lost/stolen (§11); app allowlist; no personal accounts; USB debugging off.
- No respondent data on removable storage; sync-then-retain policy per §8.

---

## 7. Backup & recovery

### 7.1 Server-side backup  ·  *(closes #221)*
- Automated **daily** backup of the CSWeb DB + uploaded files to a separate encrypted volume; **⟨DECISION⟩** frequency (recommend daily incremental + weekly full) and location (§7.4).
- Backups **encrypted** with a key held separately from the server.

### 7.2 Tablet-side / mid-interview backup  ·  *(closes #222)*
- CSEntry **partial save** / auto-save on (so a crash mid-interview doesn't lose the case); confirm interval.
- Daily end-of-day **sync** to CSWeb is the primary backup of field data; STL verifies sync completion (end-of-day review). Un-synced tablets are a data-loss + data-at-rest risk → §6.4.

### 7.3 Recovery test protocol  ·  *(closes #223)*
- Before fieldwork and at least once mid-engagement: **restore the latest backup to a clean staging server and verify** record counts + integrity + that the app loads. Document each drill (date, who, result). A backup that has never been test-restored does not count as a backup.

### 7.4 Off-site backup decision  ·  *(closes #224)*
- **⟨DECISION⟩** Recommend an **encrypted off-site/cloud copy** (geo-separate) in addition to local, since a single-site backup is lost with the site. If off-site is cloud, the provider must be covered by an NPC-compliant processing agreement and store within an acceptable jurisdiction. If DOH policy forbids off-site, document the accepted single-site risk + mitigation.

---

## 8. Retention  ·  *(closes #225, #226)*

### 8.1 Data retention policy (#225)
RA 10173 §11(e): retain only as long as necessary for the declared purpose, then dispose securely.
- **Identifiable field data (names, contact, GPS, photo):** retain only through data collection + QA/verification + analysis sign-off, then **de-identify or destroy** the identifiers (§9). Recommend identifiers destroyed at **project close / final report acceptance**.
- **De-identified analysis dataset:** retained per the DOH research protocol / archival requirement.
- **⟨DECISION⟩ — authoritative period must come from DOH/the research protocol/NPC.** Whose policy governs is an open question in the issue itself; resolve with DOH's DPO. Do not assume the RA 10173 generic "as necessary" without a concrete number agreed in writing.

### 8.2 Audit-log retention (#226)
- Retain audit logs long enough to investigate incidents and demonstrate compliance — **recommend ≥ 1 year** (or per DOH policy), separate from and outliving the operational data they describe. F2's KV-based revocation entries self-expire by design; the `F2_Audit` sheet is durable. **⟨DECISION⟩** confirm the number with DOH/NPC expectations.

---

## 9. Secure destruction & turn-over  ·  *(closes #227, #228, #209)*

### 9.1 Tablet destruction post-fieldwork (#228)
- After all cases are synced **and** sync is verified server-side: **factory reset + verified wipe** of each tablet (and re-encryption so prior data is unrecoverable). Log per device (ID, date, who, method). If tablets are returned/repurposed, wipe before hand-over (§ ties to #185 decommission SOP).

### 9.2 NDU-compliant file turn-over / destruction at project close (#227)
- At engagement close, per the **Non-Disclosure Undertaking**: turn over the agreed deliverable dataset to DOH/ASPSI in the agreed format, then **securely destroy** all working copies of identifiable data held by the processor (Carl/system) — local files, backups, cloud objects, R2, Sheets exports — with a signed **certificate of destruction**.
- **⟨DECISION⟩** ASPSI/DOH to confirm: what is turned over (identifiable vs de-identified), to whom, and the destruction sign-off authority.

### 9.3 NDU compliance throughout (#209)
- All personnel (enumerators, STLs, analysts, Carl) sign the NDU before touching data; no disclosure of project data, respondent identities, or findings outside the authorized channel; this plan + the NDU are part of onboarding. Breach of NDU → §10 incident process.

---

## 10. Breach & incident response  ·  *(closes #229, #230)*

### 10.1 Data-breach response protocol (#229)
On suspected breach (lost/stolen tablet, server compromise, accidental disclosure, F2 credential compromise):
1. **Contain** — isolate the asset; for F2, **toggle the kill-switch** + **revoke sessions** (bump `role_version` / write the per-user `revoked_user` entry) and rotate the JWT signing + HMAC secrets; for a tablet, remote-wipe; for CSWeb, disable affected accounts.
2. **Assess** — what data, how many subjects, sensitivity (SPI? names + home GPS = high), likelihood of real risk to subjects.
3. **Notify** — NPC + affected data subjects **within 72 hours** of knowledge of a breach meeting the §IRR Rule IX threshold (SPI or info that may enable identity fraud / real harm). DOH's DPO leads NPC notification; ASPSI supports.
4. **Remediate + document** — root cause, fix, lessons; record in the breach register.

### 10.2 Incident escalation chain (#230)
**Enumerator/STL → ASPSI field lead → ASPSI DPO/Carl → DOH DPO → NPC** (and affected subjects). Define for each tier: contact, max time-to-escalate, and decision authority. **⟨DECISION⟩** populate names/contacts + the NPC-notification decision owner (DOH DPO). Tabletop-test the chain once before fieldwork.

---

## 11. Lost/stolen device (cross-cuts #220/#228/#229)
Immediate: report up the §10.2 chain → MDM **remote-wipe** → assess un-synced cases (data loss + breach) → if SPI at risk, trigger §10.1 notification → replace per the field-replacement SOP (#183).

---

## 12. Personnel, training & the NDU
- Everyone with data access signs the **NDU** (§9.3) and completes a short data-privacy briefing (this plan's respondent-facing duties + device rules + incident reporting).
- Access is provisioned least-privilege (§6.3) and **de-provisioned at role end**.

---

## Issue coverage map
| Section | E9 issues closed/addressed |
|---|---|
| 1 PII inventory | #210 |
| 2 Minimization | #211 |
| 3 Handling protocol | #212 |
| 4.1 Consent | #214 |
| 4.2 Subject rights | #213 |
| 5 Audit trail | #219 |
| 6.1 / 6.2 Encryption | #215, #216 |
| 6.3 Access + auth | #217, #218 |
| 6.4 Device policy | #220 |
| 7 Backup/recovery | #221, #222, #223, #224 |
| 8 Retention | #225, #226 |
| 9 Destruction/turn-over/NDU | #227, #228, #209 |
| 10 Breach + escalation | #229, #230 |

**Open ⟨DECISION⟩ items requiring ASPSI/DOH/NPC sign-off** (cannot be assumed): processing agreement + named DPO; retention period (#225) & audit-log period (#226); minimization calls on name/home-GPS/birthdate/photo (#211); off-site backup (#224); consent-wording legal review (#214); escalation-chain names + NPC-notification owner (#230); turn-over scope + destruction authority (#227). These are flagged inline; everything else is specified.
