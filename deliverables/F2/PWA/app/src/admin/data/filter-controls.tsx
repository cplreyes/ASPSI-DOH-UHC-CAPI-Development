/**
 * F2 Admin Portal — shared filter-bar controls for the Data dashboard tabs.
 *
 * Extracted from ResponsesTab (2026-07-17) when the filter bar rolled out to
 * HCWs / Audit / DLQ, so the four tabs render one idiom and cannot drift.
 * Data hooks live in filter-hooks.ts (react-refresh wants component files to
 * export only components). Verde Manual: hairline-underline inputs, mono
 * uppercase labels, pill toggles in signal color.
 */
import { Button } from '@/components/ui/button';
import type { SelectOption } from './filter-hooks';

// FX-014 (2026-05-03): inputs derive `name` from the label so Chrome's
// "form field should have an id or name" issue panel stays clean and so
// browser autofill / password managers have something to key on.
function slugifyLabel(label: string): string {
  return (
    label
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '') || 'field'
  );
}

export function FilterDate({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}): JSX.Element {
  const name = slugifyLabel(label);
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="date"
        name={name}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-0 border-b border-hairline bg-transparent py-1 font-mono text-sm outline-none focus:border-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
      />
    </label>
  );
}

export function FilterText({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}): JSX.Element {
  const name = slugifyLabel(label);
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="text"
        name={name}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
      />
    </label>
  );
}

export function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (v: string) => void;
}): JSX.Element {
  const name = slugifyLabel(label);
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <select
        name={name}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-0 border-b border-hairline bg-transparent py-1 text-sm outline-none focus:border-signal focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function PillToggle({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <Button
      type="button"
      variant="outline"
      onClick={onClick}
      className={
        active
          ? 'h-auto rounded-sm border-signal bg-signal-bg px-3 py-1 text-xs text-signal hover:bg-signal-bg'
          : 'h-auto rounded-sm border-hairline bg-transparent px-3 py-1 text-xs text-muted-foreground hover:bg-transparent hover:text-ink'
      }
    >
      {children}
    </Button>
  );
}

/** Render inside the filter bar ONLY when a filter is active. */
export function ClearFiltersButton({ onClick }: { onClick: () => void }): JSX.Element {
  return (
    <Button
      type="button"
      variant="outline"
      onClick={onClick}
      className="h-auto rounded-sm border-hairline bg-transparent px-3 py-1 font-mono text-xs uppercase tracking-wider text-muted-foreground hover:bg-transparent hover:text-ink"
    >
      ✕ Clear filters
    </Button>
  );
}
