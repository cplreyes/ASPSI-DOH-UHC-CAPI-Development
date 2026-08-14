/**
 * Model C — numbered short-link claim (design F2-Model-C-Numbered-Links-2026-07-16).
 * Calls the API's public `POST /claim` with the slug (from the `/e/<slug>` path)
 * and secret `k` (from the query string). The server verifies the pair and mints a
 * per-HCW device token bound to that slot's QN; the device then enrolls device-bound
 * to it — no token paste, no HCW-ID picker.
 */

export interface ClaimDeps {
  proxyUrl: string;
  slug: string;
  /** The per-link secret from `?k=…`. */
  k: string;
  fetchImpl: typeof fetch;
}

export type ClaimResponse =
  | { ok: true; token: string; hcw_id: string; qn: string; facility_id: string }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function claimBySlug(deps: ClaimDeps): Promise<ClaimResponse> {
  const url = `${deps.proxyUrl}/claim`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug: deps.slug, k: deps.k }),
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
    | { ok: true; token: string; hcw_id: string; qn: string; facility_id: string }
    | { ok: false; error: { code: string; message: string } };
  if (env.ok === true && env.token && env.hcw_id) {
    return {
      ok: true,
      token: env.token,
      hcw_id: env.hcw_id,
      qn: env.qn ?? '',
      facility_id: env.facility_id ?? '',
    };
  }
  return {
    ok: false,
    transport: false,
    error:
      env.ok === false ? env.error : { code: 'E_UNKNOWN', message: 'Claim returned no token' },
  };
}

/** Parse `/e/<slug>?k=<secret>` from the current location. null when not a claim URL. */
export function parseClaimUrl(loc: { pathname: string; search: string }): { slug: string; k: string } | null {
  const m = /^\/e\/([^/?#]+)\/?$/.exec(loc.pathname);
  if (!m) return null;
  const slug = decodeURIComponent(m[1]!);
  const k = new URLSearchParams(loc.search).get('k') ?? '';
  return { slug, k };
}
