#!/usr/bin/env python
"""Build cover_logos.png — the strip embedded (as a data-URI) on every CAPI cover.

Sequence per ASPSI's clarification on #1190 (Shan, 2026-08-11):
    DOH Seal → ASPSI → Bagong Pilipinas → Bawat Buhay Mahalaga
(ASPSI sits in the "attached agency" slot, second, per their reference image.)

Inputs, both in logos/:
  - cover_logos_doh3.png  — DOH Seal | Bagong Pilipinas | Bawat Buhay Mahalaga,
    pre-composed 2026-08-11 from the DOH brand-book folder. Split here on fully
    transparent column runs into its three marks.
  - aspsi-official-colored-nobg.png — official colored ASPSI mark, transparent bg.

Rerun after changing any input:  py compose_cover_logos.py
Then regenerate each instrument's qsf (stamp_version.py bump F<n>). Keep the
<img width> in each generate_qsf.py at round(output_width * 400/520) — the
script prints the right value.
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
GAP = 14          # px between marks
ASPSI_H = 99      # match the visual height of the marks in the DOH strip


def split_on_transparent_columns(img, min_gap=6):
    """Split an RGBA strip into segments separated by >=min_gap fully transparent columns."""
    alpha = img.getchannel("A")
    w, h = img.size
    px = alpha.load()
    blank = [all(px[x, y] == 0 for y in range(h)) for x in range(w)]
    segments, start = [], None
    x = 0
    while x < w:
        if not blank[x] and start is None:
            start = x
        elif blank[x] and start is not None:
            run = 0
            while x + run < w and blank[x + run]:
                run += 1
            if run >= min_gap or x + run >= w:
                segments.append(img.crop((start, 0, x, h)))
                start = None
                x += run - 1
        x += 1
    if start is not None:
        segments.append(img.crop((start, 0, w, h)))
    return segments


base = Image.open(HERE / "logos" / "cover_logos_doh3.png").convert("RGBA")
aspsi = Image.open(HERE / "logos" / "aspsi-official-colored-nobg.png").convert("RGBA")

marks = split_on_transparent_columns(base)
assert len(marks) == 3, f"expected 3 marks in doh3 strip, got {len(marks)}"
doh, bp, bbm = marks

w = round(aspsi.width * ASPSI_H / aspsi.height)
aspsi = aspsi.resize((w, ASPSI_H), Image.LANCZOS)

ordered = [doh, aspsi, bp, bbm]
total_w = sum(m.width for m in ordered) + GAP * (len(ordered) - 1)
out = Image.new("RGBA", (total_w, base.height), (0, 0, 0, 0))
x = 0
for m in ordered:
    out.paste(m, (x, (base.height - m.height) // 2), m)
    x += m.width + GAP
out.save(HERE / "cover_logos.png")
print(f"cover_logos.png: {out.width}x{out.height} "
      f"(doh {doh.width} + aspsi {w} + bp {bp.width} + bbm {bbm.width}, gaps {GAP})")
print(f"set <img width> in generate_qsf.py to: {round(out.width * 400 / 520)}")
