/**
 * F2 Admin Portal routes on f2-api — port of worker/src/admin/routes.ts with
 * the Apps Script RPC layer folded into AdminStore (SQL on csweb_f2). The
 * Admin Portal frontend (app/src/admin/**, lib/api-client.ts) is the parity
 * contract: success bodies are UNWRAPPED, errors carry { ok:false, error }
 * with the Worker's exact codes + status codes, and every response carries
 * an X-Request-Id header.
 *
 * Where the Worker used CF KV, this uses auth_kv (AdminStore.kv*); where it
 * used R2, a FileStore on F2_FILES_DIR; where it called Apps Script, the
 * AS handler logic lives here / in AdminStore (AS files are retired at P4).
 */
import { Hono, type Context } from 'hono';
import type { ContentfulStatusCode } from 'hono/utils/http-status';
import { createHash, randomUUID } from 'node:crypto';
import { handleSubmit } from '../handlers.js';
import { mintJwt, SELF_REGISTER_TABLET_ID, type JwtClaims } from '../jwt.js';
import { buildSlug, generateSecret, secretHmac, SHORT_CODE_RE } from '../enroll-links.js';
import { FACILITY_SLUG_RE, normalizeFacilitySlug, RESERVED_FACILITY_SLUGS } from '../facility-slugs.js';
import { validateFacilityInput, type FacilityMasterInput } from '../facility-master.js';
import type { Store } from '../store.js';
import {
  getDummyPasswordHash,
  hashPassword,
  mintAdminJwt,
  PERM_KEYS,
  projectPermissions,
  verifyAdminJwt,
  verifyPassword,
  type AdminJwtPayload,
  type PermKey,
} from './auth.js';
import { requirePerm, RoleVersionCache, type Role } from './rbac.js';
import {
  checkLoginThrottle,
  recordFailedLogin,
  resetLoginThrottle,
  retryAfterSeconds,
} from './throttle.js';
import { formRevisions, mapReport, type CoverageLevel } from './reports.js';
import { mnlWindow } from './mnl-window.js';
import {
  toPublicUser,
  type AdminRoleRecord,
  type AdminStore,
  type AdminUserRecord,
  type AuditFilters,
  type DlqFilters,
  type FileMetaRecord,
  type FileStore,
  type HcwFilters,
  type RespFilters,
} from './store.js';

export interface AdminEnv {
  jwtSigningKey: string;
  /** Respondent-path store — encode + DLQ replay reuse handleSubmit; config reads. */
  store: Store;
  adminStore: AdminStore;
  fileStore: FileStore;
  /** Public PWA origin for enroll_url QR links (env PWA_ORIGIN). */
  pwaOrigin: string;
  pwaVersion: string;
  pwaBuildSha: string;
  apiVersion: string;
  /** ISO timestamp stamped by the deploy script (env API_DEPLOYED_AT). */
  apiDeployedAt: string;
}

type Vars = { Variables: { requestId: string } };
type Ctx = Context<Vars>;

const JWT_TTL_SECONDS = 4 * 60 * 60;
const USERNAME_RE = /^[A-Za-z0-9_]{3,32}$/;
const NAME_RE = /^[A-Za-z][A-Za-z\-' ]*$/;
const ROLE_NAME_RE = /^[A-Za-z][A-Za-z0-9 _-]{0,63}$/;
const HCW_ID_RE = /^[A-Za-z0-9_\-]{1,64}$/;
const FACILITY_ID_RE = /^[A-Za-z0-9_\-]{1,32}$/;
const FILE_ID_RE = /^[A-Za-z0-9_-]+$/;
const FOLDER_NAME_RE = /^(?!.*\.\.)[A-Za-z0-9 _\-.]{1,128}$/;

export const ALLOWED_MIME = new Set([
  'application/pdf',
  'application/zip',
  'application/octet-stream',
  'image/png',
  'image/jpeg',
  'image/gif',
]);
export const MAX_FILE_BYTES = 100 * 1024 * 1024;
const ALLOWED_FILE_EXTENSIONS = ['pdf', 'zip', 'png', 'jpg', 'jpeg', 'gif'];
export const BROADCAST_MAX_LEN = 280;

const errBody = (code: string, message: string) => ({ ok: false, error: { code, message } });

const jsonAt = (c: Ctx, body: unknown, status: number): Response =>
  c.json(body, status as ContentfulStatusCode);

function statusForAsError(code: string | undefined): number {
  if (code === 'E_VALIDATION') return 400;
  if (code === 'E_PAYLOAD_INVALID') return 400;
  if (code === 'E_NOT_FOUND') return 404;
  if (code === 'E_CONFLICT') return 409;
  if (code === 'E_CAS_FAILED') return 409;
  if (code === 'E_LOCK_TIMEOUT') return 503;
  if (code === 'E_DLQ_CORRUPT') return 422;
  return 502;
}

function ipHashOf(c: Ctx): string {
  const raw = (c.req.header('x-forwarded-for') ?? '').split(',')[0]?.trim() ?? '';
  return createHash('sha256').update(raw).digest('hex');
}

/** Strip chars that would break Content-Disposition (Worker parity). */
function sanitizeFilename(name: string): string {
  let cleaned = '';
  for (let i = 0; i < name.length; i++) {
    const code = name.charCodeAt(i);
    if (code < 0x20 || code === 0x7f || code === 0x22 || code === 0x5c) continue;
    cleaned += name[i];
  }
  cleaned = cleaned.trim();
  return cleaned.length > 0 ? cleaned : 'file';
}

function extensionOf(name: string): string {
  const dot = name.lastIndexOf('.');
  if (dot === -1 || dot === name.length - 1) return '';
  return name.slice(dot + 1).toLowerCase();
}

function validFileExtension(name: string): boolean {
  return ALLOWED_FILE_EXTENSIONS.includes(extensionOf(name));
}

const isTruthy = (v: unknown): boolean => {
  if (typeof v === 'boolean') return v;
  if (typeof v === 'number') return v !== 0;
  if (typeof v === 'string') {
    const s = v.trim().toLowerCase();
    return s === 'true' || s === '1' || s === 'yes';
  }
  return false;
};

// ----- query-filter parsing (worker/src/admin/handlers/data.ts parity) ------

const qs = (c: Ctx, k: string): string | undefined => {
  const v = c.req.query(k);
  return v ? v : undefined;
};

const qInt = (c: Ctx, k: string): number | undefined => {
  const v = c.req.query(k);
  return v && /^\d+$/.test(v) ? Number(v) : undefined;
};

function parseRespFilters(c: Ctx): RespFilters {
  const out: RespFilters = {};
  // Manila-day window: bare dates → half-open UTC bounds (audit P2-7).
  const { fromUtc, toUtcExcl } = mnlWindow(qs(c, 'from'), qs(c, 'to'));
  const facility = qs(c, 'facility_id');
  const status = qs(c, 'status');
  const sp = qs(c, 'source_path');
  const q = qs(c, 'q');
  const limit = qInt(c, 'limit');
  const offset = qInt(c, 'offset');
  if (fromUtc) out.from = fromUtc;
  if (toUtcExcl) out.to = toUtcExcl;
  if (facility) out.facility_id = facility;
  if (status) out.status = status;
  if (sp) out.source_path = sp;
  if (q) out.q = q;
  if (limit !== undefined) out.limit = limit;
  if (offset !== undefined) out.offset = offset;
  return out;
}

function parseAuditFilters(c: Ctx): AuditFilters {
  const out: AuditFilters = {};
  const { fromUtc, toUtcExcl } = mnlWindow(qs(c, 'from'), qs(c, 'to'));
  const eventType = qs(c, 'event_type');
  const hcwId = qs(c, 'hcw_id');
  const actor = qs(c, 'actor_username');
  const q = qs(c, 'q');
  const limit = qInt(c, 'limit');
  const offset = qInt(c, 'offset');
  if (fromUtc) out.from = fromUtc;
  if (toUtcExcl) out.to = toUtcExcl;
  if (eventType) out.event_type = eventType;
  if (hcwId) out.hcw_id = hcwId;
  if (actor) out.actor_username = actor;
  if (q) out.q = q;
  if (limit !== undefined) out.limit = limit;
  if (offset !== undefined) out.offset = offset;
  return out;
}

function parseDlqFilters(c: Ctx): DlqFilters {
  const out: DlqFilters = {};
  const { fromUtc, toUtcExcl } = mnlWindow(qs(c, 'from'), qs(c, 'to'));
  const q = qs(c, 'q');
  const limit = qInt(c, 'limit');
  const offset = qInt(c, 'offset');
  if (fromUtc) out.from = fromUtc;
  if (toUtcExcl) out.to = toUtcExcl;
  if (q) out.q = q;
  if (limit !== undefined) out.limit = limit;
  if (offset !== undefined) out.offset = offset;
  return out;
}

function parseHcwFilters(c: Ctx): HcwFilters {
  const out: HcwFilters = {};
  // Manila-day created_at window (Data-tab filter bar, 2026-07-17) — same
  // half-open bounds as the responses/audit/dlq lists.
  const { fromUtc, toUtcExcl } = mnlWindow(qs(c, 'from'), qs(c, 'to'));
  const facility = qs(c, 'facility_id');
  const status = qs(c, 'status');
  const hcwId = qs(c, 'hcw_id');
  const q = qs(c, 'q');
  const limit = qInt(c, 'limit');
  const offset = qInt(c, 'offset');
  if (fromUtc) out.from = fromUtc;
  if (toUtcExcl) out.to = toUtcExcl;
  if (facility) out.facility_id = facility;
  if (status) out.status = status;
  if (hcwId) out.hcw_id = hcwId;
  if (q) out.q = q;
  if (limit !== undefined) out.limit = limit;
  if (offset !== undefined) out.offset = offset;
  return out;
}

/** Minimal Blob surface — avoids depending on DOM lib types. */
interface UploadedBlob {
  name?: string;
  size: number;
  type: string;
  arrayBuffer(): Promise<ArrayBuffer>;
}

interface AuditEntry {
  event_type: string;
  actor_username: string;
  actor_jti: string;
  actor_role: string;
  client_ip_hash: string;
  event_resource?: string;
  request_id?: string;
}

export function buildAdminApp(env: AdminEnv): Hono<Vars> {
  const admin = new Hono<Vars>();
  const roleCache = new RoleVersionCache();

  const rbacOpts = () => ({
    secret: env.jwtSigningKey,
    cache: roleCache,
    kv: { kvGet: (k: string) => env.adminStore.kvGet(k) },
    rolesListFn: async () => {
      try {
        const roles = await env.adminStore.listRoles();
        return { ok: true, data: { roles: roles as unknown as Role[] } };
      } catch {
        return { ok: false };
      }
    },
  });

  /** Fire-and-forget audit write — never delays or fails the user response. */
  const audit = (entry: AuditEntry): void => {
    void env.adminStore.writeAudit(entry).catch(() => undefined);
  };

  /** #327 parity: success-gated audit for mutation routes. */
  const auditMutation = (
    c: Ctx,
    res: Response,
    payload: AdminJwtPayload,
    eventType: string,
    resource: string,
  ): void => {
    if (res.status < 200 || res.status >= 300) return;
    audit({
      event_type: eventType,
      actor_username: payload.sub,
      actor_jti: payload.jti,
      actor_role: payload.role,
      client_ip_hash: ipHashOf(c),
      event_resource: resource,
      request_id: c.get('requestId'),
    });
  };

  type GateResult = { ok: true; payload: AdminJwtPayload } | { ok: false; res: Response };

  const gate = async (c: Ctx, perm: string): Promise<GateResult> => {
    const auth = await requirePerm(c.req.header('Authorization'), perm, rbacOpts());
    if (!auth.ok || !auth.payload) {
      return {
        ok: false,
        res: jsonAt(c, errBody(auth.errorCode ?? 'E_AUTH_INVALID', 'access denied'), auth.status ?? 401),
      };
    }
    return { ok: true, payload: auth.payload };
  };

  // Request-id + backend-failure envelope for every admin route.
  admin.use('*', async (c, next) => {
    const requestId = randomUUID();
    c.set('requestId', requestId);
    try {
      await next();
    } catch (err) {
      console.error('[admin]', requestId, err);
      c.res = jsonAt(c, errBody('E_BACKEND', 'backend unavailable'), 502);
    }
    c.res.headers.set('X-Request-Id', requestId);
  });

  // ----- auth ---------------------------------------------------------------

  admin.post('/login', async (c) => {
    const body = (await c.req.json().catch(() => ({}))) as { username?: unknown; password?: unknown };
    const username = typeof body.username === 'string' ? body.username.trim() : '';
    const password = typeof body.password === 'string' ? body.password : '';
    if (!username || !password) {
      return c.json(errBody('E_VALIDATION', 'username and password are required'), 400);
    }
    const ipHash = ipHashOf(c);

    const pre = await checkLoginThrottle(env.adminStore, username, ipHash);
    if (!pre.allowed) {
      const ra = retryAfterSeconds();
      c.header('Retry-After', String(ra));
      return c.json(errBody('E_AUTH_LOCKED', `Too many login attempts. Try again in ${ra}s.`), 429);
    }

    // Timing-equalized verify: unknown user still burns one PBKDF2 (parity).
    const user = await env.adminStore.getUserAuth(username);
    const stored = user ? user.password_hash : await getDummyPasswordHash();
    const ok = await verifyPassword(password, stored);
    if (!user || !ok) {
      await recordFailedLogin(env.adminStore, username, ipHash);
      return c.json(errBody('E_AUTH_INVALID', 'Invalid username or password'), 401);
    }

    const roles = await env.adminStore.listRoles();
    const role = roles.find((r) => r.name === user.role_name);
    if (!role) {
      return c.json(errBody('E_BACKEND', `Role "${user.role_name}" not found for user "${username}"`), 502);
    }

    const mustChange = isTruthy(user.password_must_change);
    const token = await mintAdminJwt(
      env.jwtSigningKey,
      { sub: username, role: role.name, role_version: role.version, ...(mustChange ? { pwc: true } : {}) },
      { ttl: JWT_TTL_SECONDS },
    );
    await resetLoginThrottle(env.adminStore, username);
    void env.adminStore.touchLastLogin(username, new Date().toISOString()).catch(() => undefined);

    const v = await verifyAdminJwt(env.jwtSigningKey, token);
    if (v.ok) {
      audit({
        event_type: 'admin_login',
        actor_username: username,
        actor_jti: v.payload.jti,
        actor_role: role.name,
        client_ip_hash: ipHash,
        request_id: c.get('requestId'),
      });
    }

    return c.json({
      token,
      role: role.name,
      role_version: role.version,
      expires_at: Math.floor(Date.now() / 1000) + JWT_TTL_SECONDS,
      password_must_change: mustChange,
      permissions: projectPermissions(role),
    });
  });

  admin.post('/logout', async (c) => {
    const m = /^Bearer (.+)$/.exec(c.req.header('Authorization') || '');
    if (!m) return c.json(errBody('E_AUTH_INVALID', 'Authorization header missing or malformed'), 401);
    const v = await verifyAdminJwt(env.jwtSigningKey, m[1]!);
    if (!v.ok) {
      const code = v.error === 'expired' ? 'E_AUTH_EXPIRED' : 'E_AUTH_INVALID';
      return c.json(errBody(code, 'Token invalid or expired'), 401);
    }
    const now = Math.floor(Date.now() / 1000);
    const ttl = Math.max(60, v.payload.exp - now + 60);
    await env.adminStore.kvPut(`revoked_jti:${v.payload.jti}`, '1', ttl);
    audit({
      event_type: 'admin_logout',
      actor_username: v.payload.sub,
      actor_jti: v.payload.jti,
      actor_role: v.payload.role,
      client_ip_hash: ipHashOf(c),
      request_id: c.get('requestId'),
    });
    return c.body(null, 204);
  });

  // R2-#134: user-self password rotation — JWT-only gate, no perm.
  admin.patch('/me/password', async (c) => {
    const m = /^Bearer (.+)$/.exec(c.req.header('Authorization') || '');
    if (!m) return c.json(errBody('E_AUTH_INVALID', 'Authorization header missing or malformed'), 401);
    const v = await verifyAdminJwt(env.jwtSigningKey, m[1]!);
    if (!v.ok) {
      const code = v.error === 'expired' ? 'E_AUTH_EXPIRED' : 'E_AUTH_INVALID';
      return c.json(errBody(code, 'Token invalid or expired'), 401);
    }

    const body = (await c.req.json().catch(() => ({}))) as {
      current_password?: unknown;
      new_password?: unknown;
    };
    const currentPw = typeof body.current_password === 'string' ? body.current_password : '';
    const newPw = typeof body.new_password === 'string' ? body.new_password : '';
    if (!currentPw || !newPw) {
      return c.json(errBody('E_VALIDATION', 'current_password and new_password are required'), 400);
    }
    if (newPw.length < 8) {
      return c.json(errBody('E_VALIDATION', 'new_password must be at least 8 characters'), 400);
    }
    if (newPw === currentPw) {
      return c.json(errBody('E_VALIDATION', 'new_password must differ from current_password'), 400);
    }

    const username = v.payload.sub;
    const user = await env.adminStore.getUserAuth(username);
    if (!user) return c.json(errBody('E_AUTH_INVALID', 'User no longer exists'), 401);
    const ok = await verifyPassword(currentPw, user.password_hash);
    if (!ok) return c.json(errBody('E_AUTH_INVALID', 'current_password does not match'), 401);

    const newHash = await hashPassword(newPw);
    await env.adminStore.replaceUser({ ...user, password_hash: newHash, password_must_change: false });

    // #340: invalidate all JWTs minted before this change; the fresh one passes.
    const revokeTs = Math.floor(Date.now() / 1000);
    await env.adminStore.kvPut(`revoked_user:${username}`, String(revokeTs), JWT_TTL_SECONDS + 60);

    const roles = await env.adminStore.listRoles();
    const role = roles.find((r) => r.name === v.payload.role);
    if (!role) {
      return c.json(errBody('E_BACKEND', `Role "${v.payload.role}" not found for user "${username}"`), 502);
    }
    const token = await mintAdminJwt(
      env.jwtSigningKey,
      { sub: username, role: role.name, role_version: role.version },
      { ttl: JWT_TTL_SECONDS },
    );
    const fresh = await verifyAdminJwt(env.jwtSigningKey, token);
    if (fresh.ok) {
      audit({
        event_type: 'admin_password_change',
        actor_username: username,
        actor_jti: fresh.payload.jti,
        actor_role: role.name,
        client_ip_hash: ipHashOf(c),
        request_id: c.get('requestId'),
      });
    }
    return c.json({
      token,
      role: role.name,
      role_version: role.version,
      expires_at: Math.floor(Date.now() / 1000) + JWT_TTL_SECONDS,
      password_must_change: false,
      permissions: projectPermissions(role),
    });
  });

  // ----- paper-encoder submit -------------------------------------------------

  admin.post('/encode/:hcwId', async (c) => {
    const g = await gate(c, 'dict_paper_encoded_up');
    if (!g.ok) return g.res;
    const hcwId = c.req.param('hcwId');
    if (!hcwId) return c.json(errBody('E_VALIDATION', 'hcw_id path param required'), 400);
    const body = (await c.req.json().catch(() => ({}))) as Record<string, unknown>;
    if (typeof body.client_submission_id !== 'string' || body.client_submission_id.length === 0) {
      return c.json(errBody('E_VALIDATION', 'client_submission_id required'), 400);
    }
    if (typeof body.spec_version !== 'string' || body.spec_version.length === 0) {
      return c.json(errBody('E_VALIDATION', 'spec_version required'), 400);
    }
    if (body.values == null || typeof body.values !== 'object' || Array.isArray(body.values)) {
      return c.json(errBody('E_VALIDATION', 'values must be a JSON object'), 400);
    }

    // AS adminEncodeSubmit parity: source_path/encoded_by/encoded_at are
    // force-injected; missing client clock falls back to server-now.
    const nowMs = Date.now();
    const enriched: Record<string, unknown> = {
      client_submission_id: body.client_submission_id,
      hcw_id: hcwId,
      spec_version: body.spec_version,
      app_version: body.app_version ?? '',
      submitted_at_client: body.submitted_at_client ?? nowMs,
      device_fingerprint: body.device_fingerprint ?? '',
      facility_id: body.facility_id ?? '',
      values: body.values,
      ...(typeof body.qn === 'string' && body.qn ? { qn: body.qn } : {}),
      source_path: 'paper_encoded',
      encoded_by: g.payload.sub,
      encoded_at: new Date(nowMs).toISOString(),
    };
    const r = await handleSubmit(enriched, env.store);
    const res = r.ok
      ? c.json(r.data)
      : jsonAt(c, errBody(r.error.code || 'E_BACKEND', r.error.message), 502);
    auditMutation(c, res, g.payload, 'admin_encode_submit', hcwId);
    return res;
  });

  // ----- data dashboards --------------------------------------------------------

  admin.get('/dashboards/data/responses', async (c) => {
    const g = await gate(c, 'dash_data');
    if (!g.ok) return g.res;
    return c.json(await env.adminStore.listResponses(parseRespFilters(c)));
  });

  admin.get('/dashboards/data/responses/:id', async (c) => {
    const g = await gate(c, 'dash_data');
    if (!g.ok) return g.res;
    const id = c.req.param('id');
    if (!id) return c.json(errBody('E_VALIDATION', 'submission id required'), 400);
    const row = await env.adminStore.getResponseById(id);
    if (!row) return c.json(errBody('E_NOT_FOUND', `submission ${id} not found`), 404);
    return c.json(row);
  });

  // #831: void a response — status flip + audit trail; never a hard delete.
  // The reason is required (it lands in the response_voided audit row).
  admin.post('/dashboards/data/responses/:id/void', async (c) => {
    const g = await gate(c, 'dash_data');
    if (!g.ok) return g.res;
    const id = c.req.param('id');
    if (!id) return c.json(errBody('E_VALIDATION', 'submission id required'), 400);
    const body = (await c.req.json().catch(() => ({}))) as { reason?: unknown };
    const reason = typeof body.reason === 'string' ? body.reason.trim() : '';
    if (!reason) return c.json(errBody('E_VALIDATION', 'reason required'), 400);
    const r = await env.adminStore.voidResponse(id, reason);
    const res = r.ok
      ? c.json({ submission_id: r.submission_id, status: 'voided', prev_status: r.prev_status })
      : r.code === 'E_NOT_FOUND'
        ? c.json(errBody('E_NOT_FOUND', `submission ${id} not found`), 404)
        : c.json(errBody('E_ALREADY_VOIDED', `submission ${id} is already voided`), 409);
    auditMutation(c, res, g.payload, 'admin_void_response', id);
    return res;
  });

  admin.get('/dashboards/data/audit', async (c) => {
    const g = await gate(c, 'dash_data');
    if (!g.ok) return g.res;
    return c.json(await env.adminStore.listAudit(parseAuditFilters(c)));
  });

  admin.get('/dashboards/data/dlq', async (c) => {
    const g = await gate(c, 'dash_data');
    if (!g.ok) return g.res;
    return c.json(await env.adminStore.listDlq(parseDlqFilters(c)));
  });

  // #297/R2-#84: DLQ replay + delete. Failure status is ALWAYS 502 with the
  // underlying code (Worker handleDlqMutation parity).
  admin.post('/dashboards/data/dlq/:dlqId/replay', async (c) => {
    const g = await gate(c, 'dash_data');
    if (!g.ok) return g.res;
    const dlqId = c.req.param('dlqId');
    let res: Response;
    const row = await env.adminStore.dlqFind(dlqId);
    if (!row) {
      res = jsonAt(c, errBody('E_NOT_FOUND', `DLQ row not found: ${dlqId}`), 502);
    } else {
      let parsed: unknown;
      let parseError: string | null = null;
      try {
        parsed = JSON.parse(row.payload_json);
      } catch (e) {
        parseError = e instanceof Error ? e.message : String(e);
      }
      if (parseError !== null) {
        res = jsonAt(c, errBody('E_DLQ_CORRUPT', `DLQ payload_json is not valid JSON: ${parseError}`), 502);
      } else {
        const r = await handleSubmit(parsed, env.store);
        if (!r.ok) {
          res = jsonAt(c, errBody(r.error.code || 'E_BACKEND', r.error.message), 502);
        } else {
          await env.adminStore.dlqDelete(dlqId);
          const d = r.data as { submission_id?: string };
          res = c.json({ submission_id: d.submission_id ?? null, status: 'replayed', dlq_id: dlqId });
        }
      }
    }
    auditMutation(c, res, g.payload, 'admin_dlq_replay', dlqId);
    return res;
  });

  admin.delete('/dashboards/data/dlq/:dlqId', async (c) => {
    const g = await gate(c, 'dash_data');
    if (!g.ok) return g.res;
    const dlqId = c.req.param('dlqId');
    const deleted = await env.adminStore.dlqDelete(dlqId);
    const res = deleted
      ? c.json({ dlq_id: dlqId, status: 'deleted' })
      : jsonAt(c, errBody('E_NOT_FOUND', `DLQ row not found: ${dlqId}`), 502);
    auditMutation(c, res, g.payload, 'admin_dlq_delete', dlqId);
    return res;
  });

  admin.get('/dashboards/data/hcws', async (c) => {
    const g = await gate(c, 'dash_data');
    if (!g.ok) return g.res;
    return c.json(await env.adminStore.listHcws(parseHcwFilters(c)));
  });

  // Distinct audit event types for the Audit tab's dropdown (2026-07-17).
  // Derived from the data itself so the list never drifts from reality.
  admin.get('/dashboards/data/audit-event-types', async (c) => {
    const g = await gate(c, 'dash_data');
    if (!g.ok) return g.res;
    const rows = await env.adminStore.listAuditEventTypes();
    return c.json({ rows, total: rows.length });
  });

  // Facility options for the Data-tab filter dropdowns (2026-07-17): id + name
  // of every non-archived master row. Gated dash_data — the composite
  // /admin/api/facilities list is dash_users, which a data-only operator may
  // lack. Same source as the PWA's facility picker (readFacilities already
  // filters archived=0).
  admin.get('/dashboards/data/facility-options', async (c) => {
    const g = await gate(c, 'dash_data');
    if (!g.ok) return g.res;
    const rows = (await env.store.readFacilities())
      .map((f) => ({ facility_id: f.facility_id, facility_name: f.facility_name }))
      .sort((a, b) => a.facility_name.localeCompare(b.facility_name));
    return c.json({ rows, total: rows.length });
  });

  // ----- reports ------------------------------------------------------------------

  // Coverage report (spec F2-Coverage-Report-2026-07-17) — replaces /report/sync.
  admin.get('/dashboards/report/coverage', async (c) => {
    const g = await gate(c, 'dash_report');
    if (!g.ok) return g.res;
    const lvl = c.req.query('level');
    const level: CoverageLevel =
      lvl === 'province' || lvl === 'facility' ? lvl : 'region';
    const { fromUtc, toUtcExcl } = mnlWindow(qs(c, 'from'), qs(c, 'to'));
    return c.json(
      await env.adminStore.coverageReport({
        level,
        ...(fromUtc ? { from: fromUtc } : {}),
        ...(toUtcExcl ? { to: toUtcExcl } : {}),
        ...(c.req.query('include_archived') === 'true' ? { include_archived: true } : {}),
      }),
    );
  });

  admin.get('/dashboards/report/map', async (c) => {
    const g = await gate(c, 'dash_report');
    if (!g.ok) return g.res;
    const filters: { from?: string; to?: string; region_id?: string; province_id?: string } = {};
    const { fromUtc, toUtcExcl } = mnlWindow(qs(c, 'from'), qs(c, 'to'));
    const region = qs(c, 'region_id');
    const province = qs(c, 'province_id');
    if (fromUtc) filters.from = fromUtc;
    if (toUtcExcl) filters.to = toUtcExcl;
    if (region) filters.region_id = region;
    if (province) filters.province_id = province;
    return c.json(mapReport(await env.adminStore.readResponsesLite(), filters));
  });

  // ----- apps: version / kill-switch / broadcast --------------------------------------
  // The Apps Script quota gauge was removed 2026-07-17 (Apps-tab audit P1-2):
  // nothing on the VPS stack writes the counter and the 20k cap doesn't exist here.

  admin.get('/dashboards/apps/version', async (c) => {
    const g = await gate(c, 'dash_apps');
    if (!g.ok) return g.res;
    // Degrade gracefully if the DB read fails — the status panel should
    // still show build identifiers.
    let revisions: ReturnType<typeof formRevisions> = { revisions: [], total: 0 };
    try {
      revisions = formRevisions(await env.adminStore.readResponsesLite());
    } catch {
      /* degrade */
    }
    return c.json({
      pwa_version: env.pwaVersion || 'unknown',
      pwa_build_sha: env.pwaBuildSha || 'unknown',
      api_version: env.apiVersion || 'unknown',
      form_revisions: revisions.revisions,
      total_submissions: revisions.total,
      api_deployed_at: env.apiDeployedAt || null,
    });
  });

  admin.get('/dashboards/apps/kill-switch', async (c) => {
    const g = await gate(c, 'dash_apps');
    if (!g.ok) return g.res;
    const v = await env.store.getConfig('kill_switch');
    return c.json({ kill_switch: v === 'true' });
  });

  admin.patch('/dashboards/apps/kill-switch', async (c) => {
    const g = await gate(c, 'dash_apps');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as { kill_switch?: unknown };
    if (typeof body.kill_switch !== 'boolean') {
      return c.json(errBody('E_VALIDATION', 'kill_switch must be a boolean'), 400);
    }
    const okSet = await env.adminStore.setConfig('kill_switch', body.kill_switch ? 'true' : 'false');
    const res = okSet
      ? c.json({ kill_switch: body.kill_switch })
      : jsonAt(c, errBody('E_NOT_FOUND', 'Config key not found: kill_switch'), 502);
    auditMutation(c, res, g.payload, 'admin_kill_switch_set', 'kill_switch');
    return res;
  });

  admin.get('/dashboards/apps/broadcast', async (c) => {
    const g = await gate(c, 'dash_apps');
    if (!g.ok) return g.res;
    return c.json({ broadcast_message: await env.store.getConfig('broadcast_message') });
  });

  admin.patch('/dashboards/apps/broadcast', async (c) => {
    const g = await gate(c, 'dash_apps');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as { broadcast_message?: unknown };
    if (typeof body.broadcast_message !== 'string') {
      return c.json(errBody('E_VALIDATION', 'broadcast_message must be a string'), 400);
    }
    const value = body.broadcast_message.trim();
    if (value.length > BROADCAST_MAX_LEN) {
      return c.json(
        errBody('E_VALIDATION', `broadcast_message must be ${BROADCAST_MAX_LEN} characters or fewer`),
        400,
      );
    }
    const okSet = await env.adminStore.setConfig('broadcast_message', value);
    const res = okSet
      ? c.json({ broadcast_message: value })
      : jsonAt(c, errBody('E_NOT_FOUND', 'Config key not found: broadcast_message'), 502);
    auditMutation(c, res, g.payload, 'admin_broadcast_set', 'broadcast_message');
    return res;
  });

  // ----- apps: files (R2 → FileStore on F2_FILES_DIR) --------------------------------

  admin.get('/dashboards/apps/files', async (c) => {
    const g = await gate(c, 'dash_apps');
    if (!g.ok) return g.res;
    const filters: { q?: string; path?: string } = {};
    const q = qs(c, 'q');
    const path = qs(c, 'path');
    if (q) filters.q = q;
    if (path) filters.path = path;
    return c.json(await env.adminStore.listFiles(filters));
  });

  admin.post('/dashboards/apps/files', async (c) => {
    const g = await gate(c, 'dash_apps');
    if (!g.ok) return g.res;
    const ct = c.req.header('content-type') || '';
    if (!ct.toLowerCase().startsWith('multipart/form-data')) {
      return c.json(errBody('E_VALIDATION', 'multipart/form-data body required'), 400);
    }
    let form: FormData;
    try {
      form = await c.req.formData();
    } catch {
      return c.json(errBody('E_VALIDATION', 'request body is not valid multipart/form-data'), 400);
    }
    const fileEntry = form.get('file');
    if (fileEntry === null || typeof fileEntry === 'string') {
      return c.json(errBody('E_VALIDATION', '"file" form field required'), 400);
    }
    const file = fileEntry as unknown as UploadedBlob;
    if (file.size > MAX_FILE_BYTES) {
      return c.json(errBody('E_VALIDATION', `file exceeds ${MAX_FILE_BYTES} byte cap`), 413);
    }
    const mime = file.type || 'application/octet-stream';
    if (!ALLOWED_MIME.has(mime)) {
      return c.json(errBody('E_VALIDATION', `MIME type ${mime} not allowed`), 400);
    }
    // Audit P3-1: octet-stream is in ALLOWED_MIME (browsers report it for
    // anything they can't type), so the extension allowlist is the real
    // gate — enforce it on upload, not just rename.
    if (!validFileExtension(file.name ?? '')) {
      return c.json(
        errBody('E_VALIDATION', 'file extension not allowed (pdf, zip, png, jpg, jpeg, gif)'),
        400,
      );
    }
    const descriptionEntry = form.get('description');
    const description = typeof descriptionEntry === 'string' ? descriptionEntry : '';
    // #174: validate the destination folder path rather than silently
    // misfiling the upload at root.
    const rawPathEntry = form.get('path');
    const rawPath = typeof rawPathEntry === 'string' ? rawPathEntry.trim() : '';
    let folderPath = '/';
    if (rawPath && rawPath !== '/') {
      const seg = rawPath.startsWith('/') ? rawPath.slice(1) : rawPath;
      if (!FOLDER_NAME_RE.test(seg)) {
        return c.json(errBody('E_VALIDATION', 'invalid upload folder path'), 400);
      }
      folderPath = `/${seg}`;
    }

    const fileId = randomUUID();
    const safeName = sanitizeFilename(file.name ?? 'upload');
    const uploadedAt = new Date().toISOString();
    await env.fileStore.put(fileId, new Uint8Array(await file.arrayBuffer()));

    const rec: FileMetaRecord = {
      file_id: fileId,
      filename: safeName,
      content_type: mime,
      size_bytes: file.size,
      uploaded_by: g.payload.sub,
      uploaded_at: uploadedAt,
      description,
      deleted_at: '',
      folder_path: folderPath,
      is_folder: false,
    };
    const outcome = await env.adminStore.insertFileMeta(rec);
    if (outcome === 'conflict') {
      await env.fileStore.delete(fileId).catch(() => undefined);
      return jsonAt(c, errBody('E_CONFLICT', 'file_id already exists'), 409);
    }
    const res = c.json({ file: rec }, 201);
    auditMutation(c, res, g.payload, 'admin_files_create', safeName);
    return res;
  });

  // #174: folder create — registered before the :fileId routes.
  admin.post('/dashboards/apps/files/folders', async (c) => {
    const g = await gate(c, 'dash_apps');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as { name?: unknown };
    const name = typeof body.name === 'string' ? body.name.trim() : '';
    if (!FOLDER_NAME_RE.test(name)) {
      return c.json(
        errBody('E_VALIDATION', 'invalid folder name (letters, digits, space, . _ - ; no slashes or ..)'),
        400,
      );
    }
    if (await env.adminStore.folderExists(name)) {
      return c.json(errBody('E_CONFLICT', 'folder already exists'), 409);
    }
    const rec: FileMetaRecord = {
      file_id: randomUUID(),
      filename: name,
      content_type: 'application/x-directory',
      size_bytes: 0,
      uploaded_by: g.payload.sub,
      uploaded_at: new Date().toISOString(),
      description: '',
      deleted_at: '',
      folder_path: '/',
      is_folder: true,
    };
    await env.adminStore.insertFileMeta(rec);
    const res = c.json({ folder: rec }, 201);
    auditMutation(c, res, g.payload, 'admin_files_create_folder', name);
    return res;
  });

  admin.get('/dashboards/apps/files/:fileId', async (c) => {
    const g = await gate(c, 'dash_apps');
    if (!g.ok) return g.res;
    const fileId = c.req.param('fileId');
    if (!fileId) return c.json(errBody('E_VALIDATION', 'file_id required'), 400);
    const meta = await env.adminStore.getFileMeta(fileId);
    if (!meta) return c.json(errBody('E_NOT_FOUND', `file ${fileId} not found`), 404);
    if (meta.deleted_at) return c.json(errBody('E_NOT_FOUND', 'file deleted'), 404);
    const bytes = await env.fileStore.get(fileId);
    if (!bytes) return c.json(errBody('E_NOT_FOUND', 'file bytes not found in storage'), 404);
    const safeName = sanitizeFilename(meta.filename);
    const ab = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
    return c.body(ab, 200, {
      'Content-Type': meta.content_type || 'application/octet-stream',
      'Content-Disposition': `attachment; filename="${safeName}"`,
    });
  });

  // #175: rename — display name only; file_id (storage key) never changes.
  admin.patch('/dashboards/apps/files/:fileId', async (c) => {
    const g = await gate(c, 'dash_apps');
    if (!g.ok) return g.res;
    const fileId = c.req.param('fileId');
    if (!FILE_ID_RE.test(fileId)) {
      return c.json(errBody('E_VALIDATION', 'invalid file_id path param'), 400);
    }
    const body = (await c.req.json().catch(() => ({}))) as { filename?: unknown };
    const filename = typeof body.filename === 'string' ? body.filename.trim() : '';
    if (!filename) return c.json(errBody('E_VALIDATION', '"filename" is required'), 400);
    if (filename.includes('/') || filename.includes('\\') || filename.includes('..')) {
      return c.json(errBody('E_VALIDATION', 'new_name cannot contain path separators or ..'), 400);
    }
    if (!validFileExtension(filename)) {
      return c.json(errBody('E_VALIDATION', 'new_name extension not allowed (pdf, zip, png, jpg, jpeg, gif)'), 400);
    }
    const meta = await env.adminStore.getFileMeta(fileId);
    if (!meta || meta.deleted_at) {
      return c.json(errBody('E_NOT_FOUND', `file ${fileId} not found`), 404);
    }
    if (meta.is_folder) {
      return c.json(errBody('E_VALIDATION', 'folders cannot be renamed'), 400);
    }
    await env.adminStore.updateFilename(fileId, filename);
    const res = c.json({ file: { ...meta, filename } });
    auditMutation(c, res, g.payload, 'admin_files_rename', fileId);
    return res;
  });

  admin.delete('/dashboards/apps/files/:fileId', async (c) => {
    const g = await gate(c, 'dash_apps');
    if (!g.ok) return g.res;
    const fileId = c.req.param('fileId');
    if (!fileId) return c.json(errBody('E_VALIDATION', 'file_id required'), 400);
    const meta = await env.adminStore.getFileMeta(fileId);
    let res: Response;
    if (!meta) {
      res = c.json(errBody('E_NOT_FOUND', `file ${fileId} not found`), 404);
    } else if (meta.deleted_at) {
      res = c.json(errBody('E_NOT_FOUND', `file ${fileId} already deleted`), 404);
    } else {
      await env.adminStore.softDeleteFile(fileId);
      // Best-effort byte purge — metadata is the system of record (parity).
      await env.fileStore.delete(fileId).catch(() => undefined);
      res = c.body(null, 204);
    }
    auditMutation(c, res, g.payload, 'admin_files_delete', fileId);
    return res;
  });

  // ----- users --------------------------------------------------------------------

  admin.get('/dashboards/users', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const filters: { role_name?: string; username?: string; q?: string } = {};
    const role = qs(c, 'role_name');
    const uname = qs(c, 'username');
    const q = qs(c, 'q');
    if (role) filters.role_name = role;
    if (uname) filters.username = uname;
    if (q) filters.q = q;
    const users = await env.adminStore.listUsers(filters);
    return c.json({ users: users.map(toPublicUser), total: users.length });
  });

  /** AS adminUsersCreate parity (validation + conflict), used by create + bulk. */
  const createUserRecord = async (payload: {
    username: string;
    password_hash: string;
    role_name: string;
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
    password_must_change: boolean;
    created_by: string;
  }): Promise<{ ok: true; user: ReturnType<typeof toPublicUser> } | { ok: false; code: string; message: string }> => {
    if (!USERNAME_RE.test(payload.username)) {
      return { ok: false, code: 'E_VALIDATION', message: 'username must be 3-32 chars [A-Za-z0-9_]' };
    }
    if (!payload.password_hash) {
      return { ok: false, code: 'E_VALIDATION', message: 'password_hash required (worker should pre-hash)' };
    }
    if (!payload.role_name) {
      return { ok: false, code: 'E_VALIDATION', message: 'role_name required' };
    }
    if (payload.first_name && !NAME_RE.test(payload.first_name)) {
      return { ok: false, code: 'E_VALIDATION', message: 'first_name must be letters' };
    }
    if (payload.last_name && !NAME_RE.test(payload.last_name)) {
      return { ok: false, code: 'E_VALIDATION', message: 'last_name must be letters' };
    }
    const rec: AdminUserRecord = {
      username: payload.username,
      first_name: payload.first_name,
      last_name: payload.last_name,
      role_name: payload.role_name,
      password_hash: payload.password_hash,
      password_must_change: payload.password_must_change,
      email: payload.email,
      phone: payload.phone,
      created_at: new Date().toISOString(),
      created_by: payload.created_by,
      last_login_at: '',
    };
    const outcome = await env.adminStore.insertUser(rec);
    if (outcome === 'conflict') {
      return { ok: false, code: 'E_CONFLICT', message: 'username already exists' };
    }
    return { ok: true, user: toPublicUser(rec) };
  };

  // R2-#98: bulk import — registered before by-name routes for clarity.
  admin.post('/dashboards/users/bulk-import', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as { rows?: unknown };
    if (!body || !Array.isArray(body.rows)) {
      return c.json(errBody('E_VALIDATION', 'body.rows must be an array'), 400);
    }
    if (body.rows.length === 0) {
      return c.json(errBody('E_VALIDATION', 'rows must not be empty'), 400);
    }
    if (body.rows.length > 100) {
      return c.json(errBody('E_VALIDATION', 'max 100 rows per bulk import'), 400);
    }

    type ResultRow = { username: string; status: 'created' | 'rejected'; error?: { code: string; message: string } };
    const results: Array<ResultRow | undefined> = new Array<ResultRow | undefined>(body.rows.length);
    const toHash: Array<{ idx: number; row: { username: string; password: string; role_name: string; first_name: string; last_name: string; email: string; phone: string } }> = [];

    body.rows.forEach((raw, idx) => {
      const r = (raw ?? {}) as Record<string, unknown>;
      const row = {
        username: typeof r.username === 'string' ? r.username.trim() : '',
        password: typeof r.password === 'string' ? r.password : '',
        role_name: typeof r.role_name === 'string' ? r.role_name.trim() : '',
        first_name: typeof r.first_name === 'string' ? r.first_name.trim() : '',
        last_name: typeof r.last_name === 'string' ? r.last_name.trim() : '',
        email: typeof r.email === 'string' ? r.email.trim() : '',
        phone: typeof r.phone === 'string' ? r.phone.trim() : '',
      };
      if (!USERNAME_RE.test(row.username)) {
        results[idx] = {
          username: row.username,
          status: 'rejected',
          error: { code: 'E_VALIDATION', message: 'username must be 3-32 chars [A-Za-z0-9_]' },
        };
        return;
      }
      if (row.password.length < 8) {
        results[idx] = {
          username: row.username,
          status: 'rejected',
          error: { code: 'E_VALIDATION', message: 'password must be at least 8 characters' },
        };
        return;
      }
      if (!row.role_name) {
        results[idx] = {
          username: row.username,
          status: 'rejected',
          error: { code: 'E_VALIDATION', message: 'role_name required' },
        };
        return;
      }
      toHash.push({ idx, row });
    });

    const hashed = await Promise.all(
      toHash.map(async ({ idx, row }) => ({
        idx,
        payload: {
          username: row.username,
          password_hash: await hashPassword(row.password),
          role_name: row.role_name,
          first_name: row.first_name,
          last_name: row.last_name,
          email: row.email,
          phone: row.phone,
          password_must_change: true,
          created_by: g.payload.sub,
        },
      })),
    );

    let created = 0;
    let rejected = results.filter((r) => r != null).length;
    for (const { idx, payload } of hashed) {
      const r = await createUserRecord(payload);
      if (r.ok) {
        created++;
        results[idx] = { username: payload.username, status: 'created' };
      } else {
        rejected++;
        results[idx] = {
          username: payload.username,
          status: 'rejected',
          error: { code: r.code, message: r.message },
        };
      }
    }

    const merged = results.map(
      (r, idx) =>
        r ?? {
          username: String(((body.rows as Record<string, unknown>[])[idx] ?? {}).username ?? ''),
          status: 'rejected' as const,
          error: { code: 'E_INTERNAL', message: 'Server returned no result for this row' },
        },
    );
    const res = c.json({ results: merged, total: body.rows.length, created, rejected });
    auditMutation(c, res, g.payload, 'admin_users_bulk_import', '');
    return res;
  });

  admin.post('/dashboards/users', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as Record<string, unknown>;
    const username = typeof body.username === 'string' ? body.username.trim() : '';
    const password = typeof body.password === 'string' ? body.password : '';
    const roleName = typeof body.role_name === 'string' ? body.role_name.trim() : '';
    if (!USERNAME_RE.test(username)) {
      return c.json(errBody('E_VALIDATION', 'username must be 3-32 chars [A-Za-z0-9_]'), 400);
    }
    if (password.length < 8) {
      return c.json(errBody('E_VALIDATION', 'password must be at least 8 characters'), 400);
    }
    if (!roleName) {
      return c.json(errBody('E_VALIDATION', 'role_name required'), 400);
    }
    const r = await createUserRecord({
      username,
      password_hash: await hashPassword(password),
      role_name: roleName,
      first_name: typeof body.first_name === 'string' ? body.first_name.trim() : '',
      last_name: typeof body.last_name === 'string' ? body.last_name.trim() : '',
      email: typeof body.email === 'string' ? body.email.trim() : '',
      phone: typeof body.phone === 'string' ? body.phone.trim() : '',
      password_must_change: true,
      created_by: g.payload.sub,
    });
    const res = r.ok
      ? c.json({ user: r.user })
      : jsonAt(c, errBody(r.code, r.message), statusForAsError(r.code));
    auditMutation(c, res, g.payload, 'admin_users_create', username);
    return res;
  });

  admin.post('/dashboards/users/:username/revoke-sessions', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const username = c.req.param('username');
    let res: Response;
    if (!USERNAME_RE.test(username)) {
      res = c.json(errBody('E_VALIDATION', 'invalid username path param'), 400);
    } else {
      await env.adminStore.kvPut(`revoked_user:${username}`, String(Math.floor(Date.now() / 1000)), 24 * 3600);
      res = c.body(null, 204);
    }
    // Worker parity: this audit row is fired unconditionally after the handler.
    audit({
      event_type: 'admin_revoke_sessions',
      actor_username: g.payload.sub,
      actor_jti: g.payload.jti,
      actor_role: g.payload.role,
      client_ip_hash: ipHashOf(c),
      event_resource: username,
      request_id: c.get('requestId'),
    });
    return res;
  });

  admin.patch('/dashboards/users/:username', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const username = c.req.param('username');
    if (!USERNAME_RE.test(username)) {
      return c.json(errBody('E_VALIDATION', 'invalid username path param'), 400);
    }
    const body = (await c.req.json().catch(() => ({}))) as Record<string, unknown>;
    const fields: Partial<AdminUserRecord> = {};
    if (typeof body.first_name === 'string') fields.first_name = body.first_name.trim();
    if (typeof body.last_name === 'string') fields.last_name = body.last_name.trim();
    if (typeof body.role_name === 'string') fields.role_name = body.role_name.trim();
    if (typeof body.email === 'string') fields.email = body.email.trim();
    if (typeof body.phone === 'string') fields.phone = body.phone.trim();
    if (typeof body.password_must_change === 'boolean') fields.password_must_change = body.password_must_change;
    if (typeof body.password === 'string' && body.password.length > 0) {
      if (body.password.length < 8) {
        return c.json(errBody('E_VALIDATION', 'password must be at least 8 characters'), 400);
      }
      fields.password_hash = await hashPassword(body.password);
      // Admin-initiated reset forces rotation on next login (parity).
      fields.password_must_change = true;
    }
    const existing = await env.adminStore.getUserAuth(username);
    if (!existing) return c.json(errBody('E_NOT_FOUND', `user ${username} not found`), 404);
    const updated: AdminUserRecord = { ...existing, ...fields };
    await env.adminStore.replaceUser(updated);
    const res = c.json({ user: toPublicUser(updated) });
    auditMutation(c, res, g.payload, 'admin_users_update', username);
    return res;
  });

  admin.delete('/dashboards/users/:username', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const username = c.req.param('username');
    if (!USERNAME_RE.test(username)) {
      return c.json(errBody('E_VALIDATION', 'invalid username path param'), 400);
    }
    // R2-#133: self-delete guard + last-Administrator orphan guard.
    if (username === g.payload.sub) {
      return c.json(errBody('E_CONFLICT', 'cannot delete your own account'), 409);
    }
    const existing = await env.adminStore.getUserAuth(username);
    if (!existing) return c.json(errBody('E_NOT_FOUND', `user ${username} not found`), 404);
    if (existing.role_name === 'Administrator' && (await env.adminStore.countUsersWithRole('Administrator')) <= 1) {
      return c.json(errBody('E_CONFLICT', 'cannot orphan the last Administrator'), 409);
    }
    await env.adminStore.deleteUser(username);
    const res = c.body(null, 204);
    auditMutation(c, res, g.payload, 'admin_users_delete', username);
    return res;
  });

  // ----- roles --------------------------------------------------------------------

  admin.get('/dashboards/roles', async (c) => {
    const g = await gate(c, 'dash_roles');
    if (!g.ok) return g.res;
    const roles = await env.adminStore.listRoles();
    return c.json({ roles, total: roles.length });
  });

  const permBools = (body: Record<string, unknown>): Partial<Record<PermKey, boolean>> => {
    const out: Partial<Record<PermKey, boolean>> = {};
    for (const k of PERM_KEYS) {
      const v = body[k];
      if (typeof v === 'boolean') out[k] = v;
    }
    return out;
  };

  admin.post('/dashboards/roles', async (c) => {
    const g = await gate(c, 'dash_roles');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as Record<string, unknown>;
    const name = typeof body.name === 'string' ? body.name.trim() : '';
    if (!ROLE_NAME_RE.test(name)) {
      return c.json(errBody('E_VALIDATION', 'role name must start with a letter; up to 64 chars [A-Za-z0-9 _-]'), 400);
    }
    const perms = permBools(body);
    if (!PERM_KEYS.some((k) => perms[k] === true)) {
      return c.json(errBody('E_VALIDATION', 'at least one permission must be granted'), 400);
    }
    const rec = {
      name,
      is_builtin: false,
      version: 1,
      created_at: new Date().toISOString(),
      created_by: g.payload.sub,
      ...Object.fromEntries(PERM_KEYS.map((k) => [k, perms[k] === true])),
    } as AdminRoleRecord;
    const outcome = await env.adminStore.insertRole(rec);
    const res =
      outcome === 'conflict'
        ? jsonAt(c, errBody('E_CONFLICT', 'role name already exists'), 409)
        : c.json({ role: rec });
    auditMutation(c, res, g.payload, 'admin_roles_create', name);
    return res;
  });

  admin.patch('/dashboards/roles/:name', async (c) => {
    const g = await gate(c, 'dash_roles');
    if (!g.ok) return g.res;
    const name = c.req.param('name');
    if (!ROLE_NAME_RE.test(name)) {
      return c.json(errBody('E_VALIDATION', 'invalid role name path param'), 400);
    }
    const body = (await c.req.json().catch(() => ({}))) as Record<string, unknown>;
    const role = await env.adminStore.getRole(name);
    if (!role) return c.json(errBody('E_NOT_FOUND', `role ${name} not found`), 404);
    const perms = permBools(body);
    const updated: AdminRoleRecord = { ...role };
    let changed = false;
    for (const k of PERM_KEYS) {
      const v = perms[k];
      if (v !== undefined && v !== updated[k]) {
        updated[k] = v;
        changed = true;
      }
    }
    // Version bump on change invalidates every JWT minted under the prior
    // version (rbac role_version comparison) — AS adminRolesUpdate parity.
    if (changed) updated.version = (Number(updated.version) || 0) + 1;
    await env.adminStore.replaceRole(updated);
    roleCache.invalidate(name);
    const res = c.json({ role: updated, changed });
    auditMutation(c, res, g.payload, 'admin_roles_update', name);
    return res;
  });

  admin.delete('/dashboards/roles/:name', async (c) => {
    const g = await gate(c, 'dash_roles');
    if (!g.ok) return g.res;
    const name = c.req.param('name');
    if (!ROLE_NAME_RE.test(name)) {
      return c.json(errBody('E_VALIDATION', 'invalid role name path param'), 400);
    }
    const role = await env.adminStore.getRole(name);
    let res: Response;
    if (!role) {
      res = c.json(errBody('E_NOT_FOUND', `role ${name} not found`), 404);
    } else if (role.is_builtin) {
      res = c.json(errBody('E_VALIDATION', 'built-in roles cannot be deleted'), 400);
    } else if ((await env.adminStore.countUsersWithRole(name)) > 0) {
      res = c.json(errBody('E_CONFLICT', 'role still assigned to one or more users'), 409);
    } else {
      await env.adminStore.deleteRoleRow(name);
      roleCache.invalidate(name);
      res = c.body(null, 204);
    }
    auditMutation(c, res, g.payload, 'admin_roles_delete', name);
    return res;
  });

  // ----- HCWs (create + reissue) -----------------------------------------------------

  // R2-#58: first-class Create HCW. dash_users gate (same as reissue).
  admin.post('/hcws', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as Record<string, unknown>;
    const hcwId = typeof body.hcw_id === 'string' ? body.hcw_id.trim() : '';
    const facilityId = typeof body.facility_id === 'string' ? body.facility_id.trim() : '';
    const facilityName = typeof body.facility_name === 'string' ? body.facility_name.trim() : '';
    const qn = typeof body.qn === 'string' ? body.qn.trim() : '';
    if (!HCW_ID_RE.test(hcwId)) {
      return c.json(errBody('E_VALIDATION', 'hcw_id must be 1-64 chars [A-Za-z0-9_-]'), 400);
    }
    if (!FACILITY_ID_RE.test(facilityId)) {
      return c.json(errBody('E_VALIDATION', 'facility_id must be 1-32 chars [A-Za-z0-9_-]'), 400);
    }
    if (qn && !/^\d{12}$/.test(qn)) {
      return c.json(errBody('E_VALIDATION', 'qn must be exactly 12 digits when provided'), 400);
    }
    // status forced to 'pending' — provisioning lifecycle Create → Reissue → enrolled.
    const r = await env.adminStore.createHcw({
      hcw_id: hcwId,
      facility_id: facilityId,
      facility_name: facilityName,
      status: 'pending',
      qn,
    });
    if (!r.ok) {
      return jsonAt(c, errBody(r.code, r.message), statusForAsError(r.code));
    }
    const res = c.json({ hcw_id: r.hcw_id, facility_id: facilityId, qn: r.qn ?? '', status: 'pending' }, 201);
    auditMutation(c, res, g.payload, 'admin_hcws_create', hcwId);
    return res;
  });

  // Reissue: CAS the row FIRST, mint ONLY on success (issuance-order invariant).
  admin.post('/hcws/:hcwId/reissue-token', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const hcwId = c.req.param('hcwId');
    const body = (await c.req.json().catch(() => ({}))) as { prev_jti?: unknown; ttl_days?: unknown };
    let res: Response;
    if (!hcwId) {
      res = c.json(errBody('E_VALIDATION', 'hcw_id required'), 400);
    } else {
      const prevJti = typeof body.prev_jti === 'string' ? body.prev_jti : '';
      const ttlDays =
        typeof body.ttl_days === 'number' && body.ttl_days >= 1 && body.ttl_days <= 365 ? body.ttl_days : 30;
      const newJti = randomUUID();

      const cas = await env.adminStore.reissueHcwToken({ hcw_id: hcwId, new_jti: newJti, prev_jti: prevJti });
      if (!cas.ok) {
        res = jsonAt(c, errBody(cas.code, cas.message), statusForAsError(cas.code));
      } else {
        const nowS = Math.floor(Date.now() / 1000);
        const exp = nowS + ttlDays * 86400;
        const claims: JwtClaims = {
          jti: newJti,
          tablet_id: randomUUID(),
          facility_id: cas.facility_id || '',
          iat: nowS,
          exp,
          // Bind the enrollment-assigned QN into the device token so
          // /verify-token surfaces it with no extra round-trip.
          ...(cas.qn ? { qn: cas.qn } : {}),
        };
        const token = await mintJwt(claims, env.jwtSigningKey);
        await env.adminStore.tokenAudit({
          jti: newJti,
          tablet_id: claims.tablet_id,
          tablet_label: 'reissued for ' + hcwId,
          facility_id: cas.facility_id || '',
          issued_at: nowS,
          expires_at: exp,
        });
        const enrollUrl = `${env.pwaOrigin}/enroll?token=${encodeURIComponent(token)}`;
        res = c.json({
          hcw_id: hcwId,
          facility_id: cas.facility_id || '',
          qn: cas.qn || '',
          old_jti: cas.old_jti,
          new_token: token,
          new_jti: newJti,
          expires_at: exp,
          enroll_url: enrollUrl,
        });
      }
    }
    // Worker parity: the reissue audit row fires unconditionally.
    audit({
      event_type: 'admin_hcws_reissue_token',
      actor_username: g.payload.sub,
      actor_jti: g.payload.jti,
      actor_role: g.payload.role,
      client_ip_hash: ipHashOf(c),
      event_resource: hcwId,
      request_id: c.get('requestId'),
    });
    return res;
  });

  // Model C — mint a durable, facility-scoped self-register token (the QR any HCW
  // at this facility scans to spawn their own case; design
  // F2-Model-C-Self-Register-2026-07-16). NOT bound to an HCW: tablet_id ===
  // SELF_REGISTER_TABLET_ID marks it so ONLY /self-register accepts it. dash_users
  // gate (same as HCW create/reissue). facility_id must be a real 9-digit code so
  // the assigned QN is a valid, joinable 12-digit number.
  admin.post('/facility-token', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as { facility_id?: unknown; ttl_days?: unknown };
    const facilityId = typeof body.facility_id === 'string' ? body.facility_id.trim() : '';
    if (!/^\d{9}$/.test(facilityId)) {
      return c.json(errBody('E_VALIDATION', 'facility_id must be a real 9-digit facility code'), 400);
    }
    const ttlDays =
      typeof body.ttl_days === 'number' && body.ttl_days >= 1 && body.ttl_days <= 365 ? body.ttl_days : 365;
    const nowS = Math.floor(Date.now() / 1000);
    const exp = nowS + ttlDays * 86400;
    const jti = randomUUID();
    const claims: JwtClaims = {
      jti,
      tablet_id: SELF_REGISTER_TABLET_ID,
      facility_id: facilityId,
      iat: nowS,
      exp,
    };
    const token = await mintJwt(claims, env.jwtSigningKey);
    await env.adminStore.tokenAudit({
      jti,
      tablet_id: SELF_REGISTER_TABLET_ID,
      tablet_label: 'self-register QR for ' + facilityId,
      facility_id: facilityId,
      issued_at: nowS,
      expires_at: exp,
    });
    const enrollUrl = `${env.pwaOrigin}/enroll?token=${encodeURIComponent(token)}`;
    const res = c.json({ facility_id: facilityId, token, enroll_url: enrollUrl, jti, expires_at: exp });
    auditMutation(c, res, g.payload, 'admin_facility_token_mint', facilityId);
    return res;
  });

  // Model C — generate numbered short-links for a facility's HCW slots (design
  // F2-Model-C-Numbered-Links-2026-07-16). Stamps `<CODE>-HCW-NN` + a fresh secret
  // onto each non-revoked, QN-bearing slot (ascending by qn) and returns the
  // printable links. The plaintext secret is returned ONCE here — only its HMAC is
  // stored.
  //
  // NON-DESTRUCTIVE BY DEFAULT: a slot that already has a secret is left untouched
  // (its printed card keeps working) and reported as `already_issued` with no secret.
  // Rotation — minting fresh secrets that invalidate every previously printed card —
  // is opt-in via `rotate:true`. This makes an accidental second call safe; a
  // deliberate reprint is a distinct, separately-audited action.
  // dash_users gate, same as HCW create/reissue/facility-token.
  admin.post('/facility-links', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as {
      facility_id?: unknown;
      short_code?: unknown;
      rotate?: unknown;
    };
    const facilityId = typeof body.facility_id === 'string' ? body.facility_id.trim() : '';
    const shortCode = typeof body.short_code === 'string' ? body.short_code.trim().toUpperCase() : '';
    const rotate = body.rotate === true;
    if (!/^\d{9}$/.test(facilityId)) {
      return c.json(errBody('E_VALIDATION', 'facility_id must be a real 9-digit facility code'), 400);
    }
    if (!SHORT_CODE_RE.test(shortCode)) {
      return c.json(errBody('E_VALIDATION', 'short_code must be 2-12 chars [A-Z0-9]'), 400);
    }
    const slots = await env.adminStore.listFacilitySlotsForLinks(facilityId);
    if (slots.length === 0) {
      return c.json(
        errBody('E_NOT_FOUND', `no provisioned HCW slots at facility ${facilityId} — create HCWs first`),
        404,
      );
    }
    const links: Array<{
      hcw_id: string;
      qn: string;
      slug: string;
      secret: string | null;
      enroll_url: string | null;
      already_issued: boolean;
    }> = [];
    let issued = 0;
    let skipped = 0;
    for (let i = 0; i < slots.length; i++) {
      const slot = slots[i]!;
      // Non-destructive default: an already-issued slot keeps its live secret, so
      // its printed card stays valid. Only rotate:true mints a fresh one.
      if (slot.has_secret && !rotate) {
        links.push({
          hcw_id: slot.hcw_id,
          qn: slot.qn,
          slug: slot.enroll_slug,
          secret: null,
          enroll_url: null,
          already_issued: true,
        });
        skipped++;
        continue;
      }
      const slug = buildSlug(shortCode, i + 1);
      const secret = generateSecret();
      await env.adminStore.assignEnrollLink({
        hcw_id: slot.hcw_id,
        slug,
        secret_hmac: secretHmac(secret, env.jwtSigningKey),
      });
      links.push({
        hcw_id: slot.hcw_id,
        qn: slot.qn,
        slug,
        secret,
        enroll_url: `${env.pwaOrigin}/e/${slug}?k=${secret}`,
        already_issued: false,
      });
      issued++;
    }
    const res = c.json({
      facility_id: facilityId,
      short_code: shortCode,
      count: links.length,
      issued,
      skipped,
      rotated: rotate,
      links,
    });
    // Distinct audit event for rotations — this is the forensic trail that tells you
    // WHEN every card at a facility was invalidated (the signal we lacked before).
    auditMutation(
      c,
      res,
      g.payload,
      rotate ? 'admin_facility_links_rotate' : 'admin_facility_links_generate',
      facilityId,
    );
    return res;
  });

  // ----- facility slug links (design F2-Facility-Slug-Links-2026-07-16) ------
  // One public link per facility: /f/<slug>. Upsert-only management — renaming
  // a facility's link = upsert the new slug, then toggle the old row inactive.
  // dash_users gate, same as facility-links / HCW create.

  admin.get('/facility-slugs', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const rows = await env.adminStore.listFacilitySlugs();
    return c.json({ slugs: rows.map((r) => ({ ...r, url: `${env.pwaOrigin}/f/${r.slug}` })) });
  });

  admin.post('/facility-slugs', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as {
      slug?: unknown;
      facility_id?: unknown;
      facility_name?: unknown;
      active?: unknown;
    };
    const slug = typeof body.slug === 'string' ? normalizeFacilitySlug(body.slug) : '';
    const facilityId = typeof body.facility_id === 'string' ? body.facility_id.trim() : '';
    const facilityName = typeof body.facility_name === 'string' ? body.facility_name.trim() : '';
    // Strict boolean: silently coercing 0/'false'/null to active=true would
    // RE-ACTIVATE a link an ops script is trying to kill.
    if (body.active !== undefined && typeof body.active !== 'boolean') {
      return c.json(errBody('E_VALIDATION', 'active must be a boolean'), 400);
    }
    const active = body.active !== false; // default true
    if (!FACILITY_SLUG_RE.test(slug) || RESERVED_FACILITY_SLUGS.has(slug)) {
      return c.json(
        errBody('E_VALIDATION', 'slug must be 2-31 chars of a-z 0-9 hyphen, not "resolve"'),
        400,
      );
    }
    if (!/^\d{9}$/.test(facilityId)) {
      return c.json(errBody('E_VALIDATION', 'facility_id must be a real 9-digit facility code'), 400);
    }
    if (!facilityName || facilityName.length > 160) {
      return c.json(errBody('E_VALIDATION', 'facility_name is required (max 160 chars)'), 400);
    }
    // Upsert keeps the original provenance (created_at/created_by survive edits).
    const existing = await env.adminStore.getFacilitySlug(slug);
    await env.adminStore.upsertFacilitySlug({
      slug,
      facility_id: facilityId,
      facility_name: facilityName,
      active,
      created_at: existing?.created_at || new Date().toISOString(),
      created_by: existing?.created_by || g.payload.sub,
    });
    const res = c.json({
      ok: true,
      slug,
      facility_id: facilityId,
      facility_name: facilityName,
      active,
      url: `${env.pwaOrigin}/f/${slug}`,
    });
    auditMutation(c, res, g.payload, 'admin_facility_slug_upsert', `${slug}→${facilityId}`);
    return res;
  });

  // Facilities page (spec F2-Facilities-Page-2026-07-16, Approach A): every
  // master row + its deduped slug + live counts, in one composite read. The
  // master list is READ-ONLY — there is deliberately no write route for it.
  admin.get('/facilities', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const qp = (k: string) => c.req.query(k)?.trim() || '';
    const hasLinkRaw = qp('has_link');
    const limitN = Number(c.req.query('limit'));
    const offsetN = Number(c.req.query('offset'));
    const pageData = await env.adminStore.listFacilitiesOverview({
      ...(qp('q') ? { q: qp('q') } : {}),
      ...(qp('region') ? { region: qp('region') } : {}),
      ...(qp('province') ? { province: qp('province') } : {}),
      ...(qp('facility_type') ? { facility_type: qp('facility_type') } : {}),
      ...(hasLinkRaw === 'true' ? { has_link: true } : hasLinkRaw === 'false' ? { has_link: false } : {}),
      ...(qp('include_archived') === 'true' ? { include_archived: true } : {}),
      ...(limitN > 0 ? { limit: limitN } : {}),
      ...(offsetN > 0 ? { offset: offsetN } : {}),
    });
    return c.json({
      rows: pageData.rows.map((r) => ({
        ...r,
        url: r.slug ? `${env.pwaOrigin}/f/${r.slug}` : '',
      })),
      total: pageData.total,
      has_more: pageData.has_more,
    });
  });

  // ----- facility master management (spec F2-Facility-Master-Mgmt-2026-07-16) -
  // CRUD (archive-only, id immutable) + batch import with dry-run. One shared
  // validator (facility-master.ts) so the form and CSV paths never disagree;
  // geo mismatches WARN, never block. dash_users gate throughout.

  // Coverage target parsing (spec F2-Coverage-Report-2026-07-17): undefined and
  // blank-string mean "not specified" (leave existing value alone — a 7-column
  // wave file can never wipe targets); explicit null clears; junk → NaN so the
  // validator reports a per-row error instead of silently storing null.
  const parseTarget = (v: unknown): number | null | undefined => {
    if (v === undefined) return undefined;
    if (v === null) return null;
    if (typeof v === 'number') return v;
    if (typeof v === 'string') {
      const t = v.trim();
      return t === '' ? undefined : Number(t);
    }
    return Number.NaN;
  };

  const facilityInputFrom = (raw: Record<string, unknown>): FacilityMasterInput => {
    const target = parseTarget(raw.target_hcws);
    return {
      facility_id: typeof raw.facility_id === 'string' ? raw.facility_id.trim() : '',
      facility_name: typeof raw.facility_name === 'string' ? raw.facility_name.trim() : '',
      facility_type: typeof raw.facility_type === 'string' ? raw.facility_type.trim() : '',
      region: typeof raw.region === 'string' ? raw.region.trim() : '',
      province: typeof raw.province === 'string' ? raw.province.trim() : '',
      city_mun: typeof raw.city_mun === 'string' ? raw.city_mun.trim() : '',
      barangay: typeof raw.barangay === 'string' ? raw.barangay.trim() : '',
      ...(target !== undefined ? { target_hcws: target } : {}),
    };
  };

  const knownProvinces = async (): Promise<Set<string>> => {
    const all = await env.adminStore.listFacilitiesOverview({ include_archived: true, limit: 500 });
    return new Set(all.rows.map((r) => r.province).filter(Boolean));
  };

  admin.post('/facilities', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const raw = (await c.req.json().catch(() => ({}))) as Record<string, unknown>;
    const input = facilityInputFrom(raw);
    const { errors, warnings } = validateFacilityInput(input, await knownProvinces());
    if (errors.length) return c.json(errBody('E_VALIDATION', errors[0]!), 400);
    const existing = await env.adminStore.getFacility(input.facility_id);
    if (existing) {
      return c.json(
        errBody(
          'E_CONFLICT',
          `facility ${input.facility_id} already exists` +
            (existing.archived ? ' (archived) — unarchive it instead' : ''),
        ),
        409,
      );
    }
    const r = await env.adminStore.createFacility(input);
    if (r === 'conflict') {
      return c.json(errBody('E_CONFLICT', `facility ${input.facility_id} already exists`), 409);
    }
    const row = await env.adminStore.getFacility(input.facility_id);
    const res = c.json({ ok: true, row, warnings });
    auditMutation(c, res, g.payload, 'admin_facility_create', input.facility_id);
    return res;
  });

  admin.patch('/facilities/:id', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const id = c.req.param('id');
    const raw = (await c.req.json().catch(() => ({}))) as Record<string, unknown>;
    if (raw.facility_id !== undefined) {
      return c.json(errBody('E_VALIDATION', 'facility_id is immutable — archive + recreate instead'), 400);
    }
    if (raw.archived !== undefined && typeof raw.archived !== 'boolean') {
      return c.json(errBody('E_VALIDATION', 'archived must be a boolean'), 400);
    }
    const existing = await env.adminStore.getFacility(id);
    if (!existing) return c.json(errBody('E_NOT_FOUND', `facility ${id} not found`), 404);
    // Validate the row as it would look after the patch (id already valid).
    const merged: FacilityMasterInput = {
      facility_id: existing.facility_id,
      facility_name:
        typeof raw.facility_name === 'string' ? raw.facility_name.trim() : existing.facility_name,
      facility_type:
        typeof raw.facility_type === 'string' ? raw.facility_type.trim() : existing.facility_type,
      region: typeof raw.region === 'string' ? raw.region.trim() : existing.region,
      province: typeof raw.province === 'string' ? raw.province.trim() : existing.province,
      city_mun: typeof raw.city_mun === 'string' ? raw.city_mun.trim() : existing.city_mun,
      barangay: typeof raw.barangay === 'string' ? raw.barangay.trim() : existing.barangay,
      target_hcws:
        raw.target_hcws !== undefined
          ? (parseTarget(raw.target_hcws) ?? null)
          : existing.target_hcws,
    };
    const { errors, warnings } = validateFacilityInput(merged, await knownProvinces());
    if (errors.length) return c.json(errBody('E_VALIDATION', errors[0]!), 400);
    const patch: Partial<FacilityMasterInput> & { archived?: boolean } = {};
    for (const k of ['facility_name', 'facility_type', 'region', 'province', 'city_mun', 'barangay'] as const) {
      if (typeof raw[k] === 'string') patch[k] = (raw[k] as string).trim();
    }
    if (raw.target_hcws !== undefined) {
      const t = parseTarget(raw.target_hcws);
      if (t !== undefined) patch.target_hcws = t;
    }
    if (typeof raw.archived === 'boolean') patch.archived = raw.archived;
    const row = await env.adminStore.updateFacility(id, patch);
    if (!row) return c.json(errBody('E_NOT_FOUND', `facility ${id} not found`), 404);
    const res = c.json({ ok: true, row, warnings });
    const event =
      patch.archived === undefined
        ? 'admin_facility_update'
        : patch.archived
          ? 'admin_facility_archive'
          : 'admin_facility_unarchive';
    auditMutation(c, res, g.payload, event, id);
    return res;
  });

  admin.post('/facilities/import', async (c) => {
    const g = await gate(c, 'dash_users');
    if (!g.ok) return g.res;
    const body = (await c.req.json().catch(() => ({}))) as { mode?: unknown; rows?: unknown };
    const mode = body.mode === 'apply' ? 'apply' : body.mode === 'dry_run' ? 'dry_run' : null;
    if (!mode) return c.json(errBody('E_VALIDATION', "mode must be 'dry_run' or 'apply'"), 400);
    if (!Array.isArray(body.rows) || body.rows.length === 0) {
      return c.json(errBody('E_VALIDATION', 'rows must be a non-empty array'), 400);
    }
    if (body.rows.length > 2000) {
      return c.json(errBody('E_VALIDATION', 'at most 2000 rows per import'), 400);
    }
    const provinces = await knownProvinces();
    const FIELDS = ['facility_name', 'facility_type', 'region', 'province', 'city_mun', 'barangay'] as const;
    const verdicts: Array<{
      row: number;
      facility_id: string;
      action: 'create' | 'update' | 'unchanged' | 'error';
      changes?: string[];
      warnings: string[];
      errors: string[];
    }> = [];
    const summary = { creates: 0, updates: 0, unchanged: 0, errors: 0, warnings: 0 };
    for (let i = 0; i < body.rows.length; i++) {
      const input = facilityInputFrom((body.rows[i] ?? {}) as Record<string, unknown>);
      const { errors, warnings } = validateFacilityInput(input, provinces);
      if (errors.length) {
        verdicts.push({ row: i + 1, facility_id: input.facility_id, action: 'error', warnings, errors });
        summary.errors++;
        summary.warnings += warnings.length;
        continue;
      }
      const existing = await env.adminStore.getFacility(input.facility_id);
      if (!existing) {
        if (mode === 'apply') await env.adminStore.createFacility(input);
        verdicts.push({ row: i + 1, facility_id: input.facility_id, action: 'create', warnings, errors: [] });
        summary.creates++;
        summary.warnings += warnings.length;
        // New provinces become "known" for later rows in the same file.
        if (input.province) provinces.add(input.province);
        continue;
      }
      const rowWarnings = [...warnings];
      if (existing.archived) rowWarnings.push('row updates an archived facility');
      const changes: string[] = FIELDS.filter((k) => (input[k] ?? '') !== (existing[k] ?? ''));
      // Only when the row SPECIFIES a target (8-col file, non-blank cell) —
      // absent/blank never clears an existing target.
      if (input.target_hcws !== undefined && (input.target_hcws ?? null) !== (existing.target_hcws ?? null)) {
        changes.push('target_hcws');
      }
      if (changes.length === 0) {
        verdicts.push({ row: i + 1, facility_id: input.facility_id, action: 'unchanged', warnings: rowWarnings, errors: [] });
        summary.unchanged++;
        summary.warnings += rowWarnings.length;
        continue;
      }
      if (mode === 'apply') {
        const patch: Partial<FacilityMasterInput> = {};
        for (const k of changes) {
          if (k === 'target_hcws') patch.target_hcws = input.target_hcws ?? null;
          else {
            const f = k as (typeof FIELDS)[number];
            patch[f] = input[f] ?? '';
          }
        }
        await env.adminStore.updateFacility(input.facility_id, patch);
      }
      verdicts.push({
        row: i + 1,
        facility_id: input.facility_id,
        action: 'update',
        changes,
        warnings: rowWarnings,
        errors: [],
      });
      summary.updates++;
      summary.warnings += rowWarnings.length;
    }
    const res = c.json({ ok: true, mode, summary, verdicts });
    if (mode === 'apply') {
      auditMutation(
        c,
        res,
        g.payload,
        'admin_facility_import',
        `creates=${summary.creates} updates=${summary.updates} errors=${summary.errors}`,
      );
    }
    return res;
  });

  // Route-table parity: unmatched /admin/api/* paths → Worker's notFound body.
  admin.all('*', (c) => c.json(errBody('E_NOT_FOUND', 'route not found'), 404));

  return admin;
}
