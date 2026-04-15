#!/usr/bin/env python3
"""
Emit a per-instrument PB/sprint snapshot block for the daily CAPI Scrum post.

Scans scrum/epics/*.md for task checkboxes tagged with instrument-specific
task IDs (E2-F1-*, E2-F2-*, E3-F1-*, E3-F2-GF-*, E2-F3-*, E2-F4-*, E2-PLF-*)
and tallies done / open / blocked / deferred per instrument × epic. Also
scans scrum/sprint-current.md for committed items.

Output is Slack-friendly mrkdwn, ~15 lines, designed to append to the
existing :sunrise: CAPI Scrum daily post body.

Usage:
    python .claude/scripts/snapshot_instruments.py [--repo PATH]

Exits 0 on success; prints to stdout. Never raises — missing files degrade
to the literal string "snapshot unavailable" so the daily poster still runs.
"""

from __future__ import annotations
import argparse
import io
import re
import sys
from pathlib import Path

# Windows cp1252 gotcha — force UTF-8 for stdout so block chars and ⚠ render.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

INSTRUMENTS = ["F1", "F2", "F3", "F4", "PLF"]
EPIC_PREFIXES = {
    "Design":  ("E2",),   # Questionnaire design
    "Build":   ("E3",),   # CAPI / Google Forms build
}

TASK_LINE = re.compile(r"^- \[(?P<mark>[ xX~!])\] \*\*(?P<id>E\d+-(?:[A-Z0-9]+-)?(?P<inst>F\d|PLF|GF|[A-Z]+)-?\d*[a-z]?)\*\*.*?(?:`status::(?P<status>[a-z-]+)`)?", re.IGNORECASE)
TASK_LINE_SIMPLE = re.compile(
    r"^- \[(?P<mark>[ xX~!])\] \*\*(?P<id>E\d+-F?\d?-?[A-Za-z0-9-]*)\*\*"
)

# Loose match: any line starting with "- [x] **E2-F1-" etc.
ID_RE = re.compile(r"^- \[(?P<mark>[ x])\] \*\*(?P<id>E(?P<epic>\d+)-(?P<rest>[A-Z0-9-]+))\*\*")
STATUS_RE = re.compile(r"`status::([a-z-]+)`")


def classify_instrument(task_id: str) -> str | None:
    """Return F1/F2/F3/F4/PLF given a task ID like E2-F1-010 or E3-F2-GF-001."""
    # Strip leading epic prefix (E2-, E3-)
    m = re.match(r"E\d+-(F\d|PLF)\b", task_id)
    if m:
        return m.group(1)
    return None


def classify_epic(task_id: str) -> str | None:
    m = re.match(r"E(\d+)-", task_id)
    if not m:
        return None
    n = int(m.group(1))
    if n == 2:
        return "Design"
    if n == 3:
        return "Build"
    return None


def scan_epics(repo: Path) -> dict:
    """Return {instrument: {epic: {done, open, blocked, deferred}}}."""
    tally: dict[str, dict[str, dict[str, int]]] = {
        inst: {"Design": {"done": 0, "open": 0, "blocked": 0, "deferred": 0},
               "Build":  {"done": 0, "open": 0, "blocked": 0, "deferred": 0}}
        for inst in INSTRUMENTS
    }
    epic_dir = repo / "scrum" / "epics"
    if not epic_dir.exists():
        return tally
    for md in sorted(epic_dir.glob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            m = ID_RE.match(line)
            if not m:
                continue
            task_id = m.group("id")
            inst = classify_instrument(task_id)
            epic = classify_epic(task_id)
            if inst not in tally or epic not in tally[inst]:
                continue
            status_match = STATUS_RE.search(line)
            status = status_match.group(1) if status_match else None
            if status == "deferred":
                tally[inst][epic]["deferred"] += 1
            elif status == "blocked":
                tally[inst][epic]["blocked"] += 1
            elif m.group("mark").lower() == "x" or status == "done":
                tally[inst][epic]["done"] += 1
            else:
                tally[inst][epic]["open"] += 1
    return tally


def scan_sprint(repo: Path) -> dict[str, dict[str, int]]:
    """Return {instrument: {committed, done}} for the current sprint."""
    out = {inst: {"committed": 0, "done": 0} for inst in INSTRUMENTS}
    sprint_file = repo / "scrum" / "sprint-current.md"
    if not sprint_file.exists():
        return out
    try:
        text = sprint_file.read_text(encoding="utf-8")
    except OSError:
        return text
    for line in text.splitlines():
        m = ID_RE.match(line)
        if not m:
            continue
        task_id = m.group("id")
        inst = classify_instrument(task_id)
        if inst not in out:
            continue
        out[inst]["committed"] += 1
        if m.group("mark").lower() == "x":
            out[inst]["done"] += 1
    return out


def progress_bar(done: int, total: int, width: int = 10) -> str:
    if total == 0:
        return "·" * width + f" 0/0"
    filled = round((done / total) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {done}/{total}"


def render(tally: dict, sprint: dict) -> str:
    lines = ["*By Survey Instrument* (Epic 2 Design · Epic 3 Build · Sprint)"]
    lines.append("```")
    for inst in INSTRUMENTS:
        t = tally[inst]
        d = t["Design"]
        b = t["Build"]
        design_total = d["done"] + d["open"] + d["blocked"]
        build_total = b["done"] + b["open"] + b["blocked"]
        # Deferred tasks excluded from totals (F2 CSPro track)
        s = sprint[inst]
        design_bar = progress_bar(d["done"], design_total, 8)
        build_bar = progress_bar(b["done"], build_total, 8)
        sprint_str = f"{s['done']}/{s['committed']}" if s["committed"] else "—"
        flags = []
        if d["blocked"]: flags.append(f"{d['blocked']}blk")
        if b["blocked"]: flags.append(f"{b['blocked']}blk")
        if d["deferred"] or b["deferred"]:
            flags.append(f"{d['deferred'] + b['deferred']}def")
        flag_str = (" ⚠ " + ",".join(flags)) if flags else ""
        lines.append(f"{inst:<4}  D:{design_bar}  B:{build_bar}  sprint:{sprint_str}{flag_str}")
    lines.append("```")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]),
                    help="Repo root (default: infer from script location)")
    args = ap.parse_args(argv)
    repo = Path(args.repo)
    try:
        tally = scan_epics(repo)
        sprint = scan_sprint(repo)
        out = render(tally, sprint)
    except Exception as e:  # noqa: BLE001
        print(f"snapshot unavailable ({type(e).__name__}: {e})", file=sys.stderr)
        print("snapshot unavailable")
        return 0
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
