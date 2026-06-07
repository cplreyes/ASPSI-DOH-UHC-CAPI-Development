#!/usr/bin/env python3
"""
Auto-seed the weekly retro section in sprint-current.md when the sprint
end date has been reached (Asia/Manila).

Fires on sprint end day (Fridays for 1-week sprints). If the four retro
answer slots still contain `_TBD YYYY-MM-DD_` placeholders, replace them
with auto-seeded content derived from standups + file activity. Any
human-written answer is preserved (only placeholders get replaced).

Idempotent: safe to run many times. Never crashes. Logs to
.claude/scripts/generate-retro.log.

    python generate_retro.py [--repo PATH] [--force]
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    MANILA = ZoneInfo("Asia/Manila")
except Exception:
    MANILA = timezone(timedelta(hours=8))

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

FM_BOUNDARY = re.compile(r"^---\s*$")
TBD_LINE = re.compile(r"^_TBD\s+\d{4}-\d{2}-\d{2}_\s*$")


def today_manila() -> date:
    return datetime.now(MANILA).date()


def log(repo: Path, msg: str) -> None:
    log_file = repo / ".claude" / "scripts" / "generate-retro.log"
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(MANILA).isoformat(timespec="seconds")
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {msg}\n")
    except OSError:
        pass


def parse_frontmatter(text: str) -> tuple[dict, int]:
    lines = text.splitlines()
    if not lines or not FM_BOUNDARY.match(lines[0]):
        return {}, 0
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if FM_BOUNDARY.match(line):
            end = i
            break
    if end is None:
        return {}, 0
    fm: dict = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, end + 1


def standups_in_range(standups_dir: Path, start: date, end: date) -> list[Path]:
    out = []
    if not standups_dir.exists():
        return out
    for f in standups_dir.glob("*.md"):
        try:
            d = date.fromisoformat(f.stem)
        except ValueError:
            continue
        if start <= d <= end:
            out.append(f)
    out.sort()
    return out


def compose_answers(repo: Path, sprint_fm: dict) -> dict[int, str]:
    try:
        start = date.fromisoformat(sprint_fm.get("start", ""))
        end = date.fromisoformat(sprint_fm.get("end", ""))
    except ValueError:
        start, end = None, None

    standups_dir = repo / "scrum" / "standups"
    files = standups_in_range(standups_dir, start, end) if start and end else []

    standup_count = len(files)
    expected = ((end - start).days + 1) if start and end else 0

    q1 = (
        f"_Auto-seed: {standup_count} standup(s) filed of {expected} sprint days. "
        "Review the week and answer: yes / partial / no — one line why. Overwrite this placeholder._"
    )
    q2 = (
        "_Auto-seed: review the week's standups in `scrum/standups/` for process surprises "
        "(not work surprises). Up to 3 bullets. Overwrite this placeholder._"
    )
    q3 = (
        "_Auto-seed: compute D2/D3/Tranche 2 slip days vs. contractual dates. "
        "Answer explicitly even if 0. Overwrite this placeholder._"
    )
    q4 = (
        "_Auto-seed: pick exactly one smallest concrete behavior change for next sprint, "
        "or write \"none — keep the same shape.\" Overwrite this placeholder._"
    )

    return {1: q1, 2: q2, 3: q3, 4: q4}


def seed_retro(sprint_text: str, answers: dict[int, str]) -> tuple[str, int]:
    lines = sprint_text.splitlines()
    in_retro = False
    current_q: int | None = None
    replaced = 0
    q_header = re.compile(r"^###\s+(\d+)\.")

    for i, line in enumerate(lines):
        if line.startswith("## Retrospective"):
            in_retro = True
            continue
        if in_retro and line.startswith("## ") and not line.startswith("## Retrospective"):
            break
        if not in_retro:
            continue
        m = q_header.match(line)
        if m:
            current_q = int(m.group(1))
            continue
        if current_q in answers and TBD_LINE.match(line):
            lines[i] = answers[current_q]
            replaced += 1

    return "\n".join(lines) + ("\n" if sprint_text.endswith("\n") else ""), replaced


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()

    try:
        today = today_manila()
        sprint_path = repo / "scrum" / "sprint-current.md"
        if not sprint_path.exists():
            log(repo, "skip: sprint-current.md missing")
            return 0

        text = sprint_path.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)

        end_str = fm.get("end", "")
        try:
            end_date = date.fromisoformat(end_str)
        except ValueError:
            log(repo, f"skip: cannot parse sprint end date: {end_str!r}")
            return 0

        if today < end_date and not args.force:
            log(repo, f"skip: today {today} < sprint end {end_date}")
            return 0

        answers = compose_answers(repo, fm)
        new_text, replaced = seed_retro(text, answers)

        if replaced == 0:
            log(repo, "skip: no TBD placeholders found (retro already written)")
            return 0

        sprint_path.write_text(new_text, encoding="utf-8")
        log(repo, f"seeded {replaced} retro answer(s) in sprint-current.md")
        print(f"[generate_retro] seeded {replaced} retro placeholder(s)")
        return 0

    except Exception as e:  # noqa: BLE001
        log(repo, f"error: {type(e).__name__}: {e}")
        log(repo, traceback.format_exc())
        return 0


if __name__ == "__main__":
    sys.exit(main())
