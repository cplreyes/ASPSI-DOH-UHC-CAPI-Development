/**
 * Calls the Worker's public `/verify-token` endpoint during enrollment.
 * Spec §4.2 step 2.
 */

export interface VerifyTokenDeps {
  proxyUrl: string;
  fetchImpl: typeof fetch;
}

export type VerifyTokenResponse =
  | { ok: true; claims: { facility_id: string; exp: number; tablet_id: string } }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function verifyDeviceToken(
  token: string,
  deps: VerifyTokenDeps,
): Promise<VerifyTokenResponse> {
  const url = `${deps.proxyUrl}/verify-token`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
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
    return {
      ok: false,
      transport: true,
      error: { code: 'E_PARSE', message: 'Invalid JSON from worker' },
    };
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

  const env = parsed as
    | { ok: true; claims: { facility_id: string; exp: number; tablet_id: string } }
    | { ok: false; error: { code: string; message: string } };
  if (env.ok === true) {
    return { ok: true, claims: env.claims };
  }
  return {
    ok: false,
    transport: false,
    error: env.error ?? { code: 'E_UNKNOWN', message: 'Unknown verify-token failure' },
  };
}
