# F2 Model C — Numbered HCW Links (short-link claim)

**Status:** **DEPLOYED to prod 2026-07-16** (backend + DDL + frontend, uhc-hcw.asiansocial.org)
— supersedes the facility-QR handout in `F2-Model-C-Self-Register-Design-2026-07-16.md`
as the *primary* distribution. **Owner:** Carl.
**Verified:** 81/81 server tests, 528/528 app tests, clean typecheck + lint; prod smoke
green (`/claim` + `/admin/api/facility-links` return 401 = live-and-gated; `f2_hcws`
carries `enroll_slug`/`enroll_secret_hmac`/`claimed_at`). Used for the 2026-07-16 pretest.
Deploy script: `pretest-2026-07-16/deploy_model_c_full.sh`.

> **Update 2026-07-16 — non-destructive generation (hardening).** The first pretest
> print "expired" because `/facility-links` rotated **every** secret on **every** call,
> so a second run silently invalidated all printed cards. There is no time-based
> expiry — "Invalid or expired link" is only ever a secret-HMAC mismatch. Fix: the
> endpoint is now **non-destructive by default** — it issues a secret only for slots
> that don't have one (already-issued slots return `already_issued:true`, no secret),
> and rotation is opt-in via **`rotate:true`** (guarded "Rotate all" toggle in the
> modal). Rotations write a distinct `admin_facility_links_rotate` audit event (the
> forensic trail that was missing). The 25 LPH-Bay cards were reissued once via
> `rotate:true` and reprinted. See "Endpoint contract" below.

## Decision

Distribute **one short, human-readable link per HCW**, pre-assigned to a fixed QN
slot. Opening the link auto-claims that slot — no token paste, no HCW-ID typing.

```
https://uhc-hcw.asiansocial.org/e/LPHBAY-HCW-19?k=a9f3kd
                                   └──── slug ────┘  └ secret
```

- **slug** = `<CODE>-HCW-<NN>` — `CODE` is an admin-chosen facility short-code
  (e.g. `LPHBAY`), `NN` a human sequence (01, 02, …). Maps 1:1 to a pre-provisioned
  `f2_hcws` slot (its QN, e.g. `040340210119`). The slug is a **label**, not the QN —
  the "19" need not equal the QN sequence (which floors at 101).
- **secret `k`** = 6 chars, Crockford base32 (no I/L/O/U). ~30 bits. Present as a
  query key so the readable path stays exactly `…/e/LPHBAY-HCW-19`.

This **replaces** the single facility-QR auto-assign as the main hand-out. The
facility-QR self-register path (`POST /self-register`) stays in place for walk-ins
but is not the default.

### Why a secret (not a bare `/…HCW-19`)

A bare slug is guessable (`…HCW-20`, `…HCW-21`), so a leaked pattern lets anyone
claim or submit for a slot that isn't theirs — junk data or "taking" a real HCW's
slot (a DoS on the enumeration). The 6-char `k` makes each link unguessable while
keeping the number visible. Threat model is bounded further by: anonymous survey
(no PII), in-person distribution, admin visibility + prune, and HMAC-keyed secret
storage (below) so a DB-only leak can't derive live secrets.

## Data model — `f2_hcws` (additive, idempotent)

```sql
ALTER TABLE f2_hcws
  ADD COLUMN enroll_slug        VARCHAR(96) NULL,
  ADD COLUMN enroll_secret_hmac VARCHAR(64) NULL,   -- HMAC-SHA256(secret, JWT key), hex
  ADD COLUMN claimed_at         DATETIME    NULL,
  ADD UNIQUE KEY uq_enroll_slug (enroll_slug);
```

Only the **HMAC** is stored — the plaintext secret is shown to the admin exactly
once (at generation) for printing, never persisted or re-displayed. Lose the sheet →
regenerate (new secret).

## Endpoints

### Admin — `POST /admin/api/facility-links` (gate `dash_users`)

Stamp slugs + secrets onto a facility's existing HCW slots. **Non-destructive by
default**: a slot that already has a secret is left untouched (its printed card
keeps working). `rotate:true` mints fresh secrets for **every** slot — invalidating
all previously printed cards — and is the only path that rotates.

```
req:  { facility_id: "040340210", short_code: "LPHBAY", rotate?: false }
resp: { facility_id, short_code, count, issued, skipped, rotated,
        links: [ { hcw_id, qn, slug: "LPHBAY-HCW-01",
                   secret: "a9f3kd" | null,     // fresh secret, shown ONCE (null if already_issued)
                   enroll_url: ".../e/LPHBAY-HCW-01?k=a9f3kd" | null,
                   already_issued: false }, … ] }
```

- Targets non-revoked, 12-digit-QN slots at `facility_id`, ordered by `qn` →
  assigns `HCW-01…HCW-NN`. Slugs are stable per slot across runs.
- **Default (no `rotate`):** issues a secret only for slots lacking one; already-issued
  slots come back `already_issued:true` with `secret:null`/`enroll_url:null`. Safe to
  re-run — cannot invalidate distributed cards. Audited `admin_facility_links_generate`.
- **`rotate:true`:** regenerates every slot's secret (reprint the whole set + redistribute).
  Audited as a distinct `admin_facility_links_rotate` event — the forensic record of
  when a facility's cards were invalidated.
- `short_code` validated `^[A-Z0-9]{2,12}$` (upper-cased).

### Public — `POST /claim`

```
req:  { slug: "LPHBAY-HCW-19", k: "a9f3kd" }
resp: { ok:true, token, hcw_id, qn, facility_id }   // token = device JWT (qn-bound)
```

Rules:
1. Look up slot by `enroll_slug`; unknown → `E_TOKEN_INVALID` 401 (no slug/secret
   distinction — don't leak which half was wrong).
2. Verify `k` via HMAC + `timingSafeEqual`; mismatch → `E_TOKEN_INVALID` 401.
3. Reject if `status ∈ {submitted, refusal, revoked}` → `E_CONFLICT` 409
   ("this link's survey is already completed"). Otherwise **re-openable**: the real
   HCW can reopen their link until they submit (mint is idempotent on the QN).
4. Mint a device JWT `{ jti, tablet_id: <uuid>, facility_id, qn, iat, exp }` — the
   same shape a reissued per-HCW token has, so enrollment/submit/refusal/sync are
   inherited unchanged. `tokenAudit` + stamp `claimed_at`.
5. `kill_switch` parity: HTTP 200 + `{ok:false, E_KILL_SWITCH}`.

`/claim` is added to `API_PATH_RE` so a miss is a JSON 404, never the SPA.

## Frontend — `/e/:slug`

The app is a pathname-switch (`/admin` → portal; else the HCW app; SPA fallback
already serves `index.html` for any path). Add: when unenrolled and the path is
`/e/<slug>`, a **ClaimScreen** auto-runs `POST /claim` (slug from path, `k` from
query) → on success enrolls device-bound to the returned token/qn → drops straight
into consent → survey. Failure shows a plain "ask ASPSI ops" message. No token box,
no HCW-ID picker.

**Personal-device assumption:** numbered links assume each HCW opens their own on
their own phone (one device → one QN). Shared-phone / walk-in stays on the facility-QR
self-register path (kept, no longer the default).

## Files (as built — 2026-07-16)

Code lives in the staging worktree `deliverables/F2/PWA/`. New = created, Edit = modified.

### Frontend — `app/`

| File | Change | Purpose |
|---|---|---|
| `src/lib/claim-client.ts` | New | `POST /claim` client + `parseClaimUrl()` for `/e/<slug>?k=` |
| `src/components/enrollment/ClaimScreen.tsx` | New | Auto-claims on mount → enrolls device-bound → consent/survey; Retry on failure |
| `src/components/enrollment/ClaimScreen.test.tsx` | New | 5 tests: URL parse, enroll-on-success, E_CONFLICT, offline+Retry, missing-secret |
| `src/App.tsx` | Edit | Routes `/e/:slug` to `ClaimScreen` when unenrolled (`claimTarget` guard) |
| `src/admin/data/FacilityLinksModal.tsx` | New | Admin generator: facility + short-code → link table (copy-row / copy-all TSV / print), once-only-secret warning, guarded "Rotate all" toggle + `already_issued` rows + issued/skipped summary |
| `src/admin/data/HCWsTab.tsx` | Edit | "Facility links" button (prefilled from facility filter) + modal wiring |
| `src/i18n/locales/en.ts` | Edit | `claim` block (heading/claiming/invalidLink/alreadyDone/offline/unavailable/retry) |
| `src/i18n/locales/{fil,bcl,bis,ceb,hil,ilo,war}.ts` | Edit | `claim` block, English-fallback (translations pending) |

### Backend — `server/`

| File | Change | Purpose |
|---|---|---|
| `ddl/f2_api_tables.sql` | Edit | Idempotent add of `enroll_slug` / `enroll_secret_hmac` / `claimed_at` + `uq_enroll_slug` to `f2_hcws` |
| `src/enroll-links.ts` | New | Slug/secret/HMAC helpers (Crockford base32, keyed HMAC, constant-time verify) |
| `src/admin/store.ts` | Edit | `HcwRecord` +slug/claimed_at; `FacilitySlot` +`enroll_slug`/`has_secret`; `listFacilitySlotsForLinks` (surfaces existing slug + has_secret) / `assignEnrollLink` / `getEnrollLinkBySlug` / `markClaimed` (InMemory + MySQL) |
| `src/app.ts` | Edit | `POST /claim` + `claim`/`self-register` added to `API_PATH_RE` |
| `src/admin/routes.ts` | Edit | `POST /admin/api/facility-links` (dash_users gate) — non-destructive default + `rotate:true` opt-in + `issued`/`skipped`/`rotated` + distinct rotate audit event |
| `test/claim.test.ts` | New | 9 tests for `/claim` |
| `test/admin.test.ts` | Edit | 6 tests for `facility-links` (generate→claim e2e, non-destructive re-run, rotate:true invalidation, validation, RBAC) |

## Rollout / timing

- **Status:** **DEPLOYED to prod 2026-07-16** — backend + DDL + frontend live at
  uhc-hcw.asiansocial.org; smoke green. 80/80 server tests, 528/528 app tests, clean
  `tsc -b` + eslint; production build clean (bundle-secrets/budget/contrast OK).
- **What shipped:** the whole app working tree (Model C + the QN plumbing it depends on
  — `qn` threaded enrollment→draft→submission→sync, an *optional* `db.ts` field so no
  forced device migration — plus tested `ReviewSection`/`MultiSectionForm`/`LanguageSwitcher`/
  `CreateHCWModal` changes that were already staged). Isolating Model C alone wasn't clean
  because the QN plumbing is entangled.
- **How:** `pretest-2026-07-16/deploy_model_c_full.sh` — backend (build→ship→rebuild f2-api)
  → idempotent DDL migration → frontend (build→`/opt/app/f2-www`, served live off the
  ro-mount, no restart). Enrolled devices keep their session; pick up the new build on next load.
