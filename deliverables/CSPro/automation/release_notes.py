#!/usr/bin/env python
r"""CAPI instrument release notes generator (Carl, 2026-08-19; Keep-a-Changelog rev same day).

Renders ../RELEASE-NOTES.md -- the per-instrument (F1/F3/F4/HUB) release-notes and
versioning monitor. Format follows Keep a Changelog 1.1.0 adapted to a multi-instrument
repo: one section per instrument, one entry per released version (newest first), human
notes grouped by change type (Added / Changed / Deprecated / Removed / Fixed / Security),
an Unreleased section for working-tree bumps, linkable versions, ISO dates, and explicit
BREAKING flags. Versioning follows SemVer (see VERSIONING.md).

Inputs:
  1. git history of versions.json: every commit where an instrument's version changed is
     a release (deploy date from the json `date` field; commit kept as provenance).
  2. Working-tree versions.json: a bumped-but-uncommitted version renders under Unreleased.
  3. automation/release-notes-extra.json: the CURATED notes, per "KEY x.y.z":
       "F3 4.0.0": {"breaking": true, "Changed": ["..."], "Fixed": ["..."]}
     (a plain list is accepted and rendered as Changed). These are the human notes the
     standard asks for -- commit subjects only fill in where no curated notes exist yet.

Usage:
  py release_notes.py regen
  py release_notes.py note F3 "Q45 skip restored after renumbering"            # -> Fixed
  py release_notes.py note F3 --type added "GAMOT block Q69-78" --breaking     # typed + flag

stamp_version.py calls regen after every bump/set; its --notes text lands here typed by
bump kind (patch->Fixed, minor->Added, major->Changed) unless --type overrides.
RELEASE-NOTES.md is GENERATED -- never hand-edit it; edit the overlay instead.
F2 PWA is a separate lane: deliverables/F2/PWA/app/CHANGELOG.md (milestone-close workflow).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]            # deliverables/CSPro
VERSIONS = ROOT / "versions.json"
OUT = ROOT / "RELEASE-NOTES.md"
EXTRA = ROOT / "automation" / "release-notes-extra.json"
F2_PKG = ROOT.parents[0] / "F2" / "PWA" / "app" / "package.json"
ORDER = ["F1", "F3", "F4", "HUB"]
NAMES = {"F1": "Facility Head Survey", "F3": "Patient Survey",
         "F4": "Household Survey", "HUB": "Supervisor Hub"}
TYPES = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]


def git(*args):
    r = subprocess.run(["git", "-C", str(ROOT), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""


def repo_url():
    url = git("config", "--get", "remote.origin.url").strip()
    url = re.sub(r"\.git$", "", url)
    return url if url.startswith("http") else "https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development"


def load_extra():
    if EXTRA.exists():
        return json.loads(EXTRA.read_text(encoding="utf-8"))
    return {}


def history():
    """Per-instrument release list, oldest->newest, from versions.json's git history."""
    log = git("log", "--reverse", "--format=%H|%ad|%s", "--date=short", "--", "versions.json")
    releases = {k: [] for k in ORDER}
    prev = {}
    for line in log.strip().splitlines():
        sha, cdate, subj = line.split("|", 2)
        raw = git("show", f"{sha}:./versions.json")
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        for k in ORDER:
            if k in data and data[k].get("version") != prev.get(k):
                releases[k].append({"version": data[k]["version"],
                                    "date": data[k].get("date", cdate),
                                    "subject": subj, "sha": sha})
                prev[k] = data[k]["version"]
    cur = json.loads(VERSIONS.read_text(encoding="utf-8"))
    unreleased = []
    for k in ORDER:
        if k in cur and cur[k]["version"] != prev.get(k):
            unreleased.append({"key": k, "version": cur[k]["version"],
                               "date": cur[k].get("date", "")})
    return releases, cur, unreleased


def f2_version():
    try:
        return json.loads(F2_PKG.read_text(encoding="utf-8")).get("version", "?")
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def bump_class(prev_ver, ver):
    if not prev_ver:
        return "baseline"
    try:
        p, c = [tuple(int(x) for x in s.split(".")) for s in (prev_ver, ver)]
    except ValueError:
        return ""
    if c[0] != p[0]:
        return "MAJOR"
    if c[1] != p[1]:
        return "MINOR"
    return "PATCH"


def linkify(text, url):
    """#123 -> issue link (leave already-bracketed refs alone)."""
    return re.sub(r"(?<!\[)#(\d{1,5})\b", rf"[#\1]({url}/issues/\1)", text)


def notes_for(extra, key, ver):
    """Normalized overlay entry: (dict type->bullets, breaking:bool)."""
    slot = extra.get(f"{key} {ver}")
    if slot is None:
        return {}, False
    if isinstance(slot, list):
        return ({"Changed": list(slot)} if slot else {}), False
    groups = {t: list(slot[t]) for t in TYPES if slot.get(t)}
    return groups, bool(slot.get("breaking"))


def render_entry(lines, key, rel, prev_sha, prev_ver, extra, url):
    ver, sha = rel["version"], rel["sha"]
    ref = f"{url}/compare/{prev_sha}...{sha}" if prev_sha else f"{url}/commit/{sha}"
    cls = bump_class(prev_ver, ver)
    groups, breaking = notes_for(extra, key, ver)
    head = f"### [v{ver}]({ref}) - {rel['date']}"
    if cls:
        head += f" · {cls}"
    if breaking:
        head += " · **BREAKING** (data shape)"
    lines.append(head)
    if groups:
        for t in TYPES:
            if t in groups:
                lines.append(f"#### {t}")
                lines += [f"- {linkify(b, url)}" for b in groups[t]]
        lines.append(f"_Release commit [`{sha[:7]}`]({url}/commit/{sha}): "
                     f"{linkify(rel['subject'], url)}_")
    else:
        # no curated notes yet -- the release commit's subject stands in (add real
        # notes with `release_notes.py note`; don't leave user-facing releases like this)
        lines.append(f"- {linkify(rel['subject'], url)} ([`{sha[:7]}`]({url}/commit/{sha}))")
    lines.append("")


def regen():
    url = repo_url()
    releases, cur, unreleased = history()
    extra = load_extra()
    lines = [
        "# CAPI Instrument Release Notes",
        "",
        "All notable changes to the CSEntry CAPI instruments - **F1** Facility Head Survey,",
        "**F3** Patient Survey, **F4** Household Survey, and the **Supervisor Hub** - written",
        "for the people who use them: testers, field staff, and data users.",
        "",
        "The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), adapted",
        "to this multi-instrument repo (one section per instrument, one entry per released",
        "version, newest first). Versioning follows [Semantic Versioning](https://semver.org/):",
        "**PATCH** = bug-fix deploy · **MINOR** = new/changed functionality · **MAJOR** = UAT",
        "round close or a breaking change; entries flagged **BREAKING** change the collected",
        "data's shape. Dates are ISO (YYYY-MM-DD) deploy dates from `versions.json` (the",
        "version SSOT, tracked since 2026-07-02 - earlier builds predate it).",
        "",
        "> **GENERATED file - do not hand-edit.** Rebuild: `py automation/release_notes.py regen`",
        "> (runs automatically on every `stamp_version.py bump/set`). Curated notes live in",
        "> `automation/release-notes-extra.json` - add them with",
        '> `py automation/release_notes.py note F3 [--type fixed|added|...] [--breaking] "..."`',
        '> or `stamp_version.py bump F3 --notes "..."` (typed by bump kind). Entries without',
        "> curated notes fall back to their release commit's subject.",
    ]
    f2v = f2_version()
    if f2v:
        lines += [">",
                  f"> F2 PWA (separate lane): **v{f2v}** - notes in `deliverables/F2/PWA/app/CHANGELOG.md`",
                  "> (written by the milestone-close workflow `uat-release-notes.yml`)."]
    lines += ["", "## Current versions", "",
              "| Instrument | Version | Deployed |", "|---|---|---|"]
    for k in ORDER:
        if k in cur:
            lines.append(f"| {k} - {NAMES[k]} | **v{cur[k]['version']}** | {cur[k]['date']} |")
    if f2v:
        lines.append(f"| F2 - Healthcare Worker Survey (PWA) | **v{f2v}** | see F2 CHANGELOG |")
    lines.append("")
    if unreleased:
        lines += ["## Unreleased", ""]
        for u in unreleased:
            groups, breaking = notes_for(extra, u["key"], u["version"])
            flag = " · **BREAKING** (data shape)" if breaking else ""
            lines.append(f"- **{u['key']} v{u['version']}** ({u['date']}) - bumped in the "
                         f"working tree, not yet committed{flag}")
            for t in TYPES:
                for b in groups.get(t, []):
                    lines.append(f"  - {t}: {linkify(b, url)}")
        lines.append("")
    for k in ORDER:
        if not releases[k]:
            continue
        lines += [f"## {k} - {NAMES[k]}", ""]
        rels = releases[k]
        for i in range(len(rels) - 1, -1, -1):
            prev = rels[i - 1] if i > 0 else None
            render_entry(lines, k, rels[i],
                         prev["sha"] if prev else None,
                         prev["version"] if prev else None, extra, url)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    n = sum(len(v) for v in releases.values())
    print(f"[notes] {OUT.name}: {n} releases, {len(unreleased)} unreleased, "
          f"{sum(1 for k in ORDER if releases[k])} instruments")
    return True


def add_note(key, version, text, type_=None, breaking=None):
    t = (type_ or "Fixed").capitalize()
    if t not in TYPES:
        print(f"[notes] ! unknown type '{type_}' (use one of {'/'.join(TYPES)})")
        return
    extra = load_extra()
    slot = extra.setdefault(f"{key.upper()} {version}", {})
    if isinstance(slot, list):                          # migrate legacy list in place
        slot = {"Changed": slot}
        extra[f"{key.upper()} {version}"] = slot
    slot.setdefault(t, [])
    if text not in slot[t]:
        slot[t].append(text)
    if breaking:
        slot["breaking"] = True
    EXTRA.write_text(json.dumps(extra, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8", newline="\n")
    print(f"[notes] {t} bullet recorded for {key.upper()} {version}")


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("regen", "note"):
        print(__doc__)
        sys.exit(1)
    if args[0] == "note":
        rest = args[1:]
        if not rest or rest[0].upper() not in ORDER:
            print('usage: release_notes.py note F1|F3|F4|HUB [--type <t>] [--breaking] "text"')
            sys.exit(1)
        key = rest[0].upper()
        type_ = rest[rest.index("--type") + 1] if "--type" in rest else None
        breaking = "--breaking" in rest
        skip = set()
        if "--type" in rest:
            skip = {rest.index("--type"), rest.index("--type") + 1}
        words = [a for i, a in enumerate(rest) if i > 0 and i not in skip and a != "--breaking"]
        if not words:
            print("note needs text")
            sys.exit(1)
        cur = json.loads(VERSIONS.read_text(encoding="utf-8"))
        add_note(key, cur[key]["version"], " ".join(words), type_, breaking)
    sys.exit(0 if regen() else 1)


if __name__ == "__main__":
    main()
