# F2 Admin — Facilities Page (facility + link management)

**Status:** **DEPLOYED to prod 2026-07-16** (uhc-hcw.asiansocial.org) — Operate →
Facilities live; composite endpoint smoke-verified with real data (LPH-Bay:
slug=lphbay, submitted=2 · refusals=1 · in_progress=1). **Owner:** Carl.
**Verified:** 101/101 server tests (+6), 571/571 app tests (+18 net), clean
`tsc -b --force` + eslint, production build checks OK; no DDL.
**Plan:** `F2-Facilities-Page-Plan-2026-07-16.md` (executed same day).
**Diagram:** `F2-Facilities-Page-Design-2026-07-16.excalidraw` / `.png` (approved canvas).
**Builds on:** `F2-Facility-Slug-Links-Design-2026-07-16.md` (DEPLOYED — one public
`/f/<slug>` link per facility; `f2_facility_slugs` + `POST /admin/api/facility-slugs`
upsert already live in prod).
**Fix 2026-07-17 (in_progress accuracy, api 0.1.1):** the `in_progress` definition below
assumed a successful submit moves the sr- row out of `enrolled` — but nothing did (only
the #825 refusal tag existed), so finished slug cases double-counted as both Submitted
and In progress. `handleSubmit` now forward-only tags the HCW `submitted` on every
non-refusal insert (mirror of `tagRefusal`, same guard), a DDL backfill closed the
pre-fix rows, and the `/claim` already-completed 409 gate now actually fires for
submitted numbered slots.

## Premise (decided with Carl, 2026-07-16)

Admins manage the per-facility links **grounded in the facility master list** instead
of hand-typing 9-digit IDs into a modal. Decisions locked:

1. **Links only — the facility master is READ-ONLY** in the portal. `f2_facility_master`
   stays a controlled sampling-frame artifact loaded outside the portal (no add/edit UI,
   no CSV import).
2. **New top-level "Facilities" page under Operate** (nav: Data · **Facilities** ·
   Reports · Encode), route `/admin/facilities`. Not a Data-dashboard tab, not the modal.
3. **Each row shows link status + live counts** — submitted · refusals · in-progress —
   so the page doubles as the rollout coverage board. **No target counts / completion %**
   (stays deferred).
4. **Slug is auto-suggested from the facility name, editable** before save.
5. **Approach A:** ONE new composite read endpoint feeds the page; all writes go through
   the **existing** `POST /admin/api/facility-slugs` upsert, unchanged.

## Backend — `GET /admin/api/facilities` (the only new endpoint)

Gate `dash_users` (same as all slug management). Paged response in the standard shape:

```
GET /admin/api/facilities?q=&region=&province=&facility_type=&has_link=&limit=&offset=

{ "rows": [ {
    "facility_id":   "040341130",
    "facility_name": "RHU Daraga I",
    "facility_type": "RHU",
    "region":        "Region V",
    "province":      "Albay",
    "city_mun":      "Daraga",
    "slug":          "rhu-daraga-i",   // '' when no link yet
    "active":        true,             // null when no link yet
    "url":           "https://…/f/rhu-daraga-i",  // '' when no link yet
    "submitted":     0,
    "refusals":      0,
    "in_progress":   0
  } ],
  "total": 128, "has_more": false }
```

- **Source of rows:** every `f2_facility_master` row (LEFT JOIN — facilities without
  links always appear). Sort: `region, province, facility_name` ASC. Filters: `q`
  (substring on name + id), exact `region` / `province` / `facility_type`, and
  `has_link` (`true` = slug exists, `false` = none, absent = all). Same
  `limit`/`offset` normalization as the other admin lists.
- **Count definitions (explicit):**
  - `submitted` = `f2_responses` rows at the facility with `status <> 'refusal'`.
  - `refusals`  = `f2_responses` rows with `status = 'refusal'`.
  - `in_progress` = `f2_hcws` rows with `facility_id = ?` AND `hcw_id LIKE 'sr-%'`
    AND `status = 'enrolled'` — slug self-registrations that started and never
    finished (the visible drop-off). **Numbered-link slots are deliberately
    excluded**: idle pre-provisioned `LPHBAY-HCW-NN` slots would inflate the number;
    a claimed-but-unfinished card going uncounted here is an accepted legacy edge.
- **Store:** new `AdminStore.listFacilitiesOverview(f): Promise<Paged<FacilityOverviewRow>>`.
  MySQL: one query — `f2_facility_master` LEFT JOIN `f2_facility_slugs` LEFT JOIN two
  per-facility aggregate subqueries. InMemory: merge `base.readFacilities()` with
  `facilitySlugs` + counted `base.responses` / `hcws` (test double parity).
- `url` composed server-side from `env.pwaOrigin` (same as the existing list endpoint).
- **No DDL.** Every table already exists.

## Frontend — the Facilities page

- **Nav + route:** `Facilities` item in `Layout.tsx` under Operate (icon consistent
  with the existing set); route `/admin/facilities` in the pages router. Page gated
  like its endpoint — a 403 renders the standard access-denied state.
- **Files:** new `app/src/admin/facilities/FacilitiesPage.tsx` +
  `FacilityLinkDialog.tsx` (+ tests). Follows the ResponsesTab conventions: filter
  state synced to URL params, no implicit default filters (#296), `adminFetch`,
  hairline table, mono microcopy.
- **Filter bar:** search box + Region / Province / Type selects + a "no link yet"
  toggle (`has_link=false`) for rollout sweeps. The page loads with `limit=500`
  (the master list is bounded — hundreds of rows, not thousands) and derives the
  select options from the full result set, so options never depend on the current
  filter/page. If the master ever outgrows one page, the options move server-side —
  out of scope now.
- **Table columns:** Facility (name + mono 9-digit id) · Link (`/f/<slug>` or
  "— no link yet") · Status chip (ACTIVE green / OFF dashed / — none) ·
  Submitted · Refusals · In progress · Actions.
- **Row actions:**
  - No link → **+ Create link** → dialog (below).
  - Has link → **QR** (opens the dialog in view mode: URL + `QRCodeSVG` + Copy +
    Print) · **Copy** · **Deactivate / Activate** (re-POSTs the row with `active`
    flipped, other fields unchanged).
- **Create-link dialog:** facility name + id shown read-only (from the row — never
  typed). Slug field pre-filled by `suggestSlug(facility_name)`, editable, validated
  against the shared grammar before Save. Save → existing
  `POST /admin/api/facility-slugs {slug, facility_id, facility_name, active:true}` →
  success shows URL + QR + Copy/Print, and the page reloads its list.
- **`suggestSlug(name)` (deterministic):** lowercase → replace every non-`[a-z0-9]`
  run with a single hyphen → trim leading/trailing hyphens → truncate to 31 chars
  (cutting back to the last hyphen boundary when truncation lands mid-word) →
  return `''` (admin types manually) if the result is shorter than 2 chars or equals
  the reserved `resolve`. Example: "RHU Daraga I" → `rhu-daraga-i`;
  "LPH-Bay District Hospital" → `lph-bay-district-hospital`.
- **Duplicate-slug guard (client-side):** the server upsert is keyed by slug, so
  saving an existing slug for a DIFFERENT facility would silently repoint it. The
  dialog blocks Save when the entered slug already appears in the loaded list under
  another facility_id, with the message "This link name already belongs to
  <facility>. Pick another." (Server behavior unchanged — admin-gated upsert stays
  the deliberate correction path; the page just makes stealing impossible by
  accident.) Re-saving the SAME facility's slug (rename of name text, reactivate)
  stays allowed.

## Rides along (same build)

1. **Responses tab — QN column.** `ResponseRow.qn` already reaches the client; show
   it as a mono column. The HCW cell renders `sr-…` ids as a muted
   `self-registered` label (full UUID stays visible in the Response detail view);
   named ids (e.g. `LPHBAY-HCW-01`) render as today. This gives slug-model rows
   (Shan's `sr-b9493…`) their meaningful identity: the 12-digit QN.
2. **HCWs tab cleanup.** The "Facility link" button + `FacilitySlugModal` move off
   the HCWs tab (superseded by this page; the dialog component is rebuilt as
   `FacilityLinkDialog` and the modal file + its tests are removed). The
   **"Numbered links (legacy)"** button stays exactly where it is.

## Error handling

- Composite endpoint: standard admin envelope (`E_VALIDATION` on bad params,
  `E_PERM_DENIED`, `E_BACKEND` + request id on SQL failure). Page renders the shared
  error banner with retry.
- Dialog Save reuses the existing upsert error mapping (`E_VALIDATION`,
  `E_PERM_DENIED`, `E_NETWORK`, `E_BACKEND`) plus the client-side duplicate guard.
- Counts are read-time aggregates — no caching layer, no staleness handling beyond
  the page's reload-on-mutation.

## Testing

- **Server:** `listFacilitiesOverview` (InMemory): facilities without links appear,
  slug/active/url join correctly, count definitions (seeded responses incl. refusal
  rows + sr-/non-sr hcws), `q`/`region`/`has_link` filters, paging shape. Route:
  RBAC 403 for non-`dash_users`, url composition, param normalization.
- **App:** FacilitiesPage — renders rows + chips + counts from a mocked fetch,
  filters update the query string, create dialog pre-fills `suggestSlug`, blocks
  duplicate slugs, Saves with the right body, toggle re-POSTs with `active` flipped;
  `suggestSlug` unit tests (truncation boundary, reserved name, degenerate input);
  ResponsesTab QN column + `self-registered` rendering; nav/a11y suites updated.
- Full suites green (server + app), clean `tsc -b --force` + eslint, production
  build clean — before deploy (standing autodeploy; **no DDL step needed**).

## Out of scope / non-goals

- Editing or importing `f2_facility_master` (stays external, read-only here).
- Per-facility target counts / completion % (deferred, again).
- A per-facility drill-down page (the Data tabs already filter by facility id).
- Touching the numbered-links legacy generator or any public PWA surface.
