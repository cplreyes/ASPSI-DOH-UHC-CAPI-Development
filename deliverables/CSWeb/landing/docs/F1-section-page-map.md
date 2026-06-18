# F1 questionnaire — section → page map (build aid)

Rendered from `raw/Project-Deliverable-1/Annex F1…April 08.pdf` (34 pp) via PyMuPDF
at 2× → `docs/img/f1-paper-pNN.png` (1224×1584 each, ~7 MB total). Used to place
the "end of section → printed page ↔ CAPI screens" blocks in the crosswalk.

| Pages | Block / section |
|---|---|
| 1–2 | **Informed Consent** (Part I info + Part II certificate). Contains named study contacts (SJREB / DOH / ASPSI emails + phones). **DECISION (Carl, 2026-06-16): include as-is** — the link is not for distribution even though the site is public. Built into the crosswalk. |
| 3 | Front matter: Questionnaire No · **Field Control** · **Health Facility & Geographic ID** · **A. Facility Head Profile** · **B. Facility Profile** |
| 4–11 | **C. Universal Health Care (UHC) Implementation** |
| 12–18 | **D. YAKAP / Konsulta Package** |
| 19 | **E. Awareness on Expanded Health Programs (BUCAS and GAMOT)** |
| 20–24 | **F. DOH Licensing — Status and Barriers** |
| 25–27 | **G. Service Delivery Process** |
| 28–29 | **H. Human Resources for Health** |
| 30–34 | **Secondary Data block** (note: reuses A–D letters — a *different* lettering than the main A–H). p30 Hospital Census / Patient Load · p31–32 HCW counts (full/part-time, departures, non-renewed contractuals) · p33–34 YAKAP service availability, diagnostic procurement, standard cost / markup. |

Notes for the full build:
- A printed page can carry several sections (p3 = front matter + A + B); a section can span pages (C = p4–11). Each section's end-block shows the page(s) it actually appears on, labelled — so a page may legitimately repeat across adjacent sections.
- The **Secondary Data block (pp. 30–34)** is its own thing; the earlier F1 skip-logic spec flagged it. Label it distinctly so its A–D don't collide with the main A–H.
- Paper pages are renderable on demand; the CAPI screen-sequence panels fill in from the emulator capture.
