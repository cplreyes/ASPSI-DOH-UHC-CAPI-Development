/**
 * F2 Admin Portal — left-sidebar layout (industry-standard shape).
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.14, Step 4)
 * Design: deliverables/F2/PWA/app/DESIGN.md — Verde Manual.
 *
 * Refined 2026-05-04 to follow modern admin-console patterns (Linear / Vercel
 * / Stripe / Posthog / ServiceNow Lightning):
 *
 *   - Icons before labels — visual scan + 44×44 touch targets (closes FX-017
 *     in this surface).
 *   - Section grouping — OPERATE / CONFIGURE / HELP — with mono eyebrow
 *     dividers between groups; matches CSWeb's mental model + makes role-
 *     gating visually contiguous when we ship the FX-002 perm-aware filter.
 *   - User profile at sidebar bottom — industry-standard slot. Frees the
 *     content area's top of the previous user/sign-out strip; the section
 *     heading ("Section / Data Dashboard") already identifies the page.
 *   - Active state stacks three signals: signal-colored left edge, secondary
 *     bg tint, bold ink text. Strong-enough affordance that a quick glance
 *     locates the current page even on a busy sidebar.
 *   - Hover state adds a subtle bg-tint without changing the layout — no
 *     content shift, common pattern.
 *
 * Verde Manual styling: tokens only (paper / ink / signal / secondary /
 * hairline / muted-foreground), no raw Tailwind colors per memory
 * `project_f2_verde_manual_prod.md`.
 *
 * Mobile/narrow viewport (<768px): sidebar collapses to a horizontal nav
 * strip at the top to avoid cramming the 7 items into a narrow column on
 * phones. The strip omits icons (label-only) for compactness.
 *
 * Role-aware filtering still TBD (FX-002 follow-up). Today every link is
 * visible to every authenticated user; Worker enforces 403 on actual access.
 */
import { type ReactNode, type SVGProps } from 'react';
import { Link, useRouter } from './lib/pages-router';
import { useAdminAuth } from './lib/auth-context';

interface LayoutProps {
  children: ReactNode;
}

interface NavItemSpec {
  to: string;
  label: string;
  description: string;
  icon: (props: SVGProps<SVGSVGElement>) => JSX.Element;
}

interface NavGroup {
  title: string;
  items: NavItemSpec[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Operate',
    items: [
      {
        to: '/admin/data',
        label: 'Data',
        description: 'Submissions, audit log, DLQ, HCWs registry — day-to-day operations.',
        icon: IconTable,
      },
      {
        to: '/admin/report',
        label: 'Reports',
        description: 'Coverage by region/province/facility + geographic Map Report.',
        icon: IconChart,
      },
      {
        to: '/admin/encode',
        label: 'Encode',
        description:
          'Paper-response transcription flow. Used when an HCW completed the survey on paper.',
        icon: IconEdit,
      },
    ],
  },
  {
    title: 'Configure',
    items: [
      {
        to: '/admin/apps',
        label: 'Apps & Settings',
        description:
          'Build versions, file uploads, scheduled break-out exports, Apps Script quota.',
        icon: IconSliders,
      },
      {
        to: '/admin/users',
        label: 'Users',
        description: 'CRUD for ops staff accounts. Bulk-import for new cohorts.',
        icon: IconUsers,
      },
      {
        to: '/admin/roles',
        label: 'Roles',
        description: 'Permission matrix editor. Built-in + custom roles.',
        icon: IconShield,
      },
    ],
  },
  {
    title: 'Help',
    items: [
      {
        to: '/admin/help',
        label: 'Help',
        description: 'Operator guide — what each tab does, common workflows, glossary.',
        icon: IconBook,
      },
    ],
  },
];

const FLAT_NAV: NavItemSpec[] = NAV_GROUPS.flatMap((g) => g.items);

export function Layout({ children }: LayoutProps): JSX.Element {
  const { username, role, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();

  const onLogout = () => {
    clearAuth();
    navigate('/admin/login');
  };

  const initial = (username ?? '—').slice(0, 1).toUpperCase();

  return (
    <div className="flex h-screen-dvh w-full flex-col overflow-hidden md:flex-row">
      {/* Desktop / tablet sidebar (≥md) — fixed; doesn't scroll with the
          content area. The nav region scrolls internally only if it overflows
          (rare; future-proofing for more items / role-based subgroups). The
          brand area at top + the user/sign-out footer stay anchored. Outer
          container flips between column (mobile: header→content top-down) and
          row (desktop: sidebar→content side-by-side); both directions hold
          h-screen + overflow-hidden so only the inner main element scrolls. */}
      <aside
        className="hidden h-full w-56 shrink-0 flex-col border-r border-hairline bg-paper md:flex"
        aria-label="Primary"
      >
        <Link to="/admin/data" className="flex flex-col gap-0 px-5 py-5">
          <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            F2 Admin
          </span>
          <span className="font-serif text-lg font-medium tracking-tight">F2 PWA Portal</span>
        </Link>

        <nav className="flex flex-1 flex-col gap-4 overflow-y-auto py-2">
          {NAV_GROUPS.map((group) => (
            <div key={group.title} className="flex flex-col">
              <p className="px-5 pb-1 pt-2 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                {group.title}
              </p>
              {group.items.map((item) => (
                <SidebarLink key={item.to} item={item} />
              ))}
            </div>
          ))}
        </nav>

        {/* Sidebar footer: user profile + sign out + version */}
        <div className="flex flex-col gap-3 border-t border-hairline px-5 py-4">
          <div className="flex items-center gap-3">
            <div
              aria-hidden="true"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-hairline bg-secondary/40 font-mono text-sm text-ink"
            >
              {initial}
            </div>
            <div className="flex min-w-0 flex-col">
              <p className="truncate text-sm font-medium text-ink">{username ?? '—'}</p>
              <p className="truncate font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                {role ?? '—'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onLogout}
            className="flex h-9 w-full items-center justify-center border border-hairline font-mono text-xs uppercase tracking-wider text-muted-foreground hover:bg-secondary/40 hover:text-ink"
          >
            Sign out
          </button>
          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
            v0.1.0-staging
          </p>
        </div>
      </aside>

      {/* Mobile / narrow viewport (<md): horizontal nav strip stays fixed at
          top while the content scrolls below. Header is `shrink-0` so it
          never compresses; main owns the overflow. Hidden on desktop — the
          desktop sidebar above takes its place. */}
      <header className="flex shrink-0 flex-col gap-2 border-b border-hairline px-4 py-3 md:hidden">
        <div className="flex items-baseline justify-between">
          <Link to="/admin/data" className="flex flex-col">
            <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              F2 Admin
            </span>
            <span className="font-serif text-base font-medium tracking-tight">F2 PWA Portal</span>
          </Link>
          <div className="flex items-center gap-3">
            <span className="text-sm">{username ?? '—'}</span>
            <button
              type="button"
              onClick={onLogout}
              className="font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-ink"
            >
              Sign out
            </button>
          </div>
        </div>
        <nav className="flex flex-wrap gap-x-4 gap-y-2 text-sm" aria-label="Primary (mobile)">
          {FLAT_NAV.map((item) => (
            <MobileNavLink key={item.to} item={item} />
          ))}
        </nav>
      </header>

      {/* Single content area — scrolls independently of fixed sidebar (≥md)
          / fixed header (<md). children renders ONCE; CSS does the layout
          flip between row (desktop, sidebar to the left) and column (mobile,
          header on top). Avoids the double-mount that earlier 2-pane attempt
          produced (would have fired API calls twice for live components). */}
      <main className="min-w-0 flex-1 overflow-y-auto px-4 py-4 md:px-6 md:py-6">{children}</main>
    </div>
  );
}

function SidebarLink({ item }: { item: NavItemSpec }): JSX.Element {
  const { pathname } = useRouter();
  const active = pathname === item.to || pathname.startsWith(item.to + '/');
  const Icon = item.icon;
  return (
    <Link
      to={item.to}
      aria-current={active ? 'page' : undefined}
      title={item.description}
      aria-label={`${item.label} — ${item.description}`}
      className={
        active
          ? 'flex h-11 items-center gap-3 border-l-2 border-signal bg-secondary/50 pl-[1.125rem] pr-5 text-sm font-medium text-ink'
          : 'flex h-11 items-center gap-3 border-l-2 border-transparent pl-[1.125rem] pr-5 text-sm text-muted-foreground hover:bg-secondary/30 hover:text-ink'
      }
    >
      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
      <span className="truncate">{item.label}</span>
    </Link>
  );
}

function MobileNavLink({ item }: { item: NavItemSpec }): JSX.Element {
  const { pathname } = useRouter();
  const active = pathname === item.to || pathname.startsWith(item.to + '/');
  return (
    <Link
      to={item.to}
      aria-current={active ? 'page' : undefined}
      title={item.description}
      aria-label={`${item.label} — ${item.description}`}
      className={
        active
          ? 'border-b-2 border-signal pb-1 text-ink'
          : 'pb-1 text-muted-foreground hover:text-ink'
      }
    >
      {item.label}
    </Link>
  );
}

/* ============================================================
 * Inline SVG icons — single-stroke, 16px, currentColor.
 * Lucide-style restraint; no library dependency to keep the bundle slim
 * and stay aligned with DESIGN.md's hairline aesthetic.
 * ============================================================ */

function IconBase(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    />
  );
}

function IconTable(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <IconBase {...props}>
      <rect x="2" y="3" width="12" height="10" rx="1" />
      <path d="M2 7h12M2 11h12M6 3v10" />
    </IconBase>
  );
}

function IconChart(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <IconBase {...props}>
      <path d="M2 13h12" />
      <rect x="3" y="9" width="2.5" height="4" />
      <rect x="6.75" y="6" width="2.5" height="7" />
      <rect x="10.5" y="3" width="2.5" height="10" />
    </IconBase>
  );
}

function IconEdit(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <IconBase {...props}>
      <path d="M11 2.5L13.5 5L5 13.5H2.5V11L11 2.5z" />
      <path d="M9.5 4l2.5 2.5" />
    </IconBase>
  );
}

function IconSliders(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <IconBase {...props}>
      <path d="M3 4h10M3 8h10M3 12h10" />
      <circle cx="6" cy="4" r="1.25" />
      <circle cx="10" cy="8" r="1.25" />
      <circle cx="5" cy="12" r="1.25" />
    </IconBase>
  );
}

function IconUsers(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <IconBase {...props}>
      <circle cx="6" cy="5" r="2.25" />
      <path d="M2 13c0-2.5 2-4 4-4s4 1.5 4 4" />
      <circle cx="11" cy="5.5" r="1.75" />
      <path d="M10.5 9c2 0 3.5 1.5 3.5 3.5" />
    </IconBase>
  );
}

function IconShield(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <IconBase {...props}>
      <path d="M8 2L13 4v4c0 3-2 5-5 6c-3-1-5-3-5-6V4L8 2z" />
      <path d="M6 8l1.5 1.5L10.5 6.5" />
    </IconBase>
  );
}

function IconBook(props: SVGProps<SVGSVGElement>): JSX.Element {
  return (
    <IconBase {...props}>
      <path d="M3 2.5h7a2 2 0 0 1 2 2v9H5a2 2 0 0 1-2-2v-9z" />
      <path d="M12 4.5h1v9h-7" />
      <path d="M5.5 5.5h4M5.5 8h4" />
    </IconBase>
  );
}
