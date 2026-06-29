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

echo "1/5  Assembling combined markdown (strip author-note comments; rewrite image paths) ..."
{
  for f in $(ls sections/*.md | sort); do
    # strip the leading <!-- ... --> author note, then point images at the published path
    perl -0777 -pe 's/^<!--.*?-->\s*//s' "$f" | sed 's#](\.\./img/#](/docs/img/capi-manual/#g'
    printf '\n\n'
  done
} > "$TMP/capi-web.md"

echo "2/5  Rendering mermaid diagrams to SVG (green theme) ..."
rm -f "$TMP"/capi-web.rendered*.svg "$TMP/capi-web.rendered.md"
PUPPETEER_SKIP_DOWNLOAD=1 npx -y @mermaid-js/mermaid-cli@10.9.1 \
  -i "$TMP/capi-web.md" -o "$TMP/capi-web.rendered.md" \
  -e svg -c build/mermaid-green.json -p build/puppeteer.json -b transparent >/dev/null 2>&1

echo "3/5  Publishing images (screenshots + diagrams) ..."
rm -f "$OUT_IMG"/*.png "$OUT_IMG"/capi-web.rendered-*.svg
cp img/*.png "$OUT_IMG"/
cp "$TMP"/capi-web.rendered-*.svg "$OUT_IMG"/ 2>/dev/null || true
# absolutize the mermaid SVG refs the cli inserted (they are relative to the tmp md)
sed -i -E 's#\((\./)?capi-web\.rendered-([0-9]+)\.svg\)#(/docs/img/capi-manual/capi-web.rendered-\2.svg)#g' "$TMP/capi-web.rendered.md"

echo "4/5  pandoc -> green CSWeb-hub HTML ..."
pandoc "$TMP/capi-web.rendered.md" -f gfm -t html5 --standalone \
  --template build/csweb-help-template.html \
  --toc --toc-depth=1 \
  -M title="UHC Survey Year 2 — CAPI Manual" \
  -M subtitle="Tablet & Application User Manual — CSEntry · Supervisor Hub · CSWeb" \
  -M author="Department of Health · ASPSI — Universal Health Care Survey (Year 2)" \
  -M date="June 2026" \
  -o "$OUT_HTML"

echo "5/5  Stripping any residual HTML comments (public-safe) ..."
perl -0777 -i -pe 's/<!--.*?-->//gs' "$OUT_HTML"

echo "Done -> $OUT_HTML"
echo "Images -> $OUT_IMG ($(ls -1 "$OUT_IMG" | wc -l) files)"
