# CAPI Release Lane — `/capi-release` (design spec)

- **Date:** 2026-07-15
- **Status:** DRAFT — awaiting Carl's review before writing the implementation plan
- **Owner:** Carl (Analytiflow) · authored with Claude
- **Related:** `deliverables/CSPro/VERSIONING.md`, `deliverables/CSPro/versions.json`,
  `automation/stamp_version.py`, `supervisor-hub/build_hub_apps.py`,
  decision diagrams `deliverables/CSPro/capi-versioning-options.png` and
  `deliverables/CSPro/hub-one-vs-two-apps.png`

---

## 1. Problem & goals

We stamp version **numbers** onto each CAPI app (`versions.json` → `stamp_version.py`
→ `.pff` Description + on-screen footer). We do **not** preserve or reproduce the
**built artifact** that was deployed. Concretely:

- The built package (`.csds` bundle / `.pen` / `.csdb` / `mbtiles`) is gitignored, so
  "exactly what CSWeb ran as HUB v1.1.4" is not stored anywhere retrievable.
- Git tags (`v1.0.0`…`v2.1.0`) do **not** map to the app versions (HUB is v1.1.4 with
  no `v1.1.4` tag). There is no binding between "deployed version X" and "commit + inputs".
- There is no isolation convention for building the *next* version without disturbing
  the currently-deployed one.

**Goals** (all four, confirmed with Carl): reproduce/roll back · provenance/audit ·
safe parallel dev · low ceremony. **Deliverable:** a reusable **skill**, `/capi-release`
(+ `/capi-rollback`).

**Non-goals (YAGNI):** no Git LFS / large binaries in git (rejected Option B); no
auto-push/tag without Carl (he drives git); no re-architecting `versions.json` /
`stamp_version.py` (reuse them); not building the two-role app split (scrapped
2026-07-15 — the hub stays one role-gated app).

---

## 2. Approach — Option C (Hybrid)

Chosen over "source-only" (A, can't roll back fast) and "artifact archive" (B, repo
bloat + secrets in stored bundles). See `capi-versioning-options.png`.

- **Commit the small, text truth:** a per-version `manifest.json` (commit SHA, tag,
  input hashes, output hashes) + the generated `.pff` Description text. This is the
  provenance / audit trail and it diffs cleanly.
- **Rebuild the big binaries from the tag,** verified byte-for-byte against the manifest
  hashes — reproducibility without storing binaries in git.
- **Keep the last N built bundles in a local, gitignored cache** for *instant* rollback
  of the versions you'd actually revert to (e.g. the frozen pretest build).
- **Wrap it in a skill** so day-to-day ceremony is one command.

---

## 3. Architecture / layout

```
deliverables/CSPro/releases/<APP>/<version>/       ← COMMITTED, tiny
    manifest.json          the record (schema below)
    LoginApp.pff           generated Description text (diff-able); per-app .pff snapshot
    MenuApp.pff            (HUB only)
deliverables/CSPro/releases-cache/<APP>/<version>/  ← GITIGNORED, local, last N (default 3)
    <the full built bundle, incl. mbtiles/.pen/.csdb — the exact deploy payload>
```

- `<APP>` ∈ `{F1, F3, F4, HUB}`, keyed off `versions.json`. The skill is app-agnostic;
  HUB is exercised first because its build is fully scripted (`build_hub_apps.py`).
- **`.gitignore` additions:** ignore `deliverables/CSPro/releases-cache/` entirely.
  `releases/` **is** committed.

### `manifest.json` schema

```jsonc
{
  "app": "HUB",
  "app_name": "UHC Survey Y2 — Field App",   // the .pff Description base
  "version": "1.1.5",
  "date": "2026-07-15",
  "released_at": "2026-07-15T14:30:00+08:00",
  "git_commit": "<sha of the release commit>",
  "git_tag": "capi-hub-v1.1.5",
  "inputs":  { "roster-source.csv": "<sha256>", "psgc_city_municipality.csv": "<sha256>",
               "survey-basemap.mbtiles": "<sha256>", "...source dcf/qsf": "<sha256>" },
  "outputs": { "LoginApp.pff": "<sha256>", "MenuApp.ent": "<sha256>", "...": "..." },
  "pff_descriptions": { "LoginApp.pff": "UHC Survey Y2 — Field App - v1.1.5 (2026-07-15)",
                        "MenuApp.pff":  "(suppressed — no Description)" },
  "csweb_package": "LoginApp",
  "deployed_at": null            // filled when the deploy step actually runs
}
```

`inputs` records the **hashes** of the gitignored secret/large inputs — never their
content. That is what lets `--verify` prove a rebuild reproduces the artifact without
committing secrets.

---

## 4. Components (the skill)

The skill **orchestrates existing scripts**; it does not reimplement builds or stamping.

### `/capi-release <APP> [--minor|--major]`
1. **Preflight** — release branch is cut from **main HEAD** (not a stale worktree);
   working tree clean; gitignored inputs present (`roster-source.csv`, `psgc_*`,
   `survey-basemap.mbtiles`); `releases/<APP>/<newver>/` does not already exist.
2. **Bump** — `py automation/stamp_version.py bump <APP> [--minor|--major]` (default
   PATCH). HUB path re-runs `build_hub_apps.py`; instruments restamp `.pff` + regen `.qsf`.
3. **Build** — assemble the deployable bundle. HUB: fully scripted (bundle list mirrors
   `deploy_hub_bundle.py`). Instruments: `.pen` compile via Designer/CSDeploy (GUI
   automation — semi-manual today; see §7 risk).
4. **Manifest + snapshot** — compute input/output SHA-256s, write
   `releases/<APP>/<newver>/manifest.json`, copy the generated `.pff`(s) text alongside.
5. **Cache** — copy the full built bundle to `releases-cache/<APP>/<newver>/`; prune to
   last N.
6. **Changelog** — append one row to `VERSIONING.md`'s history table.
7. **Git prep** — stage the `releases/` files; print the exact `git add / commit / tag
   capi-<app>-v<ver>` commands for Carl to run (he drives git). `--commit` opt-in runs them.
8. **Deploy** — SEPARATE and gated. `--deploy` hands off to `auto_deploy.py` /
   `deploy_hub_bundle.py`. Refused while the pretest-freeze flag is set.

### `/capi-rollback <APP> <version>`
- **Cache hit** → redeploy those exact bytes (`auto_deploy.py`).
- **Cache miss** → checkout tag `capi-<app>-v<version>`, restore pinned inputs, rebuild,
  **verify output hashes == manifest**, then redeploy. Mismatch → hard stop.

### `/capi-release --verify <APP> <version>`
Rebuild from the tag and compare output hashes to the manifest; report match/mismatch;
no deploy. This is the reproducibility proof.

---

## 5. Data flow

```
bump → build → manifest(+pff snapshot) → cache → changelog → [git commit+tag] → [deploy]
                         │                                                          │
                    hashes only                                          separate, gated,
                   (no secrets)                                         OFF during freeze
```

- **Git:** the skill *prepares* the commit + tag; Carl runs the actual git (his standing
  preference). The cache is never committed or pushed.
- **Deploy freeze:** a simple flag (e.g. `releases/FREEZE`) makes `--deploy` refuse, so
  the lane can archive/bump during a pretest without any risk of touching CSWeb.

---

## 6. Error handling / guardrails

- **Dirty tree or missing gitignored inputs → refuse.** Either would produce an
  unreproducible or secret-less build.
- **`releases/<APP>/<version>/` already exists → refuse.** Releases are immutable.
- **Hash mismatch on `--verify` / rollback → hard stop.** The build drifted; investigate
  before deploying.
- **`--deploy` during freeze → refuse.**
- **Secrets:** manifest stores hashes only; `releases-cache/` (real bundles with baked-in
  secrets like `UserRoster.dat`) is gitignored and local — never committed, never pushed.
- **Worktree trap:** builds must run on a branch in the **main checkout** — a fresh
  worktree lacks the gitignored `roster-source.csv` / `psgc_*`, so hub/instrument builds
  fail there (the known compile trap).

---

## 7. First release through the lane — hub rename + suppress duplicate

The first thing to ride `/capi-release` is Carl's original ask, proving the lane end-to-end.

- **Baseline (recommended):** capture the **currently deployed HUB v1.1.4** as the first
  archived release (manifest from the current build) *before* changing anything — a
  known-good rollback point.
- **Rename** (`supervisor-hub/build_hub_apps.py:887`):
  `description=f"Supervisor Hub (HUB) - {HUB_VERSION}"`
  → `description=f"UHC Survey Y2 — Field App - {HUB_VERSION}"`.
- **Suppress the duplicate entry** (`build_hub_apps.py:917`): drop the `description=`
  argument on the MenuApp `_pff(...)` call so `MenuApp.pff` carries **no** `Description`
  line. `execpff` references `MenuApp.pff` by path, so the LoginApp → MenuApp chain is
  unaffected.
- **Optional nicety:** the login **form header** (LoginApp `.qsf`) can read
  "UHC Survey Y2 — Field App — Login" — distinct from the app-list Description, which
  carries the version.
- **Bump:** HUB **PATCH → 1.1.5** (a naming/cosmetic change; Carl's SemVer call).
- **Ship:** `/capi-release HUB` archives v1.1.5. Deploy is **post-pretest** (freeze on).

### DEVICE SPIKE (acceptance gate for the first release)
Dropping MenuApp's `Description` is the lever we *expect* hides it, but CSEntry's
app-list behaviour for a Description-less `.pff` is **unverified**. On a test device,
confirm both:
1. **MenuApp no longer appears** in the CSEntry application list (not shown under a
   fallback filename like "MenuApp").
2. **LoginApp → MenuApp → instrument chain still resolves** (login still reaches the menu).

**Fallbacks if it still lists:** (a) investigate a CSEntry mechanism to exclude a bundled
`.pff` from the app list; (b) ship `MenuApp.pff` as an unregistered bundle file; (c) accept
a clearly-secondary Description (e.g. "· menu (do not open)"). Choose during the spike.

---

## 8. Testing

- **Unit:** manifest writer determinism (fixed inputs → identical manifest bar timestamp);
  hashing; cache pruning to N; each preflight refusal.
- **Integration:** run `/capi-release HUB` on a scratch branch → assert `releases/` +
  `releases-cache/` + `VERSIONING.md` row + git-prep produced; `--verify` → hashes match;
  simulate rollback from cache **and** from rebuild.
- **Device:** the MenuApp-suppression spike above (first-release acceptance).

## 9. Open risks

- **MenuApp suppression** unverified on device (§7 spike; fallbacks documented).
- **Instrument (F1/F3/F4) builds** need Designer/CSDeploy `.pen` compile (GUI automation),
  so their build step is semi-manual; HUB is fully scripted, hence first on the lane.
- **Deterministic build** assumption for `--verify`: `build_hub_apps.py` output must be
  byte-stable given fixed inputs. If it embeds a build timestamp or nondeterministic
  ordering, `--verify` compares a normalized subset — validate during implementation.
