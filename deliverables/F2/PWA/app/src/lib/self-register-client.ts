/**
 * Model C — open self-register (design F2-Model-C-Self-Register-2026-07-16).
 * Calls the API's public `POST /self-register` with the facility QR token in the
 * Authorization header. The server assigns the next 12-digit QN in the facility's
 * F2 block and creates the case; the device then enrolls device-bound to it.
 */

export interface SelfRegisterDeps {
  proxyUrl: string;
  /** The verified facility QR token (tablet_id === '__self_register__'). */
  deviceToken: string;
  fetchImpl: typeof fetch;
}

export type SelfRegisterResponse =
  | { ok: true; hcw_id: string; qn: string; facility_id: string }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function selfRegister(deps: SelfRegisterDeps): Promise<SelfRegisterResponse> {
  const url = `${deps.proxyUrl}/self-register`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${deps.deviceToken}`, 'Content-Type': 'application/json' },
    });
  } catch (err) {
    return {
      ok: false,
      transport: true,
      error: { code: 'E_NETWORK', message: (err as Error).message || 'Network error' },
    };
  }

  let parsed: unknown;
  try {
    parsed = await response.json();
  } catch {
    return { ok: false, transport: true, error: { code: 'E_PARSE', message: 'Invalid JSON from server' } };
  }

  if (!response.ok) {
    const env = parsed as { error?: { code?: string; message?: string } };
    return {
      ok: false,
      transport: false,
      error: {
        code: env.error?.code ?? 'E_HTTP_' + response.status,
        message: env.error?.message ?? `HTTP ${response.status}`,
      },
    };
  }

  // kill_switch returns HTTP 200 with { ok: false, error } (AS envelope parity).
  const env = parsed as
    | { ok: true; hcw_id: string; qn: string; facility_id: string }
    | { ok: false; error: { code: string; message: string } };
  if (env.ok === true && env.qn && env.hcw_id) {
    return { ok: true, hcw_id: env.hcw_id, qn: env.qn, facility_id: env.facility_id ?? '' };
  }
  return {
    ok: false,
    transport: false,
    error:
      env.ok === false
        ? env.error
        : { code: 'E_UNKNOWN', message: 'Self-register returned no QN' },
  };
}
