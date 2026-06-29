#!/usr/bin/env bash
# Rebuild the CAPI Manual as an EDITABLE .docx for review markup.
# sections/*.md -> combined md -> (mermaid -> PNG) -> pandoc docx -> bordered tables.
# Requires: pandoc, node/npx (mermaid-cli auto-fetched), Google Chrome, python + python-docx.
# Run from the CAPI-Manual/ directory:  bash build/build-docx.sh
set -e
cd "$(dirname "$0")/.."

echo "1/4  Assembling combined markdown (with DRAFT banner) ..."
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
  printf '\n> **DRAFT FOR REVIEW — June 2026.** Editable copy circulated for ASPSI / DOH review and markup. Please add comments or tracked changes.\n\n'
  for f in $(ls sections/*.md | sort); do
    perl -0777 -pe 's/^<!--.*?-->\s*//s' "$f" | sed 's#](\.\./img/#](img/#g'
    printf '\n\n'
  done
} > ./_docx_combined.md

echo "2/4  Rendering mermaid diagrams to PNG ..."
PUPPETEER_SKIP_DOWNLOAD=1 npx -y @mermaid-js/mermaid-cli@10.9.1 \
  -i ./_docx_combined.md -o ./_docx_rendered.md -e png -p build/puppeteer.json -b white >/dev/null 2>&1

echo "3/4  pandoc -> docx ..."
pandoc ./_docx_rendered.md -f gfm+yaml_metadata_block --toc --toc-depth=2 -o CAPI-Manual.docx

echo "4/4  Post-processing (table borders + header shading) ..."
python build/postprocess_docx.py CAPI-Manual.docx

rm -f ./_docx_combined.md ./_docx_rendered.md ./_docx_rendered-*.png
echo "Done -> CAPI-Manual.docx"
