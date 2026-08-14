/**
 * AdminStore — the admin API's seam to csweb_f2 (same discipline as
 * src/store.ts): routes take an AdminStore, tests use InMemoryAdminStore,
 * prod uses MySqlAdminStore on the SAME pool as MySqlStore.
 *
 * Table contract = ddl/f2_api_tables.sql (f2_users/f2_roles/f2_hcws/f2_audit/
 * f2_files/auth_kv/auth_token_audit) + the csweb_f2 mirror tables
 * (f2_responses/f2_dlq/f2_config). List semantics port the AS read RPCs
 * (AdminData.js / AdminUsers.js / AdminHCWs.js / AdminFiles.js /
 * AdminSettings.js): newest-first, limit ≤ 500 default 50, `q` substring.
 */
import mysql from 'mysql2/promise';
import { mkdir, readFile, unlink, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { isoToDt, type DlqRow, type FacilityRow, type InMemoryStore, type ResponseRow } from '../store.js';
import type { FacilityMasterInput } from '../facility-master.js';
import { PERM_KEYS, type PermKey } from './auth.js';
import {
  rollupCoverage,
  type CoverageFacility,
  type CoverageLevel,
  type CoverageOrphan,
  type CoverageReportData,
} from './reports.js';

// ---------------------------------------------------------------------------
// Record types (type aliases, not interfaces, so they satisfy Record<string,…>)
// ---------------------------------------------------------------------------

export type AdminUserRecord = {
  username: string;
  first_name: string;
  last_name: string;
  role_name: string;
  password_hash: string;
  password_must_change: boolean;
  email: string;
  phone: string;
  created_at: string;
  created_by: string;
  last_login_at: string;
};

/** List/API shape — password_hash stripped, has_password surfaced (AS parity). */
export type PublicUserRow = Omit<AdminUserRecord, 'password_hash'> & { has_password: boolean };

export function toPublicUser(u: AdminUserRecord): PublicUserRow {
  const { password_hash, ...rest } = u;
  return { ...rest, has_password: !!password_hash };
}

export type AdminRoleRecord = {
  name: string;
  is_builtin: boolean;
  version: number;
  created_at: string;
  created_by: string;
} & Record<PermKey, boolean>;

export type HcwRecord = {
  hcw_id: string;
  facility_id: string;
  facility_name: string;
  enrollment_token_jti: string;
  token_issued_at: string;
  token_revoked_at: string;
  status: string;
  created_at: string;
  qn: string;
  /** Numbered short-link (Model C): human slug + when it was first claimed.
   * The secret HMAC is NOT surfaced here — it lives only on EnrollLinkRow. */
  enroll_slug: string;
  claimed_at: string;
};

export type AuditRecord = {
  audit_id: string;
  occurred_at_server: string;
  occurred_at_client: string;
  event_type: string;
  hcw_id: string;
  facility_id: string;
  app_version: string;
  payload_json: string;
  actor_username: string;
  actor_jti: string;
  actor_role: string;
  event_resource: string;
  event_payload_json: string;
  client_ip_hash: string;
  request_id: string;
};

export type FileMetaRecord = {
  file_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  uploaded_by: string;
  uploaded_at: string;
  description: string;
  deleted_at: string;
  folder_path: string;
  is_folder: boolean;
};

/** Minimal projection for the sync/map/version reports (AdminReports.js port). */
export type LiteResponseRow = {
  submission_id: string;
  hcw_id: string;
  facility_id: string;
  submitted_at_server: string;
  spec_version: string;
  // Reports must distinguish completed questionnaires from refusals — the
  // Sync Report counted every row as "submitted" until 2026-07-17 (audit P0-2).
  status: string;
  submission_lat: number | null;
  submission_lng: number | null;
  /** GPS capture outcome ('' = legacy row) — audit P1-4 instrumentation. */
  gps_status: string;
};

// ---------------------------------------------------------------------------
// Filters + paging (AS defaults: limit 50 cap 500, offset ≥ 0, newest-first)
// ---------------------------------------------------------------------------

// Date bounds on all list filters are UTC ISO strings produced by mnlWindow():
// `from` is INCLUSIVE, `to` is EXCLUSIVE (half-open window — audit P2-7).
export interface RespFilters {
  from?: string;
  to?: string;
  facility_id?: string;
  status?: string;
  source_path?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface AuditFilters {
  from?: string;
  to?: string;
  event_type?: string;
  hcw_id?: string;
  actor_username?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface DlqFilters {
  from?: string;
  to?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface HcwFilters {
  facility_id?: string;
  status?: string;
  hcw_id?: string;
  /** created_at window — UTC ISO half-open bounds from the route's mnlWindow
   *  (Data-tab filter bar, 2026-07-17). */
  from?: string;
  to?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface UsersFilters {
  role_name?: string;
  username?: string;
  q?: string;
}

export interface Paged<T> {
  rows: T[];
  total: number;
  has_more: boolean;
}

const DEFAULT_LIMIT = 50;
const MAX_LIMIT = 500;
const SCAN_CAP = 50000;

/**
 * F2's HCW sequence block within a facility's 12-digit QN (= 9-digit facility
 * code + 3-digit sequence, shared with F1/F3/F4).
 *
 * The QN space at ONE facility is partitioned BY INSTRUMENT — that partition is
 * what makes a QN uniquely identify a respondent across the whole survey:
 *
 *   F1 Facility Head : seq 000
 *   F3 Patients      : seq 001..099
 *   F2 HCWs          : seq 101..999   <- this floor
 *
 * Without the floor the assigner starts at 001 and only ever looks at f2_hcws —
 * it cannot see that CSPro already issued 001..00N to PATIENTS at the same
 * facility, so an HCW would silently be handed a patient's questionnaire number.
 * (Caught 2026-07-14: a fresh HCW at LPH-Bay 040340220 was auto-assigned
 * 040340220001, colliding head-on with the F3 patient key of the same value.)
 */
const F2_QN_SEQ_FLOOR = 100;

function normLimit(v: number | undefined): number {
  return Math.min(Number(v) || DEFAULT_LIMIT, MAX_LIMIT);
}
function normOffset(v: number | undefined): number {
  return Math.max(Number(v) || 0, 0);
}

export type StoreErr = { ok: false; code: string; message: string };

export type CreateHcwInput = {
  hcw_id: string;
  facility_id: string;
  facility_name: string;
  status: string;
  qn: string;
};
export type CreateHcwResult = { ok: true; hcw_id: string; qn: string } | StoreErr;

/** A facility's provisioned slot, in slug-assignment order (ascending qn). */
export type FacilitySlot = {
  hcw_id: string;
  qn: string;
  facility_name: string;
  /** The slot's current slug, or '' if none is assigned yet. */
  enroll_slug: string;
  /** True once a secret HMAC is stored — a non-rotating generate leaves it alone. */
  has_secret: boolean;
};

/** Claim-path lookup by enroll_slug — carries the secret HMAC for verification. */
export type EnrollLinkRow = {
  hcw_id: string;
  facility_id: string;
  qn: string;
  status: string;
  enroll_secret_hmac: string;
};

/** One facility's public link slug (design F2-Facility-Slug-Links-2026-07-16). */
export type FacilitySlugRecord = {
  slug: string; // lowercase, PK
  facility_id: string; // 9-digit PSGC facility code
  facility_name: string; // shown on the StartScreen + written to the case
  active: boolean; // soft on/off without deleting
  created_at: string; // ISO
  created_by: string;
};

/** One Facilities-page row: master + its (deduped) slug + live counts
 *  (spec F2-Facilities-Page-2026-07-16, Approach A). */
export type FacilityOverviewRow = {
  facility_id: string;
  facility_name: string;
  facility_type: string;
  region: string;
  province: string;
  city_mun: string;
  archived: boolean; // spec F2-Facility-Master-Mgmt-2026-07-16
  target_hcws: number | null; // spec F2-Coverage-Report-2026-07-17
  slug: string; // '' when the facility has no link yet
  active: boolean | null; // null when no link
  submitted: number; // f2_responses status <> 'refusal'
  refusals: number; // f2_responses status = 'refusal'
  in_progress: number; // f2_hcws sr-% AND status='enrolled'
};

export interface FacilityOverviewFilters {
  q?: string;
  region?: string;
  province?: string;
  facility_type?: string;
  has_link?: boolean;
  /** Include archived master rows (default false — spec F2-Facility-Master-Mgmt). */
  include_archived?: boolean;
  limit?: number;
  offset?: number;
}

/** Master row as the management surfaces see it (archived/target made explicit). */
export type FacilityMasterRecord = FacilityRow & { archived: boolean; target_hcws: number | null };

export interface CoverageFilters {
  level: CoverageLevel;
  /** Inclusive UTC ISO lower bound (mnlWindow). */
  from?: string;
  /** EXCLUSIVE UTC ISO upper bound (mnlWindow). */
  to?: string;
  include_archived?: boolean;
}

export type ReissueResult =
  | {
      ok: true;
      hcw_id: string;
      facility_id: string;
      qn: string;
      new_jti: string;
      old_jti: string;
      token_issued_at: string;
    }
  | StoreErr;

export interface TokenAuditRow {
  jti: string;
  tablet_id: string;
  tablet_label: string;
  facility_id: string;
  issued_at: number; // epoch seconds
  expires_at: number; // epoch seconds
}

// ---------------------------------------------------------------------------
// AdminStore interface
// ---------------------------------------------------------------------------

export interface AdminStore {
  // -- users -----------------------------------------------------------------
  /** Full record incl. password_hash — login/change-password only. */
  getUserAuth(username: string): Promise<AdminUserRecord | null>;
  /** AS adminUsersList semantics (filters + newest-first). Full records; caller strips. */
  listUsers(f: UsersFilters): Promise<AdminUserRecord[]>;
  insertUser(rec: AdminUserRecord): Promise<'created' | 'conflict'>;
  replaceUser(rec: AdminUserRecord): Promise<void>;
  deleteUser(username: string): Promise<boolean>;
  countUsersWithRole(roleName: string): Promise<number>;
  touchLastLogin(username: string, ts: string): Promise<void>;
  // -- roles -----------------------------------------------------------------
  /** Built-in first, then name asc (AS adminRolesList). */
  listRoles(): Promise<AdminRoleRecord[]>;
  getRole(name: string): Promise<AdminRoleRecord | null>;
  insertRole(rec: AdminRoleRecord): Promise<'created' | 'conflict'>;
  replaceRole(rec: AdminRoleRecord): Promise<void>;
  deleteRoleRow(name: string): Promise<boolean>;
  // -- hcws ------------------------------------------------------------------
  listHcws(f: HcwFilters): Promise<Paged<HcwRecord>>;
  /** Full qn-assignment port of AS adminHcwsCreate (transactional in MySQL). */
  createHcw(p: CreateHcwInput): Promise<CreateHcwResult>;
  /** CAS jti rotation port of AS adminHcwsReissueToken. */
  reissueHcwToken(p: { hcw_id: string; new_jti: string; prev_jti: string }): Promise<ReissueResult>;
  // -- numbered short-link claim (Model C — F2-Model-C-Numbered-Links-2026-07-16) --
  /** Non-revoked slots with a 12-digit QN at this facility, ascending by qn. */
  listFacilitySlotsForLinks(facilityId: string): Promise<FacilitySlot[]>;
  /** Set (or rotate) a slot's slug + secret HMAC; clears claimed_at. */
  assignEnrollLink(p: { hcw_id: string; slug: string; secret_hmac: string }): Promise<void>;
  /** Claim lookup by slug (includes the HMAC for constant-time verification). */
  getEnrollLinkBySlug(slug: string): Promise<EnrollLinkRow | null>;
  /** Stamp claimed_at on first claim (no-op if already stamped). */
  markClaimed(hcwId: string): Promise<void>;
  // -- facility slug links (design F2-Facility-Slug-Links-2026-07-16) ----------
  /** Insert or replace a slug row (PK = slug). */
  upsertFacilitySlug(rec: FacilitySlugRecord): Promise<void>;
  /** All slug rows, newest first. */
  listFacilitySlugs(): Promise<FacilitySlugRecord[]>;
  /** Lookup by slug in any active state — callers gate on `.active`. */
  getFacilitySlug(slug: string): Promise<FacilitySlugRecord | null>;
  /** Facilities page: every master row + deduped slug (active first, then newest) + counts. */
  listFacilitiesOverview(f: FacilityOverviewFilters): Promise<Paged<FacilityOverviewRow>>;
  // -- facility master management (spec F2-Facility-Master-Mgmt-2026-07-16) ----
  /** Insert a new master row (archived=false). 'conflict' when the id exists (archived counts). */
  createFacility(rec: FacilityMasterInput): Promise<'created' | 'conflict'>;
  /** Master row by id, archived rows included. */
  getFacility(id: string): Promise<FacilityMasterRecord | null>;
  /** Patch name/type/geo and/or the archived flag. facility_id never changes. Null when unknown. */
  updateFacility(
    id: string,
    patch: Partial<FacilityMasterInput> & { archived?: boolean },
  ): Promise<FacilityMasterRecord | null>;
  /** Coverage report (spec F2-Coverage-Report-2026-07-17): per-geo progress vs
   *  targets. Dates are half-open UTC bounds from mnlWindow(); counts share the
   *  overview's definitions via rollupCoverage(). */
  coverageReport(f: CoverageFilters): Promise<CoverageReportData>;
  // -- data dashboards (csweb_f2 reads) ---------------------------------------
  listResponses(f: RespFilters): Promise<Paged<ResponseRow>>;
  getResponseById(id: string): Promise<ResponseRow | null>;
  listAudit(f: AuditFilters): Promise<Paged<AuditRecord>>;
  /** Distinct event_type values, sorted — feeds the Audit tab's dropdown. */
  listAuditEventTypes(): Promise<string[]>;
  listDlq(f: DlqFilters): Promise<Paged<DlqRow>>;
  dlqFind(dlqId: string): Promise<DlqRow | null>;
  dlqDelete(dlqId: string): Promise<boolean>;
  /** #831: flip a response's status to 'voided' — never a delete; the row stays
   *  for audit and remains visible in list/detail, but drops out of coverage,
   *  map, form-revision counts, and the csweb_f2 exports. Writes a
   *  `response_voided` audit row carrying the reason + prev_status. */
  voidResponse(
    id: string,
    reason: string,
  ): Promise<
    | { ok: true; submission_id: string; prev_status: string }
    | { ok: false; code: 'E_NOT_FOUND' | 'E_ALREADY_VOIDED' }
  >;
  readResponsesLite(cap?: number): Promise<LiteResponseRow[]>;
  // -- audit write (mirrors AS writeAuditRow columns) --------------------------
  writeAudit(entry: Partial<AuditRecord> & { event_type: string }): Promise<void>;
  // -- config (f2_config; update-only like AS adminConfigSet) ------------------
  setConfig(key: string, value: string): Promise<boolean>;
  // -- files metadata ----------------------------------------------------------
  listFiles(f: { q?: string; path?: string }): Promise<{ files: FileMetaRecord[]; total: number }>;
  getFileMeta(fileId: string): Promise<FileMetaRecord | null>;
  insertFileMeta(rec: FileMetaRecord): Promise<'created' | 'conflict'>;
  updateFilename(fileId: string, newName: string): Promise<void>;
  /** Stamps deleted_at; null when unknown or already deleted (AS parity). */
  softDeleteFile(fileId: string): Promise<string | null>;
  /** True when a non-deleted folder row of this name exists at root. */
  folderExists(name: string): Promise<boolean>;
  // -- auth kv (replaces CF KV: revoked_jti / revoked_user / throttle) ----------
  kvGet(key: string): Promise<string | null>;
  kvPut(key: string, value: string, ttlSeconds?: number): Promise<void>;
  kvDelete(key: string): Promise<void>;
  // -- device-token audit (auth_token_audit; replaces KV token:<jti>) -----------
  tokenAudit(row: TokenAuditRow): Promise<void>;
}

// ---------------------------------------------------------------------------
// Shared filter logic (AS ports) — used by InMemoryAdminStore
// ---------------------------------------------------------------------------

const jsonHay = (row: unknown): string => JSON.stringify(row).toLowerCase();

function newestFirst<T>(rows: T[], key: (r: T) => string): T[] {
  return rows.sort((a, b) => {
    const ka = key(a);
    const kb = key(b);
    if (ka < kb) return 1;
    if (ka > kb) return -1;
    return 0;
  });
}

function page<T>(matched: T[], limit: number, offset: number): Paged<T> {
  const rows = matched.slice(offset, offset + limit);
  return { rows, total: matched.length, has_more: offset + rows.length < matched.length };
}

// ---------------------------------------------------------------------------
// InMemoryAdminStore — test double sharing the InMemoryStore's responses/dlq/config
// ---------------------------------------------------------------------------

export class InMemoryAdminStore implements AdminStore {
  users = new Map<string, AdminUserRecord>();
  roles = new Map<string, AdminRoleRecord>();
  hcws: HcwRecord[] = [];
  auditRows: AuditRecord[] = [];
  files: FileMetaRecord[] = [];
  tokenAudits: TokenAuditRow[] = [];
  kv = new Map<string, { v: string; expiresAt: number | null }>();
  /** hcw_id → enroll_secret_hmac (kept off HcwRecord so list reads never leak it). */
  enrollSecrets = new Map<string, string>();
  facilitySlugs = new Map<string, FacilitySlugRecord>();

  constructor(public base: InMemoryStore) {}

  // -- users -----------------------------------------------------------------
  async getUserAuth(username: string) {
    return this.users.get(username) ?? null;
  }

  async listUsers(f: UsersFilters) {
    const q = f.q ? f.q.toLowerCase() : null;
    const matched: AdminUserRecord[] = [];
    for (const u of this.users.values()) {
      if (f.role_name && u.role_name !== f.role_name) continue;
      if (f.username && u.username !== f.username) continue;
      if (q) {
        const hay = `${u.username} ${u.first_name} ${u.last_name} ${u.email}`.toLowerCase();
        if (!hay.includes(q)) continue;
      }
      matched.push({ ...u });
    }
    return newestFirst(matched, (u) => u.created_at);
  }

  async insertUser(rec: AdminUserRecord) {
    if (this.users.has(rec.username)) return 'conflict' as const;
    this.users.set(rec.username, { ...rec });
    return 'created' as const;
  }

  async replaceUser(rec: AdminUserRecord) {
    this.users.set(rec.username, { ...rec });
  }

  async deleteUser(username: string) {
    return this.users.delete(username);
  }

  async countUsersWithRole(roleName: string) {
    let n = 0;
    for (const u of this.users.values()) if (u.role_name === roleName) n++;
    return n;
  }

  async touchLastLogin(username: string, ts: string) {
    const u = this.users.get(username);
    if (u) u.last_login_at = ts;
  }

  // -- roles -----------------------------------------------------------------
  async listRoles() {
    const rows = [...this.roles.values()].map((r) => ({ ...r }));
    rows.sort((a, b) => {
      const ba = a.is_builtin ? 0 : 1;
      const bb = b.is_builtin ? 0 : 1;
      if (ba !== bb) return ba - bb;
      return a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
    });
    return rows;
  }

  async getRole(name: string) {
    const r = this.roles.get(name);
    return r ? { ...r } : null;
  }

  async insertRole(rec: AdminRoleRecord) {
    if (this.roles.has(rec.name)) return 'conflict' as const;
    this.roles.set(rec.name, { ...rec });
    return 'created' as const;
  }

  async replaceRole(rec: AdminRoleRecord) {
    this.roles.set(rec.name, { ...rec });
  }

  async deleteRoleRow(name: string) {
    return this.roles.delete(name);
  }

  // -- hcws ------------------------------------------------------------------
  async listHcws(f: HcwFilters) {
    const q = f.q ? f.q.toLowerCase() : null;
    const matched: HcwRecord[] = [];
    for (const r of this.hcws) {
      if (f.facility_id && r.facility_id !== f.facility_id) continue;
      if (f.status && r.status !== f.status) continue;
      if (f.hcw_id && r.hcw_id !== f.hcw_id) continue;
      if (f.from && r.created_at && r.created_at < f.from) continue;
      if (f.to && r.created_at && r.created_at >= f.to) continue;
      if (q && !jsonHay(r).includes(q)) continue;
      matched.push({ ...r });
    }
    newestFirst(matched, (r) => r.created_at);
    return page(matched, normLimit(f.limit), normOffset(f.offset));
  }

  async createHcw(p: CreateHcwInput): Promise<CreateHcwResult> {
    // Port of AS adminHcwsCreate — dup-active check, then qn assignment.
    for (const r of this.hcws) {
      if (r.hcw_id === p.hcw_id && r.status !== 'revoked') {
        return { ok: false, code: 'E_CONFLICT', message: `hcw_id ${p.hcw_id} already enrolled` };
      }
    }
    let qn = p.qn.trim();
    if (qn) {
      if (!/^\d{12}$/.test(qn)) {
        return { ok: false, code: 'E_VALIDATION', message: 'qn must be exactly 12 digits' };
      }
      for (const r of this.hcws) {
        if (r.qn === qn) {
          return { ok: false, code: 'E_CONFLICT', message: `qn ${qn} already assigned` };
        }
      }
    } else if (/^\d{9}$/.test(p.facility_id)) {
      // Start at the F2 block floor, never at 001 — 001..099 belong to F3 patients.
      let maxSeq = F2_QN_SEQ_FLOOR;
      for (const r of this.hcws) {
        if (r.qn.length === 12 && r.qn.startsWith(p.facility_id)) {
          const s = Number(r.qn.slice(9));
          if (s > maxSeq) maxSeq = s;
        }
      }
      if (maxSeq >= 999) {
        return {
          ok: false,
          code: 'E_VALIDATION',
          message: `facility ${p.facility_id} HCW sequence exhausted (999)`,
        };
      }
      qn = p.facility_id + String(maxSeq + 1).padStart(3, '0');
    }
    const nowIso = new Date().toISOString();
    this.hcws.push({
      hcw_id: p.hcw_id,
      facility_id: p.facility_id,
      facility_name: p.facility_name,
      enrollment_token_jti: '',
      token_issued_at: nowIso,
      token_revoked_at: '',
      status: p.status || 'enrolled',
      created_at: nowIso,
      qn,
      enroll_slug: '',
      claimed_at: '',
    });
    return { ok: true, hcw_id: p.hcw_id, qn };
  }

  // -- numbered short-link claim (Model C) -----------------------------------
  async listFacilitySlotsForLinks(facilityId: string): Promise<FacilitySlot[]> {
    return this.hcws
      .filter((r) => r.facility_id === facilityId && r.status !== 'revoked' && /^\d{12}$/.test(r.qn))
      .sort((a, b) => (a.qn < b.qn ? -1 : a.qn > b.qn ? 1 : 0))
      .map((r) => ({
        hcw_id: r.hcw_id,
        qn: r.qn,
        facility_name: r.facility_name,
        enroll_slug: r.enroll_slug || '',
        has_secret: (this.enrollSecrets.get(r.hcw_id) ?? '') !== '',
      }));
  }

  async assignEnrollLink(p: { hcw_id: string; slug: string; secret_hmac: string }) {
    const row = this.hcws.find((r) => r.hcw_id === p.hcw_id);
    if (!row) return;
    // Mirror the DB UNIQUE(enroll_slug): a slug belongs to at most one slot.
    for (const r of this.hcws) if (r.enroll_slug === p.slug && r.hcw_id !== p.hcw_id) r.enroll_slug = '';
    row.enroll_slug = p.slug;
    row.claimed_at = '';
    this.enrollSecrets.set(p.hcw_id, p.secret_hmac);
  }

  async getEnrollLinkBySlug(slug: string): Promise<EnrollLinkRow | null> {
    const row = this.hcws.find((r) => r.enroll_slug === slug && r.enroll_slug !== '');
    if (!row) return null;
    return {
      hcw_id: row.hcw_id,
      facility_id: row.facility_id,
      qn: row.qn,
      status: row.status,
      enroll_secret_hmac: this.enrollSecrets.get(row.hcw_id) ?? '',
    };
  }

  async markClaimed(hcwId: string) {
    const row = this.hcws.find((r) => r.hcw_id === hcwId);
    if (row && !row.claimed_at) row.claimed_at = new Date().toISOString();
  }

  // -- facility slug links -----------------------------------------------------
  async upsertFacilitySlug(rec: FacilitySlugRecord) {
    this.facilitySlugs.set(rec.slug, { ...rec });
  }

  async listFacilitySlugs() {
    return newestFirst(
      [...this.facilitySlugs.values()].map((r) => ({ ...r })),
      (r) => r.created_at,
    );
  }

  async getFacilitySlug(slug: string) {
    const r = this.facilitySlugs.get(slug);
    return r ? { ...r } : null;
  }

  async listFacilitiesOverview(f: FacilityOverviewFilters): Promise<Paged<FacilityOverviewRow>> {
    // One slug per facility: active first, then newest created_at, then slug asc
    // (mirrors the MySQL ROW_NUMBER() dedup).
    const slugByFacility = new Map<string, FacilitySlugRecord>();
    const ranked = [...this.facilitySlugs.values()].sort((a, b) => {
      if (a.active !== b.active) return a.active ? -1 : 1;
      if (a.created_at !== b.created_at) return a.created_at > b.created_at ? -1 : 1;
      return a.slug < b.slug ? -1 : 1;
    });
    for (const s of ranked) if (!slugByFacility.has(s.facility_id)) slugByFacility.set(s.facility_id, s);

    const q = f.q ? f.q.toLowerCase() : null;
    const matched: FacilityOverviewRow[] = [];
    for (const m of this.base.facilities) {
      if (m.archived && !f.include_archived) continue;
      if (f.region && m.region !== f.region) continue;
      if (f.province && m.province !== f.province) continue;
      if (f.facility_type && m.facility_type !== f.facility_type) continue;
      const s = slugByFacility.get(m.facility_id);
      if (f.has_link === true && !s) continue;
      if (f.has_link === false && s) continue;
      if (q && !`${m.facility_name} ${m.facility_id}`.toLowerCase().includes(q)) continue;
      let submitted = 0;
      let refusals = 0;
      for (const r of this.base.responses.values()) {
        if (r.facility_id !== m.facility_id) continue;
        if (r.status === 'refusal') refusals++;
        else submitted++;
      }
      const inProgress = this.hcws.filter(
        (h) => h.facility_id === m.facility_id && h.hcw_id.startsWith('sr-') && h.status === 'enrolled',
      ).length;
      matched.push({
        facility_id: m.facility_id,
        facility_name: m.facility_name,
        facility_type: m.facility_type,
        region: m.region,
        province: m.province,
        city_mun: m.city_mun,
        archived: m.archived === true,
        target_hcws: m.target_hcws ?? null,
        slug: s?.slug ?? '',
        active: s ? s.active : null,
        submitted,
        refusals,
        in_progress: inProgress,
      });
    }
    matched.sort(
      (a, b) =>
        a.region.localeCompare(b.region) ||
        a.province.localeCompare(b.province) ||
        a.facility_name.localeCompare(b.facility_name),
    );
    return page(matched, normLimit(f.limit), normOffset(f.offset));
  }

  // -- facility master management ----------------------------------------------
  async createFacility(rec: FacilityMasterInput) {
    if (this.base.facilities.some((m) => m.facility_id === rec.facility_id)) {
      return 'conflict' as const;
    }
    this.base.facilities.push({
      facility_id: rec.facility_id,
      facility_name: rec.facility_name,
      facility_type: rec.facility_type ?? '',
      region: rec.region ?? '',
      province: rec.province ?? '',
      city_mun: rec.city_mun ?? '',
      barangay: rec.barangay ?? '',
      archived: false,
      target_hcws: rec.target_hcws ?? null,
    });
    return 'created' as const;
  }

  async getFacility(id: string): Promise<FacilityMasterRecord | null> {
    const m = this.base.facilities.find((r) => r.facility_id === id);
    return m ? { ...m, archived: m.archived === true, target_hcws: m.target_hcws ?? null } : null;
  }

  async updateFacility(
    id: string,
    patch: Partial<FacilityMasterInput> & { archived?: boolean },
  ): Promise<FacilityMasterRecord | null> {
    const m = this.base.facilities.find((r) => r.facility_id === id);
    if (!m) return null;
    for (const k of ['facility_name', 'facility_type', 'region', 'province', 'city_mun', 'barangay'] as const) {
      if (patch[k] !== undefined) m[k] = patch[k]!;
    }
    if (patch.archived !== undefined) m.archived = patch.archived;
    if (patch.target_hcws !== undefined) m.target_hcws = patch.target_hcws;
    return { ...m, archived: m.archived === true, target_hcws: m.target_hcws ?? null };
  }

  async coverageReport(f: CoverageFilters): Promise<CoverageReportData> {
    const inWindow = (ts: string): boolean => {
      if (f.from && ts && ts < f.from) return false;
      if (f.to && ts && ts >= f.to) return false;
      return true;
    };
    const masterIds = new Set(this.base.facilities.map((m) => m.facility_id));
    const facilities: CoverageFacility[] = [];
    for (const m of this.base.facilities) {
      if (m.archived && !f.include_archived) continue;
      let submitted = 0;
      let refusals = 0;
      let paper = 0;
      let last = '';
      for (const r of this.base.responses.values()) {
        if (r.facility_id !== m.facility_id) continue;
        if (r.status === 'voided') continue; // #831
        if (!inWindow(r.submitted_at_server)) continue;
        if (r.status === 'refusal') refusals++;
        else {
          submitted++;
          if (r.source_path === 'paper_encoded') paper++;
        }
        if (r.submitted_at_server > last) last = r.submitted_at_server;
      }
      const started = this.hcws.filter(
        (h) => h.facility_id === m.facility_id && h.hcw_id.startsWith('sr-') && h.status === 'enrolled',
      ).length;
      const linkActive = [...this.facilitySlugs.values()].some(
        (s) => s.facility_id === m.facility_id && s.active,
      );
      facilities.push({
        facility_id: m.facility_id,
        facility_name: m.facility_name,
        region: m.region,
        province: m.province,
        link_active: linkActive,
        target_hcws: m.target_hcws ?? null,
        started,
        submitted,
        refusals,
        paper_encoded: paper,
        last_activity: last,
      });
    }
    const orphanAgg = new Map<string, CoverageOrphan>();
    for (const r of this.base.responses.values()) {
      if (masterIds.has(r.facility_id)) continue;
      if (r.status === 'voided') continue; // #831
      if (!inWindow(r.submitted_at_server)) continue;
      let o = orphanAgg.get(r.facility_id);
      if (!o) {
        o = { facility_id: r.facility_id, submitted: 0, refusals: 0, paper_encoded: 0, last_activity: '' };
        orphanAgg.set(r.facility_id, o);
      }
      if (r.status === 'refusal') o.refusals++;
      else {
        o.submitted++;
        if (r.source_path === 'paper_encoded') o.paper_encoded++;
      }
      if (r.submitted_at_server > o.last_activity) o.last_activity = r.submitted_at_server;
    }
    return rollupCoverage(f.level, facilities, [...orphanAgg.values()]);
  }

  async reissueHcwToken(p: { hcw_id: string; new_jti: string; prev_jti: string }): Promise<ReissueResult> {
    const row = this.hcws.find((r) => r.hcw_id === p.hcw_id);
    if (!row) {
      return { ok: false, code: 'E_NOT_FOUND', message: `hcw_id ${p.hcw_id} not found` };
    }
    const currentJti = row.enrollment_token_jti || '';
    if (currentJti !== (p.prev_jti || '')) {
      return {
        ok: false,
        code: 'E_CAS_FAILED',
        message: 'token already reissued by another admin; refresh and retry',
      };
    }
    const nowIso = new Date().toISOString();
    row.enrollment_token_jti = p.new_jti;
    row.token_issued_at = nowIso;
    if (currentJti) row.token_revoked_at = nowIso;
    row.status = 'enrolled';
    return {
      ok: true,
      hcw_id: p.hcw_id,
      facility_id: row.facility_id,
      qn: row.qn || '',
      new_jti: p.new_jti,
      old_jti: currentJti,
      token_issued_at: nowIso,
    };
  }

  // -- data dashboards ---------------------------------------------------------
  async listResponses(f: RespFilters) {
    const q = f.q ? f.q.toLowerCase() : null;
    const matched: ResponseRow[] = [];
    for (const r of this.base.responses.values()) {
      if (f.from && r.submitted_at_server && r.submitted_at_server < f.from) continue;
      if (f.to && r.submitted_at_server && r.submitted_at_server >= f.to) continue;
      if (f.facility_id && r.facility_id !== f.facility_id) continue;
      if (f.status && r.status !== f.status) continue;
      if (f.source_path && r.source_path !== f.source_path) continue;
      if (q && !jsonHay(r).includes(q)) continue;
      matched.push({ ...r });
    }
    newestFirst(matched, (r) => r.submitted_at_server);
    return page(matched, normLimit(f.limit), normOffset(f.offset));
  }

  async getResponseById(id: string) {
    for (const r of this.base.responses.values()) {
      if (r.submission_id === id) return { ...r };
    }
    return null;
  }

  async voidResponse(id: string, reason: string) {
    for (const r of this.base.responses.values()) {
      if (r.submission_id !== id) continue;
      const prev = r.status ?? '';
      if (prev === 'voided') return { ok: false as const, code: 'E_ALREADY_VOIDED' as const };
      r.status = 'voided';
      await this.writeAudit({
        event_type: 'response_voided',
        hcw_id: r.hcw_id ?? '',
        facility_id: r.facility_id ?? '',
        payload_json: JSON.stringify({ submission_id: id, reason, prev_status: prev }),
      });
      return { ok: true as const, submission_id: id, prev_status: prev };
    }
    return { ok: false as const, code: 'E_NOT_FOUND' as const };
  }

  async listAudit(f: AuditFilters) {
    const q = f.q ? f.q.toLowerCase() : null;
    const matched: AuditRecord[] = [];
    for (const r of this.auditRows) {
      if (f.from && r.occurred_at_server && r.occurred_at_server < f.from) continue;
      if (f.to && r.occurred_at_server && r.occurred_at_server >= f.to) continue;
      if (f.event_type && r.event_type !== f.event_type) continue;
      if (f.hcw_id && r.hcw_id !== f.hcw_id) continue;
      if (f.actor_username && r.actor_username !== f.actor_username) continue;
      if (q && !jsonHay(r).includes(q)) continue;
      matched.push({ ...r });
    }
    newestFirst(matched, (r) => r.occurred_at_server);
    return page(matched, normLimit(f.limit), normOffset(f.offset));
  }

  async listAuditEventTypes() {
    return [...new Set(this.auditRows.map((r) => r.event_type).filter(Boolean))].sort();
  }

  async listDlq(f: DlqFilters) {
    const q = f.q ? f.q.toLowerCase() : null;
    const matched: DlqRow[] = [];
    for (const r of this.base.dlq) {
      if (f.from && r.received_at_server && r.received_at_server < f.from) continue;
      if (f.to && r.received_at_server && r.received_at_server >= f.to) continue;
      if (q && !jsonHay(r).includes(q)) continue;
      matched.push({ ...r });
    }
    newestFirst(matched, (r) => r.received_at_server);
    return page(matched, normLimit(f.limit), normOffset(f.offset));
  }

  async dlqFind(dlqId: string) {
    const r = this.base.dlq.find((d) => d.dlq_id === dlqId);
    return r ? { ...r } : null;
  }

  async dlqDelete(dlqId: string) {
    const idx = this.base.dlq.findIndex((d) => d.dlq_id === dlqId);
    if (idx === -1) return false;
    this.base.dlq.splice(idx, 1);
    return true;
  }

  async readResponsesLite(cap = SCAN_CAP) {
    const out: LiteResponseRow[] = [];
    for (const r of this.base.responses.values()) {
      if (r.status === 'voided') continue; // #831: voided rows never feed map/revisions
      if (out.length >= cap) break;
      out.push({
        submission_id: r.submission_id,
        hcw_id: r.hcw_id,
        facility_id: r.facility_id,
        submitted_at_server: r.submitted_at_server,
        spec_version: r.spec_version,
        status: r.status,
        submission_lat: r.submission_lat === '' ? null : Number(r.submission_lat),
        submission_lng: r.submission_lng === '' ? null : Number(r.submission_lng),
        gps_status: r.gps_status,
      });
    }
    return out;
  }

  // -- audit write ---------------------------------------------------------------
  async writeAudit(entry: Partial<AuditRecord> & { event_type: string }) {
    this.auditRows.push({
      audit_id: entry.audit_id ?? '',
      occurred_at_server: new Date().toISOString(),
      occurred_at_client: entry.occurred_at_client ?? '',
      event_type: entry.event_type,
      hcw_id: entry.hcw_id ?? '',
      facility_id: entry.facility_id ?? '',
      app_version: entry.app_version ?? '',
      payload_json: entry.payload_json ?? '',
      actor_username: entry.actor_username ?? '',
      actor_jti: entry.actor_jti ?? '',
      actor_role: entry.actor_role ?? '',
      event_resource: entry.event_resource ?? '',
      event_payload_json: entry.event_payload_json ?? '',
      client_ip_hash: entry.client_ip_hash ?? '',
      request_id: entry.request_id ?? '',
    });
  }

  // -- config ---------------------------------------------------------------------
  async setConfig(key: string, value: string) {
    if (!this.base.config.has(key)) return false;
    this.base.config.set(key, value);
    return true;
  }

  // -- files ------------------------------------------------------------------------
  async listFiles(f: { q?: string; path?: string }) {
    const q = f.q ? f.q.toLowerCase() : null;
    let pathFilter = f.path ? f.path : null;
    if (pathFilter === '/') pathFilter = null;
    const matched: FileMetaRecord[] = [];
    for (const r of this.files) {
      if (r.deleted_at) continue;
      const fp = r.folder_path || '/';
      if (pathFilter) {
        if (fp !== pathFilter) continue;
      } else if (fp !== '/') {
        continue;
      }
      if (q) {
        const hay = `${r.filename} ${r.description} ${r.uploaded_by}`.toLowerCase();
        if (!hay.includes(q)) continue;
      }
      matched.push({ ...r });
    }
    newestFirst(matched, (r) => r.uploaded_at);
    return { files: matched, total: matched.length };
  }

  async getFileMeta(fileId: string) {
    const r = this.files.find((x) => x.file_id === fileId);
    return r ? { ...r } : null;
  }

  async insertFileMeta(rec: FileMetaRecord) {
    if (this.files.some((x) => x.file_id === rec.file_id)) return 'conflict' as const;
    this.files.push({ ...rec });
    return 'created' as const;
  }

  async updateFilename(fileId: string, newName: string) {
    const r = this.files.find((x) => x.file_id === fileId);
    if (r) r.filename = newName;
  }

  async softDeleteFile(fileId: string) {
    const r = this.files.find((x) => x.file_id === fileId);
    if (!r || r.deleted_at) return null;
    r.deleted_at = new Date().toISOString();
    return r.deleted_at;
  }

  async folderExists(name: string) {
    return this.files.some((r) => !r.deleted_at && r.is_folder && r.filename === name);
  }

  // -- kv -------------------------------------------------------------------------
  async kvGet(key: string) {
    const e = this.kv.get(key);
    if (!e) return null;
    if (e.expiresAt !== null && Date.now() > e.expiresAt) {
      this.kv.delete(key);
      return null;
    }
    return e.v;
  }

  async kvPut(key: string, value: string, ttlSeconds?: number) {
    this.kv.set(key, { v: value, expiresAt: ttlSeconds ? Date.now() + ttlSeconds * 1000 : null });
  }

  async kvDelete(key: string) {
    this.kv.delete(key);
  }

  async tokenAudit(row: TokenAuditRow) {
    this.tokenAudits.push({ ...row });
  }
}

// ---------------------------------------------------------------------------
// MySqlAdminStore — SQL on csweb_f2 (shares the pool with MySqlStore)
// ---------------------------------------------------------------------------

type Row = mysql.RowDataPacket;

const dtToIso = (v: unknown): string =>
  v == null || v === '' ? '' : v instanceof Date ? v.toISOString() : String(v);

const strOf = (v: unknown): string => (v == null ? '' : String(v));

/** JSON columns come back parsed from mysql2 — the API contract is a string. */
const jsonStrOf = (v: unknown): string =>
  v == null ? '' : typeof v === 'string' ? v : JSON.stringify(v);

const boolOf = (v: unknown): boolean => v === true || v === 1 || v === '1' || v === 'true';

function mapDbUser(r: Row): AdminUserRecord {
  return {
    username: strOf(r.username),
    first_name: strOf(r.first_name),
    last_name: strOf(r.last_name),
    role_name: strOf(r.role_name),
    password_hash: strOf(r.password_hash),
    password_must_change: boolOf(r.password_must_change),
    email: strOf(r.email),
    phone: strOf(r.phone),
    created_at: dtToIso(r.created_at),
    created_by: strOf(r.created_by),
    last_login_at: dtToIso(r.last_login_at),
  };
}

function mapDbRole(r: Row): AdminRoleRecord {
  const base = {
    name: strOf(r.name),
    is_builtin: boolOf(r.is_builtin),
    version: Number(r.version) || 0,
    created_at: dtToIso(r.created_at),
    created_by: strOf(r.created_by),
  };
  const perms = {} as Record<PermKey, boolean>;
  for (const k of PERM_KEYS) perms[k] = boolOf(r[k]);
  return { ...base, ...perms };
}

function mapDbHcw(r: Row): HcwRecord {
  return {
    hcw_id: strOf(r.hcw_id),
    facility_id: strOf(r.facility_id),
    facility_name: strOf(r.facility_name),
    enrollment_token_jti: strOf(r.enrollment_token_jti),
    token_issued_at: dtToIso(r.token_issued_at),
    token_revoked_at: dtToIso(r.token_revoked_at),
    status: strOf(r.status),
    created_at: dtToIso(r.created_at),
    qn: strOf(r.qn),
    enroll_slug: strOf(r.enroll_slug),
    claimed_at: dtToIso(r.claimed_at),
  };
}

// Shared count fragments (spec F2-Coverage-Report-2026-07-17, decision 3): the
// Facilities overview and the Coverage report aggregate responses/HCWs with the
// SAME SQL so the two surfaces can never disagree on a count. `where` scopes
// the response aggregates to a date window ('' = all time, overview's use).
const respCountsSubquery = (where: string): string => `SELECT facility_id,
       SUM(CASE WHEN status <> 'refusal' THEN 1 ELSE 0 END) AS submitted,
       SUM(CASE WHEN status = 'refusal' THEN 1 ELSE 0 END) AS refusals,
       SUM(CASE WHEN status <> 'refusal' AND source_path='paper_encoded' THEN 1 ELSE 0 END) AS paper_encoded,
       MAX(submitted_at_server) AS last_activity
  FROM f2_responses${where ? `${where} AND status <> 'voided'` : " WHERE status <> 'voided'"} GROUP BY facility_id`;

const IN_PROGRESS_SUBQUERY = `SELECT facility_id, COUNT(*) AS in_progress
  FROM f2_hcws WHERE hcw_id LIKE 'sr-%' AND status='enrolled' GROUP BY facility_id`;

function mapDbFacilityMaster(r: Row): FacilityMasterRecord {
  return {
    facility_id: strOf(r.facility_id),
    facility_name: strOf(r.facility_name),
    facility_type: strOf(r.facility_type),
    region: strOf(r.region),
    province: strOf(r.province),
    city_mun: strOf(r.city_mun),
    barangay: strOf(r.barangay),
    archived: boolOf(r.archived),
    target_hcws: r.target_hcws == null ? null : Number(r.target_hcws),
  };
}

function mapDbFacilitySlug(r: Row): FacilitySlugRecord {
  return {
    slug: strOf(r.slug),
    facility_id: strOf(r.facility_id),
    facility_name: strOf(r.facility_name),
    active: boolOf(r.active),
    created_at: dtToIso(r.created_at),
    created_by: strOf(r.created_by),
  };
}

function mapDbResponse(r: Row): ResponseRow {
  return {
    submission_id: strOf(r.submission_id),
    client_submission_id: strOf(r.client_submission_id),
    submitted_at_server: dtToIso(r.submitted_at_server),
    submitted_at_client: dtToIso(r.submitted_at_client),
    source: strOf(r.source),
    spec_version: strOf(r.spec_version),
    app_version: strOf(r.app_version),
    hcw_id: strOf(r.hcw_id),
    facility_id: strOf(r.facility_id),
    device_fingerprint: strOf(r.device_fingerprint),
    sync_attempt_count: r.sync_attempt_count == null ? '' : String(r.sync_attempt_count),
    status: strOf(r.status),
    values_json: jsonStrOf(r.values_json),
    submission_lat: r.submission_lat == null ? '' : String(r.submission_lat),
    submission_lng: r.submission_lng == null ? '' : String(r.submission_lng),
    gps_status: strOf(r.gps_status),
    source_path: strOf(r.source_path),
    encoded_by: strOf(r.encoded_by),
    encoded_at: dtToIso(r.encoded_at),
    qn: strOf(r.qn),
  };
}

function mapDbAudit(r: Row): AuditRecord {
  return {
    audit_id: strOf(r.audit_id),
    occurred_at_server: dtToIso(r.occurred_at_server),
    occurred_at_client: strOf(r.occurred_at_client),
    event_type: strOf(r.event_type),
    hcw_id: strOf(r.hcw_id),
    facility_id: strOf(r.facility_id),
    app_version: strOf(r.app_version),
    payload_json: jsonStrOf(r.payload_json),
    actor_username: strOf(r.actor_username),
    actor_jti: strOf(r.actor_jti),
    actor_role: strOf(r.actor_role),
    event_resource: strOf(r.event_resource),
    event_payload_json: jsonStrOf(r.event_payload_json),
    client_ip_hash: strOf(r.client_ip_hash),
    request_id: strOf(r.request_id),
  };
}

function mapDbDlq(r: Row): DlqRow {
  return {
    dlq_id: strOf(r.dlq_id),
    received_at_server: dtToIso(r.received_at_server),
    client_submission_id: strOf(r.client_submission_id),
    reason: strOf(r.reason),
    payload_json: jsonStrOf(r.payload_json),
  };
}

function mapDbFile(r: Row): FileMetaRecord {
  return {
    file_id: strOf(r.file_id),
    filename: strOf(r.filename),
    content_type: strOf(r.content_type),
    size_bytes: Number(r.size_bytes) || 0,
    uploaded_by: strOf(r.uploaded_by),
    uploaded_at: dtToIso(r.uploaded_at),
    description: strOf(r.description),
    deleted_at: dtToIso(r.deleted_at),
    folder_path: strOf(r.folder_path) || '/',
    is_folder: boolOf(r.is_folder),
  };
}

export class MySqlAdminStore implements AdminStore {
  constructor(private pool: mysql.Pool) {}

  private async q<T extends Row = Row>(sql: string, params: unknown[] = []): Promise<T[]> {
    const [rows] = await this.pool.query<T[]>(sql, params);
    return rows;
  }

  // -- users -----------------------------------------------------------------
  async getUserAuth(username: string) {
    const rows = await this.q('SELECT * FROM f2_users WHERE username=? LIMIT 1', [username]);
    return rows.length ? mapDbUser(rows[0]!) : null;
  }

  async listUsers(f: UsersFilters) {
    const where: string[] = [];
    const params: unknown[] = [];
    if (f.role_name) {
      where.push('role_name=?');
      params.push(f.role_name);
    }
    if (f.username) {
      where.push('username=?');
      params.push(f.username);
    }
    if (f.q) {
      where.push("LOWER(CONCAT_WS(' ', username, first_name, last_name, email)) LIKE ?");
      params.push(`%${f.q.toLowerCase()}%`);
    }
    const sql = `SELECT * FROM f2_users${where.length ? ' WHERE ' + where.join(' AND ') : ''} ORDER BY created_at DESC LIMIT ${SCAN_CAP}`;
    return (await this.q(sql, params)).map(mapDbUser);
  }

  async insertUser(rec: AdminUserRecord) {
    try {
      await this.pool.query(
        `INSERT INTO f2_users (username, first_name, last_name, role_name, password_hash,
           password_must_change, email, phone, created_at, created_by, last_login_at)
         VALUES (?,?,?,?,?,?,?,?,?,?,?)`,
        [
          rec.username, rec.first_name, rec.last_name, rec.role_name, rec.password_hash,
          rec.password_must_change ? 1 : 0, rec.email, rec.phone,
          isoToDt(rec.created_at), rec.created_by, isoToDt(rec.last_login_at),
        ],
      );
      return 'created' as const;
    } catch (err) {
      if ((err as { code?: string }).code === 'ER_DUP_ENTRY') return 'conflict' as const;
      throw err;
    }
  }

  async replaceUser(rec: AdminUserRecord) {
    await this.pool.query(
      `UPDATE f2_users SET first_name=?, last_name=?, role_name=?, password_hash=?,
         password_must_change=?, email=?, phone=? WHERE username=?`,
      [
        rec.first_name, rec.last_name, rec.role_name, rec.password_hash,
        rec.password_must_change ? 1 : 0, rec.email, rec.phone, rec.username,
      ],
    );
  }

  async deleteUser(username: string) {
    const [res] = await this.pool.query<mysql.ResultSetHeader>(
      'DELETE FROM f2_users WHERE username=?',
      [username],
    );
    return res.affectedRows > 0;
  }

  async countUsersWithRole(roleName: string) {
    const rows = await this.q('SELECT COUNT(*) AS n FROM f2_users WHERE role_name=?', [roleName]);
    return Number(rows[0]?.n ?? 0);
  }

  async touchLastLogin(username: string, ts: string) {
    await this.pool.query('UPDATE f2_users SET last_login_at=? WHERE username=?', [
      isoToDt(ts),
      username,
    ]);
  }

  // -- roles -----------------------------------------------------------------
  async listRoles() {
    const rows = await this.q('SELECT * FROM f2_roles ORDER BY is_builtin DESC, name ASC');
    return rows.map(mapDbRole);
  }

  async getRole(name: string) {
    const rows = await this.q('SELECT * FROM f2_roles WHERE name=? LIMIT 1', [name]);
    return rows.length ? mapDbRole(rows[0]!) : null;
  }

  async insertRole(rec: AdminRoleRecord) {
    try {
      await this.pool.query(
        `INSERT INTO f2_roles (name, is_builtin, version,
           dash_data, dash_report, dash_apps, dash_users, dash_roles,
           dict_self_admin_up, dict_self_admin_down,
           dict_paper_encoded_up, dict_paper_encoded_down,
           dict_capi_up, dict_capi_down, created_at, created_by)
         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
        [
          rec.name, rec.is_builtin ? 1 : 0, rec.version,
          ...PERM_KEYS.map((k) => (rec[k] ? 1 : 0)),
          isoToDt(rec.created_at), rec.created_by,
        ],
      );
      return 'created' as const;
    } catch (err) {
      if ((err as { code?: string }).code === 'ER_DUP_ENTRY') return 'conflict' as const;
      throw err;
    }
  }

  async replaceRole(rec: AdminRoleRecord) {
    await this.pool.query(
      `UPDATE f2_roles SET version=?,
         dash_data=?, dash_report=?, dash_apps=?, dash_users=?, dash_roles=?,
         dict_self_admin_up=?, dict_self_admin_down=?,
         dict_paper_encoded_up=?, dict_paper_encoded_down=?,
         dict_capi_up=?, dict_capi_down=?
       WHERE name=?`,
      [rec.version, ...PERM_KEYS.map((k) => (rec[k] ? 1 : 0)), rec.name],
    );
  }

  async deleteRoleRow(name: string) {
    const [res] = await this.pool.query<mysql.ResultSetHeader>(
      'DELETE FROM f2_roles WHERE name=?',
      [name],
    );
    return res.affectedRows > 0;
  }

  // -- hcws ------------------------------------------------------------------
  async listHcws(f: HcwFilters) {
    const where: string[] = [];
    const params: unknown[] = [];
    if (f.facility_id) {
      where.push('facility_id=?');
      params.push(f.facility_id);
    }
    if (f.status) {
      where.push('status=?');
      params.push(f.status);
    }
    if (f.hcw_id) {
      where.push('hcw_id=?');
      params.push(f.hcw_id);
    }
    if (f.from) {
      where.push('created_at >= ?');
      params.push(isoToDt(f.from));
    }
    if (f.to) {
      where.push('created_at < ?');
      params.push(isoToDt(f.to));
    }
    if (f.q) {
      where.push(
        "LOWER(CONCAT_WS(' ', hcw_id, facility_id, facility_name, enrollment_token_jti, status, COALESCE(qn,''))) LIKE ?",
      );
      params.push(`%${f.q.toLowerCase()}%`);
    }
    const w = where.length ? ' WHERE ' + where.join(' AND ') : '';
    const limit = normLimit(f.limit);
    const offset = normOffset(f.offset);
    const rows = await this.q(
      `SELECT * FROM f2_hcws${w} ORDER BY created_at DESC LIMIT ? OFFSET ?`,
      [...params, limit, offset],
    );
    const count = await this.q(`SELECT COUNT(*) AS n FROM f2_hcws${w}`, params);
    const total = Number(count[0]?.n ?? 0);
    return { rows: rows.map(mapDbHcw), total, has_more: offset + rows.length < total };
  }

  async createHcw(p: CreateHcwInput): Promise<CreateHcwResult> {
    // MySQL transaction replaces the AS ScriptLock; SELECT … FOR UPDATE keeps
    // two concurrent creates at one facility from double-assigning a sequence,
    // and the UNIQUE KEY on qn is the backstop.
    const conn = await this.pool.getConnection();
    try {
      await conn.beginTransaction();
      const [dups] = await conn.query<Row[]>(
        "SELECT 1 FROM f2_hcws WHERE hcw_id=? AND status<>'revoked' LIMIT 1 FOR UPDATE",
        [p.hcw_id],
      );
      if (dups.length) {
        await conn.rollback();
        return { ok: false, code: 'E_CONFLICT', message: `hcw_id ${p.hcw_id} already enrolled` };
      }
      let qn = p.qn.trim();
      if (qn) {
        if (!/^\d{12}$/.test(qn)) {
          await conn.rollback();
          return { ok: false, code: 'E_VALIDATION', message: 'qn must be exactly 12 digits' };
        }
        const [qrows] = await conn.query<Row[]>(
          'SELECT 1 FROM f2_hcws WHERE qn=? LIMIT 1 FOR UPDATE',
          [qn],
        );
        if (qrows.length) {
          await conn.rollback();
          return { ok: false, code: 'E_CONFLICT', message: `qn ${qn} already assigned` };
        }
      } else if (/^\d{9}$/.test(p.facility_id)) {
        const [mrows] = await conn.query<Row[]>(
          `SELECT MAX(CAST(SUBSTRING(qn, 10, 3) AS UNSIGNED)) AS max_seq
             FROM f2_hcws WHERE qn LIKE CONCAT(?, '%') AND CHAR_LENGTH(qn)=12 FOR UPDATE`,
          [p.facility_id],
        );
        // Start at the F2 block floor, never at 001 — 001..099 belong to F3 patients
        // at this same facility, and f2_hcws cannot see CSPro's keys.
        const maxSeq = Math.max(Number(mrows[0]?.max_seq ?? 0), F2_QN_SEQ_FLOOR);
        if (maxSeq >= 999) {
          await conn.rollback();
          return {
            ok: false,
            code: 'E_VALIDATION',
            message: `facility ${p.facility_id} HCW sequence exhausted (999)`,
          };
        }
        qn = p.facility_id + String(maxSeq + 1).padStart(3, '0');
      }
      const nowIso = new Date().toISOString();
      await conn.query(
        `INSERT INTO f2_hcws (hcw_id, facility_id, facility_name, enrollment_token_jti,
           token_issued_at, token_revoked_at, status, created_at, qn)
         VALUES (?,?,?,?,?,NULL,?,?,?)`,
        [
          p.hcw_id, p.facility_id, p.facility_name || null, null,
          isoToDt(nowIso), p.status || 'enrolled', isoToDt(nowIso), qn || null,
        ],
      );
      await conn.commit();
      return { ok: true, hcw_id: p.hcw_id, qn };
    } catch (err) {
      await conn.rollback().catch(() => undefined);
      if ((err as { code?: string }).code === 'ER_DUP_ENTRY') {
        return { ok: false, code: 'E_CONFLICT', message: 'hcw_id or qn already exists' };
      }
      throw err;
    } finally {
      conn.release();
    }
  }

  async reissueHcwToken(p: { hcw_id: string; new_jti: string; prev_jti: string }): Promise<ReissueResult> {
    const conn = await this.pool.getConnection();
    try {
      await conn.beginTransaction();
      const [rows] = await conn.query<Row[]>(
        'SELECT * FROM f2_hcws WHERE hcw_id=? LIMIT 1 FOR UPDATE',
        [p.hcw_id],
      );
      if (!rows.length) {
        await conn.rollback();
        return { ok: false, code: 'E_NOT_FOUND', message: `hcw_id ${p.hcw_id} not found` };
      }
      const row = mapDbHcw(rows[0]!);
      const currentJti = row.enrollment_token_jti || '';
      if (currentJti !== (p.prev_jti || '')) {
        await conn.rollback();
        return {
          ok: false,
          code: 'E_CAS_FAILED',
          message: 'token already reissued by another admin; refresh and retry',
        };
      }
      const nowIso = new Date().toISOString();
      await conn.query(
        `UPDATE f2_hcws SET enrollment_token_jti=?, token_issued_at=?,
           token_revoked_at=${currentJti ? '?' : 'token_revoked_at'}, status='enrolled'
         WHERE hcw_id=?`,
        currentJti
          ? [p.new_jti, isoToDt(nowIso), isoToDt(nowIso), p.hcw_id]
          : [p.new_jti, isoToDt(nowIso), p.hcw_id],
      );
      await conn.commit();
      return {
        ok: true,
        hcw_id: p.hcw_id,
        facility_id: row.facility_id,
        qn: row.qn || '',
        new_jti: p.new_jti,
        old_jti: currentJti,
        token_issued_at: nowIso,
      };
    } catch (err) {
      await conn.rollback().catch(() => undefined);
      throw err;
    } finally {
      conn.release();
    }
  }

  // -- numbered short-link claim (Model C) -----------------------------------
  async listFacilitySlotsForLinks(facilityId: string): Promise<FacilitySlot[]> {
    const rows = await this.q(
      `SELECT hcw_id, qn, facility_name, enroll_slug,
              (enroll_secret_hmac IS NOT NULL AND enroll_secret_hmac <> '') AS has_secret
         FROM f2_hcws
        WHERE facility_id=? AND status<>'revoked' AND qn IS NOT NULL AND CHAR_LENGTH(qn)=12
        ORDER BY qn ASC`,
      [facilityId],
    );
    return rows.map((r) => ({
      hcw_id: strOf(r.hcw_id),
      qn: strOf(r.qn),
      facility_name: strOf(r.facility_name),
      enroll_slug: strOf(r.enroll_slug),
      has_secret: Number(r.has_secret) === 1,
    }));
  }

  async assignEnrollLink(p: { hcw_id: string; slug: string; secret_hmac: string }) {
    await this.pool.query(
      'UPDATE f2_hcws SET enroll_slug=?, enroll_secret_hmac=?, claimed_at=NULL WHERE hcw_id=?',
      [p.slug, p.secret_hmac, p.hcw_id],
    );
  }

  async getEnrollLinkBySlug(slug: string): Promise<EnrollLinkRow | null> {
    const rows = await this.q(
      'SELECT hcw_id, facility_id, qn, status, enroll_secret_hmac FROM f2_hcws WHERE enroll_slug=? LIMIT 1',
      [slug],
    );
    if (!rows.length) return null;
    const r = rows[0]!;
    return {
      hcw_id: strOf(r.hcw_id),
      facility_id: strOf(r.facility_id),
      qn: strOf(r.qn),
      status: strOf(r.status),
      enroll_secret_hmac: strOf(r.enroll_secret_hmac),
    };
  }

  async markClaimed(hcwId: string) {
    await this.pool.query(
      'UPDATE f2_hcws SET claimed_at=? WHERE hcw_id=? AND claimed_at IS NULL',
      [isoToDt(new Date().toISOString()), hcwId],
    );
  }

  // -- facility slug links -----------------------------------------------------
  async upsertFacilitySlug(rec: FacilitySlugRecord) {
    await this.pool.query(
      `INSERT INTO f2_facility_slugs (slug, facility_id, facility_name, active, created_at, created_by)
       VALUES (?,?,?,?,?,?)
       ON DUPLICATE KEY UPDATE facility_id=VALUES(facility_id),
         facility_name=VALUES(facility_name), active=VALUES(active)`,
      [rec.slug, rec.facility_id, rec.facility_name, rec.active ? 1 : 0, isoToDt(rec.created_at), rec.created_by],
    );
  }

  async listFacilitySlugs() {
    const rows = await this.q('SELECT * FROM f2_facility_slugs ORDER BY created_at DESC, slug ASC');
    return rows.map(mapDbFacilitySlug);
  }

  async getFacilitySlug(slug: string) {
    const rows = await this.q('SELECT * FROM f2_facility_slugs WHERE slug=? LIMIT 1', [slug]);
    return rows.length ? mapDbFacilitySlug(rows[0]!) : null;
  }

  async listFacilitiesOverview(f: FacilityOverviewFilters): Promise<Paged<FacilityOverviewRow>> {
    const where: string[] = [];
    const params: unknown[] = [];
    if (f.region) {
      where.push('m.region=?');
      params.push(f.region);
    }
    if (f.province) {
      where.push('m.province=?');
      params.push(f.province);
    }
    if (f.facility_type) {
      where.push('m.facility_type=?');
      params.push(f.facility_type);
    }
    if (f.q) {
      where.push('(LOWER(m.facility_name) LIKE ? OR m.facility_id LIKE ?)');
      params.push(`%${f.q.toLowerCase()}%`, `%${f.q}%`);
    }
    if (f.has_link === true) where.push('s.slug IS NOT NULL');
    if (f.has_link === false) where.push('s.slug IS NULL');
    if (!f.include_archived) where.push('m.archived=0');
    const w = where.length ? ' WHERE ' + where.join(' AND ') : '';
    // One slug per facility: prefer active, then newest, then slug asc (MySQL 8
    // window function; mirrored by the InMemory ranked-sort dedup).
    const slugJoin = `LEFT JOIN (
        SELECT facility_id, slug, active FROM (
          SELECT facility_id, slug, active,
                 ROW_NUMBER() OVER (PARTITION BY facility_id
                   ORDER BY active DESC, created_at DESC, slug ASC) AS rn
            FROM f2_facility_slugs) ranked WHERE rn=1
      ) s ON s.facility_id = m.facility_id`;
    const limit = normLimit(f.limit);
    const offset = normOffset(f.offset);
    const rows = await this.q(
      `SELECT m.facility_id, m.facility_name, m.facility_type, m.region, m.province, m.city_mun,
              m.archived AS archived, m.target_hcws AS target_hcws,
              COALESCE(s.slug,'') AS slug, s.active AS active,
              COALESCE(r.submitted,0) AS submitted, COALESCE(r.refusals,0) AS refusals,
              COALESCE(h.in_progress,0) AS in_progress
         FROM f2_facility_master m
         ${slugJoin}
         LEFT JOIN (${respCountsSubquery('')}) r ON r.facility_id = m.facility_id
         LEFT JOIN (${IN_PROGRESS_SUBQUERY}) h ON h.facility_id = m.facility_id
         ${w}
        ORDER BY m.region ASC, m.province ASC, m.facility_name ASC
        LIMIT ? OFFSET ?`,
      [...params, limit, offset],
    );
    const count = await this.q(
      `SELECT COUNT(*) AS n FROM f2_facility_master m ${slugJoin}${w}`,
      params,
    );
    const total = Number(count[0]?.n ?? 0);
    return {
      rows: rows.map((r) => ({
        facility_id: strOf(r.facility_id),
        facility_name: strOf(r.facility_name),
        facility_type: strOf(r.facility_type),
        region: strOf(r.region),
        province: strOf(r.province),
        city_mun: strOf(r.city_mun),
        archived: boolOf(r.archived),
        target_hcws: r.target_hcws == null ? null : Number(r.target_hcws),
        slug: strOf(r.slug),
        active: r.active == null ? null : boolOf(r.active),
        submitted: Number(r.submitted) || 0,
        refusals: Number(r.refusals) || 0,
        in_progress: Number(r.in_progress) || 0,
      })),
      total,
      has_more: offset + rows.length < total,
    };
  }

  // -- facility master management ----------------------------------------------
  async createFacility(rec: FacilityMasterInput) {
    try {
      await this.pool.query(
        `INSERT INTO f2_facility_master (facility_id, facility_name, facility_type, region, province, city_mun, barangay, archived, target_hcws)
         VALUES (?,?,?,?,?,?,?,0,?)`,
        [
          rec.facility_id, rec.facility_name, rec.facility_type ?? '', rec.region ?? '',
          rec.province ?? '', rec.city_mun ?? '', rec.barangay ?? '', rec.target_hcws ?? null,
        ],
      );
      return 'created' as const;
    } catch (err) {
      if ((err as { code?: string }).code === 'ER_DUP_ENTRY') return 'conflict' as const;
      throw err;
    }
  }

  async getFacility(id: string): Promise<FacilityMasterRecord | null> {
    const rows = await this.q(
      'SELECT facility_id, facility_name, facility_type, region, province, city_mun, barangay, archived, target_hcws FROM f2_facility_master WHERE facility_id=? LIMIT 1',
      [id],
    );
    if (!rows.length) return null;
    return mapDbFacilityMaster(rows[0]!);
  }

  async updateFacility(
    id: string,
    patch: Partial<FacilityMasterInput> & { archived?: boolean },
  ): Promise<FacilityMasterRecord | null> {
    // Existence check first — MySQL's affectedRows counts CHANGED rows, so a
    // no-op edit (same values) would otherwise read as "not found".
    const existing = await this.getFacility(id);
    if (!existing) return null;
    const sets: string[] = [];
    const params: unknown[] = [];
    for (const k of ['facility_name', 'facility_type', 'region', 'province', 'city_mun', 'barangay'] as const) {
      if (patch[k] !== undefined) {
        sets.push(`${k}=?`);
        params.push(patch[k]);
      }
    }
    if (patch.archived !== undefined) {
      sets.push('archived=?');
      params.push(patch.archived ? 1 : 0);
    }
    if (patch.target_hcws !== undefined) {
      sets.push('target_hcws=?');
      params.push(patch.target_hcws);
    }
    if (sets.length) {
      await this.pool.query(`UPDATE f2_facility_master SET ${sets.join(', ')} WHERE facility_id=?`, [
        ...params,
        id,
      ]);
    }
    return this.getFacility(id);
  }

  async coverageReport(f: CoverageFilters): Promise<CoverageReportData> {
    const dateWhere: string[] = [];
    const dateParams: unknown[] = [];
    if (f.from) {
      dateWhere.push('submitted_at_server >= ?');
      dateParams.push(isoToDt(f.from));
    }
    if (f.to) {
      dateWhere.push('submitted_at_server < ?');
      dateParams.push(isoToDt(f.to));
    }
    const rw = dateWhere.length ? ' WHERE ' + dateWhere.join(' AND ') : '';

    const facRows = await this.q(
      `SELECT m.facility_id, m.facility_name, m.region, m.province, m.target_hcws,
              COALESCE(r.submitted,0) AS submitted, COALESCE(r.refusals,0) AS refusals,
              COALESCE(r.paper_encoded,0) AS paper_encoded, r.last_activity,
              COALESCE(h.in_progress,0) AS started,
              EXISTS(SELECT 1 FROM f2_facility_slugs s
                      WHERE s.facility_id=m.facility_id AND s.active=1) AS link_active
         FROM f2_facility_master m
         LEFT JOIN (${respCountsSubquery(rw)}) r ON r.facility_id = m.facility_id
         LEFT JOIN (${IN_PROGRESS_SUBQUERY}) h ON h.facility_id = m.facility_id
         ${f.include_archived ? '' : 'WHERE m.archived=0'}`,
      dateParams,
    );
    const facilities: CoverageFacility[] = facRows.map((r) => ({
      facility_id: strOf(r.facility_id),
      facility_name: strOf(r.facility_name),
      region: strOf(r.region),
      province: strOf(r.province),
      link_active: boolOf(r.link_active),
      target_hcws: r.target_hcws == null ? null : Number(r.target_hcws),
      started: Number(r.started) || 0,
      submitted: Number(r.submitted) || 0,
      refusals: Number(r.refusals) || 0,
      paper_encoded: Number(r.paper_encoded) || 0,
      last_activity: dtToIso(r.last_activity),
    }));

    // Responses whose facility_id has no master row — surfaced, never dropped.
    const orphanDates = dateWhere.map((w) => 'r.' + w);
    const orphanRows = await this.q(
      `SELECT r.facility_id,
              SUM(CASE WHEN r.status <> 'refusal' THEN 1 ELSE 0 END) AS submitted,
              SUM(CASE WHEN r.status = 'refusal' THEN 1 ELSE 0 END) AS refusals,
              SUM(CASE WHEN r.status <> 'refusal' AND r.source_path='paper_encoded' THEN 1 ELSE 0 END) AS paper_encoded,
              MAX(r.submitted_at_server) AS last_activity
         FROM f2_responses r
         LEFT JOIN f2_facility_master m ON m.facility_id = r.facility_id
        WHERE m.facility_id IS NULL AND r.status <> 'voided'${orphanDates.length ? ' AND ' + orphanDates.join(' AND ') : ''}
        GROUP BY r.facility_id`,
      dateParams,
    );
    const orphans: CoverageOrphan[] = orphanRows.map((r) => ({
      facility_id: strOf(r.facility_id),
      submitted: Number(r.submitted) || 0,
      refusals: Number(r.refusals) || 0,
      paper_encoded: Number(r.paper_encoded) || 0,
      last_activity: dtToIso(r.last_activity),
    }));

    return rollupCoverage(f.level, facilities, orphans);
  }

  // -- data dashboards ---------------------------------------------------------
  async listResponses(f: RespFilters) {
    const where: string[] = [];
    const params: unknown[] = [];
    if (f.from) {
      where.push('submitted_at_server >= ?');
      params.push(isoToDt(f.from));
    }
    if (f.to) {
      where.push('submitted_at_server < ?');
      params.push(isoToDt(f.to));
    }
    if (f.facility_id) {
      where.push('facility_id=?');
      params.push(f.facility_id);
    }
    if (f.status) {
      where.push('status=?');
      params.push(f.status);
    }
    if (f.source_path) {
      where.push('source_path=?');
      params.push(f.source_path);
    }
    if (f.q) {
      // CAST(json AS CHAR) yields utf8mb4_bin; without an explicit COLLATE the
      // CONCAT_WS aggregate has no determinable collation and the LIKE dies with
      // "Illegal mix of collations (utf8mb4_bin,NONE)" (prod 500, 2026-07-17).
      where.push(
        "LOWER(CONCAT_WS(' ', submission_id, client_submission_id, hcw_id, facility_id, status, source_path, spec_version, app_version, device_fingerprint, encoded_by, COALESCE(qn,''), CAST(values_json AS CHAR) COLLATE utf8mb4_general_ci)) LIKE ?",
      );
      params.push(`%${f.q.toLowerCase()}%`);
    }
    const w = where.length ? ' WHERE ' + where.join(' AND ') : '';
    const limit = normLimit(f.limit);
    const offset = normOffset(f.offset);
    const rows = await this.q(
      `SELECT * FROM f2_responses${w} ORDER BY submitted_at_server DESC LIMIT ? OFFSET ?`,
      [...params, limit, offset],
    );
    const count = await this.q(`SELECT COUNT(*) AS n FROM f2_responses${w}`, params);
    const total = Number(count[0]?.n ?? 0);
    return { rows: rows.map(mapDbResponse), total, has_more: offset + rows.length < total };
  }

  async getResponseById(id: string) {
    const rows = await this.q('SELECT * FROM f2_responses WHERE submission_id=? LIMIT 1', [id]);
    return rows.length ? mapDbResponse(rows[0]!) : null;
  }

  async voidResponse(id: string, reason: string) {
    const rows = await this.q(
      'SELECT status, hcw_id, facility_id FROM f2_responses WHERE submission_id=? LIMIT 1',
      [id],
    );
    if (!rows.length) return { ok: false as const, code: 'E_NOT_FOUND' as const };
    const prev = strOf(rows[0]!.status);
    if (prev === 'voided') return { ok: false as const, code: 'E_ALREADY_VOIDED' as const };
    await this.pool.query("UPDATE f2_responses SET status='voided' WHERE submission_id=?", [id]);
    await this.writeAudit({
      event_type: 'response_voided',
      hcw_id: strOf(rows[0]!.hcw_id),
      facility_id: strOf(rows[0]!.facility_id),
      payload_json: JSON.stringify({ submission_id: id, reason, prev_status: prev }),
    });
    return { ok: true as const, submission_id: id, prev_status: prev };
  }

  async listAudit(f: AuditFilters) {
    const where: string[] = [];
    const params: unknown[] = [];
    if (f.from) {
      where.push('occurred_at_server >= ?');
      params.push(isoToDt(f.from));
    }
    if (f.to) {
      where.push('occurred_at_server < ?');
      params.push(isoToDt(f.to));
    }
    if (f.event_type) {
      where.push('event_type=?');
      params.push(f.event_type);
    }
    if (f.hcw_id) {
      where.push('hcw_id=?');
      params.push(f.hcw_id);
    }
    if (f.actor_username) {
      where.push('actor_username=?');
      params.push(f.actor_username);
    }
    if (f.q) {
      // Same collation trap as listResponses: JSON casts need an explicit COLLATE.
      where.push(
        "LOWER(CONCAT_WS(' ', COALESCE(audit_id,''), event_type, COALESCE(hcw_id,''), COALESCE(facility_id,''), COALESCE(actor_username,''), COALESCE(actor_role,''), COALESCE(event_resource,''), COALESCE(CAST(payload_json AS CHAR) COLLATE utf8mb4_general_ci,''), COALESCE(CAST(event_payload_json AS CHAR) COLLATE utf8mb4_general_ci,''))) LIKE ?",
      );
      params.push(`%${f.q.toLowerCase()}%`);
    }
    const w = where.length ? ' WHERE ' + where.join(' AND ') : '';
    const limit = normLimit(f.limit);
    const offset = normOffset(f.offset);
    const rows = await this.q(
      `SELECT * FROM f2_audit${w} ORDER BY occurred_at_server DESC, id DESC LIMIT ? OFFSET ?`,
      [...params, limit, offset],
    );
    const count = await this.q(`SELECT COUNT(*) AS n FROM f2_audit${w}`, params);
    const total = Number(count[0]?.n ?? 0);
    return { rows: rows.map(mapDbAudit), total, has_more: offset + rows.length < total };
  }

  async listAuditEventTypes() {
    const rows = await this.q(
      "SELECT DISTINCT event_type FROM f2_audit WHERE event_type IS NOT NULL AND event_type <> '' ORDER BY event_type ASC",
      [],
    );
    return rows.map((r) => strOf(r.event_type));
  }

  async listDlq(f: DlqFilters) {
    const where: string[] = [];
    const params: unknown[] = [];
    if (f.from) {
      where.push('received_at_server >= ?');
      params.push(isoToDt(f.from));
    }
    if (f.to) {
      where.push('received_at_server < ?');
      params.push(isoToDt(f.to));
    }
    if (f.q) {
      // Same collation trap as listResponses: JSON cast needs an explicit COLLATE.
      where.push(
        "LOWER(CONCAT_WS(' ', dlq_id, COALESCE(client_submission_id,''), COALESCE(reason,''), COALESCE(CAST(payload_json AS CHAR) COLLATE utf8mb4_general_ci,''))) LIKE ?",
      );
      params.push(`%${f.q.toLowerCase()}%`);
    }
    const w = where.length ? ' WHERE ' + where.join(' AND ') : '';
    const limit = normLimit(f.limit);
    const offset = normOffset(f.offset);
    const rows = await this.q(
      `SELECT * FROM f2_dlq${w} ORDER BY received_at_server DESC LIMIT ? OFFSET ?`,
      [...params, limit, offset],
    );
    const count = await this.q(`SELECT COUNT(*) AS n FROM f2_dlq${w}`, params);
    const total = Number(count[0]?.n ?? 0);
    return { rows: rows.map(mapDbDlq), total, has_more: offset + rows.length < total };
  }

  async dlqFind(dlqId: string) {
    const rows = await this.q('SELECT * FROM f2_dlq WHERE dlq_id=? LIMIT 1', [dlqId]);
    return rows.length ? mapDbDlq(rows[0]!) : null;
  }

  async dlqDelete(dlqId: string) {
    const [res] = await this.pool.query<mysql.ResultSetHeader>(
      'DELETE FROM f2_dlq WHERE dlq_id=?',
      [dlqId],
    );
    return res.affectedRows > 0;
  }

  async readResponsesLite(cap = SCAN_CAP) {
    const rows = await this.q(
      `SELECT submission_id, hcw_id, facility_id, submitted_at_server, spec_version,
              status, submission_lat, submission_lng, gps_status
         FROM f2_responses WHERE COALESCE(status,'') <> 'voided' LIMIT ?`,
      [cap],
    );
    return rows.map((r) => ({
      submission_id: strOf(r.submission_id),
      hcw_id: strOf(r.hcw_id),
      facility_id: strOf(r.facility_id),
      submitted_at_server: dtToIso(r.submitted_at_server),
      spec_version: strOf(r.spec_version),
      status: strOf(r.status),
      submission_lat: r.submission_lat == null ? null : Number(r.submission_lat),
      submission_lng: r.submission_lng == null ? null : Number(r.submission_lng),
      gps_status: strOf(r.gps_status),
    }));
  }

  // -- audit write ---------------------------------------------------------------
  async writeAudit(entry: Partial<AuditRecord> & { event_type: string }) {
    await this.pool.query(
      `INSERT INTO f2_audit (audit_id, occurred_at_server, occurred_at_client, event_type,
         hcw_id, facility_id, app_version, payload_json, actor_username, actor_jti,
         actor_role, event_resource, event_payload_json, client_ip_hash, request_id)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
      [
        entry.audit_id || null,
        isoToDt(new Date().toISOString()),
        entry.occurred_at_client || null,
        entry.event_type,
        entry.hcw_id || null,
        entry.facility_id || null,
        entry.app_version || null,
        entry.payload_json || null,
        entry.actor_username || null,
        entry.actor_jti || null,
        entry.actor_role || null,
        entry.event_resource || null,
        entry.event_payload_json || null,
        entry.client_ip_hash || null,
        entry.request_id || null,
      ],
    );
  }

  // -- config ---------------------------------------------------------------------
  async setConfig(key: string, value: string) {
    const rows = await this.q('SELECT 1 FROM f2_config WHERE k=? LIMIT 1', [key]);
    if (!rows.length) return false;
    await this.pool.query('UPDATE f2_config SET v=? WHERE k=?', [value, key]);
    return true;
  }

  // -- files ------------------------------------------------------------------------
  async listFiles(f: { q?: string; path?: string }) {
    const where: string[] = ['deleted_at IS NULL'];
    const params: unknown[] = [];
    const pathFilter = f.path && f.path !== '/' ? f.path : null;
    if (pathFilter) {
      where.push('folder_path = ?');
      params.push(pathFilter);
    } else {
      where.push("(folder_path IS NULL OR folder_path='' OR folder_path='/')");
    }
    if (f.q) {
      where.push("LOWER(CONCAT_WS(' ', filename, COALESCE(description,''), uploaded_by)) LIKE ?");
      params.push(`%${f.q.toLowerCase()}%`);
    }
    const rows = await this.q(
      `SELECT * FROM f2_files WHERE ${where.join(' AND ')} ORDER BY uploaded_at DESC LIMIT ${SCAN_CAP}`,
      params,
    );
    const files = rows.map(mapDbFile);
    return { files, total: files.length };
  }

  async getFileMeta(fileId: string) {
    const rows = await this.q('SELECT * FROM f2_files WHERE file_id=? LIMIT 1', [fileId]);
    return rows.length ? mapDbFile(rows[0]!) : null;
  }

  async insertFileMeta(rec: FileMetaRecord) {
    try {
      await this.pool.query(
        `INSERT INTO f2_files (file_id, filename, content_type, size_bytes, uploaded_by,
           uploaded_at, description, deleted_at, folder_path, is_folder)
         VALUES (?,?,?,?,?,?,?,NULL,?,?)`,
        [
          rec.file_id, rec.filename, rec.content_type, rec.size_bytes, rec.uploaded_by,
          isoToDt(rec.uploaded_at), rec.description, rec.folder_path, rec.is_folder ? 1 : 0,
        ],
      );
      return 'created' as const;
    } catch (err) {
      if ((err as { code?: string }).code === 'ER_DUP_ENTRY') return 'conflict' as const;
      throw err;
    }
  }

  async updateFilename(fileId: string, newName: string) {
    await this.pool.query('UPDATE f2_files SET filename=? WHERE file_id=?', [newName, fileId]);
  }

  async softDeleteFile(fileId: string) {
    const nowIso = new Date().toISOString();
    const [res] = await this.pool.query<mysql.ResultSetHeader>(
      'UPDATE f2_files SET deleted_at=? WHERE file_id=? AND deleted_at IS NULL',
      [isoToDt(nowIso), fileId],
    );
    return res.affectedRows > 0 ? nowIso : null;
  }

  async folderExists(name: string) {
    const rows = await this.q(
      'SELECT 1 FROM f2_files WHERE is_folder=1 AND filename=? AND deleted_at IS NULL LIMIT 1',
      [name],
    );
    return rows.length > 0;
  }

  // -- kv -------------------------------------------------------------------------
  async kvGet(key: string) {
    const rows = await this.q(
      'SELECT v FROM auth_kv WHERE k=? AND (expires_at IS NULL OR expires_at > UTC_TIMESTAMP()) LIMIT 1',
      [key],
    );
    return rows.length ? String(rows[0]!.v ?? '') : null;
  }

  async kvPut(key: string, value: string, ttlSeconds?: number) {
    await this.pool.query(
      `INSERT INTO auth_kv (k, v, expires_at)
       VALUES (?, ?, ${ttlSeconds ? 'UTC_TIMESTAMP() + INTERVAL ? SECOND' : 'NULL'})
       ON DUPLICATE KEY UPDATE v=VALUES(v), expires_at=VALUES(expires_at)`,
      ttlSeconds ? [key, value, ttlSeconds] : [key, value],
    );
  }

  async kvDelete(key: string) {
    await this.pool.query('DELETE FROM auth_kv WHERE k=?', [key]);
  }

  async tokenAudit(row: TokenAuditRow) {
    await this.pool.query(
      `INSERT INTO auth_token_audit (jti, tablet_id, tablet_label, facility_id, issued_at, expires_at)
       VALUES (?,?,?,?,?,?)
       ON DUPLICATE KEY UPDATE tablet_id=VALUES(tablet_id), tablet_label=VALUES(tablet_label),
         facility_id=VALUES(facility_id), issued_at=VALUES(issued_at), expires_at=VALUES(expires_at)`,
      [
        row.jti, row.tablet_id, row.tablet_label, row.facility_id,
        isoToDt(new Date(row.issued_at * 1000).toISOString()),
        isoToDt(new Date(row.expires_at * 1000).toISOString()),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// FileStore — R2 replacement (local filesystem under F2_FILES_DIR)
// ---------------------------------------------------------------------------

export interface FileStore {
  put(fileId: string, data: Uint8Array): Promise<void>;
  get(fileId: string): Promise<Uint8Array | null>;
  delete(fileId: string): Promise<void>;
}

const FILE_ID_SAFE_RE = /^[A-Za-z0-9_-]+$/;

export class LocalFileStore implements FileStore {
  constructor(private dir: string) {}

  private pathFor(fileId: string): string {
    if (!FILE_ID_SAFE_RE.test(fileId)) throw new Error(`unsafe file id: ${fileId}`);
    return join(this.dir, fileId);
  }

  async put(fileId: string, data: Uint8Array) {
    await mkdir(this.dir, { recursive: true });
    await writeFile(this.pathFor(fileId), data);
  }

  async get(fileId: string) {
    try {
      return new Uint8Array(await readFile(this.pathFor(fileId)));
    } catch (err) {
      if ((err as NodeJS.ErrnoException).code === 'ENOENT') return null;
      throw err;
    }
  }

  async delete(fileId: string) {
    try {
      await unlink(this.pathFor(fileId));
    } catch (err) {
      if ((err as NodeJS.ErrnoException).code !== 'ENOENT') throw err;
    }
  }
}

export class InMemoryFileStore implements FileStore {
  blobs = new Map<string, Uint8Array>();

  async put(fileId: string, data: Uint8Array) {
    this.blobs.set(fileId, data);
  }

  async get(fileId: string) {
    return this.blobs.get(fileId) ?? null;
  }

  async delete(fileId: string) {
    this.blobs.delete(fileId);
  }
}
