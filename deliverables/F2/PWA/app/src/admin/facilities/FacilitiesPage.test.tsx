/**
 * Facilities page (spec F2-Facilities-Page-2026-07-16): composite list render,
 * URL-synced filters, create/view dialog wiring, toggle re-POST, RBAC error.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FacilitiesPage } from './FacilitiesPage';
import { AdminAuthProvider } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const lphbay = {
  facility_id: '040340210',
  facility_name: 'LPH-Bay District Hospital',
  facility_type: 'Hospital',
  region: 'Region V',
  province: 'Albay',
  city_mun: 'Bay',
  target_hcws: 30,
  slug: 'lphbay',
  active: true,
  url: 'https://uhc-hcw.asiansocial.org/f/lphbay',
  submitted: 12,
  refusals: 2,
  in_progress: 3,
};
const daraga = {
  facility_id: '040341130',
  facility_name: 'RHU Daraga I',
  facility_type: 'RHU',
  region: 'Region V',
  province: 'Albay',
  city_mun: 'Daraga',
  target_hcws: null,
  slug: '',
  active: null,
  url: '',
  submitted: 0,
  refusals: 0,
  in_progress: 0,
};

function listFetch(rows = [lphbay, daraga]) {
  const calls: Array<{ url: string; body?: unknown }> = [];
  const fetchImpl = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    const entry: { url: string; body?: unknown } = { url: String(url) };
    if (init?.body) entry.body = JSON.parse(String(init.body));
    calls.push(entry);
    if (init?.method === 'POST') {
      return jsonResponse({ ok: true, slug: 'lphbay', facility_id: '040340210', facility_name: 'LPH-Bay District Hospital', active: false, url: lphbay.url });
    }
    return jsonResponse({ rows, total: rows.length, has_more: false });
  }) as unknown as typeof fetch;
  return { fetchImpl, calls };
}

function renderPage(fetchImpl: typeof fetch) {
  render(
    <AdminAuthProvider>
      <RouterProvider>
        <FacilitiesPage apiBaseUrl="https://w.example" fetchImpl={fetchImpl} />
      </RouterProvider>
    </AdminAuthProvider>,
  );
}

describe('<FacilitiesPage />', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/admin/facilities');
  });

  it('renders linked rows with slug, ACTIVE chip, and counts', async () => {
    const { fetchImpl } = listFetch();
    renderPage(fetchImpl);
    await waitFor(() => expect(screen.getByTestId('facility-row-040340210')).toBeInTheDocument());
    const row = screen.getByTestId('facility-row-040340210');
    expect(row.textContent).toContain('LPH-Bay District Hospital');
    expect(row.textContent).toContain('/f/lphbay');
    expect(row.textContent).toContain('Active');
    expect(row.textContent).toContain('12');
    expect(screen.getByText(/2 facilities/i)).toBeInTheDocument();
    // Target column (F2-Coverage-Report): value when set, em dash when null.
    expect(screen.getByTestId('facility-target-040340210').textContent).toBe('30');
    expect(screen.getByTestId('facility-target-040341130').textContent).toBe('—');
  });

  it('link-less rows show "no link yet" + a create button', async () => {
    const { fetchImpl } = listFetch();
    renderPage(fetchImpl);
    await waitFor(() => expect(screen.getByTestId('facility-row-040341130')).toBeInTheDocument());
    expect(screen.getByTestId('facility-row-040341130').textContent).toMatch(/no link yet/i);
    expect(screen.getByTestId('facility-create-040341130')).toBeInTheDocument();
  });

  it('first load requests limit=500 with no filter params', async () => {
    const { fetchImpl, calls } = listFetch();
    renderPage(fetchImpl);
    await waitFor(() => expect(fetchImpl).toHaveBeenCalled());
    expect(calls[0]!.url).toBe('https://w.example/admin/api/facilities?limit=500');
  });

  it('filters update the fetch query and the URL; "no link yet" sends has_link=false', async () => {
    const { fetchImpl, calls } = listFetch();
    const user = userEvent.setup();
    renderPage(fetchImpl);
    await waitFor(() => expect(screen.getByTestId('facilities-region')).toBeInTheDocument());
    await user.selectOptions(screen.getByTestId('facilities-region'), 'Region V');
    await waitFor(() =>
      expect(calls.some((c) => c.url.includes('region=Region+V'))).toBe(true),
    );
    expect(window.location.search).toContain('region=Region+V');
    await user.click(screen.getByTestId('facilities-no-link'));
    await waitFor(() => expect(calls.some((c) => c.url.includes('has_link=false'))).toBe(true));
    expect(window.location.search).toContain('no_link=1');
  });

  it('create button opens the dialog with the row facility read-only', async () => {
    const { fetchImpl } = listFetch();
    const user = userEvent.setup();
    renderPage(fetchImpl);
    await waitFor(() => expect(screen.getByTestId('facility-create-040341130')).toBeInTheDocument());
    await user.click(screen.getByTestId('facility-create-040341130'));
    expect(screen.getByTestId('dialog-facility-id').textContent).toBe('040341130');
    expect(screen.getByTestId('dialog-slug-input')).toHaveValue('rhu-daraga-i');
  });

  it('Deactivate re-POSTs the slug with active:false and refetches', async () => {
    const { fetchImpl, calls } = listFetch();
    const user = userEvent.setup();
    renderPage(fetchImpl);
    await waitFor(() => expect(screen.getByTestId('facility-toggle-040340210')).toBeInTheDocument());
    await user.click(screen.getByTestId('facility-toggle-040340210'));
    await waitFor(() => expect(calls.some((c) => c.body)).toBe(true));
    expect(calls.find((c) => c.body)!.body).toEqual({
      slug: 'lphbay',
      facility_id: '040340210',
      facility_name: 'LPH-Bay District Hospital',
      active: false,
    });
    // list + toggle + reload
    expect(calls.filter((c) => !c.body).length).toBeGreaterThanOrEqual(2);
  });

  it('counts deep-link into the Data tabs; zero counts stay plain text (F2-Facility-Master-Mgmt)', async () => {
    const { fetchImpl } = listFetch();
    renderPage(fetchImpl);
    await waitFor(() => expect(screen.getByTestId('facility-row-040340210')).toBeInTheDocument());
    expect(screen.getByTestId('facility-submitted-040340210')).toHaveAttribute(
      'href',
      '/admin/data?tab=responses&facility_id=040340210',
    );
    expect(screen.getByTestId('facility-refusals-040340210')).toHaveAttribute(
      'href',
      '/admin/data?tab=responses&facility_id=040340210&status=refusal',
    );
    expect(screen.getByTestId('facility-inprogress-040340210')).toHaveAttribute(
      'href',
      '/admin/data?tab=hcws&facility_id=040340210&status=enrolled&q=sr-',
    );
    // Daraga has all-zero counts → no links.
    expect(screen.queryByTestId('facility-submitted-040341130')).not.toBeInTheDocument();
  });

  it('Add facility opens the create dialog; Edit opens it pre-filled with a frozen id', async () => {
    const { fetchImpl } = listFetch();
    const user = userEvent.setup();
    renderPage(fetchImpl);
    await waitFor(() => expect(screen.getByTestId('facilities-add')).toBeInTheDocument());
    await user.click(screen.getByTestId('facilities-add'));
    expect(screen.getByTestId('edit-facility-id')).toBeInTheDocument();
    await user.keyboard('{Escape}');
    await user.click(screen.getByTestId('facility-edit-040340210'));
    expect(screen.getByTestId('edit-facility-id-frozen').textContent).toBe('040340210');
  });

  it('Archive confirms then PATCHes archived:true; Show archived adds include_archived', async () => {
    const { fetchImpl, calls } = listFetch();
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    const user = userEvent.setup();
    renderPage(fetchImpl);
    await waitFor(() => expect(screen.getByTestId('facility-archive-040340210')).toBeInTheDocument());
    await user.click(screen.getByTestId('facility-archive-040340210'));
    await waitFor(() =>
      expect(
        calls.some(
          (c) =>
            c.url === 'https://w.example/admin/api/facilities/040340210' &&
            JSON.stringify(c.body) === JSON.stringify({ archived: true }),
        ),
      ).toBe(true),
    );
    expect(confirmSpy.mock.calls[0]![0]).toMatch(/stays LIVE/);
    await user.click(screen.getByTestId('facilities-archived'));
    await waitFor(() => expect(calls.some((c) => c.url.includes('include_archived=true'))).toBe(true));
    expect(window.location.search).toContain('archived=1');
    confirmSpy.mockRestore();
  });

  it('surfaces E_PERM_DENIED with the role-lacks message', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ ok: false, error: { code: 'E_PERM_DENIED', message: 'access denied' } }, 403),
    ) as unknown as typeof fetch;
    renderPage(fetchImpl);
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByRole('alert').textContent).toMatch(/dash_users/i);
  });
});
