---
type: entity
tags: [aspsi, qa, testing, team]
source_count: 1
aliases: [Sean]
---

# Shan Lait

ASPSI Research Assistant formally introduced at the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-04-13|Apr 13, 2026 ASPSI team meeting]] and assigned as **QA Tester** for the F-series CAPI stack — **F2 PWA + Admin Portal** (production at v2.0.0 since 2026-05-04, **UAT Round 2 in flight** with Kidd) and the downstream **CSPro CAPI applications** (F1/F3/F4) once those reach build state. Carl's primary tester and the first external pair of eyes on every build artifact.

> [!note] Name correction
> Earlier wiki entries and scrum/log content (pre-Apr 15, 2026) referred to this person as **"Sean"** based on a phonetic mishearing. The formal Apr 13 meeting minutes (docx) introduced **Shan Lait** as the canonical spelling. The wiki was swept on 2026-04-15 to replace all "Sean" references with "Shan" / "Shan Lait"; `aliases: [Sean]` is preserved in frontmatter so searches on the old name still land here.

## Role

- **Currently in flight (Sprint 004, since 2026-05-04):** UAT Round 2 against the F2 PWA + Admin Portal at v2.0.0. Walks both the HCW-Survey side (8 prod-signed enrollment tokens DEMO-HCW-001..008) and the Admin Portal side (`shan_admin` account; both UAT testers walk both sides). Issues filed under the GH label `from-uat-round-2-2026-05`. Tester guides at `docs/F2-PWA-UAT-Round-2-{HCW-Survey,Admin-Portal}-Tester-Guide-2026-05-04.md`.
- **2026-05-07 catch — orphan-admin guard finding (E4-APRT-050).** While testing step U.E1 of §5.12 of the Admin Portal tester guide ("delete carl_admin → expected: 'cannot orphan the last Administrator'"), Shan surfaced that the guard was specced but never implemented in code — the row was hard-deleted, locking Carl out of the prod admin portal. Real bug, not a misclick. Recovery same session: Shan re-created `carl_admin` via Users dashboard → Create User; Carl rotated the temp password via Worker API two-step PATCH. Filed as **E4-APRT-050** for v2.0.1 hotfix. Excellent first finding under R2's full surface.
- **Upcoming (Sprint 005, 2026-05-12 Tue):** UAT Round 3 against **staging** at v2.0.1-rc, focused on the v2.0.1 hotfix queue (orphan-admin guard verification, change-password UI, `last_login_at` populating, Create-HCW UI, per-tester admin accounts). Round 3 is Admin-Portal-only (no HCW Survey changes in v2.0.1) so testing scope is bounded. Tester guide skeleton at `docs/F2-PWA-UAT-Round-3-Admin-Portal-Tester-Guide-DRAFT.md`. R2 + R3 run in parallel with explicit env labels (R2 = prod / R3 = staging) to avoid confusion.
- **Earlier rounds (closed):** UAT Rounds 1 + 2 vs the F2 PWA at v1.1.1 (Apr 23 → Apr 25), 13 issues fixed; cross-platform QA pass closure (E4-APRT-035) on E1 Chrome + tablets, paired with Carl during 2026-05-02 → 2026-05-05.
- **Downstream:** F1/F3/F4 CSPro CAPI applications once those reach build state. F1 is closest — dictionary Build-ready 2026-05-04 (sign-off CLOSED); FMF Section A in flight (E3-F1-001).
- Reports bugs per the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off|forward-only sign-off rule]] — symptoms route back to the owning source doc rather than cascading gate approvals.
- Test comms flow through the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] project mailbox (`aspsi.doh.uhc.survey2.data@gmail.com`), the CAPI Viber group, and the `#f2-pwa-uat` Slack channel.

## Context

- Newly onboarded RA as of Apr 13, 2026 (introduced at the internal ASPSI team meeting alongside Daisy Ramos).
- Engaged from Sprint 001 (Apr 2026) onward as the test pipeline for F2 and, downstream, F1/F3/F4 CSPro builds. Scope grew with the Admin Portal program (Sprints AP1–AP4 / E4-APRT-001..051) and the v2.0.0 cutover; further v2.0.1 hotfix work surfaced via R2 (E4-APRT-050 orphan-admin guard, E4-APRT-051 change-password UI).
- The forward-only sign-off rule means Shan's first reads on any deliverable are treated as the acceptance gate — there is no intermediate formal design sign-off before artifacts hit him.
- Memory: `memory/team_sean_qa_tester.md` (filename preserved for continuity; content refers to Shan).
