---
type: deliverable
kind: sop
audience: ASPSI CAPI team · Survey Team Leaders (STLs) · supervising RAs
prepared_by: Carl Patrick L. Reyes
date_drafted: 2026-06-02
status: draft-for-review
related_tasks: [E5-CAPI-003, E5-CAPI-004, E5-CAPI-005, E5-CAPI-006, E5-CAPI-007]
companion_to:
  - security/Data-Privacy-and-Security-Plan.md
  - training/2026-06-02-stl-training-deck.md
  - Survey-Manual/CAPI-PWA-Stakeholder-Section_2026-05-02.md
tags: [field-ops, capi, tablet, mdm, sop, e5]
---

# CAPI Tablet & Device Operations SOP

Operational procedures for the Android CAPI tablets that run **CSEntry** with the F1 / F3 / F4 instruments (FacilityHeadSurvey · PatientSurvey · HouseholdSurvey), syncing to the project **CSWeb server (live on Elestio)**. Covers imaging, per-tablet enrollment, in-field replacement, charging/connectivity, and end-of-engagement decommission.

> **Grounding.** Device-security settings come from the **Data Privacy & Security Plan** §6.4 (device policy), §9.1 (destruction), §11 (lost/stolen). Field-replacement + sync verification mirror the **STL Training Deck**. Pre-configuration model + roles mirror the **Survey Manual stakeholder section** §2.1, §8.
>
> **⟨CONFIRM⟩ markers** are choices ASPSI must lock before fieldwork (MDM product, fleet count, charging kit). Everything else is specified.

---

## 0. Scope, roles & inventory

| Role | Device responsibility |
|---|---|
| **ASPSI CAPI team** | Image, enroll, and provision every tablet; hold the device register; remote-wipe / revoke sync on loss; decommission at close |
| **Survey Team Leader (STL)** | Sign for the cluster's tablets; daily end-of-day review + sync verification; execute field replacement from cluster spares; report loss immediately |
| **Survey Enumerator (SE)** | One assigned tablet, signed for; keep charged + locked; never share, never delete apps/cases |
| **Supervising RA** | Cluster-level device reconciliation against the CSWeb dashboard |

- **Fleet size:** ⟨CONFIRM⟩ ~126 active units + **10–15% spares** per the procurement request (see #179 spec / #180 procurement). Spares are fully imaged and held at cluster level.
- **Device register** (master spreadsheet, ASPSI-held): one row per tablet — `device_id`, serial/IMEI, MDM-enrolled (Y/N), assigned SE, cluster, issue date, return date, wipe-certified date. This register is the spine of every procedure below.

---

## 1. Imaging SOP  ·  *(E5-CAPI-003 / #181)*

Every tablet is imaged to an identical, hardened baseline **before it leaves Los Baños**. SEs never image or update devices themselves.

### 1.1 Base configuration
1. Factory reset → set device language + **timezone Asia/Manila**.
2. Sign in to the **project-managed Google/Android Enterprise account** ⟨CONFIRM account⟩ — **no personal accounts** on survey devices.
3. Set date/time to **automatic (network)** so case timestamps are trustworthy.
4. Disable: auto-update over mobile data (Wi-Fi only), Bluetooth file transfer, nearby-share, and any pre-installed bloat not needed for fieldwork.

### 1.2 MDM enrollment (security baseline)
Enroll each device in the project **MDM** ⟨CONFIRM product — e.g. Android Enterprise / a zero-touch MDM⟩ and push this baseline (mirrors Privacy Plan §6.4):

- [ ] **Screen lock** PIN/biometric required; **auto-lock ≤ 2 minutes**.
- [ ] **Max failed unlock attempts → device wipe.**
- [ ] **Device encryption ON** — *verified at imaging and recorded in the register.*
- [ ] **Remote-wipe + remote-lock** capability confirmed working (test once per batch).
- [ ] **App allowlist** — only CSEntry + system essentials; block app installs by the SE.
- [ ] **USB debugging / developer options OFF**; block sideloading post-imaging.
- [ ] **No removable-storage** writes of respondent data (block SD/USB export).
- [ ] **Location services ON** (required for GPS capture) and locked on.

### 1.3 CSEntry install
1. Install **CSEntry** (version must match the CSPro Designer version used to build F1/F3/F4 — see CSWeb deploy guide prerequisite 0.2). ⟨CONFIRM CSEntry version⟩.
2. Confirm the install opens and reaches its main menu.
3. The three instruments + sync endpoint are loaded in **§2 (enrollment)** — imaging leaves a clean, CSEntry-ready device.

### 1.4 Imaging sign-off
A device is "imaged" only when the §1.2 checklist is fully ticked **and** encryption is verified. Record imaged-date + the imager's name in the register. Spares are imaged identically.

---

## 2. Per-tablet enrollment SOP  ·  *(E5-CAPI-004 / #182)*

Binds a specific tablet to a specific enumerator and loads the live survey apps.

1. **Bind device ↔ SE.** In the device register, set `assigned_se` for the `device_id`; the SE signs the device-issue line (custody handover).
2. **Push the CSPro applications** — the three CSEntry apps (FacilityHeadSurvey, PatientSurvey, HouseholdSurvey) with their **data dictionaries** and the **PSGC lookup dictionaries** (region/province/city/barangay).
3. **Point the sync endpoint** at the project CSWeb server URL ⟨CONFIRM CSWeb URL — `csweb.asiansocial.org` once DNS repoints, else the elestio.app URL⟩.
4. **Create the CSWeb sync credential** for that SE (named account, least-privilege "enumerator" role — see CSWeb user-management #236) and enter it on-device, **or** confirm the SE will authenticate at first sync.
5. **First-sync smoke test:** start a throwaway case, accept it, run a sync, confirm **"Sync successful"** and that the case appears on the CSWeb dashboard tagged with this device + SE. **Delete the throwaway case server-side** before fieldwork.
6. Record enrolled-date in the register.

> **Spares** are imaged (§1) but enrollment (§2 steps 1, 3–6) happens at the moment of a field swap (§3) so the spare binds to the right SE and Q-number range.

---

## 3. Field replacement protocol  ·  *(E5-CAPI-005 / #183)*

> **The core principle (teach this to every STL):** a **synced** case is safe on the server regardless of the tablet's fate; an **un-synced** case dies with an unrecoverable device. This is *why* the daily-sync-before-10 PM rule exists. Replacement protects accounted data and re-establishes capture fast.

When a tablet is **broken, unresponsive, lost, or stolen:**

1. **Report immediately** → STL → ASPSI CAPI team. (Lost/stolen also triggers the **privacy-incident path** — §5 + Privacy Plan §10/§11.)
2. **Revoke the old device's sync access** (ASPSI CAPI team, via CSWeb user management / token) so a lost device cannot sync or be used — this does **not** affect already-uploaded data.
3. **Recover in-flight data if possible.** If the old device still powers on, **attempt one sync first** to flush un-synced cases. If it cannot power on, **log the exact case IDs known to be un-synced** so the data manager knows what to expect or re-collect.
4. **Issue a pre-imaged spare** from the cluster kit; **enroll it** (§2) to the same SE and **re-assign the SE's remaining questionnaire-number range** to the new device.
5. **Update the device register:** old device → `status=replaced/lost`, new `device_id` ↔ SE, note the date and the at-risk case IDs.
6. SE resumes capture on the spare; STL confirms the next sync lands on the dashboard.

---

## 4. Charging & connectivity logistics  ·  *(E5-CAPI-006 / #184)*

- **Charging:** each SE carries the tablet charger; ⟨CONFIRM kit⟩ each cluster carries **power banks + a multi-port charger/strip** for areas with limited mains. Rule of thumb: start each field day **≥ 50%** (per the enumerator QRC).
- **Connectivity:** capture is **offline-first** — no connectivity is needed *during* an interview; sync is the only step that needs a network. Each cluster has a **daily-sync plan**: identify the reliable Wi-Fi / mobile-data point and time window so every device syncs **before 10 PM**.
- **GIDA / low-signal areas:** stage a sync at the nearest reliable signal on the way out; un-synced cases persist safely on the device until then (§3 principle).
- ⟨CONFIRM⟩ SIM/data-plan provisioning per tablet vs per cluster.

---

## 5. Retrieval & decommission SOP  ·  *(E5-CAPI-007 / #185 — feeds Epic 12 handover)*

At engagement close, after **all cases are synced and server-verified:**

1. **Retrieve** every tablet against the device register; reconcile issued vs returned. Chase any outstanding device through the STL.
2. **Confirm zero un-synced cases** remain on each device (final sync + dashboard reconciliation) **before** wiping — a wipe destroys anything not yet on the server.
3. **Decommission each device** (Privacy Plan §9.1): **factory reset + verified wipe + re-encryption** so prior respondent data is unrecoverable. Remove the project Google/MDM account and un-enroll from MDM.
4. **Record per device** in the register: wipe date, method, and who performed it → this is the **certificate-of-destruction** evidence for the NDU turn-over (Privacy Plan §9.2).
5. Tablets that are returned/leased/repurposed are wiped **before** hand-over; owned units are stored wiped.

> **Lost/stolen device (cross-cuts §1.2, §3, §5):** treat as a **data + privacy incident**, not just hardware loss — report up the incident chain, remote-wipe, assess un-synced cases at risk, and trigger the breach process if SPI is exposed (Privacy Plan §10.1 / §11).

---

## Issue coverage map
| Section | Field-ops issue |
|---|---|
| 1 Imaging | #181 (E5-CAPI-003) |
| 2 Enrollment | #182 (E5-CAPI-004) |
| 3 Field replacement | #183 (E5-CAPI-005) |
| 4 Charging & connectivity | #184 (E5-CAPI-006) |
| 5 Retrieval & decommission | #185 (E5-CAPI-007) |

**Pending ⟨CONFIRM⟩ before fieldwork:** MDM product + project Google/Android-Enterprise account; final fleet count + spares (#179/#180); CSEntry + CSWeb-Designer version pin; CSWeb sync URL (DNS repoint); charging/SIM kit per cluster. Procurement (#180) and the live pretest are separate execution tasks.
