---
title: "99 — Quick Reference"
category: deliverable
tags: [capi, cspro, csweb, csentry, quick-reference, cheat-sheets, uhc-y2]
last_updated: 2026-05-08
status: draft
---

# 99 — Quick Reference

One page per role. Print it. Pin it. Tape it inside the back cover of the field manual. The long-form guide files do the explaining; this file does the reminding.

Each cheat sheet is a stand-alone page covering the same five-block shape — **Daily ritual | Top commands/checklists | Top escalation triggers | Cross-references** — so anyone in the project can find theirs in under five seconds.

The cheat sheets in this file:

1. CAPI Developer (Carl)
2. CAPI QA Tester (Shan)
3. CSWeb Administrator (TBD)
4. Field Manager (Almendral / TBD)
5. Survey Team Leader (STL)
6. Survey Enumerator (SE)
7. Project Coordinator (Juvy)
8. Project Lead (Dr Claro)
9. Survey Manager (Paunlagui)

Plus a **Common reference appendix** with the Khurshid pointer, six critical Khurshid rules, the file map, and a glossary.

---

## Cheat sheet 1: CAPI Developer (Carl)

**Role**: Owns the CSPro side of F1, F3, F4 — generators, dictionaries, FMFs, PROC logic, PFF packaging, regression-as-data. Hands builds to QA (Shan), then to CSWeb Admin for sync wiring, then to the field.

### Daily ritual

- 09:00 standup (per-project Scrum) — read overnight Slack from `#capi-dev`, scan GitHub Issues triaged overnight, pick the top item from the sprint backlog.
- Pull latest spec changes from ASPSI Survey Manager (Paunlagui) and Project Coordinator (Juvy). If a questionnaire row changed, the **generator is the patch site, not the dcf**.
- Regenerate the affected dictionary; diff the dcf against the previous build; update the skip-logic-and-validations spec where the generator change implies a logic or validation shift.
- Open CSPro Designer; verify item properties (length, decimals, value-set bindings); rebuild the FMF skeleton if forms shifted.
- Replay the regression mock cases on the rebuilt app in CSEntry Windows. Any failure is a P1 — fix before commit.
- End of day: commit generators + artefacts + spec together; post a one-line build digest to `#capi-dev`.

### Top commands

Regenerate all dcfs in one shot:

```bash
python deliverables/CSPro/F1/generate_dcf.py && \
python deliverables/CSPro/F3/generate_dcf.py && \
python deliverables/CSPro/F4/generate_dcf.py && \
python deliverables/CSPro/shared/build_psgc_lookups.py
```

Regenerate FMF skeletons after a dcf change (F3 + F4):

```bash
python deliverables/CSPro/F3/generate_fmf.py && \
python deliverables/CSPro/F4/generate_fmf.py
```

Export review workbooks for second-opinion review without CSPro Designer:

```bash
python deliverables/CSPro/export_dcf_to_xlsx.py --all
```

Open CSPro Designer with the F1 entry app:

```text
"C:\Program Files (x86)\CSPro 8.0\CSPro\CSDesigner.exe" ^
  "C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro\F1\FacilityHeadSurvey.ent"
```

Run regression replay (per [[05-Phase-7-Testing]]):

```text
CSEntry Windows -> Open PFF -> Replay test-cases\*.csdb against the new build -> diff exports
```

### CSPro Designer keyboard shortcuts that matter most

| Shortcut | Action |
|---|---|
| **Ctrl+T** | Toggle dictionary tree between names and labels |
| **F2** | Help text editor for current field |
| **F5** | Run the application |
| **F8** | Rebuild |
| **Ctrl+S** | Save |

### Common errmsg patterns (paste-ready)

```text
errmsg("Q12_AGE must be 0-120; entered: %d", Q12_AGE) reenter;
errmsg("Q34_TENURE (%d) cannot exceed AGE (%d) - 15", Q34_TENURE, Q12_AGE) reenter;
errmsg("Select at most one 'I don't know' in the multi-select.") reenter;
errmsg("Date of birth %s is in the future.", edit("9999/99/99", DOB)) reenter;
```

### Trace setup for Android **(Khurshid 2023-09-19)**

Window-based trace (`tracewindow on`) is silently ignored on CSEntry Android. Use file-based:

```text
PROC GLOBAL
  set trace on file("trace.txt");
  set trace level=detail;
```

The file lands at the Android `path_type_csentry_external` resolved location (typically `<sdcard>/CSPro/<APP>/trace.txt`). Pull with `adb pull /sdcard/CSPro/F1/trace.txt`.

### Escalation triggers

| Trigger | Escalate to |
|---|---|
| Methodology / sampling / replacement-cap question | Survey Manager (Paunlagui) |
| Client-facing change request, deliverable slip, missing input from DOH | Project Coordinator (Juvy) |
| Ethics / SJREB blocker (e.g. consent text mismatch) | Project Lead (Dr Claro) via Juvy |
| QA found a release-blocker after PFF was packaged | Pause distribution; new PFF revision before any further field push |
| Schema change requested mid-fieldwork | Hold; **never** add fields to a dcf in production without an `addkey` migration plan **(Khurshid 2023-09-21)** |

### Cross-references

- [[03-Phase-3-5-Spec-and-Generators]] — spec, parser, dictionary regeneration loop.
- [[04-Phase-6-Build-CAPI-App]] — FMF, PROC, capture types, FIELD_CONTROL block.
- [[05-Phase-7-Testing]] — regression-as-data discipline.
- [[02-Phase-0-2-Foundation]] — CSPro concept pages and toolchain knowledge base.

---

## Cheat sheet 2: CAPI QA Tester (Shan)

**Role**: Receives a CSPro build from Carl, walks the happy path, walks every skip variant, replays regression cases, files bugs against GitHub Issues with reproducible repro steps. Owns the **bench-test sign-off** that gates pretest.

### Daily ritual

- Pull the latest build from `#capi-dev` (PFF + dcf + fmf + apc) and confirm version stamp matches the build digest.
- Walk **happy path** end-to-end on CSEntry Windows: cover screen -> consent -> screening -> all sections -> disposition -> save complete.
- Walk **skip variants**: every "if Yes go to Q…", every "None of the above" route, every eligibility gate, every Other-specify path.
- **Replay regression cases** — load each `.csdb` in `test-cases/` against the new build; any prior-passing case that now fails is a P1.
- File bugs as they appear; do not batch — Carl can fix in parallel.
- Pull Android trace if a tablet bug is suspected (`adb pull /sdcard/CSPro/F1/trace.txt`).
- End of day: post a status line to `#capi-dev` — `<n> cases replayed, <n> new bugs (P0/P1/P2), build status: GREEN | RED`.

### Test-case checklist template

```markdown
- [ ] Cover page captures interviewer + supervisor IDs
- [ ] Consent screen verbatim matches Annex H ICF for this instrument
- [ ] Eligibility gate routes the ineligible path correctly
- [ ] GPS auto-captures on screen open
- [ ] Verification photo block fires at end-of-interview
- [ ] PSGC cascade Region -> Province -> City -> Barangay all populate
- [ ] Roster max occurs respected (F4 C_HOUSEHOLD_ROSTER = 20)
- [ ] Every HARD validation triggers + clears
- [ ] Every SOFT validation warns + accepts override
- [ ] Every dynamic value-set branch surfaces the right options
- [ ] Partial save survives app kill + relaunch (Khurshid 2022-09-21 OnStop+savepartial)
- [ ] Disposition codes populate FIELD_CONTROL
- [ ] Multi-language toggle re-renders labels without losing focus
```

### Regression replay command

```text
CSEntry Windows -> File -> Open PFF -> select FacilityHeadSurvey.pff
  -> File -> Run from data file -> select test-cases\<case>.csdb
  -> verify run completes without errmsg pop ups
  -> compare exported .dat to expected fixture
```

For batch replay, use a small Python harness that walks `test-cases/*.csdb` and shells out to `CSEntry.exe` per case (one is checked into `deliverables/CSPro/<F>/test-cases/replay.py` once it lands).

### Android trace file location

```text
<sdcard>/CSPro/F1/trace.txt
<sdcard>/CSPro/F3/trace.txt
<sdcard>/CSPro/F4/trace.txt
```

(Path resolves via `path_type_csentry_external` per CSEntry Android conventions.) Pull with:

```bash
adb pull /sdcard/CSPro/F1/trace.txt ./trace-F1-$(date +%Y%m%d-%H%M).txt
```

### Bug report template

Title format:

```text
[<F1|F3|F4>] [<Section>] <one-line summary>
```

Body:

```markdown
**Severity**: P0 (blocks build) | P1 (blocks fieldwork) | P2 (correct but not blocking) | P3 (cosmetic)
**Build**: <commit short SHA or build digest>
**Device**: CSEntry Windows | CSEntry Android <model + Android version>

### Repro steps
1. Open <PFF>
2. ...
3. ...

### Expected
<what should happen>

### Actual
<what happens>

### Trace excerpt (Android only)
```
<paste the relevant 20 lines from trace.txt>
```

### Mock case
<attach .csdb if one reproduces the bug>
```

### Severity rubric

| Severity | Definition |
|---|---|
| **P0** | Build will not load, app crashes on launch, dictionary fails to load |
| **P1** | Mid-interview crash, data loss, sync failure, cross-field validation regression |
| **P2** | Skip path wrong but recoverable, label typo, capture type sub-optimal |
| **P3** | Cosmetic — alignment, font, screen overflow on a specific device |

### Tools she should have installed

- **CSEntry Windows** — to run PFFs without a tablet.
- **CSPro Designer** — read-only access to dcf/fmf for cross-referencing item properties.
- **ADB** (Android Debug Bridge) — to pull `trace.txt` and `csdb` files from a tablet.
- **GitHub Issues access** to `cplreyes/ASPSI-DOH-UHC-CAPI-Development` for filing.
- **Slack** in `#capi-dev` for real-time chat with Carl.

### Escalation triggers

| Trigger | Escalate to |
|---|---|
| Regression case that previously passed now fails on the latest build | Carl — P1 fix before next push |
| Bench-test sign-off blocker discovered <72h before pretest | Carl + Survey Manager (Paunlagui) — pretest may need to slip |
| Suspected questionnaire wording error (not a build bug) | Project Coordinator (Juvy) for client clarification |
| Tablet-only bug not reproducible on CSEntry Windows | Pull Android trace immediately, attach to issue |

### Cross-references

- [[05-Phase-7-Testing]] — full QA discipline, regression-as-data, bench-test sign-off gate.
- [[04-Phase-6-Build-CAPI-App]] — what each PROC pattern is supposed to do (so QA knows what to expect).

---

## Cheat sheet 3: CSWeb Administrator (TBD)

**Role**: Owns the CSWeb server — provisioning, user management, daily monitoring, hot-fix push to tablets, nightly backups. Receives PFF from Carl after QA sign-off; pushes to fielded tablets.

### Daily ritual

- **Wampserver tray icon green** — check first thing in the morning.
- **Verify nightly backup** — `csweb-YYYYMMDD.sql` exists in the backup folder, file size in expected range, restorability check once per week.
- **Check sync log** — every assigned tablet has at least one successful sync in the last 24 h. Stale tablets (`>24h no sync`, computed from CSWeb `synctime()`) get flagged to the Field Manager.
- **Check case counts** — per dictionary (F1/F3/F4), expected delta from yesterday; zero on a working day = anomaly.
- **Update issue log** — every field-reported anomaly with resolution notes.
- **Post overnight digest** to `#capi-fieldwork-ops` so STLs and FM see sync state by 08:00.

### Provisioning checklist (Day 1)

Per [[06-Phase-8-CSWeb-and-Tablets]] §8.2-8.4:

1. Install Wampserver (Apache + MySQL + PHP); confirm tray icon green.
2. Drop CSWeb PHP application into `wamp64/www/csweb/`.
3. Initialize MySQL database `csweb` (run install SQL from CSWeb distribution).
4. Set CSWeb admin password; rotate from default immediately.
5. **Configure firewall** — port 80 / 443 inbound from the org's static IP block; **NEVER** expose CSWeb to the public internet.
6. Define dictionaries on the server — upload F1/F3/F4 `.dcf` via the CSWeb Data Settings dashboard.
7. Configure relational break-out for repeating records (F4 C_HOUSEHOLD_ROSTER).
8. Bulk-create users via CSV (see format below).
9. Test sync round trip from a tablet over the org WiFi; confirm record landed in the relational break-out tables.
10. Confirm the **live sync URL is the LAN IP, not localhost** **(Khurshid 2022-04-30)** — tablets cannot resolve `localhost` on the server.

### User CSV format

```csv
username,password,role,name,email
STL01-01,Tempo123!,STL_NCR,Juan dela Cruz,j.delacruz@aspsi.example.com
SE01-01,Tempo456!,ENUMERATOR,Maria Santos,
SE01-02,Tempo789!,ENUMERATOR,Pedro Reyes,
FM01,Tempo321!,FIELD_MANAGER,Almendral,almendral@aspsi.example.com
```

Roles map to CSWeb's two built-in roles (Administrator, Standard User) plus per-dictionary up/down permissions on the F1/F3/F4 dictionaries — set per-user after CSV import.

### Daily monitoring checklist

```markdown
- [ ] Wampserver tray icon green
- [ ] Nightly backup file exists and size > 1 KB
- [ ] CSWeb Sync Report opens; no error banner
- [ ] Per-dictionary case count delta vs yesterday within expected band
- [ ] No tablet >24h since last sync
- [ ] No HMAC / auth failures in CSWeb log (these usually mean clock skew)
- [ ] All assigned STL/SE/FM accounts are still active (no accidental disable)
- [ ] App version on the server matches the version STLs report from the field
```

### Hot-fix push procedure

1. Carl publishes a new `.pen` to the shared drive plus a one-line CHANGELOG entry.
2. CSWeb Admin downloads the `.pen` and verifies the SHA matches the published one.
3. Upload the `.pen` to the CSWeb application slot for that dictionary (F1 / F3 / F4).
4. Bump the app-version field; tablets see the new version on next sync.
5. Force-sync one canary tablet; verify new build serves; confirm a roundtrip test case lands in the right relational break-out tables.
6. Broadcast in `#capi-fieldwork-ops`: **"PFF v<X.Y.Z> deployed; STLs please confirm tablets pulled new version on next sync."**
7. Watch the next 24 h sync log for stuck tablets (still on old version).

### Backup commands

```bash
# Daily MySQL dump (cron at 02:00 local)
mysqldump -u root -p csweb > C:\backups\csweb-$(date +%Y%m%d).sql

# Compress + retain 30 days
gzip C:\backups\csweb-$(date +%Y%m%d).sql

# Weekly off-server copy (rsync, robocopy, or rclone to external)
robocopy C:\backups \\nas01\aspsi\csweb-backups /MIR /R:3 /W:10
```

Restore drill (run quarterly):

```bash
mysql -u root -p csweb < C:\backups\csweb-YYYYMMDD.sql
```

### Escalation triggers

| Trigger | Escalate to |
|---|---|
| Server hard-down (Wampserver fails to start, OS-level error) | Field Manager + Project Coordinator (Juvy) **immediately** |
| Mass sync failure (>10% of tablets, or whole region) | Field Manager — likely network or version-drift root cause |
| App version drift detected (tablet reports older version than server) | Carl — possible PFF packaging issue |
| Backup failure (no `csweb-YYYYMMDD.sql` for 2 days) | Project Coordinator (Juvy) — risk of data loss escalates fast |
| HMAC / clock-skew failures climbing | Suspect tablet system-clock drift; flag to FM for cluster-level check |

### Cross-references

- [[06-Phase-8-CSWeb-and-Tablets]] — provisioning, sync architecture, tablet packaging.
- [[07-Phase-9-10-Pretest-Fieldwork]] — daily monitoring + hot-fix protocol in production.

---

## Cheat sheet 4: Field Manager (Almendral / TBD)

**Role**: Owns the field. Receives the CSWeb overnight digest, checks cluster sync rates, supports STLs in real time, makes the call on replacement requests within Annex D rules, and escalates to Survey Manager when the rules don't cover the case.

### Daily ritual

- 07:30 — read overnight digest from CSWeb Admin in `#capi-fieldwork-ops`.
- Verify **cluster sync rates** — every cluster has ≥ 80% of tablets synced in the last 24 h (target). Anything <80% surfaces as a flagged cluster.
- Walk through the STL daily reports filed by 22:00 the previous day; pick up open issues.
- Address replacement-protocol questions — STLs ping FM, FM rules per Annex D or escalates to Survey Manager.
- 17:00 check-in — STLs post a snapshot to `#capi-fieldwork-ops` (cluster, cases captured today, sync status).
- 22:30 — confirm all STLs filed daily reports; chase the missing ones.

### Tablet provisioning checklist (abridged)

Per [[06-Phase-8-CSWeb-and-Tablets]] §8.15:

```markdown
- [ ] Tablet OS up to date (security patches at least current quarter)
- [ ] Storage encryption enabled
- [ ] Lock screen with PIN (per ICF privacy commitment)
- [ ] CSEntry Android installed from APK on shared drive (do NOT use Play Store version - version mismatch risk)
- [ ] PFF + dcf + fmf + apc deployed under /sdcard/CSPro/<F>/
- [ ] Sync URL configured: http://<csweb-server-LAN-IP>/csweb (NOT localhost)
- [ ] Sync credentials configured per assigned SE
- [ ] One sync round trip tested on org WiFi before handover
- [ ] System clock auto-set from network (HMAC will reject skewed clocks)
- [ ] Battery health check (>80% of design capacity)
- [ ] Asset tag affixed; serial number logged
- [ ] Tablet handover form signed by SE (per Annex D return-to-base rules)
```

### Sync troubleshooting decision tree (first-line)

```text
"Tablet won't sync"
  -> Q1: Can the tablet reach any web page in a browser?
        NO  -> WiFi / cellular issue. Reconnect; if persists, escalate to FM.
        YES -> Q2: Sync URL is the live LAN IP (not localhost)?
                 NO  -> Reconfigure (Khurshid 2022-04-30).
                 YES -> Q3: Tablet system clock within +-5 min of CSWeb server?
                          NO  -> Force network time sync; retry.
                          YES -> Q4: CSEntry Android version matches PFF target?
                                   NO  -> Reinstall APK from shared drive.
                                   YES -> Q5: Pull trace.txt and post to issue
                                              (sdcard/CSPro/<F>/trace.txt).
                                              Escalate to Carl + CSWeb Admin.
```

### Replacement protocol cheat sheet

Annex D rules — paste this on the back of every STL clipboard:

| Rule | Detail |
|---|---|
| **Minimum contact attempts** | ≥ 3 visits before a unit may be flagged for replacement |
| **Stratum match** | Replacement must be drawn from the same stratum (region × cohort × class) |
| **Cap** | 5–10% of facility/household sample; FM must monitor running cap; >10% = SM escalation |
| **Enumerator discretion** | **None.** SE may not pick a replacement on their own. STL files the request; FM rules; SM signs off when cap is approaching. |
| **Documentation** | Every replacement carries the original case ID, the 3 visit attempts with timestamps, and the new case ID drawn from the same stratum |

### Escalation tree

```text
SE  -> STL  -> FM  -> Survey Manager (Paunlagui)  -> Project Lead (Dr Claro)
                                              ^
                                              |
                            (only methodology questions reach SM;
                             only contractual / ethics issues reach Project Lead)
```

| Trigger | Escalate to |
|---|---|
| Standard sync issue resolvable on-tablet | Stays at STL/SE level |
| Sync issue requires server / version intervention | CSWeb Admin via FM |
| Replacement request within Annex D rules | FM rules |
| Replacement request that breaks cap or stratum rule | Survey Manager (Paunlagui) |
| Refusal-rate spike, suspected SJ violation, lost tablet | Survey Manager + Project Coordinator (Juvy); Project Lead if ethics implicated |
| App-level bug or build defect | Carl via CSWeb Admin |

### Cross-references

- [[01-Roles-and-Handoffs]] — full RACI + escalation tree.
- [[07-Phase-9-10-Pretest-Fieldwork]] — pretest + main-fieldwork operations.

---

## Cheat sheet 5: Survey Team Leader (STL)

**Role**: Leads a cluster team of SEs in the field. Runs the morning standup, supports SEs through the day, does the **end-of-day sync verification**, files the daily report, and is the first escalation point for SE issues.

### Daily ritual

- **09:00 standup** with SEs — yesterday/today/blockers; confirm tablet ID, charge level, today's assigned cases.
- **Mid-day check-in** — quick walk-through of cases captured so far; flag any SE who is stuck or behind pace.
- **17:00 evening sync verification** — every SE syncs their tablet under STL supervision (or remote attestation if dispersed); STL confirms each tablet shows "sync successful" with today's date.
- **22:00 daily report** filed to `#capi-fieldwork-ops` — cluster, cases captured, sync status per tablet, blockers, replacement requests if any.

### Daily sync verification checklist

```markdown
- [ ] Open CSWeb Reports -> Sync Report
- [ ] Filter by cluster
- [ ] Confirm every assigned tablet synced today (date matches)
- [ ] Per-tablet case count > 0 on a working day (zero is an anomaly)
- [ ] Per-tablet case count is consistent with the SE's day plan
- [ ] No "sync error" rows in the report
- [ ] Cross-check the on-tablet "last sync" timestamp against the server
- [ ] Confirm partial-save cases are intact (Khurshid 2022-09-21 OnStop+savepartial)
- [ ] Note any anomaly in the daily report
```

### Replacement protocol (one-line summary)

Annex D rules apply: ≥3 visits, same stratum, 5-10% cap, **no enumerator discretion**. STL files the request to FM with the visit log; FM rules. Full rules on the **Field Manager cheat sheet** above.

### Field anomaly reporting (paste-ready Slack format)

```text
*Daily Field Report — Cluster <N> — <Region> — <YYYY-MM-DD>*
- STL: <name>
- Cases captured today: F1=<n>, F3=<n>, F4=<n>
- Sync status: <X>/<Y> tablets synced
- Blockers: <one-line per blocker>
- Replacement requests: <count> (filed to FM)
- Anomalies: <one-line per anomaly, e.g. refusal cluster, app crash, SJ concern>
- Tomorrow's plan: <one-line>
```

### Escalation triggers

| Trigger | Escalate to |
|---|---|
| Tablet won't sync after the SE tried twice | STL runs the FM decision tree (above); if unresolved, escalate to FM |
| App crash or freeze that loses data | FM + Carl (via FM); pull trace.txt if Android |
| Refusal-rate spike on a cluster (>30% in a day) | FM + Survey Manager (Paunlagui) — methodology issue |
| Replacement cap approaching (>8%) | FM **before** filing the next replacement |
| SJ violation, lost or stolen tablet, safety incident | FM + Survey Manager **immediately**; Project Lead if ethics-implicated |

### Cross-references

- [[07-Phase-9-10-Pretest-Fieldwork]] — STL operating routine + cluster monitoring.
- [[01-Roles-and-Handoffs]] — full escalation tree + RACI.

---

## Cheat sheet 6: Survey Enumerator (SE)

**Role**: Captures cases. Owns the tablet during fieldwork, conducts the interview per the questionnaire and survey manual, syncs end-of-day, hands the tablet back to STL for charging.

### Daily ritual

- 09:00 morning standup with STL.
- Charge tablet to >80% before leaving base.
- Capture cases per assignment; save partial when interrupted, save complete when done.
- End-of-day: sync from the field if connectivity allows; otherwise sync at base.
- Hand tablet to STL for charging (or charge yourself if multi-day deployment).
- Brief blocker note to STL; chase by Slack if urgent.

### Tablet basic-ops

| Action | How |
|---|---|
| **Turn on** | Power button (top-right); enter PIN (your assigned SE-PIN) |
| **Login** | Open CSEntry Android -> select F1 / F3 / F4 PFF -> enter operator credentials if prompted |
| **Launch entry app** | Tap the PFF tile -> the cover/eligibility screen opens |
| **Capture case** | Walk through screens; "Next" or auto-advance moves you forward |
| **Save partial** | Menu -> Save partial (case marked in-progress; resumable from sync server) |
| **Save complete** | Reach disposition screen -> select disposition code -> Save complete |

### Sync trigger

- Menu -> **Sync** (or the dedicated sync button if mapped on the launcher).
- Success looks like: a green confirmation banner with "Sync successful — N cases sent". Tablet's "Last sync" timestamp updates to now.
- Failure looks like: a red banner with an error code, or no progress after 60 seconds.

### What to do when sync fails

1. **Try again.** Tap Sync once more — transient network errors clear themselves.
2. **Check connectivity.** Open a browser; visit any web page. If that fails, reconnect WiFi or switch to cellular.
3. **Check sync URL.** Confirm it's the LAN IP **(Khurshid 2022-04-30)**, not `localhost` or a hostname your tablet can't resolve.
4. **Report to STL.** If 2 attempts fail, hand it to STL with a brief description; **do not keep retrying** without escalation — repeated failures may indicate a server-side issue.

### Replacement protocol (when an SE may NOT decide)

**Never decide a replacement on your own.** Annex D forbids enumerator discretion. If a unit refuses, is unreachable after 3 visits, or is otherwise non-respondent, **document the visit log and report to STL**; STL files to FM; FM rules.

### Tablet care

| Concern | Rule |
|---|---|
| **Battery** | Charge to 100% overnight; carry a power bank for >6 h field days |
| **Water** | Tablets are NOT waterproof; carry a zip-top dry bag in rainy weather |
| **Drops** | Use the issued case + screen protector; report cracks immediately |
| **Theft** | Never leave the tablet in a vehicle or unattended in public; lost tablet = immediate STL escalation |
| **Personal use** | None. Tablets carry case data and ICF-protected information |

### Escalation triggers

| Trigger | Escalate to |
|---|---|
| App freeze that doesn't resolve on relaunch | STL — pull trace.txt if STL knows how |
| Sync failure after 2 attempts | STL — do not retry blindly |
| Lost or stolen tablet | STL **immediately**; STL escalates to FM and Survey Manager |
| SJ violation (consent issue, harassment, threat) | STL + Survey Manager — same day |
| Respondent visibly distressed by a question | STL and document on the case; SM may need to update training |

### Cross-references

- Pretest training materials (forthcoming under `deliverables/Survey-Manual/`).
- Survey Manual Working File (Kidd 2026-05-06) — duties of SEs section.

---

## Cheat sheet 7: Project Coordinator (Juvy)

**Role**: Owns formal client-facing communications with DOH-PMSMD and the deliverable-acceptance loop. Carl is **not** a DOH sender; client-facing comms route through Juvy or Kidd.

### Daily ritual

- Morning: scan DOH-PMSMD inbox + Slack; triage anything time-sensitive.
- Mid-day: deliverable scheduling — confirm upcoming tranche dates, gate review meetings, SJREB submission windows.
- Coordinate internally with Carl, Survey Manager (Paunlagui), Project Lead (Dr Claro), Kidd.
- Evening: post tomorrow's gate / blocker summary to the internal ASPSI channel.

### Weekly client comms template (paste-ready)

```text
Subject: ASPSI-DOH UHC Y2 — Week of <YYYY-MM-DD> Update

Dear DOH-PMSMD team,

This week's progress:
- <bullet 1: completed deliverable / milestone>
- <bullet 2: ongoing build or test stream>
- <bullet 3: input received / acknowledgement>

Open issues / risks:
- <bullet 1: blocker + proposed mitigation>
- <bullet 2: open client clarification request>

Asks of DOH-PMSMD this week:
- <bullet 1: e.g. SJREB endorsement letter draft>
- <bullet 2: e.g. confirm tablet procurement spec>

Respectfully,
Juvy Chavez-Rocamora
ASPSI Project Coordinator
```

### Deliverable acceptance checklist

Before signing off on a tranche payment:

```markdown
- [ ] Deliverable packet attached (Inception / Pretest / CAPI build / Final)
- [ ] All annexes referenced in the contract are present
- [ ] Survey Manager (Paunlagui) signed off on methodology content
- [ ] Carl signed off on CAPI / CSWeb technical content (if applicable)
- [ ] Project Lead (Dr Claro) signed off on the cover memo
- [ ] SJREB clearance status reflected accurately
- [ ] Date of submission and version number on every component
- [ ] Acknowledgement-of-receipt request included
- [ ] Tranche reference + amount in the cover memo
```

### Communication protocol reminder

- **Carl is NOT a DOH sender.** All formal DOH-facing comms route through **Juvy or Kidd** per the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Team Communication Protocol|Team Communication Protocol]] adopted at the 2026-04-13 ASPSI Team Meeting.
- Carl's CAPI inputs go to **Kidd** (for Survey Manual integration) and **Juvy** (for client-facing packaging).
- Slack `#capi-dev` is internal; never paste DOH client there.

### Escalation triggers

| Trigger | Escalate to |
|---|---|
| DOH change request that affects scope or timeline | Project Lead (Dr Claro) — joint review |
| Deliverable slip risk (>5 working days) | Project Lead + Survey Manager — replan the tranche |
| Contract issue (payment, scope language, late-penalty) | Project Lead — owner of the signed CSA |
| Ethics escalation surfacing in client comms | Project Lead + Survey Manager — ethics is a Project Lead authority |
| Field anomaly DOH gets wind of before our weekly update | Project Lead + Field Manager — pre-empt with a same-day brief |

### Cross-references

- [[01-Roles-and-Handoffs]] §6 — full communication protocol.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Team Communication Protocol]] — formal routing.

---

## Cheat sheet 8: Project Lead (Dr Claro)

**Role**: Final sign-off on contractual deliverables, ethics escalations, and tranche payment release. Convenes LSS sessions when the project teaches us something we need to absorb organisation-wide.

### Weekly ritual

- Monday — read weekly digest from Project Coordinator (Juvy); flag items for the week's gate review.
- Mid-week — attend LSS / internal review session (event-driven; not on a fixed weekly cadence in this project).
- Friday — sign off on the week's deliverables; release the next tranche if the prior tranche has been formally accepted.

### Decision authority

Only the Project Lead may sign off on:

| Decision | Why it sits here |
|---|---|
| **Final deliverable acceptance** to DOH-PMSMD | Owner of the signed CSA |
| **Tranche payment release** | Contractual gate; tied to acceptance |
| **SJREB / IRB ethics submissions and responses** | Ethics is a Project Lead authority — methodology + safety |
| **Scope-affecting client change requests** | Re-baselines the contract and timeline |
| **Public-facing comms to DOH or co-funders** | Carl + Juvy + Kidd are the senders; Project Lead is the signatory |

### Cross-references

- [[01-Roles-and-Handoffs]] §10 — authority matrix.

---

## Cheat sheet 9: Survey Manager (Paunlagui)

**Role**: Methodology authority. Signs off on sample design, replacement-protocol exceptions, pretest plan, training plan, and any methodology question that comes up the escalation tree.

### Daily ritual (during active fieldwork)

- Morning: scan `#capi-fieldwork-ops` for methodology pings from STLs / FM.
- Mid-day: review any replacement-cap excursions or stratum-substitution edge cases the FM has flagged.
- Pretest oversight (during pretest weeks): observe sessions, debrief enumerators, capture findings to feed back into the build.
- Evening: post a one-line methodology status to the internal channel if anything moved.

### Authority

| Decision | Authority |
|---|---|
| **Sample design questions** (stratum boundaries, cluster assignments, replacement cap interpretation) | Survey Manager |
| **Replacement-cap exceptions** (>10%) | Survey Manager (escalates to Project Lead if scope-affecting) |
| **Pretest plan + sign-off** | Survey Manager (jointly with Project Lead) |
| **Training plan + sign-off** | Survey Manager |
| **Methodology disagreements with the questionnaire wording** | Survey Manager — Carl implements per ruling |

### Cross-references

- [[01-Roles-and-Handoffs]] — full RACI.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol]] — the rules SM owns.

---

## Common reference appendix

### Khurshid corpus quick-link

The Khurshid technique cards live at:

```text
[[3_Resources/Learning-Materials/mentors/khurshid-arshad/_index]]
```

How to use:

1. Open the `_index` page; scan the **CAPI phase** column.
2. Find the phase you're in (e.g. Phase 6 build, Phase 8 sync).
3. Read the linked technique cards for that phase — each is one technique with a date and a working code snippet.
4. If a card cites a YouTube clip, the clip is timestamped in the card metadata.
5. Cite back as `**(Khurshid YYYY-MM-DD)**` in your spec, code comment, or PR description.

### Critical Khurshid rules

Six rules every role should recognise on sight:

- **Tablet sync URL must be live LAN IP, not `localhost`** **(Khurshid 2022-04-30)** — tablets cannot resolve `localhost` on the server; first thing to check on any sync failure.
- **Window-based trace ignored on Android — use file-based** **(Khurshid 2023-09-19)** — `tracewindow on` is silently dropped; use `set trace on file("trace.txt")` and pull via `adb`.
- **Don't enter new cases before reformatting — old data won't recover** **(Khurshid 2023-09-21)** — new cases captured against an unmigrated dictionary cannot be recovered after the schema change.
- **Schema changes break `.dat` but not `.csdb`** **(Khurshid 2023-09-21)** — flat `.dat` exports break under schema drift; case database `.csdb` is more resilient. Always test recovery on `.csdb` after a dictionary change.
- **`errmsg` = HARD edit; `warning` = SOFT edit** **(Khurshid 2022-06-26)** — HARD blocks + forces re-entry; SOFT warns but accepts. Use the right tier per the validation spec.
- **`OnStop` + `savepartial` for durable resume** **(Khurshid 2022-09-21)** — a partial-save in `OnStop` survives app kill / battery die / OS restart; without it, in-flight cases are lost.

### File map

| Audience | Their primary guide files |
|---|---|
| **CAPI Developer (Carl)** | [[03-Phase-3-5-Spec-and-Generators]], [[04-Phase-6-Build-CAPI-App]], [[05-Phase-7-Testing]], [[02-Phase-0-2-Foundation]] |
| **CAPI QA Tester (Shan)** | [[05-Phase-7-Testing]], [[04-Phase-6-Build-CAPI-App]] |
| **CSWeb Administrator** | [[06-Phase-8-CSWeb-and-Tablets]], [[07-Phase-9-10-Pretest-Fieldwork]] |
| **Field Manager** | [[06-Phase-8-CSWeb-and-Tablets]], [[07-Phase-9-10-Pretest-Fieldwork]], [[01-Roles-and-Handoffs]] |
| **Survey Team Leader** | [[07-Phase-9-10-Pretest-Fieldwork]], [[01-Roles-and-Handoffs]] |
| **Survey Enumerator** | Survey Manual Working File (Kidd 2026-05-06), pretest training materials |
| **Project Coordinator (Juvy)** | [[01-Roles-and-Handoffs]], [[00-Architecture]] |
| **Project Lead (Dr Claro)** | [[01-Roles-and-Handoffs]], [[00-Architecture]] |
| **Survey Manager (Paunlagui)** | [[01-Roles-and-Handoffs]], [[03-Phase-3-5-Spec-and-Generators]] (for methodology-bearing items) |

### Glossary

| Term | Definition |
|---|---|
| **CAPI** | Computer-Assisted Personal Interviewing — interviewer-administered survey on a device |
| **CASI** | Computer-Assisted Self-Interviewing — respondent-administered on a device |
| **CAWI** | Computer-Assisted Web Interviewing — respondent-administered over the web (e.g. F2 PWA) |
| **CSPro** | Census and Survey Processing System — the toolchain (Designer + CSEntry + CSWeb + CSBatch + CSTab) maintained by US Census Bureau |
| **CSEntry** | The data-entry runtime in CSPro — Windows or Android |
| **CSWeb** | The web sync server in the CSPro toolchain (PHP + MySQL + Apache, packaged with Wampserver) |
| **CSBatch** | Batch-edit runtime — runs structure / validity / consistency / imputation passes |
| **CSTab** | Tabulation runtime — produces cross-tabs from `.dat` exports |
| **CSDB** | The case database file — `.csdb`; more resilient to schema change than `.dat` |
| **DCF** | Data Dictionary File — `.dcf`; the CSPro JSON schema for an instrument |
| **FMF** | Form Map File — `.fmf`; the CSPro form layout file edited in Designer |
| **APC** | Application logic file — `.apc`; the CSPro PROC code for an instrument |
| **PFF** | Packaged File Format — `.pff`; the deployable bundle for CSEntry |
| **PEN** | The packaged CSPro app archive used for hot-fix push |
| **PROC** | Procedural code blocks in `.apc` files — preproc, postproc, onfocus, killfocus, onoccchange |
| **FIELD_CONTROL** | Standard CSPro record carrying interviewer/supervisor IDs, AAPOR disposition, GPS, consent flags |
| **GEO_ID** | Standard CSPro record carrying the geographic key (region / province / city / barangay / facility / patient home where applicable) |
| **PSGC** | Philippine Standard Geographic Code — anchored on PSA 1Q 2026 in this project (43,803 entries) |
| **AAPOR** | American Association for Public Opinion Research — owner of the standard disposition code framework |
| **SJREB** | Single Joint Research Ethics Board — Philippine ethics-clearance body for this project |
| **IRB** | Institutional Review Board — generic ethics body (SJREB is the local instance) |
| **ICF** | Informed Consent Form — Annex H carries the four ICFs (F1/F2/F3/F4) |
| **DOH** | Department of Health (Philippines) — the client |
| **PMSMD** | DOH Performance Monitoring and Strategy Management Division — the contracting unit |
| **ASPSI** | Asian Social Project Services, Inc. — implementing organisation |
| **STL** | Survey Team Leader — leads a cluster team of SEs |
| **SE** | Survey Enumerator — captures cases on the tablet |
| **ICC** | Independent Component City — a Philippine LGU classification used in stratification |
| **HUC** | Highly Urbanised City — a Philippine LGU classification used in stratification |
| **UHC IS** | Universal Health Care Integration Site — the 107 LGUs in the UHC integration cohort |
| **F1 / F2 / F3 / F4** | Facility Head / Healthcare Worker / Patient / Household survey instruments |

---

## See also

- [[index]] — the master deliverable index for this guide.
- [[00-Architecture]] — the high-level system view.
- [[01-Roles-and-Handoffs]] — the long-form RACI + escalation tree this cheat-sheet pack distills.
- [[02-Phase-0-2-Foundation]] — toolchain knowledge base.
- [[03-Phase-3-5-Spec-and-Generators]] — generator + skip-logic spec.
- [[04-Phase-6-Build-CAPI-App]] — CAPI app build (Designer / FMF / PROC).
- [[05-Phase-7-Testing]] — regression-as-data discipline.
- [[06-Phase-8-CSWeb-and-Tablets]] — sync, packaging, deployment.
- [[07-Phase-9-10-Pretest-Fieldwork]] — pretest, fieldwork, hot-fix, daily monitoring.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/index|Project index]] — full source / entity / concept catalog.
