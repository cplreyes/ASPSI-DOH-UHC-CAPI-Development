import type { FacilityRow } from './db';

export interface FacilitiesClientDeps {
  proxyUrl: string;
  deviceToken: string;
  fetchImpl: typeof fetch;
}

export type GetFacilitiesResponse =
  | { ok: true; facilities: FacilityRow[] }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function getFacilities(deps: FacilitiesClientDeps): Promise<GetFacilitiesResponse> {
  const url = `${deps.proxyUrl}/exec?action=facilities`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, {
      method: 'GET',
      headers: { Authorization: `Bearer ${deps.deviceToken}` },
    });
  } catch (err) {
    return {
      ok: false,
      transport: true,
      error: { code: 'E_NETWORK', message: (err as Error).message || 'Network error' },
    };
  }

  if (!response.ok) {
    let workerErr: { code?: string; message?: string } | undefined;
    try {
      const body = (await response.json()) as { error?: { code?: string; message?: string } };
      workerErr = body.error;
    } catch {
      /* fall through */
    }
    return {
      ok: false,
      transport: true,
      error: {
        code: workerErr?.code ?? 'E_HTTP_' + response.status,
        message: workerErr?.message ?? `HTTP ${response.status}`,
      },
    };
  }

  let parsed: unknown;
  try {
    parsed = await response.json();
  } catch {
    return {
      ok: false,
      transport: true,
      error: { code: 'E_PARSE', message: 'Invalid JSON from backend' },
    };
  }

  const env = parsed as
    | { ok: true; data: { facilities: FacilityRow[] } }
    | { ok: false; error: { code: string; message: string } };

  if (env && env.ok === true) {
    return { ok: true, facilities: env.data.facilities };
  }
  return {
    ok: false,
    transport: false,
    error:
      env && 'error' in env
        ? env.error
        : { code: 'E_UNKNOWN', message: 'Malformed backend envelope' },
  };
}
