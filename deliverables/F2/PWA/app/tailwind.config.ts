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
        // Alpha-aware HSL slot syntax. Lets utilities like `bg-primary/10`,
        // `border-l-warning`, `bg-destructive/10` resolve through --alpha-value.
        border: 'hsl(var(--border) / <alpha-value>)',
        input: 'hsl(var(--input) / <alpha-value>)',
        ring: 'hsl(var(--ring) / <alpha-value>)',
        background: 'hsl(var(--background) / <alpha-value>)',
        foreground: 'hsl(var(--foreground) / <alpha-value>)',
        primary: {
          DEFAULT: 'hsl(var(--primary) / <alpha-value>)',
          foreground: 'hsl(var(--primary-foreground) / <alpha-value>)',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary) / <alpha-value>)',
          foreground: 'hsl(var(--secondary-foreground) / <alpha-value>)',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive) / <alpha-value>)',
          foreground: 'hsl(var(--destructive-foreground) / <alpha-value>)',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted) / <alpha-value>)',
          foreground: 'hsl(var(--muted-foreground) / <alpha-value>)',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent) / <alpha-value>)',
          foreground: 'hsl(var(--accent-foreground) / <alpha-value>)',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning) / <alpha-value>)',
          foreground: 'hsl(var(--warning-foreground) / <alpha-value>)',
        },
        // Verde Manual aliases. The CSS vars in index.css are documented with
        // these names ("paper", "ink", "hairline", "signal") and the admin
        // portal code consumes them via `bg-paper`, `text-ink`,
        // `border-hairline`, `border-signal`, `text-error` etc. Without
        // these aliases those classes silently drop and modals render
        // background-less (surfaced during AP0 dogfood — modal panels
        // appeared transparent because bg-paper resolved to nothing).
        paper: 'hsl(var(--background) / <alpha-value>)',
        ink: 'hsl(var(--foreground) / <alpha-value>)',
        hairline: 'hsl(var(--border) / <alpha-value>)',
        signal: 'hsl(var(--primary) / <alpha-value>)',
        error: 'hsl(var(--destructive) / <alpha-value>)',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        // Verde Manual. See DESIGN.md.
        // `serif` overrides the Tailwind default so `font-serif` resolves to Newsreader.
        serif: ['Newsreader', 'Georgia', '"Times New Roman"', 'serif'],
        sans: [
          'Public Sans',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
        mono: ['"JetBrains Mono"', '"SF Mono"', 'Menlo', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [tailwindcssAnimate],
} satisfies Config;
