---
title: F2 PWA Design Spec
date: 2026-04-17
project: ASPSI-DOH-CAPI-CSPro-Development
author: Carl Patrick Reyes
status: approved-for-planning
plan_role: Plan B (parallel to CSPro/CSEntry Plan A)
quality_bar: production-eligible
effort_estimate: 150–200h cumulative
related:
  - deliverables/F2/F2-Spec.md
  - deliverables/F2/F2-Skip-Logic.md
  - deliverables/F2/F2-Validation.md
  - deliverables/F2/F2-Cross-Field.md
  - deliverables/F2/F2-Build-Handoff.md
  - deliverables/F2/F2-0_Tooling-and-Access-Model-Decision-Memo.md
  - deliverables/F2/apps-script/
---

# F2 PWA Design Spec

## 1. Context and Decision History

This is the design for the F2 (Healthcare Worker Survey) instrument delivered as a Progressive Web App (PWA). It is **Plan B**, running alongside the primary CSPro/CSEntry delivery (Plan A).

### Why PWA

- **Dr Myra requested** (2026-04-17 Zoom) an offline, installable, self-administered option for F2 comparable to MS Access — an app HCWs can install on their own laptop or phone, fill in the field, and submit later.
- **Carl selected capture-path (b)**: offline completion → export → email/upload back to ASPSI. Online Google Forms demoted to "least priority" because field internet is unreliable.
- **CSPro/CSEntry does not support iOS.** iPhone-using HCWs have no offline path without a PWA. Verified against Wikipedia and csprousers.org.
- **PWA is the one architecture** that covers iPhone + Android + laptop in a single codebase with true offline capability.
- **F2 is now the last instrument** in the suite (per same Zoom call). PWA work has runway behind F1/F3/F4 CSPro delivery.
- **Carl is building it as a side-track learning project.** Minimal React experience, no end-to-end PWA experience. Production-eligible is the target, reachable in 4–10 months depending on burst pace.

### Plan B discipline

- PWA and CSPro F2 coexist. HCWs pick the path that fits their device.
- Promotion triggers to Plan A (if ever) are explicit, gated on milestone checkpoints (section 11).
- PWA must never degrade Plan A delivery. F1/F3/F4 CSPro work always takes priority in burst allocation.

## 2. Non-Goals

- Not replacing CSPro for F1/F3/F4.
- Not a general-purpose survey platform. Scope is the F2 instrument only. Generator pattern is reusable if needed later.
- Not building MDM or remote device management. HCWs install on personal devices; ASPSI has no remote control.
- Not building realtime collaboration. Single user per device, single response per HCW.
- Not building native mobile apps (iOS/Android binaries). PWA only.
- Not replacing the Google Forms F2 path. Both paths coexist, writing to the same master Sheet.
- Not implementing push notifications (out of scope for MVP; revisit post-M11).

## 3. High-Level Architecture

```
┌─────────────────────────────┐
│   HCW Device                │
│  (iPhone / Android / laptop)│
│                             │
│  ┌───────────────────────┐  │
│  │ PWA (standalone mode) │  │
│  │                       │  │
│  │  React + Vite         │  │
│  │  Service Worker       │  │
│  │  IndexedDB (Dexie)    │  │
│  └───────────┬───────────┘  │
└──────────────┼──────────────┘
               │ HTTPS (signed)
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌─────────────┐   ┌──────────────────────┐
│ Cloudflare  │   │ Apps Script Web App  │
│ Pages (CDN) │   │ (under ASPSI mailbox)│
│             │   │                      │
│ static      │   │  ingest endpoints    │
│ bundle      │   │  signature verify    │
└─────────────┘   └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Google Sheet         │
                  │ (master dataset)     │
                  │  F2_Responses        │
                  │  F2_Audit            │
                  │  F2_Config           │
                  │  FacilityMasterList  │
                  │  F2_DLQ              │
                  └──────────────────────┘
```

Three tiers: **Client** (PWA on device), **CDN** (Cloudflare Pages serves static bundle), **Backend** (Apps Script + Sheet, reuses existing project infrastructure). The existing Day-3 Apps Script bundle pivots from Google-Forms-generator to PWA ingestion backend; the Sheet becomes the single master dataset for both paths.

## 4. Backend Design

### 4.1 Google Sheet — master dataset

Single spreadsheet under the ASPSI project mailbox. Tabs:

| Tab | Role |
|---|---|
| `F2_Responses` | One row per response. PWA + Google Forms both write here. ~120 columns (one per F2 item + metadata). |
| `F2_Audit` | Audit log of submissions, installs, errors, sync events. |
| `F2_Config` | Server-side config the PWA reads: `current_spec_version`, `min_accepted_spec_version`, `kill_switch`, broadcast messages. |
| `FacilityMasterList` | Facility table (already scaffolded in Day-3 bundle). PWA caches at install, refreshes on sync. |
| `F2_DLQ` | Dead-letter queue for submissions that fail validation. Nothing is ever lost. |

**Metadata columns on every `F2_Responses` row:** `submission_id`, `client_submission_id` (UUID from device), `submitted_at_server`, `submitted_at_client`, `source` (`PWA` | `Forms`), `spec_version`, `app_version`, `hcw_id`, `facility_id`, `device_fingerprint`, `sync_attempt_count`, `status`.

### 4.2 Apps Script Web App — endpoints

One deployed Web App, routes dispatched by `e.parameter.action`:

| Route | Method | Purpose |
|---|---|---|
| `?action=submit` | POST | Single response. Returns `submission_id` + server timestamp. |
| `?action=batch-submit` | POST | Array of queued responses (PWA sync drain). Up to 50 per call. |
| `?action=facilities` | GET | Returns `FacilityMasterList` as JSON. |
| `?action=config` | GET | Returns `F2_Config`. |
| `?action=spec-hash` | GET | Returns hash of current spec; PWA compares to detect updates. |
| `?action=audit` | POST | Lightweight telemetry (install, error, resume). |

**Deployment:** `Execute as: Me` (project mailbox owner), `Who has access: Anyone, even anonymous`. HCWs do not have Google accounts in this flow.

### 4.3 Security model

- **Static API key** embedded in PWA build at deploy time. Public — the Sheet is write-only from the PWA side, risk is spam not data theft.
- **HMAC signatures** on every request using a rotating shared secret stored in Apps Script `ScriptProperties`. Server verifies before accepting.
- **Rate limiting** by IP + per-`hcw_id` to kill spam.
- **Upgrade path (post-M11):** per-HCW signed enrollment tokens if threat model demands. Out of scope for MVP.

### 4.4 Data flow — one submission round-trip

```
HCW fills F2 offline (minutes to days)
        │
        ▼
IndexedDB: record saved, status=pending_sync, client_submission_id=UUID
        │
        ▼ device online + sync trigger
POST /batch-submit → Apps Script
        │
        ▼
For each response:
  ├─ verify HMAC signature
  ├─ idempotency check on client_submission_id
  │   ├─ already in F2_Responses → return existing server_submission_id
  │   └─ new → validate payload, append to F2_Responses
  └─ validation fail → append to F2_DLQ
        │
        ▼
Response: [{client_submission_id, server_submission_id, status, error?}, ...]
        │
        ▼
PWA updates IndexedDB: pending_sync → synced | rejected | retry_scheduled
```

### 4.5 Idempotency, dedup, versioning

- **Client-generated UUIDs** make every retry safe. Default to retry; mobile networks drop.
- **Last-submit-wins** for the same `hcw_id` submitting twice. Older row stamped `status: superseded`; both kept for audit.
- **Spec-version gating** via `F2_Config.min_accepted_spec_version`. Old-install PWAs get `409 Conflict` with update instruction. Prevents silent schema drift.

### 4.6 Performance budget

| Concern | Reality | Status |
|---|---|---|
| Cold-start latency | ~2–5s | Fine; PWA shows "syncing…" UI. |
| 6-min execution limit | `batch-submit` capped at 50 rows | Plenty; typical sync is <10 rows. |
| URL fetch quota | N/A (server receives, doesn't fetch) | No pressure. |
| 10M-cell Sheet cap | F2 max ~5,000 responses × 120 cols = 600k cells | <10% of cap. |
| Concurrent writes | `LockService` mutex on writes | Adequate at F2 volume. |

### 4.7 Admin dashboard

Apps-Script-served HTML (HtmlService). Read-only views of `F2_Responses` and `F2_Audit`: filter by facility, by date, by status; flag `F2_DLQ` rows; CSV export. Functional, not polished. If an upgrade is desired later, a second React app can consume the same Sheet via a `/api/admin` endpoint.

### 4.8 Failure modes

| Failure | Handling |
|---|---|
| Web App down | PWA queues locally; retries on interval. No data loss. |
| Sheet write fails (quota, race) | Apps Script retries; on permanent fail, write to `F2_DLQ`; email alert to project mailbox. |
| Network failure mid-upload | Idempotent replay via `client_submission_id`. |
| Expired spec version on client | `409 Conflict` → forced update. See §7.7. |

## 5. Frontend Design

### 5.1 Stack

| Concern | Choice | Rationale |
|---|---|---|
| Build tool | Vite | Fast, minimal config, large community. |
| Language | TypeScript | Type safety reduces runtime debugging for learner. |
| Framework | React 18 | Carl's existing familiarity. |
| Routing | react-router v7 | Mature, ubiquitous docs. |
| Form state | react-hook-form | Industry standard, great perf, minimal boilerplate. |
| Validation | Zod | TS-first, schemas derivable from spec. `zodResolver` for RHF integration. |
| Offline store | Dexie.js | Promise-based IndexedDB ORM. Clean API. |
| Service worker | vite-plugin-pwa (Workbox) | Declarative caching, auto-regenerates on build. |
| Styling | Tailwind CSS + shadcn/ui | Accessible, copy-paste components, no lock-in. |
| i18n | react-i18next | Bilingual (English + Filipino); label bundles from generator. |
| HTTP client | `fetch` (native) | No axios needed. |
| App-wide state | React Context | No Redux/Zustand for this size. |

### 5.2 Project structure

```
f2-pwa/
├── spec/                        # SINGLE SOURCE OF TRUTH (mirror of deliverables/F2/*.md)
│   ├── F2-Spec.md
│   ├── F2-Skip-Logic.md
│   ├── F2-Validation.md
│   ├── F2-Cross-Field.md
│   └── FacilityMasterList.json  # cached from /facilities endpoint
├── scripts/
│   └── generate.ts              # Parses spec → emits TS types, Zod schemas, form tree
├── src/
│   ├── generated/               # NEVER HAND-EDIT. Regenerated from spec.
│   │   ├── items.ts
│   │   ├── schema.ts            # Zod validators per section + composed full
│   │   ├── skip-logic.ts        # Skip predicates
│   │   └── cross-field.ts       # POST rules
│   ├── lib/
│   │   ├── db.ts                # Dexie schema
│   │   ├── sync.ts              # Sync orchestration
│   │   ├── api.ts               # Apps Script client
│   │   ├── hmac.ts              # Request signer
│   │   └── i18n.ts              # react-i18next setup
│   ├── components/
│   │   ├── ui/                  # shadcn/ui primitives
│   │   ├── survey/              # Question, Section, Navigator, Progress, SyncBadge
│   │   └── layout/
│   ├── pages/
│   │   ├── Home.tsx             # Install / enroll / resume
│   │   ├── Fill.tsx             # The form itself
│   │   ├── Review.tsx           # Pre-submit review
│   │   ├── Sync.tsx             # Sync queue status + retry
│   │   └── Help.tsx
│   ├── App.tsx
│   ├── main.tsx
│   └── sw.ts                    # Workbox service worker (declarative)
├── public/
│   ├── manifest.webmanifest
│   ├── icons/                   # 192, 512, maskable
│   └── offline.html             # Fallback shell for cold-start offline load
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

### 5.3 Pages and user flow

```
Home  →  Fill  →  Review  →  Sync
 │               ↑              ↑
 └── Resume ─────┘              │
                                │
               (Sync page also reachable from header SyncBadge at any time)
```

- **Home**: install prompt (Android) / tutorial (iOS), enroll (HCW id + facility select), resume.
- **Fill**: section-by-section, autosave on change (debounced), live skip-logic, inline validation.
- **Review**: all answers read-only, cross-field warnings, Submit button.
- **Sync**: pending queue, manual "Sync now", per-row status.
- **Help**: FAQ, contact, export-to-file escape hatch.

### 5.4 Domain components

| Component | Purpose |
|---|---|
| `<Question>` | Renders one item. Dispatches by type (text, number, single-select, multi-select, grid, date, etc.). Driven by `generated/items.ts`. |
| `<Section>` | Renders a list of `<Question>` with section header, progress, validation summary. |
| `<Navigator>` | Prev/next buttons, section jump list, required-field gate. |
| `<ProgressBar>` | % complete across whole instrument. |
| `<SyncBadge>` | Header pill showing online/offline + pending-sync count. Always visible. |
| `<InstallPrompt>` | Shows only when `beforeinstallprompt` fires (Android); hides after install. |

All props-in / callbacks-out. No component reaches into global store.

### 5.5 State management

| State | Lives in | Reason |
|---|---|---|
| Current form values (editing) | react-hook-form | Fine-grained rerenders, built-in RHF/Zod integration. |
| Completed/pending submissions | Dexie | Durable across reloads, offline-survives. |
| Facility list + server config | Dexie (write-through cache) | Available offline after first sync. |
| Online/offline status | React Context (`SyncContext`) | Read by SyncBadge + auto-sync trigger. |
| HCW identity | React Context (`AuthContext`) + Dexie | Set once at enroll, persisted. |
| UI language | React Context + `localStorage` | Survives reload. |

## 6. Generator Pattern

**Rule inherited from F1:** generator over hand-edit. Never edit `src/generated/*.ts` by hand. Revise `spec/*.md`, rerun `npm run generate`.

### 6.1 Inputs

- `spec/F2-Spec.md` — 114 items with type, label, options, required, group
- `spec/F2-Skip-Logic.md` — section graph + routing table
- `spec/F2-Validation.md` — hard-required fields + per-item rules
- `spec/F2-Cross-Field.md` — 20 POST rules
- `spec/FacilityMasterList.json` — facility table (cached from API)

### 6.2 Outputs

| File | Content |
|---|---|
| `src/generated/items.ts` | `items: Item[]` — id, type, label keys (en + fil), options, required, group |
| `src/generated/schema.ts` | Zod schemas per section + composed full-form schema |
| `src/generated/skip-logic.ts` | `shouldShow(itemId, answers): boolean` predicates |
| `src/generated/cross-field.ts` | POST rule evaluators |
| `public/locales/en.json` | English label bundle for react-i18next |
| `public/locales/fil.json` | Filipino label bundle |

### 6.3 Execution

- Manual: `npm run generate`
- Pre-commit hook: `npm run generate && git add src/generated/ public/locales/`
- CI: regenerates on each build; fails if `src/generated/` drifts from spec

### 6.4 Language choice

TypeScript, not Python. Lives in the PWA repo; shares types with the code it emits; avoids a cross-language toolchain. The F1 Python generator and this TS generator serve different targets but share the same conceptual pattern.

## 7. Offline / Sync Strategy

### 7.1 Service worker — caching by resource type

| Resource | Workbox strategy | Rationale |
|---|---|---|
| App shell (HTML/JS/CSS bundles) | Precache | Cold-start offline. |
| Icons, fonts, images | CacheFirst (30-day expiry) | Rarely change. |
| `/facilities`, `/config` | StaleWhileRevalidate | Show cached instantly, update in background. |
| `/spec-hash` | NetworkFirst (3s timeout → cache) | Detect updates promptly when online. |
| `/submit`, `/batch-submit` | NetworkOnly + Background Sync (Android) / foreground retry (iOS) | Never cached. |

First install downloads shell (~300–500 KB gzipped). Subsequent loads instant.

### 7.2 IndexedDB schema (Dexie)

```ts
// src/lib/db.ts
export const db = new Dexie('f2_pwa').version(1).stores({
  drafts:      'id, hcw_id, updated_at',
  submissions: 'client_submission_id, status, synced_at, hcw_id',
  facilities:  'id, region, province, name',
  config:      'key',
  audit:       '++id, event, occurred_at',
});
```

**Invariants:**

- `id` on a draft is stable from enroll onward (UUID, client-generated).
- Draft → submission on Submit: draft archived, submission row created with `status='pending_sync'`.
- `client_submission_id` is the idempotency key; **same on every retry, always**.
- Status state machine: `pending_sync → syncing → synced | rejected | retry_scheduled`.

### 7.3 Sync orchestrator — state machine

```
          pending_sync ◄── HCW taps Submit
               │
               │ online + sync trigger
               ▼
            syncing
               │
        ┌──────┼──────┐
        │      │      │
     200 OK  200 OK  network/5xx
      valid  invalid
        │      │      │
        ▼      ▼      ▼
      synced rejected retry_scheduled
                       │
                exponential backoff
              (30s → 2m → 10m → 1h)
                       │
                       └─→ pending_sync
```

**Sync triggers (priority order):**

1. Background Sync API (Android only — iOS WebKit lacks support)
2. Window `online` event (all platforms)
3. Periodic foreground check every 5 minutes (while app open + online)
4. Manual "Sync now" button on Sync page

**Batching:** up to 50 `pending_sync` rows per `batch-submit` call. Repeat until queue empty.

### 7.4 Install experience

**Android / desktop Chromium:** `beforeinstallprompt` captured and deferred; Home page shows "Install F2 App" button that fires `prompt()`.

**iOS Safari:** no `beforeinstallprompt`. Tutorial screen:

> "To install F2 on your iPhone:
> 1. Tap the Share button (square with up arrow)
> 2. Scroll and tap 'Add to Home Screen'
> 3. Tap 'Add'"

Friction is unavoidable — Apple platform constraint, not design choice.

**After install:** app launches in standalone mode (no browser chrome). First launch downloads `/facilities` + `/config`, caches service worker, ready for offline use.

### 7.5 Web App Manifest

```json
{
  "name": "F2 — Healthcare Worker Survey",
  "short_name": "F2 Survey",
  "start_url": "/",
  "display": "standalone",
  "orientation": "portrait",
  "theme_color": "#0f766e",
  "background_color": "#ffffff",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/icon-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "lang": "en"
}
```

### 7.6 Storage persistence and quota

1. **Request persistent storage** on install: `navigator.storage.persist()`. Android Chrome grants for installed PWAs; iOS Safari grants conditionally.
2. **Monitor quota** via `navigator.storage.estimate()` on Sync page visits. Warn user at >80% usage.
3. **Retention policy:** submissions at `status=synced` have their response body **purged after 7 days** (metadata retained for audit).
4. **Export-to-JSON escape hatch:** Sync page has "Export all responses as JSON" button. Belt-and-suspenders backup for storage-pressure or no-network edge cases.

### 7.7 Spec version handling

| Condition | Behavior |
|---|---|
| Client `spec_version` ≥ server `current_spec_version` | Submission accepted. |
| Client < server but ≥ `min_accepted` | Submission accepted. Response `{ update_available: true }`. Sync page shows update banner; SW updates on next resume. |
| Client < `min_accepted_spec_version` | Submission **rejected** with `409 Conflict`. App forces update. **Drafts migrated automatically where possible; flagged for HCW re-entry if schema is incompatible.** |

Spec version is bumped when: a question's code set changes, a required field is added, skip logic changes, or validation rules change. Label-only edits do not bump.

### 7.8 iOS-specific considerations

| Concern | Reality | Mitigation |
|---|---|---|
| Background Sync API | Not supported | iOS syncs only when foregrounded; adequate — HCWs open app to sync. |
| Service worker persistence | More aggressive eviction | App shell precached; loads offline regardless. |
| IndexedDB quota | ~50 MB nominal, evictable | Persistent storage request + lean local store + export escape hatch. |
| `beforeinstallprompt` | Not supported | Tutorial screen workaround. |
| Push notifications | iOS 16.4+ only | Out of scope for MVP. |

None are blockers for production-eligible.

## 8. Error Handling

### 8.1 User-facing UX

| Scenario | UX |
|---|---|
| Offline when syncing | SyncBadge turns yellow: "Offline — will sync when connected." |
| Submit fails (5xx / timeout) | Inline toast: "Couldn't sync — will retry in 30s." Draft preserved. |
| Validation error on-screen | Inline red text under field. No modal. |
| Spec version too old | Full-screen: "A new version is required. Updating…" Auto-reloads. |
| Quota >80% | Banner on Sync page: "Storage getting full. Sync or export to free space." |
| Double enrollment on same device | Modal: "A draft exists for HCW {id}. Resume or start new?" |
| Server-rejected submission | Sync page row turns red with reason. HCW can retry/edit. |

### 8.2 Developer visibility

- Every error written to local `audit` Dexie table with `{event, occurred_at, context}`.
- Audit drained to server on next successful sync via `POST /audit`.
- Server-side audit visible in Apps Script logs + `F2_Audit` Sheet tab.
- **No PII in error payloads** beyond `hcw_id`.

### 8.3 Global error boundary

Wraps React tree. Catches unrecoverable errors (malformed generated code, etc.):

> "Something went wrong. Your data is safe. Tap reload to continue." + "Send report" button that posts the error + audit tail to server.

## 9. Testing Strategy

Pragmatic, not dogmatic. Spend test budget where bugs cluster.

| Layer | Tool | Coverage target | What gets tested |
|---|---|---|---|
| Generator (`scripts/generate.ts`) | Vitest | 90%+ | Each spec markdown parses correctly; emits expected TS/Zod output. **Most bug-prone; highest payoff.** |
| Survey components | Vitest + React Testing Library | ~60% | `<Question>` renders every item type; `<Section>` honors skip logic. |
| Sync state machine | Vitest | 90%+ | Transitions, idempotency, backoff math. **Async + retries = bugs.** |
| Dexie operations | Vitest + fake-indexeddb | ~80% | Schema, draft→submission, 7-day purge. |
| E2E happy path | Playwright | 1 test | Install → enroll → fill → review → submit → sync, online + offline scenarios. |
| Cross-platform manual | Device matrix spreadsheet | Each release | Chrome Android, Safari iOS, Chrome Windows, Safari Mac. |

**YAGNI:** no Storybook, no Cypress, no visual regression.

## 10. Deployment and Distribution

### 10.1 Frontend

- **Host:** Cloudflare Pages. Connect GitHub repo → auto-deploy on push to `main`.
- **Preview deploys** on PRs and branches (test spec changes without affecting prod).
- **Custom domain:** TBD with ASPSI (placeholder: `f2.aspsi-doh.ph`). Free HTTPS.
- **Distribution to HCWs:** QR code + short URL on paper handout. Tap → browser opens → install / tutorial. No app stores.

### 10.2 Backend

- **Apps Script Web App** under the ASPSI project mailbox.
- **Versioned deploys:** each deploy creates a new version; frontend build pins to a specific deployment URL (not "latest"). Rollback = re-pin.
- **Secrets in `ScriptProperties`:** HMAC secret, internal API key. Rotatable via Apps Script UI.
- **Kill switch:** `F2_Config.kill_switch = true` → all endpoints return `503`. Frontend shows "Temporarily unavailable — data saved locally, try again later."

### 10.3 Build pipeline

1. Edit spec markdown or source → commit.
2. Pre-commit hook: `npm run generate && npm run test && npm run lint`.
3. Push to GitHub → Cloudflare Pages runs `npm run build`.
4. Artifact deployed to custom domain.
5. Service worker `skipWaiting` + `clientsClaim` on new deploy. Users get update after confirming "update available" prompt on next app resume.

### 10.4 Release cadence

As fast as desired. No approval cycles. Spec change + push = live in ~2 min.

## 11. Milestone Roadmap

Effort-based, not calendar-based. Each milestone ships something demonstrable. Variable-burst friendly.

### 11.1 The twelve milestones

| # | Milestone | Effort | Skill acquired | Ships |
|---|---|---|---|---|
| M0 | Foundation: Vite + React + TS + Tailwind + shadcn/ui + vite-plugin-pwa scaffold | 8–10h | PWA manifest, SW registration, Tailwind | Installable "Hello F2" shell |
| M1 | Generator v1 + single-section render | 12–15h | TS generator, react-hook-form, Zod | One F2 section in browser from spec |
| M2 | Autosave + IndexedDB via Dexie | 8–10h | Dexie, debounced effects, persistence | Draft survives reload |
| M3 | Skip logic + multi-section nav + progress | 10–12h | Derived state, navigation | 3 sections with skip logic |
| M4 | Apps Script backend (endpoints, Sheet, HMAC) | 12–15h | Apps Script Web App, request signing | Backend live, curl-testable |
| **M5** | **Sync orchestrator end-to-end** ⭐ | **15–20h** | Async state machines, Background Sync | **First vertical slice. Demo-able.** |
| M6 | Full instrument scaffolding (all 114 items, 35 sections) | 20–25h | Generator robustness, large-form perf | All items fillable |
| M7 | Validation + 20 POST cross-field rules | 15–20h | Zod composition, form-level validation | Full validation |
| M8 | Facility list + enrollment flow | 8–10h | AuthContext, cached lookups | Proper enrollment |
| M9 | i18n — Filipino translations | 10–15h (+20–30h if Carl translates) | react-i18next, label bundles | Bilingual instrument |
| M10 | Admin dashboard (Apps-Script-served HTML) | 10–15h | HtmlService, CSV export | Operations panel |
| M11 | Hardening: E2E, cross-platform QA, iOS polish, a11y, perf | 20–30h | Playwright, accessibility audit | **Production-eligible** |

**Total: 150–200h.**

### 11.2 Promotion checkpoints

| After | Cumulative hrs | Decision available |
|---|---|---|
| **M5** (vertical slice) | ~70–80h | Demo to Dr Myra. Decide: invest further, or declare "proof exists" and keep Plan A focus. |
| **M8** (full instrument + enrollment) | ~110–130h | Pilot decision. Shan can QA; 5–10 HCWs dry-run. |
| **M11** (hardened) | ~150–200h | Production decision. Replace CSPro F2? Run parallel? iPhone-only path? |

### 11.3 Calendar bracketing (intuition, not commitment)

| Burst pace | Monthly hrs | M5 | M8 | M11 |
|---|---|---|---|---|
| Low (~5h/wk avg) | ~20h | ~4 months | ~6 months | ~8–10 months |
| Medium (~10h/wk avg) | ~40h | ~2 months | ~3 months | ~4–5 months |
| High (~15h/wk avg) | ~60h | ~6 weeks | ~2 months | ~3 months |

**Honest expectation:** M5 demo in late June–August 2026. Pilot-ready August–October 2026. Production October 2026–February 2027. F1/F3/F4 CSPro should be deployed well before then.

### 11.4 Skill pay-off curve

- **M0–M3 (~40h):** Concurrent learning of PWA, React, TS, Dexie, generator pattern. Steep, slow.
- **M4–M5 (~30h):** Backend + sync integration. Less new-concept density.
- **M6–M11 (~110h):** Breadth, not depth. Grinding through instrument scope + polish.

By M5 (~70h in), Carl is self-sufficient on React + PWA. Everything after is application.

### 11.5 Ordering rationale

1. **Frontend-first** (M0–M3) is gentler than backend-first — visual progress each session.
2. **HMAC before sync** (M4 before M5) so M5 is not blocked debugging auth.
3. **Enrollment after vertical slice** (M8 after M5) — demo uses stub constants.
4. **i18n late** (M9) — blocked on ASPSI translations anyway.
5. **Admin dashboard late** (M10) — ASPSI uses Sheet directly during early milestones.
6. **Hardening last** (M11) — nothing worth hardening until scope is frozen.

### 11.6 Side-project discipline

- Commit often, push often. GitHub is memory between bursts.
- End every session with a one-line `NEXT.md` note at repo root. Future-self after a 2-week gap will thank you.
- No speculative refactors. Generator and sync orchestrator will feel messy mid-build; hardening (M11) is for cleanup.
- Time-box debugging to 90 min. If stuck, stub + note + move on.

## 12. Defaults and Decisions

| Decision | Value | Rationale |
|---|---|---|
| Local retention after sync | 7 days before purging response body | Verification window; storage hygiene |
| Auto-sync cadence | 5 min foreground; not user-configurable for MVP | Balance freshness vs battery |
| Spec-version strictness | Force update + auto-migrate drafts; flag incompatibles for re-entry | Data integrity over convenience |
| Token security (MVP) | Static API key + HMAC signatures | Adequate for F2 threat model |
| Generator language | TypeScript | Same repo, type-share benefits |
| Frontend host | Cloudflare Pages | Free HTTPS, edge-cached, auto-deploy |
| Backend infra | Apps Script + Google Sheet | Reuses project mailbox infrastructure |
| Admin dashboard style | Apps-Script-served HTML | Functional, not polished |
| i18n languages | English + Filipino | Philippine context; matches CSPro work |

## 13. Open Questions (Deferred to Implementation Planning)

1. **ASPSI-provided Filipino translations, or Carl translates?** Affects M9 effort estimate by +20–30h.
2. **Custom domain choice** — needs ASPSI decision on subdomain branding.
3. **Admin dashboard "nice" upgrade** — defer until after M11 ships.
4. **Per-HCW enrollment tokens** — defer until M11 if threat model demands.
5. **iOS push notifications for deadline reminders** — deferred; revisit post-M11.

## 14. Related Artifacts

- `deliverables/F2/F2-Spec.md` — 114 items verbatim
- `deliverables/F2/F2-Skip-Logic.md`
- `deliverables/F2/F2-Validation.md`
- `deliverables/F2/F2-Cross-Field.md`
- `deliverables/F2/F2-Build-Handoff.md`
- `deliverables/F2/F2-Cover-Block-Rewrite-Draft.md`
- `deliverables/F2/F2-0_Tooling-and-Access-Model-Decision-Memo.md`
- `deliverables/F2/apps-script/` — existing Apps Script bundle (pivots from Google-Forms-generator to PWA ingestion backend)
