#!/usr/bin/env python3
"""
Build and post a UAT progress digest to Slack.

Reads issues from the GitHub repo using the gh CLI (already auth'd in GitHub Actions
via GITHUB_TOKEN), groups by milestone / status / severity, and posts a snapshot
to the Slack webhook.

Required env vars:
  SLACK_WEBHOOK_URL  Slack incoming webhook URL
  GH_REPO            owner/repo (e.g. cplreyes/ASPSI-DOH-UHC-CAPI-Development)

Optional:
  DRY_RUN=1          Print payload to stdout instead of posting
  DIGEST_TZ          Timezone for the timestamp (default: Asia/Manila)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any


PROJECT_URL = "https://github.com/users/cplreyes/projects/7"
STAGING_URL = "https://5466a539.f2-pwa-staging.pages.dev"
PROD_URL = "https://f2-pwa.pages.dev"


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, check=True, encoding="utf-8")
    return result.stdout


def gh(args: list[str]) -> Any:
    """Run gh and parse JSON output."""
    repo = os.environ["GH_REPO"]
    out = _run(["gh"] + args + ["--repo", repo])
    return json.loads(out) if out.strip() else None


def get_open_milestones() -> list[dict]:
    out = _run([
        "gh", "api",
        f"repos/{os.environ['GH_REPO']}/milestones",
        "--jq", "[.[] | select(.state == \"open\")]",
    ])
    return json.loads(out) if out.strip() else []


def get_all_issues() -> list[dict]:
    return gh(["issue", "list", "--state", "all", "--limit", "200", "--json",
               "number,title,state,url,labels,milestone,createdAt,updatedAt,closedAt,author"])


def labels_of(issue: dict) -> set[str]:
    return {lbl["name"] for lbl in issue.get("labels") or []}


def severity_of(issue: dict) -> str | None:
    for lbl in labels_of(issue):
        if lbl.startswith("severity:"):
            return lbl.split(":", 1)[1]
    return None


def status_of(issue: dict) -> str:
    """Derive a coarse status from labels + state."""
    if issue["state"] == "CLOSED":
        return "closed"
    lbls = labels_of(issue)
    if "status:fixed-pending-verify" in lbls:
        return "fixed-pending-verify"
    if "status:investigating" in lbls:
        return "investigating"
    if "status:blocked" in lbls:
        return "blocked"
    return "todo"


def round_of(issue: dict) -> str | None:
    for lbl in labels_of(issue):
        if lbl.startswith("round:"):
            return lbl.split(":", 1)[1]
    return None


def is_active_round(milestones: list[dict], issues: list[dict]) -> bool:
    """A round is 'active' if there's an open milestone with any issue activity in last 14 days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    open_milestone_titles = {m["title"] for m in milestones}
    for iss in issues:
        ms = iss.get("milestone")
        if ms and ms.get("title") in open_milestone_titles:
            updated = datetime.fromisoformat(iss["updatedAt"].replace("Z", "+00:00"))
            if updated >= cutoff:
                return True
    return False


SEV_EMOJI = {
    "critical": ":red_circle:",
    "high": ":large_orange_circle:",
    "medium": ":large_yellow_circle:",
    "low": ":large_green_circle:",
}

STATUS_EMOJI = {
    "todo": ":inbox_tray:",
    "investigating": ":mag:",
    "fixed-pending-verify": ":white_check_mark:",
    "blocked": ":no_entry:",
    "closed": ":dart:",
}

SEV_ORDER = ["critical", "high", "medium", "low"]
STATUS_ORDER = ["investigating", "todo", "fixed-pending-verify", "blocked", "closed"]


def build_blocks(milestones: list[dict], issues: list[dict]) -> list[dict]:
    open_issues = [i for i in issues if i["state"] == "OPEN"]
    closed_issues = [i for i in issues if i["state"] == "CLOSED"]

    # Recent activity (last 24h)
    cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = []
    for iss in issues:
        for ts_field, action in [("createdAt", "opened"), ("closedAt", "closed")]:
            ts_raw = iss.get(ts_field)
            if not ts_raw:
                continue
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            if ts >= cutoff_24h:
                recent.append((ts, action, iss))
    recent.sort(reverse=True)

    # Status breakdown (open only)
    status_counts = Counter(status_of(i) for i in open_issues)
    sev_counts = Counter()
    for i in open_issues:
        s = severity_of(i)
        if s:
            sev_counts[s] += 1

    # Milestone progress
    milestone_lines = []
    by_ms_open = Counter()
    by_ms_closed = Counter()
    for iss in issues:
        ms = iss.get("milestone")
        if not ms:
            continue
        if iss["state"] == "OPEN":
            by_ms_open[ms["title"]] += 1
        else:
            by_ms_closed[ms["title"]] += 1
    for m in milestones:
        title = m["title"]
        opened = by_ms_open.get(title, 0)
        closed = by_ms_closed.get(title, 0)
        total = opened + closed
        if total == 0:
            continue
        milestone_lines.append(f"• *{title}* — {closed}/{total} closed")

    # Top critical/high open
    top = sorted(
        [i for i in open_issues if severity_of(i) in ("critical", "high")],
        key=lambda i: (SEV_ORDER.index(severity_of(i) or "low"), i["number"]),
    )[:5]

    tz_name = os.environ.get("DIGEST_TZ", "Asia/Manila")
    now_local = datetime.now(timezone(timedelta(hours=8)))  # MNL is UTC+8

    blocks: list[dict] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":test_tube: F2 PWA UAT — Daily Snapshot",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"_{now_local.strftime('%A, %B %d, %Y · %H:%M %Z')}_ · `{os.environ['GH_REPO']}`",
                }
            ],
        },
        {"type": "divider"},
    ]

    if milestone_lines:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Milestone progress*\n" + "\n".join(milestone_lines)},
        })

    status_lines = []
    for s in STATUS_ORDER:
        if status_counts.get(s):
            status_lines.append(f"{STATUS_EMOJI.get(s, '·')} *{s}*: {status_counts[s]}")
    sev_lines = []
    for s in SEV_ORDER:
        if sev_counts.get(s):
            sev_lines.append(f"{SEV_EMOJI[s]} *{s}*: {sev_counts[s]}")

    fields = []
    if status_lines:
        fields.append({"type": "mrkdwn", "text": "*Status (open)*\n" + "\n".join(status_lines)})
    if sev_lines:
        fields.append({"type": "mrkdwn", "text": "*Severity (open)*\n" + "\n".join(sev_lines)})
    if fields:
        blocks.append({"type": "section", "fields": fields})

    if top:
        top_lines = []
        for iss in top:
            sev = severity_of(iss) or "?"
            top_lines.append(f"{SEV_EMOJI.get(sev, '·')} <{iss['url']}|#{iss['number']}> {iss['title']}")
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Top open by severity*\n" + "\n".join(top_lines)},
        })

    if recent:
        recent_lines = []
        for ts, action, iss in recent[:6]:
            recent_lines.append(f"• `[{action}]` <{iss['url']}|#{iss['number']}> {iss['title']}")
        if len(recent) > 6:
            recent_lines.append(f"_…and {len(recent) - 6} more_")
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Recent activity (last 24h)*\n" + "\n".join(recent_lines)},
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "actions",
        "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Project board"}, "url": PROJECT_URL},
            {"type": "button", "text": {"type": "plain_text", "text": "Open issues"}, "url": f"https://github.com/{os.environ['GH_REPO']}/issues"},
            {"type": "button", "text": {"type": "plain_text", "text": "File a bug"}, "url": f"https://github.com/{os.environ['GH_REPO']}/issues/new/choose"},
            {"type": "button", "text": {"type": "plain_text", "text": "Staging"}, "url": STAGING_URL},
        ],
    })

    return blocks


def post(blocks: list[dict]) -> None:
    payload = {
        "blocks": blocks,
        "text": "F2 PWA UAT — Daily Snapshot",  # fallback for notifications
    }
    if os.environ.get("DRY_RUN") == "1":
        print(json.dumps(payload, indent=2))
        return
    webhook = os.environ["SLACK_WEBHOOK_URL"]
    req = urllib.request.Request(
        webhook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
        if body.strip() != "ok":
            print(f"Slack response: {body}", file=sys.stderr)
            sys.exit(1)


def main() -> int:
    try:
        milestones = get_open_milestones()
        issues = get_all_issues()
    except subprocess.CalledProcessError as e:
        print(f"gh error: {e.stderr}", file=sys.stderr)
        return 1

    only_when_active = os.environ.get("ONLY_WHEN_ACTIVE", "1") == "1"
    if only_when_active and not is_active_round(milestones, issues):
        print("No active UAT round — skipping post.")
        return 0

    blocks = build_blocks(milestones, issues)
    post(blocks)
    print("Digest posted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
