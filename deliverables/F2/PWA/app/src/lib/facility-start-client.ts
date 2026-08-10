/**
 * Facility slug links (design F2-Facility-Slug-Links-2026-07-16).
 *
 * A facility's public link is `<origin>/f/<slug>` — bare slug, no secret. The
 * StartScreen resolves it read-only (`GET /f/resolve`) to show the facility
 * name, and only an explicit Start tap POSTs `/self-register {slug}`, which
 * creates the sr- case, assigns the next QN in the facility's block, and mints
 * a qn-bound device token (same shape as a numbered-link claim).
 */

export interface ResolveDeps {
  proxyUrl: string;
  slug: string;
  fetchImpl: typeof fetch;
}

export type ResolveResponse =
  | { ok: true; facility_id: string; facility_name: string }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function resolveFacilitySlug(deps: ResolveDeps): Promise<ResolveResponse> {
  const url = `${deps.proxyUrl}/f/resolve?slug=${encodeURIComponent(deps.slug)}`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, { method: 'GET' });
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

  const env = parsed as
    | { ok: true; facility_id: string; facility_name: string }
    | { ok: false; error: { code: string; message: string } };
  if (env.ok === true && env.facility_id) {
    return { ok: true, facility_id: env.facility_id, facility_name: env.facility_name ?? '' };
  }
  return {
    ok: false,
    transport: false,
    error: env.ok === false ? env.error : { code: 'E_UNKNOWN', message: 'Resolve returned no facility' },
  };
}

export interface SelfRegisterDeps {
  proxyUrl: string;
  slug: string;
  fetchImpl: typeof fetch;
}

export type SelfRegisterResponse =
  | {
      ok: true;
      token: string;
      hcw_id: string;
      qn: string;
      facility_id: string;
      facility_name: string;
    }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function selfRegisterBySlug(deps: SelfRegisterDeps): Promise<SelfRegisterResponse> {
  const url = `${deps.proxyUrl}/self-register`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug: deps.slug }),
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
    | {
        ok: true;
        token: string;
        hcw_id: string;
        qn: string;
        facility_id: string;
        facility_name: string;
      }
    | { ok: false; error: { code: string; message: string } };
  if (env.ok === true && env.token && env.hcw_id) {
    return {
      ok: true,
      token: env.token,
      hcw_id: env.hcw_id,
      qn: env.qn ?? '',
      facility_id: env.facility_id ?? '',
      facility_name: env.facility_name ?? '',
    };
  }
  return {
    ok: false,
    transport: false,
    error:
      env.ok === false ? env.error : { code: 'E_UNKNOWN', message: 'Self-register returned no token' },
  };
}

/**
 * Parse `/f/<slug>` from the current location. null when not a facility URL.
 * Mirror of the server's FACILITY_SLUG_RE (+ case-fold); `/f/resolve` is the
 * resolver endpoint, never a start page.
 */
export function parseFacilityUrl(loc: { pathname: string }): { slug: string } | null {
  const m = /^\/f\/([a-z0-9][a-z0-9-]{1,30})\/?$/i.exec(loc.pathname);
  if (!m) return null;
  const slug = m[1]!.toLowerCase();
  return slug === 'resolve' ? null : { slug };
}
