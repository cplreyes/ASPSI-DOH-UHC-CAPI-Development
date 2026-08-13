# F2 — Facility Slug Links (per-facility self-register)

**Status:** **DEPLOYED to prod 2026-07-16** (uhc-hcw.asiansocial.org) — slug `lphbay`
live (`/f/lphbay` → 040340210 LPH-Bay District Hospital), announced to #f2-pwa-uat.
**Owner:** Carl.
**Verified:** 95/95 server tests (+14 new), 558/558 app tests (+30 new), clean
`tsc -b --force` + eslint, production build clean (bundle-secrets/budget/contrast OK);
prod smoke green (resolve 200 / unknown-slug 404 / `/f/lphbay` serves SPA / legacy
paths intact). Plan: `F2-Facility-Slug-Links-Plan-2026-07-16.md`.
**Adversarial review (pre-deploy) → 4 hardening fixes shipped with it:**
`enroll()` now resets per-case local state (stale thank-you + cross-respondent
draft/consent bleed on shared phones); "Start new survey" on a `/f/` device
unenrolls back to the FacilityStartScreen (fresh QN per respondent — never two
people under one case key); post-submit immediate sync is skipped while offline
(row stays `pending_sync` so the reconnect trigger sends instantly); a queued
batch hitting E_KILL_SWITCH now schedules a retry instead of terminal rejection.
Plus: transient resolve errors say "try again" (only a real 404 says inactive),
strict boolean `active` on the admin upsert, 160-char name cap mirrored client-side.
**Supersedes as PRIMARY distribution:** `F2-Model-C-Numbered-Links-Design-2026-07-16.md`
(per-HCW numbered cards) and `F2-Model-C-Self-Register-Design-2026-07-16.md` (facility-JWT
QR). Both remain in the codebase — the numbered-link `/claim` path stays alive so the 25
already-distributed LPH-Bay cards keep resolving (see Migration).

## Premise (decided with Carl, 2026-07-16)

Field ops distributes **one clean, readable link per facility** — not 25 cards per facility
(Model C), and not one global link (which throws away facility attribution). Example:

```
uhc-hcw.asiansocial.org/f/lphbay
                        └┬┘ └─┬─┘
                    namespace  facility slug → resolves to facility_id 040340210
```

Any HCW at that facility opens it on their own phone, self-registers, answers, submits.
Decisions locked:
- **Facility slug in the URL** (readable, e.g. `lphbay`), namespaced under **`/f/`** so it
  can't collide with `/admin`, `/e/`, `/api/`, `/claim`, `/enroll`.
- **Bare slug, no secret** — fully open. Junk/duplicate risk is handled admin-side
  (dedup/prune of `sr-` cases) + kill switch, and by only self-registering on an explicit
  **Start** tap (below).
- **Facility from the slug** → the 12-digit facility-encoded QN, Map Report, and
  HCW-by-facility monitoring all keep working with **no rework**.

## The model (flow)

```
open /f/lphbay ──► StartScreen: "Bicol… LPH-Bay HCW Survey — [Start]"   (GET resolve, read-only)
      │
   tap Start ──► POST /self-register {slug}  →  server: slug→facility_id
      │                                          → createHcw(sr-…, facility, qn='')  → assigns next QN in block
      │                                          → mint qn-bound device token (same shape as /claim)
      │                                          → { token, hcw_id, qn, facility_id, facility_name }
      ▼
   enroll (Dexie) ──► consent ──► survey ──► Submit ──► /exec?action=submit (token) ──► sync
```

Consent / draft-save / offline / submit / refusal (#825) / sync are **inherited unchanged**
from the existing enrollment engine — the only new thing is how a case is *started*.

**Why self-register on the Start tap (not on page load):** a bare public slug will get
casual/bot opens. A page load does nothing; only an explicit **Start** POSTs `/self-register`.
That filters accidental/bot traffic without touching the submit path. Residual
abandoned-after-Start cases show as `enrolled`-not-`submitted` (visible drop-off, prune-able).
*(Optional future hardening: defer QN assignment to submit. Not needed for launch.)*

## Sync-on-submit (delivery guarantee)

The self-register device is **one-and-done**: the HCW submits and closes the phone — nobody
runs a manual sync. So the submission has to reach the server on its own.

- **Already in place:** a successful Submit fires an **immediate sync** (`App.tsx` calls
  `runSync()` right after `submitDraft`), on top of the periodic timer + on-reconnect triggers
  (`sync-triggers.ts`). Online, the response lands on the server within ~a second.
- **Hardening for one-and-done (new, small):** gate the thank-you on **delivery** — show
  **"Submitting…"** until the server acknowledges, then **"Submitted ✓ — you can close this."**
  If offline at submit, show **"Saved — it will send automatically when you're back online"**
  (the Dexie queue + on-reconnect trigger deliver it). This closes the only stranding risk: a
  fire-and-forget push interrupted by the tab closing before it completes, on a device that
  never reopens.
- The response is **durably queued in IndexedDB the instant Submit succeeds**, so even a killed
  push is retried on next open/reconnect — the gate just makes "did it actually send?" visible
  to a user who won't come back.

## URL & routing

- **`/f/<slug>`** is an SPA route. The server's existing SPA fallback serves `index.html` for
  any non-API GET, so `/f/lphbay` loads the app; the PWA reads `location.pathname`, extracts
  the slug, and shows the StartScreen. `/f/` is **not** added to `API_PATH_RE` (it must fall
  through to the SPA, like `/e/…` does today).
- Slug grammar: `^[a-z0-9][a-z0-9-]{1,30}$` (lowercase; hyphens allowed). Normalized lower-case.

## Backend

### Slug store — new `f2_facility_slugs`
| col | type | notes |
|---|---|---|
| `slug` | VARCHAR(32) PK | lowercase, unique |
| `facility_id` | CHAR(9) | 9-digit PSGC facility code |
| `facility_name` | VARCHAR(160) | shown on StartScreen + written to the case |
| `active` | TINYINT(1) | soft on/off without deleting |
| `created_at` / `created_by` | | audit |

DDL is additive + idempotent (same guarded-ALTER pattern as `f2_api_tables.sql`).

### `GET /f/resolve?slug=<slug>` (public, read-only)
Resolves an active slug → `{ facility_id, facility_name }` for the StartScreen confirmation.
Unknown/inactive slug → 404 `E_NOT_FOUND` ("This survey link isn't active — check with ASPSI ops").
Creates nothing.

### `POST /self-register` (public) — extended to accept a slug
Today it requires a facility JWT (`SELF_REGISTER_TABLET_ID`). Extend it to also accept
`{ slug }`:
1. If `slug` present → look it up in `f2_facility_slugs` (active) → `facility_id` + `facility_name`.
   (Falls back to the existing facility-JWT path if a token is presented instead.)
2. kill_switch parity (200 + error envelope), as today.
3. `createHcw({ hcw_id:'sr-'+uuid, facility_id, facility_name, status:'enrolled', qn:'' })`
   → server assigns the next 12-digit QN in that facility's block (existing assigner).
4. **Mint a qn-bound device token** — same `JwtClaims` shape `/claim` mints (`tablet_id`=random
   uuid, `facility_id`, `qn`, exp) + `tokenAudit`. *(This is the one addition vs today's
   `/self-register`, which returns a QN but no per-device token.)*
5. Return `{ ok:true, token, hcw_id, qn, facility_id, facility_name }`.
6. Audit `admin_self_register_slug` (facility_id + slug) for the forensic trail.

Unknown/inactive slug → 401/404 with a neutral message. No secret to leak (bare slug).

## Admin (F2 Admin portal)

- **Repurpose the "Facility links" surface** (currently `FacilityLinksModal` → per-HCW numbered
  links) into **"Facility link"** (singular per facility): pick/enter a facility (id + name),
  set a slug → upserts `f2_facility_slugs` → shows the `**/f/<slug>**` URL + a **QR** + copy/print.
  Manage: list existing slugs, toggle `active`, change slug.
- **Monitoring is unchanged in shape** — `sr-` cases carry a real `facility_id`/`facility_name`,
  so **Data → HCWs** filtered by facility, the **Responses** view, and the **Map Report** all
  work as-is. Completion = count of `submitted`/`refusal` per facility; optional per-facility
  **target count** if you want a % (nice-to-have, can defer).
- **Per-HCW numbered-link generation is retired from the primary flow.** The `/facility-links`
  endpoint + its non-destructive/rotate logic stay in the codebase (dormant) so LPH-Bay reprints
  still work during migration; the button can be moved behind an "advanced/legacy" affordance.

## PWA (F2 app)

- **New `FacilityStartScreen`** for `/f/<slug>` when unenrolled: calls `GET /f/resolve`, shows
  "*<Facility name>* — HCW Survey" + a **Start** button + a one-line "answers are voluntary and
  anonymous" note. Start → `POST /self-register {slug}` → enroll with the returned token/qn →
  consent → survey.
- **`App.tsx` routing** (order): `/e/<slug>` claim URL → `ClaimScreen` (legacy cards);
  `/f/<slug>` → `FacilityStartScreen`; otherwise unenrolled with no slug → a short "open your
  facility's survey link" message (the token `EnrollmentScreen` can stay behind a legacy path
  for any enumerator-assisted use).
- **`ClaimScreen` stays** for the 25 distributed `/e/LPHBAY-HCW-NN?k=` cards.
- i18n: one new `facilityStart` block (heading/start/resolving/inactive) across the 8 locales
  (English fallback for the 7 non-en, per existing convention).

## QN & attribution

- **QN stays 12-digit, facility-encoded** — assigned in the slug's facility block by the existing
  assigner. No reporting/CSWeb rework. This is the whole reason per-facility beats the global link.
- Facility as an in-survey question is **now optional** (attribution already comes from the slug),
  so the instrument can stay as-is or drop a redundant facility item.

## Integrity (fully open, per decision)

- No credential in the URL. Controls = **Start-tap self-register** (filters casual/bot opens),
  **admin dedup/prune** of `sr-` cases, **kill switch**, and device-singleton enrollment (one
  active case per device). If junk ever appears, a per-facility `?k=` secret is a drop-in later
  (the HMAC machinery already exists from the numbered links) — not built now.

## Migration (cut over now)

1. Ship backend (slug store + `/f/resolve` + `/self-register` slug path) + admin + PWA.
2. Create slug `lphbay` → `040340210` (name "LPH-Bay District Hospital"). Announce
   **`uhc-hcw.asiansocial.org/f/lphbay`** to the field (Slack + Viber), replacing the numbered cards.
3. **Keep `/claim` + `ClaimScreen` alive** — the 25 distributed numbered cards still resolve as a
   fallback; both paths write valid submissions at facility `040340210`.
4. New facilities get a slug each; no per-HCW card generation going forward.

## Reuse map (what's new vs existing)

| Piece | Status |
|---|---|
| Case creation + QN-in-facility-block assigner (`createHcw` qn='') | **exists** (`/self-register`) |
| qn-bound device-token mint + tokenAudit | **exists** (`/claim`) — reused in the slug path |
| SPA fallback for `/f/…` deep links | **exists** (`serveStatic` index.html) |
| Consent / draft / offline / submit / refusal / sync | **exists** — inherited |
| Facility-scoped monitoring, Map Report, Responses view | **exists** — works because `facility_id` is set |
| `f2_facility_slugs` table + `GET /f/resolve` + `/self-register` slug branch | **new** (small) |
| `FacilityStartScreen` + `/f/` routing + `facilityStart` i18n | **new** (small) |
| "Facility link" admin surface (repurpose `FacilityLinksModal`) | **modify** |

## Out of scope / non-goals

- Per-HCW identity, rosters, pre-provisioned slots — gone in this model (self-register only).
- Per-facility secrets, PINs, CAPTCHA — deliberately omitted (fully open); drop-in later if needed.
- Ripping out the numbered-link/`/claim` code — kept dormant for the LPH-Bay fallback.

## Testing

- **Server:** `f2_facility_slugs` store (InMemory + MySQL); `/f/resolve` (hit/miss/inactive);
  `/self-register {slug}` (creates `sr-` case at the right facility, assigns a facility QN, mints a
  working token, kill-switch envelope, unknown-slug 404); the legacy facility-JWT path still works.
- **App:** `FacilityStartScreen` (resolves + starts + error states); `App.tsx` routing precedence
  (`/e/…` vs `/f/…` vs default); enroll→submit e2e on a slug-started case.
- **App — sync-on-submit:** online submit reaches the server before the thank-you resolves and
  the thank-you gates on the server ack; offline submit shows the "saved, will send" state and
  delivers on the next `online` event.
- Full suites green (server + app), clean tsc + lint, before deploy.

## Open items (none blocking)

- Per-facility **target counts** for a completion % — include now or defer? (Recommend defer.)
- Whether to drop the now-redundant in-survey facility question from the instrument.
