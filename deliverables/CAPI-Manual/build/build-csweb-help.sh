#!/usr/bin/env bash
# Build the CAPI Manual as a self-contained, DOH-green page for the CSWeb help hub:
#   sections/*.md -> combined md -> (mermaid -> SVG) -> pandoc (green template) ->
#   deliverables/CSWeb/landing/docs/capi-manual.html  (+ images under docs/img/capi-manual/)
# Same design as the other /docs guides (uses /assets/docs.css). Public-safe: strips the
# section author-note HTML comments; no client-side JS (mermaid pre-rendered to SVG).
# Requires: pandoc, node/npx (mermaid-cli auto-fetched), Google Chrome.
# Run from the CAPI-Manual/ directory:  bash build/build-csweb-help.sh
set -e
cd "$(dirname "$0")/.."

LANDING="../CSWeb/landing"
OUT_HTML="$LANDING/docs/capi-manual.html"
OUT_IMG="$LANDING/docs/img/capi-manual"
TMP="${CLAUDE_JOB_DIR:-${TMPDIR:-/tmp}}/tmp"
mkdir -p "$TMP" "$OUT_IMG"

echo "1/6  Assembling combined markdown (strip author-note comments; rewrite image paths) ..."
{
  for f in $(ls sections/*.md | sort); do
    # strip the leading <!-- ... --> author note, then point images at the published path
    perl -0777 -pe 's/^<!--.*?-->\s*//s' "$f" | sed 's#](\.\./img/#](/docs/img/capi-manual/#g'
    printf '\n\n'
  done
} > "$TMP/capi-web.md"

echo "2/6  Rendering mermaid diagrams to SVG (green theme) ..."
rm -f "$TMP"/capi-web.rendered*.svg "$TMP/capi-web.rendered.md"
PUPPETEER_SKIP_DOWNLOAD=1 npx -y @mermaid-js/mermaid-cli@10.9.1 \
  -i "$TMP/capi-web.md" -o "$TMP/capi-web.rendered.md" \
  -e svg -c build/mermaid-green.json -p build/puppeteer.json -b transparent >/dev/null 2>&1

echo "3/6  Publishing images (screenshots + diagrams) ..."
rm -f "$OUT_IMG"/*.png "$OUT_IMG"/capi-web.rendered-*.svg
cp img/*.png "$OUT_IMG"/
cp "$TMP"/capi-web.rendered-*.svg "$OUT_IMG"/ 2>/dev/null || true
# absolutize the mermaid SVG refs the cli inserted (they are relative to the tmp md)
sed -i -E 's#\((\./)?capi-web\.rendered-([0-9]+)\.svg\)#(/docs/img/capi-manual/capi-web.rendered-\2.svg)#g' "$TMP/capi-web.rendered.md"

echo "4/6  pandoc -> green CSWeb-hub HTML ..."
pandoc "$TMP/capi-web.rendered.md" -f gfm -t html5 --standalone \
  --template build/csweb-help-template.html \
  --shift-heading-level-by=1 \
  --toc --toc-depth=2 \
  -M title="UHC Survey Year 2 — CAPI Manual" \
  -M subtitle="Tablet & Application User Manual — CSEntry · Supervisor Hub · CSWeb" \
  -M author="Department of Health · ASPSI — Universal Health Care Survey (Year 2)" \
  -M date="June 2026" \
  -o "$OUT_HTML"

echo "5/6  Stripping any residual HTML comments (public-safe) ..."
perl -0777 -i -pe 's/<!--.*?-->//gs' "$OUT_HTML"

echo "6/6  Setting descriptive alt text on the 7 SVG diagrams (WCAG 1.1.1) ..."
python - "$OUT_HTML" <<'PY'
import re, sys
out = sys.argv[1]
# diagrams render in document order = capi-web.rendered-N.svg (N is stable per source order)
ALTS = {
  1: "Diagram: the CAPI system at a glance — supervisor and enumerator tablets (running LoginApp/MenuApp and F1/F3/F4) exchange assignments and finished interviews over Bluetooth, then sync or relay to the CSWeb server where the data manager monitors.",
  2: "Diagram: a normal field day — sign in to LoginApp, get your assignment, collect interviews (offline is fine), save and accept each case, then sync to CSWeb directly or hand to the supervisor to relay.",
  3: "Diagram: role hierarchy — the Data Manager/Admin (CSWeb) oversees the Field Supervisor, who oversees the Enumerators.",
  4: "Diagram: sign-in flow — open CSEntry, tap the green plus in LoginApp, enter username then password, and your role menu opens.",
  5: "Diagram: the life of a case — Not started, then Partial (save and resume), then Completed, then Synced to the server.",
  6: "Diagram: the supervisor's data path — assign an enumeration area over Bluetooth, collect finished interviews over Bluetooth, then relay them to CSWeb over the internet (merged by 12-digit case key).",
  7: "Diagram: troubleshooting decision tree — start from 'What's wrong?' and branch to can't sign in, no assignments, GPS, sync, and other common problems.",
}
def fix(m):
    tag, n = m.group(0), int(m.group(1))
    if n in ALTS:
        tag = re.sub(r'alt="[^"]*"', 'alt="' + ALTS[n].replace('"', "'") + '"', tag, count=1)
    return tag
html = open(out, encoding="utf-8").read()
html = re.sub(r'<img[^>]*capi-web\.rendered-(\d+)\.svg[^>]*>', fix, html)
open(out, "w", encoding="utf-8").write(html)
print("   alt text set on diagrams:", ", ".join(str(k) for k in sorted(ALTS)))
PY

echo "Done -> $OUT_HTML"
echo "Images -> $OUT_IMG ($(ls -1 "$OUT_IMG" | wc -l) files)"
