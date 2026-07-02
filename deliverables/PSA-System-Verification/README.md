# DOH UHC Survey Year 2 — CAPI System Verification &amp; Documentation (for PSA)

Evidence that a working CAPI application exists across all instruments — the mobile/tablet apps, the CSWeb server, and the F2 PWA + Admin Portal — plus install-and-use documentation **and a complete, section-by-section question list** for each. Prepared for PSA review.

**Prepared by:** Carl Patrick L. Reyes (Data Programmer / CAPI developer) · ASPSI for DOH.

## Contents

| File | What it is |
|---|---|
| `index.html` | **Web version** — the single-page documentation site (overview, verification status, install guide, per-instrument sections with screenshots). Intended for hosting at `csweb.asiansocial.org/docs`. |
| `F1-Facility-Head-Survey-Install-and-Use.md` | F1 standalone install &amp; use guide. |
| `F3-Patient-Survey-Install-and-Use.md` | F3 standalone install &amp; use guide. |
| `F4-Household-Survey-Install-and-Use.md` | F4 standalone install &amp; use guide. |
| `CSWeb-Server-Guide.md` | CSWeb server guide. |
| `F2-HCW-Survey-PWA-Install-and-Use.md` | F2 Healthcare Worker Survey (PWA) + Admin Portal install &amp; use guide. |
| `F1/F3/F4-Full-Question-List.md`, `F2-Full-Question-List.md` | **Complete, sectioned question lists** — every question each instrument asks (with type + answer options), generated from the CSPro data dictionaries (F1/F3/F4) and the app data (F2), so they match the deployed apps exactly. Also embedded as collapsible per-section blocks in `index.html`. |
| `gen-question-list.py`, `embed-question-lists.py` | Reproducible generators: build the question lists from the dictionaries and embed them into the web doc. |
| `screenshots/` | Captured evidence (CSEntry app list, per-instrument CAPI screens, CSWeb sign-in, F2 PWA + Admin Portal). |

## Verification status

| Component | Status |
|---|---|
| F1 Facility Head Survey (CSEntry) | ✅ Verified working — screenshots captured |
| F3 Patient Survey (CSEntry) | ✅ Verified working — screenshots captured |
| F4 Household Survey (CSEntry) | ✅ Verified working — screenshots captured |
| CSWeb server | ✅ Live (sign-in captured) · ⏳ authenticated dashboard pending admin login |
| F2 HCW Survey PWA + Admin Portal | ✅ Live — PWA enrollment + Admin sign-in + operator guide captured · ⏳ authenticated dashboards pending admin login |

## How the screenshots were produced

The three CAPI instruments were launched on an Android tablet (CSEntry on the `capi_tablet` emulator, 2560×1600) and driven through their entry flow; screens were captured with `adb`. CSWeb and the F2 PWA + Admin Portal were captured in a browser at their live public addresses. *(Note: the emulator itself cannot sync to CSWeb due to a local TLS issue — issue #390 — which does not affect capturing the app screens; the real CSWeb already holds real cases synced from the field tests.)*

## To complete (pending your input — login-gated only)

1. **CSWeb admin login** → deployed-apps list, Sync Report with real cases, GPS map, case view.
2. **F2 Admin Portal login** → authenticated dashboards (live response data, GPS map, user/role management). The PWA enrollment, Admin sign-in, and operator guide are already captured.
3. *(Optional)* deeper CAPI screenshots — GPS auto-fetch, consent, a combined-question screen, verification photo, sync success.
