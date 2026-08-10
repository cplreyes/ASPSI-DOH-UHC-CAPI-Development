/**
 * f2-api — Worker-compatible HTTP surface on uhc-hcw.asiansocial.org.
 * Routes match the Cloudflare Worker exactly (the app changes ONLY
 * VITE_F2_PROXY_URL): POST /verify-token · POST|GET /exec?action=… ·
 * GET /api/health · /admin/api/* (P1b, mounted when env.admin is present).
 */
import { randomUUID } from 'node:crypto';
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { serveStatic } from '@hono/node-server/serve-static';
import { verifyJwt, mintJwt, SELF_REGISTER_TABLET_ID, type JwtClaims } from './jwt.js';
import { normalizeSlug, verifySecret, SLUG_RE } from './enroll-links.js';
import { FACILITY_SLUG_RE, normalizeFacilitySlug } from './facility-slugs.js';
import { handleBatchSubmit, handleConfig, handleFacilities, handleSubmit } from './handlers.js';
import type { Store } from './store.js';
import { buildAdminApp } from './admin/routes.js';
import type { AdminStore, FileStore } from './admin/store.js';

export interface AdminOptions {
  adminStore: AdminStore;
  fileStore: FileStore;
  /** Public PWA origin for reissue enroll_url links (env PWA_ORIGIN). */
  pwaOrigin?: string;
  pwaVersion?: string;
  pwaBuildSha?: string;
  apiVersion?: string;
  apiDeployedAt?: string;
}

export interface AppEnv {
  jwtSigningKey: string;
  store: Store;
  /** P1b admin portal backend — /admin/api/* is mounted when present. */
  admin?: AdminOptions;
  /**
   * P3: directory holding the PWA build (env F2_WWW_DIR). When present the app
   * serves it with an index.html SPA fallback — the CF Pages `_redirects`
   * replacement (#528: cold /enroll?token= must load). API paths never fall
   * through to the SPA.
   */
  staticDir?: string;
}

/** Paths owned by the API — a miss here is a JSON 404, never index.html. */
const API_PATH_RE = /^\/(exec$|verify-token$|self-register$|claim$|api\/|admin\/api\/)/;

/** Device-token lifetime for a numbered-link claim (covers a fieldwork window). */
const CLAIM_TOKEN_TTL_DAYS = 90;

const errJson = (code: string, message: string) => ({ ok: false, error: { code, message } });

export function createApp(env: AppEnv): Hono {
  const app = new Hono();
  // Same-origin in the end-state; permissive during transition (parity with the
  // Worker's CORS_HEADERS — PATCH/DELETE are admin-portal methods).
  app.use(
    '*',
    cors({
      origin: '*',
      allowMethods: ['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
      allowHeaders: ['Authorization', 'Content-Type'],
      maxAge: 86400,
    }),
  );

  if (env.admin) {
    app.route(
      '/admin/api',
      buildAdminApp({
        jwtSigningKey: env.jwtSigningKey,
        store: env.store,
        adminStore: env.admin.adminStore,
        fileStore: env.admin.fileStore,
        pwaOrigin: env.admin.pwaOrigin ?? 'https://uhc-hcw.asiansocial.org',
        pwaVersion: env.admin.pwaVersion ?? '',
        pwaBuildSha: env.admin.pwaBuildSha ?? '',
        apiVersion: env.admin.apiVersion ?? '',
        apiDeployedAt: env.admin.apiDeployedAt ?? '',
      }),
    );
  }

  app.get('/api/health', (c) => c.json({ ok: true, service: 'f2-api', now: new Date().toISOString() }));

  app.post('/verify-token', async (c) => {
    const body = (await c.req.json().catch(() => ({}))) as { token?: string };
    const token = (body.token ?? '').trim();
    if (!token) return c.json(errJson('E_BAD_REQUEST', 'token is required.'), 400);
    const result = await verifyJwt(token, env.jwtSigningKey);
    if (!result.ok) return c.json(errJson('E_TOKEN_INVALID', `Token rejected (${result.reason}).`), 401);
    if (result.claims.tablet_id === '__admin_session__') {
      return c.json(errJson('E_TOKEN_INVALID', 'Not a device token.'), 401);
    }
    if (await env.store.isRevoked(result.claims.jti)) {
      return c.json(errJson('E_TOKEN_REVOKED', 'Token has been revoked.'), 401);
    }
    return c.json({
      ok: true,
      claims: {
        facility_id: result.claims.facility_id,
        exp: result.claims.exp,
        tablet_id: result.claims.tablet_id,
        qn: result.claims.qn ?? '',
      },
    });
  });

  // Facility slug links (design F2-Facility-Slug-Links-2026-07-16) — public,
  // read-only StartScreen lookup. Exact route: it wins over the /f/<slug> SPA
  // fallback below (Hono matches in registration order); "resolve" is a
  // reserved slug. Unknown/inactive/malformed all return the SAME neutral 404
  // (don't reveal which).
  app.get('/f/resolve', async (c) => {
    const admin = env.admin;
    if (!admin) return c.json(errJson('E_UNAVAILABLE', 'Resolve requires the admin store.'), 503);
    const slug = normalizeFacilitySlug(c.req.query('slug') ?? '');
    const miss = () =>
      c.json(errJson('E_NOT_FOUND', "This survey link isn't active — check with ASPSI ops."), 404);
    if (!FACILITY_SLUG_RE.test(slug)) return miss();
    const rec = await admin.adminStore.getFacilitySlug(slug);
    if (!rec || !rec.active) return miss();
    return c.json({ ok: true, facility_id: rec.facility_id, facility_name: rec.facility_name });
  });

  // Model C — open self-register (design F2-Model-C-Self-Register-2026-07-16;
  // slug branch: F2-Facility-Slug-Links-2026-07-16).
  // Two ways in, both spawning a fresh case whose 12-digit QN is assigned in the
  // facility's F2 block by REUSING the admin-create assigner (adminStore.createHcw
  // with qn=''). Consent/survey/submit/refusal/sync are all inherited unchanged.
  //   1. `{ slug }` body (facility slug link) — no credential at all; the bare
  //      public slug names the facility and a qn-bound device token is minted.
  //   2. Facility-scoped QR token (tablet_id === SELF_REGISTER_TABLET_ID) —
  //      the legacy facility-QR handout; returns a QN but no device token.
  app.post('/self-register', async (c) => {
    const admin = env.admin;
    if (!admin) {
      return c.json(errJson('E_UNAVAILABLE', 'Self-register requires the admin store.'), 503);
    }
    const body = (await c.req.json().catch(() => ({}))) as { slug?: unknown };
    const slug = typeof body.slug === 'string' ? normalizeFacilitySlug(body.slug) : '';

    // Facility slug path: the explicit Start tap POSTs here; the server creates
    // the sr- case, assigns the next QN in the facility block, AND mints a
    // qn-bound device token (same shape as /claim) so the phone drops straight
    // into consent → survey.
    if (slug) {
      const miss = () =>
        c.json(errJson('E_NOT_FOUND', "This survey link isn't active — check with ASPSI ops."), 404);
      if (!FACILITY_SLUG_RE.test(slug)) return miss();
      // kill_switch parity with /exec (HTTP 200 + error envelope).
      if ((await env.store.getConfig('kill_switch')) === 'true') {
        return c.json(errJson('E_KILL_SWITCH', 'Backend is temporarily unavailable'));
      }
      const rec = await admin.adminStore.getFacilitySlug(slug);
      if (!rec || !rec.active) return miss();
      const hcwId = 'sr-' + randomUUID();
      const r = await admin.adminStore.createHcw({
        hcw_id: hcwId,
        facility_id: rec.facility_id,
        facility_name: rec.facility_name,
        status: 'enrolled',
        qn: '',
      });
      if (!r.ok) {
        const status = r.code === 'E_VALIDATION' ? 400 : r.code === 'E_CONFLICT' ? 409 : 502;
        return c.json(errJson(r.code, r.message), status);
      }
      const nowS = Math.floor(Date.now() / 1000);
      const exp = nowS + CLAIM_TOKEN_TTL_DAYS * 86400;
      const jti = randomUUID();
      const claims: JwtClaims = {
        jti,
        tablet_id: randomUUID(),
        facility_id: rec.facility_id,
        iat: nowS,
        exp,
        ...(r.qn ? { qn: r.qn } : {}),
      };
      const token = await mintJwt(claims, env.jwtSigningKey);
      await admin.adminStore.tokenAudit({
        jti,
        tablet_id: claims.tablet_id,
        tablet_label: 'slug ' + slug,
        facility_id: rec.facility_id,
        issued_at: nowS,
        expires_at: exp,
      });
      // Forensic trail: which slug spawned which case.
      await admin.adminStore.writeAudit({
        event_type: 'admin_self_register_slug',
        hcw_id: r.hcw_id,
        facility_id: rec.facility_id,
        event_resource: slug,
      });
      return c.json({
        ok: true,
        token,
        hcw_id: r.hcw_id,
        qn: r.qn,
        facility_id: rec.facility_id,
        facility_name: rec.facility_name,
      });
    }

    // Legacy facility-QR path — a purpose-minted facility token in the
    // Authorization header; never a per-HCW device token (models A/B) or an
    // admin session.
    const authHeader = c.req.header('Authorization') ?? '';
    if (!authHeader.startsWith('Bearer ')) {
      return c.json(errJson('E_BAD_REQUEST', 'Missing or malformed Authorization header.'), 400);
    }
    const token = authHeader.slice('Bearer '.length).trim();
    const vr = await verifyJwt(token, env.jwtSigningKey);
    if (!vr.ok) {
      const expired = vr.reason === 'expired';
      return c.json(
        errJson(
          expired ? 'E_TOKEN_EXPIRED' : 'E_TOKEN_INVALID',
          expired
            ? 'Facility QR expired. Ask ASPSI ops for a fresh one.'
            : 'Facility token invalid. Contact ASPSI ops.',
        ),
        401,
      );
    }
    if (vr.claims.tablet_id !== SELF_REGISTER_TABLET_ID) {
      return c.json(errJson('E_TOKEN_INVALID', 'Not a self-register token.'), 401);
    }
    if (await env.store.isRevoked(vr.claims.jti)) {
      return c.json(errJson('E_TOKEN_REVOKED', 'Facility QR revoked by ops. Ask them for a new one.'), 401);
    }
    // kill_switch parity with /exec (HTTP 200 + error envelope).
    if ((await env.store.getConfig('kill_switch')) === 'true') {
      return c.json(errJson('E_KILL_SWITCH', 'Backend is temporarily unavailable'));
    }
    // Server-generated hcw_id (no roster identifier in open self-register); the
    // 'sr-' prefix marks self-registered cases in the admin HCW list. status
    // 'enrolled' = the case is open ("In progress" on the Facilities page) until
    // the forward-only close-out in handleSubmit tags it submitted/refusal.
    const hcwId = 'sr-' + randomUUID();
    const r = await admin.adminStore.createHcw({
      hcw_id: hcwId,
      facility_id: vr.claims.facility_id,
      facility_name: '',
      status: 'enrolled',
      qn: '',
    });
    if (!r.ok) {
      const status = r.code === 'E_VALIDATION' ? 400 : r.code === 'E_CONFLICT' ? 409 : 502;
      return c.json(errJson(r.code, r.message), status);
    }
    return c.json({ ok: true, hcw_id: r.hcw_id, qn: r.qn, facility_id: vr.claims.facility_id });
  });

  // Model C — numbered short-link claim (design F2-Model-C-Numbered-Links-2026-07-16).
  // The credential is the URL itself: slug (a pre-provisioned HCW slot) + secret `k`.
  // On success we mint a per-HCW device token bound to that slot's QN — the SAME
  // shape a reissued token has — so enrollment/submit/refusal/sync are inherited
  // unchanged. The slot's secret is stored only as an HMAC (keyed with the signing
  // key); verification is constant-time. Unknown-slug and bad-secret return the SAME
  // 401 so the response never reveals which half was wrong.
  app.post('/claim', async (c) => {
    const admin = env.admin;
    if (!admin) {
      return c.json(errJson('E_UNAVAILABLE', 'Claim requires the admin store.'), 503);
    }
    const body = (await c.req.json().catch(() => ({}))) as { slug?: unknown; k?: unknown };
    const slug = typeof body.slug === 'string' ? normalizeSlug(body.slug) : '';
    const k = typeof body.k === 'string' ? body.k.trim() : '';
    const badLink = () =>
      c.json(errJson('E_TOKEN_INVALID', 'Invalid or expired link. Ask ASPSI ops for a new one.'), 401);
    if (!SLUG_RE.test(slug) || !k) return badLink();
    // kill_switch parity with /exec (HTTP 200 + error envelope).
    if ((await env.store.getConfig('kill_switch')) === 'true') {
      return c.json(errJson('E_KILL_SWITCH', 'Backend is temporarily unavailable'));
    }
    const link = await admin.adminStore.getEnrollLinkBySlug(slug);
    if (!link || !verifySecret(k, link.enroll_secret_hmac, env.jwtSigningKey)) return badLink();
    // A finished slot cannot be re-claimed (the response is already in).
    if (link.status === 'submitted' || link.status === 'refusal' || link.status === 'revoked') {
      return c.json(errJson('E_CONFLICT', "This link's survey is already completed."), 409);
    }
    const nowS = Math.floor(Date.now() / 1000);
    const exp = nowS + CLAIM_TOKEN_TTL_DAYS * 86400;
    const jti = randomUUID();
    const claims: JwtClaims = {
      jti,
      tablet_id: randomUUID(),
      facility_id: link.facility_id,
      iat: nowS,
      exp,
      ...(link.qn ? { qn: link.qn } : {}),
    };
    const token = await mintJwt(claims, env.jwtSigningKey);
    await admin.adminStore.tokenAudit({
      jti,
      tablet_id: claims.tablet_id,
      tablet_label: 'claim ' + slug,
      facility_id: link.facility_id,
      issued_at: nowS,
      expires_at: exp,
    });
    // First-claim stamp for admin visibility (idempotent — re-opens don't reset it).
    await admin.adminStore.markClaimed(link.hcw_id);
    return c.json({ ok: true, token, hcw_id: link.hcw_id, qn: link.qn, facility_id: link.facility_id });
  });

  app.on(['GET', 'POST'], '/exec', async (c) => {
    // 1-3. Bearer → JWT → revocation (identical order + codes to worker/src/exec.ts).
    const authHeader = c.req.header('Authorization') ?? '';
    if (!authHeader.startsWith('Bearer ')) {
      return c.json(errJson('E_BAD_REQUEST', 'Missing or malformed Authorization header.'), 400);
    }
    const token = authHeader.slice('Bearer '.length).trim();
    const verifyResult = await verifyJwt(token, env.jwtSigningKey);
    if (!verifyResult.ok) {
      const expired = verifyResult.reason === 'expired';
      return c.json(
        errJson(
          expired ? 'E_TOKEN_EXPIRED' : 'E_TOKEN_INVALID',
          expired
            ? 'Tablet token expired. Re-enrol with a new token from ops.'
            : 'Tablet authorisation invalid. Contact ASPSI ops.',
        ),
        401,
      );
    }
    if (verifyResult.claims.tablet_id === '__admin_session__') {
      return c.json(errJson('E_TOKEN_INVALID', 'Admin session is not a valid device token.'), 401);
    }
    if (await env.store.isRevoked(verifyResult.claims.jti)) {
      return c.json(errJson('E_TOKEN_REVOKED', 'Tablet revoked by ops. Contact them for a new token.'), 401);
    }

    // 4. Action routing — replaces the AS forward; envelopes/codes are AS-identical.
    const action = c.req.query('action') ?? '';
    if (!action) return c.json(errJson('E_BAD_REQUEST', 'action query parameter is required.'), 400);

    // AS Router.js:27 parity: kill_switch gates every public action (HTTP 200 +
    // error envelope, like ContentService). This is also what makes a post-P4
    // rollback single-authority: unflip sets MySQL kill_switch=true so the new
    // stack refuses writes while the Sheet path serves again.
    if ((await env.store.getConfig('kill_switch')) === 'true') {
      return c.json(errJson('E_KILL_SWITCH', 'Backend is temporarily unavailable'));
    }

    const body: unknown = c.req.method === 'GET' ? {} : await c.req.json().catch(() => null);

    switch (action) {
      case 'batch-submit':
        return c.json(await handleBatchSubmit(body, env.store));
      case 'submit':
        return c.json(await handleSubmit(body, env.store));
      case 'config':
        return c.json(await handleConfig(env.store));
      case 'facilities':
        return c.json(await handleFacilities(env.store));
      default:
        return c.json(errJson('E_UNKNOWN_ACTION', `No handler for action '${action}'.`), 404);
    }
  });

  if (env.staticDir) {
    const staticDir = env.staticDir;
    // Unknown API paths 404 as JSON here — they must not fall through to the SPA.
    app.get('*', (c, next) => {
      if (API_PATH_RE.test(c.req.path)) {
        return Promise.resolve(c.json(errJson('E_NOT_FOUND', `No route for GET ${c.req.path}`), 404));
      }
      return next();
    });
    app.get('*', serveStatic({ root: staticDir }));
    // SPA fallback (#528): any other GET serves index.html — /enroll?token=,
    // /admin, deep links — matching the CF Pages `_redirects` behaviour.
    app.get('*', serveStatic({ root: staticDir, rewriteRequestPath: () => '/index.html' }));
  }

  app.notFound((c) => c.json(errJson('E_NOT_FOUND', `No route for ${c.req.method} ${c.req.path}`), 404));
  return app;
}
