/**
 * F2 Admin Portal — top nav layout.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.14, Step 4)
 * Design: deliverables/F2/PWA/app/DESIGN.md — Verde Manual.
 *
 * Two nav groups per spec §7: Operations (always-visible: Data, Reports)
 * and Configuration (Apps & Settings, Users, Roles — folded behind a
 * dropdown to keep the bar quiet, opens on click). Active link uses the
 * signal color underline; everything else stays muted.
 *
 * Role-aware filtering is intentionally NOT implemented in this shell
 * task — the perms dictionary lands in Sprint 3 with the full Roles CRUD.
 * Today every authenticated user sees every link; clicking into a tab
 * the worker rejects with E_PERM_DENIED 403 will surface a "no access"
 * panel via Sprint 2.20 empty-state work.
 */
import { useState, type ReactNode } from 'react';
import { Link, useRouter } from './lib/pages-router';
import { useAdminAuth } from './lib/auth-context';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps): JSX.Element {
  const { username, role, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();

  const onLogout = () => {
    clearAuth();
    navigate('/admin/login');
  };

  return (
    <div className="mx-auto flex min-h-screen-dvh w-full max-w-screen-2xl flex-col">
      <header className="flex flex-wrap items-baseline gap-x-8 gap-y-2 border-b border-hairline px-6 py-3">
        <Link to="/admin/data" className="flex flex-col">
          <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            F2 Admin
          </span>
          <span className="font-serif text-lg font-medium tracking-tight">F2 PWA Portal</span>
        </Link>

        <nav className="flex flex-1 flex-wrap items-center gap-6 text-sm" aria-label="Primary">
          <NavLink to="/admin/data">Data</NavLink>
          <NavLink to="/admin/report">Reports</NavLink>
          <ConfigDropdown />
          <NavLink to="/admin/encode">Encode</NavLink>
        </nav>

        <div className="flex items-center gap-4">
          <div className="hidden text-right sm:block">
            <p className="text-sm">{username}</p>
            <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              {role ?? '—'}
            </p>
          </div>
          <button
            type="button"
            onClick={onLogout}
            className="font-mono text-xs uppercase tracking-wider text-muted-foreground underline-offset-4 hover:text-ink hover:underline"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="flex-1 px-6 py-6">{children}</main>
    </div>
  );
}

function NavLink({ to, children }: { to: string; children: ReactNode }): JSX.Element {
  const { pathname } = useRouter();
  const active = pathname === to || pathname.startsWith(to + '/');
  return (
    <Link
      to={to}
      aria-current={active ? 'page' : undefined}
      className={
        active
          ? 'border-b-2 border-signal pb-1 text-ink'
          : 'pb-1 text-muted-foreground hover:text-ink'
      }
    >
      {children}
    </Link>
  );
}

function ConfigDropdown(): JSX.Element {
  const [open, setOpen] = useState(false);
  const { pathname } = useRouter();
  const active =
    pathname.startsWith('/admin/apps') ||
    pathname.startsWith('/admin/users') ||
    pathname.startsWith('/admin/roles');

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className={
          active
            ? 'flex items-center gap-1 border-b-2 border-signal pb-1 text-ink'
            : 'flex items-center gap-1 pb-1 text-muted-foreground hover:text-ink'
        }
      >
        Configuration
        <span aria-hidden="true" className="text-xs">▾</span>
      </button>
      {open ? (
        <div
          role="menu"
          className="absolute left-0 top-full z-10 mt-1 flex min-w-[12rem] flex-col border border-hairline bg-paper py-1"
          onClick={() => setOpen(false)}
        >
          <Link to="/admin/apps" className="px-3 py-2 text-sm hover:bg-secondary">
            Apps &amp; Settings
          </Link>
          <Link to="/admin/users" className="px-3 py-2 text-sm hover:bg-secondary">
            Users
          </Link>
          <Link to="/admin/roles" className="px-3 py-2 text-sm hover:bg-secondary">
            Roles
          </Link>
        </div>
      ) : null}
    </div>
  );
}
