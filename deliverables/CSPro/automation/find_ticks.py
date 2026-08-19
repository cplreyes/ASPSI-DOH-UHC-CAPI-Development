#!/usr/bin/env python3
r"""Locate CSEntry Check Box tick-box glyphs in a csentry_runner screenshot.

WHY THIS EXISTS. A Check Box (tick-all) field cannot be driven by typing the option
code (established in F4 task-1.9) and does not respond to {SPACE} either (probed in
F1 task-2.6) -- the only mechanic available to csentry_runner.py is `click <x> <y>`
on the tick-box glyph itself. Hunting those coordinates by eye costs one full
scenario re-run per checkbox. This reads them straight out of the run's own
screenshot instead.

The glyphs form a vertical column 20 px apart; each is ~10x10 with a dark top-border
row and a dark left-border column. Detect the solid top-border runs, then keep the
longest 20px-spaced run of them.

The column x is ALSO predictable as `767 + 14.1 * <item dictionary length>`: the
value box starts at x=723 and runs 14.1 px per character, and the popup opens 28 px
to its right with a 16 px tick inset. That rule held exactly on ten popups across
F1's four Aug-17 scenarios, so it is the default search window -- but it FAILS when
the popup is too wide to fit to the right of the value box and shifts LEFT instead,
which is what happens under a locale with longer option labels. Pass --wide then.

The y is NOT predictable offline: it depends on the list's scroll state, which
differs between a field at the start of a section and one further down.

Usage:
    python find_ticks.py <shot.png> <item_length> [--wide]

Prints the click coordinate for every option row, so option N is a direct lookup.
"""

import sys
from PIL import Image

path = sys.argv[1]
ln = int(sys.argv[2])
xpred = 767 + round(14.1 * ln)
lo, hi = (60, 1900) if "--wide" in sys.argv else (xpred - 40, xpred + 40)

im = Image.open(path).convert("L")
W, H = im.size
px = im.load()

RUN = 9          # length of the top-border run to look for
tops = {}        # x0 -> [y, ...]
for y in range(H):
    x = lo
    while x < min(hi, W - RUN):
        if all(px[x + k, y] < 150 for k in range(RUN)):
            # require the pixel just left and just right to be lighter (a box, not a line)
            if px[max(0, x - 2), y] > 150 and px[min(W - 1, x + RUN + 2), y] > 150:
                tops.setdefault(x, []).append(y)
            x += RUN
        else:
            x += 1

best = None
for x0, ys in tops.items():
    runs = []
    for y in ys:
        if runs and 17 <= y - runs[-1][-1] <= 23:
            runs[-1].append(y)
        else:
            runs.append([y])
    r = max(runs, key=len)
    if len(r) >= 3 and (best is None or len(r) > len(best[1])):
        best = (x0, r)

if not best:
    print(f"no tick column found (searched x in {lo}..{hi}; predicted {xpred})")
    sys.exit(2)

x0, ys = best
cx, cy = x0 + RUN // 2, ys[0] + 5
print(f"predicted x={xpred} for length {ln}; DETECTED column x0={x0} -> click x={cx}")
print(f"{len(ys)} options; option 01 tick center y={cy}")
print(f"  -> click {cx} {cy}")
for i, y in enumerate(ys):
    print(f"     option {i+1:>2}: click {cx} {y + 5}")
