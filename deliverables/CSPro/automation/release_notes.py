#!/usr/bin/env python
r"""CAPI instrument release notes generator (Carl, 2026-08-19).

Renders ../RELEASE-NOTES.md -- the per-instrument (F1/F3/F4/HUB) release-notes and
versioning monitor -- from three inputs:

  1. git history of versions.json: every commit where an instrument's version changed
     is a release; the entry's date is the deploy date recorded in versions.json at
     that commit, and its baseline note is that commit's subject line.
  2. The working-tree versions.json: a version bumped but not yet committed appears
     as the newest entry, marked "(working tree - not yet committed)".
  3. automation/release-notes-extra.json: hand-written bullets per "KEY x.y.z"
     (richer than a commit subject). These survive regeneration -- add them with
     `note`, never by editing RELEASE-NOTES.md (it is GENERATED and overwritten).

Usage:
  py release_notes.py regen                  # rebuild RELEASE-NOTES.md
  py release_notes.py note F3 "fixed Q45 skip after Aug-17 renumbering"
                                             # bullet for F3's CURRENT version + regen

stamp_version.py calls regen after every bump/set (and routes its --notes flag to
note), so the notes can only drift if RELEASE-NOTES.md is hand-edited -- don't.
F2 PWA release notes are a separate lane: deliverables/F2/PWA/app/CHANGELOG.md,
written by the milestone-close workflow (.github/workflows/uat-release-notes.yml).
"""
import json
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


def git(*args):
    r = subprocess.run(["git", "-C", str(ROOT), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""


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
                releases[k].append({
                    "version": data[k]["version"],
                    "date": data[k].get("date", cdate),
                    "note": subj,
                    "sha": sha[:7],
                })
                prev[k] = data[k]["version"]
    cur = json.loads(VERSIONS.read_text(encoding="utf-8"))
    for k in ORDER:
        if k in cur and cur[k]["version"] != prev.get(k):
            releases[k].append({
                "version": cur[k]["version"],
                "date": cur[k].get("date", ""),
                "note": "(working tree - not yet committed)",
                "sha": None,
            })
    return releases, cur


def f2_version():
    try:
        return json.loads(F2_PKG.read_text(encoding="utf-8")).get("version", "?")
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def regen():
    releases, cur = history()
    extra = load_extra()
    lines = [
        "# CAPI Instrument Release Notes",
        "",
        "> **GENERATED file - do not hand-edit.** Rebuild: `py automation/release_notes.py regen`",
        "> (runs automatically on every `stamp_version.py bump/set`). Add richer bullets with",
        '> `py automation/release_notes.py note F3 "..."` or `stamp_version.py bump F3 --notes "..."`;',
        "> they live in `automation/release-notes-extra.json` and survive regeneration.",
        ">",
        "> Versions SSOT: `versions.json` (semver; PATCH = bug-fix deploy, MINOR = new/changed",
        "> functionality, MAJOR = UAT round close / breaking change). History reconstructed from",
        "> git history of versions.json (SSOT since 2026-07-02; earlier builds predate it).",
    ]
    f2v = f2_version()
    if f2v:
        lines += [">",
                  f"> F2 PWA (separate lane): **v{f2v}** - notes in `deliverables/F2/PWA/app/CHANGELOG.md`",
                  "> (written by the milestone-close workflow `uat-release-notes.yml`)."]
    lines += ["", "## Current versions", "",
              "| Instrument | Version | Date |", "|---|---|---|"]
    for k in ORDER:
        if k in cur:
            lines.append(f"| {k} - {NAMES[k]} | **v{cur[k]['version']}** | {cur[k]['date']} |")
    if f2v:
        lines.append(f"| F2 - Healthcare Worker Survey (PWA) | **v{f2v}** | see F2 CHANGELOG |")
    lines.append("")
    for k in ORDER:
        if not releases[k]:
            continue
        lines += [f"## {k} - {NAMES[k]}", ""]
        for rel in reversed(releases[k]):
            sha = f" · `{rel['sha']}`" if rel["sha"] else ""
            lines.append(f"### v{rel['version']} - {rel['date']}{sha}")
            for bullet in extra.get(f"{k} {rel['version']}", []):
                lines.append(f"- {bullet}")
            lines.append(f"- {rel['note']}")
            lines.append("")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    n = sum(len(v) for v in releases.values())
    print(f"[notes] {OUT.name}: {n} releases across {sum(1 for k in ORDER if releases[k])} instruments")
    return True


def add_note(key, version, text):
    extra = load_extra()
    slot = f"{key.upper()} {version}"
    extra.setdefault(slot, [])
    if text not in extra[slot]:
        extra[slot].append(text)
    EXTRA.write_text(json.dumps(extra, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8", newline="\n")
    print(f"[notes] extra bullet recorded for {slot}")


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("regen", "note"):
        print(__doc__)
        sys.exit(1)
    if args[0] == "note":
        if len(args) < 3 or args[1].upper() not in ORDER:
            print('usage: release_notes.py note F1|F3|F4|HUB "text"')
            sys.exit(1)
        cur = json.loads(VERSIONS.read_text(encoding="utf-8"))
        add_note(args[1], cur[args[1].upper()]["version"], " ".join(args[2:]))
    sys.exit(0 if regen() else 1)


if __name__ == "__main__":
    main()
