# F2 Admin — Facility Master Management (CRUD + batch import + counts deep-links)

**Status:** **DEPLOYED to prod 2026-07-16** (uhc-hcw.asiansocial.org) — CRUD + import
routes live and gated (401 unauthenticated), `archived` column applied BEFORE the
backend rebuild, overview carries `archived:false` on all 4 seeded rows.
**Owner:** Carl.
**Verified:** 116/116 server tests (+15), 586/586 app tests (+28 net), clean
`tsc -b --force` + eslint, production build checks OK.
**Plan:** `F2-Facility-Master-Mgmt-Plan-2026-07-16.md` (executed same day).
**Diagram:** `F2-Facility-Master-Mgmt-Options-2026-07-16.png` (Option C chosen).
**Builds on:** `F2-Facilities-Page-Spec-2026-07-16.md` (DEPLOYED — the Facilities page
this extends). Supersedes that spec's "facility master is read-only" scope line.

## Premise (decided with Carl, 2026-07-16)

The master's 4 rows are the pretest set ported from the FacilityMasterList sheet at P4
(`csweb_f2_schema.sql` §f2_facility_master); rollout brings facility waves, so the
portal now manages the master itself. Decisions locked:

1. **Option C — both paths:** batch CSV import (dry-run → confirm) for waves, plus
   row-level add / edit / archive for one-off fixes. One shared validation core.
2. **Geo check: warn but allow.** Region/province names that don't match the known
   geo lists import with a visible warning instead of being rejected. (The unified
   dashboard joins areas BY NAME, so warnings must be loud — but the list must never
   block a wave.)
3. **Counts become deep-links** (the "linking Facilities and Data" feature): clicking
   a facility row's Submitted / Refusals / In-progress count opens the matching Data
   tab pre-filtered to that facility.

## Guardrails (every path)

- **`facility_id` is immutable** once created — QNs embed it, cases reference it.
  Create validates `^\d{9}$` and uniqueness; edit never touches it.
- **No hard delete — archive only.** `archived` facilities disappear from the default
  Facilities view (a "Show archived" toggle reveals them) and from the PWA's legacy
  facilities dropdown, but all their data, links, and counts stay intact. Archiving a
  facility with an ACTIVE slug shows a confirm noting the public link stays live until
  deactivated on its row.
- **Geo warnings:** region checked against the canonical PSGC region-name list
  (shipped constant, byte-identical to CSWeb's `region_name` values); province checked
  advisorily against the distinct provinces already in the master. Mismatch = warning
  chip on the row/preview, never a block.
- **Audit everything:** `admin_facility_create` / `admin_facility_update` /
  `admin_facility_archive` (+`_unarchive`) / `admin_facility_import` (with
  created/updated counts in the resource string) — same success-gated trail as the
  link actions.

## Data model (additive, idempotent DDL)

```sql
-- f2_facility_master gains one flag (guarded ALTER, same pattern as f2_hcws adds):
ALTER TABLE f2_facility_master ADD COLUMN archived TINYINT(1) NOT NULL DEFAULT 0;
```

No other schema change. Who/when history lives in `f2_audit`, not on the row.

## Backend

All gated `dash_users`, standard envelope + `auditMutation`.

### `POST /admin/api/facilities` — create
Body `{ facility_id, facility_name, facility_type?, region?, province?, city_mun?, barangay? }`.
Validation: id `^\d{9}$` + not already present (409 `E_CONFLICT`); name required ≤255;
type ≤64; geo fields ≤128. Response `{ ok:true, row, warnings: string[] }` (geo
warnings surface here). Archived rows count as "present" — creating over an archived
id is a 409 pointing at unarchive.

### `PATCH /admin/api/facilities/:id` — edit / archive / unarchive
Body: any of `{ facility_name, facility_type, region, province, city_mun, barangay,
archived }`. `facility_id` in the body is rejected (400). Unknown id → 404. Response
`{ ok:true, row, warnings }`. `archived:true|false` flips the flag (distinct audit
events).

### `POST /admin/api/facilities/import` — batch upsert with dry-run
Body `{ mode: 'dry_run' | 'apply', rows: Array<{ facility_id, facility_name,
facility_type?, region?, province?, city_mun?, barangay? }> }` (CSV is parsed
client-side; the server sees JSON rows — max 2000 per call).
Per-row verdict: `{ row: n, facility_id, action: 'create' | 'update' | 'unchanged'
| 'error', changes?: string[], warnings: string[], errors: string[] }` plus a summary
`{ creates, updates, unchanged, errors, warnings }`. `apply` executes creates +
updates for valid rows only (row errors never abort the batch — they're reported);
`unchanged` rows are skipped. Import never archives — removal from a wave file does
NOT archive a facility (explicit row action only). `archived` facilities in the file
are updated in place and reported with a warning ("row updates an archived facility").

### Store (`AdminStore`, InMemory + MySQL)
```ts
type FacilityMasterRecord = FacilityRow & { archived: boolean };
createFacility(rec: FacilityMasterInput): Promise<'created' | 'conflict'>;
updateFacility(id: string, patch: Partial<FacilityMasterInput> & { archived?: boolean }): Promise<FacilityMasterRecord | null>;
getFacility(id: string): Promise<FacilityMasterRecord | null>;
```
The composite
`listFacilitiesOverview` gains `include_archived?: boolean` (default false) and each
row gains `archived`. The PWA's `readFacilities` (legacy dropdown) adds
`WHERE archived=0` — public behaviour of `/f/<slug>` is untouched (slug `active` is
the only public gate). Shared validation lives in `server/src/facility-master.ts`
(id/name/geo rules + the canonical region list) — the create, patch, and import
routes all call the same `validateFacilityInput()`.

## Frontend (Facilities page extensions)

- **"+ Add facility"** button (header, next to the filters) → dialog with the shared
  validation; geo fields as **datalist autocompletes** fed by the canonical region
  list / existing provinces (free text allowed — warnings, not blocks). Save → create
  endpoint → list reloads; warnings render as amber chips in the dialog.
- **Row "Edit"** action → same dialog pre-filled, id shown frozen (read-only, mono);
  Save → PATCH. **"Archive"** action (confirm dialog; notes live-link caveat when the
  slug is active) / **"Unarchive"** on archived rows.
- **"Show archived"** toggle in the filter bar (default off); archived rows render
  muted with an `ARCHIVED` chip.
- **"Import CSV"** button → import dialog: file picker (or paste area) → client-side
  CSV parse (shared 7-column header `facility_id,facility_name,facility_type,region,
  province,city_mun,barangay`; quoted fields supported; a small hand-rolled parser —
  no new dependency) → **dry-run table** (per-row action + warnings/errors, summary
  strip) → **Apply** button (disabled until dry-run runs; re-runs as `apply`) →
  result summary + list reload. A "download template CSV" link writes the header row.
- **Counts deep-links:**
  - **Submitted** → `/admin/data?tab=responses&facility_id=<id>`
  - **Refusals** → `/admin/data?tab=responses&facility_id=<id>&status=refusal`
  - **In progress** → `/admin/data?tab=hcws&facility_id=<id>&status=enrolled&q=sr-`
  Counts render as links only when > 0 (a zero count stays plain text).

## Data-tab support for the deep-links

- **Responses tab:** URL param `status` (e.g. `refusal`) joins the existing filter
  set — read from URL, passed to the API (which already supports it), preserved in
  the tab's own URL building. The `errors_only` chip keeps precedence if both appear.
- **HCWs tab:** reads `facility_id`, `status`, and `q` from URL params on mount
  (today its filters start empty) so the In-progress link lands pre-filtered.

## Error handling

- Standard admin envelope everywhere; create 409s name the conflicting facility.
- Import is per-row fault-tolerant: a bad row reports `action:'error'` and the rest
  proceed; the apply response repeats the final per-row verdicts so the admin sees
  exactly what landed.
- Client CSV parse failures (wrong header, empty file) surface in the dialog before
  any network call.

## Testing

- **Server:** shared validator (id/name/geo warn rules); create (created/conflict/
  archived-conflict); patch (edit fields, id-immutable 400, archive/unarchive,
  unknown 404); import dry-run vs apply (create/update/unchanged/error rows, warnings,
  fault tolerance, 2000-row cap); overview `include_archived` + `archived` flag;
  `readFacilities` excludes archived; audit events per mutation; RBAC on all three
  routes.
- **App:** add/edit/archive dialogs (validation, frozen id, warning chips, confirm
  flows); import dialog (parse, dry-run table, apply, template download); archived
  toggle + muted rows; counts render as links with the exact hrefs above (and plain
  text at zero); Responses tab honors `status` param; HCWs tab honors URL params;
  suggest/link flows from the existing page unchanged.
- Full suites green, tsc/lint/build clean; deploy includes the one-column DDL
  (idempotent guarded ALTER via the standard script).

## Out of scope / non-goals

- Hard delete of facilities (never).
- Editing `facility_id` (never — archive + recreate is the correction path).
- Auto-archiving from import files.
- Per-facility target counts / completion % (still deferred).
- Syncing the master back out to CSWeb/CSPro (one-way: portal manages csweb_f2 only).
