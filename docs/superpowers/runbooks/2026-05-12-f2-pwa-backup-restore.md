# Runbook — F2 PWA backup + restore

**Created:** 2026-05-12
**Closes:** #173 (E4-PWA-011 — backup + restore runbook for FacilityMasterList + submissions sheets)
**Owner:** Carl (hands-on Google account access — can't be delegated unless ops team has equivalent permissions on `aspsi.doh.uhc.survey2.data@gmail.com`)
**Cadence:** Weekly Friday + before any major migration or destructive admin action

---

## Context

The F2 backend lives in three storage layers:

1. **Google Sheet** (`F2-PWA-Backend` spreadsheet on the project Gmail account) — primary durable store. 9 sheets: `F2_Responses`, `F2_Audit`, `F2_Users`, `F2_Roles`, `F2_HCWs`, `F2_FileMeta`, `F2_DataSettings`, `FacilityMasterList`, plus the original Google Forms intake sheet (legacy, retained as historical reference).
2. **Cloudflare R2** — file uploads (training plans, rosters) + scheduled break-out CSV exports. Buckets: `f2-admin` (prod), `f2-admin-staging`. Object lifecycle: keep indefinitely (no TTL) until manual cleanup.
3. **Cloudflare KV** (`F2_AUTH` namespace) — JWT revocation list. Ephemeral; reconstructible from `F2_HCWs.token_revoked_at` if lost.

Risk profile:

| Layer | Loss = | Recovery without backup |
|---|---|---|
| Sheet | All survey responses + audit + admin state | None — submission data is irrecoverable |
| R2 | Operator-uploaded files + historical CSV exports | Files: irrecoverable. CSVs: re-runnable from sheet |
| KV | Revocation list | Reconstruct from F2_HCWs in ~5 min |

**Sheet is the only single-point-of-failure that can't be reconstructed from another layer.** This runbook prioritizes it.

---

## Backup procedure

### 1. Sheet snapshot (weekly Friday)

Google Sheets keeps revision history forever, but a snapshot copy gives a clean restore target if the live sheet becomes corrupted by a bad migration or accidental deletion.

```
File → Make a copy
Name: "F2-PWA-Backend — snapshot YYYY-MM-DD"
Folder: "Drive / ASPSI-DOH / F2 backups/"
```

Notes:
- Copy includes all sheets, including the legacy Google Forms intake sheet.
- Apps Script projects bound to the original sheet are NOT copied; the snapshot is a data copy only.
- Add a note in the copy's first cell: `SNAPSHOT — DO NOT EDIT. Source: F2-PWA-Backend, taken YYYY-MM-DD HH:MM PHT by <name>.`

### 2. Apps Script source export (monthly)

Apps Script auto-saves every keystroke and keeps version history, but a tarball offline gives an off-platform copy.

```
clasp pull --rootDir ./backups/apps-script-YYYY-MM-DD
```

Or manually: open the AS editor → File → Download `.js` files individually. Slower but no clasp install needed.

### 3. R2 bucket sync (weekly Friday)

Pull all R2 objects to a local backup folder via wrangler:

```
wrangler r2 object get --recursive f2-admin --output-dir ./backups/r2/YYYY-MM-DD/
```

Sizes: typically <100 MB if file uploads are kept lean per the 100 MB-per-file ceiling.

### 4. KV snapshot (optional — reconstructible)

Skip unless you've recently mass-revoked tokens and want a point-in-time record:

```
wrangler kv:bulk get F2_AUTH --output ./backups/kv/F2_AUTH-YYYY-MM-DD.json
```

---

## Restore procedure

### Sheet — full restore from snapshot

1. **Stop writes.** Apps Script editor → click the active deployment → Pause cron triggers (or set `OPS_DISABLE_WRITES=true` script property if implemented).
2. Open the snapshot copy. Verify it's the right vintage (check the first-cell note).
3. **Decide:** rename-and-replace OR per-sheet copy.
   - **Rename-and-replace** (cleaner if all sheets are corrupted): rename `F2-PWA-Backend` to `F2-PWA-Backend — corrupt YYYY-MM-DD`, rename the snapshot to `F2-PWA-Backend`. Update Apps Script project to bind to the new sheet (Project Settings → Script Properties → SHEET_ID).
   - **Per-sheet copy** (cleaner if only one sheet is corrupted): copy the affected sheet from the snapshot into the live spreadsheet (Tab → Copy to → existing spreadsheet → F2-PWA-Backend). Delete the corrupted tab.
4. **Re-enable writes.** Resume cron triggers.
5. **Smoke-verify:** open Admin Portal → Data → Responses; confirm the table renders. Run a test enrollment from `/admin/users` → `Add user`.

### R2 — restore individual file

1. Find the affected `file_id` from the `F2_FileMeta` sheet.
2. Locate the corresponding object in `./backups/r2/<date>/`.
3. Push back: `wrangler r2 object put f2-admin/<file_id> --file <local-path> --content-type <mime>`.
4. Verify via Admin Portal → Apps & Settings → Files → click row → Download.

### KV — full revocation-list rebuild

```javascript
// Run from AS editor or local Node script with Cloudflare API token:
// 1. Read F2_HCWs sheet, filter where token_revoked_at IS NOT NULL
// 2. For each, KV.put(F2_AUTH, `revoked:${enrollment_token_jti}`, '1')
```

---

## Verification (post-restore)

Run all of these before declaring restore complete:

- [ ] Admin Portal `/admin/login` loads and authenticates.
- [ ] `/admin/data?tab=responses` shows non-empty table for the expected period.
- [ ] `/admin/data?tab=audit` shows audit rows for the period.
- [ ] `/admin/apps?tab=files` shows the expected file list.
- [ ] HCW enrollment flow: open a known `DEMO-HCW-*` enrollment URL → token validates → form loads.
- [ ] Submit a test response → check it appears in `F2_Responses` within 60 seconds.

---

## Schedule

| Backup | Cadence | Owner | Where |
|---|---|---|---|
| Sheet snapshot | Weekly Fri 17:00 PHT | Carl (or ops trainee) | Drive / ASPSI-DOH / F2 backups/ |
| Apps Script source | Monthly first Friday | Carl | local repo `./backups/apps-script-*` (gitignored) |
| R2 bucket sync | Weekly Fri 17:00 PHT | Carl | local repo `./backups/r2/*` (gitignored) |
| KV snapshot | On-demand only | Carl | local repo `./backups/kv/*` (gitignored) |

Pre-fieldwork (when production HCW enrollments begin), upgrade the Sheet cadence to **daily 23:00 PHT** via Apps Script time-driven trigger writing a snapshot copy programmatically. Issue to file when fieldwork start date is set.

---

## Restore drill (annual)

Once a year, exercise the restore on staging:

1. Take a snapshot of the staging sheet.
2. Make a destructive edit on staging (delete a row, drop a column).
3. Restore from snapshot per the procedure above.
4. Confirm verification checklist passes.
5. Document drill date in this file's footer.

**Drills run:** _(none yet — first scheduled 2027-05-12)_
