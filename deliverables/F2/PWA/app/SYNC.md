# F2 PWA — Sync operator reference

## Configure

1. Deploy the backend per `../backend/README.md` §"One-time deploy".
2. `cp .env.example .env.local` in `app/`.
3. Fill in:
   - `VITE_F2_BACKEND_URL` — the Web App `/exec` URL.
   - `VITE_F2_HMAC_SECRET` — the 64-char hex secret from backend ScriptProperties.
4. `npm run build && npm run preview` — verify the PWA loads with sync enabled.

## How sync runs

The orchestrator (`src/lib/sync-orchestrator.ts`) triggers on:

1. Window `online` event
2. Every 5 minutes while the app is open
3. Immediately after the user submits a form
4. Manual click of the "Sync now" button

Reentrant calls are coalesced — only one `runSync()` executes at a time.

## State machine

```
pending_sync ──▶ syncing ──▶ synced          (200 accepted / duplicate)
    ▲              │    ▶    rejected         (E_VALIDATION / E_PAYLOAD_INVALID / E_SPEC_TOO_OLD)
    │              │    ▶    retry_scheduled  (network / 5xx / missing per-item result)
    │                         │
    └──────── backoff ────────┘   30s → 2m → 10m → 1h (capped)
```

Rows stuck in `syncing` for >10 minutes (crash mid-flight) are auto-reclaimed to `pending_sync` on the next run.

## Spec-too-old handling

If any batch item returns `E_SPEC_TOO_OLD`, `config.update_available` is set to `true` in IndexedDB. UI surfacing of the "Update available" banner is deferred to M6 (spec version gate).

## Debugging

Open the browser devtools → Application → IndexedDB → `f2_pwa` → `submissions`. Each row shows `status`, `retry_count`, `next_retry_at`, and `last_error`. Clear-and-replay by right-clicking a row and editing back to `pending_sync`.

## Deferred to later milestones

- Live-reload of the PWA when `update_available=true` — M6 or later.
- Per-item partial retry (currently the whole batch shares a transport-failure fate) — M10/M11 if observed as pain.
- Audit events (`install`, `sync_run_summary`) to `/audit` endpoint — M6 alongside facility enrollment.
