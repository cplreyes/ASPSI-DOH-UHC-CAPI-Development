#!/usr/bin/env python3
"""Write one per-response F2 detail JSON into /docs/f2/, for /docs/f2-case.html.

Why this exists: the Sync Dashboard case list links F1/F3/F4 rows to the CSWeb View
case and that works after a single CSWeb login. The equivalent F2 link went to the
F2 Admin Portal, whose login screen navigates to a hardcoded /admin/data and throws
away the route you asked for — so you signed in and the case did not open. The
upstream fix belongs in the F2 frontend; this gives the console its own viewer so
F2 needs no second sign-in at all (Carl, 2026-07-30).

Design notes:
  * Runs ON the box like the other generators (host python3 + docker exec mysql), so
    NO database credential ever reaches a web page — the viewer is static HTML that
    fetches these files.
  * One small file per response = O(1) to view. The dashboard's own page-weight
    lesson: never make a reader download every record to see one.
  * values_json is carried as TO_BASE64 so a tab or newline inside an answer cannot
    corrupt the --batch TSV. (The dashboard generator learned the charset half of
    this the hard way; this is the delimiter half.)
  * Writes only when content changed, so the 2-minute cron does not rewrite
    thousands of identical files or bump mtimes for no reason.
  * REFUSES to write if the directory's .htaccess is missing — same guard the
    responses generator uses. /docs/ FilesMatch blocks match FILENAMES, so an
    ungated directory here would be public.
"""
import base64, json, os, subprocess, sys, datetime

OUT_DIR = "/opt/app/lamp/www/docs/f2"
LABELS = "/opt/spss-meta/f2-item-labels.json"
ENV = "/opt/app/.env"

# values_json keys that are provenance/plumbing, not survey answers.
SKIP = {"submission_id", "client_submission_id", "hcw_id", "facility_id", "qn",
        "spec_version", "app_version", "device_fingerprint", "source", "source_path",
        "status", "submitted_at_client", "submitted_at_server", "encoded_by",
        "encoded_at", "gps_status", "submission_lat", "submission_lng"}

SQL = (
    "SELECT r.submission_id, COALESCE(NULLIF(r.qn,''),''), COALESCE(r.facility_id,''),"
    " COALESCE(fm.facility_name,''), COALESCE(fm.region,''), COALESCE(fm.province,''),"
    " COALESCE(r.status,''), COALESCE(r.source_path,''),"
    " COALESCE(DATE_FORMAT(CONVERT_TZ(r.submitted_at_server,'+00:00','+08:00'),"
    "   '%Y-%m-%d %H:%i'),''),"
    " COALESCE(r.spec_version,''), COALESCE(r.app_version,''), COALESCE(r.encoded_by,''),"
    # TO_BASE64 WRAPS at 76 chars with a newline, which shreds the --batch TSV: the
    # row splits mid-token and the payload silently arrives truncated. Strip the
    # wrapping IN SQL with CHAR(10)/CHAR(13) (unambiguous through every quoting layer).
    " REPLACE(REPLACE(COALESCE(TO_BASE64(r.values_json),''),CHAR(10),''),CHAR(13),'')"
    " FROM csweb_f2.f2_responses r"
    " LEFT JOIN csweb_f2.f2_facility_master fm ON fm.facility_id=r.facility_id"
    " WHERE COALESCE(r.status,'') <> 'voided'")


def rootpw():
    with open(ENV, encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("MYSQL_ROOT_PASSWORD="):
                return ln.split("=", 1)[1].strip()
    raise RuntimeError("MYSQL_ROOT_PASSWORD not found in %s" % ENV)


def rows():
    r = subprocess.run(
        ["docker", "exec", "lamp-mysql8", "mysql", "-uroot", "-p" + rootpw(),
         "--default-character-set=utf8mb4", "--batch", "-N", "-e", SQL],
        capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "mysql failed").strip()[:300])
    return [ln.split("\t") for ln in r.stdout.splitlines() if ln.strip()]


def flatten(v):
    """One display string per answer. Lists are multi-selects; dicts are sub-field
    groups the F2 form stores whole."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, list):
        return "; ".join(flatten(x) for x in v if x not in (None, ""))
    if isinstance(v, dict):
        return "; ".join("%s: %s" % (k, flatten(x)) for k, x in v.items()
                         if x not in (None, ""))
    return str(v)


def main():
    if not os.path.isfile(os.path.join(OUT_DIR, ".htaccess")):
        print("REFUSING: %s/.htaccess missing — an ungated dir here would be public."
              % OUT_DIR)
        return 2
    labels = json.load(open(LABELS, encoding="utf-8"))
    order = {k: i for i, k in enumerate(labels)}        # the label file IS the form order
    gen = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    written = skipped = 0
    bad = []

    for r in rows():
        (sub, qn, fid, fname, region, province, status, srcpath,
         when, spec, appv, encby, vb64) = (r + [""] * 13)[:13]
        if not sub:
            continue
        # No silent fallback here. An earlier version swallowed decode errors into an
        # empty dict, so a truncated payload published a response with ZERO answers
        # that looked like a legitimately blank questionnaire. Fail loudly instead.
        try:
            vals = json.loads(base64.b64decode(vb64).decode("utf-8")) if vb64 else {}
        except Exception as e:
            print("ERROR %s: values_json did not decode (%s) — skipped, NOT published"
                  % (sub, str(e)[:80]))
            bad.append(sub)
            continue
        if not isinstance(vals, dict) or not vals:
            print("ERROR %s: values_json decoded to no answers — skipped" % sub)
            bad.append(sub)
            continue
        answers = []
        for k, v in vals.items():
            if k in SKIP:
                continue
            meta = labels.get(k) or {}
            answers.append({"code": k,
                            "label": meta.get("label") or k,
                            "value": flatten(v),
                            "labelled": bool(meta.get("label"))})
        answers.sort(key=lambda a: (order.get(a["code"], 10**6), a["code"]))
        blob = {
            "submission_id": sub, "qn": qn,
            "facility": {"id": fid, "name": fname, "region": region, "province": province},
            "status": status, "source_path": srcpath, "submitted": when,
            "spec_version": spec, "app_version": appv, "encoded_by": encby,
            "answered": sum(1 for a in answers if a["value"] != ""),
            "answers": answers, "generated": gen,
        }
        # `generated` is excluded from the change test, or every run would rewrite
        # every file and the mtimes would lie about when data actually changed.
        cmp_new = json.dumps({k: v for k, v in blob.items() if k != "generated"},
                             sort_keys=True, ensure_ascii=False)
        path = os.path.join(OUT_DIR, sub + ".json")
        try:
            prev = json.load(open(path, encoding="utf-8"))
            cmp_old = json.dumps({k: v for k, v in prev.items() if k != "generated"},
                                 sort_keys=True, ensure_ascii=False)
        except Exception:
            cmp_old = None
        if cmp_old == cmp_new:
            skipped += 1
            continue
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(blob, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, path)                       # atomic: a reader never sees a partial file
        written += 1

    print("f2 cases: %d written, %d unchanged, %d FAILED -> %s"
          % (written, skipped, len(bad), OUT_DIR))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
