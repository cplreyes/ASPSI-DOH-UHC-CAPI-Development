# Next step (future-Carl)

**Last milestone shipped:** M9 — i18n / Filipino. react-i18next wired in, LocaleProvider persists locale to `localStorage` key `f2_locale`, header LanguageSwitcher toggles EN/FIL. Generator now emits `LocalizedString = { en, fil }` for every label/title/help/preamble/choice/subField; `localized(label, locale)` resolves at render time with English fallback. All chrome strings (header, EnrollmentScreen, Navigator, ReviewSection, Section, SyncPage, SyncButton, PendingCount) routed through `t()`. Cross-field warning messages converted to interpolated i18n keys (`{ key, values }`). **Filipino strings are placeholder-equal-to-English — drop in real translations by editing `app/src/i18n/locales/fil.ts` (chrome) and adding a `--with-translations spec/F2-Spec.fil.md` overlay to the generator (instrument labels) when ASPSI delivers.** Tests + typecheck + build clean.

**Next milestone:** M10 — Admin dashboard (Apps-Script-served HTML). 10–15h per spec §11.1.

**Before starting M10:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §4.7 (Admin dashboard) and §11.1 row M10.
2. Confirm the existing `backend/src/Handlers.js` exposes the data the dashboard needs (status counts, recent submissions, kill-switch toggle, broadcast_message editor). If not, the plan also needs backend additions.
3. Target: HtmlService template served from a new `?action=admin` route, basic-auth gated by a separate ADMIN_SECRET env var. CSV export. Status counters live-queried via the existing endpoints.
4. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M10-admin-dashboard.md`.

**M9 follow-ups (slot in when ASPSI delivers):**

- **Filipino instrument translations.** Add `spec/F2-Spec.fil.md` (parallel structure to `spec/F2-Spec.md`). Extend `app/scripts/lib/parse-spec.ts` to read it as an overlay (when present, populate `fil` from the overlay instead of mirroring `en`). Regenerate `items.ts`. Estimated 3–5h.
- **Filipino chrome translations.** Replace placeholder values in `app/src/i18n/locales/fil.ts` with the real translations. Estimated 1–2h.
- **Browser language auto-detection on first load.** Currently defaults to `'en'` if nothing is in `localStorage`. Optional: use `i18next-browser-languagedetector` to auto-pick `fil` for users whose browser locale is `fil-PH`. Estimated 30 minutes.

**M8 technical debt still outstanding:**

- **`facility_has_bucas` / `facility_has_gamot` flags** — backend schema additions still pending; needed before FAC-01..07 cross-field rules can wire up.
- **`response_source` per-respondent capture** — currently hardcoded `source: 'pwa'`. SRC-01..03 cross-field rules want this.
- **Sync-page "change enrollment" affordance** — `unenroll()` exists but no UI calls it.
- **Auto-refresh facilities on app open** — currently only the explicit Refresh button on EnrollmentScreen calls it.
- **`/config` endpoint** — backend has it; PWA never calls it. M11 hardening should poll on app open.

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build` — confirm M9 still green.
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build` — confirm M4 still green.
- Copy `.env.example` → `.env.local` and fill both vars from the live Apps Script deployment.
- `npm run dev`, walk through: enrollment screen → fill form (toggle EN/FIL in header) → review → submit → sync.
- Open `../2026-04-17-design-spec.md` §4.7 + §11.1 row M10 to re-orient for the admin dashboard.
