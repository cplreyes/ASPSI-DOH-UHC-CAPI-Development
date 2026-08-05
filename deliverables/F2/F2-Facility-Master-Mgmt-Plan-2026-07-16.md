# F2 Admin — Facility Master Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. **Project override:** no git commit steps — Carl handles git manually.

**Goal:** Facility master CRUD (add/edit/archive) + batch CSV import with dry-run on the Facilities page, plus counts that deep-link into the Data tabs.

**Architecture:** One shared server-side validator (`facility-master.ts`) feeds three new admin routes (create / patch / import) over new AdminStore methods; `archived` is one additive column; the Facilities page gains two dialogs (edit, import) and linkified counts; the Responses tab learns a `status` URL param (HCWs tab already reads URL params — no change).

**Tech Stack:** Hono + mysql2 (server), React + TS (admin app), hand-rolled CSV parser (no new deps), Vitest.

**Spec:** `deliverables/F2/F2-Facility-Master-Mgmt-Spec-2026-07-16.md` (approved 2026-07-16: Option C, warn-but-allow geo, counts deep-links).

## Global Constraints

- `facility_id` immutable (`^\d{9}$`, unique); archive-only (no delete); import never archives.
- Geo checks WARN, never block: region vs the 18 canonical PSGC names (byte-identical to `deliverables/CSPro/data/psgc/psgc_region.csv`); province advisorily vs distinct existing master provinces.
- Field caps: name ≤255 (required), type ≤64, region/province/city_mun/barangay ≤128. Import ≤2000 rows/call.
- All routes `dash_users`; audits: `admin_facility_create` / `admin_facility_update` / `admin_facility_archive` / `admin_facility_unarchive` / `admin_facility_import`.
- Public `/f/<slug>` behaviour untouched; `readFacilities` (legacy PWA dropdown) excludes archived.
- DDL: exactly one guarded ALTER (`archived TINYINT(1) NOT NULL DEFAULT 0`). Deploy applies DDL BEFORE the backend rebuild (new SQL references the column).
- No git commits; `tsc -b --force` before push. Codebase: `deliverables/F2/PWA/{server,app}` (staging worktree).

## Canonical region list (verbatim, both sides)

```ts
export const PH_REGIONS = [
  'National Capital Region (NCR)',
  'Cordillera Administrative Region (CAR)',
  'Region I (Ilocos Region)',
  'Region II (Cagayan Valley)',
  'Region III (Central Luzon)',
  'Region IV-A (CALABARZON)',
  'MIMAROPA Region',
  'Region V (Bicol Region)',
  'Region VI (Western Visayas)',
  'Negros Island Region (NIR)',
  'Region VII (Central Visayas)',
  'Region VIII (Eastern Visayas)',
  'Region IX (Zamboanga Peninsula)',
  'Region X (Northern Mindanao)',
  'Region XI (Davao Region)',
  'Region XII (SOCCSKSARGEN)',
  'Region XIII (Caraga)',
  'Bangsamoro Autonomous Region In Muslim Mindanao (BARMM)',
] as const;
```

---

### Task 1: Server — shared validator (`facility-master.ts`)

**Files:** Create `server/src/facility-master.ts`; Test `server/test/facility-master-validate.test.ts`.

**Produces:** `PH_REGIONS`; `type FacilityMasterInput = { facility_id: string; facility_name: string; facility_type?: string; region?: string; province?: string; city_mun?: string; barangay?: string }`; `validateFacilityInput(input: FacilityMasterInput, knownProvinces: Set<string>): { errors: string[]; warnings: string[] }`.

Rules: id must match `^\d{9}$` (error); name required non-empty ≤255 (error); type ≤64, geo fields ≤128 (errors); region set but ∉ PH_REGIONS → warning `region "<x>" is not a canonical PSGC region name — dashboard by-name joins may miss`; province set but ∉ knownProvinces → warning `province "<x>" is new to the master — check spelling against CSWeb`. Tests: valid input → empty/empty; each error rule; each warning rule; empty geo fields produce no warnings.

- [ ] Write tests → run FAIL → implement → run PASS.

### Task 2: Server — store methods + DDL + archived plumbing

**Files:** Modify `server/src/store.ts` (FacilityRow `archived?: boolean`; InMemory `readFacilities` filters `!f.archived`; MySQL `readFacilities` adds `WHERE archived=0`), `server/src/admin/store.ts`, `server/ddl/f2_api_tables.sql` (guarded ALTER).

**Produces (AdminStore):**
```ts
type FacilityMasterRecord = FacilityRow & { archived: boolean };
createFacility(rec: FacilityMasterInput): Promise<'created' | 'conflict'>;
getFacility(id: string): Promise<FacilityMasterRecord | null>;
updateFacility(id: string, patch: Partial<FacilityMasterInput> & { archived?: boolean }): Promise<FacilityMasterRecord | null>;
```
`FacilityOverviewFilters` gains `include_archived?: boolean`; `FacilityOverviewRow` gains `archived: boolean`. Overview excludes archived rows unless `include_archived` (InMemory skip; MySQL `AND m.archived=0`). MySQL `updateFacility` builds a dynamic SET from present keys only (id never settable). InMemory create checks duplicates incl. archived rows → 'conflict'.

DDL (after the f2_facility_slugs block):
```sql
SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='f2_facility_master' AND COLUMN_NAME='archived');
SET @s := IF(@c=0, 'ALTER TABLE f2_facility_master ADD COLUMN archived TINYINT(1) NOT NULL DEFAULT 0', 'DO 0');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
```

- [ ] Implement (tests ride in Task 3's route suite + one overview-archived case added to `facilities-overview.test.ts`) → server typecheck clean.

### Task 3: Server — routes create / patch / import

**Files:** Modify `server/src/admin/routes.ts` (before catch-all); Test `server/test/facility-master.test.ts` (new, reuses admin.test.ts setup conventions).

**Contracts:**
- `POST /admin/api/facilities` body=FacilityMasterInput → 200 `{ ok:true, row: FacilityMasterRecord, warnings }` | 400 `E_VALIDATION` (first error) | 409 `E_CONFLICT` (`facility <id> already exists…` + `— unarchive it instead` when the existing row is archived). Audit `admin_facility_create`, resource=facility_id.
- `PATCH /admin/api/facilities/:id` body=partial (+`archived?: boolean`) → 200 `{ ok:true, row, warnings }` | 400 (`facility_id` present in body → `facility_id is immutable`; strict boolean archived) | 404 `E_NOT_FOUND`. Audit `admin_facility_update`, or `admin_facility_archive`/`admin_facility_unarchive` when `archived` flips.
- `POST /admin/api/facilities/import` body `{ mode:'dry_run'|'apply', rows: FacilityMasterInput[] }` (≤2000 else 400) → 200 `{ ok:true, mode, summary:{creates,updates,unchanged,errors,warnings}, verdicts:[{row,facility_id,action:'create'|'update'|'unchanged'|'error',changes?,warnings,errors}] }`. Per-row: validate → error rows never abort; existing row → field diff (only provided keys) → update/unchanged; archived existing → warning `row updates an archived facility`. `apply` executes create/update rows. Audit `admin_facility_import`, resource=`creates=<n> updates=<n> errors=<n>`.

Tests (~10): create ok+warnings; create conflict + archived-conflict message; patch edit + geo warning; patch id-immutable 400; patch archive→unarchive with distinct audits; patch 404; import dry-run mixed (create/update/unchanged/error rows, correct summary + changes); import apply persists and re-verdicts; import row-cap 400; overview include_archived + archived flag + readFacilities exclusion; RBAC 403 on all three.

- [ ] Tests FAIL → implement → full server suite green + typecheck.

### Task 4: App — Add/Edit/Archive on the Facilities page

**Files:** Create `app/src/admin/facilities/FacilityEditDialog.tsx`, `app/src/admin/facilities/ph-regions.ts` (client mirror of PH_REGIONS); Modify `FacilitiesPage.tsx`; Test `FacilityEditDialog.test.tsx` + FacilitiesPage.test.tsx additions.

Dialog (`mode:'create'|'edit'`): create shows editable 9-digit id; edit shows frozen mono id. Fields name/type/region/province/city_mun/barangay; region+province inputs use `<datalist>` (regions from `ph-regions.ts`; provinces passed in from loaded rows). Save → POST or PATCH; response `warnings` render as amber chips (`data-testid="edit-warnings"`) with the dialog staying open (Close reloads); no-warning success closes + reloads. Save disabled until id valid (create) + name non-empty.

Page: header **+ Add facility** button (`facilities-add`); row actions gain **Edit** (`facility-edit-<id>`) and **Archive/Unarchive** (`facility-archive-<id>`, `window.confirm` — archive copy notes the live-link caveat when `slug && active`); filter bar gains **Show archived** toggle (`facilities-archived`, URL param `archived=1` → API `include_archived=true`); archived rows render muted (`opacity-60`) with an `ARCHIVED` chip.

Tests: create dialog POSTs the typed fields; edit dialog PATCHes only changed fields with frozen id; warning chips render; archive confirm → PATCH `{archived:true}`; toggle adds include_archived to the fetch + URL; archived row shows chip.

- [ ] Tests FAIL → implement → facilities suite green.

### Task 5: App — CSV import dialog

**Files:** Create `app/src/admin/facilities/parse-csv.ts`, `FacilityImportDialog.tsx`; Test `parse-csv.test.ts`, `FacilityImportDialog.test.tsx`; Modify `FacilitiesPage.tsx` (**Import CSV** button `facilities-import`).

`parseFacilityCsv(text: string): { rows: FacilityMasterInput[]; error?: string }` — hand-rolled RFC-ish parser: quoted fields with `""` escapes, CRLF/LF, skips blank lines; requires exact header `facility_id,facility_name,facility_type,region,province,city_mun,barangay` (order-sensitive) else `error`. Tests: happy path; quoted commas + escaped quotes; CRLF; wrong header → error; empty file → error.

Dialog flow: paste area + file picker (FileReader → same textarea) → **Dry run** (`import-dry-run`) → POST mode:'dry_run' → verdict table (row / id / action / changes / warnings / errors; `import-verdicts`) + summary strip (`import-summary`) → **Apply** (`import-apply`, enabled only after a dry run whose parse hasn't changed) → POST mode:'apply' → final summary → Close reloads page. "Download template" link (`import-template`) generates the header-row CSV via a Blob URL.

Tests: paste → dry-run POST body correct; verdict table renders actions incl. error rows; Apply disabled before dry-run, enabled after, sends mode:'apply'; template link has a `download` attr.

- [ ] Tests FAIL → implement → suites green.

### Task 6: App — counts deep-links + Responses `status` param

**Files:** Modify `FacilitiesPage.tsx` (counts → `Link`s when >0), `app/src/admin/data/ResponsesTab.tsx` (status param); Tests in both suites.

Hrefs: Submitted `/admin/data?tab=responses&facility_id=<id>`; Refusals `…&status=refusal`; In progress `/admin/data?tab=hcws&facility_id=<id>&status=enrolled&q=sr-`. Zero counts stay plain text. (HCWs tab already reads `facility_id`/`status`/`q` from the URL — no change.)

ResponsesTab: `UiFilters` gains `status: string` (from `?status=`); `buildQuery` echoes it; `buildApiQuery`: `errors_only` keeps precedence (`status=rejected`), else `if (filters.status) p.set('status', filters.status)`.

Tests: FacilitiesPage — count anchors carry the exact hrefs, zero renders no link; ResponsesTab — `?status=refusal` reaches the API query and survives the tab's URL round-trip.

- [ ] Tests FAIL → implement → suites green.

### Task 7: Verify + deploy + close out

- [ ] Server: full suite + typecheck. App: full suite (`--max-workers=2`) + `tsc -b --force` + eslint + production build (checks green).
- [ ] Deploy: apply the DDL guarded ALTER on the box FIRST (standalone ssh + mysql step), then run `deploy_model_c_full.sh` (its DDL step re-applies idempotently).
- [ ] Smoke: POST/PATCH/import routes 401 unauthenticated; authenticated overview rows carry `archived:false`; legacy `/exec?action=facilities` unaffected.
- [ ] Update spec status → DEPLOYED; memory note.

## Self-Review

- **Spec coverage:** validator+regions (T1); archived column/readFacilities/overview (T2); three routes + audits + fault-tolerant import (T3); dialogs + archived UX (T4); CSV parse/import UI + template (T5); deep-links + status param (T6); DDL-first deploy (T7). HCWs-tab URL support verified pre-existing. ✔
- **Placeholders:** dialog/table internals specified by contract + testids with full code for parser/validator/contracts — executor is the plan author with the shipped conventions in context; no TBDs.
- **Type consistency:** `FacilityMasterInput`/`FacilityMasterRecord`/verdict shape used identically in T1–T5; `include_archived` name consistent T2/T4.
