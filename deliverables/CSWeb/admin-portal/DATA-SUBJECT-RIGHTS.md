---
module: CAPI Console Admin Portal
task: E9-ADMIN-044
created: 2026-08-09
status: runbook — procedure defined, legal basis needs ASPSI/DOH sign-off
---

# Data-subject rights runbook — UHC Survey Year 2

What to do when a respondent asks *"what do you hold about me"* or *"delete
me"*. Written because the answer was previously "nobody knows", and RA 10173
gives a data subject the right to both (§16(c) access, §16(e) erasure or
blocking) with a **15-day** response expectation under NPC Circular 16-03.

Every table and path below was verified against the live database on
2026-08-09. Row counts are pretest-era and will grow.

> [!warning] The legal question is not mine to answer
> Whether §16(e) **erasure** applies at all to a statistical collection carried
> out under a DOH mandate is a determination for ASPSI and DOH, not for the
> engineer holding the delete key. Research and statistical processing has
> narrower erasure obligations than commercial processing, and destroying a
> case may breach the survey's own obligations to PSA/DOH. **Route every
> erasure request to ASPSI before executing anything in Part 2.** Part 1
> (access/export) has no such ambiguity — do it.

## 0. Identify the subject

There is no name-keyed index, by design. Respondents are identified by:

| Instrument | Identifier | Where it lives |
|---|---|---|
| F1 Facility Head | 12-digit case key (QN) | `csweb_uhc_y2.FACILITYHEADSURVEY_DICT.key` |
| F3 Patient | 12-digit case key (QN) | `csweb_uhc_y2.PATIENTSURVEY_DICT.key` |
| F4 Household | 12-digit case key (QN) | `csweb_uhc_y2.HOUSEHOLDSURVEY_DICT.key` |
| F2 Healthcare Worker | `hcw_id` (+ `qn`, `facility_id`) | `csweb_f2.f2_hcws`, `csweb_f2.f2_responses` |

A respondent will not know their case key. In practice you locate them via the
facility and the interview date through the field team — which is itself a
reason the answer must go back through ASPSI rather than direct.

## 1. Access / export (do this)

Everything for one CSPro case key `$K`:

```sql
-- authoritative CSPro store: the questionnaire itself
SELECT * FROM csweb_uhc_y2.PATIENTSURVEY_DICT            WHERE `key` = '$K';
SELECT * FROM csweb_uhc_y2.PATIENTSURVEY_DICT_notes      WHERE `key` = '$K';
-- photographs and other captured binaries
SELECT * FROM csweb_uhc_y2.PATIENTSURVEY_DICT_case_binary_data WHERE `key` = '$K';

-- flattened breakout copy (one row per section)
SELECT * FROM csweb_f3_breakout.cases WHERE `key` = '$K';
--   then each section table joined on the same key; the section list is
--   the table list of csweb_f3_breakout (a_*, b_*, … plus field_control)
```

For an F2 healthcare worker `$H`:

```sql
SELECT * FROM csweb_f2.f2_hcws     WHERE hcw_id = '$H';
SELECT * FROM csweb_f2.f2_responses WHERE hcw_id = '$H';   -- values_json holds the answers
```

**Also disclose who has looked at it.** Post-cutover, `authz.php` writes an
audit row for every read of `/docs/cases/`, `/docs/f2/`, `/docs/data/` and the
case pages. That is arguably the most useful thing you can give a data subject:

```sql
SELECT ts, actor, verb, target, ip FROM capi_auth.console_audit
 WHERE target LIKE CONCAT('%', '$K', '%') ORDER BY ts;
```

Export as CSV from the Audit screen for the audit part; hand-assemble the case
part. There is no one-button export and, at this volume, building one would
cost more than doing it by hand a handful of times.

## 2. Erasure or blocking (only after ASPSI sign-off)

Order matters. Work from the source of truth outward, then let the generators
catch up — every derived artefact is rebuilt from the database on a 2-minute
cron, so deleting a derived file without deleting the row just recreates it.

1. **Take a dump first.** `bash /opt/borg/preBackup.sh` — it works now
   (see RETENTION.md; it had been silently producing nothing).
2. **CSPro store** — delete or blank the case in the `*_DICT`, `*_DICT_notes`
   and `*_DICT_case_binary_data` tables. Prefer CSWeb's own delete so its
   `last_modified_revision` bookkeeping stays coherent; a raw SQL delete can
   confuse the next incremental sync.
3. **Breakouts** — `csweb_f{1,3,4}_breakout`: delete from `cases` and from
   every section table on the same `key`.
4. **F2** — `f2_responses` for the answers; decide separately whether the
   `f2_hcws` roster row goes (it holds an enrolment token, not answers).
5. **Generated artefacts** — after the DB is clean, force a regeneration
   rather than hand-deleting files:
   `/opt/csweb-cases-gen.py`, `/opt/csweb-f2-cases-gen.py`,
   `/opt/csweb-responses-gen.py`, `/opt/csweb-spss-gen.py`,
   `/opt/csweb-tabulations-gen.py`. Then confirm the case no longer appears
   under `/docs/cases/`, `/docs/f2/` or the data room.
6. **Tablets.** A case already synced to a device is outside the server's
   reach. Field ops must confirm the device copy is cleared, or the erasure is
   partial and you should say so in the response.
7. **Backups.** Borg keeps 7 days (`--keep-within=7d`). An erased case persists
   in snapshots until they age out. This is normal and defensible, but it must
   be *stated* in the response rather than discovered later.
8. **Do not touch `console_audit`.** It records that an operator read a case,
   which is data about the operator. The application cannot delete it anyway
   (E9-ADMIN-012).

## 3. Response template

Record every request and its outcome. Until there is a register, log it as an
audit row so it is durable and timestamped:

```sql
INSERT INTO capi_auth.console_audit (actor, verb, target, detail, ip)
VALUES ('<who handled it>', 'dsr.request', '<case key or hcw id>',
        JSON_OBJECT('type','access|erasure','received','2026-08-09',
                    'outcome','fulfilled|refused|referred','note','...'),
        '');
```

`dsr.request` is a deliberate verb: it makes the Audit screen the register,
filterable with `verb = dsr.` like any other family.

## 4. What is still missing

- **No respondent-facing channel.** There is no address a data subject can
  write to. That belongs on the consent form and is ASPSI's to publish.
- **No 15-day clock.** Nothing tracks elapsed time against a request. The
  audit row above is a record, not a reminder.
- **No tested erasure.** This procedure has never been executed end to end. It
  should be rehearsed once against a disposable pretest case before it is
  needed for a real one — a runbook first run under time pressure is a draft.
