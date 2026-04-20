import type { Page, Route } from '@playwright/test';

export interface MockState {
  facilities: Array<{
    facility_id: string;
    facility_name: string;
    facility_type: string;
    region: string;
    province: string;
    city_mun: string;
    barangay: string;
  }>;
  config: {
    current_spec_version: string;
    min_accepted_spec_version: string;
    kill_switch: boolean;
    broadcast_message: string;
    spec_hash: string;
  };
  submissions: Array<{ client_submission_id: string; submission_id: string }>;
  failSubmitOnce?: boolean;
}

export function installMockBackend(page: Page, state: MockState) {
  const handler = async (route: Route) => {
    const url = new URL(route.request().url());
    const action = url.searchParams.get('action') ?? '';
    const method = route.request().method();

    if (action === 'facilities' && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ok: true, data: { facilities: state.facilities } }),
      });
      return;
    }
    if (action === 'config' && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ok: true, data: state.config }),
      });
      return;
    }
    if ((action === 'submit' || action === 'batch-submit') && method === 'POST') {
      if (state.failSubmitOnce) {
        state.failSubmitOnce = false;
        await route.fulfill({ status: 500, body: 'transient' });
        return;
      }
      const body = JSON.parse(route.request().postData() ?? '{}');
      if (action === 'submit') {
        const id = `srv-${body.client_submission_id}`;
        state.submissions.push({
          client_submission_id: body.client_submission_id,
          submission_id: id,
        });
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ok: true,
            data: {
              submission_id: id,
              status: 'accepted',
              server_timestamp: new Date().toISOString(),
            },
          }),
        });
      } else {
        const results = (body.responses ?? []).map((r: { client_submission_id: string }) => {
          const id = `srv-${r.client_submission_id}`;
          state.submissions.push({
            client_submission_id: r.client_submission_id,
            submission_id: id,
          });
          return {
            client_submission_id: r.client_submission_id,
            submission_id: id,
            status: 'accepted',
          };
        });
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ok: true, data: { results } }),
        });
      }
      return;
    }
    if (action === 'audit' && method === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ok: true, data: { audit_id: 'a' } }),
      });
      return;
    }
    await route.fallback();
  };

  return page.route(/.*\/exec\?.*/, handler);
}

export function defaultState(): MockState {
  return {
    facilities: [
      {
        facility_id: 'F001',
        facility_name: 'Test Facility A',
        facility_type: 'Urban Health Center',
        region: 'NCR',
        province: 'Metro Manila',
        city_mun: 'Manila',
        barangay: 'B1',
      },
    ],
    config: {
      current_spec_version: '2026-04-17-m1',
      min_accepted_spec_version: '2026-04-17-m1',
      kill_switch: false,
      broadcast_message: '',
      spec_hash: 'h',
    },
    submissions: [],
  };
}
