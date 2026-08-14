#!/usr/bin/env python3
r"""Remove questionnaire ROUTING ANNOTATIONS from translated labels - both shapes.

The paper questionnaire carries margin notes telling the interviewer when a question
applies ("<Only for those who answered ...>", "<Proceed to Q148>", "<Ask if answer in Q159
is ...>"). The CAPI implements that routing as skip logic, so the notes were never meant to
reach a respondent - but the PDF extraction carried them into the stored translations, and
many were left truncated mid-note by the page break, so they have no closing ">".

Two dispositions, because two different things went wrong:

  TRIM   the value has real translated text and the note is stuck on one end.
         Keep the text, drop the note.

  DROP   the value is nothing BUT the note - e.g. the Waray label for the option
         "Physical plant" is the whole of `<Only for those who answered "`. Deleting the
         key makes apply_translations fall back to English, which is the documented
         behaviour for a missing translation and is strictly better than showing a
         truncated English margin note where an answer option should be. Writing "" would
         NOT fall back - it would render blank - so the key must be removed, not emptied.

Never touches a value whose ENGLISH KEY also carries the note: there it is part of the
approved label. Deletes only; no text is ever composed.

    python clean_annotations.py            # dry run
    python clean_annotations.py --apply
"""
import argparse
import glob
import io
import json
import os
import re

CSPRO = (r"C:\Users\analy\Documents\analytiflow\1_Projects"
         r"\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro")
CLOSED = re.compile(r"<[^>]{8,}>")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def plan_value(k, v):
    """-> ('trim', text) | ('drop', None) | None"""
    if not isinstance(v, str) or "<" not in v:
        return None
    if "<" in k:
        return None                      # the note belongs to the approved English label
    m = CLOSED.search(v)
    if m:
        head, tail = norm(v[:m.start()]), norm(CLOSED.sub(" ", v[m.start():]))
    else:
        i = v.find("<")
        head, tail = norm(v[:i]), ""     # unterminated: nothing usable after it
    tail = tail.lstrip("—-– ").strip()
    kept = head if len(head.split()) >= 3 else tail
    if len(kept.split()) >= 3:
        return ("trim", kept) if kept != norm(v) else None
    return ("drop", None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    trims = drops = 0
    for inst in ("F1", "F3", "F4"):
        for path in sorted(glob.glob(os.path.join(CSPRO, inst, "translations", "*.json"))):
            obj = json.loads(io.open(path, encoding="utf-8").read())
            todo = {}
            for k, v in obj.items():
                r = plan_value(k, v)
                if r:
                    todo[k] = r
            if not todo:
                continue
            name = f"{inst}/{os.path.basename(path)}"
            nt = sum(1 for r in todo.values() if r[0] == "trim")
            nd = sum(1 for r in todo.values() if r[0] == "drop")
            trims += nt
            drops += nd
            print(f"\n{name}: trim {nt}, drop {nd}")
            for k, (kind, kept) in list(todo.items())[:4]:
                print(f"   [{kind}] {k[:62]}")
                print(f"        was: {norm(obj[k])[:100]}")
                if kind == "trim":
                    print(f"        now: {kept[:100]}")
                else:
                    print(f"        now: (key removed -> English fallback)")
            if a.apply:
                for k, (kind, kept) in todo.items():
                    if kind == "trim":
                        obj[k] = kept
                    else:
                        obj.pop(k, None)
                with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(obj, fh, ensure_ascii=False, indent=1)

    print(f"\n{'APPLIED' if a.apply else 'WOULD APPLY'}: {trims} trims, {drops} key removals")


if __name__ == "__main__":
    main()
