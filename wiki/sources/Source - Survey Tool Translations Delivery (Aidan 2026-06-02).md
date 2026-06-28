---
type: source-summary
source: "Gmail thread 19e85e4018e2507d — Aidan (spprt.aspsi.doh.uhc.survey2@gmail.com) → clreyes6@up.edu.ph, 2026-06-02"
date_ingested: 2026-06-28
tags: [capi, translations, multi-language, build-input, f1-f3-f4]
---

# Source - Survey Tool Translations Delivery (Aidan 2026-06-02)

**Email, Aidan (`spprt.aspsi.doh.uhc.survey2@gmail.com`) → Carl, 2026-06-02.** Concrete delivery of translated survey tools for the CAPI build, via a Google Drive folder: `https://drive.google.com/drive/folders/1Ja--pVqFBG31ckdRB_X7svxFqyj50u9c`. Fetched 2026-06-28 (UP connector).

## Delivery state (as of 2026-06-02)

- **Batch 1 — Bicolano, Bisaya, Cebuano, Waray: DONE.**
- **Batch 2 — Tagalog, Ilocano, Hiligaynon: PENDING** (awaiting translation-check results; update to follow).
- **Two file versions provided:**
  - **Version 3.1** — changes tracked (green font), **except Cebuano**.
  - **Version 3.2** — clean (revisions integrated, highlights removed). *Use 3.2 for the build.*

## Build relevance

Confirms the standing translation gap: **Batch 1 is build-ready; Batch 2 (Tagalog/Ilocano/Hiligaynon) was still not QC-cleared** as of June 2 — consistent with [[project_aspsi_cspro_translations]] (fil/ilo/hil F3-F4 blocked on ASPSI delivery) and the switcher-infra approach in [[project_aspsi_translations_pipeline]]. The drop-in pipeline (maps → regenerate → deploy) is proven; Batch 2 wires in when QC-cleared. Supersedes the snapshot in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Tool Translation Delivery Status 2026-05-15|the 2026-05-15 status]].

> [!note] Files are in the Drive folder (not email attachments). Per [[reference_drive_gmail_connector_limits]], folder children are only enumerable/readable once opened in the browser — to pull these via the connector, open each once in Drive first; otherwise download from the folder link.

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CAPI Seven-Language Translation Build]] — the 7-language build + PSA gate.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Survey Tool Translation Delivery Status 2026-05-15]] — prior status snapshot.
