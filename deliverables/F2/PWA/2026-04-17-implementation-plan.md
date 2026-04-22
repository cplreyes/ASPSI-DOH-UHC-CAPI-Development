---
title: F2 PWA Implementation Plan — M0 Foundation
date: 2026-04-17
project: ASPSI-DOH-CAPI-CSPro-Development
spec: deliverables/F2/PWA/2026-04-17-design-spec.md
milestone: M0
effort_estimate: 8–10h
status: ready-to-execute
---

# F2 PWA Implementation Plan — M0: Foundation

## Positioning (revised 2026-04-21, Frame #2)

The PWA is the long-term F2 capture target. The Google Forms build at `../apps-script/` is a temporary bridge for **Tranche 2 (Apr 24)** only — smoke test + Shan QA pass, no further investment. M1–M5 is the **Tranche 2→3 critical path** that produces the demo-able vertical slice ASPSI/DOH sees as the "real" F2 instrument. See design spec §1 "Track positioning" for the full framing.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold an installable PWA shell at `deliverables/F2/PWA/app/` that boots, passes Lighthouse "Installable" audit on Chromium, and is ready to receive the F2 generator (M1).

**Architecture:** Vite + React 18 + TypeScript (strict) + Tailwind + shadcn/ui Button + vite-plugin-pwa (Workbox). Single route (`/`) showing "Hello F2" + install CTA. No backend, no IndexedDB, no form logic yet — those land in M1–M5.

**Tech Stack:** Vite 5, React 18, TypeScript 5 (strict), Tailwind CSS 3, shadcn/ui, vite-plugin-pwa, Workbox, Vitest, React Testing Library, ESLint, Prettier, sharp (for placeholder icons).

---

## Scope note

This plan covers **M0 Foundation only** (8–10h of the 150–200h total). M1–M11 are listed in §11 of the design spec; each gets its own plan file written when its predecessor ships. Rationale: solo-dev variable-burst pace benefits from incremental per-milestone plans — future-Carl resuming after a 2-week gap gets a concrete next plan, not a 3000-line monolith. Plans for later milestones are drafted with knowledge of the live code, not speculation.

**Next plan to draft after this ships:** `YYYY-MM-DD-implementation-plan-M1-generator-plus-render.md` (M1 — Generator v1 + single-section render, 12–15h).

---

## Milestone roadmap (from spec §11)

| # | Milestone | Effort | Tranche alignment | Status |
|---|---|---|---|---|
| **M0** | **Foundation** | **8–10h** | T2 complement | **Shipped** (merge `9745b1c`, tag `f2-pwa-m0`) |
| M1 | Generator v1 + single-section render | 12–15h | T2→T3 critical path | Plan drafted (`…-M1-generator-plus-render.md`) |
| M2 | Autosave + IndexedDB via Dexie | 8–10h | T3 critical path | Plan drafted |
| M3 | Skip logic + multi-section nav + progress | 10–12h | T3 critical path | Plan drafted |
| M4 | Apps Script backend (endpoints, Sheet, HMAC) | 12–15h | T3 critical path | Plan drafted |
| M5 | Sync orchestrator end-to-end ⭐ | 15–20h | **T3 vertical-slice demo** | Plan drafted (demo-to-ASPSI checkpoint) |
| M6 | Full instrument scaffolding (124 items, Apr 20 rev) | 20–25h | T3 content completion | Plan drafted |
| M7 | Validation + 20 POST cross-field rules | 15–20h | T3→T4 hardening | Plan drafted |
| M8 | Facility list + enrollment flow | 8–10h | T3→T4 hardening | Plan drafted |
| M9 | i18n — Filipino translations | 10–15h | T3→T4 hardening | Plan drafted |
| M10 | Admin dashboard (HtmlService) | 10–15h | T3→T4 hardening | Plan drafted |
| M11 | Hardening → production-eligible | 20–30h | **T4 production-eligible** | Plan drafted |

---

## File structure at end of M0

```
deliverables/F2/PWA/app/
├── public/
│   └── icons/
│       ├── icon-192.png          # teal placeholder; real design in M11
│       ├── icon-512.png
│       └── icon-maskable.png
├── scripts/
│   └── gen-icons.mjs             # regenerates placeholder icons
├── src/
│   ├── components/
│   │   └── ui/
│   │       └── button.tsx        # shadcn/ui Button (manual copy)
│   ├── lib/
│   │   └── utils.ts              # shadcn cn() helper
│   ├── App.test.tsx              # smoke test
│   ├── App.tsx                   # Hello F2 + Install CTA
│   ├── index.css                 # Tailwind directives + shadcn tokens
│   ├── main.tsx                  # React root + SW registration
│   └── vite-env.d.ts
├── .eslintrc.cjs
├── .gitignore
├── .prettierrc
├── components.json               # shadcn config (manual)
├── index.html
├── NEXT.md                       # one-line forward note for future-Carl
├── package.json
├── postcss.config.js
├── README.md
├── tailwind.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
└── vitest.config.ts
```

---

## Conventions used in this plan

- All `cd` targets use forward-slash paths (Git Bash on Windows handles these).
- All commands are bash (Git Bash on Windows). No PowerShell syntax.
- Working directory for every task (unless noted): `C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app`.
- Commits use Conventional Commits. Prefix: `feat(f2-pwa):` for new features, `test(f2-pwa):` for test-only additions, `chore(f2-pwa):` for config.
- Commit messages include the milestone + task number (e.g., `M0.3`) for traceability.

---

## Task 1: Scaffold Vite + React + TypeScript project

**Files:**
- Create: `deliverables/F2/PWA/app/` (directory)
- Create by Vite template: `package.json`, `tsconfig.json`, `tsconfig.node.json`, `vite.config.ts`, `index.html`, `src/main.tsx`, `src/App.tsx`, `src/App.css`, `src/index.css`, `src/vite-env.d.ts`, `src/assets/react.svg`, `public/vite.svg`, `.gitignore`, `.eslintrc.cjs`, `README.md`

- [ ] **Step 1: Create the app directory**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA"
mkdir -p app
cd app
```

- [ ] **Step 2: Initialize Vite React-TS template into current directory**

```bash
npm create vite@5 . -- --template react-ts
```

When prompted "Current directory is not empty. Continue?" answer `y`. When prompted for package name, accept default.

Expected files created: `package.json`, `index.html`, `src/`, `public/`, `tsconfig*.json`, `vite.config.ts`, `.gitignore`.

- [ ] **Step 3: Install dependencies**

```bash
npm install
```

- [ ] **Step 4: Boot the dev server as a smoke test**

```bash
npm run dev
```

Expected output includes:
```
  VITE v5.x.x  ready in xxx ms
  ➜  Local:   http://localhost:5173/
```

Open `http://localhost:5173/` in Chrome. Confirm the default Vite+React page renders. Press Ctrl-C to stop.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git add deliverables/F2/PWA/app/
git commit -m "feat(f2-pwa): M0.1 scaffold Vite React TS template"
```

---

## Task 2: Configure strict TypeScript

**Files:**
- Modify: `deliverables/F2/PWA/app/tsconfig.json`

- [ ] **Step 1: Overwrite tsconfig.json with strict config**

Replace contents of `deliverables/F2/PWA/app/tsconfig.json` with:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable", "WebWorker"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 2: Wire the `@/` alias into Vite**

Edit `deliverables/F2/PWA/app/vite.config.ts` to import `path` and add `resolve.alias`. Replace contents with:

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

- [ ] **Step 3: Verify typecheck passes**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npx tsc --noEmit
```

Expected: exits 0, no output.

If it fails with unused-var errors in the default `App.tsx`, that's fine — we rewrite App.tsx in Task 6. For now, delete any unused imports from the generated `App.tsx` just enough to make typecheck pass.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git add deliverables/F2/PWA/app/tsconfig.json deliverables/F2/PWA/app/vite.config.ts deliverables/F2/PWA/app/src/App.tsx
git commit -m "feat(f2-pwa): M0.2 strict TS config + @/ alias"
```

---

## Task 3: Install and configure Tailwind CSS

**Files:**
- Create: `deliverables/F2/PWA/app/tailwind.config.ts`, `postcss.config.js`
- Modify: `deliverables/F2/PWA/app/src/index.css`

- [ ] **Step 1: Install Tailwind 3 + PostCSS + Autoprefixer**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npm install -D tailwindcss@3 postcss autoprefixer
```

- [ ] **Step 2: Generate config files**

```bash
npx tailwindcss init -p --ts
```

This creates `tailwind.config.ts` and `postcss.config.js`.

- [ ] **Step 3: Configure Tailwind content paths**

Replace contents of `deliverables/F2/PWA/app/tailwind.config.ts` with:

```ts
import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
} satisfies Config;
```

- [ ] **Step 4: Replace src/index.css with Tailwind directives**

Replace contents of `deliverables/F2/PWA/app/src/index.css` with:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #root {
  height: 100%;
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

Delete `src/App.css` (no longer needed):

```bash
rm src/App.css
```

And remove the `import './App.css'` line from `src/App.tsx` if present.

- [ ] **Step 5: Smoke-test a Tailwind utility**

Temporarily replace `src/App.tsx` contents with:

```tsx
export default function App() {
  return (
    <div className="p-8 text-2xl text-teal-700">Tailwind OK</div>
  );
}
```

Run `npm run dev`, open `http://localhost:5173/`, confirm "Tailwind OK" renders in teal (#0f766e-ish) with padding. Ctrl-C.

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git add deliverables/F2/PWA/app/
git commit -m "feat(f2-pwa): M0.3 Tailwind CSS"
```

---

## Task 4: Add shadcn/ui (manual; Button component only)

**Files:**
- Create: `deliverables/F2/PWA/app/components.json`, `src/lib/utils.ts`, `src/components/ui/button.tsx`
- Modify: `deliverables/F2/PWA/app/tailwind.config.ts`, `src/index.css`

shadcn's CLI is interactive and brittle on Windows-Bash; we install its deps and copy Button manually. This is the documented supported pattern ("copy-paste components, no lock-in").

- [ ] **Step 1: Install runtime dependencies used by shadcn components**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npm install class-variance-authority clsx tailwind-merge lucide-react
npm install -D tailwindcss-animate
```

- [ ] **Step 2: Create components.json (records shadcn settings)**

Create `deliverables/F2/PWA/app/components.json`:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui"
  }
}
```

- [ ] **Step 3: Create src/lib/utils.ts**

Create `deliverables/F2/PWA/app/src/lib/utils.ts`:

```ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 4: Extend Tailwind config with shadcn tokens**

Replace `deliverables/F2/PWA/app/tailwind.config.ts` with:

```ts
import type { Config } from 'tailwindcss';
import tailwindcssAnimate from 'tailwindcss-animate';

export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: { '2xl': '1400px' },
    },
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [tailwindcssAnimate],
} satisfies Config;
```

- [ ] **Step 5: Add shadcn CSS variables to index.css**

Replace `deliverables/F2/PWA/app/src/index.css` with:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --primary: 173 80% 26%;            /* teal-700 for brand */
    --primary-foreground: 0 0% 100%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --ring: 173 80% 26%;
    --radius: 0.5rem;
  }
}

@layer base {
  * { @apply border-border; }
  body { @apply bg-background text-foreground; }
  html, body, #root { height: 100%; }
}
```

- [ ] **Step 6: Create Button component (copy-pasted from shadcn/ui)**

Create `deliverables/F2/PWA/app/src/components/ui/button.tsx`:

```tsx
import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground shadow hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90',
        outline: 'border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-10 rounded-md px-8',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props}
    />
  ),
);
Button.displayName = 'Button';

export { Button, buttonVariants };
```

- [ ] **Step 7: Smoke-test Button rendering**

Replace `src/App.tsx` with:

```tsx
import { Button } from '@/components/ui/button';

export default function App() {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <Button>Shadcn OK</Button>
    </div>
  );
}
```

Run `npm run dev`, open `http://localhost:5173/`, confirm a teal Button reads "Shadcn OK". Ctrl-C.

- [ ] **Step 8: Commit**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git add deliverables/F2/PWA/app/
git commit -m "feat(f2-pwa): M0.4 shadcn/ui + Button component"
```

---

## Task 5: Set up Vitest, ESLint, Prettier

**Files:**
- Create: `deliverables/F2/PWA/app/vitest.config.ts`, `src/test-setup.ts`, `.prettierrc`, `.prettierignore`
- Modify: `deliverables/F2/PWA/app/package.json`, `tsconfig.json`, `.eslintrc.cjs`

- [ ] **Step 1: Install test + lint + format deps**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npm install -D vitest @vitest/ui jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event prettier eslint-config-prettier
```

- [ ] **Step 2: Create vitest.config.ts**

Create `deliverables/F2/PWA/app/vitest.config.ts`:

```ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    globals: true,
    css: false,
  },
});
```

- [ ] **Step 3: Create src/test-setup.ts**

Create `deliverables/F2/PWA/app/src/test-setup.ts`:

```ts
import '@testing-library/jest-dom/vitest';
```

- [ ] **Step 4: Add Vitest types to tsconfig**

In `deliverables/F2/PWA/app/tsconfig.json`, add `"vitest/globals"` to the `types` array. If no `types` key exists, add under `compilerOptions`:

```json
"types": ["vitest/globals", "@testing-library/jest-dom"]
```

- [ ] **Step 5: Create Prettier config**

Create `deliverables/F2/PWA/app/.prettierrc`:

```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2,
  "arrowParens": "always"
}
```

Create `deliverables/F2/PWA/app/.prettierignore`:

```
dist/
dev-dist/
node_modules/
public/icons/
```

- [ ] **Step 6: Extend ESLint config with Prettier interop**

Open `deliverables/F2/PWA/app/.eslintrc.cjs`. Add `'prettier'` as the last entry of the `extends` array so Prettier wins any style conflicts. The file should end up looking approximately like:

```js
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    'prettier',
  ],
  ignorePatterns: ['dist', 'dev-dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
  },
};
```

- [ ] **Step 7: Add npm scripts**

In `deliverables/F2/PWA/app/package.json`, replace the `"scripts"` object with:

```json
"scripts": {
  "dev": "vite",
  "build": "tsc --noEmit && vite build",
  "preview": "vite preview",
  "test": "vitest run",
  "test:watch": "vitest",
  "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
  "format": "prettier --write .",
  "format:check": "prettier --check .",
  "typecheck": "tsc --noEmit"
}
```

- [ ] **Step 8: Run format + lint + typecheck + test scripts to verify wiring**

```bash
npm run format
npm run typecheck
npm run lint
npm run test
```

Expected:
- `format`: writes formatting, exits 0
- `typecheck`: exits 0, no output
- `lint`: exits 0 (there may be warnings but no errors)
- `test`: exits 0 with "No test files found" (we add the first test in Task 6)

- [ ] **Step 9: Commit**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git add deliverables/F2/PWA/app/
git commit -m "chore(f2-pwa): M0.5 Vitest + ESLint + Prettier tooling"
```

---

## Task 6: First test — App renders "Hello F2"

**Files:**
- Create: `deliverables/F2/PWA/app/src/App.test.tsx`
- Modify: `deliverables/F2/PWA/app/src/App.tsx`

- [ ] **Step 1: Write the failing test**

Create `deliverables/F2/PWA/app/src/App.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders the "Hello F2" heading', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /hello f2/i })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npm run test
```

Expected: FAIL with "Unable to find an accessible element with the role 'heading'" (because App.tsx currently renders only the shadcn Button from Task 4).

- [ ] **Step 3: Implement the minimal App to make the test pass**

Replace `deliverables/F2/PWA/app/src/App.tsx` with:

```tsx
import { Button } from '@/components/ui/button';

export default function App() {
  return (
    <main className="flex h-full flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-semibold tracking-tight">Hello F2</h1>
      <p className="text-muted-foreground">
        Healthcare Worker Survey — offline-capable PWA
      </p>
      <Button>Install (coming in M0.10)</Button>
    </main>
  );
}
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
npm run test
```

Expected: PASS, 1 passed.

- [ ] **Step 5: Visual smoke test**

```bash
npm run dev
```

Open `http://localhost:5173/`, confirm "Hello F2" heading + teal Button visible. Ctrl-C.

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git add deliverables/F2/PWA/app/src/App.tsx deliverables/F2/PWA/app/src/App.test.tsx
git commit -m "test(f2-pwa): M0.6 App renders Hello F2"
```

---

## Task 7: Install vite-plugin-pwa and configure manifest

**Files:**
- Modify: `deliverables/F2/PWA/app/vite.config.ts`
- Modify: `deliverables/F2/PWA/app/src/main.tsx`

- [ ] **Step 1: Install vite-plugin-pwa**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npm install -D vite-plugin-pwa
```

- [ ] **Step 2: Configure VitePWA in vite.config.ts**

Replace `deliverables/F2/PWA/app/vite.config.ts` with:

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import path from 'node:path';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'prompt',
      injectRegister: false,
      includeAssets: ['icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-maskable.png'],
      manifest: {
        name: 'F2 — Healthcare Worker Survey',
        short_name: 'F2 Survey',
        description: 'Offline-capable self-administered survey for healthcare workers.',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        orientation: 'portrait',
        theme_color: '#0f766e',
        background_color: '#ffffff',
        lang: 'en',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/icon-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,webmanifest}'],
        navigateFallback: '/index.html',
        cleanupOutdatedCaches: true,
      },
      devOptions: {
        enabled: false,
      },
    }),
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
});
```

- [ ] **Step 3: Add SW registration stub to main.tsx**

Replace `deliverables/F2/PWA/app/src/main.tsx` with:

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { registerSW } from 'virtual:pwa-register';

// Prompt-style SW registration. Full update UX lands in M11.
registerSW({
  onNeedRefresh() {
    console.info('[PWA] New content available. Reload to update.');
  },
  onOfflineReady() {
    console.info('[PWA] Ready to work offline.');
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 4: Add virtual module types to vite-env.d.ts**

Replace `deliverables/F2/PWA/app/src/vite-env.d.ts` with:

```ts
/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />
```

- [ ] **Step 5: Typecheck**

```bash
npm run typecheck
```

Expected: exits 0. (Icons don't exist yet — that's Task 8. Build will fail with missing icons but typecheck won't.)

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git add deliverables/F2/PWA/app/vite.config.ts deliverables/F2/PWA/app/src/main.tsx deliverables/F2/PWA/app/src/vite-env.d.ts deliverables/F2/PWA/app/package.json deliverables/F2/PWA/app/package-lock.json
git commit -m "feat(f2-pwa): M0.7 vite-plugin-pwa + manifest"
```

---

## Task 8: Generate placeholder icons

**Files:**
- Create: `deliverables/F2/PWA/app/scripts/gen-icons.mjs`
- Create: `deliverables/F2/PWA/app/public/icons/icon-192.png`, `icon-512.png`, `icon-maskable.png`

Real icon design happens in M11. For M0 we ship solid teal (#0f766e) squares so Lighthouse accepts the PWA as installable.

- [ ] **Step 1: Install sharp as a dev dependency**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npm install -D sharp
```

- [ ] **Step 2: Create the icon generator script**

Create `deliverables/F2/PWA/app/scripts/gen-icons.mjs`:

```js
import sharp from 'sharp';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(__dirname, '../public/icons');
mkdirSync(outDir, { recursive: true });

const bg = { r: 15, g: 118, b: 110, alpha: 1 }; // teal-700 #0f766e

async function solid(size, filename) {
  await sharp({
    create: { width: size, height: size, channels: 4, background: bg },
  })
    .png()
    .toFile(path.join(outDir, filename));
  console.log(`  wrote ${filename} (${size}x${size})`);
}

await solid(192, 'icon-192.png');
await solid(512, 'icon-512.png');
await solid(512, 'icon-maskable.png');
console.log('Icons generated.');
```

- [ ] **Step 3: Add npm script and run it**

In `deliverables/F2/PWA/app/package.json`, add to the `"scripts"` object:

```json
"gen:icons": "node scripts/gen-icons.mjs"
```

Then:

```bash
npm run gen:icons
```

Expected output:
```
  wrote icon-192.png (192x192)
  wrote icon-512.png (512x512)
  wrote icon-maskable.png (512x512)
Icons generated.
```

- [ ] **Step 4: Verify files exist**

```bash
ls -la public/icons/
```

Expected: three PNG files, roughly 400–2000 bytes each.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git add deliverables/F2/PWA/app/scripts/gen-icons.mjs deliverables/F2/PWA/app/public/icons/ deliverables/F2/PWA/app/package.json deliverables/F2/PWA/app/package-lock.json
git commit -m "feat(f2-pwa): M0.8 placeholder PWA icons"
```

---

## Task 9: Build & verify service worker emits

**Files:**
- No source changes; this task verifies that the configured PWA toolchain produces `sw.js`, `manifest.webmanifest`, and workbox precache entries on build.

- [ ] **Step 1: Run the production build**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npm run build
```

Expected tail of output includes a `PWA v0.x.x` section listing precache entries and emitting `sw.js` + `workbox-*.js`.

- [ ] **Step 2: Inspect build artifacts**

```bash
ls -la dist/
```

Expected to include: `index.html`, `manifest.webmanifest`, `registerSW.js`, `sw.js`, `workbox-<hash>.js`, `icons/`, `assets/`.

- [ ] **Step 3: Preview the production build**

```bash
npm run preview
```

Open `http://localhost:4173/` in Chrome.

In DevTools:
- **Application → Manifest**: confirm name="F2 — Healthcare Worker Survey", three icons listed, theme color #0f766e.
- **Application → Service Workers**: confirm one SW registered, status "activated and is running".

Ctrl-C to stop.

- [ ] **Step 4: Commit (no source changes — skip if nothing to commit)**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git status
```

If clean, this task is verification-only — no commit needed. If any lockfile drift, commit with:

```bash
git add -A deliverables/F2/PWA/app/
git commit -m "chore(f2-pwa): M0.9 verify SW build artifacts"
```

---

## Task 10: beforeinstallprompt handler + visible install CTA

**Files:**
- Create: `deliverables/F2/PWA/app/src/lib/install-prompt.ts`, `src/lib/install-prompt.test.ts`
- Modify: `deliverables/F2/PWA/app/src/App.tsx`, `src/App.test.tsx`

Android / Chromium fires `beforeinstallprompt`. iOS does not (spec §7.4) — we ship the Install button only when the event fires; iOS tutorial UI is M11.

- [ ] **Step 1: Write the failing test for the install-prompt hook**

Create `deliverables/F2/PWA/app/src/lib/install-prompt.test.ts`:

```ts
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useInstallPrompt } from './install-prompt';

describe('useInstallPrompt', () => {
  let listeners: Record<string, EventListener[]> = {};
  const originalAdd = window.addEventListener.bind(window);
  const originalRemove = window.removeEventListener.bind(window);

  beforeEach(() => {
    listeners = {};
    window.addEventListener = vi.fn((type: string, cb: EventListener) => {
      (listeners[type] ??= []).push(cb);
    }) as typeof window.addEventListener;
    window.removeEventListener = vi.fn((type: string, cb: EventListener) => {
      listeners[type] = (listeners[type] ?? []).filter((c) => c !== cb);
    }) as typeof window.removeEventListener;
  });

  afterEach(() => {
    window.addEventListener = originalAdd;
    window.removeEventListener = originalRemove;
  });

  it('initially reports not installable', () => {
    const { result } = renderHook(() => useInstallPrompt());
    expect(result.current.canInstall).toBe(false);
  });

  it('becomes installable when beforeinstallprompt fires', () => {
    const { result } = renderHook(() => useInstallPrompt());
    const evt = Object.assign(new Event('beforeinstallprompt'), {
      prompt: vi.fn().mockResolvedValue({ outcome: 'accepted' }),
      userChoice: Promise.resolve({ outcome: 'accepted', platform: 'web' }),
      preventDefault: vi.fn(),
    });
    act(() => {
      listeners['beforeinstallprompt']?.forEach((cb) => cb(evt));
    });
    expect(result.current.canInstall).toBe(true);
  });

  it('calls prompt() when install() is invoked', async () => {
    const { result } = renderHook(() => useInstallPrompt());
    const prompt = vi.fn().mockResolvedValue({ outcome: 'accepted' });
    const evt = Object.assign(new Event('beforeinstallprompt'), {
      prompt,
      userChoice: Promise.resolve({ outcome: 'accepted', platform: 'web' }),
      preventDefault: vi.fn(),
    });
    act(() => {
      listeners['beforeinstallprompt']?.forEach((cb) => cb(evt));
    });
    await act(async () => {
      await result.current.install();
    });
    expect(prompt).toHaveBeenCalledOnce();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npm run test
```

Expected: FAIL — "Cannot find module './install-prompt'".

- [ ] **Step 3: Implement the hook**

Create `deliverables/F2/PWA/app/src/lib/install-prompt.ts`:

```ts
import { useCallback, useEffect, useState } from 'react';

interface BeforeInstallPromptEvent extends Event {
  readonly userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
  prompt(): Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

interface InstallPromptState {
  canInstall: boolean;
  install: () => Promise<void>;
}

export function useInstallPrompt(): InstallPromptState {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
    };
    window.addEventListener('beforeinstallprompt', handler);
    const installed = () => setDeferred(null);
    window.addEventListener('appinstalled', installed);
    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      window.removeEventListener('appinstalled', installed);
    };
  }, []);

  const install = useCallback(async () => {
    if (!deferred) return;
    await deferred.prompt();
    setDeferred(null);
  }, [deferred]);

  return { canInstall: deferred !== null, install };
}
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
npm run test
```

Expected: PASS — 4 tests passing (1 App + 3 install-prompt).

- [ ] **Step 5: Wire the hook into App.tsx**

Replace `deliverables/F2/PWA/app/src/App.tsx` with:

```tsx
import { Button } from '@/components/ui/button';
import { useInstallPrompt } from '@/lib/install-prompt';

export default function App() {
  const { canInstall, install } = useInstallPrompt();

  return (
    <main className="flex h-full flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-semibold tracking-tight">Hello F2</h1>
      <p className="text-muted-foreground">
        Healthcare Worker Survey — offline-capable PWA
      </p>
      {canInstall ? (
        <Button onClick={install}>Install F2</Button>
      ) : (
        <p className="text-sm text-muted-foreground">
          Open in Chrome or install via your browser menu (iOS: Share → Add to Home Screen)
        </p>
      )}
    </main>
  );
}
```

- [ ] **Step 6: Update App smoke test to tolerate either CTA state**

Replace `deliverables/F2/PWA/app/src/App.test.tsx` with:

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders the Hello F2 heading', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /hello f2/i })).toBeInTheDocument();
  });

  it('renders the iOS fallback copy when beforeinstallprompt has not fired', () => {
    render(<App />);
    expect(screen.getByText(/add to home screen/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 7: Run the full test suite**

```bash
npm run test
```

Expected: PASS — 5 tests passing.

- [ ] **Step 8: Commit**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git add deliverables/F2/PWA/app/
git commit -m "feat(f2-pwa): M0.10 install prompt hook + CTA"
```

---

## Task 11: Lighthouse PWA installability audit

**Files:**
- Modify: `deliverables/F2/PWA/app/package.json`

Lighthouse's "Installable" check verifies: manifest has name + icons + start_url + display, SW is registered, served over HTTPS (or localhost). We run it against `npm run preview`.

- [ ] **Step 1: Install Lighthouse CLI**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npm install -D lighthouse
```

- [ ] **Step 2: Add audit script to package.json**

Add to the `"scripts"` object in `deliverables/F2/PWA/app/package.json`:

```json
"audit:pwa": "lighthouse http://localhost:4173 --only-categories=pwa --chrome-flags=\"--headless=new\" --output=json --output-path=./lighthouse-pwa.json --quiet"
```

- [ ] **Step 3: Build and preview, then audit**

In terminal 1:
```bash
npm run build
npm run preview
```
(leave running)

In terminal 2:
```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npm run audit:pwa
```

Expected: a `lighthouse-pwa.json` file is created, Lighthouse exits 0.

- [ ] **Step 4: Assert the installable audit passed**

```bash
node -e "const r = require('./lighthouse-pwa.json'); const a = r.audits['installable-manifest']; if (a.score !== 1) { console.error('FAIL', a.title, a.explanation ?? a.description); process.exit(1); } console.log('PASS:', a.title);"
```

Expected output: `PASS: Web app manifest and service worker meet the installability requirements`.

If it fails, common causes:
- Icons missing → rerun Task 8.
- SW not registered → verify `dist/sw.js` exists; rerun `npm run build`.
- Preview server not running → restart `npm run preview` in terminal 1.

Stop preview server in terminal 1 (Ctrl-C).

- [ ] **Step 5: Ignore the audit output in git**

Append to `deliverables/F2/PWA/app/.gitignore`:

```
lighthouse-pwa.json
```

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git add deliverables/F2/PWA/app/package.json deliverables/F2/PWA/app/package-lock.json deliverables/F2/PWA/app/.gitignore
git commit -m "chore(f2-pwa): M0.11 Lighthouse PWA audit script"
```

---

## Task 12: README, NEXT.md, and M0 milestone tag

**Files:**
- Create: `deliverables/F2/PWA/app/README.md` (overwrite Vite default)
- Create: `deliverables/F2/PWA/app/NEXT.md`

- [ ] **Step 1: Write README.md**

Replace `deliverables/F2/PWA/app/README.md` with:

```markdown
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
npm run typecheck   # tsc --noEmit
```

## Production build

```bash
npm run build       # emits dist/ including sw.js and manifest.webmanifest
npm run preview     # serve dist/ at http://localhost:4173
npm run audit:pwa   # Lighthouse PWA audit against preview
```

## Assets

- Placeholder icons: `npm run gen:icons` regenerates the solid-teal placeholders from `scripts/gen-icons.mjs`. Real design lands in M11.

## Milestones

See `../2026-04-17-implementation-plan.md` for current M0 plan. Subsequent milestones each get their own plan file at `../YYYY-MM-DD-implementation-plan-MN-<name>.md`.
```

- [ ] **Step 2: Write NEXT.md**

Create `deliverables/F2/PWA/app/NEXT.md`:

```markdown
# Next step (future-Carl)

**Last milestone shipped:** M0 — Foundation (installable PWA shell).

**Next milestone:** M1 — Generator v1 + single-section render (12–15h).

**Before starting M1:**
1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §§5.2, 6, 11.1 (M1 row) to draft the M1 plan file.
2. Target: parse one F2 section from `../../F2-Spec.md` into generated TS + Zod, render it via react-hook-form, validate on submit.
3. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M1-generator-plus-render.md`.

**When picking this back up after a gap:**
- Run `npm install` first.
- Run `npm run test && npm run typecheck && npm run build` to confirm M0 still green.
- Open `../2026-04-17-design-spec.md` §6 (Generator Pattern) to re-orient.
```

- [ ] **Step 3: Run a final sanity check — all scripts green**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app"
npm run format:check
npm run typecheck
npm run lint
npm run test
npm run build
```

All five commands must exit 0.

- [ ] **Step 4: Commit the docs**

```bash
cd "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development"
git add deliverables/F2/PWA/app/README.md deliverables/F2/PWA/app/NEXT.md
git commit -m "docs(f2-pwa): M0.12 README + NEXT forward-note"
```

- [ ] **Step 5: Tag the M0 milestone**

```bash
git tag -a f2-pwa-m0 -m "F2 PWA M0 — Foundation complete (installable shell)"
```

- [ ] **Step 6: Demo checklist (manual, ~5 min)**

Manually verify the milestone acceptance criteria before declaring M0 done:

1. `npm run dev` → `http://localhost:5173/` shows "Hello F2" heading + either an Install button (Chrome) or the iOS fallback copy.
2. `npm run build && npm run preview` → `http://localhost:4173/` renders identically.
3. Chrome DevTools → Application → Manifest: name, short_name, icons, theme_color all populated from spec §7.5.
4. Chrome DevTools → Application → Service Workers: one SW registered, status "activated and is running".
5. `npm run audit:pwa` → `installable-manifest` audit scores 1.
6. Chrome menu → "Install F2 Survey": installs to desktop/home-screen; launches in standalone mode (no browser chrome); shows "Hello F2".

If all six pass, M0 is demonstrably done.

---

## M0 Acceptance Criteria

M0 is complete when every item below is true:

- [ ] `npm run build` exits 0 and emits `dist/sw.js` + `dist/manifest.webmanifest`.
- [ ] `npm run test` passes (5 tests: 2 App + 3 useInstallPrompt).
- [ ] `npm run typecheck` exits 0 under strict TS.
- [ ] `npm run lint` exits 0 with `--max-warnings 0`.
- [ ] Lighthouse `installable-manifest` audit scores 1.
- [ ] App installs to desktop and home-screen on a Chromium browser.
- [ ] App launches standalone and renders "Hello F2" offline (disable network in DevTools → reload).
- [ ] Tag `f2-pwa-m0` exists in git.
- [ ] `NEXT.md` points forward to M1 planning.

---

## What this plan intentionally does NOT do

Per spec §11.5 (Ordering Rationale) and §11.6 (Side-project Discipline):

- **No routing.** Single route `/`. react-router lands in M3 when multi-section navigation arrives.
- **No Dexie / IndexedDB.** Storage lands in M2.
- **No backend.** Apps Script lands in M4; sync in M5.
- **No real icons.** Placeholder teal squares; real branded icons in M11.
- **No generator.** Pure hand-written "Hello F2" shell; generator pipeline is M1.
- **No i18n.** English only; Filipino bundles in M9.
- **No admin dashboard.** M10.
- **No hardening, no a11y audit, no perf pass.** M11.

Keeping M0 small is the point. Every one of the above additions is someone else's milestone.

---

## References

- Design spec: `deliverables/F2/PWA/2026-04-17-design-spec.md`
- Milestone table: spec §11.1
- Install experience notes: spec §7.4
- Manifest fields: spec §7.5
- Scrum discipline: `scrum/sprint-current.md`, `scrum/epics/epic-00-project-management.md`
- vite-plugin-pwa docs: https://vite-pwa-org.netlify.app/
- shadcn/ui Button source: https://ui.shadcn.com/docs/components/button
- Lighthouse PWA audits: https://developer.chrome.com/docs/lighthouse/pwa/
