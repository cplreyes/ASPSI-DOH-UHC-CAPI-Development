# CAPI Console Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse five hand-maintained page-chromes into one, and make `/projects/uhc-y2/{monitoring, monitoring/map, data, admin}/` the live pages themselves rather than signposts that point at `/docs/*`.

**Architecture:** `portal_shell.py` becomes the single markup source for every surface. Python generators import it directly; `admin/index.php` consumes a *generated* PHP partial emitted from the same module, so PHP never hand-copies the nav. The on-box generators change their output paths to write into the static portal's docroot — exactly the pattern `csweb-tabulations-gen.py` already uses. `/docs/*` becomes redirects.

**Tech Stack:** Python 3 (stdlib only — the box has no third-party deps), PHP 8.1 (mod_php in `lamp-php8`), Apache 2.4, nginx (host-networked `elestio-nginx`), MySQL 8.4. No build step, no bundler, no framework.

**Spec:** `docs/superpowers/specs/2026-08-09-capi-console-unification-design.md`

## Global Constraints

- **stdlib only** in every Python file under `deliverables/CSWeb/` — the box generators have no third-party dependencies. No `requests`, no `jinja2`.
- **Do not touch `/csweb/` or the CSEntry `SyncUrl`.** Pretest is running. Any task that would change sync behaviour is out of scope and must stop and report instead.
- **Permissions must not change.** `monitoring.view` for dashboard and map, `data.export` for the data room, `admin.system` / `admin.users` for admin. This plan moves URLs; it does not widen or narrow access.
- **`acl.php` is deny-by-default and `ACL_PREFIX` is first-match-wins.** Every new path needs a rule, and more specific prefixes must be listed before less specific ones.
- **Canonical brand values** (already in `portal_shell.py`): `VERDE = "#046a38"`, `GOLD = "#e5b23b"`, `P = "/projects/uhc-y2"`.
- **Every commit message** ends with the session trailer already configured for this repo.
- Tests are plain scripts with a `check()` helper and a non-zero exit on failure — matching `deliverables/CSWeb/auth/test_acl.php`. No pytest, no PHPUnit.

---

## File Structure

**Created**

| File | Responsibility |
|---|---|
| `deliverables/CSWeb/test_portal_shell.py` | Unit tests for the shared shell: nav model, `css` mode, PHP partial emission. |
| `deliverables/CSWeb/ops/verify-chrome.sh` | Post-deploy assertion that the one stylesheet and one shell module are byte-identical in all three deployed locations. |
| `deliverables/CSWeb/ops/probe-surfaces.sh` | Role × URL probe: every nav href returns 200 for a permitted role and 403/302 for one without. |

**Modified**

| File | Change |
|---|---|
| `deliverables/CSWeb/portal_shell.py` | Gains `css` mode, `emit_php_partial()`, `data-perm` on nav entries; drops `PILL_LOCK`; repoints identity endpoints. |
| `deliverables/CSWeb/capi-portal/build_portal.py` | Imports `portal_shell`; loses its cloned `_ico`/`_NAV`/`_sidebar`/`_CRUMBS`/`_crumbs_html`/`_PILL_*`/`shell` (lines ~692–804); gains `--check`. |
| `deliverables/CSWeb/csweb-dashboard-gen.py` | `OUT` moves to the portal tree; `seg` hrefs repoint; stale `<nav>` at line 581 removed. |
| `deliverables/CSWeb/csweb-map-gen.py` | Default `--out` moves to the portal tree; `seg` hrefs repoint. |
| `deliverables/CSWeb/csweb-responses-gen.py` | `index_html()` renders through `portal_shell`; index writes to the portal tree; the 149 payload files stay put. |
| `deliverables/CSWeb/auth/acl.php` | Four new prefix rules, before the generic `/projects/` entry. |
| `deliverables/CSWeb/auth/test_acl.php` | New positive/negative cases and an ordering assertion. |
| `deliverables/CSWeb/admin/index.php` | Requires the generated shell partial instead of its hand-written chrome. |
| `deliverables/CSWeb/nginx/capi.asiansocial.org.conf` | `location = /docs/admin/` redirect; `location /projects/uhc-y2/admin/` proxy. |

**Deleted**

| File | Why |
|---|---|
| `deliverables/CSWeb/capi-portal/portal_shell.py` | Byte-identical duplicate of the root module. |
| `deliverables/CSWeb/capi-portal/portal.css` | Stale duplicate — 13 lines behind the root copy. |
| `capi-www:/projects/uhc-y2/monitoring/index.html` (signpost) | Replaced by the live dashboard at the same URL. |
| `capi-www:/projects/uhc-y2/data/index.html` (signpost) | Replaced by the live data room at the same URL. |

---

# SLICE 1 — Shell consolidation (no URL changes)

### Task 1: Give `portal_shell.py` a CSS mode and a nav permission model

**Files:**
- Modify: `deliverables/CSWeb/portal_shell.py:59-80` (the `_NAV` model), `:90-108` (`sidebar`), `:154-167` (`head`)
- Test: `deliverables/CSWeb/test_portal_shell.py` (create)

**Interfaces:**
- Consumes: nothing.
- Produces: `head(title, desc="", extra_css="", robots="noindex", css="inline")` — `css` is `"inline"` (current behaviour, emits `<style>`) or `"link"` (emits `<link rel="stylesheet" href="/portal.css">`). `sidebar(active, base="")` now emits `data-perm="<perm>"` on entries that require one. `NAV_PERMS: dict[str, str]` maps a nav href to the permission `acl.php` requires for it.

- [ ] **Step 1: Write the failing test**

Create `deliverables/CSWeb/test_portal_shell.py`:

```python
# -*- coding: utf-8 -*-
"""Unit tests for the shared shell. Plain script, stdlib only.

    python test_portal_shell.py      # exit 0 = all pass
"""
import sys
import portal_shell as PS

_pass = 0
_fail = 0


def check(what, got, want):
    global _pass, _fail
    if got == want:
        _pass += 1
        return
    _fail += 1
    print("FAIL  %-52s got=%r want=%r" % (what, got, want))


def contains(what, haystack, needle):
    check(what, needle in haystack, True)


def missing(what, haystack, needle):
    check(what, needle in haystack, False)


# --- css mode --------------------------------------------------------------
h_inline = PS.head("T", css="inline")
h_link = PS.head("T", css="link")
contains("inline mode emits a style block", h_inline, "<style>")
missing("inline mode has no stylesheet link", h_inline, 'rel="stylesheet"')
contains("link mode emits the stylesheet", h_link, '<link rel="stylesheet" href="/portal.css">')
missing("link mode inlines no tokens", h_link, "--verde")
check("inline is the default", PS.head("T"), h_inline)

# --- nav permission model --------------------------------------------------
check("monitoring needs monitoring.view", PS.NAV_PERMS.get(PS.P + "/monitoring/"), "monitoring.view")
check("data needs data.export", PS.NAV_PERMS.get(PS.P + "/data/"), "data.export")
check("overview needs nothing", PS.NAV_PERMS.get(PS.P + "/"), None)

side = PS.sidebar(PS.P + "/monitoring/")
contains("permissioned entry carries data-perm", side, 'data-perm="monitoring.view"')
missing("unpermissioned entry carries none", side,
        '<a class="" href="/projects/uhc-y2/guides/" data-perm')
contains("active entry is marked", side, 'class="on" href="/projects/uhc-y2/monitoring/"')

print("%d passed, %d failed" % (_pass, _fail))
sys.exit(1 if _fail else 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSWeb && python test_portal_shell.py`
Expected: FAIL — `AttributeError: module 'portal_shell' has no attribute 'NAV_PERMS'`

- [ ] **Step 3: Add the permission model to `_NAV`**

In `portal_shell.py`, replace the `_NAV` list (lines 59–80) — the fourth tuple slot changes from the string `"lock"` to the permission name, and plain entries use `""`:

```python
# Navigation model. The fourth slot is the permission acl.php requires for that
# path, or "" for entries any signed-in account may open. It used to hold the
# literal string "lock", which rendered a padlock on three entries regardless of
# who was looking — decorative, and misleading once the whole portal became
# gated on 2026-07-28. Now it drives data-perm, and a small script dims what
# YOUR account cannot open.
_NAV = [
    ("Project", [
        ("Overview", P + "/", _ico('<path d="M3 10.5 12 4l9 6.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>'), ""),
        ("Guides", P + "/guides/", _ico('<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M8 7h7M8 11h7"/>'), ""),
        ("Instruments", P + "/instruments/", _ico('<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>'), ""),
        ("Manual", P + "/manual/", _ico('<path d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v6h6"/>'), ""),
    ]),
    ("Operations", [
        ("Monitoring", P + "/monitoring/", _ico('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'), "monitoring.view"),
        ("Data &amp; exports", P + "/data/", _ico('<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>'), "data.export"),
        ("Tabulations", P + "/tabulations/", _ico('<path d="M3 5h18v14H3z"/><path d="M3 10h18M9 5v14M15 5v14"/>'), "tabulations.view"),
        ("Archive", P + "/archive/pretest-2026-07-15/", _ico('<rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8"/><path d="M10 12h4"/>'), ""),
    ]),
    ("Administration", [
        ("Admin console", P + "/admin/", _ico('<path d="M4 7h9M17 7h3M4 12h3M11 12h9M4 17h9M17 17h3"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="15" cy="17" r="2"/>'), "admin.system"),
    ]),
    ("Platform", [
        ("All projects", "/projects/", _ico('<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>'), ""),
        ("What we build", "/platform/", _ico('<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>'), ""),
        ("About", "/about/", _ico('<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>'), ""),
    ]),
]

NAV_PERMS = {href: perm for _, items in _NAV for _, href, _i, perm in items if perm}
```

Note the two deliberate href changes in this block: **Admin console** moves from the absolute `https://capi.asiansocial.org/docs/admin/` to `P + "/admin/"`, and **Archive** keeps its dated path (open question 3 in the spec — not resolved here).

- [ ] **Step 4: Emit `data-perm` from `sidebar()`**

Replace the loop body in `sidebar()` (lines 99–104):

```python
    for sec, items in _NAV:
        o.append('<div class="sb-sec">%s</div>' % sec)
        for label, href, icon, perm in items:
            dp = ' data-perm="%s"' % perm if perm else ""
            o.append('<a class="%s" href="%s"%s>%s<span>%s</span></a>'
                     % ("on" if href == active else "", _href(href, base), dp, icon, label))
```

The trailing `%s` that emitted the padlock span is gone; so is the `lk` local.

- [ ] **Step 5: Add the `css` mode to `head()`**

Replace `head()` (lines 154–167):

```python
def head(title, desc="", extra_css="", robots="noindex", css="inline"):
    """<!doctype> through </head>.

    css="inline" bakes portal.css into the document. That was required while the
    dashboards were served from csweb and the portal from capi — a cross-origin
    stylesheet would have needed CORS. Everything is same-origin since
    2026-07-28, so css="link" is now viable and is what the static portal uses;
    the generators stay on "inline" here so this task changes no output.
    """
    extra = ("\n<style>%s</style>" % extra_css) if extra_css else ""
    sheet = ('<style>%s</style>' % tokens_css()) if css == "inline" \
        else '<link rel="stylesheet" href="/portal.css">'
    return ('<!doctype html>\n<html lang="en">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="robots" content="%s">\n'
            '<title>%s</title>\n'
            '<meta name="description" content="%s">\n'
            '%s%s\n'
            '<link rel="icon" href="%s">\n'
            '</head>' % (robots, title, desc, sheet, extra, FAVICON))
```

Thread the parameter through `open_shell` by adding `css="inline"` to its signature and passing it to `head(title, desc, extra_css, css=css)`.

- [ ] **Step 6: Run test to verify it passes**

Run: `cd deliverables/CSWeb && python test_portal_shell.py`
Expected: `12 passed, 0 failed`, exit 0

- [ ] **Step 7: Confirm the generators still emit byte-identical output**

The three importers must be unaffected. Run each with its existing arguments against a scratch output and diff:

Run: `cd deliverables/CSWeb && python csweb-tabulations-gen.py --out /tmp/tab-after.html && diff <(curl -s https://capi.asiansocial.org/projects/uhc-y2/tabulations/) /tmp/tab-after.html`
Expected: differences confined to the generated-at timestamp. Any structural diff means step 4 changed markup it should not have — stop and investigate.

- [ ] **Step 8: Commit**

```bash
git add deliverables/CSWeb/portal_shell.py deliverables/CSWeb/test_portal_shell.py
git commit -m "feat(portal): css mode + data-perm nav model on the shared shell"
```

---

### Task 2: Emit a generated PHP shell partial

**Files:**
- Modify: `deliverables/CSWeb/portal_shell.py` (append)
- Test: `deliverables/CSWeb/test_portal_shell.py` (append)

**Interfaces:**
- Consumes: `sidebar()`, `crumbs_html()`, `tokens_css()`, `head()` from Task 1.
- Produces: `emit_php_partial(path, active=P + "/admin/", base="")` — writes a PHP file defining `capi_shell_open(string $title, string $crumbLeaf): string` and `capi_shell_close(): string`. Returns the number of bytes written.

- [ ] **Step 1: Write the failing test**

Append to `deliverables/CSWeb/test_portal_shell.py`, above the final `print`:

```python
# --- generated php partial -------------------------------------------------
import os
import tempfile

_tmp = os.path.join(tempfile.gettempdir(), "capi-shell-test.php")
_n = PS.emit_php_partial(_tmp)
with open(_tmp, encoding="utf-8") as _fh:
    _php = _fh.read()

check("emit reports the byte count", _n, len(_php.encode("utf-8")))
contains("partial opens with a php tag", _php[:5], "<?php")
contains("partial warns against editing", _php, "GENERATED by portal_shell.py")
contains("partial defines the open helper", _php, "function capi_shell_open(")
contains("partial defines the close helper", _php, "function capi_shell_close(")
contains("partial carries the real sidebar", _php, 'class="sb-brand"')
contains("partial marks admin active", _php, 'class="on" href="/projects/uhc-y2/admin/"')
missing("nowdoc body cannot terminate early", _php, "\nHTML;\nHTML;")
os.unlink(_tmp)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSWeb && python test_portal_shell.py`
Expected: FAIL — `AttributeError: module 'portal_shell' has no attribute 'emit_php_partial'`

- [ ] **Step 3: Implement `emit_php_partial`**

Append to `portal_shell.py`:

```python
_PHP_TEMPLATE = """<?php
// GENERATED by portal_shell.py -- do not edit. Regenerate with:
//     python -c "import portal_shell; portal_shell.emit_php_partial('%(path)s')"
//
// Why this file exists: admin/index.php is PHP and portal_shell.py is Python,
// and hand-copying the nav into PHP is exactly how the console ended up with
// five different chromes. The markup keeps ONE source; this is a mechanical
// transcription of it, rewritten on every deploy.
declare(strict_types=1);

const CAPI_SHELL_HEAD = <<<'CAPIHTML'
%(head)s
CAPIHTML;

const CAPI_SHELL_SIDEBAR = <<<'CAPIHTML'
%(sidebar)s
CAPIHTML;

const CAPI_SHELL_CRUMB_PREFIX = <<<'CAPIHTML'
%(crumbs)s
CAPIHTML;

function capi_shell_open(string $title, string $crumbLeaf): string
{
    $t = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
    $l = htmlspecialchars($crumbLeaf, ENT_QUOTES, 'UTF-8');
    $head = str_replace('__CAPI_TITLE__', $t, CAPI_SHELL_HEAD);
    return $head . "\\n<body>\\n<div class=\\"app\\">\\n" . CAPI_SHELL_SIDEBAR
        . "\\n<div class=\\"main\\">\\n<div class=\\"topbar\\"><div class=\\"crumbs\\">"
        . CAPI_SHELL_CRUMB_PREFIX . '<span class="sep">/</span><span class="cur">' . $l
        . "</span></div>"
        . '<div class="tb-right"><span class="tb-user" id="tbUser"></span></div></div>'
        . "\\n<div class=\\"canvas\\">\\n";
}

function capi_shell_close(): string
{
    return "\\n</div>\\n</div>\\n</div>\\n" . CAPI_SHELL_SIGNOUT_JS . "\\n</body>\\n</html>\\n";
}

const CAPI_SHELL_SIGNOUT_JS = <<<'CAPIHTML'
%(signout)s
CAPIHTML;
"""


def emit_php_partial(path, active=P + "/admin/", base=""):
    """Write the shell as a generated PHP include for admin/index.php.

    Nowdoc (<<<'CAPIHTML') is used deliberately: it does not interpolate, so
    markup containing $ or backslashes survives untouched. sidebar() joins
    without newlines, so no emitted line can collide with the terminator.
    """
    body = _PHP_TEMPLATE % {
        "path": path.replace("\\", "/"),
        "head": head("__CAPI_TITLE__", "", css="link"),
        "sidebar": sidebar(active, base),
        "crumbs": crumbs_html([("Console", _href("/", base)),
                               ("UHC Survey Year 2", _href(P + "/", base))], ""),
        "signout": SIGNOUT_JS,
    }
    for chunk, name in ((body, "partial"),):
        if "\nCAPIHTML;\nCAPIHTML;" in chunk:
            raise ValueError("%s: nowdoc terminator collision" % name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return len(body.encode("utf-8"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSWeb && python test_portal_shell.py`
Expected: `20 passed, 0 failed`, exit 0

- [ ] **Step 5: Verify the generated PHP actually parses**

Run: `cd deliverables/CSWeb && python -c "import portal_shell; portal_shell.emit_php_partial('/tmp/shell.php')" && php -l /tmp/shell.php`
Expected: `No syntax errors detected in /tmp/shell.php`

This step is the one that matters — a partial that passes the string assertions but does not parse is worse than useless.

- [ ] **Step 6: Commit**

```bash
git add deliverables/CSWeb/portal_shell.py deliverables/CSWeb/test_portal_shell.py
git commit -m "feat(portal): emit a generated PHP shell partial for the admin console"
```

---

### Task 3: Point `build_portal.py` at the shared shell and delete the clone

**Files:**
- Modify: `deliverables/CSWeb/capi-portal/build_portal.py:36` (imports), `:692-804` (the clone), and the `shell()` call sites
- Delete: `deliverables/CSWeb/capi-portal/portal_shell.py`, `deliverables/CSWeb/capi-portal/portal.css`

**Interfaces:**
- Consumes: `portal_shell.open_shell / close_shell / sidebar / crumbs_html / head / PILL_LIVE / P / NAV_PERMS` from Tasks 1–2.
- Produces: `build_portal.py --check` — exits non-zero if the module defines its own chrome again.

- [ ] **Step 1: Write the failing test**

Add to `build_portal.py` a `--check` mode. First write the assertion that must hold, as a shell test in `deliverables/CSWeb/ops/verify-chrome.sh` (create):

```bash
#!/usr/bin/env bash
# One chrome, one stylesheet. This script exists because the console had two
# copies of portal.css that silently diverged: /opt/portal.css carried a mobile
# topbar fix that /opt/app/capi-www/portal.css did not, so every portal page
# scrolled sideways on a phone while the dashboard behaved. Found 2026-08-09.
set -euo pipefail

REPO="${1:?usage: verify-chrome.sh <repo-CSWeb-dir> [ssh-target]}"
SSH="${2:-root@207.148.65.115}"
KEY="${KEY:-$HOME/.ssh/aspsi-csweb}"
fails=0

say() { printf '%-58s %s\n' "$1" "$2"; }

# 1. the repo must hold exactly one of each
for stray in "$REPO/capi-portal/portal_shell.py" "$REPO/capi-portal/portal.css"; do
  if [ -e "$stray" ]; then say "stray duplicate $stray" "FAIL"; fails=$((fails+1));
  else say "no duplicate $(basename "$stray")" "ok"; fi
done

# 2. build_portal.py must not have regrown its own chrome
if grep -qE '^_NAV = \[|^def _sidebar\(|^_PILL_LOCK' "$REPO/capi-portal/build_portal.py"; then
  say "build_portal.py defines its own chrome" "FAIL"; fails=$((fails+1))
else
  say "build_portal.py has no cloned chrome" "ok"
fi

# 3. the deployed copies must be byte-identical to the repo
local_css=$(md5sum "$REPO/portal.css" | cut -d' ' -f1)
remote=$(ssh -i "$KEY" -o StrictHostKeyChecking=no "$SSH" \
  'md5sum /opt/portal.css /opt/app/capi-www/portal.css /opt/portal_shell.py' 2>/dev/null)
for want in /opt/portal.css /opt/app/capi-www/portal.css; do
  got=$(echo "$remote" | awk -v f="$want" '$2==f {print $1}')
  if [ "$got" = "$local_css" ]; then say "$want matches repo" "ok";
  else say "$want DIVERGED ($got)" "FAIL"; fails=$((fails+1)); fi
done

local_shell=$(md5sum "$REPO/portal_shell.py" | cut -d' ' -f1)
got=$(echo "$remote" | awk '$2=="/opt/portal_shell.py" {print $1}')
if [ "$got" = "$local_shell" ]; then say "/opt/portal_shell.py matches repo" "ok";
else say "/opt/portal_shell.py DIVERGED ($got)" "FAIL"; fails=$((fails+1)); fi

echo
if [ "$fails" -eq 0 ]; then echo "chrome verified: one shell, one stylesheet"; exit 0; fi
echo "$fails check(s) failed"; exit 1
```

- [ ] **Step 2: Run it to verify it fails**

Run: `chmod +x deliverables/CSWeb/ops/verify-chrome.sh && deliverables/CSWeb/ops/verify-chrome.sh deliverables/CSWeb`
Expected: FAIL on `stray duplicate .../capi-portal/portal_shell.py`, `stray duplicate .../capi-portal/portal.css`, `build_portal.py defines its own chrome`, and `/opt/app/capi-www/portal.css DIVERGED`.

- [ ] **Step 3: Import the shared shell in `build_portal.py`**

Replace line 36 (`import argparse, os, re, shutil, subprocess, sys, datetime`) with:

```python
import argparse, os, re, shutil, subprocess, sys, datetime

# The shared chrome lives one directory up, beside the on-box generators that
# also import it. Inserting the parent on sys.path keeps ONE copy of the module
# rather than a build-time duplicate — the duplicate is how portal.css drifted.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import portal_shell as PS
```

- [ ] **Step 4: Delete the cloned chrome and re-point `shell()`**

Delete lines 692–804 of `build_portal.py` — `_ico`, `_NAV`, `_sidebar`, `_CRUMBS`, `_crumbs_html`, `_PILL_LIVE`, `_PILL_LOCK` and `shell`. Replace with:

```python
# Crumb trails for the authored pages. The shell itself comes from portal_shell.
_CRUMBS = {
    "/": [("Console", None)],
    "/projects/": [("Projects", None)],
    "/platform/": [("Platform", None), ("What we build", None)],
    "/about/": [("Platform", None), ("About", None)],
    P + "/": [("Projects", "/projects/"), ("UHC Survey Year 2", None)],
    P + "/guides/": [("UHC Survey Year 2", P + "/"), ("Guides", None)],
    P + "/manual/": [("UHC Survey Year 2", P + "/"), ("Manual", None)],
    P + "/instruments/": [("UHC Survey Year 2", P + "/"), ("Instruments", None)],
    P + "/tabulations/": [("UHC Survey Year 2", P + "/"), ("Tabulations", None)],
}


def tiles(items):
    return '<div class="tiles">%s</div>' % "".join(
        '<div class="tile"><div class="k">%s</div><div class="v">%s</div><div class="s">%s</div></div>'
        % t for t in items)


def shell(title, desc, body, crumb="", active=""):
    """App shell. Markup and CSS both come from portal_shell; this function is
    now only a crumb lookup and a css-mode choice.

    css="link" because these pages are static files served by capi-www and a
    shared stylesheet is cached once for the whole site. The on-box generators
    keep css="inline" — see portal_shell.head().
    """
    return (PS.open_shell(title, desc,
                          active=active,
                          crumbs=_CRUMBS.get(active) or [("ASPSI CAPI", None)],
                          tb_right=PS.PILL_LIVE,
                          css="link")
            + body
            + PS.close_shell())
```

Note `_CRUMBS` loses its `monitoring/` and `data/` entries — those pages stop being authored here in Slices 3 and 4, and leaving dead keys invites someone to re-add the pages.

- [ ] **Step 5: Add the `--check` mode**

In `build_portal.py`'s argument parser, add:

```python
    ap.add_argument("--check", action="store_true",
                    help="assert the shared chrome is in use, then exit")
```

and immediately after parsing:

```python
    if a.check:
        import inspect
        src = inspect.getsource(sys.modules[__name__])
        bad = [n for n in ("\n_NAV = [", "\ndef _sidebar(", "\n_PILL_LOCK") if n in src]
        if bad:
            print("FAIL: build_portal.py has regrown its own chrome: %s" % ", ".join(bad))
            sys.exit(1)
        print("ok: chrome comes from portal_shell (%s)" % PS.__file__)
        sys.exit(0)
```

- [ ] **Step 6: Delete the duplicates**

```bash
git rm deliverables/CSWeb/capi-portal/portal_shell.py deliverables/CSWeb/capi-portal/portal.css
```

- [ ] **Step 7: Build and diff against what is live**

Run: `cd deliverables/CSWeb/capi-portal && python build_portal.py --check && python build_portal.py`
Expected: `--check` prints `ok: chrome comes from portal_shell`, and the build completes.

Run: `diff <(curl -s https://capi.asiansocial.org/projects/uhc-y2/guides/) build/projects/uhc-y2/guides/index.html`
Expected: the only differences are the padlock spans disappearing from the sidebar and `data-perm` attributes appearing. **Any change to page bodies means the shell swap altered content — stop.**

- [ ] **Step 8: Commit**

```bash
git add -A deliverables/CSWeb/capi-portal deliverables/CSWeb/ops/verify-chrome.sh
git commit -m "refactor(portal): build_portal imports the shared shell; delete the cloned twin"
```

---

### Task 4: Deploy Slice 1 and verify the stylesheets converge

**Files:**
- Modify: `deliverables/CSWeb/capi-portal/build_portal.py` (the `--deploy` path)

**Interfaces:**
- Consumes: `verify-chrome.sh` from Task 3.
- Produces: a deploy that also refreshes `/opt/portal_shell.py`, `/opt/portal.css` and `/opt/app/capi-www/portal.css` from the single repo copy.

- [ ] **Step 1: Copy the canonical stylesheet into the build**

In `build_portal.py`'s deploy/build step, before rsync, add:

```python
    # capi-www serves /portal.css. It must be the SAME file the on-box
    # generators inline, or the two halves of the site drift — which is exactly
    # what happened between 2026-07-28 and 2026-08-09.
    shutil.copyfile(os.path.join(os.path.dirname(PS.__file__), "portal.css"),
                    os.path.join(BUILD, "portal.css"))
```

- [ ] **Step 2: Deploy the shell module and stylesheet to `/opt/`**

```bash
scp -i ~/.ssh/aspsi-csweb deliverables/CSWeb/portal_shell.py deliverables/CSWeb/portal.css \
    root@207.148.65.115:/opt/
```

- [ ] **Step 3: Deploy the portal**

Run: `cd deliverables/CSWeb/capi-portal && python build_portal.py --deploy`

- [ ] **Step 4: Verify convergence**

Run: `deliverables/CSWeb/ops/verify-chrome.sh deliverables/CSWeb`
Expected: `chrome verified: one shell, one stylesheet`, exit 0

- [ ] **Step 5: Verify the mobile bug is gone**

Run: `python -c "print('open https://capi.asiansocial.org/projects/uhc-y2/ at 430px')"` then, using the Playwright MCP: resize to 430×900, navigate, and evaluate `document.documentElement.scrollWidth <= document.documentElement.clientWidth`.
Expected: `true`. Before this task it is `false` — the topbar measured 448 px in a 430 px window.

- [ ] **Step 6: Commit**

```bash
git add deliverables/CSWeb/capi-portal/build_portal.py
git commit -m "fix(portal): ship one portal.css to both docroots; closes the mobile topbar overflow"
```

---

# SLICE 2 — Chrome defects (no URL changes)

### Task 5: Retire the misleading lock pill and dim by permission

**Files:**
- Modify: `deliverables/CSWeb/portal_shell.py:151` (`PILL_LOCK`), `:122-148` (chip CSS and JS)
- Modify: `deliverables/CSWeb/csweb-dashboard-gen.py:1903`, `deliverables/CSWeb/csweb-map-gen.py:1166`
- Test: `deliverables/CSWeb/test_portal_shell.py` (append)

**Interfaces:**
- Consumes: `NAV_PERMS`, `data-perm` markup from Task 1.
- Produces: `PERM_DIM_JS` — a script that fetches `/docs/idp/me` and adds `class="sb-off"` to nav entries whose `data-perm` the account lacks. `PILL_LOCK` is **removed**; referencing it must raise `AttributeError`.

- [ ] **Step 1: Write the failing test**

Append to `test_portal_shell.py`:

```python
# --- the lock pill is gone, dimming replaces it ----------------------------
check("PILL_LOCK is removed", hasattr(PS, "PILL_LOCK"), False)
check("PILL_LIVE survives", "Fieldwork live" in PS.PILL_LIVE, True)
contains("dim script reads the session", PS.PERM_DIM_JS, "/docs/idp/me")
contains("dim script keys off data-perm", PS.PERM_DIM_JS, "data-perm")
contains("close_shell ships the dim script", PS.close_shell(), "data-perm")
contains("signout uses the idp endpoint", PS.SIGNOUT_JS, "/docs/idp/me")
contains("signout links the idp logout", PS.SIGNOUT_JS, "/docs/idp/logout")
missing("no legacy whoami", PS.SIGNOUT_JS, "whoami.php")
missing("no legacy logout", PS.SIGNOUT_JS, "/docs/auth/logout")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSWeb && python test_portal_shell.py`
Expected: FAIL on `PILL_LOCK is removed` and `AttributeError: PERM_DIM_JS`.

- [ ] **Step 3: Delete `PILL_LOCK` and repoint the identity endpoints**

In `portal_shell.py`, delete the `PILL_LOCK` line entirely and replace `SIGNOUT_JS` (lines 138–148):

```python
# Fills the identity chip from the session. /docs/idp/me and /docs/idp/logout are
# the canonical endpoints since the 2026-08-08 cutover; whoami.php and
# /docs/auth/logout are legacy shims kept alive only so old bookmarks resolve.
#
# me.php returns a FLAT object -- {signed_in, user, roles, perms, must_change,
# can{}, tier, logout} -- NOT the {ok,data,request_id} envelope the admin API
# uses. Reading d.data here would silently blank the chip on every page,
# because every one of these fetches ends in an empty .catch().
# `tier` is emitted by me.php:51-55 precisely so this chip keeps working.
SIGNOUT_JS = (
    '<script>(function(){var e=document.getElementById("tbUser");if(!e)return;'
    'fetch("/docs/idp/me",{credentials:"same-origin"})'
    '.then(function(r){return r.ok?r.json():null})'
    '.then(function(d){if(!d||!d.signed_in)return;'
    'var u=document.createElement("b");u.textContent=d.user;'
    'var t=document.createElement("span");t.className="tier";'
    't.textContent=d.tier||"user";'
    'var a=document.createElement("a");a.href=d.logout||"/docs/idp/logout";'
    'a.textContent="Sign out";'
    'e.appendChild(u);e.appendChild(t);e.appendChild(a);e.className="tb-user on";'
    '}).catch(function(){});})();</script>'
)
```

- [ ] **Step 4: Add the permission-dimming script and its CSS**

Append to `portal_shell.py`:

```python
# A padlock on a nav entry told every reader the same thing regardless of who
# they were, which is decoration. This dims the entries YOUR account cannot
# open. It fails open: if /docs/idp/me is unreachable, nothing is dimmed and
# the edge still enforces — a cosmetic script must never be the gate.
PERM_DIM_CSS = (
    '.sb-nav a.sb-off{opacity:.45}'
    '.sb-nav a.sb-off:after{content:"\\1F512";margin-left:auto;font-size:11px}'
)

PERM_DIM_JS = (
    '<script>(function(){'
    'var links=document.querySelectorAll(".sb-nav a[data-perm]");if(!links.length)return;'
    'fetch("/docs/idp/me",{credentials:"same-origin"})'
    '.then(function(r){return r.ok?r.json():null})'
    '.then(function(d){if(!d||!d.signed_in)return;'
    'var held=d.perms||[];'
    'Array.prototype.forEach.call(links,function(a){'
    'if(held.indexOf(a.getAttribute("data-perm"))<0){a.className+=" sb-off";'
    'a.setAttribute("title","Your account does not have access to this");}});'
    '}).catch(function(){});})();</script>'
)
```

Append `PERM_DIM_CSS` to the return value of `tokens_css()` alongside `SIGNOUT_CSS`, and emit `PERM_DIM_JS` from `close_shell()` next to `SIGNOUT_JS`.

- [ ] **Step 5: Replace `PS.PILL_LOCK` at both call sites**

`csweb-dashboard-gen.py:1903` and `csweb-map-gen.py:1166` both read `tb_right = seg + PS.PILL_LOCK`. Change both to:

```python
    tb_right = seg
```

The segmented Dashboard/Map control stays; the pill goes. The identity chip that `open_shell` already appends to `.tb-right` now carries the "who am I / sign out" job the pill was pretending to do.

- [ ] **Step 6: Run test to verify it passes**

Run: `cd deliverables/CSWeb && python test_portal_shell.py`
Expected: `29 passed, 0 failed`, exit 0

- [ ] **Step 7: Verify the dim behaves for a real account**

Create a scratch `field_supervisor` account, sign in, load `/projects/uhc-y2/`, and confirm **Data & exports** and **Admin console** are dimmed with a tooltip while **Monitoring** is not. Then delete the scratch account.
Expected: dimming matches the account's permission set exactly.

- [ ] **Step 8: Commit**

```bash
git add deliverables/CSWeb/portal_shell.py deliverables/CSWeb/test_portal_shell.py \
        deliverables/CSWeb/csweb-dashboard-gen.py deliverables/CSWeb/csweb-map-gen.py
git commit -m "fix(portal): retire the misleading lock pill; dim nav by actual permission"
```

---

### Task 6: Relabel the surviving badges and remove the stale second nav

**Files:**
- Modify: `deliverables/CSWeb/capi-portal/build_portal.py:187`, `:332-383`
- Modify: `deliverables/CSWeb/csweb-dashboard-gen.py:581`, `:666`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing consumed downstream.

- [ ] **Step 1: Confirm the stale nav actually renders**

Run: `curl -s https://capi.asiansocial.org/docs/dashboard.html | grep -c 'Site sections'`
Expected: `0` if it is dead code, `1` if it renders. Record which. If it renders, it is a second navigation contradicting the sidebar and must be removed; if it does not, delete the dead source anyway.

- [ ] **Step 2: Remove the stale nav**

Delete the `<nav aria-label="Site sections">…</nav>` block at `csweb-dashboard-gen.py:581`, and in the footer at line 666 repoint `/docs/map.html` to `/projects/uhc-y2/monitoring/map/`.

- [ ] **Step 3: Relabel the badges that survive**

At `build_portal.py:187`, the `ROLES` badge helper, change the label:

```python
        badge = '<span class="badge soon">separate login</span>' if gate else ""
```

and update the two `ROLES` gate flags at lines 174 and 178 from `"login"` to `""` — those rows now point at pages inside the same sign-in, so the badge is wrong there.

In the F2 admin and CSWeb cards (`build_portal.py:349`, `:354`), change `login needed` to `separate login`. These two are genuinely behind different credentials, which is the fact worth surfacing.

- [ ] **Step 4: Verify no "login needed" text survives**

Run: `cd deliverables/CSWeb && grep -rn "login needed" capi-portal/build_portal.py`
Expected: no matches.

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSWeb/capi-portal/build_portal.py deliverables/CSWeb/csweb-dashboard-gen.py
git commit -m "fix(portal): badges say 'separate login' where that is true; drop the stale second nav"
```

---

### Task 7: Render the data room through the shared shell

**Files:**
- Modify: `deliverables/CSWeb/csweb-responses-gen.py:15` (docstring), `:306` (`index_html`), `:471`

**Interfaces:**
- Consumes: `PS.open_shell / close_shell / PILL_LIVE` from Tasks 1 and 5.
- Produces: `index_html(...)` returns a full document wrapped in the shared shell. Its signature is unchanged.

- [ ] **Step 1: Import the shell**

Add near the top of `csweb-responses-gen.py`, matching the idiom at `csweb-dashboard-gen.py:42`:

```python
import portal_shell as PS   # page chrome — /opt/portal_shell.py + portal.css on the box
```

- [ ] **Step 2: Wrap the existing body**

`index_html()` currently returns a whole bespoke document. Keep everything it builds *inside* `<body>` as the body, and replace its own `<!doctype>`/`<head>`/header/footer with:

```python
    return (PS.open_shell("Data room — UHC Survey Y2",
                          "Analysis-ready exports for UHC Survey Year 2, rebuilt every two minutes.",
                          active=PS.P + "/data/",
                          crumbs=[("UHC Survey Year 2", PS.P + "/"), ("Data &amp; exports", None)],
                          tb_right=PS.PILL_LIVE,
                          extra_css=_PAGE_CSS)
            + body
            + PS.close_shell())
```

Move the page-specific rules the old document carried in its `<style>` block into a module-level `_PAGE_CSS` string and pass it as `extra_css`, exactly as `csweb-tabulations-gen.py:525` does.

- [ ] **Step 3: Generate to a scratch path and compare**

Run: `cd deliverables/CSWeb && python csweb-responses-gen.py --out-dir /tmp/dataroom`
Expected: the run succeeds and `/tmp/dataroom/index.html` exists.

- [ ] **Step 4: Verify the file list is intact**

Run: `grep -c 'href="' /tmp/dataroom/index.html` and compare with `curl -s https://capi.asiansocial.org/docs/data/ | grep -c 'href="'`
Expected: the new count is greater than or equal to the old (the shell adds nav links). **A lower count means download links were lost — stop.**

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSWeb/csweb-responses-gen.py
git commit -m "refactor(dataroom): render the index through the shared shell"
```

---

# SLICE 3 — Monitoring and Map move to the portal

### Task 8: Add the ACL rules first

**Files:**
- Modify: `deliverables/CSWeb/auth/acl.php:144-185` (`ACL_PREFIX`)
- Test: `deliverables/CSWeb/auth/test_acl.php`

**Interfaces:**
- Consumes: nothing.
- Produces: `acl_required_perm('/projects/uhc-y2/monitoring/')` returns `'monitoring.view'`.

The rules go in **before** the URLs exist. A path that 403s because it is not yet built is a deploy ordering problem; a path that serves respondent data because its rule was added second is an incident.

- [ ] **Step 1: Write the failing test**

In `test_acl.php`, add to the `$paths` map:

```php
    // the console's live pages, at their portal URLs (2026-08-09 unification)
    '/projects/uhc-y2/monitoring/'            => 'monitoring.view',
    '/projects/uhc-y2/monitoring/map/'        => 'monitoring.view',
    '/projects/uhc-y2/data/'                  => 'data.export',
    '/projects/uhc-y2/admin/'                 => 'admin.system',
    '/projects/uhc-y2/admin/users'            => 'admin.users',
    // the payload does NOT move: these must keep resolving under /docs/
    '/docs/data/f1_responses.csv'             => 'data.export',
    '/docs/data/tabulations-preview.json'     => 'tabulations.view',
    // unrelated project paths still fall through to the generic rule
    '/projects/uhc-y2/guides/'                => 'AUTH',
    '/projects/uhc-y2/instruments/f1/'        => 'AUTH',
```

and add an explicit ordering assertion after the loop:

```php
// Ordering: ACL_PREFIX is first-match-wins, so the admin users rule must be
// listed before the generic admin rule and both before '/projects/'. Asserting
// the resolved values is not enough — assert the ORDER, because a later edit
// that appends rather than inserts would still pass the value checks above
// while quietly granting admin.system where admin.users was required.
$order = array_map(static fn(array $r): string => $r[0], ACL_PREFIX);
$ixUsers = array_search('/projects/uhc-y2/admin/users', $order, true);
$ixAdmin = array_search('/projects/uhc-y2/admin/', $order, true);
$ixProj  = array_search('/projects/', $order, true);
check('admin/users precedes admin/', $ixUsers !== false && $ixUsers < $ixAdmin, true);
check('admin/ precedes /projects/',  $ixAdmin !== false && $ixAdmin < $ixProj, true);
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSWeb/auth && php test_acl.php`
Expected: FAIL — the five new portal paths resolve to `AUTH` (they match the generic `/projects/` rule), not to their permissions.

- [ ] **Step 3: Insert the rules in the right position**

In `acl.php`, inside `ACL_PREFIX`, immediately **before** the existing `['/projects/uhc-y2/tabulations/', 'tabulations.view'],` line:

```php
    // The console's live pages now live at portal URLs (2026-08-09). These MUST
    // precede the generic '/projects/' rule below, which is AUTH — first match
    // wins, so a rule appended after it would never be reached and the data
    // room would be readable by anyone with any account.
    ['/projects/uhc-y2/monitoring/', 'monitoring.view'],
    ['/projects/uhc-y2/data/',       'data.export'],
    ['/projects/uhc-y2/admin/users', 'admin.users'],
    ['/projects/uhc-y2/admin/',      'admin.system'],
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSWeb/auth && php test_acl.php`
Expected: `196 passed, 0 failed` (185 existing + 9 paths + 2 ordering), exit 0

- [ ] **Step 5: Deploy the ACL alone and re-run the existing gate check**

```bash
scp -i ~/.ssh/aspsi-csweb deliverables/CSWeb/auth/acl.php root@207.148.65.115:/var/www/private/capi-auth/acl.php
deliverables/CSWeb/ops/cutover-check.sh
```
Expected: 25/25. The new rules point at URLs that 404 today, which is correct and harmless.

- [ ] **Step 6: Commit**

```bash
git add deliverables/CSWeb/auth/acl.php deliverables/CSWeb/auth/test_acl.php
git commit -m "feat(acl): rules for the console's portal URLs, ahead of the move"
```

---

### Task 9: Move the dashboard and map output into the portal tree

**Files:**
- Modify: `deliverables/CSWeb/csweb-dashboard-gen.py:48` (`OUT`), `:1901-1902` (`seg`)
- Modify: `deliverables/CSWeb/csweb-map-gen.py:63` (`--out` default), `:1164-1165` (`seg`)

**Interfaces:**
- Consumes: ACL rules from Task 8.
- Produces: the dashboard at `/projects/uhc-y2/monitoring/`, the map at `/projects/uhc-y2/monitoring/map/`.

- [ ] **Step 1: Repoint the dashboard output and its active nav entry**

`csweb-dashboard-gen.py:48`:

```python
# Writes into the STATIC PORTAL docroot, not the Apache one. This is the pattern
# csweb-tabulations-gen.py has used since 2026-07-28: a live, database-backed
# page published at its project URL, so the nav entry IS the page.
OUT = "/opt/app/capi-www/projects/uhc-y2/monitoring/index.html"
```

and at line 1901:

```python
    seg = ('<div class="tb-seg"><a class="on" href="/projects/uhc-y2/monitoring/">Sync Dashboard</a>'
           '<a href="/projects/uhc-y2/monitoring/map/">Map</a></div>')
```

Confirm the `open_shell(... active=...)` call in this file passes `active=PS.P + "/monitoring/"` so the sidebar highlights correctly.

- [ ] **Step 2: Repoint the map output and its segment**

`csweb-map-gen.py:63` — change the argparse default for `--out` to `/opt/app/capi-www/projects/uhc-y2/monitoring/map/index.html`, and at line 1164:

```python
    seg = ('<div class="tb-seg"><a href="/projects/uhc-y2/monitoring/">Sync Dashboard</a>'
           '<a class="on" href="/projects/uhc-y2/monitoring/map/">Map</a></div>')
```

The map's `active` must also be `PS.P + "/monitoring/"` — one nav entry covers both views.

- [ ] **Step 3: Create the target directories on the box**

```bash
ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115 \
  'mkdir -p /opt/app/capi-www/projects/uhc-y2/monitoring/map'
```

- [ ] **Step 4: Deploy the generators and run them once**

```bash
scp -i ~/.ssh/aspsi-csweb deliverables/CSWeb/csweb-dashboard-gen.py \
    deliverables/CSWeb/csweb-map-gen.py root@207.148.65.115:/opt/
ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115 \
  'cd /opt/app && python3 /opt/csweb-dashboard-gen.py && python3 /opt/csweb-map-gen.py'
```
Expected: both write without error.

- [ ] **Step 5: Verify both URLs serve, with the right gate**

Run: `deliverables/CSWeb/ops/probe-surfaces.sh` (created in Task 12; until then, probe by hand with a `field_supervisor` cookie).
Expected: `/projects/uhc-y2/monitoring/` and `…/map/` both `200` for an account holding `monitoring.view`, `403` for one without.

- [ ] **Step 6: Confirm the old URLs still serve**

Run: `curl -sS -o /dev/null -w '%{http_code}\n' https://capi.asiansocial.org/docs/dashboard.html`
Expected: `200`. The old files are untouched at this point — the redirects come in Task 10, so this task is fully revertible by re-pointing `OUT`.

- [ ] **Step 7: Commit**

```bash
git add deliverables/CSWeb/csweb-dashboard-gen.py deliverables/CSWeb/csweb-map-gen.py
git commit -m "feat(monitoring): publish the dashboard and map at their portal URLs"
```

---

### Task 10: Redirect the old monitoring URLs and delete the signpost

**Files:**
- Modify: `deliverables/CSWeb/nginx/capi.asiansocial.org.conf` (Apache vhost section is in the lamp stack — see step 2)
- Delete: `capi-www:/projects/uhc-y2/monitoring/` signpost (overwritten by Task 9's generator output)
- Modify: `deliverables/CSWeb/capi-portal/build_portal.py` (drop `monitoring_index()` and its `write()` call)

**Interfaces:**
- Consumes: Task 9's live pages.
- Produces: `/docs/dashboard.html` and `/docs/map.html` return `301`.

- [ ] **Step 1: Stop building the signpost**

In `build_portal.py`, delete the `monitoring_index()` function (lines ~327–375) and its `write("projects/uhc-y2/monitoring/index.html", monitoring_index())` call. The generator now owns that path.

- [ ] **Step 2: Add the Apache redirects**

In the lamp Apache vhost (`/opt/app/lamp/apache/conf/…`, the same file the cutover script edits), inside the `capi` vhost:

```apache
    # Moved to project URLs 2026-08-09. Anchored deliberately: a bare
    # "Redirect 301 /docs/data/" is a PREFIX rule and would bounce all 149
    # export downloads to the index page.
    Redirect      301 /docs/dashboard.html https://capi.asiansocial.org/projects/uhc-y2/monitoring/
    Redirect      301 /docs/map.html       https://capi.asiansocial.org/projects/uhc-y2/monitoring/map/
```

- [ ] **Step 3: Reload Apache and verify the redirects**

```bash
ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115 'docker exec lamp-php8 apachectl -t && docker exec lamp-php8 apachectl graceful'
curl -sS -o /dev/null -w '%{http_code} %{redirect_url}\n' https://capi.asiansocial.org/docs/dashboard.html
```
Expected: `301 https://capi.asiansocial.org/projects/uhc-y2/monitoring/`

- [ ] **Step 4: Verify no redirect chain**

Run: `curl -sSL -o /dev/null -w 'redirects=%{num_redirects} final=%{url_effective} code=%{http_code}\n' https://capi.asiansocial.org/docs/map.html`
Expected: `redirects=1`, final URL is the portal map, `code=200` (with a session) or `302` to sign-in (without).

- [ ] **Step 5: Rebuild and deploy the portal**

Run: `cd deliverables/CSWeb/capi-portal && python build_portal.py --deploy`

`--deploy` is `scp -q -i KEY -r` (`build_portal.py:677-680`), **not** rsync, and carries no `--delete`. It merges: files present in `build/` overwrite their counterparts and everything else on the box is left alone. So once the builder stops emitting `projects/uhc-y2/monitoring/index.html`, the generator's live page survives the deploy untouched. No exclude list is needed — but do not "improve" this into `rsync --delete` later without one, because `monitoring/`, `data/` and `tabulations/` are all generator-owned and would be wiped every deploy.

Expected: the deploy prints its file list and `projects/uhc-y2/monitoring/index.html` is absent from it.

- [ ] **Step 5b: Confirm the live page survived the deploy**

Run: `curl -sS https://capi.asiansocial.org/projects/uhc-y2/monitoring/ | grep -c "tb-seg"`
Expected: `1` — the segmented Dashboard/Map control, which only the generator emits. `0` means the deploy overwrote the live page with a stale build artefact.

- [ ] **Step 6: Commit**

```bash
git add deliverables/CSWeb/capi-portal/build_portal.py deliverables/CSWeb/nginx/
git commit -m "feat(monitoring): 301 the old /docs URLs; delete the signpost page"
```

---

# SLICE 4 — Data room moves to the portal

### Task 11: Publish the data room index at its portal URL

**Files:**
- Modify: `deliverables/CSWeb/csweb-responses-gen.py:471`
- Modify: `deliverables/CSWeb/capi-portal/build_portal.py` (drop `data_index()` and its `write()` at line 638)

**Interfaces:**
- Consumes: Task 7's shell-wrapped `index_html`, Task 8's ACL rule.
- Produces: the data room at `/projects/uhc-y2/data/`; the 149 payload files unchanged at `/docs/data/`.

- [ ] **Step 1: Split the index destination from the payload destination**

In `csweb-responses-gen.py`, add an argument and use it only for the index:

```python
    ap.add_argument("--index-out",
                    default="/opt/app/capi-www/projects/uhc-y2/data/index.html",
                    help="where the data-room PAGE goes. The 149 export FILES stay "
                         "in --out-dir under /docs/data/ — a .csv needs no chrome, "
                         "and moving them would churn every manifest and the "
                         "data.export ACL rule.")
```

and change line 471:

```python
    os.makedirs(os.path.dirname(a.index_out), exist_ok=True)
    with open(a.index_out, "w", encoding="utf-8") as f:
        f.write(index_html(manifests, generated, spss, cspro, cbook))
```

- [ ] **Step 2: Stop building the signpost**

Delete `data_index()` from `build_portal.py` and its `write("projects/uhc-y2/data/index.html", data_index())` call at line 638.

- [ ] **Step 3: Deploy and run**

```bash
scp -i ~/.ssh/aspsi-csweb deliverables/CSWeb/csweb-responses-gen.py root@207.148.65.115:/opt/
ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115 'cd /opt/app && python3 /opt/csweb-responses-gen.py'
```

- [ ] **Step 4: Verify the page moved and the payload did not**

```bash
curl -sS -o /dev/null -w 'page=%{http_code}\n' https://capi.asiansocial.org/projects/uhc-y2/data/
curl -sS -o /dev/null -w 'csv=%{http_code}\n'  https://capi.asiansocial.org/docs/data/f1_responses.csv
curl -sS -o /dev/null -w 'zip=%{http_code}\n'  https://capi.asiansocial.org/docs/data/f1-cases-spss.zip
```
Expected (with a `data.export` session): `page=200`, `csv=200`, `zip=200`.

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSWeb/csweb-responses-gen.py deliverables/CSWeb/capi-portal/build_portal.py
git commit -m "feat(dataroom): publish the index at its portal URL; payload stays at /docs/data/"
```

---

### Task 12: Redirect the bare data-room URL, and build the surface probe

**Files:**
- Create: `deliverables/CSWeb/ops/probe-surfaces.sh`
- Modify: the lamp Apache vhost

**Interfaces:**
- Consumes: everything above.
- Produces: `probe-surfaces.sh <user> <pass>` — exits non-zero if any surface answers with the wrong status for that account.

- [ ] **Step 1: Write the probe**

Create `deliverables/CSWeb/ops/probe-surfaces.sh`:

```bash
#!/usr/bin/env bash
# Role x URL probe. Signs in once, then asserts a status per surface.
#
#   probe-surfaces.sh <username> <password> <expect-file>
#
# expect-file lines:  <path> <expected-status>
# Run it before and after every URL move. The failure it exists to catch is a
# path that starts answering 200 to an account that should get 403.
set -euo pipefail

U="${1:?username}"; PW="${2:?password}"; EXPECT="${3:?expect-file}"
BASE="https://capi.asiansocial.org"
JAR=$(mktemp); trap 'rm -f "$JAR"' EXIT
fails=0

code=$(curl -sS -c "$JAR" -o /dev/null -w '%{http_code}' \
  -d "username=$U" -d "password=$PW" "$BASE/docs/idp/login")
if [ "$code" != "302" ] && [ "$code" != "200" ]; then
  echo "sign-in failed for $U (HTTP $code)"; exit 1
fi

while read -r path want; do
  [ -z "${path:-}" ] && continue
  case "$path" in \#*) continue ;; esac
  got=$(curl -sS -b "$JAR" -o /dev/null -w '%{http_code}' "$BASE$path")
  if [ "$got" = "$want" ]; then printf '%-50s %s ok\n' "$path" "$got"
  else printf '%-50s got=%s want=%s FAIL\n' "$path" "$got" "$want"; fails=$((fails+1)); fi
done < "$EXPECT"

echo
[ "$fails" -eq 0 ] && { echo "all surfaces correct for $U"; exit 0; }
echo "$fails surface(s) wrong for $U"; exit 1
```

- [ ] **Step 2: Write the expectation files**

Create `deliverables/CSWeb/ops/expect-field-supervisor.txt`:

```
/projects/uhc-y2/                    200
/projects/uhc-y2/monitoring/         200
/projects/uhc-y2/monitoring/map/     200
/projects/uhc-y2/data/               403
/docs/data/f1_responses.csv          403
/projects/uhc-y2/admin/              403
/docs/admin-portal-guide.html        200
```

Create `deliverables/CSWeb/ops/expect-owner.txt`:

```
/projects/uhc-y2/monitoring/         200
/projects/uhc-y2/monitoring/map/     200
/projects/uhc-y2/data/               200
/docs/data/f1_responses.csv          200
/docs/data/f1-cases-spss.zip         200
/docs/data/tabulations-preview.json  200
/projects/uhc-y2/admin/              200
```

- [ ] **Step 3: Add the anchored data-room redirect**

In the Apache vhost, next to Task 10's redirects:

```apache
    # ANCHORED. RedirectMatch with ^…$ so ONLY the bare directory moves; the
    # 149 downloads beneath it must keep resolving. A plain "Redirect 301
    # /docs/data/" would break every export link on the site.
    RedirectMatch 301 ^/docs/data/$ https://capi.asiansocial.org/projects/uhc-y2/data/
```

- [ ] **Step 4: Reload and run both probes**

```bash
ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115 'docker exec lamp-php8 apachectl -t && docker exec lamp-php8 apachectl graceful'
chmod +x deliverables/CSWeb/ops/probe-surfaces.sh
deliverables/CSWeb/ops/probe-surfaces.sh <scratch-supervisor> <pw> deliverables/CSWeb/ops/expect-field-supervisor.txt
deliverables/CSWeb/ops/probe-surfaces.sh cplreyes <pw> deliverables/CSWeb/ops/expect-owner.txt
```
Expected: `all surfaces correct` for both. The owner run is the one that proves hazard (a) did not happen.

- [ ] **Step 5: Delete the scratch account and commit**

```bash
git add deliverables/CSWeb/ops/
git commit -m "feat(ops): role x URL surface probe; anchored 301 for the data-room index"
```

---

# SLICE 5 — Admin console at the portal path

### Task 13: Serve the admin console from `/projects/uhc-y2/admin/`

**Files:**
- Modify: `deliverables/CSWeb/nginx/capi.asiansocial.org.conf`

**Interfaces:**
- Consumes: Task 8's `admin.system` / `admin.users` rules.
- Produces: `/projects/uhc-y2/admin/` proxied to Apache's `/docs/admin/`.

- [ ] **Step 1: Add the proxy location**

Insert **before** `location /` in the nginx vhost:

```nginx
  # The admin console is PHP and capi-www has no PHP, so it cannot simply be
  # copied into the portal tree like the dashboards were. Proxy it instead.
  #
  # There must be NO Apache-level redirect on /docs/admin/: this proxy targets
  # it directly, and a 301 there would be answered back to nginx, re-proxied,
  # and loop forever. The public /docs/admin/ redirect lives in nginx (below).
  location /projects/uhc-y2/admin/ {
    auth_request /_capi_auth;
    auth_request_set $auth_user   $upstream_http_x_auth_user;
    auth_request_set $auth_roles  $upstream_http_x_auth_roles;
    auth_request_set $auth_reason $upstream_http_x_auth_reason;
    error_page 401 = @capi_login;
    error_page 403 = @capi_denied;
    error_page 502 503 504 = @capi_authdown;

    proxy_set_header X-Auth-User  $auth_user;
    proxy_set_header X-Auth-Roles $auth_roles;
    proxy_set_header Host         $host;
    proxy_set_header X-Forwarded-Proto https;
    proxy_pass http://172.17.0.1:8080/docs/admin/;
  }

  location = /docs/admin/ {
    auth_request /_capi_auth;
    error_page 401 = @capi_login;
    return 301 https://capi.asiansocial.org/projects/uhc-y2/admin/;
  }
```

- [ ] **Step 2: Test the config before reloading**

```bash
ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115 'docker exec elestio-nginx nginx -t'
```
Expected: `syntax is ok` / `test is successful`. **Do not reload on any other output.**

- [ ] **Step 3: Reload and check for a loop**

```bash
ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115 'docker exec elestio-nginx nginx -s reload'
curl -sSL -b "$JAR" -o /dev/null -w 'redirects=%{num_redirects} code=%{http_code}\n' \
  https://capi.asiansocial.org/projects/uhc-y2/admin/
```
Expected: `redirects=0 code=200`. Anything above `0` redirects means hazard (b) has occurred — revert immediately with the backup config.

- [ ] **Step 4: Commit**

```bash
git add deliverables/CSWeb/nginx/capi.asiansocial.org.conf
git commit -m "feat(admin): serve the admin console at its portal URL"
```

---

### Task 14: Make the admin console wear the shared chrome

**Files:**
- Modify: `deliverables/CSWeb/admin/index.php:65-130`
- Modify: `deliverables/CSWeb/admin/app.js`, `boot.js` (asset paths)

**Interfaces:**
- Consumes: `capi_shell_open()` / `capi_shell_close()` from Task 2.
- Produces: an admin page whose sidebar and topbar are identical to every other surface.

- [ ] **Step 1: Deploy the generated partial**

```bash
python -c "import sys; sys.path.insert(0,'deliverables/CSWeb'); import portal_shell; portal_shell.emit_php_partial('/tmp/shell.php')"
scp -i ~/.ssh/aspsi-csweb /tmp/shell.php root@207.148.65.115:/var/www/private/capi-shell/shell.php
```

Add the same two lines to `build_portal.py --deploy` so the partial is regenerated whenever the chrome changes.

- [ ] **Step 2: Replace the hand-written shell in `index.php`**

Replace everything from `?><!doctype html>` (line 65) through the closing `</aside>` (line 116) with:

```php
require_once '/var/www/private/capi-shell/shell.php';
echo capi_shell_open('Admin — ASPSI CAPI', 'Admin');
?>
```

and replace the closing markup (from `</div>` after `#admView` to `</html>`) with:

```php
<?php echo capi_shell_close(); ?>
```

Keep the two `<link rel="stylesheet">` lines for `admin.css` only — `portal.css` now arrives via the generated head. Keep every `<script src>` tag; they are unchanged.

The admin-specific nav (Users, Roles, Sessions, Audit, Activities, Alerts, Plan, My account) becomes a **second-level nav inside the canvas**, not a replacement sidebar — the left rail is now the site's rail, the same as everywhere else.

- [ ] **Step 3: Verify the page renders and the app still boots**

Load `/projects/uhc-y2/admin/` and confirm: the site sidebar is present, `#admView` renders the Users table, and the browser console is clean.
Expected: no 404s for `ui.js`, `view-users.js` or `admin.css`; the CSRF cookies are still minted.

- [ ] **Step 4: Verify the guide link still resolves**

The sidebar's "How to use this portal" link is gone with the old rail. Add the operator guide to the admin canvas header instead, pointing at `/docs/admin-portal-guide.html` (unchanged, still `AUTH`).

- [ ] **Step 5: Commit**

```bash
git add deliverables/CSWeb/admin/index.php deliverables/CSWeb/capi-portal/build_portal.py
git commit -m "refactor(admin): adopt the generated shared shell; drop the fourth chrome"
```

---

### Task 15: Full-surface verification and cleanup

**Files:**
- Modify: `deliverables/CSWeb/ops/cutover-check.sh` (extend)
- Modify: `docs/superpowers/specs/2026-08-09-capi-console-unification-design.md` (record outcomes)

- [ ] **Step 1: Run every check**

```bash
cd deliverables/CSWeb
python test_portal_shell.py
php auth/test_acl.php
php auth/test_admin.php
php auth/test_lib.php
ops/verify-chrome.sh .
ops/cutover-check.sh
ops/probe-surfaces.sh cplreyes <pw> ops/expect-owner.txt
```
Expected: all exit 0.

- [ ] **Step 2: Confirm one chrome, everywhere**

For each of `/`, `/projects/uhc-y2/`, `/projects/uhc-y2/monitoring/`, `…/map/`, `…/data/`, `…/tabulations/`, `…/admin/`, `…/guides/` — fetch and assert the sidebar markup is byte-identical apart from the `class="on"` marker:

```bash
for p in / /projects/uhc-y2/ /projects/uhc-y2/monitoring/ /projects/uhc-y2/monitoring/map/ \
         /projects/uhc-y2/data/ /projects/uhc-y2/tabulations/ /projects/uhc-y2/admin/ \
         /projects/uhc-y2/guides/; do
  n=$(curl -sS -b "$JAR" "https://capi.asiansocial.org$p" | grep -o 'class="sb-sec"' | wc -l)
  printf '%-42s %s nav sections\n' "$p" "$n"
done
```
Expected: `4` on every line. A different count means a surface is still wearing its own chrome.

- [ ] **Step 3: Confirm the signposts are gone**

```bash
curl -sS https://capi.asiansocial.org/projects/uhc-y2/monitoring/ | grep -c "Open the dashboard"
curl -sS https://capi.asiansocial.org/projects/uhc-y2/data/       | grep -c "Open the data room"
```
Expected: `0` for both — those strings only existed on the signpost pages.

- [ ] **Step 4: Record outcomes in the spec**

Fill in the spec's §9 open questions with what was decided during execution, and note the 301 expiry date agreed with Carl.

- [ ] **Step 5: Commit**

```bash
git add -A deliverables/CSWeb docs/superpowers
git commit -m "chore(console): full-surface verification of the unification"
```

---

## Self-Review

**Spec coverage.** §3.1 → Tasks 1, 3, 4. §3.2 → Tasks 2, 14. §3.3 URL map → Tasks 9–13. §3.3 hazard (a) → Task 12 step 3, tested Task 12 step 4. §3.3 hazard (b) → Task 13, tested Task 13 step 3. §3.4 "what does not move" → Task 11 step 1 (`--index-out`), Task 12 expectation files. §3.5 → Tasks 13, 14. §4 defect 1 → Task 5. Defect 2 → Tasks 1, 5. Defect 3 → Task 6. Defect 4 → Task 7. Defect 5 → Task 5 step 3. Defect 6 → Task 4 step 5. Defect 7 → Task 6 steps 1–2. §5 ACL → Task 8. §7 testing → Tasks 3, 12, 15.

**Gap found and closed:** the spec's §7 called for a clone guard; the plan now has it twice — as `build_portal.py --check` (Task 3 step 5) and as a grep in `verify-chrome.sh` (Task 3 step 1), because the first only runs when someone runs the builder.

**Two errors found and fixed during review, both verified against the source rather than assumed:**

1. **`/docs/idp/me` returns a flat object, not the admin API's envelope.** The first draft of Task 5 read `d.data.username` and `s.permissions`. `me.php:57-75` actually returns `{signed_in, user, roles, perms, must_change, can{}, tier, logout}` at the top level. Because every one of these chip fetches ends in an empty `.catch()`, the wrong shape would not have thrown — it would have silently blanked the identity chip on every page in the console, and the permission dimming would have dimmed nothing while appearing to work. Corrected in Task 5 steps 3 and 4.
2. **`--deploy` is `scp -r`, not rsync.** Task 10 originally warned about `rsync --delete` wiping generator-owned files. `build_portal.py:677-680` shows `scp -q -i KEY -r`, which merges and never deletes — so the caution was misdirected. Rewritten as an accurate note plus a positive check (step 5b) that the live page survived.

**Type consistency.** `NAV_PERMS` (Task 1) is consumed by name in Task 5's `PERM_DIM_JS` test and Task 3's import list. `emit_php_partial(path, active, base)` (Task 2) is called with one positional argument in Task 14 step 1, which matches its defaults. `capi_shell_open(string $title, string $crumbLeaf)` (Task 2) is called with exactly two strings in Task 14 step 2. `head(..., css=...)` (Task 1) is passed `css="link"` in Task 3 step 4 and Task 2's partial, and left at its `"inline"` default by the three on-box generators.

**One deliberate omission:** the inline→link CSS switch for the on-box generators. `head()` supports it as of Task 1, but no task flips it, because that would change the bytes of three live pages for a size win rather than a correctness one. Worth a follow-up once the unification has settled.
