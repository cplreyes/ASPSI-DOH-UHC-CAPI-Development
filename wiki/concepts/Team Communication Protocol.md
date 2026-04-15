---
type: concept
tags: [communication, process, team, working-convention]
source_count: 1
---

# Team Communication Protocol

Formal communication routing rules established at the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-04-13|Apr 13, 2026 ASPSI team meeting]] in response to accumulated lessons learned about client management, iteration control, and coordination failures. These rules govern all project communications from Apr 13, 2026 onward.

## Why this exists

The Apr 13 lessons-learned discussion surfaced several chronic problems:
- Viber group chat was flooded; signal-to-noise too low to track commitments.
- Direct / informal DOH↔RA exchanges bypassed project leadership, causing conflicting requests and uncoordinated feedback from DOH, PSA, and ADB to hit the team unfiltered.
- No accountability trail for decisions and file exchanges.
- Team members over-extended beyond agreed scope because no one was gating inbound requests.

The protocol below is the corrective action.

## Routing rules

### Within the team

- **Streamline.** Not every message goes to the big group.
- **Smaller groups** as needed.
- **Viber** — urgent updates and information only.
- **Email** — file sharing and anything that needs an audit trail. Use relevant subject lines to avoid long threads.
- **Ms. Juvy (ASPSI Coordinator) must be in the loop** on every communication.

### From team → DOH

- **Authorized senders:** **Ms. Juvy Chavez-Rocamora (ASPSI Coordinator)**, **Dr. Paulyn Claro (Project Lead)**, **Dr. Merlyne Paunlagui (Asst Project Lead / Survey Manager)**. These are the only three people who may send to DOH.
- **Official submissions are done by the Project Coordinator (Juvy).**
- **Team members must prepare and share deliverables in advance** to give the Project Coordinator sufficient time for final review before submission.
- **Viber** — urgent updates/info only.
- **Email** — file sharing, relevant subject lines.

### From DOH → team

- DOH focal person → **Project Lead / Asst Proj Lead + ASPSI focal person** (cc: RAs).
- **Viber** — urgent updates/info/questions only.
- **Email** — file sharing.
- **If DOH follow-ups arise, they are shared in the big ASPSI-DOH group** — no side-channel handling.

### Direct DOH ↔ RA exchanges

**Prohibited.** All DOH requests must be transparently communicated and shared with the entire team. Informal or bilateral requests between DOH and Research Associates are explicitly disallowed.

## Meeting notes workflow

- **Internal team meetings** → notes captured.
- **Meetings with DOH** → minutes / summary points captured.
- **Review gate**: notes reviewed by attendees of the meeting.
- **Approval gate**: Project Lead or Asst Proj Lead approves before any notes are sent to DOH.
- Notes should be shared to the Project Lead after any meeting.

## Implications for Carl

Carl is **not** an authorized DOH-facing sender. This is formally established regardless of the CSA TOR scope. Carl's operating rules:

1. **Never cc DOH directly** on technical decisions, clarifications, or deliverable drops. Route everything to Juvy first (with Dr. Claro / Dr. Paunlagui cc) and let her forward/submit.
2. **Submit F1/F2 build artifacts to Juvy** with enough lead time for her to review + forward to DOH. "Enough lead time" is not defined numerically yet — treat it as ≥1 working day until a norm emerges.
3. **Flag DOH-originating requests that arrive directly** (e.g., if someone from PMSMD pings Carl informally) back up to Juvy + the ASPSI project mailbox so the team has visibility. This is an explicit requirement from the Apr 13 protocol, not a nice-to-have.
4. **The forward-only sign-off rule** ([[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off|Forward-Only Sign-Off]]) still governs internal bug routing; the comms protocol only constrains external (DOH-facing) channels.
5. **Weekly → bi-monthly status cadence** (per the same meeting's "Other Matters") means Carl's E0-010 status-format deliverable should target a bi-monthly rhythm.

## Related

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - ASPSI Team Meeting 2026-04-13|Source — ASPSI Team Meeting, 2026-04-13]] (establishing meeting)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] (organization)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD|DOH-PMSMD]] (client)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off|Forward-Only Sign-Off]] (internal bug routing — orthogonal concern)
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/LSS Meeting|LSS Meeting]] (internal technical decision ceremony — a different channel from comms routing)
