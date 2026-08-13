#!/usr/bin/env python3
r"""Mint F2 (HCW survey) enrollment tokens for the pretest and emit a printable sheet.

WHY THIS EXISTS
---------------
F2 enrollment is per-HCW: the token carries `hcw_id`, and a device is bound to ONE
HCW at a time (to survey the next person the enumerator taps "Change enrollment"
and pastes the next token). The tokens are long JWTs — nobody types those. So the
field needs the tokens as **links / QR codes**, one per HCW.

It also means enrollment REQUIRES NETWORK at the moment it happens (the app posts
to /verify-token). The survey itself works offline afterwards, but the enrol step
does not — see the field note printed on the sheet.

WHAT IT DOES
------------
For each HCW in the roster it:
  1. creates the HCW (POST /admin/api/hcws) at a REAL 9-digit facility, so the
     server auto-assigns the **12-digit QN** (facility + 3-digit seq, F2 block 101+),
  2. mints an enrollment token (POST /admin/api/hcws/<id>/reissue-token),
  3. writes a printable HTML sheet: one card per HCW with a QR code + the link.

Both field models are covered by the same sheet:
  * enumerator's tablet -> scan/tap each card in turn (Change enrollment between HCWs)
  * HCW's own phone     -> hand them their card, they scan their own QR

ROSTER (CSV, from ASPSI):
    facility_id,hcw_name[,hcw_id]
    040340220,Juan Dela Cruz
    040340220,Maria Santos
    040341130,Pedro Reyes
`facility_id` MUST be one of the seeded 9-digit codes (see f2_facility_master) —
a slug facility yields a BLANK QN and the response cannot be joined to F1/F3/F4.
`hcw_id` is optional; if omitted it is derived as <facility>-<NN>.

USAGE
    py mint_hcw_enrollment_sheets.py --roster hcw-roster.csv --user marriz_admin
    (password is prompted, or read from F2_ADMIN_PASS; never pass it on the CLI)
"""
from __future__ import annotations

import argparse
import csv
import getpass
import html
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

try:
    import segno
except ImportError:
    sys.exit("segno is required for the QR codes:  py -m pip install segno")

BASE = os.environ.get("F2_BASE", "https://uhc-hcw.asiansocial.org")
HERE = Path(__file__).resolve().parent


def call(method: str, path: str, body=None, bearer: str | None = None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", "Origin": BASE}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roster", required=True, help="CSV: facility_id,hcw_name[,hcw_id]")
    ap.add_argument("--user", default="marriz_admin")
    ap.add_argument("--out", default="hcw-enrollment-sheets.html")
    ap.add_argument("--dry-run", action="store_true",
                    help="render the sheet with placeholder tokens; no login, no HCWs created. "
                         "Use to check the layout/QR before minting real tokens.")
    args = ap.parse_args()

    token = None
    if not args.dry_run:
        # Password from F2_ADMIN_PASS_FILE (preferred — keeps it off the command line
        # and out of any transcript), then F2_ADMIN_PASS, else an interactive prompt.
        pw_file = os.environ.get("F2_ADMIN_PASS_FILE")
        pw = (Path(pw_file).read_text(encoding="utf-8").strip() if pw_file and Path(pw_file).exists()
              else os.environ.get("F2_ADMIN_PASS")
              or getpass.getpass(f"F2 admin password for {args.user}: "))
        st, body = call("POST", "/admin/api/login", {"username": args.user, "password": pw})
        token = body.get("token")
        if not token:
            return print(f"login failed ({st}): {body}") or 1
        print(f"logged in as {args.user} ({body.get('role')})")

    rows = list(csv.DictReader(Path(args.roster).open(encoding="utf-8-sig")))
    if not rows:
        return print("roster is empty") or 1

    minted, failures = [], []
    seq_by_fac: dict[str, int] = {}

    for r in rows:
        fac = (r.get("facility_id") or "").strip()
        name = (r.get("hcw_name") or "").strip()
        hcw_id = (r.get("hcw_id") or "").strip()

        if not re.fullmatch(r"\d{9}", fac):
            failures.append((name or "?", fac, "facility_id is not a 9-digit code — "
                                               "a slug yields a BLANK qn (unjoinable)"))
            continue
        if not hcw_id:
            seq_by_fac[fac] = seq_by_fac.get(fac, 0) + 1
            hcw_id = f"{fac}-{seq_by_fac[fac]:02d}"

        if args.dry_run:
            seq_by_fac[fac] = seq_by_fac.get(fac, 0)   # already bumped above when deriving hcw_id
            qn = f"{fac}{100 + max(seq_by_fac[fac], 1):03d}"   # mirrors the server's F2 block (101+)
            link = f"{BASE}/enroll?token=DRY-RUN-PLACEHOLDER-{hcw_id}"
        else:
            st, b = call("POST", "/admin/api/hcws",
                         {"hcw_id": hcw_id, "facility_id": fac, "facility_name": r.get("facility_name", "")},
                         bearer=token)
            if st not in (200, 201):
                failures.append((name, hcw_id, f"create failed {st}: {b.get('error', b)}"))
                continue
            qn = b.get("qn", "")
            if len(qn) != 12:
                failures.append((name, hcw_id, f"server returned a {len(qn)}-digit qn ({qn!r}) — "
                                               "expected 12; check the facility frame"))
                continue

            st, b = call("POST", f"/admin/api/hcws/{hcw_id}/reissue-token", {}, bearer=token)
            tok = b.get("new_token") or b.get("token")
            if not tok:
                failures.append((name, hcw_id, f"token mint failed {st}: {b.get('error', b)}"))
                continue
            link = b.get("link") or f"{BASE}/enroll?token={tok}"
        minted.append({"name": name, "hcw_id": hcw_id, "facility_id": fac, "qn": qn, "link": link})
        print(f"  {hcw_id:<16} qn={qn}  {name}")

    # ---- printable sheet -----------------------------------------------------
    cards = []
    for m in minted:
        qr = segno.make(m["link"], error="m")
        svg = qr.svg_inline(scale=4, dark="#000", light="#fff")
        cards.append(f"""
      <article class="card">
        <div class="qr">{svg}</div>
        <div class="meta">
          <div class="name">{html.escape(m['name'] or m['hcw_id'])}</div>
          <div class="row"><span>HCW ID</span><code>{html.escape(m['hcw_id'])}</code></div>
          <div class="row"><span>QN</span><code class="qn">{html.escape(m['qn'])}</code></div>
          <div class="row"><span>Facility</span><code>{html.escape(m['facility_id'])}</code></div>
          <div class="link">{html.escape(m['link'][:78])}…</div>
        </div>
      </article>""")

    doc = f"""<!doctype html>
<meta charset="utf-8">
<title>F2 HCW Enrollment Sheets — Pretest</title>
<style>
  body {{ font: 14px/1.5 system-ui, sans-serif; margin: 24px; color: #111; }}
  h1 {{ font-size: 20px; margin: 0 0 4px; }}
  .note {{ background: #fff8e1; border-left: 4px solid #E5B23B; padding: 10px 14px;
           margin: 12px 0 20px; font-size: 13px; }}
  .note b {{ color: #8a6d00; }}
  .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }}
  .card {{ display: flex; gap: 14px; border: 1px solid #ccc; border-radius: 6px;
           padding: 12px; break-inside: avoid; }}
  .qr svg {{ width: 116px; height: 116px; }}
  .meta {{ flex: 1; min-width: 0; }}
  .name {{ font-weight: 600; margin-bottom: 6px; }}
  .row {{ display: flex; justify-content: space-between; font-size: 12px; padding: 1px 0; }}
  .row span {{ color: #666; }}
  code {{ font-family: ui-monospace, monospace; }}
  .qn {{ font-weight: 600; }}
  .link {{ font-size: 10px; color: #888; word-break: break-all; margin-top: 6px; }}
  @media print {{ body {{ margin: 10mm; }} .note {{ break-inside: avoid; }} }}
</style>
<h1>UHC Survey Y2 — Healthcare Worker Survey (F2): enrollment sheet</h1>
<div class="note">
  <b>Enrolling needs a signal.</b> The tablet must be online at the moment an HCW enrolls
  (the app checks the token with the server). The survey itself works offline afterwards —
  answers are queued and sync later. If there is no signal, enrol where there is one first.
  <br><br>
  <b>One HCW at a time.</b> After a submission, tap <i>Change enrollment</i> before scanning
  the next person's code — otherwise the next survey is filed under the previous HCW.
  Alternatively, hand each HCW their own card and let them scan it on their phone.
</div>
<div class="grid">{''.join(cards)}</div>
"""
    out = HERE / args.out
    out.write_text(doc, encoding="utf-8")

    print(f"\nminted {len(minted)} enrollment token(s) -> {out}")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for n, i, why in failures:
            print(f"  {n} / {i}: {why}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
