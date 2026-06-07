#!/usr/bin/env python3
"""
Auto-generate today's daily standup for the ASPSI-DOH-CAPI-CSPro project.

Reads:
  scrum/product-backlog.md   stakeholder context (frontmatter + narrative)
  scrum/sprint-current.md    sprint frontmatter, goal, committed items
  scrum/standups/*.md        most recent prior standup (gap window anchor)
  <project>/**               modified files since prior standup (activity)

Writes:
  scrum/standups/YYYY-MM-DD.md (Asia/Manila). Idempotent: exit 0 if exists.

Never crashes the invoking hook. On any error, logs to
.claude/scripts/generate-standup.log and exits 0.

    python generate_standup.py [--repo PATH] [--force]
"""

from __future__ import annotations

import argparse
import io
import os
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
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

SKIP_DIRS = {
    "node_modules", ".git", ".obsidian", "dist", "build", ".next",
    "__pycache__", ".venv", "venv", ".claude",
}
SCAN_EXTS = {".md", ".py", ".csv", ".xlsx", ".dcf", ".fmf", ".apc", ".json", ".ts", ".tsx", ".js", ".jsx"}

FM_BOUNDARY = re.compile(r"^---\s*$")
# Item IDs start with an uppercase letter/digit but may carry lowercase
# segments (e.g. E0-009b, E4-CSWeb-001) — the continuation class must allow
# them or those rows are silently dropped from the board.
TASK_LINE = re.compile(
    r"^-\s*\[(?P<mark>[ xX~!])\]\s*\*\*(?P<id>[A-Z0-9][A-Za-z0-9-]*)\*\*\s*(?P<title>.*?)$"
)
INLINE_FIELD = re.compile(r"`(?P<key>[a-z_]+)::(?P<val>[^`]+)`")
RISK_ROW = re.compile(r"^\|\s*(?P<name>[^|]+?)\s*\|\s*(?P<likelihood>[^|]+?)\s*\|\s*(?P<impact>[^|]+?)\s*\|(?P<rest>.*)\|\s*$")


def today_manila() -> date:
    return datetime.now(MANILA).date()


def parse_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or not FM_BOUNDARY.match(lines[0]):
        return {}, text
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if FM_BOUNDARY.match(line):
            end = i
            break
    if end is None:
        return {}, text
    fm: dict = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip().strip('"').strip("'")
    body = "\n".join(lines[end + 1:])
    return fm, body


def parse_committed_items(sprint_body: str) -> list[dict]:
    items = []
    in_section = False
    for raw in sprint_body.splitlines():
        line = raw.rstrip()
        if line.startswith("## Committed Items"):
            in_section = True
            continue
        if in_section and line.startswith("## ") and not line.startswith("## Committed Items"):
            break
        if not in_section:
            continue
        m = TASK_LINE.match(line)
        if not m:
            continue
        title = m.group("title").strip()
        fields = {k: v for k, v in INLINE_FIELD.findall(line)}
        title_clean = INLINE_FIELD.sub("", title).strip()
        done = m.group("mark").lower() == "x"
        items.append({
            "id": m.group("id"),
            "title": title_clean,
            "done": done,
            "status": fields.get("status", "done" if done else "todo"),
            "priority": fields.get("priority", ""),
            "estimate": fields.get("estimate", ""),
            "epic": fields.get("epic", ""),
        })
    return items


def find_prior_standup(standups_dir: Path, today: date) -> Path | None:
    if not standups_dir.exists():
        return None
    candidates = []
    for f in standups_dir.glob("*.md"):
        try:
            d = date.fromisoformat(f.stem)
            if d < today:
                candidates.append((d, f))
        except ValueError:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def scan_file_activity(repo: Path, since: datetime, upper: datetime | None = None) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    since_ts = since.timestamp()
    upper_ts = upper.timestamp() if upper else None
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            p = Path(root) / name
            if p.suffix.lower() not in SCAN_EXTS:
                continue
            try:
                mtime = p.stat().st_mtime
            except OSError:
                continue
            if mtime < since_ts:
                continue
            if upper_ts is not None and mtime >= upper_ts:
                continue
            rel = p.relative_to(repo).as_posix()
            if rel.startswith("scrum/standups/"):
                continue
            top = rel.split("/", 1)[0] if "/" in rel else "(root)"
            groups.setdefault(top, []).append(rel)
    for k in groups:
        groups[k].sort()
    return groups


PB_HEADLINE_RE = re.compile(r"^##\s+(?:\d+\.\s+)?Status at a Glance\b", re.IGNORECASE)


def extract_pb_headline(pb_body: str) -> list[str]:
    out = []
    in_headline = False
    for line in pb_body.splitlines():
        if PB_HEADLINE_RE.match(line):
            in_headline = True
            continue
        if in_headline and line.startswith("## "):
            break
        if in_headline:
            out.append(line)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


PB_RISKS_RE = re.compile(r"^##\s+(?:\d+\.\s+)?Risks?\b", re.IGNORECASE)
HIGH_WORD = re.compile(r"\bhigh\b", re.IGNORECASE)


def extract_pb_risks(pb_body: str) -> list[dict]:
    risks = []
    in_section = False
    for line in pb_body.splitlines():
        if PB_RISKS_RE.match(line):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.strip().startswith("|"):
            continue
        if set(line.strip().strip("|").strip()) <= set("-|: "):
            continue
        m = RISK_ROW.match(line)
        if not m:
            continue
        name = m.group("name").strip()
        lk = m.group("likelihood").strip()
        im = m.group("impact").strip()
        if name.lower() in {"name", "risk"}:
            continue
        if HIGH_WORD.search(lk) or HIGH_WORD.search(im):
            risks.append({"name": name, "likelihood": lk, "impact": im})
    return risks


def compute_sprint_day(fm: dict, today: date) -> tuple[int | None, int | None, int | None]:
    try:
        start = date.fromisoformat(fm.get("start", ""))
        end = date.fromisoformat(fm.get("end", ""))
    except ValueError:
        return None, None, None
    total = (end - start).days + 1
    day = (today - start).days + 1
    remaining = (end - today).days
    return day, total, remaining


def sprint_board_counts(items: list[dict]) -> dict[str, int]:
    counts = {"todo": 0, "in-progress": 0, "review": 0, "blocked": 0, "done": 0}
    for it in items:
        s = it["status"].lower()
        if it["done"] or s == "done":
            counts["done"] += 1
        elif s in counts:
            counts[s] += 1
        else:
            counts["todo"] += 1
    return counts


def render_standup(ctx: dict) -> str:
    today: date = ctx["today"]
    dow = today.strftime("%A")
    fm = ctx["sprint_fm"]
    sprint_num = fm.get("sprint", "?")
    status = fm.get("status", "active")
    day, total, _remaining = ctx["sprint_day"]
    planning = status.lower() == "planning"
    # Roll-over: the sprint window has elapsed but sprint-current.md was never
    # closed/reset, so compute_sprint_day yields "Day 8 of 5". A stale standup
    # like this is the exact failure E0-008 exists to surface.
    roll_over = day is not None and total is not None and day > total
    no_activity = not ctx["file_activity"]

    out = [
        "---",
        f"date: {today.isoformat()}",
        f"project: {ctx['project_name']}",
        f"sprint: {sprint_num}",
    ]
    if day is not None and total is not None:
        out.append(f"sprint_day: {day} of {total}")
    if planning:
        out.append("sprint_status: planning")
    out.append("---")
    out.append("")
    out.append(f"# Daily Standup — {today.isoformat()}, {dow}")
    out.append("")
    out.append(f"**Project:** {ctx['project_name']}")
    goal = ctx["sprint_goal"] or "TBD"
    out.append(f"**Sprint:** {sprint_num} — {goal}")
    if day is not None and total is not None:
        out.append(f"**Sprint Day:** {day} of {total}")
    if planning:
        out.append("")
        out.append("> Sprint is in `status: planning`. Populate goal, committed items, and DoD during planning; tactical sections below reflect current stubs.")
    if roll_over:
        out.append("")
        out.append(
            f"> [!warning] Sprint window exceeded — Day {day} of {total}. "
            f"Sprint {sprint_num} ran past its end date without being closed and "
            f"rolled over, so this auto-standup is **provisional** — it reflects a "
            f"sprint that should already be retired. Run `/scrum` to close Sprint "
            f"{sprint_num} (Mode D retro + archive) and plan the next one. "
            f"_Silence ≠ idle: an unreset sprint does not mean no work happened._"
        )
    out.append("")
    out.append("---")
    out.append("")

    out.append("## Stakeholder Context *(from Product Backlog)*")
    out.append("")
    if ctx["pb_stale_days"] is not None and ctx["pb_stale_days"] > 14:
        out.append(f"> Product Backlog last updated {ctx['pb_last_updated']} — {ctx['pb_stale_days']} days stale. Consider regroom.")
        out.append("")
    headline = ctx["pb_headline"]
    if headline:
        out.extend(headline)
        out.append("")
    if ctx["pb_risks"]:
        out.append("**Top-level risks on the watchlist (Likelihood High OR Impact High):**")
        out.append("")
        for r in ctx["pb_risks"]:
            out.append(f"- **{r['name']}** — Likelihood {r['likelihood']}, Impact {r['impact']}")
        out.append("")
    out.append("---")
    out.append("")

    if not planning:
        counts = ctx["board_counts"]
        total_committed = sum(counts.values())
        out.append("## Sprint Board")
        out.append("")
        out.append("| To Do | In Progress | Review | Blocked | Done |")
        out.append("|-------|-------------|--------|---------|------|")
        out.append(f"| {counts['todo']} | {counts['in-progress']} | {counts['review']} | {counts['blocked']} | {counts['done']} / {total_committed} |")
        out.append("")

    prior_label = ctx["prior_standup_label"]
    out.append(f"## Yesterday — {prior_label}")
    out.append("")
    activity = ctx["file_activity"]
    if not activity:
        out.append(
            "> [!note] No file activity detected in the repo since the last "
            "standup. **Silence ≠ idle** — work may have happened off-repo "
            "(CSPro/CSEntry Designer GUI, tablet testing, comms, planning, "
            "review). Confirm and fill this in manually rather than treating "
            "the blank window as a no-work day."
        )
        out.append("")
    else:
        for top in sorted(activity.keys()):
            files = activity[top]
            if len(files) > 12:
                shown = files[:12]
                extra = len(files) - 12
                out.append(f"**{top}/** ({len(files)} files)")
                for f in shown:
                    out.append(f"- `{f}`")
                out.append(f"- _…and {extra} more_")
            else:
                out.append(f"**{top}/**")
                for f in files:
                    out.append(f"- `{f}`")
            out.append("")

    out.append("## Today (Plan)")
    out.append("")
    today_items = [it for it in ctx["committed"] if not it["done"] and it["status"].lower() != "blocked"]
    if planning and not today_items:
        out.append("_Sprint in planning — populate `scrum/sprint-current.md` Committed Items first._")
        out.append("")
    elif not today_items:
        out.append("_No open committed items._")
        out.append("")
    else:
        out.append("| # | ID | Item | Status | Priority | Estimate |")
        out.append("|---|----|------|--------|----------|----------|")
        for i, it in enumerate(today_items, 1):
            out.append(f"| {i} | **{it['id']}** | {it['title']} | {it['status']} | {it['priority'] or '—'} | {it['estimate'] or '—'} |")
        out.append("")

    out.append("## Blockers & Impediments")
    out.append("")
    blocked = [it for it in ctx["committed"] if it["status"].lower() == "blocked"]
    at_risk = ctx["at_risk"]
    if blocked:
        for it in blocked:
            out.append(f"- **Blocked:** **{it['id']}** {it['title']}")
    if at_risk:
        for it in at_risk:
            out.append(f"- **At risk:** **{it['id']}** {it['title']} — still `{it['status']}` past sprint midpoint")
    if not blocked and not at_risk:
        if ctx["pb_risks"]:
            out.append("_No sprint-level blockers. See Stakeholder Context above for watchlist risks._")
        else:
            out.append("_No blockers recorded._")
    out.append("")

    out.append("---")
    out.append("")
    out.append("## Notes")
    out.append("")
    tag = "backfilled" if ctx.get("is_backfill") else "generated"
    out.append(f"_Auto-{tag} by `.claude/scripts/generate_standup.py` on {datetime.now(MANILA).isoformat(timespec='minutes')}. Edit freely._")
    out.append("")

    return "\n".join(out)


def log(repo: Path, msg: str) -> None:
    log_file = repo / ".claude" / "scripts" / "generate-standup.log"
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(MANILA).isoformat(timespec="seconds")
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {msg}\n")
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--date", help="Override target date (YYYY-MM-DD), Asia/Manila. Used for historical backfill.")
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()

    try:
        real_today = today_manila()
        if args.date:
            try:
                today = date.fromisoformat(args.date)
            except ValueError:
                log(repo, f"bad --date {args.date!r}; falling back to today")
                today = real_today
        else:
            today = real_today
        is_backfill = today < real_today
        standups_dir = repo / "scrum" / "standups"
        out_file = standups_dir / f"{today.isoformat()}.md"

        if out_file.exists() and not args.force and not args.dry_run:
            log(repo, f"skip: {out_file.name} already exists")
            return 0

        pb_path = repo / "scrum" / "product-backlog.md"
        sprint_path = repo / "scrum" / "sprint-current.md"

        pb_fm, pb_body = ({}, "")
        if pb_path.exists():
            pb_fm, pb_body = parse_frontmatter(pb_path.read_text(encoding="utf-8"))

        sprint_fm, sprint_body = ({}, "")
        if sprint_path.exists():
            sprint_fm, sprint_body = parse_frontmatter(sprint_path.read_text(encoding="utf-8"))

        sprint_goal = ""
        in_goal = False
        for line in sprint_body.splitlines():
            if line.startswith("## Sprint Goal"):
                in_goal = True
                continue
            if in_goal and line.startswith("## "):
                break
            if in_goal and line.strip().startswith(">"):
                sprint_goal = line.strip().lstrip(">").strip()
                if sprint_goal:
                    break

        committed = parse_committed_items(sprint_body)
        board_counts = sprint_board_counts(committed)
        sprint_day = compute_sprint_day(sprint_fm, today)

        day, total, _rem = sprint_day
        at_risk: list[dict] = []
        if day is not None and total is not None and day > total / 2:
            at_risk = [it for it in committed
                       if not it["done"] and it["status"].lower() == "todo"
                       and it.get("priority", "").lower() in {"critical", "high"}]

        prior = find_prior_standup(standups_dir, today)
        if prior:
            prior_date = date.fromisoformat(prior.stem)
            since = datetime.combine(prior_date, datetime.min.time(), MANILA)
            gap = (today - prior_date).days
            if gap == 1:
                prior_label = f"since {prior_date.isoformat()}"
            else:
                prior_label = f"gap window {prior_date.isoformat()} → {(today - timedelta(days=1)).isoformat()} ({gap} days)"
        else:
            since = datetime.combine(today - timedelta(days=7), datetime.min.time(), MANILA)
            prior_label = "no prior standup on file (last 7 days)"

        upper = datetime.combine(today + timedelta(days=1), datetime.min.time(), MANILA) if is_backfill else None
        activity = scan_file_activity(repo, since, upper)

        pb_headline = extract_pb_headline(pb_body)
        pb_risks = extract_pb_risks(pb_body)
        pb_last_updated = pb_fm.get("last_updated", "")
        pb_stale_days = None
        if pb_last_updated:
            try:
                pb_stale_days = (today - date.fromisoformat(pb_last_updated)).days
            except ValueError:
                pass

        ctx = {
            "today": today,
            "project_name": pb_fm.get("project", repo.name),
            "sprint_fm": sprint_fm,
            "sprint_goal": sprint_goal,
            "committed": committed,
            "board_counts": board_counts,
            "sprint_day": sprint_day,
            "pb_headline": pb_headline,
            "pb_risks": pb_risks,
            "pb_last_updated": pb_last_updated,
            "pb_stale_days": pb_stale_days,
            "prior_standup_label": prior_label,
            "file_activity": activity,
            "at_risk": at_risk,
            "is_backfill": is_backfill,
        }

        content = render_standup(ctx)

        if args.dry_run:
            sys.stdout.write(content)
            return 0

        standups_dir.mkdir(parents=True, exist_ok=True)
        out_file.write_text(content, encoding="utf-8")
        log(repo, f"wrote: {out_file.name}")
        print(f"[generate_standup] wrote {out_file}")
        return 0

    except Exception as e:  # noqa: BLE001
        log(repo, f"error: {type(e).__name__}: {e}")
        log(repo, traceback.format_exc())
        return 0


if __name__ == "__main__":
    sys.exit(main())
