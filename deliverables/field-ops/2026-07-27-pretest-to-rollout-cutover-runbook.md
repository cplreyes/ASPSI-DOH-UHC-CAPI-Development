# Pretest → Rollout Cutover Runbook

**UHC Survey Year 2 · ASPSI × DOH · drafted 2026-07-27**
Owner: Carl Reyes · Executes: on the day ASPSI declares main fieldwork open
Status: **DRAFT — three decisions open (D1–D3), see §2**

---

## 1. What this is, and why it is lighter than it looks

The switchover from pretest to the survey proper. Every system that currently holds
pretest artifacts must either start clean or knowingly carry them forward.

**The good news, and it is substantial:** the activity/phase layer built on 26–27 July
already separates pretest from everything that follows. Every case carries a `phase`
(pretest / training / survey) and an `activity` (A1, A2 …), derived from the uploading
login and the date window. That classification flows into the dashboard filter, every
export column, the Overview counts and the tabulation previews.

So the historic hard problem of a cutover — *"how do we stop pretest numbers polluting
the real figures"* — is **already solved by filtering**. Purging is now an optional
tidiness step, not a requirement. That changes the risk calculus in §2.

### State at drafting

| Fact | Value |
|---|---|
| Pretest cases | **115** — F1 2 · F3 13 · F4 21 · F2 79 |
| Phase / activity | 100% `pretest` / `A1` — no misclassified rows |
| Enumerator sync accounts | 7 (`se-001`…`se-007`), 9 distinct users in sync history |
| Console accounts | 17 htpasswd entries (see trap T7 — duplicated `se_001` / `se-001` forms) |
| Assignment plan | F1 1,521 facilities (real) · F3 10 · F4 20 (**provisional**) |
| Instrument builds | F1 1.1.4 · F3 1.1.5 · F4 1.4.4 (2026-07-19) |
| Cron jobs | 16 · 6 reporting generators |
| Case-table engine | **InnoDB** (deletes are transactional and can roll back) |
| MyISAM tables | 7, all `oauth_*` in `csweb_uhc_y2` — **no transaction, no rollback** |

---

## 2. Decisions to make before the day

### D1 — Pretest case data: purge, or keep and filter?

| | Keep + filter **(recommended)** | Archive + purge |
|---|---|---|
| Effort | None — already works | Export, verify, delete, re-verify |
| Day-one counters | Filtered to `phase=survey`; pretest still visible if you ask for it | Naturally zero |
| Risk | A surface that forgets to filter shows a mixed number | Deletion on a live box; recovery depends on the snapshot being good |
| Reversibility | Total | Only from backup |
| Pretest record | Intact and queryable | Frozen file only |

**Recommendation: keep and filter.** The separation exists and is verified; deleting
115 rows to solve a problem that is already solved trades a real risk for a cosmetic
gain. Revisit only if DOH asks for a database that contains main-survey data *only*.

**If D1 = purge**, the case tables are InnoDB, so wrap deletions in a transaction and
verify counts before `COMMIT`. Do not touch `oauth_*` (MyISAM, no rollback) — those are
sessions, not survey data.

### D2 — Enumerator accounts: reuse `se-00x`, or issue a fresh roster?

**Recommendation: fresh roster, retire the pretest accounts.** Reusing logins makes the
activity classifier's roster rule ambiguous (the same login would span two phases, and
roster beats dates), and it muddies attribution in the audit trail. Retiring them is one
click each in the admin console. Keep them *disabled, not deleted*, so historic case
attribution still resolves.

### D3 — Do the legacy csweb front doors redirect now?

`csweb.asiansocial.org/` and `/help.html` still serve the old standalone site (HTTP 200).
The portal consolidation is not closed until they redirect. **Recommendation: do it at
cutover**, when tablets get their new configuration anyway — and never for `/csweb/**`,
which is the sync endpoint.

---

## 3. Pre-cutover (T-2 weeks → T-2 days)

Each item is safe to do early and independently.

| # | Task | Where | Verify |
|---|---|---|---|
| P1 | Declare the **Training** activity (dates + `tr-*` roster) | Admin → Activities | Overview shows it; a training case classifies to it |
| P2 | Create training accounts (`tr-*`), tier **field** | Admin → Users | Login reaches dashboard, not the data room |
| P3 | Load the **final EA plan** → `targets.json` | vault `gen-targets.py --final` + scp | Dashboard coverage denominators change |
| P4 | Deploy instrument builds to the full tablet fleet | CSPro Designer → CSWeb | Version footer on a device matches `versions.json` |
| P5 | Regenerate F2 facility links + QR codes for the real facility list | F2 admin portal | Sample link opens the right facility |
| P6 | Set the **Slack webhook** and press *Send test* | Admin → Alerting | Test message arrives |
| P7 | Bulk-create the real enumerator roster | Admin → Users (or bulk import) | Spot-check three logins |
| P8 | Dry-run this runbook end to end on a copy | — | Every §4 verification passes |

---

## 4. Cutover day — ordered checklist

Do these **in order**. Each step states its verification and its undo.

### Step 1 — Freeze and snapshot
```
# on the box
mkdir -p /opt/backups/cutover-$(date +%Y%m%d)
cd /opt/backups/cutover-$(date +%Y%m%d)
cp /opt/targets.json /opt/app/lamp/www/docs/admin/*.json .
cp /opt/app/lamp/www/.htpasswd-docs /opt/app/lamp/www/docs/.htaccess .
crontab -l > crontab.bak
docker compose -f /opt/app/docker-compose.yml exec -T database \
  mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines \
  --databases csweb_uhc_y2 csweb_f1_breakout csweb_f3_breakout csweb_f4_breakout csweb_f2 \
  | gzip > db-precutover.sql.gz
```
**Verify:** `gunzip -t db-precutover.sql.gz` exits 0, and the file is > 1 MB.
**Undo:** n/a — this *is* the undo for everything below.

### Step 2 — Cut the final pretest data package
Download the full data room (CSV/SPSS/Stata/R/CSPro), the codebook, and the tabulation
previews. Store as the pretest deliverable set. **Verify:** row counts match the console's
`phase=pretest` figures (115 at drafting). **Undo:** n/a.

### Step 3 — Close the pretest activity
Admin → Activities → set A1 `end` = last pretest day. Leave the row in place.
**Verify:** Overview shows Pretest as *ended*; classification of existing cases is unchanged.
**Undo:** clear the end date.

### Step 4 — (only if D1 = purge) Remove pretest cases
```sql
START TRANSACTION;
-- delete from each breakout schema's case tables where the case is pretest
SELECT COUNT(*) FROM ...;   -- confirm the number matches Step 2's package
-- COMMIT only if the count is exactly what you expect
COMMIT;
```
**Verify:** console totals drop to 0; the pretest package still opens.
**Undo:** `ROLLBACK` before commit; after commit, restore from Step 1.

### Step 5 — Declare the survey activity
Admin → Activities → A3 (or new): set start date, untick *planned*, attach the real
roster and quotas. **Verify:** Overview shows it active on day 1.
**Undo:** re-tick *planned*.

### Step 6 — Flip the plan to FINAL
Admin → Assignment plan → mark F1/F3/F4 final (after P3 loaded the real plan).
**Verify:** PROVISIONAL badges disappear from Overview and the dashboard banner;
coverage percentages now read against the real denominators.
**Undo:** mark provisional again (one click).

### Step 7 — Rotate accounts
Admin → Users: retire pretest `se-00x` (per D2), confirm the real roster is present and
correctly tiered. **Verify:** a retired login gets 401; a new login reaches the dashboard
but not the data room. **Undo:** recreate from the Step 1 htpasswd copy.

### Step 8 — Reset the monitoring memory
```
rm -f /opt/csweb-alert-state.json          # stops pretest alerts replaying
```
**Verify:** next sync-feed run logs `primed state`; the bell opens clean.
**Undo:** restore from Step 1.

### Step 9 — Switch the front doors (per D3)
Add 301s from the legacy csweb pages to their portal equivalents. **Never** touch
`/csweb/**`. **Verify:** `curl -I https://csweb.asiansocial.org/` returns 301 to the
portal; `/csweb/api/` still answers for tablets. **Undo:** remove the redirect block.

### Step 10 — Regenerate and confirm the public story
Run the six generators once by hand, then confirm on the live console:
`status.json` shows the new activity, day-one counts, correct provisional state; the
tabulations catalog still pins previews to the reference phase.

---

## 5. Post-cutover verification (the morning after)

- [ ] Cases arriving from real enumerators classify to the survey activity, not pretest
- [ ] Coverage percentages read against the final plan, no PROVISIONAL badges
- [ ] A field login can reach the dashboard and **not** the data room
- [ ] The silence alarm names real enumerators, and a test alert reaches Slack
- [ ] Exports carry `phase=survey` on new rows
- [ ] The pretest package opens and matches the archived counts
- [ ] Audit trail shows every change above, attributed

---

## 6. Full rollback

If the day goes wrong, in this order: restore `crontab.bak`; restore the config files from
Step 1; restore the database from `db-precutover.sql.gz`; re-run the six generators;
confirm the console matches the pre-cutover snapshot. Everything in §4 except Step 4
(after commit) is reversible without touching the database.

---

## 7. Traps — each of these has bitten this project

| # | Trap | Guard |
|---|---|---|
| T1 | `oauth_*` tables are **MyISAM** — no transaction, no rollback | Never include them in cleanup SQL |
| T2 | CSEntry's "Update Installed Applications" **misses CSWeb redeploys** | Verify the build footer on a real device, not the server |
| T3 | CSWeb bulk user import **creates only** — silently skips existing users | Check the resulting count, not the success message |
| T4 | CSEntry 8.0 **cannot sync** with CSWeb 8.1 | Never bump the server without the fleet |
| T5 | Deploying a generator **from `main`** wipes features (prod runs the worktree) | md5 prod against the worktree before every scp |
| T6 | F1/F3/F4 **won't compile in a worktree** (`psgc_*` gitignored) | Build from the MAIN checkout |
| T7 | htpasswd holds **both** `se_001` and `se-001` forms | Retire both spellings, or the gate keeps a live orphan |
| T8 | `.htpasswd` must be **`www-data:www-data 640`** | `root:root` locks everyone out; anonymous 401 looks identical to healthy |
| T9 | Gate lines are written with **two leading spaces** | `^Require` seds silently miss them |
| T10 | The tablet `SyncUrl` is baked into every `.pff` | Changing the sync host means rebuilding and redeploying every instrument |

---

## 8. Sign-off

| Decision | Choice | Date | By |
|---|---|---|---|
| D1 purge vs filter | | | |
| D2 accounts | | | |
| D3 front-door redirects | | | |
| Cutover executed | | | |
