#!/usr/bin/env python3
r"""One-shot migration: legacy text-keyed locale maps -> name-scoped keys.

Legacy format (2026-06-03 .. 2026-08-17): {"<full English label text>": "<translation>"}
applied by matching each label node's SOURCE English at apply_translations() time.
Source English is the critical detail: post-apply passes (#714 facility-placeholder
neutralisation in F3) rewrite the BUILT labels in every language, so the built .dcf's
English text is NOT the text the legacy lookup keyed on. Bridging from the built file
mis-migrates exactly those labels (found the hard way, 2026-08-17 first attempt).

This migrator therefore captures the PRE-APPLY single-language dictionary by hooking
cspro_helpers.apply_translations during a real generator run, walks it with
cspro_helpers.walk_labeled_nodes (the same walker the new applier uses), and resolves
each node with the EXACT legacy lookup (text key, then the 255-capped form). The result
is behavior-identical to the legacy pipeline: same translations, same fallbacks — the
regenerated output is byte-identical except for deliberately edited entries.

Self-echo values (translation == EN) are dropped: fallback already produces them.
Legacy keys matching no node are ORPHANS (English-edit casualties, other-instrument
keys in shared seeds, or post-neutralisation keys that never matched under legacy code
either) — counted and left behind in translations/legacy-textkey-2026-08-17/; recovery
comes from the cleared June-5 corpus via apply_safe.py, not from stale keys.

    python migrate_maps_namekeys.py            # migrate all three instruments
    python migrate_maps_namekeys.py --dry-run  # report only, write nothing

NOTE: the capture run executes each generate_dcf.py, so it also REGENERATES the
.dcf with whatever maps are currently in translations/ — run the generators again
after migration to build from the migrated maps.
"""
import argparse
import copy
import io
import json
import os
import runpy
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, CSPRO)
import cspro_helpers  # noqa: E402
from cspro_helpers import walk_labeled_nodes, _cap_text  # noqa: E402


def _utf8_stdout():
    # Only when run as a script — wrapping at import time closes the previous
    # wrapper's buffer for any importer that already wrapped (the scanner does).
    if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      line_buffering=True)

INSTRUMENTS = {
    "F1": "generate_dcf.py",
    "F3": "generate_dcf.py",
    "F4": "generate_dcf.py",
}
LOCALES = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]
LEGACY_DIRNAME = "legacy-textkey-2026-08-17"


def capture_source_dict(inst, gen_name):
    """Run the instrument's generator with apply_translations hooked; return a
    deep copy of the PRE-APPLY single-language dictionary."""
    captured = {}
    real = cspro_helpers.apply_translations

    def hook(dictionary, translations_dir, languages=cspro_helpers.TRANSLATION_LANGUAGES):
        if "dict" not in captured:          # first call only (facility_lookup etc. later)
            captured["dict"] = copy.deepcopy(dictionary)
        return real(dictionary, translations_dir, languages)

    gen_path = os.path.join(CSPRO, inst, gen_name)
    cwd = os.getcwd()
    cspro_helpers.apply_translations = hook
    try:
        os.chdir(os.path.join(CSPRO, inst))
        runpy.run_path(gen_path, run_name="__main__")
    finally:
        cspro_helpers.apply_translations = real
        os.chdir(cwd)
    if "dict" not in captured:
        raise SystemExit(f"{inst}: generator never called apply_translations")
    return captured["dict"]


def migrate_instrument(inst, gen_name, dry_run):
    tdir = os.path.join(CSPRO, inst, "translations")
    legacy_dir = os.path.join(tdir, LEGACY_DIRNAME)
    src_dir = legacy_dir if os.path.isdir(legacy_dir) else tdir

    print(f"\n=== {inst}: capturing pre-apply source dictionary (runs {gen_name})")
    d = capture_source_dict(inst, gen_name)

    nodes = []
    keys_seen = {}
    for key, node in walk_labeled_nodes(d):
        labs = node.get("labels")
        if not (isinstance(labs, list) and labs and isinstance(labs[0], dict)
                and "text" in labs[0]):
            continue
        en = labs[0]["text"]
        if key in keys_seen and keys_seen[key] != en:
            raise SystemExit(f"{inst}: key collision with divergent EN text: {key}")
        keys_seen[key] = en
        nodes.append((key, en))
    print(f"    {len(nodes)} labeled nodes, {len(keys_seen)} distinct keys")

    for loc in LOCALES:
        src = os.path.join(src_dir, f"{loc}.json")
        if not os.path.exists(src):
            print(f"  {loc}: no legacy map, skipped")
            continue
        legacy = json.load(io.open(src, encoding="utf-8"))
        if any(":" in k and k.startswith(("item:", "val:", "vs:", "dict:", "record:", "level:"))
               for k in legacy):
            raise SystemExit(f"{inst}/{loc}: {src} already name-scoped — wrong source dir?")
        used_keys = set()
        out = {}
        self_echo = 0
        for key, en in nodes:
            tr = legacy.get(en)
            if tr is None:
                capped = _cap_text(en)
                tr = legacy.get(capped)
                if tr is not None:
                    used_keys.add(capped)
            else:
                used_keys.add(en)
            if tr is None:
                continue
            if tr == en:
                self_echo += 1
                continue
            out[key] = tr
        orphans = [k for k in legacy if k not in used_keys]
        print(f"  {loc}: {len(out)} entries migrated"
              f"  (self-echo dropped: {self_echo};"
              f" legacy keys unmatched here: {len(orphans)}/{len(legacy)})")
        if dry_run:
            continue
        if src_dir is tdir:                 # first run: preserve the legacy file
            os.makedirs(legacy_dir, exist_ok=True)
            shutil.move(src, os.path.join(legacy_dir, f"{loc}.json"))
        payload = {"_meta": {
            "format": "name-scoped-v2",
            "migrated": "2026-08-17",
            "keys": "cspro_helpers.walk_labeled_nodes",
            "source": f"{LEGACY_DIRNAME}/{loc}.json bridged via PRE-APPLY source English",
        }}
        payload.update(out)
        with io.open(os.path.join(tdir, f"{loc}.json"), "w", encoding="utf-8",
                     newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")


def main():
    _utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    for inst, gen in INSTRUMENTS.items():
        migrate_instrument(inst, gen, args.dry_run)
    print("\nDone" + (" (dry run — nothing written)" if args.dry_run else "")
          + ". Re-run the three generate_dcf.py to build from the migrated maps.")


if __name__ == "__main__":
    main()
