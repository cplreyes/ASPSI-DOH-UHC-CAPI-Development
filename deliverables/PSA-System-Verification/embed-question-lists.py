#!/usr/bin/env python3
"""Embed the per-instrument `_qlist_<KEY>.html` fragments into index.html as
collapsible 'Complete question list' blocks (one per instrument, each section
collapsible inside). Idempotent: strips any prior QLIST blocks/CSS first, so it
can be re-run after regenerating the lists. Run after gen-question-list.py."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
idx = (HERE / "index.html").read_text(encoding="utf-8")

CSS = """<!--QLIST-CSS-->
details.qbox{border:1px solid var(--line);border-radius:8px;margin:10px 0;overflow:hidden}
details.qbox>summary{cursor:pointer;padding:11px 15px;font-weight:600;font-size:14px;background:#eef2f8;color:var(--brand);list-style:none}
details.qbox>summary::-webkit-details-marker{display:none}
details.qbox>summary::before{content:"\\25B8  ";color:var(--muted)}
details.qbox[open]>summary::before{content:"\\25BE  "}
.qsec details{border-top:1px solid var(--line)}
.qsec details>summary{cursor:pointer;padding:8px 16px;font-size:13.5px;font-weight:600;color:var(--ink);background:#fff;list-style:none}
.qsec details>summary::-webkit-details-marker{display:none}
.qsec details>summary::before{content:"+  ";color:var(--muted);font-weight:700}
.qsec details[open]>summary::before{content:"\\2212  "}
.qsec ul.qlist{margin:0;padding:4px 18px 12px 34px;font-size:13.5px;background:#fbfcfe;list-style:disc}
.qsec ul.qlist li{margin:7px 0;line-height:1.45}
.qsec .qt{color:var(--muted);font-size:12px;font-style:italic}
.qsec .qopts{color:var(--muted);font-size:12.5px;margin:2px 0 0}
<!--/QLIST-CSS--></style>"""

# (KEY, count, title, the marker we insert BEFORE)
INSTR = [
    ("F3", 226, "F3 — Patient Survey", '  <h2 id="f1">'),
    ("F1", 203, "F1 — Facility Head Survey", '  <h2 id="f4">'),
    ("F4", 237, "F4 — Household Survey", '  <h2 id="csweb">'),
    ("F2", 124, "F2 — Healthcare Worker Survey (PWA)", '  <div class="foot">'),
]

# strip prior blocks (idempotent)
idx = re.sub(r"<!--QLIST:[^>]*-->.*?<!--/QLIST:[^>]*-->\n*", "", idx, flags=re.S)
idx = re.sub(r"<!--QLIST-CSS-->.*?<!--/QLIST-CSS-->\n*", "", idx, flags=re.S)
# the strip above may have eaten the closing </style>; ensure exactly one remains
if "</style>" not in idx:
    idx = idx.replace("<!--QLIST-CSS-->", "", 1)  # safety (shouldn't trigger)

idx = idx.replace("</style>", CSS, 1)

for key, n, title, marker in INSTR:
    frag = (HERE / f"_qlist_{key}.html").read_text(encoding="utf-8")
    block = (
        f"<!--QLIST:{key}-->\n"
        "  <h3>Complete question list</h3>\n"
        '  <p class="sub">Every question the deployed instrument asks, grouped by section &mdash; '
        "generated from the question data so it matches the live app exactly. Click a section to expand.</p>\n"
        f'  <details class="qbox"><summary>Show all {n} questions &mdash; {title}, by section</summary>\n'
        '  <div class="qsec">\n'
        f"{frag}\n"
        "  </div></details>\n"
        f"<!--/QLIST:{key}-->\n\n"
    )
    assert marker in idx, f"marker not found for {key}: {marker!r}"
    idx = idx.replace(marker, block + marker, 1)

(HERE / "index.html").write_text(idx, encoding="utf-8")
print("embedded question lists for", ", ".join(k for k, *_ in INSTR))
