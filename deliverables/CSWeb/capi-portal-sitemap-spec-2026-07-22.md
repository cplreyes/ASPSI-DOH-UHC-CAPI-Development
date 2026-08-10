---
project: UHC Survey Year 2 — CAPI
artifact: capi.asiansocial.org — full sitemap & migration spec
version: 1.0 (2026-07-22)
status: agreed structure, build not started
decided_by: Carl (2026-07-22, options diagram `capi-portal-sitemap-options-2026-07-22.png`)
---

# capi.asiansocial.org — full sitemap & migration spec

One portal for ASPSI's CAPI work. **UHC Survey Y2 (DOH) is the first project; the structure
assumes more will follow.**

## 1. Decisions locked

| Question | Decision |
|---|---|
| IA shape | **Option A — project-first**, with Option C's *role welcome mat* on the project home |
| Migration | **New site + 301 redirects** from the old doc URLs; nothing breaks for anyone holding an old link |
| Stale content | Archive pretest-guide · regenerate the 4 crosswalks · merge the two front doors · rebuild the F2 crosswalk |
| Tablet sync | **DO NOT TOUCH — pretest is running.** `SyncUrl` stays `https://csweb.asiansocial.org/csweb/api/`. The `/csweb/` move is revisited *after* pretesting. |

## 2. What already exists (discovered 2026-07-22 — not a greenfield)

`capi.asiansocial.org` **is already live**: DNS → 207.148.65.115, TLS issued by the
`elestio-nginx` auto-SSL front end (`ALLOWED_DOMAINS` already includes it), proxied to the
**`capi-www`** nginx container serving `/opt/app/capi-www`. It holds a 3-page skeleton from
**8 July 2026**:

| URL | Title | State |
|---|---|---|
| `/` | ASPSI CAPI Services — "Survey data systems for evidence decision-makers can trust" + *What we build* / *Projects* | skeleton, keep + expand |
| `/uhc/` | UHC Survey 2026 — ASPSI CAPI | skeleton, becomes the project home |
| `/docs/` | Documentation — ASPSI CAPI | skeleton, folds into the project's guides/manual |

**No infrastructure work is needed** — no DNS, no cert, no vhost. This is content work only.
The skeleton's shape already matches the chosen project-first model.

> Naming note: the skeleton uses `/uhc/`; this spec uses `/projects/uhc-y2/` (as chosen).
> `/uhc/` will 301 to it, so the July links keep working. If you prefer the shorter
> `/uhc-y2/` (no `/projects/` segment), say so before the build — it's a find-replace now
> and a redirect exercise later.

## 3. The sitemap

🔓 = public · 🔒 = behind the shared monitoring login (same credential as today)

| URL | Page | Audience | Auth | Built from |
|---|---|---|---|---|
| `/` | **CAPI at ASPSI** — what we do + project cards | anyone | 🔓 | existing skeleton + `index.html` intro |
| `/about/` | ASPSI, the team, contact | anyone | 🔓 | new (short) |
| `/platform/` | How we build CAPI — CSPro/CSEntry + CSWeb + PWA stack, standards we follow (DDI, PSA/PSADA), QA approach | prospective clients, DOH | 🔓 | new, from the CAPI workflow template |
| `/projects/` | Project catalog (one card today) | anyone | 🔓 | new |
| **`/projects/uhc-y2/`** | **Project home — the role welcome mat** (4 rows, below) + status strip | everyone | 🔓 | merge of `csweb:/index.html` + `/help.html` |
| `/projects/uhc-y2/guides/` | Guides index | field staff | 🔓 | from `help.html` §guides |
| `/projects/uhc-y2/guides/enumerator/` | CSEntry on your tablet | enumerators | 🔓 | `enumerator-guide.html` |
| `/projects/uhc-y2/guides/supervisor/` | Supervisor & Enumerator Hub | supervisors | 🔓 | `hub-guide.html` |
| `/projects/uhc-y2/guides/healthcare-worker/` | How to complete the F2 survey | HCW respondents | 🔓 | `hcw-guide.html` |
| `/projects/uhc-y2/manual/` | Full CAPI manual (13.4k w) | supervisors, DOH | 🔓 | `capi-manual.html` |
| `/projects/uhc-y2/instruments/` | The four instruments, at a glance + current versions | all | 🔓 | new index |
| `…/instruments/f1/` … `/f4/` | **One page per instrument**: paper↔CAPI crosswalk · codebook (xlsx/PDF) · dictionary · CSPro app package · version history | reviewers, analysts | 🔓 page, 🔒 data files | `f*-crosswalk.html` + codebook & CSPro manifests |
| `/projects/uhc-y2/monitoring/` | Monitoring index — what each view answers | ASPSI/DOH | 🔓 | new (thin) |
| `…/monitoring/dashboard/` | Sync Dashboard (live, 2-min) | ASPSI/DOH | 🔒 | `dashboard.html` (generated) |
| `…/monitoring/map/` | Map Report (live, 2-min) | ASPSI/DOH | 🔒 | `map.html` (generated) |
| `/projects/uhc-y2/data/` | **Data & documentation room** — exports (CSV/SPSS/Stata/R), codebooks, CSPro packages, dictionaries | analysts | 🔒 | `/docs/data/` (generated) |
| `/projects/uhc-y2/archive/pretest-2026-07-15/` | Pretest field guide, dated banner | reference | 🔓 | `pretest-guide.html` |

### The role welcome mat (project home)

Four rows, each one sentence + a button — this is Option C's virtue without its cost:

1. **"I'm collecting in the field"** → enumerator guide · tablet setup · syncing · troubleshooting
2. **"I'm a healthcare worker invited to the survey"** → the F2 guide (+ the survey link)
3. **"I'm supervising fieldwork"** → dashboard · map · supervisor guide (login needed)
4. **"I'm working with the data"** → data room · codebooks · instruments (login needed)

Below it: a live status strip (cases collected, last sync) and *What is this survey?* in three sentences.

## 4. Redirect map (301, old → new)

| Old (csweb.asiansocial.org) | New (capi.asiansocial.org) |
|---|---|
| `/` | `/projects/uhc-y2/` |
| `/help.html` | `/projects/uhc-y2/` |
| `/docs/enumerator-guide.html` | `…/guides/enumerator/` |
| `/docs/hub-guide.html` | `…/guides/supervisor/` |
| `/docs/hcw-guide.html` | `…/guides/healthcare-worker/` |
| `/docs/capi-manual.html` | `…/manual/` |
| `/docs/f1-crosswalk.html` … `f4` | `…/instruments/f1/` … `/f4/` |
| `/docs/dashboard.html` | `…/monitoring/dashboard/` |
| `/docs/map.html` | `…/monitoring/map/` |
| `/docs/data/` | `…/data/` |
| `/docs/pretest-guide.html` | `…/archive/pretest-2026-07-15/` |
| **`/csweb/**`** | **NO REDIRECT — stays put (tablet sync)** |

Implemented in the `elestio-nginx` server block for `csweb.asiansocial.org` (a `location` per
path, `return 301`). `/csweb/` must be matched *first* and excluded.

## 5. Auth model

Unchanged in substance: guides and instrument pages public; monitoring + data behind the
existing shared credential. Two improvements:

- gate by **directory** (`/projects/uhc-y2/monitoring/`, `…/data/`) instead of today's
  three-filename `FilesMatch` — new gated pages then can't leak by being forgotten;
- one login covers both, as now (enumerator field logins + the aspsi/marriz accounts).

## 6. Content actions before/while porting

| Action | Detail |
|---|---|
| **Merge front doors** | `index.html` (1.7k w) + `help.html` (2.2k w) → one project home; keep the landing's plain-language survey description, keep help's task sections, drop the duplication. |
| **Regenerate crosswalks** | Last built 1 Jul; instruments shipped v1.1.4 / v1.1.5 / v1.4.4 on 19 Jul. Regenerate from current builds so paper↔CAPI matches what's deployed. |
| **Rebuild F2 crosswalk** | 0.7k w vs 6.8–10k for its siblings, predates R6/R7. Rebuild to match. |
| **Archive pretest guide** | Move under `/archive/pretest-2026-07-15/` with a dated banner; link from the project home's history, not the main nav. |
| **Kill the .bak clutter** | ~15 `*.bak-*` files sit in the live `/docs/` directory; they don't come across. |
| **Add** | `robots.txt` (disallow all — every page is already `noindex`) and a real 404 page. |

## 7. Build sequence

1. **Content port, public pages** — project home (merged) + guides + manual + archive. No behaviour change; old site still live.
2. **Instruments section** — regenerated crosswalks + per-instrument pages wired to the codebook/CSPro manifests.
3. **Monitoring + data** — point the generators' `OUT`/`OUT_DIR` at the `capi-www` docroot; move the `.htaccess` gate; verify 401s **before** any data lands.
4. **Redirects** — switch on the 301s from csweb doc URLs.
5. **After pretest ends** — revisit whether `/csweb/` (and the tablet `SyncUrl`) moves. **Not now.**

Steps 1–2 are safe any time. Step 3 is the only one touching live monitoring; do it in one
window and verify. Step 4 is reversible.

## 8. Deferred (explicitly, at Carl's instruction)

**The enumerator sync endpoint does not move during pretesting.** Tablets in the field carry
`SyncUrl=https://csweb.asiansocial.org/csweb/api/` in their `.pff`; CSWeb keeps serving it.
Revisit after pretest — and note that moving it means redeploying every instrument and
re-syncing the fleet, so it likely rides the next round boundary or never happens at all
(a permanent alias costs nothing).
