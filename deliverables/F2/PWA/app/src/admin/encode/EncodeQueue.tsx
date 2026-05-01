/**
 * F2 Admin Portal — paper-encoder queue.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 4.3)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.13)
 *
 * Lists HCWs eligible for paper encoding (status='enrolled', no submission
 * yet). The data feed is `/admin/api/dashboards/data/hcws` (Sprint 2.9 —
 * AP0-blocked). Until that endpoint lands, this page lets the Operator
 * type an hcw_id directly and jump to the encode page; the failure modes
 * (HCW not found, already submitted) surface from the backend at submit.
 */
import { useState, type FormEvent } from 'react';
import { useRouter } from '../lib/pages-router';

export function EncodeQueue(): JSX.Element {
  const { navigate } = useRouter();
  const [hcwId, setHcwId] = useState('');

  const onJump = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = hcwId.trim();
    if (!trimmed) return;
    navigate(`/admin/encode/${encodeURIComponent(trimmed)}`);
  };

  return (
    <section className="flex flex-col gap-6 py-8">
      <header className="border-b border-hairline pb-4">
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          Section
        </p>
        <h2 className="mt-1 font-serif text-2xl font-medium tracking-tight">Encode queue</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          HCWs eligible for paper-encoding will appear here once the Sprint 2.9 backend is live.
          For now you can type an HCW ID directly.
        </p>
      </header>

      <form onSubmit={onJump} className="flex flex-col gap-3">
        <label className="flex flex-col gap-1">
          <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
            HCW ID
          </span>
          <input
            type="text"
            value={hcwId}
            onChange={(e) => setHcwId(e.target.value)}
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            className="border-0 border-b border-hairline bg-transparent py-2 font-mono text-sm outline-none focus:border-signal"
            placeholder="e.g. hcw-001"
          />
        </label>
        <div>
          <button
            type="submit"
            disabled={!hcwId.trim()}
            className="inline-flex h-11 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground"
          >
            Open encoder
          </button>
        </div>
      </form>

      <aside className="mt-8 border-l-2 border-hairline pl-3">
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          Coming next
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          Filtered HCW table with pinnable filters (facility, region) lands with Sprint 2.9.
        </p>
      </aside>
    </section>
  );
}
