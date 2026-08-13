#!/usr/bin/env python3
"""Keep LoginApp.csds's file list in step with what build_hub_apps.py actually emits.

The .csds spec carries a STATIC file list, but the per-enumerator assignment files
(AS_<operator_id>.dat) are generated from the roster — so the roster growing (or
shrinking) silently desyncs the bundle. That is a silent failure: the package
deploys fine and the missing enumerator's tablet simply never receives an
assignment. (Caught 2026-07-14: the pretest roster added se-007/PCrudo, but the
spec still listed only se-001..se-006.)

deploy_hub_bundle.py already globs AS_*.dat for the GUI Add-files route; this does
the same for the hands-off .csds route. Idempotent — safe to re-run.

    py sync_csds_files.py [--check]
"""
from __future__ import annotations
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / "LoginApp.csds"
CHECK = "--check" in sys.argv

spec = json.loads(SPEC.read_text(encoding="utf-8"))
files = spec.get("files", [])

listed = {Path(f["path"]).name for f in files if "path" in f}
on_disk = {p.name for p in HERE.glob("AS_*.dat")}

missing = sorted(on_disk - listed)          # generated but not in the bundle
stale = sorted(n for n in (listed - on_disk) if n.startswith("AS_"))  # in bundle, no longer generated

print(f"AS files on disk : {len(on_disk)}  ({', '.join(sorted(on_disk))})")
print(f"AS files in spec : {len(listed & on_disk) + len(stale)}")
if missing:
    print(f"  MISSING from spec : {', '.join(missing)}")
if stale:
    print(f"  STALE in spec     : {', '.join(stale)}")
if not missing and not stale:
    print("  in sync — nothing to do")
    raise SystemExit(0)

if CHECK:
    print("\n--check: not modifying the spec.")
    raise SystemExit(1)

# drop stale AS_* entries, append the missing ones (keep every non-AS entry as-is)
kept = [f for f in files if not (Path(f.get("path", "")).name in stale)]
for name in missing:
    kept.append({"path": str(HERE / name)})
spec["files"] = kept

SPEC.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nLoginApp.csds updated: {len(kept)} files "
      f"(+{len(missing)} added, -{len(stale)} removed)")
