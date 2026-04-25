#!/usr/bin/env python3
"""
Generate release notes for a closed milestone, post to Slack, write CHANGELOG.md.

Reads closed issues in a milestone, groups them by type for stakeholder-friendly
release notes, and emits three outputs:
  1. Slack Block Kit payload posted to SLACK_WEBHOOK_URL
  2. Markdown body for the GitHub Release (printed to stdout when no GH token)
  3. A new entry prepended to CHANGELOG.md (if --update-changelog is passed)

Required env:
  GH_REPO              owner/repo
  SLACK_WEBHOOK_URL    Slack incoming webhook (skipped if --skip-slack)

CLI:
  --milestone-title "v1.1.1 — UAT Round 2"   pick milestone by title
  --milestone-number N                        pick milestone by number
  --update-changelog                          prepend an entry to CHANGELOG.md
  --create-release                            create a GitHub Release with the notes
  --skip-slack                                don't POST to Slack (useful for dry runs)
  --dry-run                                   print outputs only; no Slack/CHANGELOG/Release

Stakeholder copy strategy:
  We derive each line from the issue title + labels, NOT from issue body. Titles are
  already user-facing (file by tester, edited during triage), so they read naturally.
  Grouping is by label `type:*`: bug → "Fixed", ux → "Improved", validation → "Fixed",
  enhancement / feature → "Added". Severity is shown as a small inline tag for items
  that were Critical or High, so stakeholders can see priority at a glance.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = ROOT / "CHANGELOG.md"

SECTION_LABELS = {
    "Fixed": ("type:bug", "type:validation", "type:skip-logic", "type:sync", "type:i18n", "bug"),
    "Improved": ("type:ux",),
    "Added": ("enhancement",),
}
ALWAYS_OTHER = "Other"


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, check=True, encoding="utf-8")
    return result.stdout


def _gh_api(path: str) -> Any:
    out = _run(["gh", "api", path])
    return json.loads(out) if out.strip() else None


def find_milestone(repo: str, *, title: str | None, number: int | None) -> dict:
    if number is not None:
        return _gh_api(f"repos/{repo}/milestones/{number}")
    if title is None:
        raise SystemExit("Provide --milestone-title or --milestone-number")
    milestones = _gh_api(f"repos/{repo}/milestones?state=all&per_page=100")
    for m in milestones or []:
        if m["title"] == title:
            return m
    raise SystemExit(f"No milestone with title {title!r}")


def fetch_issues(repo: str, milestone_number: int) -> list[dict]:
    """Return all issues (open + closed) in the milestone, excluding PRs."""
    all_issues = _gh_api(
        f"repos/{repo}/issues?milestone={milestone_number}&state=all&per_page=100"
    )
    return [i for i in (all_issues or []) if "pull_request" not in i]


def group_for(issue: dict) -> str:
    labels = {l["name"] for l in issue.get("labels", [])}
    for section, candidates in SECTION_LABELS.items():
        if any(c in labels for c in candidates):
            return section
    return ALWAYS_OTHER


def severity_of(issue: dict) -> str | None:
    for l in issue.get("labels", []):
        name = l["name"]
        if name.startswith("severity:"):
            return name.split(":", 1)[1]
    return None


def humanise_title(raw: str) -> str:
    """Turn a GitHub issue title into a stakeholder-friendly line."""
    cleaned = raw.strip().rstrip(".")
    # Strip leading "Q##:" or "[Q##]"
    cleaned = re.sub(r"^\[?(Q\d+(?:\.\d+)?)\]?[\s:.-]+", lambda m: f"{m.group(1)}: ", cleaned)
    # Drop PR/issue refs that aren't useful in human notes
    cleaned = re.sub(r"\s+\(#\d+\)\s*$", "", cleaned)
    return cleaned


def build_markdown(milestone: dict, issues: list[dict]) -> str:
    title = milestone["title"]
    closed_at = milestone.get("closed_at") or milestone.get("updated_at") or ""
    iso_date = closed_at[:10] if closed_at else date.today().isoformat()
    closed_issues = [i for i in issues if i["state"] == "closed"]

    sections: dict[str, list[dict]] = {k: [] for k in SECTION_LABELS}
    sections[ALWAYS_OTHER] = []
    for iss in closed_issues:
        sections[group_for(iss)].append(iss)

    lines = [f"## {title} ({iso_date})", ""]
    if not closed_issues:
        lines += ["_No issues closed in this milestone._", ""]
        return "\n".join(lines)
    for section, items in sections.items():
        if not items:
            continue
        lines.append(f"### {section}")
        for iss in items:
            sev = severity_of(iss)
            tag = f"**[{sev.upper()}]** " if sev in ("critical", "high") else ""
            lines.append(f"- {tag}{humanise_title(iss['title'])} ([#{iss['number']}]({iss['html_url']}))")
        lines.append("")
    return "\n".join(lines)


def build_slack_blocks(milestone: dict, issues: list[dict], release_url: str | None) -> list[dict]:
    title = milestone["title"]
    closed_count = sum(1 for i in issues if i["state"] == "closed")

    sections: dict[str, list[dict]] = {k: [] for k in SECTION_LABELS}
    sections[ALWAYS_OTHER] = []
    for iss in issues:
        if iss["state"] != "closed":
            continue
        sections[group_for(iss)].append(iss)

    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f":tada: {title} — release"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{closed_count} issue{'s' if closed_count != 1 else ''} closed.* "
                        f"Highlights below — full notes: <{release_url or '#'}|GitHub release>.",
            },
        },
        {"type": "divider"},
    ]

    for section, items in sections.items():
        if not items:
            continue
        # Take up to 6 highlights per section to keep the post tight
        highlights = items[:6]
        more = len(items) - len(highlights)
        text_lines = [f"*{section}*"]
        for iss in highlights:
            sev = severity_of(iss)
            badge = f" `{sev.upper()}`" if sev in ("critical", "high") else ""
            text_lines.append(
                f"• <{iss['html_url']}|#{iss['number']}>{badge} {humanise_title(iss['title'])}"
            )
        if more > 0:
            text_lines.append(f"_…and {more} more_")
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(text_lines)}})

    return blocks


def post_slack(blocks: list[dict], fallback_text: str) -> None:
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        print("SLACK_WEBHOOK_URL not set — skipping Slack post.", file=sys.stderr)
        return
    payload = json.dumps({"blocks": blocks, "text": fallback_text}).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
        if body.strip() != "ok":
            print(f"Slack response: {body}", file=sys.stderr)


CHANGELOG_INTRO = (
    "# Changelog\n\n"
    "All notable changes to this project are documented here. "
    "Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n"
)


def update_changelog(entry_md: str) -> None:
    """Prepend `entry_md` above any existing `## ` entries, keeping the intro intact.
    Idempotent: a duplicate heading is detected and the file is left unchanged."""
    if not CHANGELOG.exists():
        CHANGELOG.write_text(CHANGELOG_INTRO + entry_md + "\n", encoding="utf-8")
        return
    existing = CHANGELOG.read_text(encoding="utf-8")
    first_heading = entry_md.splitlines()[0]
    if first_heading in existing:
        print(f"CHANGELOG already has {first_heading!r}; skipping prepend.", file=sys.stderr)
        return
    # Anchor on the first `## ` heading — insert the new entry just before it.
    # If no entry headings exist yet, append after the intro.
    match = re.search(r"^## ", existing, flags=re.MULTILINE)
    if match:
        idx = match.start()
        new = existing[:idx] + entry_md + "\n" + existing[idx:]
    elif existing.startswith("# Changelog"):
        new = existing.rstrip() + "\n\n" + entry_md + "\n"
    else:
        new = CHANGELOG_INTRO + entry_md + "\n" + existing
    CHANGELOG.write_text(new, encoding="utf-8")


def create_github_release(repo: str, milestone: dict, body_md: str) -> str | None:
    """Create a GitHub Release with the milestone title as the tag. Returns html_url."""
    tag = milestone["title"].split(" ", 1)[0]  # e.g. "v1.1.1" from "v1.1.1 — UAT Round 2"
    notes_path = Path(os.environ.get("RUNNER_TEMP", os.environ.get("TMP", "/tmp"))) / f"release_notes_{tag}.md"
    notes_path.write_text(body_md, encoding="utf-8")
    try:
        out = _run(
            [
                "gh", "release", "create", tag,
                "--repo", repo,
                "--title", milestone["title"],
                "--notes-file", str(notes_path),
            ]
        )
        return out.strip() or None
    except subprocess.CalledProcessError as e:
        # Most likely cause: tag already exists. Update the notes instead.
        if "already exists" in (e.stderr or ""):
            try:
                _run(
                    [
                        "gh", "release", "edit", tag,
                        "--repo", repo,
                        "--notes-file", str(notes_path),
                    ]
                )
                view = _run(["gh", "release", "view", tag, "--repo", repo, "--json", "url"])
                return json.loads(view)["url"]
            except subprocess.CalledProcessError as e2:
                print(f"Release update failed: {e2.stderr}", file=sys.stderr)
                return None
        print(f"Release creation failed: {e.stderr}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--milestone-title")
    parser.add_argument("--milestone-number", type=int)
    parser.add_argument("--update-changelog", action="store_true")
    parser.add_argument("--create-release", action="store_true")
    parser.add_argument("--skip-slack", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo = os.environ.get("GH_REPO")
    if not repo:
        print("GH_REPO env var required (e.g. cplreyes/ASPSI-DOH-UHC-CAPI-Development)", file=sys.stderr)
        return 1

    milestone = find_milestone(repo, title=args.milestone_title, number=args.milestone_number)
    issues = fetch_issues(repo, milestone["number"])
    md = build_markdown(milestone, issues)

    print("=== Markdown ===")
    print(md)

    release_url: str | None = None
    if args.create_release and not args.dry_run:
        release_url = create_github_release(repo, milestone, md)
        if release_url:
            print(f"Created release: {release_url}", file=sys.stderr)

    if args.update_changelog and not args.dry_run:
        update_changelog(md)

    blocks = build_slack_blocks(milestone, issues, release_url)
    if args.dry_run:
        print("=== Slack payload ===")
        print(json.dumps({"blocks": blocks}, indent=2))
        return 0
    if not args.skip_slack:
        post_slack(blocks, fallback_text=f"{milestone['title']} — release")
        print("Slack post sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
