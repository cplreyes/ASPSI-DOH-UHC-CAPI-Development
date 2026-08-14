# CAPI Console Unification — Design

**Date:** 2026-08-09
**Status:** approved in outline, pending spec review
**Options diagram:** `deliverables/CSWeb/capi-console-unification-options.excalidraw` (+ `.png`)
**Supersedes nothing.** Extends the portal sitemap decision of 2026-07-22 (project-first IA) and the console cutover of 2026-07-28.

---

## 1. Problem

`capi.asiansocial.org` presents itself as one console. It is five hand-maintained
page-chromes across two URL spaces, plus two apps on other origins.

| # | Chrome | Renders | Imports the shared shell? |
|---|---|---|---|
| 1 | `portal_shell.py` | `dashboard.html`, `map.html`, `tabulations/` | yes — this is the good one |
| 2 | `build_portal.py` lines ~692–790 | every static portal page | **no — hand-cloned twin** |
| 3 | `csweb-responses-gen.py:306` | `/docs/data/index.html` (238 KB) | **no — bespoke** |
| 4 | `deliverables/CSWeb/admin/index.php` | the admin portal | **no — hand-written PHP** |
| 5 | ported pages | guides, manual, crosswalks | no — original CSS + injected bar |

Two consequences are already visible in production, not predicted:

**The stylesheets have diverged.** Verified on the box 2026-08-09:

```
214743592c1a71004f94757df2a9f126  /opt/portal.css                 # console pages
eae28977a4d7d172567ad8fc855ab758  /opt/app/capi-www/portal.css    # portal pages
```

The portal's copy is 13 lines short — it lacks the `@media (max-width: 560px)`
block that lets the topbar wrap. On a phone the Sync Dashboard behaves and every
`/projects/uhc-y2/…` page scrolls sideways. One bug, caused solely by there being
two files.

**Two pages exist only to point at other pages.** `/projects/uhc-y2/monitoring/`
(8.4 KB) and `/projects/uhc-y2/data/` (7.4 KB) are static signposts, built
2026-07-28 and unchanged since. They describe the dashboard, the map and the data
room, and link out to `/docs/*`. Every operational task costs an extra click.

Meanwhile `csweb-tabulations-gen.py:73` already writes a live, database-backed
page straight into `/opt/app/capi-www/projects/uhc-y2/tabulations/index.html`
using the shared shell — and needs no signpost, because the nav entry *is* the
page. The pattern is proven; two surfaces never got it.

---

## 2. Decisions taken

| Fork | Decision |
|---|---|
| Information architecture | **Option A — the portal absorbs the console.** `/projects/uhc-y2/…` becomes the single URL space; `/docs/*` becomes 301s. |
| CSWeb | **Nav entry + new tab.** Vendor software with its own user table; it is not reskinned or proxied. |
| Scope of "fix the UI/UX" | **Unify the chrome and fix the defects found.** No redesign of dashboard/map/data-room layouts — that would be a separate spec. |

---

## 3. Architecture

### 3.1 One shell module

`deliverables/CSWeb/portal_shell.py` becomes the sole markup source, paired with
`deliverables/CSWeb/portal.css` (already the newer of the two stylesheets, and
already what `/opt/portal.css` holds — so this direction loses nothing).

- `capi-portal/portal_shell.py` and `capi-portal/portal.css` are **deleted**.
- `capi-portal/build_portal.py` imports the root module via a `sys.path` insert
  and loses its local `_ico`, `_NAV`, `_sidebar`, `_CRUMBS`, `_crumbs_html`,
  `_PILL_LIVE`, `_PILL_LOCK` and `shell`.
- Deploy copies the one pair to `/opt/portal_shell.py`, `/opt/portal.css` and
  `/opt/app/capi-www/portal.css`, then md5-verifies all three against the repo.

### 3.2 The admin portal's chrome, without a fourth shell

`admin/index.php` is PHP served by Apache; `portal_shell.py` is Python. Rather
than transcribe the nav by hand a second time, `portal_shell.py` gains
`emit_php_partial(path)` which writes a **generated** PHP file defining
`capi_shell_open($title, $active, $crumbs)` / `capi_shell_close()`. It is written
to `/var/www/private/capi-shell/shell.php` at deploy time, carries a
`GENERATED — do not edit` header, and `admin/index.php` requires it.

Markup keeps one source; PHP consumes a mechanical transcription of it. This
follows the project's existing generator-over-hand-edit rule.

### 3.3 URL map

| Today | After |
|---|---|
| `/projects/uhc-y2/monitoring/` — signpost | **the Sync Dashboard** |
| `/docs/dashboard.html` | `301 → /projects/uhc-y2/monitoring/` |
| `/docs/map.html` | `301 → /projects/uhc-y2/monitoring/map/` |
| `/projects/uhc-y2/data/` — signpost | **the data room index** |
| `/docs/data/` — **the bare directory only** | `301 → /projects/uhc-y2/data/` |
| `/docs/data/<file>` — the 149 downloads | **unchanged** |
| `/docs/admin/` | `301 → /projects/uhc-y2/admin/` |
| `/projects/uhc-y2/tabulations/` | unchanged — already correct |

The two signpost `index.html` files are **deleted, not redirected**. Their nav
entries now resolve to the live pages directly.

> **Two redirect hazards, both fatal if got wrong.**
>
> **(a) `/docs/data/` must be an anchored exact match.** A plain
> `Redirect 301 /docs/data/` in Apache is a *prefix* rule and would redirect every
> one of the 149 downloads to the portal index — silently breaking every export
> link and every manifest. It must be `RedirectMatch 301 ^/docs/data/$`, and the
> test suite must assert that `/docs/data/f1_responses.csv` still returns its file.
>
> **(b) `/docs/admin/` must not be redirected by Apache.** nginx proxies
> `/projects/uhc-y2/admin/` → `http://172.17.0.1:8080/docs/admin/` (§3.5). An
> Apache-level redirect on that path would answer the proxy's own request with a
> 301 back to the portal path, which nginx would proxy again — an infinite loop.
> So the split is:
>
> | Path | Redirect lives in | Why |
> |---|---|---|
> | `/docs/dashboard.html`, `/docs/map.html`, `^/docs/data/$` | **Apache** (`vhost`) | inside the already-gated `location /docs/`; nothing proxies back to them |
> | `/docs/admin/` | **nginx** (`location = /docs/admin/`, keeping `auth_request`) | the proxy target is Apache directly and never re-enters nginx routing, so no loop |

Generator output paths change accordingly:

- `csweb-dashboard-gen.py:48` → `/opt/app/capi-www/projects/uhc-y2/monitoring/index.html`
- `csweb-map-gen.py` (`--out`) → `/opt/app/capi-www/projects/uhc-y2/monitoring/map/index.html`
- `csweb-responses-gen.py:471` → `/opt/app/capi-www/projects/uhc-y2/data/index.html`

The existing `tb-seg` control (`csweb-dashboard-gen.py:1901`,
`csweb-map-gen.py:1164`) already toggles Dashboard ↔ Map in the topbar; only its
two hrefs change. The sidebar keeps **one** "Monitoring" entry.

### 3.4 What deliberately does not move

- **The download payload stays at `/docs/data/*`.** 149 CSV / SPSS / Stata / R /
  PDF / zip files are written there by the on-box generators and served by
  Apache. A `.csv` does not need a page chrome, and moving them would churn the
  `data.export` ACL rule and every manifest. Only the *index page* moves.
- **`/docs/data/tabulations-preview.json`** keeps its dedicated
  `tabulations.view` exact rule.
- **`/csweb/` and the CSEntry sync path.** Untouched. Pretest is running.
- **The F2 admin portal.** Deferred — see §8.

### 3.5 Admin at a portal path

`capi-www` is `nginx:alpine` with no PHP, so `/docs/admin/` cannot simply be
copied into the portal tree. nginx gains:

```nginx
location /projects/uhc-y2/admin/ {
  auth_request /_capi_auth;
  # …auth_request_set as in location /docs/…
  proxy_pass http://172.17.0.1:8080/docs/admin/;
}
```

The admin app is unchanged apart from consuming the generated shell partial and
having its internal links made relative.

Because the proxy target is `/docs/admin/`, **no Apache-level redirect may exist
on that path** — see hazard (b) in §3.3. The public `/docs/admin/` URL is
redirected by nginx instead.

---

## 4. Defects fixed as part of this work

Each is a live inconsistency found while surveying, not a nice-to-have.

1. **The "🔒 Sign-in required" pill is misleading.** `build_portal.py:780` shows
   it on exactly two pages while the whole portal has required sign-in since
   2026-07-28 — so the ten pages showing "Fieldwork live" read as public. The
   lock pill is retired from page chrome; "Fieldwork live" stays because it is
   a true status.
2. **The sidebar 🔒 glyphs mean nothing.** Currently hard-coded on Monitoring,
   Data & exports and Admin console. Replaced with `data-perm` attributes plus
   the small script the admin portal already uses, so an entry is dimmed when
   *your* account lacks the permission. The lock becomes information.
3. **The "login needed" card badges (7 cards, 3 pages).** Most vanish with the
   signposts. The survivors — F2 admin and CSWeb on the project home — are
   relabelled **"separate login"**, which is what is actually true about them.
4. **The data room's bespoke 238 KB chrome** is replaced by `portal_shell`.
5. **Legacy identity endpoints in the shared shell.** `portal_shell.py:140,145`
   still calls `/docs/whoami.php` and links `/docs/auth/logout`. Repointed to
   `/docs/idp/me` and `/docs/idp/logout`, the canonical post-cutover endpoints.
6. **The mobile topbar overflow** on every portal page — fixed for free by
   collapsing to one stylesheet (§3.1).
7. **A stale second nav** at `csweb-dashboard-gen.py:581` still links `/`,
   `/help.html`, `/docs/map.html`, `/docs/data/` and `/csweb/`. To be confirmed
   dead and removed, or repointed if it still renders.

---

## 5. Gate and ACL changes

`acl.php` is deny-by-default, so every new path needs a rule, and `ACL_PREFIX`
is first-match-wins — **the new rules must precede the generic `/projects/`
entry**, exactly as `/projects/uhc-y2/tabulations/` already does.

```php
// ACL_PREFIX, before ['/projects/', 'AUTH']
['/projects/uhc-y2/monitoring/', 'monitoring.view'],
['/projects/uhc-y2/data/',       'data.export'],
['/projects/uhc-y2/admin/users', 'admin.users'],   // more specific first
['/projects/uhc-y2/admin/',      'admin.system'],
```

The old `/docs/*` rules stay while the 301s exist: a redirect still has to pass
the gate. They are removed only when the redirects are retired.

Permissions are preserved exactly — `monitoring.view` for the dashboard and map,
`data.export` for the data room, `admin.system` / `admin.users` for admin. This
migration must not widen or narrow anyone's access; that is a separate decision.

---

## 6. Slices

Each is independently shippable and independently revertible.

| # | Slice | Touches URLs? |
|---|---|---|
| 1 | **Shell consolidation** — one `portal_shell.py` + one `portal.css`; `build_portal.py` imports it; clones deleted; `emit_php_partial` added | no |
| 2 | **Chrome defects** — items 1, 2, 3, 5, 7 of §4 | no |
| 3 | **Monitoring + Map move** — generator out-paths, nav, ACL, 301s, delete the signpost | yes |
| 4 | **Data room move** — index page only; payload stays; ACL, 301, delete the signpost | yes |
| 5 | **Admin at the portal path** — nginx proxy, generated partial, ACL, 301 | yes |

Slices 1 and 2 deliver the visible half — one consistent chrome and the mobile
fix — with no URL risk at all. 3–5 are the URL move.

---

## 7. Testing

- **`test_acl.php`** (currently 185 assertions) gains a positive and a negative
  case per new rule, plus an ordering assertion that
  `/projects/uhc-y2/admin/users` resolves to `admin.users` and not
  `admin.system`.
- **A clone guard.** `build_portal.py --check` asserts the module imports
  `portal_shell` and defines no local `_NAV` / `_sidebar` / `shell`. This is the
  regression that would silently undo the whole exercise.
- **A stylesheet identity check** in the deploy script: md5 of `portal.css` must
  match across the repo, `/opt/portal.css` and `/opt/app/capi-www/portal.css`.
  This is the check whose absence caused the current divergence.
- **A deployed-surface probe**, in the style of `ops/cutover-check.sh`: for every
  nav href, assert `200` for a role that holds the permission and `403`/`302`
  for one that does not. Run before and after each URL slice.
- **Download preservation** (hazard (a), §3.3): assert `/docs/data/` returns 301
  while `/docs/data/f1_responses.csv`, `/docs/data/f1-cases-spss.zip` and
  `/docs/data/codebook-manifest.json` still return `200` with their bytes intact.
  A sample of at least one file per extension.
- **Redirect-loop check** (hazard (b), §3.3): request
  `/projects/uhc-y2/admin/` and assert a single `200`, not a redirect chain.
  `curl -sS -o /dev/null -w '%{num_redirects}'` must report `0`.
- **Mobile regression:** render `/projects/uhc-y2/` at 430 px and assert no
  horizontal scroll — the specific bug §1 describes.

---

## 8. Out of scope / deferred

- **F2 admin portal absorption.** Mounting the Worker at
  `/projects/uhc-y2/f2-admin/` with portal chrome is viable and is the right
  end state, but its identity half is E9-ADMIN-046, explicitly post-pretest.
  Own spec, after pretest.
- **CSWeb.** Nav entry and new tab, permanently. Reverse-proxying vendor PHP that
  emits absolute URLs and owns its own session cookie would put the CSEntry sync
  path at risk for a cosmetic gain.
- **Redesign of dashboard / map / data-room page bodies.** Explicitly excluded by
  the scope decision in §2.
- **Retiring `/docs/whoami.php` and `/docs/login.php`.** Marked for deletion by
  the IdP cutover; adjacent but separate.

---

## 9. Open questions

1. **Do the 301s expire?** Proposal: keep them for one full survey round, then
   delete them together with the old `/docs/*` ACL rules. Needs a date, not a
   vague "later".
2. **`/help.html` and `/docs/index.php`** are both `AUTH` today and both predate
   the portal. Do they still have readers, or do they fold into
   `/projects/uhc-y2/guides/`?
3. **The `Archive` nav entry** points at `…/archive/pretest-2026-07-15/`. After
   rollout there will be a second archive; the entry should probably point at an
   archive index rather than one dated page.

## 10. Execution record (2026-08-09/10)

All five slices shipped. Deviations from this spec, found during execution:

- **§3.3's "gated first" redirect for `/docs/admin/` is impossible in nginx** —
  `return` runs at the rewrite phase, before `auth_request`, so the bounce is
  unconditional. Harmless (no content served; the destination location runs
  the full gate) and the deployed conf documents it.
- **The signpost deletion orphaned the F2-admin/CSWeb links** (their only home
  was the monitoring page's "Operate" cards, which §3.3 deleted). Fixed with a
  "Systems" section in the shared rail; `sidebar()` renders any external href
  with `target="_blank"` and a separate-sign-in title.
- **`adm_csrf` had to widen from `Path=/docs/admin/` to `Path=/`** — a
  path-scoped cookie is invisible to `document.cookie` at the proxied portal
  path, and the double-submit would fail with no error anywhere. §3.5 did not
  anticipate this.
- **The data-room payload hrefs had to become `/docs/data/`-absolute** — §3.4
  kept the files in place, which means every relative href on the moved page
  would have 404'd. Fifteen offline assertions now pin this.
- **Four legacy `.htaccess` gates** (`assets`, `img`, `cases`, `f2`) were found
  401ing every post-cutover session and removed with Carl's approval — the
  defect §1 could not have known about.
- Discovered during Slice 1: `build_portal.py` also carried a THIRD, shadowed
  document-site shell (pre-2026-07-22) — deleted; and `me.php` computed but
  never emitted its whoami-compat `tier` — fixed.
