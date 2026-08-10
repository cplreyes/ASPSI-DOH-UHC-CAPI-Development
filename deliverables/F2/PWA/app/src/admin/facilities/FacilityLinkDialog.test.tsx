/**
 * Facility link dialog (spec F2-Facilities-Page-2026-07-16): create mode with
 * suggestSlug pre-fill + duplicate guard, save via the existing upsert, and
 * view mode for already-linked facilities.
 */
import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FacilityLinkDialog, type FacilityLinkDialogProps } from './FacilityLinkDialog';
import { AdminAuthProvider } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const daraga = { facility_id: '040341130', facility_name: 'RHU Daraga I' };
const lphbayTaken = new Map([
  ['lphbay', { facility_id: '040340210', facility_name: 'LPH-Bay District Hospital' }],
]);

function renderDialog(over: Partial<FacilityLinkDialogProps> = {}) {
  const onSaved = vi.fn();
  const onClose = vi.fn();
  const fetchImpl =
    over.fetchImpl ??
    (vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body ?? '{}')) as { slug?: string };
      return jsonResponse({
        ok: true,
        slug: body.slug,
        facility_id: daraga.facility_id,
        facility_name: daraga.facility_name,
        active: true,
        url: `https://uhc-hcw.asiansocial.org/f/${body.slug}`,
      });
    }) as unknown as typeof fetch);
  render(
    <AdminAuthProvider>
      <RouterProvider>
        <FacilityLinkDialog
          apiBaseUrl="https://w.example"
          fetchImpl={fetchImpl}
          facility={daraga}
          existing={null}
          takenSlugs={lphbayTaken}
          onSaved={onSaved}
          onClose={onClose}
          {...over}
        />
      </RouterProvider>
    </AdminAuthProvider>,
  );
  return { onSaved, onClose, fetchImpl };
}

describe('<FacilityLinkDialog>', () => {
  it('create mode pre-fills the slug from the facility name and shows the facility read-only', () => {
    renderDialog();
    expect(screen.getByTestId('dialog-slug-input')).toHaveValue('rhu-daraga-i');
    expect(screen.getByText('RHU Daraga I')).toBeInTheDocument();
    expect(screen.getByTestId('dialog-facility-id').textContent).toBe('040341130');
  });

  it('Save POSTs the upsert body and renders the URL + QR', async () => {
    const calls: unknown[] = [];
    const fetchImpl = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      calls.push(JSON.parse(String(init?.body)));
      return jsonResponse({
        ok: true,
        slug: 'rhu-daraga-i',
        facility_id: daraga.facility_id,
        facility_name: daraga.facility_name,
        active: true,
        url: 'https://uhc-hcw.asiansocial.org/f/rhu-daraga-i',
      });
    }) as unknown as typeof fetch;
    const user = userEvent.setup();
    const { onSaved } = renderDialog({ fetchImpl });
    await user.click(screen.getByTestId('dialog-save'));
    await waitFor(() => expect(screen.getByTestId('dialog-url')).toBeInTheDocument());
    expect(screen.getByTestId('dialog-url').textContent).toBe(
      'https://uhc-hcw.asiansocial.org/f/rhu-daraga-i',
    );
    expect(screen.getByTestId('dialog-qr').querySelector('svg')).not.toBeNull();
    expect(calls[0]).toEqual({
      slug: 'rhu-daraga-i',
      facility_id: '040341130',
      facility_name: 'RHU Daraga I',
      active: true,
    });
    expect(onSaved).toHaveBeenCalledTimes(1);
  });

  it("duplicate guard: another facility's slug disables Save and names the owner", async () => {
    const user = userEvent.setup();
    renderDialog();
    const input = screen.getByTestId('dialog-slug-input');
    await user.clear(input);
    await user.type(input, 'lphbay');
    expect(screen.getByTestId('dialog-dup-error').textContent).toMatch(/LPH-Bay District Hospital/);
    expect(screen.getByTestId('dialog-save')).toBeDisabled();
  });

  it("re-saving the SAME facility's slug stays allowed (rename/reactivate path)", async () => {
    const user = userEvent.setup();
    renderDialog({
      takenSlugs: new Map([['rhu-daraga-i', daraga]]),
    });
    const input = screen.getByTestId('dialog-slug-input');
    await user.clear(input);
    await user.type(input, 'rhu-daraga-i');
    expect(screen.queryByTestId('dialog-dup-error')).not.toBeInTheDocument();
    expect(screen.getByTestId('dialog-save')).toBeEnabled();
  });

  it('invalid or reserved slugs disable Save', async () => {
    const user = userEvent.setup();
    renderDialog();
    const input = screen.getByTestId('dialog-slug-input');
    await user.clear(input);
    expect(screen.getByTestId('dialog-save')).toBeDisabled();
    await user.type(input, '-bad');
    expect(screen.getByTestId('dialog-save')).toBeDisabled();
    await user.clear(input);
    await user.type(input, 'resolve');
    expect(screen.getByTestId('dialog-save')).toBeDisabled();
  });

  it('view mode renders the existing URL + QR without a Save button', () => {
    renderDialog({
      existing: {
        slug: 'rhu-daraga-i',
        active: true,
        url: 'https://uhc-hcw.asiansocial.org/f/rhu-daraga-i',
      },
    });
    expect(screen.getByTestId('dialog-url').textContent).toBe(
      'https://uhc-hcw.asiansocial.org/f/rhu-daraga-i',
    );
    expect(screen.getByTestId('dialog-qr').querySelector('svg')).not.toBeNull();
    expect(screen.queryByTestId('dialog-save')).not.toBeInTheDocument();
    expect(screen.queryByTestId('dialog-slug-input')).not.toBeInTheDocument();
  });
});
