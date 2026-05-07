"""Post cross-sprint summary snapshot to Slack #capi-scrum.

Queries GH Project #8 (UHC CAPI - Backlog) for all cards, aggregates by
Sprint Slot x Status, and posts a monospace summary table.

Modes (controls header framing only; table contents identical):
  start   Monday morning sprint kickoff: ":rocket: Sprint NNN kickoff snapshot"
  close   Friday EOD sprint closeout:    ":bar_chart: Sprint NNN closeout snapshot"
  test    Local dry-run: prints to stdout, does NOT post to Slack

Env:
  SLACK_WEBHOOK_URL   required for non-test modes
  GH_PROJECTS_TOKEN   required PAT with `read:project` scope (or `project` for classic)
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
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(os.environ.get("GITHUB_WORKSPACE") or Path(__file__).resolve().parents[2])
SPRINT_CURRENT = REPO_ROOT / "scrum" / "sprint-current.md"

OWNER = "cplreyes"
PROJECT_NUMBER = 8
PROJECT_URL = f"https://github.com/users/{OWNER}/projects/{PROJECT_NUMBER}"

# Order to display rows (Sprint Slot column).
SPRINT_ORDER = [
    "sprint-001", "sprint-002", "sprint-003", "sprint-004",
    "sprint-005", "sprint-006", "sprint-007", "sprint-008",
]


def gh_token() -> str:
    tok = os.environ.get("GH_PROJECTS_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not tok:
        print("ERROR: no GH token in env (set GH_PROJECTS_TOKEN with `read:project` scope).", file=sys.stderr)
        sys.exit(1)
    return tok


def gh_graphql(query: str, variables: dict | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {gh_token()}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": "uhc-capi-sprint-snapshot",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read())
    if "errors" in body:
        print(f"GraphQL errors: {body['errors']}", file=sys.stderr)
        sys.exit(1)
    return body["data"]


def fetch_project_items() -> list[dict]:
    """Return list of {sprint_slot, status} for every card on Project #8."""
    q = """
    query($cursor: String) {
      user(login: "%s") {
        projectV2(number: %d) {
          items(first: 100, after: $cursor) {
            pageInfo { hasNextPage endCursor }
            nodes {
              fieldValues(first: 30) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    field { ... on ProjectV2SingleSelectField { name } }
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
    """ % (OWNER, PROJECT_NUMBER)

    items = []
    cursor = None
    while True:
        data = gh_graphql(q, {"cursor": cursor})
        page = data["user"]["projectV2"]["items"]
        for it in page["nodes"]:
            fields = {}
            for fv in it["fieldValues"]["nodes"]:
                if fv and fv.get("field") and fv.get("name"):
                    fields[fv["field"]["name"]] = fv["name"]
            items.append({
                "sprint_slot": fields.get("Sprint Slot"),
                "status": fields.get("Status"),
            })
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return items


def aggregate(items: list[dict]) -> tuple[dict, int, int, int]:
    """Returns (counts_by_slot, total_done, total_todo, grand_total).

    counts_by_slot[slot] = {"done": N, "todo": M, "in_progress": K}
    """
    counts = defaultdict(lambda: {"done": 0, "todo": 0, "in_progress": 0, "review": 0})
    for it in items:
        slot = it.get("sprint_slot") or "(no slot)"
        status = (it.get("status") or "Todo").lower().replace(" ", "_")
        # Bucket: Done vs anything-else (Todo / In Progress / Review)
        if status == "done":
            counts[slot]["done"] += 1
        elif status == "in_progress":
            counts[slot]["in_progress"] += 1
        elif status == "review":
            counts[slot]["review"] += 1
        else:
            counts[slot]["todo"] += 1

    total_done = sum(c["done"] for c in counts.values())
    total_open = sum(c["todo"] + c["in_progress"] + c["review"] for c in counts.values())
    grand_total = sum(c["done"] + c["todo"] + c["in_progress"] + c["review"] for c in counts.values())
    return dict(counts), total_done, total_open, grand_total


def get_current_sprint_number() -> str:
    """Best-effort: read sprint number from sprint-current.md frontmatter."""
    if not SPRINT_CURRENT.exists():
        return "?"
    text = SPRINT_CURRENT.read_text(encoding="utf-8")
    m = re.search(r"^sprint:\s*(\d+)", text, re.MULTILINE)
    return m.group(1) if m else "?"


def render_table(counts: dict, total_done: int, total_open: int, grand_total: int) -> str:
    """Monospace table fitted for Slack code block."""
    rows = []
    rows.append(("Sprint", "Done", "Open", "Total"))
    rows.append(("-" * 12, "-" * 4, "-" * 4, "-" * 5))

    # Pre-defined sprint slots in order
    slots_seen = set()
    for slot in SPRINT_ORDER:
        if slot not in counts:
            continue
        c = counts[slot]
        open_n = c["todo"] + c["in_progress"] + c["review"]
        done_n = c["done"]
        total = open_n + done_n
        done_str = str(done_n) if done_n else "-"
        open_str = str(open_n) if open_n else "-"
        rows.append((slot, done_str, open_str, str(total)))
        slots_seen.add(slot)

    # Any other slots (unscheduled, no-slot, future labels)
    for slot in sorted(counts.keys()):
        if slot in slots_seen:
            continue
        c = counts[slot]
        open_n = c["todo"] + c["in_progress"] + c["review"]
        done_n = c["done"]
        total = open_n + done_n
        done_str = str(done_n) if done_n else "-"
        open_str = str(open_n) if open_n else "-"
        rows.append((slot, done_str, open_str, str(total)))

    rows.append(("-" * 12, "-" * 4, "-" * 4, "-" * 5))
    rows.append(("TOTAL", str(total_done), str(total_open), str(grand_total)))

    # Compute column widths
    widths = [max(len(row[i]) for row in rows) for i in range(4)]
    lines = []
    for row in rows:
        lines.append(f"{row[0]:<{widths[0]}}  {row[1]:>{widths[1]}}  {row[2]:>{widths[2]}}  {row[3]:>{widths[3]}}")
    return "\n".join(lines)


def render_breakdown_by_status(counts: dict) -> str:
    """If any sprint has cards in In Progress or Review, surface that."""
    in_progress_total = sum(c["in_progress"] for c in counts.values())
    review_total = sum(c["review"] for c in counts.values())
    if in_progress_total + review_total == 0:
        return ""
    parts = []
    if in_progress_total:
        parts.append(f":hammer_and_wrench: {in_progress_total} In Progress")
    if review_total:
        parts.append(f":mag: {review_total} Review")
    return " · ".join(parts)


def render_message(mode: str, counts: dict, total_done: int, total_open: int, grand_total: int) -> str:
    sprint_n = get_current_sprint_number()

    if mode == "start":
        header = f":rocket: *Sprint {sprint_n} — kickoff snapshot* (active backlog state)"
    elif mode == "close":
        header = f":bar_chart: *Sprint {sprint_n} — closeout snapshot* (active backlog state)"
    else:
        header = f":clipboard: *Backlog snapshot — Sprint {sprint_n}* (manual run)"

    table = render_table(counts, total_done, total_open, grand_total)
    breakdown = render_breakdown_by_status(counts)

    lines = [header, ""]
    lines.append("```")
    lines.append(table)
    lines.append("```")
    if breakdown:
        lines.append(breakdown)
    lines.append("")
    lines.append(f"<{PROJECT_URL}|Open board on GitHub Projects>")
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

    items = fetch_project_items()
    counts, total_done, total_open, grand_total = aggregate(items)
    text = render_message(
        submode if mode == "test" else mode,
        counts, total_done, total_open, grand_total,
    )

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
