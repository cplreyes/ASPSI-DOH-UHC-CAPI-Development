#!/usr/bin/env python
"""Build cover_logos.png — the strip embedded (as a data-URI) on every CAPI cover.

Sequence: [DOH Seal | Bagong Pilipinas | Bawat Buhay Mahalaga] + ASPSI.
The first three come pre-composed in logos/cover_logos_doh3.png (built 2026-08-11
from the DOH brand-book folder, per its LOGO SEQUENCE.PNG); ASPSI is appended from
logos/aspsi-official-colored-nobg.png (official colored mark, transparent bg).

Rerun after changing any input:  py compose_cover_logos.py
Then regenerate each instrument's qsf (stamp_version.py bump F<n>) so the new
strip rides into the .pen. The <img width> in generate_qsf.py assumes the output
proportions printed at the end — keep them in sync.
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
GAP = 14          # px between the DOH block and the ASPSI mark
ASPSI_H = 99      # match the visual height of the marks in the DOH strip

base = Image.open(HERE / "logos" / "cover_logos_doh3.png").convert("RGBA")
aspsi = Image.open(HERE / "logos" / "aspsi-official-colored-nobg.png").convert("RGBA")

w = round(aspsi.width * ASPSI_H / aspsi.height)
aspsi = aspsi.resize((w, ASPSI_H), Image.LANCZOS)

out = Image.new("RGBA", (base.width + GAP + w, base.height), (0, 0, 0, 0))
out.paste(base, (0, 0), base)
out.paste(aspsi, (base.width + GAP, (base.height - ASPSI_H) // 2), aspsi)
out.save(HERE / "cover_logos.png")
print(f"cover_logos.png: {out.width}x{out.height} "
      f"(doh3 {base.width}px + gap {GAP} + aspsi {w}px)")
