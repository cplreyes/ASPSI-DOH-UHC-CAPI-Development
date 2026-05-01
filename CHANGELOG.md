# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## v1.3.0 — Round 3 Internal QA (2026-05-01)

### Fixed
- Q1_3 Middle Initial should be optional (apply same fix pattern as #14) ([#25](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/25))
- **[HIGH]** Q4/Q9/Q10/Q11 — raw Zod error 'Expected number, received nan' leaks to UI ([#19](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/19))

### Improved
- **[HIGH]** Section F/G multi-select state pollution: selections unchecked when answering other questions ([#33](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/33))
- Test Facility present in seed/cached facility list (also on staging) ([#28](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/28))
- Inconsistent Other label casing Q2 comma form vs Q5 parens form ([#26](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/26))
- Default button height 32px below 44px tablet touch-target minimum ([#23](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/23))

### Other
- **[HIGH]** F2 PWA enrollment: Enroll button no-ops on real-browser staging (verified token, no IDB write, no error) ([#46](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/46))
- **[HIGH]** F2 PWA `.env.local` stale — missing `VITE_F2_PROXY_URL` silently breaks staging build ([#45](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/45))
- Worker PBKDF2 hash defaults (600k iters) exceed Cloudflare Workers runtime cap (100k) ([#35](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/35))
- **[HIGH]** Cloudflare Pages auto-deploy on staging push is not firing ([#34](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/34))
- Header subtitle low contrast uses --muted instead of --muted-foreground ([#30](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/30))
- Right-edge floating arrow indicator clips off-screen at 375px viewport ([#29](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/29))
- Locked sidebar sections appear as enabled buttons in a11y tree ([#27](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/27))
- No visible focus ring on keyboard Tab navigation ([#24](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/24))
- **[HIGH]** Disabled buttons fail WCAG AA contrast (opacity:0.5 on teal → ~2:1) ([#22](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/22))
- **[HIGH]** Form layout pushed off-center on viewports ≥1600px ([#21](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/21))
- **[HIGH]** Inverted heading hierarchy — page H1 (18px) smaller than section H2 (24px) ([#20](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/20))

## v1.1.1 — UAT Round 2 (2026-04-25)

### Fixed
- **[CRITICAL]** Cannot proceed when gating question answered No (Q12, Q31, similar) ([#15](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/15))
- Q9: Month(s) field should be optional, not required ([#14](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/14))
- **[HIGH]** Test Scenario Observations ([#12](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/12))
- In your current position, how many (months/years) have you worked at this health facility? ([#3](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/3))
- How old are you as of your last birthday (in years)? ([#1](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/1))

### Improved
- What is your role at this health facility? ([#2](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/2))

## v1.1.0 — UAT Round 1 (2026-04-25)

### Fixed
- **[HIGH]** Mid-section skip logic — conditional jumps not enforced (Q34/Q38/Q39/Q44/Q48/Q53/Q69/Q70/Q87/Q88) ([#13](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/13))
- **[HIGH]** Section Applicability Issue (Section G) ([#11](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/11))
- **[CRITICAL]** Auto-Advance Issue on Required Questions ([#10](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/10))
- **[HIGH]** Q25: – Conditional Logic Restriction Issue ([#8](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/8))
- **[HIGH]** Q12: Have you heard about Universal Health Care (UHC) prior to this survey? ([#6](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/6))
- In your current position, how many (months/years) have you worked at this health facility? ([#5](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/5))
- How old are you as of your last birthday (in years)? ([#4](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/4))

