# CAPI Release Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `/capi-release` + `/capi-rollback` — a low-ceremony release lane that preserves, reproduces, and rolls back every deployed CAPI app version.

**Architecture:** A tested Python package (`deliverables/CSPro/automation/release/`) holds the logic — hashing, manifest, bundle resolution, cache, preflight guardrails, and an orchestrator that wraps the existing `stamp_version.py` / `build_hub_apps.py` scripts. A thin CLI (`capi_release.py`) and a skill doc expose it. Committed `releases/<APP>/<version>/manifest.json` + `.pff` snapshots are the audit trail; a gitignored `releases-cache/` holds the last few built bundles for instant rollback; big binaries are otherwise rebuilt from the git tag and hash-verified.

**Tech Stack:** Python 3 (stdlib only — `hashlib`, `json`, `pathlib`, `shutil`, `subprocess`, `argparse`), pytest, git.

## Global Constraints

- **SemVer:** MAJOR.MINOR.PATCH. PATCH = bug-fix deploy (default); MINOR = new/changed functionality; MAJOR = UAT round close / breaking change. Bumping is delegated to `automation/stamp_version.py bump <APP> [--minor|--major]`.
- **`<APP>` ∈ `{F1, F3, F4, HUB}`**, keyed off `deliverables/CSPro/versions.json`. Build the code app-agnostic; **HUB is the only app wired end-to-end in this plan** (instrument `.pen` builds are semi-manual — out of scope here).
- **`releases/<APP>/<version>/` is COMMITTED and immutable** (never overwrite an existing one). **`releases-cache/` is GITIGNORED and local** (never committed/pushed).
- **`manifest.json` stores hashes only, never secret content.** The cache holds real bundles (with baked-in `UserRoster.dat`) — that is why it stays gitignored.
- **Builds run on a branch cut from `main` HEAD**, in the main checkout — a fresh worktree lacks the gitignored `roster-source.csv` / `psgc_*` and the build fails there.
- **Deploy is separate and gated.** A `releases/FREEZE` sentinel makes any deploy refuse. The skill **prepares** the git commit + tag; **Carl runs git himself** (default). Tag format: `capi-<app>-v<version>` (lowercase app).
- **Sync-before-update is MANDATORY for any field deploy.** The reliable field update path is **remove + re-add**, which deletes the app's local `.csdb` — a case that is only on a tablet (not yet synced) is lost. So a new version is announced to the field only after devices have synced. Deploy SOP: **sync all → confirm case counts on CSWeb → then remove + re-add.** The hub is exempt from the data-loss risk (LoginApp/MenuApp carry `InputData=|type=None`, no local cases), but the announce-after-sync discipline still applies. A PATCH/MINOR keeps the `.dcf` unchanged so synced cases stay compatible; a MAJOR that changes the data shape needs a migration plan.
- **Paths:** `CSPRO_ROOT = deliverables/CSPro`. `HUB_DIR = CSPRO_ROOT/supervisor-hub`. `RELEASES = CSPRO_ROOT/releases`. `CACHE = CSPRO_ROOT/releases-cache`.

---

### Task 1: Package scaffold + file hashing

**Files:**
- Create: `deliverables/CSPro/automation/release/__init__.py`
- Create: `deliverables/CSPro/automation/release/hashing.py`
- Test: `deliverables/CSPro/automation/release/tests/__init__.py`
- Test: `deliverables/CSPro/automation/release/tests/test_hashing.py`

**Interfaces:**
- Produces: `sha256_file(path: Path) -> str` — hex SHA-256 of a file's bytes, streamed.

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/automation/release/tests/test_hashing.py
from pathlib import Path
from release.hashing import sha256_file

def test_sha256_matches_known_value(tmp_path: Path):
    f = tmp_path / "x.txt"
    f.write_bytes(b"abc")
    # sha256("abc")
    assert sha256_file(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

def test_sha256_differs_on_change(tmp_path: Path):
    a = tmp_path / "a"; a.write_bytes(b"one")
    b = tmp_path / "b"; b.write_bytes(b"two")
    assert sha256_file(a) != sha256_file(b)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_hashing.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'release'` (package/module not created yet).

- [ ] **Step 3: Create the package and implementation**

```python
# deliverables/CSPro/automation/release/__init__.py
"""CAPI release lane — preserve, reproduce, and roll back deployed app builds."""
```

```python
# deliverables/CSPro/automation/release/tests/__init__.py
```

```python
# deliverables/CSPro/automation/release/hashing.py
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Hex SHA-256 of a file, streamed in 64 KB chunks (handles the 26 MB mbtiles)."""
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_hashing.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSPro/automation/release/
git commit -m "feat(release): package scaffold + sha256_file"
```

---

### Task 2: Bundle & input resolution

**Files:**
- Create: `deliverables/CSPro/automation/release/bundle.py`
- Test: `deliverables/CSPro/automation/release/tests/test_bundle.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `bundle_files(app: str, hub_dir: Path) -> list[Path]` — the exact deployable payload for `app`.
  - `input_files(app: str, cspro_root: Path) -> dict[str, Path]` — the reproducibility-relevant inputs to hash.
  - `HUB_BUNDLE: list[str]` — HUB payload filenames (mirrors `deploy_hub_bundle.py` + the LoginApp package primaries).

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/automation/release/tests/test_bundle.py
from pathlib import Path
import pytest
from release.bundle import bundle_files, input_files, HUB_BUNDLE

def test_hub_bundle_includes_both_pffs_and_roster_data():
    names = set(HUB_BUNDLE)
    assert {"LoginApp.pff", "MenuApp.pff", "UserRoster.dat", "survey-basemap.mbtiles"} <= names

def test_bundle_files_are_under_hub_dir():
    hub = Path("/fake/hub")
    paths = bundle_files("HUB", hub)
    assert all(p.parent == hub for p in paths)
    assert len(paths) == len(HUB_BUNDLE)

def test_input_files_hub_has_roster_source():
    root = Path("/fake/cspro")
    inputs = input_files("HUB", root)
    assert inputs["roster-source.csv"] == root / "data" / "roster" / "roster-source.csv"

def test_unknown_app_raises():
    with pytest.raises(ValueError):
        bundle_files("F1", Path("/fake/hub"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_bundle.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'release.bundle'`.

- [ ] **Step 3: Write the implementation**

```python
# deliverables/CSPro/automation/release/bundle.py
from pathlib import Path

# The full on-device HUB payload = the LoginApp package's own primaries + everything
# deploy_hub_bundle.py adds. Keep in sync with supervisor-hub/deploy_hub_bundle.py::BUNDLE.
HUB_BUNDLE = [
    # LoginApp package primaries (ride the package automatically at deploy, but are part
    # of the reproducible payload, so hash + cache them here):
    "LoginApp.pff", "LoginApp.ent", "LoginApp.dcf", "LoginApp.fmf",
    "LoginApp.ent.apc", "LoginApp.ent.qsf", "LoginApp.ent.mgf", "UserRoster.dcf",
    # Added bundle files:
    "MenuApp.pff", "MenuApp.ent", "MenuApp.dcf", "MenuApp.fmf",
    "MenuApp.ent.apc", "MenuApp.ent.qsf", "MenuApp.ent.mgf",
    "UserRoster.dat", "survey-basemap.mbtiles", "report.html", "menu.html",
    "Assignment.dcf", "Assignment.dat", "MyAssignment.dat",
    "FacilityHeadSurvey.dcf", "PatientSurvey.dcf", "HouseholdSurvey.dcf",
]


def bundle_files(app: str, hub_dir: Path) -> list:
    """The exact set of files that make up the deployable payload for `app`."""
    if app == "HUB":
        return [hub_dir / name for name in HUB_BUNDLE]
    raise ValueError(f"bundle for {app!r} not defined — HUB-first (see release spec)")


def input_files(app: str, cspro_root: Path) -> dict:
    """Reproducibility-relevant inputs to hash into the manifest. HUB's build is driven
    by roster-source.csv (baked into UserRoster.dat); the mbtiles ships verbatim and is
    already hashed as an output, so it is not repeated here."""
    if app == "HUB":
        return {"roster-source.csv": cspro_root / "data" / "roster" / "roster-source.csv"}
    raise ValueError(f"inputs for {app!r} not defined — HUB-first (see release spec)")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_bundle.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSPro/automation/release/bundle.py deliverables/CSPro/automation/release/tests/test_bundle.py
git commit -m "feat(release): HUB bundle + input resolution"
```

---

### Task 3: Manifest build / write / read

**Files:**
- Create: `deliverables/CSPro/automation/release/manifest.py`
- Test: `deliverables/CSPro/automation/release/tests/test_manifest.py`

**Interfaces:**
- Consumes: `release.hashing.sha256_file`.
- Produces:
  - `build_manifest(app, app_name, version, date, released_at, git_commit, git_tag, input_paths: dict, output_paths: list, pff_descriptions: dict, csweb_package: str) -> dict`
  - `write_manifest(out_dir: Path, data: dict) -> Path`
  - `read_manifest(out_dir: Path) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/automation/release/tests/test_manifest.py
from pathlib import Path
from release.manifest import build_manifest, write_manifest, read_manifest

def _mk(p: Path, b: bytes) -> Path:
    p.write_bytes(b); return p

def test_build_manifest_hashes_inputs_and_outputs(tmp_path: Path):
    ins = {"roster-source.csv": _mk(tmp_path / "roster.csv", b"secret")}
    outs = [_mk(tmp_path / "LoginApp.pff", b"pff-bytes")]
    m = build_manifest("HUB", "UHC Survey Y2 — Field App", "1.1.5", "2026-07-15",
                       "2026-07-15T14:30:00+08:00", "deadbeef", "capi-hub-v1.1.5",
                       ins, outs, {"LoginApp.pff": "UHC Survey Y2 — Field App - v1.1.5"},
                       "LoginApp")
    assert m["app"] == "HUB" and m["version"] == "1.1.5"
    assert m["git_tag"] == "capi-hub-v1.1.5"
    assert len(m["inputs"]["roster-source.csv"]) == 64            # sha256 hex
    assert "LoginApp.pff" in m["outputs"]
    assert m["deployed_at"] is None                              # filled at deploy time
    assert "secret" not in str(m)                                # content never stored

def test_write_then_read_roundtrips(tmp_path: Path):
    data = {"app": "HUB", "version": "1.1.5"}
    write_manifest(tmp_path, data)
    assert read_manifest(tmp_path) == data
    assert (tmp_path / "manifest.json").read_text(encoding="utf-8").endswith("\n")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_manifest.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'release.manifest'`.

- [ ] **Step 3: Write the implementation**

```python
# deliverables/CSPro/automation/release/manifest.py
import json
from pathlib import Path
from release.hashing import sha256_file


def build_manifest(app, app_name, version, date, released_at, git_commit, git_tag,
                   input_paths: dict, output_paths: list, pff_descriptions: dict,
                   csweb_package: str) -> dict:
    return {
        "app": app,
        "app_name": app_name,
        "version": version,
        "date": date,
        "released_at": released_at,
        "git_commit": git_commit,
        "git_tag": git_tag,
        "inputs": {name: sha256_file(p) for name, p in input_paths.items()},
        "outputs": {Path(p).name: sha256_file(p) for p in output_paths},
        "pff_descriptions": pff_descriptions,
        "csweb_package": csweb_package,
        "deployed_at": None,
    }


def write_manifest(out_dir: Path, data: dict) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "manifest.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def read_manifest(out_dir: Path) -> dict:
    return json.loads((Path(out_dir) / "manifest.json").read_text(encoding="utf-8"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_manifest.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSPro/automation/release/manifest.py deliverables/CSPro/automation/release/tests/test_manifest.py
git commit -m "feat(release): manifest build/write/read (hashes only, no secrets)"
```

---

### Task 4: Cache bundle + prune, and gitignore the cache

**Files:**
- Create: `deliverables/CSPro/automation/release/cache.py`
- Modify: `.gitignore` (append the cache dir)
- Test: `deliverables/CSPro/automation/release/tests/test_cache.py`

**Interfaces:**
- Produces:
  - `cache_bundle(app: str, version: str, files: list, cache_root: Path) -> Path`
  - `prune_cache(app: str, cache_root: Path, keep: int = 3) -> list[str]` — returns removed version names.

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/automation/release/tests/test_cache.py
from pathlib import Path
from release.cache import cache_bundle, prune_cache

def _mk(p: Path, b=b"x") -> Path:
    p.write_bytes(b); return p

def test_cache_bundle_copies_all_files(tmp_path: Path):
    src = tmp_path / "src"; src.mkdir()
    files = [_mk(src / "a.pff"), _mk(src / "b.dat")]
    dest = cache_bundle("HUB", "1.1.5", files, tmp_path / "cache")
    assert (dest / "a.pff").exists() and (dest / "b.dat").exists()
    assert dest == tmp_path / "cache" / "HUB" / "1.1.5"

def test_prune_keeps_newest_n_by_semver(tmp_path: Path):
    cache = tmp_path / "cache"
    for v in ["1.1.3", "1.1.4", "1.1.5", "1.2.0"]:
        (cache / "HUB" / v).mkdir(parents=True)
    removed = prune_cache("HUB", cache, keep=2)
    assert set(removed) == {"1.1.3", "1.1.4"}
    assert (cache / "HUB" / "1.1.5").exists() and (cache / "HUB" / "1.2.0").exists()

def test_prune_noop_when_under_limit(tmp_path: Path):
    cache = tmp_path / "cache"
    (cache / "HUB" / "1.1.5").mkdir(parents=True)
    assert prune_cache("HUB", cache, keep=3) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_cache.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'release.cache'`.

- [ ] **Step 3: Write the implementation**

```python
# deliverables/CSPro/automation/release/cache.py
import shutil
from pathlib import Path


def _vkey(name: str):
    try:
        return tuple(int(x) for x in name.split("."))
    except ValueError:
        return (0,)


def cache_bundle(app: str, version: str, files: list, cache_root: Path) -> Path:
    dest = Path(cache_root) / app / version
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        shutil.copy2(f, dest / Path(f).name)
    return dest


def prune_cache(app: str, cache_root: Path, keep: int = 3) -> list:
    app_dir = Path(cache_root) / app
    if not app_dir.exists():
        return []
    versions = sorted((d for d in app_dir.iterdir() if d.is_dir()), key=lambda d: _vkey(d.name))
    removed = versions[:-keep] if len(versions) > keep else []
    for d in removed:
        shutil.rmtree(d)
    return [d.name for d in removed]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_cache.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Gitignore the cache**

Append to `.gitignore` (the release cache holds real bundles with baked-in secrets — never commit it):

```
# CAPI release lane: built-bundle cache (local rollback only; carries UserRoster.dat)
/deliverables/CSPro/releases-cache/
```

- [ ] **Step 6: Commit**

```bash
git add deliverables/CSPro/automation/release/cache.py deliverables/CSPro/automation/release/tests/test_cache.py .gitignore
git commit -m "feat(release): bundle cache + prune-to-N; gitignore the cache"
```

---

### Task 5: Preflight guardrails

**Files:**
- Create: `deliverables/CSPro/automation/release/preflight.py`
- Test: `deliverables/CSPro/automation/release/tests/test_preflight.py`

**Interfaces:**
- Produces:
  - `class PreflightError(Exception)`
  - `check_clean_tree(root: Path) -> None`
  - `check_inputs_present(paths: dict) -> None`
  - `check_release_absent(app: str, version: str, releases_root: Path) -> None`
  - `check_not_frozen(releases_root: Path) -> None`

  Each raises `PreflightError` on violation; returns `None` on success.

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/automation/release/tests/test_preflight.py
from pathlib import Path
import pytest
from release import preflight
from release.preflight import PreflightError

def test_inputs_present_raises_when_missing(tmp_path: Path):
    with pytest.raises(PreflightError, match="missing"):
        preflight.check_inputs_present({"roster-source.csv": tmp_path / "nope.csv"})

def test_inputs_present_ok_when_all_exist(tmp_path: Path):
    f = tmp_path / "roster.csv"; f.write_text("x")
    assert preflight.check_inputs_present({"roster-source.csv": f}) is None

def test_release_absent_raises_when_dir_exists(tmp_path: Path):
    (tmp_path / "HUB" / "1.1.5").mkdir(parents=True)
    with pytest.raises(PreflightError, match="already exists"):
        preflight.check_release_absent("HUB", "1.1.5", tmp_path)

def test_release_absent_ok_when_new(tmp_path: Path):
    assert preflight.check_release_absent("HUB", "1.1.5", tmp_path) is None

def test_not_frozen_raises_when_sentinel_present(tmp_path: Path):
    (tmp_path / "FREEZE").write_text("pretest")
    with pytest.raises(PreflightError, match="freeze"):
        preflight.check_not_frozen(tmp_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_preflight.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'release.preflight'`.

- [ ] **Step 3: Write the implementation**

```python
# deliverables/CSPro/automation/release/preflight.py
import subprocess
from pathlib import Path


class PreflightError(Exception):
    """A release precondition was not met."""


def check_clean_tree(root: Path) -> None:
    out = subprocess.run(["git", "status", "--porcelain"], cwd=str(root),
                         capture_output=True, text=True).stdout.strip()
    if out:
        raise PreflightError("working tree not clean — commit or set work aside before release")


def check_inputs_present(paths: dict) -> None:
    missing = [name for name, p in paths.items() if not Path(p).exists()]
    if missing:
        raise PreflightError(
            "missing gitignored inputs: " + ", ".join(missing)
            + " — run from the main checkout, not a worktree")


def check_release_absent(app: str, version: str, releases_root: Path) -> None:
    d = Path(releases_root) / app / version
    if d.exists():
        raise PreflightError(f"release {app} {version} already exists (immutable): {d}")


def check_not_frozen(releases_root: Path) -> None:
    if (Path(releases_root) / "FREEZE").exists():
        raise PreflightError("deploy freeze active (releases/FREEZE) — archive only, no deploy")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_preflight.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSPro/automation/release/preflight.py deliverables/CSPro/automation/release/tests/test_preflight.py
git commit -m "feat(release): preflight guardrails (clean tree, inputs, immutable, freeze)"
```

---

### Task 6: Release orchestrator

**Files:**
- Create: `deliverables/CSPro/automation/release/orchestrate.py`
- Test: `deliverables/CSPro/automation/release/tests/test_orchestrate.py`

**Interfaces:**
- Consumes: `bundle`, `manifest`, `cache`, `preflight`, `hashing.sha256_file`.
- Produces:
  - `release(app: str, bump_level: str, cspro_root: Path, released_at: str, *, bump_fn=..., head_fn=...) -> dict` — runs the full lane; returns `{"version", "tag", "release_dir", "pruned", "git": [cmd, ...]}`.
  - `_bump_version(cur: str, level: str) -> str` (helper, tested).
  - `_pff_descriptions(pff_paths: list) -> dict` (helper, tested).

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/automation/release/tests/test_orchestrate.py
import json
from pathlib import Path
import pytest
from release import orchestrate
from release.bundle import HUB_BUNDLE

def _fake_hub_root(tmp_path: Path) -> Path:
    root = tmp_path / "CSPro"
    (root / "supervisor-hub").mkdir(parents=True)
    (root / "data" / "roster").mkdir(parents=True)
    (root / "data" / "roster" / "roster-source.csv").write_text("u,p\n")
    for name in HUB_BUNDLE:
        f = root / "supervisor-hub" / name
        if name == "LoginApp.pff":
            f.write_text("[Run Information]\nDescription=Supervisor Hub (HUB) - v1.1.4\n")
        elif name == "MenuApp.pff":
            f.write_text("[Run Information]\n")            # suppressed: no Description
        else:
            f.write_text(name)
    (root / "versions.json").write_text(json.dumps(
        {"HUB": {"app": "UHC Survey Y2 — Field App", "version": "1.1.4", "date": "2026-07-15"}}))
    return root

def test_bump_version_semver():
    assert orchestrate._bump_version("1.1.4", "patch") == "1.1.5"
    assert orchestrate._bump_version("1.1.4", "minor") == "1.2.0"
    assert orchestrate._bump_version("1.1.4", "major") == "2.0.0"

def test_pff_descriptions_reads_and_flags_suppressed(tmp_path: Path):
    a = tmp_path / "LoginApp.pff"; a.write_text("Description=UHC Survey Y2 — Field App - v1.1.5\n")
    b = tmp_path / "MenuApp.pff"; b.write_text("[Run Information]\n")
    d = orchestrate._pff_descriptions([a, b])
    assert d["LoginApp.pff"] == "UHC Survey Y2 — Field App - v1.1.5"
    assert d["MenuApp.pff"] == "(suppressed — no Description)"

def test_release_produces_manifest_cache_changelog(tmp_path: Path, monkeypatch):
    root = _fake_hub_root(tmp_path)
    monkeypatch.setattr(orchestrate.preflight, "check_clean_tree", lambda r: None)

    def fake_bump(app, level, cspro_root):
        v = json.loads((cspro_root / "versions.json").read_text())
        v[app]["version"] = orchestrate._bump_version(v[app]["version"], level)
        (cspro_root / "versions.json").write_text(json.dumps(v))

    out = orchestrate.release("HUB", "patch", root, "2026-07-15T14:30:00+08:00",
                              bump_fn=fake_bump, head_fn=lambda r: "cafebabe")

    assert out["version"] == "1.1.5"
    assert out["tag"] == "capi-hub-v1.1.5"
    m = json.loads((root / "releases" / "HUB" / "1.1.5" / "manifest.json").read_text(encoding="utf-8"))
    assert m["git_commit"] == "cafebabe"
    assert m["pff_descriptions"]["MenuApp.pff"] == "(suppressed — no Description)"
    assert len(m["outputs"]) == len(HUB_BUNDLE)
    assert (root / "releases" / "HUB" / "1.1.5" / "LoginApp.pff").exists()   # .pff snapshot
    assert (root / "releases-cache" / "HUB" / "1.1.5" / "survey-basemap.mbtiles").exists()
    assert "| 2026-07-15 | HUB | 1.1.5 |" in (root / "releases" / "CHANGELOG.md").read_text(encoding="utf-8")

def test_release_refuses_when_release_exists(tmp_path: Path, monkeypatch):
    root = _fake_hub_root(tmp_path)
    monkeypatch.setattr(orchestrate.preflight, "check_clean_tree", lambda r: None)
    (root / "releases" / "HUB" / "1.1.5").mkdir(parents=True)
    with pytest.raises(orchestrate.preflight.PreflightError, match="already exists"):
        orchestrate.release("HUB", "patch", root, "t", bump_fn=lambda *a: None, head_fn=lambda r: "x")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_orchestrate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'release.orchestrate'`.

- [ ] **Step 3: Write the implementation**

```python
# deliverables/CSPro/automation/release/orchestrate.py
import json
import shutil
import subprocess
import sys
from pathlib import Path

from release import bundle, manifest, cache, preflight


def _bump_version(cur: str, level: str) -> str:
    major, minor, patch = (int(x) for x in cur.split("."))
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _read_meta(app: str, cspro_root: Path) -> dict:
    return json.loads((Path(cspro_root) / "versions.json").read_text(encoding="utf-8"))[app]


def _pff_descriptions(pff_paths: list) -> dict:
    out = {}
    for p in pff_paths:
        desc = "(suppressed — no Description)"
        for line in Path(p).read_text(encoding="utf-8-sig").splitlines():
            if line.startswith("Description="):
                desc = line[len("Description="):].strip()
                break
        out[Path(p).name] = desc
    return out


def _append_changelog(path: Path, app: str, version: str, date: str, app_name: str) -> None:
    path = Path(path)
    if not path.exists():
        path.write_text("# CAPI release log\n\n| Date | App | Version | Name |\n"
                        "| --- | --- | --- | --- |\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"| {date} | {app} | {version} | {app_name} |\n")


def _default_bump(app: str, level: str, cspro_root: Path) -> None:
    args = [sys.executable, "automation/stamp_version.py", "bump", app]
    if level in ("minor", "major"):
        args.append(f"--{level}")
    subprocess.run(args, cwd=str(cspro_root), check=True)


def _default_head(cspro_root: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(cspro_root),
                          capture_output=True, text=True).stdout.strip()


def release(app: str, bump_level: str, cspro_root: Path, released_at: str,
            *, bump_fn=_default_bump, head_fn=_default_head) -> dict:
    cspro_root = Path(cspro_root)
    hub_dir = cspro_root / "supervisor-hub"
    releases = cspro_root / "releases"
    cache_root = cspro_root / "releases-cache"

    # Refuse BEFORE mutating anything.
    preflight.check_clean_tree(cspro_root)
    inputs = bundle.input_files(app, cspro_root)
    preflight.check_inputs_present(inputs)
    next_version = _bump_version(_read_meta(app, cspro_root)["version"], bump_level)
    preflight.check_release_absent(app, next_version, releases)

    # Bump + build (HUB: stamp_version re-runs build_hub_apps.py).
    bump_fn(app, bump_level, cspro_root)
    meta = _read_meta(app, cspro_root)
    if meta["version"] != next_version:
        raise preflight.PreflightError(
            f"stamp_version produced {meta['version']}, expected {next_version}")

    files = bundle.bundle_files(app, hub_dir)
    descs = _pff_descriptions([p for p in files if p.suffix == ".pff"])
    tag = f"capi-{app.lower()}-v{meta['version']}"
    data = manifest.build_manifest(app, meta["app"], meta["version"], meta["date"], released_at,
                                   head_fn(cspro_root), tag, inputs, files, descs, "LoginApp")

    out_dir = releases / app / meta["version"]
    manifest.write_manifest(out_dir, data)
    for p in files:
        if p.suffix == ".pff":
            shutil.copy2(p, out_dir / p.name)

    cache.cache_bundle(app, meta["version"], files, cache_root)
    pruned = cache.prune_cache(app, cache_root, keep=3)
    _append_changelog(releases / "CHANGELOG.md", app, meta["version"], meta["date"], meta["app"])

    return {
        "version": meta["version"], "tag": tag, "release_dir": out_dir, "pruned": pruned,
        "git": [
            f"git add {out_dir} {releases / 'CHANGELOG.md'} deliverables/CSPro/versions.json "
            f"deliverables/CSPro/supervisor-hub/LoginApp.pff "
            f"deliverables/CSPro/supervisor-hub/MenuApp.pff",
            f'git commit -m "release({app.lower()}): {meta["version"]}"',
            f"git tag {tag}",
        ],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_orchestrate.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSPro/automation/release/orchestrate.py deliverables/CSPro/automation/release/tests/test_orchestrate.py
git commit -m "feat(release): orchestrator — bump+build → manifest → cache → changelog → git-prep"
```

---

### Task 7: Verify + rollback

**Files:**
- Create: `deliverables/CSPro/automation/release/recover.py`
- Test: `deliverables/CSPro/automation/release/tests/test_recover.py`

**Interfaces:**
- Consumes: `hashing.sha256_file`.
- Produces:
  - `verify_against_manifest(files: list, manifest: dict) -> list[str]` — filenames whose current bytes differ from the manifest (empty = reproduces).
  - `rollback(app: str, version: str, cspro_root: Path, deploy_fn) -> dict` — cache hit → `deploy_fn(cache_dir)` and return `{"mode": "cache", ...}`; miss → `{"mode": "rebuild-required", ...}`.

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/automation/release/tests/test_recover.py
from pathlib import Path
from release.recover import verify_against_manifest, rollback
from release.hashing import sha256_file

def test_verify_empty_when_bytes_match(tmp_path: Path):
    f = tmp_path / "LoginApp.pff"; f.write_bytes(b"same")
    m = {"outputs": {"LoginApp.pff": sha256_file(f)}}
    assert verify_against_manifest([f], m) == []

def test_verify_flags_changed_file(tmp_path: Path):
    f = tmp_path / "LoginApp.pff"; f.write_bytes(b"orig")
    m = {"outputs": {"LoginApp.pff": sha256_file(f)}}
    f.write_bytes(b"tampered")
    assert verify_against_manifest([f], m) == ["LoginApp.pff"]

def test_rollback_cache_hit_calls_deploy(tmp_path: Path):
    root = tmp_path / "CSPro"
    cache_dir = root / "releases-cache" / "HUB" / "1.1.4"
    cache_dir.mkdir(parents=True)
    called = {}
    rollback("HUB", "1.1.4", root, deploy_fn=lambda d: called.setdefault("dir", d))
    assert called["dir"] == cache_dir

def test_rollback_cache_miss_reports_rebuild(tmp_path: Path):
    out = rollback("HUB", "9.9.9", tmp_path / "CSPro", deploy_fn=lambda d: None)
    assert out["mode"] == "rebuild-required"
    assert "capi-hub-v9.9.9" in out["hint"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_recover.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'release.recover'`.

- [ ] **Step 3: Write the implementation**

```python
# deliverables/CSPro/automation/release/recover.py
from pathlib import Path
from release.hashing import sha256_file


def verify_against_manifest(files: list, manifest: dict) -> list:
    stored = manifest.get("outputs", {})
    bad = []
    for p in files:
        name = Path(p).name
        if name in stored and sha256_file(p) != stored[name]:
            bad.append(name)
    return bad


def rollback(app: str, version: str, cspro_root: Path, deploy_fn) -> dict:
    cache_dir = Path(cspro_root) / "releases-cache" / app / version
    if cache_dir.exists():
        deploy_fn(cache_dir)                       # instant: redeploy the exact bytes
        return {"mode": "cache", "source": cache_dir}
    return {
        "mode": "rebuild-required", "source": None,
        "hint": (f"cache miss — checkout tag capi-{app.lower()}-v{version}, restore inputs, "
                 f"rebuild, run --verify, then deploy"),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_recover.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSPro/automation/release/recover.py deliverables/CSPro/automation/release/tests/test_recover.py
git commit -m "feat(release): verify-against-manifest + rollback (cache-hit / rebuild)"
```

---

### Task 8: CLI entry point

**Files:**
- Create: `deliverables/CSPro/automation/capi_release.py`
- Test: `deliverables/CSPro/automation/release/tests/test_cli.py`

**Interfaces:**
- Consumes: `release.orchestrate.release`, `release.recover.rollback`.
- Produces: `main(argv: list | None = None) -> int` — subcommands `release <APP> [--minor|--major]`, `rollback <APP> <version>`.

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/automation/release/tests/test_cli.py
import importlib
import pytest

cli = importlib.import_module("capi_release")

def test_release_dispatch_defaults_to_patch(monkeypatch):
    seen = {}
    def fake_release(app, level, cspro_root, released_at, **kw):
        seen.update(app=app, level=level)
        return {"version": "1.1.5", "tag": "capi-hub-v1.1.5", "release_dir": "d",
                "pruned": [], "git": ["git ..."]}
    monkeypatch.setattr(cli.orchestrate, "release", fake_release)
    rc = cli.main(["release", "HUB"])
    assert rc == 0 and seen == {"app": "HUB", "level": "patch"}

def test_release_minor_flag(monkeypatch):
    seen = {}
    monkeypatch.setattr(cli.orchestrate, "release",
                        lambda app, level, *a, **k: seen.update(level=level) or
                        {"version": "1.2.0", "tag": "t", "release_dir": "d", "pruned": [], "git": []})
    cli.main(["release", "HUB", "--minor"])
    assert seen["level"] == "minor"

def test_rollback_dispatch(monkeypatch):
    seen = {}
    monkeypatch.setattr(cli.recover, "rollback",
                        lambda app, version, *a, **k: seen.update(app=app, version=version) or
                        {"mode": "cache", "source": "x"})
    rc = cli.main(["rollback", "HUB", "1.1.4"])
    assert rc == 0 and seen == {"app": "HUB", "version": "1.1.4"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'capi_release'`.

- [ ] **Step 3: Write the implementation**

```python
# deliverables/CSPro/automation/capi_release.py
"""CAPI release lane CLI.  Run from deliverables/CSPro/automation/.

  py capi_release.py release HUB [--minor|--major]
  py capi_release.py rollback HUB 1.1.4
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

from release import orchestrate, recover

CSPRO_ROOT = Path(__file__).resolve().parent.parent      # deliverables/CSPro


def _deploy_stub(cache_dir: Path) -> None:
    print(f"  redeploy the exact bytes in: {cache_dir}")
    print("  (hand off to auto_deploy.py / deploy_hub_bundle.py — gated; not automatic)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="capi_release")
    sub = ap.add_subparsers(dest="cmd", required=True)

    rel = sub.add_parser("release", help="bump + archive a new version of an app")
    rel.add_argument("app", choices=["F1", "F3", "F4", "HUB"])
    grp = rel.add_mutually_exclusive_group()
    grp.add_argument("--minor", action="store_true")
    grp.add_argument("--major", action="store_true")

    rb = sub.add_parser("rollback", help="redeploy a previously-released version")
    rb.add_argument("app", choices=["F1", "F3", "F4", "HUB"])
    rb.add_argument("version")

    args = ap.parse_args(argv)

    if args.cmd == "release":
        level = "major" if args.major else "minor" if args.minor else "patch"
        released_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        out = orchestrate.release(args.app, level, CSPRO_ROOT, released_at)
        print(f"released {args.app} {out['version']}  (tag {out['tag']})")
        if out["pruned"]:
            print(f"  pruned from cache: {', '.join(out['pruned'])}")
        print("  next — run these to record it in git:")
        for cmd in out["git"]:
            print(f"    {cmd}")
        return 0

    if args.cmd == "rollback":
        out = recover.rollback(args.app, args.version, CSPRO_ROOT, _deploy_stub)
        print(f"rollback {args.app} {args.version}: {out['mode']}")
        if out.get("hint"):
            print(f"  {out['hint']}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSPro/automation && python -m pytest release/tests/test_cli.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Run the full suite + commit**

Run: `cd deliverables/CSPro/automation && python -m pytest release/ -v`
Expected: PASS (all tasks' tests green).

```bash
git add deliverables/CSPro/automation/capi_release.py deliverables/CSPro/automation/release/tests/test_cli.py
git commit -m "feat(release): CLI (release / rollback subcommands)"
```

---

### Task 9: Skill wrapper

**Files:**
- Create: `.claude/skills/capi-release/SKILL.md`

**Interfaces:** none (documentation that drives the CLI). No test — verified by reading.

- [ ] **Step 1: Write the skill doc**

```markdown
---
name: capi-release
description: Cut, archive, and roll back a versioned build of a CAPI app (F1/F3/F4/HUB). Use when Carl says "release the hub", "cut a new version", "roll back to vX", or "archive this build". Wraps deliverables/CSPro/automation/capi_release.py. HUB is fully supported; instruments need their .pen compiled first.
---

# CAPI Release

The single source of truth is `deliverables/CSPro/versions.json`; this skill preserves
each **deployed** build so it can be reproduced or rolled back. Design spec:
`deliverables/CSPro/docs/specs/2026-07-15-capi-release-lane.md`.

## Preconditions
- Run from a branch cut off **main HEAD**, in the **main checkout** (a worktree lacks the
  gitignored `roster-source.csv` and the build fails).
- Working tree clean. Gitignored inputs present.

## Cut a release
```
cd deliverables/CSPro/automation
py capi_release.py release HUB            # PATCH (default)
py capi_release.py release HUB --minor    # or --major
```
This bumps + builds, writes `releases/HUB/<v>/manifest.json` + the `.pff` snapshots,
caches the full bundle under `releases-cache/HUB/<v>/`, appends `releases/CHANGELOG.md`,
and prints the `git add/commit/tag` commands. **Carl runs those git commands.**

## Deploy (separate, gated)
Deploy is NOT automatic and is refused while `releases/FREEZE` exists (e.g. during a
pretest). When clear, deploy with the existing automation
(`supervisor-hub/deploy_hub_bundle.py` / `automation/auto_deploy.py`).

## Sync-before-update (MANDATORY before any F1/F3/F4 update reaches the field)
The field update path is **remove + re-add**, which deletes the app's local `.csdb`. Any
case that is only on a tablet (not yet synced) is lost. Before announcing a new instrument
version:
1. Every enumerator **syncs all cases** to CSWeb.
2. **Confirm the case counts on CSWeb** (Data tab / Sync Report) — a synced case lives on
   the server and no local app update can touch it.
3. Only then push/announce the update; enumerators **remove + re-add**.

The **hub** (LoginApp/MenuApp, `InputData=|type=None`) holds no cases, so its update is
data-safe regardless — but keep the same announce-after-sync discipline. Dictionary note:
a PATCH/MINOR leaves the `.dcf` unchanged (synced cases stay compatible); a MAJOR that
changes the data shape needs a migration plan, not just a rebuild.

## Roll back
```
py capi_release.py rollback HUB 1.1.4
```
Cache hit → redeploy those exact bytes. Cache miss → checkout `capi-hub-v1.1.4`, restore
inputs, rebuild, then `py -m pytest`-style verify against the manifest before deploying.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/capi-release/SKILL.md
git commit -m "docs(release): /capi-release skill wrapper"
```

---

### Task 10: First release through the lane — hub rename + suppress duplicate

**Files:**
- Modify: `deliverables/CSPro/supervisor-hub/build_hub_apps.py` (LoginApp Description ~line 887; MenuApp `_pff` ~line 917)

**Interfaces:** none (produces the first real release + the device-spike evidence).

- [ ] **Step 1: Rename the single app**

In `build_hub_apps.py`, the LoginApp `_pff(...)` call, change:

```python
                description=f"Supervisor Hub (HUB) - {HUB_VERSION}"))
```
to:
```python
                description=f"UHC Survey Y2 — Field App - {HUB_VERSION}"))
```

- [ ] **Step 2: Suppress the MenuApp app-list entry**

In the MenuApp `_pff(...)` call, remove the `description=` argument entirely so
`MenuApp.pff` is written with **no** `Description=` line. Change:

```python
           _pff("MenuApp.ent", "|type=None", externals=menu_pff_ext,
                description=f"Supervisor Hub Menu (HUB) - {HUB_VERSION}"))
```
to:
```python
           _pff("MenuApp.ent", "|type=None", externals=menu_pff_ext))
```

- [ ] **Step 3: Rebuild and eyeball the pffs**

Run: `cd deliverables/CSPro/supervisor-hub && py build_hub_apps.py`
Then confirm:
- `LoginApp.pff` has `Description=UHC Survey Y2 — Field App - v1.1.4 (...)`
- `MenuApp.pff` has **no** `Description=` line.

- [ ] **Step 4: Cut the release (PATCH → 1.1.5)**

Run: `cd deliverables/CSPro/automation && py capi_release.py release HUB`
Expected: `released HUB 1.1.5 (tag capi-hub-v1.1.5)`, and
`releases/HUB/1.1.5/manifest.json` shows
`pff_descriptions.MenuApp.pff == "(suppressed — no Description)"`.
Run the printed `git add/commit/tag` commands to record it.

- [ ] **Step 5: DEVICE SPIKE (acceptance gate — do NOT deploy to CSWeb; freeze is on)**

On a **test device only**, sideload/install the freshly built bundle and confirm BOTH:
1. Only **one** hub entry appears — "UHC Survey Y2 — Field App" — and "Supervisor Hub
   Menu" is **gone** (not shown under a fallback name like "MenuApp").
2. Logging in still reaches the role menu (the `LoginApp → execpff → MenuApp` chain works).

If MenuApp still lists, apply a fallback (spec §7) and re-cut as 1.1.6. Record the result
(screenshot) under `deliverables/CSPro/automation/shots/`. **CSWeb deploy stays deferred
until after the pretest.**

---

## Self-review

**Spec coverage:**
- releases/ + cache layout → Tasks 3, 4, 6. manifest schema → Task 3. cache last-N → Task 4.
  preflight guardrails (dirty/inputs/immutable/freeze) → Task 5. `/capi-release` flow → Task 6.
  verify + rollback → Task 7. CLI + skill → Tasks 8, 9. hub rename + suppress + spike → Task 10.
  gitignore cache → Task 4. changelog → Task 6.
- **Deferred by design (spec §1 non-goals / §9 risks):** instrument (F1/F3/F4) `.pen` builds
  (semi-manual, HUB-first); the full "checkout tag → rebuild → verify" rollback wrapper is
  documented (skill) on top of the tested `verify_against_manifest` core; Git-LFS / two-app
  split are explicit non-goals. Deploy automation reuses existing scripts (not rebuilt here).
- **Prerequisite for the first F1/F3/F4 deploy (not the hub):** device-verify what remove +
  re-add does to an instrument's `.csdb` (wipes vs. preserves) and enforce the
  **Sync-before-update** SOP (Global Constraints + skill). The hub release (Task 10) is
  exempt — the hub stores no cases.

**Placeholder scan:** none — every code step is complete; no TBD/TODO.

**Type consistency:** `release()` returns `{version, tag, release_dir, pruned, git}` — consumed
verbatim by the CLI (Task 8). `rollback()` returns `{mode, source[, hint]}` — consumed by the CLI.
`verify_against_manifest(files, manifest) -> list` and `_pff_descriptions(list) -> dict` names
match between Tasks 6/7 and their tests.

---
