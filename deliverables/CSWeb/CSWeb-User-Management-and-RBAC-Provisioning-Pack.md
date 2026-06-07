---
type: deliverable
kind: provisioning-pack
audience: Carl (CSWeb Administrator) · ASPSI Data Manager
prepared_by: Carl Patrick L. Reyes
date: 2026-06-04
related_task: E4-CSWeb-004 (#236)
builds_on: [security/Data-Privacy-and-Security-Plan.md (§6.3), wiki/concepts/CSWeb.md]
server: csweb.asiansocial.org (CSWeb 8.0.1, LIVE)
tags: [csweb, user-management, rbac, roles, provisioning, e4]
---

# CSWeb User Management & RBAC Provisioning Pack (#236)

Turnkey design + steps to provision named accounts and role-based access on the live CSWeb box, sized to the UHC Year 2 field structure. The **account creation is your admin action** on `csweb.asiansocial.org` (live production) — this pack makes it copy-paste, and the companion `csweb-users-import-template.csv` is the bulk-import file to fill with the confirmed roster.

---

## 1. CSWeb's real permission model (verified — design to *this*, not to an ideal)

CSWeb has **exactly two permission axes**, nothing richer (per `wiki/concepts/CSWeb.md` §Permission Model — verified):

| Axis | Granularity | Grants |
|---|---|---|
| **Dashboard permissions** | 5 binary checkboxes: `data` · `report` · `apps` · `users` · `roles` | Login to the CSWeb web UI + access to that dashboard |
| **Dictionary permissions** | one binary **up/down sync** per dictionary | Whether CSEntry/Batch/Data Manager can sync that dictionary for this user |

**Hard limits — these shaped the design below:**
- **No row-level filtering.** A user with the `data` dashboard sees **all** rows in every dictionary they can access — there is no "own cases", "my cluster", or "my region" predicate.
- **No upload-only vs download-only at the role level.** The dictionary permission is a single sync grant; *direction* is set by the app's `syncdata()` logic, not by RBAC.
- **No time-window / limited-dataset permission.**
- **Built-in roles ship as exactly two:** `Administrator` (all 5 dashboards + all dictionary sync) and `Standard User` (no dashboard / cannot log into web UI, but can sync dictionaries via CSEntry + deploy apps).

> **Reconciliation with Privacy Plan §6.3.** §6.3 sketched "Enumerator: sync own cases only" and "STL: review team's cases" — neither is enforceable in CSWeb (no row-level filter). This pack achieves the *intent* differently: enumerators get **no dashboard at all** (they never see the web UI — they only sync from CSEntry), so "no bulk PII export" is enforced by withholding the `data` dashboard, not by row scoping. Supervisors get **`report` only** (aggregate coverage, no full-PII rows). True per-team/per-region scoping would require splitting into per-region dictionaries or doing it downstream in the BI layer — **not** worth it here.

---

## 2. Role design — five custom roles (least privilege)

Create these under the **Roles dashboard**. (Built-in role names can't be edited, so use custom roles for everything except the one server Administrator.)

| Project role | CSWeb role to create | Dashboards | Dictionary sync (F1/F3/F4) | Logs into web UI? | Rationale |
|---|---|---|---|---|---|
| **Enumerator (SE)** | `field-sync` | *(none)* | ✅ sync | **No** — CSEntry only | Uploads own tablet's cases; no web UI = no bulk-PII exposure |
| **Field/Cluster Supervisor (FS, RA)** | `supervisor-monitor` | `report` | ✅ sync | Yes | Coverage monitoring (Sync/Map reports — counts + geo, not full-PII rows); no `data` download |
| **Data Manager** | `data-manager` | `data` · `report` · `apps` | ✅ sync | Yes | Full review/export (audited) + app deploy. The export-approval point (§6.3 ⟨DECISION⟩) |
| **Account Admin** | `account-admin` | `users` · `roles` | *(none)* | Yes | Provisions accounts; no data access (separation of duty from Data Manager) |
| **Server Administrator** | built-in **`Administrator`** | all 5 | all | Yes | **Exactly one named holder** — break-glass; not a daily-use account |

Notes:
- `field-sync` inherently also allows **app-deploy** (CSWeb bundles deploy with non-dashboard sync — there's no separate toggle). Minor over-grant; acceptable since enumerators won't deploy and have no dashboard.
- Keep the built-in **`Administrator`** to a single named person (you, or Myra) used only for break-glass + role/dictionary setup — daily account work goes through `account-admin`, daily data work through `data-manager`.

---

## 3. Account roster — username convention + headcount

- **No shared logins** — one named account per person (Privacy Plan §6.3).
- **Username = the field ID** captured in the instruments (`INTERVIEWER_ID` / supervisor ID), so CSWeb identity ↔ case provenance line up for audit. Convention:
  - Enumerators: `se-001` … `se-NNN`
  - Field Supervisors: `fs-01` … `fs-NN`  · Cluster RAs: `ra-01` … `ra-NN`
  - Office: `dm-<surname>` (Data Manager), `adm-<surname>` (Account Admin), `root-<surname>` (Server Admin)
- **Headcount to provision** (per the Survey Manual — *confirm with ASPSI, see §6*): **6 cluster RAs + 20 field supervisors + 100 enumerators** + Data Manager (+ assistants) + 1 Account Admin + 1 Server Admin ≈ **130 accounts**.

| Role count | CSWeb role | n |
|---|---|---|
| Enumerators | `field-sync` | ~100 |
| Field supervisors | `supervisor-monitor` | ~20 |
| Cluster RAs | `supervisor-monitor` | ~6 |
| Data Manager (+ assistants) | `data-manager` | 1–3 |
| Account Admin | `account-admin` | 1 |
| Server Administrator | `Administrator` | 1 |

---

## 4. Provisioning steps (on `csweb.asiansocial.org`)

1. **Log in** as the built-in `admin` (the `<csweb-admin-password>` from the setup runbook).
2. **Roles dashboard → create the 5 custom roles** in §2 (tick the dashboard boxes + the F1/F3/F4 dictionary sync per the table). *(Dictionaries must exist first — that's #235; create roles after the per-survey upload, or create roles now with dictionary boxes added once #235 lands.)*
3. **Users dashboard → bulk import** `csweb-users-import-template.csv` (filled with the confirmed roster). CSV format CSWeb expects: `username, first name, last name, user role, password, email, phone` — tick the **header-row** checkbox on import. (First/last name must be **letters only**; password **≥ 8 chars**.)
4. **Passwords:** generate a unique strong password per user (12+ chars), store in the password manager, distribute over a secure channel (not email-in-clear). CSWeb has no native forced-rotation — set a **rotation cadence** (e.g., at pretest start + mid-fieldwork) as a procedure.
5. **Lock down the console:** restrict the CSWeb admin URL to known IPs/VPN where the host allows; confirm HTTPS-only (the live box has a valid LE cert).
6. **Quarterly access review:** de-provision role-enders; reconcile the account list against the active field roster.

---

## 5. Closure evidence for #236

- [ ] 5 custom roles created (screenshot of Roles dashboard).
- [ ] Roster CSV imported; user count matches the confirmed headcount.
- [ ] Spot-check: an `field-sync` user **cannot** log into the web UI; a `supervisor-monitor` user sees `report` but **not** `data`; `data-manager` can export.
- [ ] Password policy applied; access-review cadence recorded in the Operations SOP.

---

## 6. ⟨DECISION⟩ — needs ASPSI before provisioning (not data-programmer calls)

1. **The actual personnel roster** (names + field IDs per cluster) — to fill the CSV. The Survey Manual headcount (6 RAs / 20 FS / 100 SE) is from the manual; **confirm it hasn't shifted** (this was also flagged as Survey-Manual open-question #4).
2. **Who holds the built-in `Administrator`** (break-glass) and **who is `data-manager`** with export rights (the §6.3 export-approval owner).
3. Whether assistant data managers need `data` (full export) or `report` (monitoring) only.

These are surfaced for your go/no-go and routing to ASPSI — not DOH-facing.
