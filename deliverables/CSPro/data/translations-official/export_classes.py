#!/usr/bin/env python3
r"""Export per-locale divergence classes for review.

Writes classes/<LOCALE>.md - every distinct (CAPI shows -> cleared source says) pair with
its occurrence count and an example question, ordered by impact. One file per locale so a
reviewer (human or agent) can work a single language without wading through the rest.
"""
import io
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "verbatim_report.json")
OUT = os.path.join(HERE, "classes")
LOCALE_NAME = {"FIL": "Filipino/Tagalog", "BCL": "Bikol", "BIS": "Bisaya",
               "CEB": "Cebuano", "WAR": "Waray", "HIL": "Hiligaynon", "ILO": "Ilocano"}


def main():
    rep = json.loads(io.open(REPORT, encoding="utf-8").read())
    os.makedirs(OUT, exist_ok=True)
    pairs = defaultdict(Counter)
    example = {}
    for inst, data in rep.items():
        for lg, findings in data["findings"].items():
            for f in findings:
                if f["verdict"] != "DIVERGENT":
                    continue
                key = (f["capi"].strip(), f["official"].strip())
                pairs[lg][key] += 1
                example.setdefault((lg, key), f"{inst} Q{f['q']} {f['item']}")

    for lg, c in pairs.items():
        lines = [f"# {lg} ({LOCALE_NAME.get(lg, lg)}) - divergence classes", "",
                 f"{sum(c.values())} divergent strings across {len(c)} distinct classes.",
                 "",
                 "`CAPI` = what the deployed tool shows. `CLEARED` = the DOH/SJREB "
                 "June-5 questionnaire.", ""]
        for (capi, off), n in c.most_common():
            lines += [f"## x{n} - {example[(lg, (capi, off))]}",
                      f"- CAPI    : {capi}",
                      f"- CLEARED : {off}", ""]
        io.open(os.path.join(OUT, f"{lg}.md"), "w", encoding="utf-8").write("\n".join(lines))
        print(f"  wrote classes/{lg}.md  ({sum(c.values())} strings, {len(c)} classes)")


if __name__ == "__main__":
    main()
