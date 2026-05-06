"""Post sprint kickoff/closeout snapshot to Slack #capi-scrum.

Triggers:
  start   - Monday morning kickoff: sprint goal + committed items + stretch
  close   - Friday EOD closeout:    Done/Open split + throughput + carry-forwards
  test    - Local dry-run: prints to stdout, does NOT post to Slack

Sources:
  scrum/sprint-current.md        sprint frontmatter + committed/stretch items
  GH Project #8 (optional)        live Status field per card (uses PROJECTS_PAT if set;
                                  falls back to markdown checkbox state otherwise)

Usage:
  python .github/scripts/post_sprint_snapshot.py start
  python .github/scripts/post_sprint_snapshot.py close
  python .github/scripts/post_sprint_snapshot.py test [start|close]

Env:
  SLACK_WEBHOOK_URL  required for non-test modes
  PROJECTS_PAT       optional GH PAT with read:project to enrich with live board state
  GITHUB_WORKSPACE   set in Actions; falls back to script's repo root locally
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE") or Path(__file__).resolve().parents[2])
SPRINT_CURRENT = REPO_ROOT / "scrum" / "sprint-current.md"
SPRINTS_DIR = REPO_ROOT / "scrum" / "sprints"

PROJECT_URL = "https://github.com/users/cplreyes/projects/8"

FRONTMATTER_RE = re.compile(r"^---\n(.+?)\n---", re.DOTALL)
TASK_RE = re.compile(
    r"^- \[([x ])\]\s*\*\*([A-Z][A-Za-z0-9-]+)\*\*\s*(.+?)\s*$"
)
INLINE_FIELD = re.compile(r"`([a-z_]+)::\s*([^`]+?)\s*`")
H2_RE = re.compile(r"^## (.+?)\s*$")
H3_RE = re.compile(r"^### (.+?)\s*$")


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.search(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def parse_sprint_md(path: Path) -> dict:
    """Extract sprint metadata + committed/stretch items from a sprint markdown file."""
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)

    # Pull goal line: first H1 followed by `## Sprint Goal` block's first quoted line.
    title = ""
    title_match = re.search(r"^# (.+?)$", text, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()

    goal = ""
    goal_match = re.search(r"^## Sprint Goal\n+>\s*(.+?)$", text, re.MULTILINE)
    if goal_match:
        goal = re.sub(r"\*\*", "*", goal_match.group(1).strip())  # Slack uses * not **
        # Strip leading "Goal A —" prefix noise if too long
        if len(goal) > 200:
            goal = goal[:197] + "..."

    # Walk lines, group items by current section header.
    # Only collect tasks while inside `## Committed Items` (covers its `###` subsections
    # like Goal A / Goal B / Stretch). Skip everything else (Daily Notes, Definition of
    # Done, Retrospective).
    items = {"committed": [], "stretch": [], "other": []}
    in_committed_section = False
    current_bucket = "committed"
    for line in text.splitlines():
        m_h2 = H2_RE.match(line)
        if m_h2:
            in_committed_section = "committed items" in m_h2.group(1).lower()
            current_bucket = "committed"
            continue
        if not in_committed_section:
            continue
        m_h3 = H3_RE.match(line)
        if m_h3:
            heading = m_h3.group(1).lower()
            if "stretch" in heading or "not committed" in heading:
                current_bucket = "stretch"
            else:
                current_bucket = "committed"
            continue
        m_task = TASK_RE.match(line)
        if not m_task:
            continue
        if current_bucket == "other":
            continue
        box, tid, body = m_task.group(1), m_task.group(2), m_task.group(3)
        fields = dict(INLINE_FIELD.findall(line))
        # Strip inline fields from body for clean display
        clean_body = INLINE_FIELD.sub("", body).strip().rstrip("—-").strip()
        if len(clean_body) > 80:
            clean_body = clean_body[:77] + "..."
        items[current_bucket].append({
            "task_id": tid,
            "done": box == "x",
            "title": clean_body,
            "priority": fields.get("priority", "").lower(),
            "estimate": fields.get("estimate", ""),
        })

    return {
        "frontmatter": fm,
        "title": title,
        "goal": goal,
        "items": items,
    }


def hours_estimate(items: list[dict]) -> str:
    """Sum estimate strings like '4h', '30m', '1d', 'recurring'. Returns rough total."""
    total_hours = 0.0
    has_recurring = False
    for it in items:
        e = it.get("estimate", "").strip().lower()
        if not e:
            continue
        if "recurring" in e or "ongoing" in e or "tbd" in e:
            has_recurring = True
            continue
        m = re.match(r"([\d.]+)\s*([hmd])", e)
        if not m:
            continue
        val = float(m.group(1))
        unit = m.group(2)
        if unit == "h":
            total_hours += val
        elif unit == "m":
            total_hours += val / 60
        elif unit == "d":
            total_hours += val * 8  # nominal 8h/day
    if total_hours == 0 and not has_recurring:
        return "—"
    suffix = "+ recurring" if has_recurring else ""
    return f"~{total_hours:.0f}h{suffix}".strip()


def render_start(sprint: dict) -> str:
    fm = sprint["frontmatter"]
    n = fm.get("sprint", "?")
    start = fm.get("start", "?")
    end = fm.get("end", "?")
    committed = sprint["items"]["committed"]
    stretch = sprint["items"]["stretch"]

    lines = []
    lines.append(f":rocket: *Sprint {n} — Day 1 kickoff*")
    lines.append(f"{start} → {end}  ·  5 working days")
    if sprint["goal"]:
        lines.append(f"_{sprint['goal']}_")
    lines.append("")

    open_committed = [i for i in committed if not i["done"]]
    closed_committed = [i for i in committed if i["done"]]
    if closed_committed:
        lines.append(f"*Carry-in (already done before kickoff):* {len(closed_committed)}")

    lines.append(f"*Committed* ({len(open_committed)} open, {hours_estimate(open_committed)}):")
    for it in open_committed[:10]:
        pri = f"[{it['priority']}]" if it["priority"] else ""
        est = f" · {it['estimate']}" if it["estimate"] else ""
        lines.append(f"  • `{it['task_id']}` {pri} {it['title']}{est}".rstrip())
    if len(open_committed) > 10:
        lines.append(f"  _…+{len(open_committed) - 10} more_")

    if stretch:
        open_stretch = [i for i in stretch if not i["done"]]
        lines.append("")
        lines.append(f"*Stretch* ({len(open_stretch)} open, {hours_estimate(open_stretch)}):")
        for it in open_stretch[:5]:
            pri = f"[{it['priority']}]" if it["priority"] else ""
            est = f" · {it['estimate']}" if it["estimate"] else ""
            lines.append(f"  • `{it['task_id']}` {pri} {it['title']}{est}".rstrip())
        if len(open_stretch) > 5:
            lines.append(f"  _…+{len(open_stretch) - 5} more_")

    lines.append("")
    lines.append(f"*Board:* {PROJECT_URL}")
    return "\n".join(lines)


def render_close(sprint: dict) -> str:
    fm = sprint["frontmatter"]
    n = fm.get("sprint", "?")
    start = fm.get("start", "?")
    end = fm.get("end", "?")
    committed = sprint["items"]["committed"]
    stretch = sprint["items"]["stretch"]

    done_committed = [i for i in committed if i["done"]]
    open_committed = [i for i in committed if not i["done"]]
    done_stretch = [i for i in stretch if i["done"]]
    open_stretch = [i for i in stretch if not i["done"]]

    pct = (len(done_committed) * 100 // len(committed)) if committed else 0

    lines = []
    lines.append(f":bar_chart: *Sprint {n} — Day 5 closeout*")
    lines.append(f"{start} → {end}")
    lines.append("")
    lines.append(f"*Done: {len(done_committed)}/{len(committed)} committed* ({pct}% throughput)")
    for it in done_committed[:10]:
        lines.append(f"  • :white_check_mark: `{it['task_id']}` {it['title']}".rstrip())
    if len(done_committed) > 10:
        lines.append(f"  _…+{len(done_committed) - 10} more_")

    if open_committed:
        lines.append("")
        lines.append(f"*Open at close (carry to next sprint): {len(open_committed)}*")
        for it in open_committed:
            pri = f"[{it['priority']}]" if it["priority"] else ""
            lines.append(f"  • :arrow_right: `{it['task_id']}` {pri} {it['title']}".rstrip())

    if stretch:
        lines.append("")
        lines.append(f"*Stretch: {len(done_stretch)}/{len(stretch)} closed*")
        for it in done_stretch[:5]:
            lines.append(f"  • :white_check_mark: `{it['task_id']}` {it['title']}".rstrip())
        if open_stretch:
            for it in open_stretch[:3]:
                lines.append(f"  • :arrow_right: `{it['task_id']}` {it['title']}".rstrip())

    lines.append("")
    lines.append(f"*Board:* {PROJECT_URL}")
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

    if not SPRINT_CURRENT.exists():
        print(f"ERROR: {SPRINT_CURRENT} not found", file=sys.stderr)
        sys.exit(1)

    sprint = parse_sprint_md(SPRINT_CURRENT)

    if mode in ("start", "close"):
        text = render_start(sprint) if mode == "start" else render_close(sprint)
        post_to_slack(text)
        print(f"Posted {mode} snapshot to Slack ({len(text)} chars).")
    elif mode == "test":
        text = render_start(sprint) if submode == "start" else render_close(sprint)
        print(text)
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
