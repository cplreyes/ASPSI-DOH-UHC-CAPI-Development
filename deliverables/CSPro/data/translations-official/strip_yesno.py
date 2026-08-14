#!/usr/bin/env python3
r"""Strip an answer-option block welded onto the end of a translated question.

86 stored values end their question and then print the answer options, in English with the
local gloss beside them:

    F4/ilo Q97   "... ammom kadi no sadino ti mapanam? ) Yes (Wen) No (Saan"
    F4/hil Q90   "... nga kasagaran mo ginakadtoan? Yes Oo No Indi"
    F4/fil Q14   "... tulad ng Igorot, Lumad, Mangyan, atbp.? Yes [Oo] No [Hindi ]"

The options belong to the value set, which renders them separately, so this is duplicate
text on screen - and it is in English, on a screen the respondent is being read in their
own language.

SAFETY
------
The cut is only made when all of these hold, because plenty of legitimate text follows a
question mark (parenthetical clarifications, "(antihypertensives, antibiotics, etc)",
sub-field suffixes):

  * the key is a QUESTION (numbered or ending in "?");
  * the block starts AFTER a "?" in the value, so the question itself is never touched;
  * the block matches an English Yes ... No pair, optionally with a bracketed gloss;
  * what remains still ends on the question mark and is at least four words.

Deletes only.

    python strip_yesno.py            # dry run
    python strip_yesno.py --apply
"""
import argparse
import glob
import io
import json
import os
import re

CS = (r"C:\Users\analy\Documents\analytiflow\1_Projects"
      r"\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro")

# an option block: optional PDF debris, then Yes ... No ... to the end of the value
BLOCK = re.compile(
    r"[\s)\]\|lI,;:]*\bYes\b\s*[\(\[]?[^()\[\]]{0,25}[\)\]]?\s*"
    r"\bNo\b\s*[\(\[]?[^()\[\]]{0,25}[\)\]]?\s*$",
    re.I,
)


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def is_question_key(k):
    k = (k or "").strip()
    return bool(re.match(r"^\d{1,3}(\.\d)?\s*[.)]", k)) or k.endswith("?")


def strip(v):
    """-> cleaned value, or None when there is nothing safe to cut."""
    s = norm(v)
    if "?" not in s:
        return None
    m = BLOCK.search(s)
    if not m:
        return None
    if m.start() <= s.rfind("?"):
        return None                      # the block must start after the question mark
    kept = norm(s[:m.start()]).rstrip(") ]|lI,;: ")
    kept = norm(kept)
    if len(kept.split()) < 4 or not kept.endswith("?"):
        return None
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    total = 0
    for inst in ("F1", "F3", "F4"):
        for path in sorted(glob.glob(os.path.join(CS, inst, "translations", "*.json"))):
            obj = json.loads(io.open(path, encoding="utf-8").read())
            todo = {}
            for k, v in obj.items():
                if not isinstance(v, str) or not is_question_key(k):
                    continue
                kept = strip(v)
                if kept and kept != norm(v):
                    todo[k] = kept
            if not todo:
                continue
            total += len(todo)
            loc = os.path.basename(path)[:3]
            print(f"\n{inst}/{loc}: {len(todo)}")
            for k, kept in list(todo.items())[:3]:
                print(f"   {k[:56]}")
                print(f"      was: {norm(obj[k])[:105]}")
                print(f"      now: {kept[:105]}")
            if a.apply:
                obj.update(todo)
                with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(obj, fh, ensure_ascii=False, indent=1)

    print(f"\n{'APPLIED' if a.apply else 'WOULD APPLY'}: {total} option blocks stripped")


if __name__ == "__main__":
    main()
