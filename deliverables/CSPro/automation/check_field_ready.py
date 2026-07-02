#!/usr/bin/env python3
"""
CAPI field-readiness gate — the automatic stop-condition for the
`capi-uat-triage` loop (the second half of Sprint-012 E0-UAT-REFRAME).

The field-readiness exit criterion was *operationalized* in the R5 close-out
(`deliverables/CSPro/CAPI-UAT-Round-5-Closeout-2026-06-29.md`) and applied by
hand. This script *wires it into the loop* so "should I keep triaging?" is an
objective check instead of a judgment call each cycle.

The criterion (verbatim from the close-out), made checkable:
  1. ZERO open *actionable* F1/F3/F4 tester issues — open `bug` issues carrying
     an `epic:f1|f3|f4` label, excluding ASPSI-owned carve-outs.
  2. NO new tester-blocking finding for a quiet window — the newest actionable
     finding is at least `--quiet-days` (default 2) old.
  3. ASPSI-owned items carved out — translations and spec/structural decisions
     are ASPSI's lane; they don't block field-readiness. Carved out by label
     (anything matching blocked / parked / aspsi / translat / spec / question /
     wontfix / hold / duplicate / invalid).

Verdicts (also the process exit code, so a shell can gate on it):
  FIELD-READY   (exit 0)  — criteria 1+2 met; the loop can STOP.
  CLEAR-PENDING (exit 10) — 0 open, but a finding landed inside the quiet
                            window; let it settle, keep looping.
  NOT-READY     (exit 20) — open actionable issues remain; keep triaging.
  UNKNOWN       (exit 30) — couldn't reach GitHub; NEVER declares ready on
                            missing data.

Each run persists a `field_ready` block into triage-state.json (last verdict,
quiet-streak, last finding time, a short history) so the loop and the daily
standup share one source of truth. Advisory by design — it reads GitHub and
records state; it never closes issues or edits instruments.

    python check_field_ready.py [--quiet-days N] [--json] [--no-write]
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

GH_REPO = "cplreyes/ASPSI-DOH-UHC-CAPI-Development"
# F1/F3/F4 only — F2 (PWA) is a separate track and a separate hotfix queue.
EPIC_LABELS = {"epic:f1", "epic:f3", "epic:f4"}
# An open issue carrying any of these (as a substring of a label) is ASPSI's
# lane or otherwise not a field-readiness blocker — carved out per criterion 3.
CARVE_OUT_SUBSTRINGS = (
    "block", "park", "hold", "aspsi", "translat", "spec",
    "question", "wontfix", "won't", "duplicate", "invalid", "decision",
)
QUIET_DAYS_DEFAULT = 2.0

VERDICT_EXIT = {"FIELD-READY": 0, "CLEAR-PENDING": 10, "NOT-READY": 20, "UNKNOWN": 30}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def run_gh(args: list[str], timeout: int = 30) -> tuple[str | None, str | None]:
    exe = shutil.which("gh") or "gh"
    try:
        res = subprocess.run(
            [exe, *args], capture_output=True, text=True,
            timeout=timeout, encoding="utf-8",
        )
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"{type(e).__name__}: {e}"
    if res.returncode != 0:
        return None, (res.stderr or "").strip() or f"gh exit {res.returncode}"
    return res.stdout, None


def fetch_issues(repo: str, limit: int = 150) -> tuple[list | None, str | None]:
    out, err = run_gh([
        "issue", "list", "-R", repo, "--state", "all", "--label", "bug",
        "--json", "number,title,labels,createdAt,state", "--limit", str(limit),
    ])
    if err:
        return None, err
    try:
        return json.loads(out), None
    except (ValueError, TypeError) as e:
        return None, f"json parse: {e}"


def label_names(issue: dict) -> list[str]:
    return [l.get("name", "").lower() for l in issue.get("labels", [])]


def is_carved_out(names: list[str]) -> bool:
    return any(any(sub in n for sub in CARVE_OUT_SUBSTRINGS) for n in names)


def is_actionable(issue: dict) -> bool:
    """F1/F3/F4 tester finding that genuinely blocks field-readiness."""
    names = label_names(issue)
    if not any(e in names for e in EPIC_LABELS):
        return False
    if is_carved_out(names):
        return False
    return True


def evaluate(repo: str, quiet_days: float) -> dict:
    issues, err = fetch_issues(repo)
    now = now_utc()
    if err is not None:
        return {
            "verdict": "UNKNOWN",
            "evaluated_at": now.isoformat(timespec="seconds"),
            "error": err,
            "open_actionable": None,
            "open_issues": [],
            "last_finding_at": None,
            "days_since_finding": None,
            "quiet_days": quiet_days,
        }

    actionable = [i for i in issues if is_actionable(i)]
    open_actionable = [i for i in actionable if i.get("state", "").upper() == "OPEN"]

    finding_dates = [d for d in (parse_iso(i.get("createdAt", "")) for i in actionable) if d]
    last_finding = max(finding_dates) if finding_dates else None
    days_since = (now - last_finding).total_seconds() / 86400.0 if last_finding else None

    if open_actionable:
        verdict = "NOT-READY"
    elif days_since is not None and days_since < quiet_days:
        verdict = "CLEAR-PENDING"
    else:
        verdict = "FIELD-READY"

    return {
        "verdict": verdict,
        "evaluated_at": now.isoformat(timespec="seconds"),
        "error": None,
        "open_actionable": len(open_actionable),
        "open_issues": [
            {"number": i["number"], "title": i.get("title", ""),
             "labels": [l for l in label_names(i) if l != "bug"]}
            for i in sorted(open_actionable, key=lambda x: x["number"])
        ],
        "last_finding_at": last_finding.isoformat(timespec="seconds") if last_finding else None,
        "days_since_finding": round(days_since, 1) if days_since is not None else None,
        "quiet_days": quiet_days,
    }


def persist(state_path: Path, result: dict) -> str | None:
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return f"read triage-state: {e}"

    prev = data.get("field_ready", {}) if isinstance(data.get("field_ready"), dict) else {}
    prev_streak = int(prev.get("consecutive_clear_evals", 0) or 0)
    if result["verdict"] == "FIELD-READY":
        streak = prev_streak + 1
    elif result["verdict"] == "UNKNOWN":
        streak = prev_streak  # missing data doesn't reset progress
    else:
        streak = 0

    history = prev.get("history", [])
    if not isinstance(history, list):
        history = []
    history.append({
        "at": result["evaluated_at"],
        "verdict": result["verdict"],
        "open_actionable": result["open_actionable"],
        "days_since_finding": result["days_since_finding"],
    })
    history = history[-10:]

    data["field_ready"] = {
        "last_verdict": result["verdict"],
        "last_evaluated_at": result["evaluated_at"],
        "open_actionable": result["open_actionable"],
        "last_finding_at": result["last_finding_at"],
        "days_since_finding": result["days_since_finding"],
        "quiet_days": result["quiet_days"],
        "consecutive_clear_evals": streak,
        "error": result["error"],
        "history": history,
        "_doc": "Auto-written by automation/check_field_ready.py (E0-UAT-REFRAME "
                "stop-condition gate). FIELD-READY = capi-uat-triage may stop.",
    }
    result["consecutive_clear_evals"] = streak
    try:
        state_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as e:
        return f"write triage-state: {e}"
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="CAPI field-readiness stop-condition gate.")
    ap.add_argument("--repo", default=GH_REPO, help=f"GitHub repo (default {GH_REPO}).")
    ap.add_argument("--state-file",
                    default=str(Path(__file__).resolve().with_name("triage-state.json")))
    ap.add_argument("--quiet-days", type=float, default=QUIET_DAYS_DEFAULT,
                    help=f"Days the newest actionable finding must age before FIELD-READY (default {QUIET_DAYS_DEFAULT}).")
    ap.add_argument("--json", action="store_true", help="Print only the machine-readable JSON result.")
    ap.add_argument("--no-write", action="store_true", help="Evaluate without persisting to triage-state.json.")
    args = ap.parse_args(argv)

    result = evaluate(args.repo, args.quiet_days)

    if not args.no_write:
        werr = persist(Path(args.state_file), result)
        if werr:
            result["write_error"] = werr

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
        return VERDICT_EXIT[result["verdict"]]

    v = result["verdict"]
    icon = {"FIELD-READY": "✅", "CLEAR-PENDING": "🟡", "NOT-READY": "🔴", "UNKNOWN": "⚪"}[v]
    print(f"{icon} {v} — CAPI F1/F3/F4 field-readiness gate ({result['evaluated_at']})")
    if v == "UNKNOWN":
        print(f"   GitHub unreachable: {result['error']}. Not declaring ready on missing data.")
        return VERDICT_EXIT[v]
    print(f"   Open actionable F1/F3/F4 issues: {result['open_actionable']}")
    if result["open_issues"]:
        for i in result["open_issues"]:
            print(f"     - #{i['number']} {i['title']}  {i['labels']}")
    fin = result["last_finding_at"] or "none on record"
    dsf = result["days_since_finding"]
    print(f"   Newest actionable finding: {fin}"
          + (f" ({dsf}d ago; quiet window {result['quiet_days']}d)" if dsf is not None else ""))
    streak = result.get("consecutive_clear_evals")
    if streak is not None:
        print(f"   Consecutive clear evaluations: {streak}")
    if v == "FIELD-READY":
        print("   → Criteria 1+2 met. capi-uat-triage may STOP for F1/F3/F4 "
              "(ASPSI-owned items carved out; desk-test failures reopen it).")
    elif v == "CLEAR-PENDING":
        print("   → 0 open, but a finding is still inside the quiet window. "
              "Keep looping until it ages out.")
    else:
        print("   → Open actionable findings remain. Keep triaging.")
    return VERDICT_EXIT[v]


if __name__ == "__main__":
    sys.exit(main())
