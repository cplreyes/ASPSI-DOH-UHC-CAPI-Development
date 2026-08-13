/**
 * CSV import dialog (spec F2-Facility-Master-Mgmt-2026-07-16): dry-run gate,
 * verdict table, Apply, template link.
 */
import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FacilityImportDialog } from './FacilityImportDialog';
import { AdminAuthProvider } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const HEADER = 'facility_id,facility_name,facility_type,region,province,city_mun,barangay';
const CSV = `${HEADER}\n040341130,RHU Daraga I,RHU,Region V (Bicol Region),Albay,Daraga,\nabc,Bad,,,,,`;

function importResult(mode: string) {
  return {
    ok: true,
    mode,
    summary: { creates: 1, updates: 0, unchanged: 0, errors: 1, warnings: 1 },
    verdicts: [
      { row: 1, facility_id: '040341130', action: 'create', warnings: ['province "Albay" is new to the master — check spelling against CSWeb'], errors: [] },
      { row: 2, facility_id: 'abc', action: 'error', warnings: [], errors: ['facility_id must be exactly 9 digits'] },
    ],
  };
}

function renderDialog() {
  const onApplied = vi.fn();
  const calls: Array<{ body: { mode: string; rows: unknown[] } }> = [];
  const fetchImpl = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body)) as { mode: string; rows: unknown[] };
    calls.push({ body });
    return jsonResponse(importResult(body.mode));
  }) as unknown as typeof fetch;
  render(
    <AdminAuthProvider>
      <RouterProvider>
        <FacilityImportDialog
          apiBaseUrl="https://w.example"
          fetchImpl={fetchImpl}
          onApplied={onApplied}
          onClose={vi.fn()}
        />
      </RouterProvider>
    </AdminAuthProvider>,
  );
  return { onApplied, calls };
}

describe('<FacilityImportDialog>', () => {
  it('dry-runs the pasted CSV and renders the verdict table + summary', async () => {
    const user = userEvent.setup();
    const { calls } = renderDialog();
    expect(screen.getByTestId('import-apply')).toBeDisabled();
    await user.click(screen.getByTestId('import-text'));
    await user.paste(CSV);
    await user.click(screen.getByTestId('import-dry-run'));
    await waitFor(() => expect(screen.getByTestId('import-verdicts')).toBeInTheDocument());
    expect(calls[0]!.body.mode).toBe('dry_run');
    expect(calls[0]!.body.rows).toHaveLength(2);
    expect(screen.getByTestId('import-summary').textContent).toMatch(/1 create.*1 error/);
    expect(screen.getByTestId('import-verdicts').textContent).toMatch(/exactly 9 digits/);
  });

  it('Apply arms only after a dry run, sends mode:apply, and reports back', async () => {
    const user = userEvent.setup();
    const { calls, onApplied } = renderDialog();
    await user.click(screen.getByTestId('import-text'));
    await user.paste(CSV);
    await user.click(screen.getByTestId('import-dry-run'));
    await waitFor(() => expect(screen.getByTestId('import-apply')).toBeEnabled());
    await user.click(screen.getByTestId('import-apply'));
    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls[1]!.body.mode).toBe('apply');
    expect(onApplied).toHaveBeenCalledTimes(1);
    await waitFor(() =>
      expect(screen.getByTestId('import-summary').textContent).toMatch(/Applied/),
    );
  });

  it('editing the CSV after a dry run re-arms the gate; parse errors surface locally', async () => {
    const user = userEvent.setup();
    renderDialog();
    await user.click(screen.getByTestId('import-text'));
    await user.paste(CSV);
    await user.click(screen.getByTestId('import-dry-run'));
    await waitFor(() => expect(screen.getByTestId('import-apply')).toBeEnabled());
    await user.type(screen.getByTestId('import-text'), 'x');
    expect(screen.getByTestId('import-apply')).toBeDisabled();
    // Bad header → local parse error, no network call needed.
    await user.clear(screen.getByTestId('import-text'));
    await user.click(screen.getByTestId('import-text'));
    await user.paste('wrong,header\n1,2');
    await user.click(screen.getByTestId('import-dry-run'));
    expect(screen.getByTestId('import-parse-error').textContent).toMatch(/Header must be exactly/);
  });

  it('offers the template download', () => {
    renderDialog();
    const a = screen.getByTestId('import-template');
    expect(a).toHaveAttribute('download', 'facility-master-template.csv');
    expect(a.getAttribute('href')).toContain('facility_id');
  });
});
