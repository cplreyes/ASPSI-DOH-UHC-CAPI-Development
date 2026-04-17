# F2 PWA

Offline-capable self-administered survey for healthcare workers. Plan B to the CSPro F2 instrument. See the design spec at `../2026-04-17-design-spec.md`.

## Prerequisites

- Node 20+
- npm 10+

## Setup

```bash
cd deliverables/F2/PWA/app
npm install
```

## Development

```bash
npm run dev         # Vite dev server at http://localhost:5173
npm run test        # run Vitest once
npm run test:watch  # watch mode
npm run lint        # ESLint
npm run format      # Prettier write
npm run typecheck   # tsc -b (project-references build, noEmit)
```

## Production build

```bash
npm run build       # emits dist/ including sw.js and manifest.webmanifest
npm run preview     # serve dist/ at http://localhost:4173
npm run audit:pwa   # Lighthouse PWA audit against preview (requires preview running)
```

## Assets

- Placeholder icons: `npm run gen:icons` regenerates the solid-teal placeholders from `scripts/gen-icons.mjs`. Real design lands in M11.

## Milestones

See `../2026-04-17-implementation-plan.md` for current M0 plan. Subsequent milestones each get their own plan file at `../YYYY-MM-DD-implementation-plan-MN-<name>.md`.
