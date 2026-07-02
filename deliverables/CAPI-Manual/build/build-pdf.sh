#!/usr/bin/env bash
# Rebuild the CAPI Manual: sections/*.md -> CAPI-Manual.md -> CAPI-Manual.html -> CAPI-Manual.pdf
# Requires: pandoc + Google Chrome (headless). Mermaid renders client-side via build/mermaid.min.js.
# Run from the CAPI-Manual/ directory:  bash build/build-pdf.sh
set -e
cd "$(dirname "$0")/.."

CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
DIR="$(pwd -W 2>/dev/null || pwd)"          # Windows-style path for Chrome
DIRW="${DIR//\//\\}"

echo "1/3  Assembling combined markdown ..."
{
  cat <<'YAML'
---
title: "UHC Survey Year 2 — CAPI Manual"
subtitle: "Tablet & Application User Manual — CSEntry · Supervisor Hub · CSWeb"
author: "Department of Health · ASPSI — Universal Health Care Survey (Year 2)"
date: "June 2026"
toc-title: "Contents"
---

YAML
  for f in $(ls sections/*.md | sort); do
    perl -0777 -pe 's/^<!--.*?-->\s*//s' "$f" | sed 's#](\.\./img/#](img/#g'
    printf '\n\n'
  done
} > CAPI-Manual.md

echo "2/3  pandoc -> HTML ..."
pandoc CAPI-Manual.md -f gfm -t html5 --standalone \
  --toc --toc-depth=2 \
  --lua-filter=build/mermaid.lua \
  --css=build/purple.css \
  --include-in-header=build/head.html \
  -o CAPI-Manual.html

echo "3/3  Chrome headless -> PDF ..."
rm -f CAPI-Manual.pdf
"$CHROME" --headless=new --disable-gpu --no-sandbox --no-first-run --no-default-browser-check \
  --user-data-dir="${TMP:-/tmp}/capi-chrome-pdf" \
  --allow-file-access-from-files --export-tagged-pdf \
  --virtual-time-budget=30000 --run-all-compositor-stages-before-draw \
  --generate-pdf-document-outline --no-pdf-header-footer \
  --print-to-pdf="${DIRW}\\CAPI-Manual.pdf" \
  "file:///${DIR}/CAPI-Manual.html"

echo "Done -> CAPI-Manual.pdf"
