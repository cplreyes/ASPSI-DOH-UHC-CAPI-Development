/**
 * Add/Edit facility dialog (spec F2-Facility-Master-Mgmt-2026-07-16):
 * create POSTs, edit PATCHes with a frozen id, geo warnings keep the dialog open.
 */
import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FacilityEditDialog, type FacilityEditDialogProps } from './FacilityEditDialog';
import { AdminAuthProvider } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function renderDialog(over: Partial<FacilityEditDialogProps> = {}) {
  const onSaved = vi.fn();
  const onClose = vi.fn();
  const calls: Array<{ url: string; method: string; body: unknown }> = [];
  const fetchImpl =
    over.fetchImpl ??
    (vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), method: init?.method ?? 'GET', body: JSON.parse(String(init?.body ?? '{}')) });
      return jsonResponse({ ok: true, row: {}, warnings: [] });
    }) as unknown as typeof fetch);
  render(
    <AdminAuthProvider>
      <RouterProvider>
        <FacilityEditDialog
          apiBaseUrl="https://w.example"
          fetchImpl={fetchImpl}
          mode="create"
          initial={{}}
          knownProvinces={['Laguna']}
          onSaved={onSaved}
          onClose={onClose}
          {...over}
        />
      </RouterProvider>
    </AdminAuthProvider>,
  );
  return { onSaved, onClose, calls };
}

describe('<FacilityEditDialog>', () => {
  it('create mode POSTs the typed fields; Save gated on 9-digit id + name', async () => {
    const user = userEvent.setup();
    const { calls, onClose } = renderDialog();
    const save = screen.getByTestId('edit-save');
    expect(save).toBeDisabled();
    await user.type(screen.getByTestId('edit-facility-id'), '040341130');
    await user.type(screen.getByTestId('edit-facility-name'), 'RHU Daraga I');
    expect(save).toBeEnabled();
    await user.type(screen.getByTestId('edit-province'), 'Albay');
    await user.click(save);
    await waitFor(() => expect(calls).toHaveLength(1));
    expect(calls[0]!.url).toBe('https://w.example/admin/api/facilities');
    expect(calls[0]!.method).toBe('POST');
    expect(calls[0]!.body).toMatchObject({
      facility_id: '040341130',
      facility_name: 'RHU Daraga I',
      province: 'Albay',
    });
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it('edit mode freezes the id and PATCHes the field endpoint', async () => {
    const user = userEvent.setup();
    const { calls } = renderDialog({
      mode: 'edit',
      initial: { facility_id: '040340210', facility_name: 'LPH-Bay District Hospital' },
    });
    expect(screen.queryByTestId('edit-facility-id')).not.toBeInTheDocument();
    expect(screen.getByTestId('edit-facility-id-frozen').textContent).toBe('040340210');
    const name = screen.getByTestId('edit-facility-name');
    await user.clear(name);
    await user.type(name, 'LPH-Bay DH (renamed)');
    await user.click(screen.getByTestId('edit-save'));
    await waitFor(() => expect(calls).toHaveLength(1));
    expect(calls[0]!.url).toBe('https://w.example/admin/api/facilities/040340210');
    expect(calls[0]!.method).toBe('PATCH');
    expect(calls[0]!.body).toMatchObject({ facility_name: 'LPH-Bay DH (renamed)' });
    expect((calls[0]!.body as Record<string, unknown>).facility_id).toBeUndefined();
  });

  it('target_hcws rides as raw text; blank clears with an explicit null (F2-Coverage-Report)', async () => {
    const user = userEvent.setup();
    const { calls } = renderDialog({
      mode: 'edit',
      initial: { facility_id: '040340210', facility_name: 'LPH-Bay', target_hcws: 30 },
    });
    const target = screen.getByTestId('edit-target');
    expect(target).toHaveValue('30');
    await user.clear(target);
    await user.type(target, '45');
    await user.click(screen.getByTestId('edit-save'));
    await waitFor(() => expect(calls).toHaveLength(1));
    expect(calls[0]!.body).toMatchObject({ target_hcws: '45' }); // string — server parses
    await user.clear(target);
    await user.click(screen.getByTestId('edit-save'));
    await waitFor(() => expect(calls).toHaveLength(2));
    expect((calls[1]!.body as Record<string, unknown>).target_hcws).toBeNull(); // blank = clear
  });

  it('geo warnings keep the dialog open and render as chips', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ ok: true, row: {}, warnings: ['region "Region 5" is not a canonical PSGC region name — dashboard by-name joins may miss'] }),
    ) as unknown as typeof fetch;
    const user = userEvent.setup();
    const { onClose, onSaved } = renderDialog({
      fetchImpl,
      mode: 'edit',
      initial: { facility_id: '040340210', facility_name: 'LPH-Bay' },
    });
    await user.click(screen.getByTestId('edit-save'));
    await waitFor(() => expect(screen.getByTestId('edit-warnings')).toBeInTheDocument());
    expect(screen.getByTestId('edit-warnings').textContent).toMatch(/not a canonical PSGC region/);
    expect(onSaved).toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('surfaces a 409 conflict message', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse(
        { ok: false, error: { code: 'E_CONFLICT', message: 'facility 040340210 already exists' } },
        409,
      ),
    ) as unknown as typeof fetch;
    const user = userEvent.setup();
    renderDialog({ fetchImpl, initial: {} });
    await user.type(screen.getByTestId('edit-facility-id'), '040340210');
    await user.type(screen.getByTestId('edit-facility-name'), 'Dup');
    await user.click(screen.getByTestId('edit-save'));
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByRole('alert').textContent).toMatch(/already exists/);
  });
});
