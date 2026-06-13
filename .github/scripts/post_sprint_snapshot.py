"""Post cross-sprint summary snapshot to Slack #capi-scrum.

Tallies the repo's scrum/ markdown — the single source of truth — and posts a
monospace summary table:
  - one row per archived sprint (scrum/sprints/sprint-*.md, excluding *-plan.md)
  - one row for the active sprint (scrum/sprint-current.md)
  - one row for the epic backlogs (scrum/epics/*.md, summed)

RE-POINTED 2026-06-13 (S009 close, E0-SCRUM-SYNC): previously this queried the
GH Projects board (#8) via GraphQL — but the board was deliberately parked on
2026-06-05 (items closed not-planned; reopen trigger = the desk-test session),
so every snapshot tallied a frozen "unscheduled 103" state while the real work
lived in scrum/*.md. The repo files are maintained at sprint ceremonies (and
auto-checked by the daily standup task), so they are the honest feed.

A task = a markdown checkbox line. done = `- [x]`, open = `- [ ]`;
open lines carrying `status::in-progress` / `status::blocked` are surfaced
in the breakdown line under the table.

Modes (controls header framing only; table contents identical):
  start   Monday morning sprint kickoff: ":rocket: Sprint NNN kickoff snapshot"
  close   Friday EOD sprint closeout:    ":bar_chart: Sprint NNN closeout snapshot"
  test    Local dry-run: prints to stdout, does NOT post to Slack

Env:
  SLACK_WEBHOOK_URL   required for non-test modes
  GITHUB_WORKSPACE    set in Actions; falls back to script's repo root locally

Usage:
  python .github/scripts/post_sprint_snapshot.py start
  python .github/scripts/post_sprint_snapshot.py close
  python .github/scripts/post_sprint_snapshot.py test [start|close]
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE") or Path(__file__).resolve().parents[2])
SCRUM = REPO_ROOT / "scrum"
SPRINT_CURRENT = SCRUM / "sprint-current.md"
SPRINTS_DIR = SCRUM / "sprints"
EPICS_DIR = SCRUM / "epics"

OWNER = "cplreyes"
REPO = "ASPSI-DOH-UHC-CAPI-Development"
SCRUM_URL = f"https://github.com/{OWNER}/{REPO}/tree/main/scrum"

CHECKBOX_DONE = re.compile(r"^\s*- \[x\]", re.MULTILINE | re.IGNORECASE)
CHECKBOX_OPEN = re.compile(r"^\s*- \[ \]", re.MULTILINE)
OPEN_IN_PROGRESS = re.compile(r"^\s*- \[ \].*status::in-progress", re.MULTILINE)
OPEN_BLOCKED = re.compile(r"^\s*- \[ \].*status::blocked", re.MULTILINE)


def tally(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return {
        "done": len(CHECKBOX_DONE.findall(text)),
        "open": len(CHECKBOX_OPEN.findall(text)),
        "in_progress": len(OPEN_IN_PROGRESS.findall(text)),
        "blocked": len(OPEN_BLOCKED.findall(text)),
    }


def collect() -> tuple[list[tuple[str, dict]], dict]:
    """Returns ([(row_label, counts), ...] in display order, totals)."""
    rows: list[tuple[str, dict]] = []

    for p in sorted(SPRINTS_DIR.glob("sprint-*.md")):
        if p.stem.endswith("-plan"):
            continue
        rows.append((p.stem, tally(p)))

    if SPRINT_CURRENT.exists():
        text = SPRINT_CURRENT.read_text(encoding="utf-8")
        m = re.search(r"^sprint:\s*(\d+)", text, re.MULTILINE)
        label = f"sprint-{m.group(1)}*" if m else "current*"
        rows.append((label, tally(SPRINT_CURRENT)))

    epics = {"done": 0, "open": 0, "in_progress": 0, "blocked": 0}
    for p in sorted(EPICS_DIR.glob("epic-*.md")):
        t = tally(p)
        for k in epics:
            epics[k] += t[k]
    rows.append(("epics (all)", epics))

    totals = {"done": 0, "open": 0, "in_progress": 0, "blocked": 0}
    for _, c in rows:
        for k in totals:
            totals[k] += c[k]
    return rows, totals


def get_current_sprint_number() -> str:
    if not SPRINT_CURRENT.exists():
        return "?"
    text = SPRINT_CURRENT.read_text(encoding="utf-8")
    m = re.search(r"^sprint:\s*(\d+)", text, re.MULTILINE)
    return m.group(1) if m else "?"


def render_table(rows: list[tuple[str, dict]], totals: dict) -> str:
    out = [("Source", "Done", "Open", "Total")]
    out.append(("-" * 12, "-" * 4, "-" * 4, "-" * 5))
    for label, c in rows:
        done_str = str(c["done"]) if c["done"] else "-"
        open_str = str(c["open"]) if c["open"] else "-"
        out.append((label, done_str, open_str, str(c["done"] + c["open"])))
    out.append(("-" * 12, "-" * 4, "-" * 4, "-" * 5))
    out.append(("TOTAL", str(totals["done"]), str(totals["open"]),
                str(totals["done"] + totals["open"])))

    widths = [max(len(r[i]) for r in out) for i in range(4)]
    return "\n".join(
        f"{r[0]:<{widths[0]}}  {r[1]:>{widths[1]}}  {r[2]:>{widths[2]}}  {r[3]:>{widths[3]}}"
        for r in out
    )


def render_breakdown(totals: dict) -> str:
    parts = []
    if totals["in_progress"]:
        parts.append(f":hammer_and_wrench: {totals['in_progress']} In Progress")
    if totals["blocked"]:
        parts.append(f":no_entry: {totals['blocked']} Blocked")
    return " · ".join(parts)


def render_message(mode: str, rows: list[tuple[str, dict]], totals: dict) -> str:
    sprint_n = get_current_sprint_number()

    if mode == "start":
        header = f":rocket: *Sprint {sprint_n} — kickoff snapshot* (scrum/ task state)"
    elif mode == "close":
        header = f":bar_chart: *Sprint {sprint_n} — closeout snapshot* (scrum/ task state)"
    else:
        header = f":clipboard: *Backlog snapshot — Sprint {sprint_n}* (manual run)"

    lines = [header, "", "```", render_table(rows, totals), "```"]
    breakdown = render_breakdown(totals)
    if breakdown:
        lines.append(breakdown)
    lines.append("")
    lines.append(f"_* = active sprint_ · <{SCRUM_URL}|scrum/ on GitHub>")
    return "\n".join(lines)


def post_to_slack(text: str) -> None:
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        print("ERROR: SLACK_WEBHOOK_URL not set; cannot post to Slack.", file=sys.stderr)
        sys.exit(1)
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        webhook, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        if r.status not in (200, 201):
            print(f"ERROR: Slack returned {r.status}: {r.read()[:200]}", file=sys.stderr)
            sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    mode = sys.argv[1]
    submode = sys.argv[2] if len(sys.argv) >= 3 else "start"

    rows, totals = collect()
    text = render_message(submode if mode == "test" else mode, rows, totals)

    if mode in ("start", "close"):
        post_to_slack(text)
        print(f"Posted {mode} snapshot to Slack ({len(text)} chars).")
    elif mode == "test":
        print(text)
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
