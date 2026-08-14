#!/usr/bin/env python3
r"""Break the DIVERGENT bucket into systematic classes vs one-off differences.

Most divergence is not 1,052 separate problems. F3 Bikol alone showed the CAPI using
"Dae" for No where the cleared source uses "Dai" - one orthographic choice repeated
across every yes/no question. Grouping identical (capi -> official) pairs turns a long
list into a handful of decisions, and shows how much is fixable by a single substitution.

Run:  python analyse_divergence.py [--locale BCL] [--top 25]
"""
import argparse
import io
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "verbatim_report.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--locale")
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()

    rep = json.loads(io.open(REPORT, encoding="utf-8").read())
    pairs = defaultdict(Counter)      # locale -> (capi, official) -> count
    totals = Counter()

    for inst, data in rep.items():
        for lg, findings in data["findings"].items():
            if a.locale and lg != a.locale:
                continue
            for f in findings:
                if f["verdict"] != "DIVERGENT":
                    continue
                totals[lg] += 1
                pairs[lg][(f["capi"].strip()[:80], f["official"].strip()[:80])] += 1

    grand_div = sum(totals.values())
    grand_sys = 0
    print(f"{'locale':<8}{'divergent':>11}{'distinct pairs':>16}{'in repeats':>13}"
          f"{'repeat share':>14}")
    for lg in sorted(totals, key=lambda k: -totals[k]):
        repeated = sum(v for v in pairs[lg].values() if v > 1)
        grand_sys += repeated
        share = 100.0 * repeated / totals[lg] if totals[lg] else 0
        print(f"{lg:<8}{totals[lg]:>11}{len(pairs[lg]):>16}{repeated:>13}{share:>13.0f}%")
    print(f"\n{'ALL':<8}{grand_div:>11}{'':>16}{grand_sys:>13}"
          f"{100.0 * grand_sys / grand_div if grand_div else 0:>13.0f}%")

    for lg in sorted(totals, key=lambda k: -totals[k]):
        top = [(k, v) for k, v in pairs[lg].most_common(a.top) if v > 1]
        if not top:
            continue
        print(f"\n{'=' * 88}\n{lg} - most repeated substitutions "
              f"(CAPI shows -> cleared source says)\n{'=' * 88}")
        for (capi, off), n in top:
            print(f"  x{n:<4} {capi[:44]!r}\n        -> {off[:44]!r}")


if __name__ == "__main__":
    main()
