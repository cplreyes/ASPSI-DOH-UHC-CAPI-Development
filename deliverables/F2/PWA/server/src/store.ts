/**
 * Store — the API's only seam to csweb_f2. Mirrors the AS mock-ctx discipline:
 * handlers take a Store, tests use InMemoryStore, prod uses MySqlStore.
 *
 * Table contract = csweb_f2 (deliverables/CSWeb/f2-postgres-migration/csweb_f2_schema.sql
 * for f2_responses/f2_facility_master; ddl/f2_api_tables.sql for f2_hcws/f2_config/
 * f2_dlq/auth_*). All timestamps stored as UTC DATETIME.
 */
import mysql from 'mysql2/promise';

export interface ResponseRow {
  submission_id: string;
  client_submission_id: string;
  submitted_at_server: string; // ISO — store converts to DATETIME
  submitted_at_client: string; // ISO or ''
  source: string;
  spec_version: string;
  app_version: string;
  hcw_id: string;
  facility_id: string;
  device_fingerprint: string;
  sync_attempt_count: string;
  status: string;
  values_json: string;
  submission_lat: string;
  submission_lng: string;
  /** Why coordinates are (or aren't) present — audit P1-4 instrumentation:
   *  granted | denied | timeout | unavailable | unsupported | not_requested,
   *  '' for legacy rows ingested before 2026-07-17. */
  gps_status: string;
  source_path: string;
  encoded_by: string;
  encoded_at: string;
  qn: string;
}

export interface FacilityRow {
  facility_id: string;
  facility_name: string;
  facility_type: string;
  region: string;
  province: string;
  city_mun: string;
  barangay: string;
  /** Soft-hidden from pickers/lists; data and links stay intact. Absent = false. */
  archived?: boolean;
  /** Coverage target quota (F2-Coverage-Report-2026-07-17). Absent/null = none set. */
  target_hcws?: number | null;
}

export interface DlqRow {
  dlq_id: string;
  received_at_server: string;
  client_submission_id: string;
  reason: string;
  payload_json: string;
}

export interface Store {
  findExisting(clientSubmissionId: string): Promise<{ submission_id: string } | null>;
  /** Insert; returns 'inserted' or 'duplicate' (unique-key race lost = duplicate). */
  insertResponse(row: ResponseRow): Promise<'inserted' | 'duplicate'>;
  getConfig(key: string): Promise<string>;
  readAllConfig(): Promise<Array<[string, string]>>;
  readFacilities(): Promise<FacilityRow[]>;
  /** #825 forward-only refusal tag: only flips pending/enrolled/blank rows. */
  tagRefusal(hcwId: string): Promise<void>;
  /** Forward-only submitted tag — same guard as tagRefusal. Closes the case out
   *  of the Facilities/Coverage "In progress" count and arms /claim's
   *  already-completed gate; without it sr- rows stayed 'enrolled' forever. */
  tagSubmitted(hcwId: string): Promise<void>;
  isRevoked(jti: string): Promise<boolean>;
  dlqAppend(row: DlqRow): Promise<void>;
}

export const isoToDt = (iso: string): string | null =>
  iso ? new Date(iso).toISOString().slice(0, 19).replace('T', ' ') : null;

/** Shared pool factory — index.ts creates ONE pool for MySqlStore + MySqlAdminStore. */
export function createMySqlPool(env: NodeJS.ProcessEnv): mysql.Pool {
  return mysql.createPool({
    host: env.F2_DB_HOST || 'database',
    port: Number(env.F2_DB_PORT || 3306),
    user: env.F2_DB_USER || 'f2api',
    password: env.F2_DB_PASSWORD ?? '',
    database: env.F2_DB_NAME || 'csweb_f2',
    connectionLimit: 10,
    charset: 'utf8mb4',
    timezone: 'Z',
  });
}

export class MySqlStore implements Store {
  constructor(private pool: mysql.Pool) {}

  static fromEnv(env: NodeJS.ProcessEnv): MySqlStore {
    return new MySqlStore(createMySqlPool(env));
  }

  async findExisting(csid: string) {
    const [rows] = await this.pool.query<mysql.RowDataPacket[]>(
      'SELECT submission_id FROM f2_responses WHERE client_submission_id=? LIMIT 1',
      [csid],
    );
    return rows.length ? { submission_id: String(rows[0]!.submission_id ?? '') } : null;
  }

  async insertResponse(r: ResponseRow) {
    try {
      await this.pool.query(
        `INSERT INTO f2_responses (submission_id, client_submission_id, submitted_at_server,
           submitted_at_client, source, spec_version, app_version, hcw_id, facility_id,
           device_fingerprint, sync_attempt_count, status, values_json, submission_lat,
           submission_lng, gps_status, source_path, encoded_by, encoded_at, qn)
         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
        [
          r.submission_id, r.client_submission_id, isoToDt(r.submitted_at_server),
          isoToDt(r.submitted_at_client), r.source, r.spec_version, r.app_version, r.hcw_id,
          r.facility_id, r.device_fingerprint, Number(r.sync_attempt_count) || 1, r.status,
          r.values_json, r.submission_lat === '' ? null : Number(r.submission_lat),
          r.submission_lng === '' ? null : Number(r.submission_lng), r.gps_status,
          r.source_path, r.encoded_by || null, isoToDt(r.encoded_at), r.qn || null,
        ],
      );
      return 'inserted' as const;
    } catch (err) {
      if ((err as { code?: string }).code === 'ER_DUP_ENTRY') return 'duplicate' as const;
      throw err;
    }
  }

  async getConfig(key: string) {
    const [rows] = await this.pool.query<mysql.RowDataPacket[]>(
      'SELECT v FROM f2_config WHERE k=? LIMIT 1',
      [key],
    );
    return rows.length ? String(rows[0]!.v ?? '') : '';
  }

  async readAllConfig() {
    const [rows] = await this.pool.query<mysql.RowDataPacket[]>('SELECT k, v FROM f2_config');
    return rows.map((r) => [String(r.k), String(r.v ?? '')] as [string, string]);
  }

  async readFacilities() {
    // Archived facilities disappear from the legacy PWA dropdown (spec
    // F2-Facility-Master-Mgmt-2026-07-16) — their data and links stay intact.
    const [rows] = await this.pool.query<mysql.RowDataPacket[]>(
      'SELECT facility_id, facility_name, facility_type, region, province, city_mun, barangay FROM f2_facility_master WHERE archived=0',
    );
    return rows as unknown as FacilityRow[];
  }

  async tagRefusal(hcwId: string) {
    if (!hcwId) return;
    await this.pool.query(
      `UPDATE f2_hcws SET status='refusal'
       WHERE hcw_id=? AND (status IN ('pending','enrolled') OR status='' OR status IS NULL)`,
      [hcwId],
    );
  }

  async tagSubmitted(hcwId: string) {
    if (!hcwId) return;
    await this.pool.query(
      `UPDATE f2_hcws SET status='submitted'
       WHERE hcw_id=? AND (status IN ('pending','enrolled') OR status='' OR status IS NULL)`,
      [hcwId],
    );
  }

  async isRevoked(jti: string) {
    const [rows] = await this.pool.query<mysql.RowDataPacket[]>(
      'SELECT 1 FROM auth_revoked WHERE jti=? LIMIT 1',
      [jti],
    );
    return rows.length > 0;
  }

  async dlqAppend(r: DlqRow) {
    await this.pool.query(
      `INSERT INTO f2_dlq (dlq_id, received_at_server, client_submission_id, reason, payload_json)
       VALUES (?,?,?,?,?)`,
      [r.dlq_id, isoToDt(r.received_at_server), r.client_submission_id, r.reason, r.payload_json],
    );
  }
}

/** Test double — mirrors the AS unit tests' mock ctx. */
export class InMemoryStore implements Store {
  responses = new Map<string, ResponseRow>();
  config = new Map<string, string>([
    ['current_spec_version', '2026-04-17-m1'],
    ['min_accepted_spec_version', '2026-04-17-m1'],
    ['kill_switch', 'false'],
    ['broadcast_message', ''],
  ]);
  facilities: FacilityRow[] = [];
  hcwStatus = new Map<string, string>();
  revoked = new Set<string>();
  dlq: DlqRow[] = [];

  async findExisting(csid: string) {
    const r = this.responses.get(csid);
    return r ? { submission_id: r.submission_id } : null;
  }
  async insertResponse(r: ResponseRow) {
    if (this.responses.has(r.client_submission_id)) return 'duplicate' as const;
    this.responses.set(r.client_submission_id, r);
    return 'inserted' as const;
  }
  async getConfig(key: string) {
    return this.config.get(key) ?? '';
  }
  async readAllConfig() {
    return [...this.config.entries()];
  }
  async readFacilities() {
    return this.facilities.filter((f) => !f.archived);
  }
  async tagRefusal(hcwId: string) {
    const s = this.hcwStatus.get(hcwId) ?? '';
    if (['pending', 'enrolled', ''].includes(s)) this.hcwStatus.set(hcwId, 'refusal');
  }
  async tagSubmitted(hcwId: string) {
    if (!hcwId) return;
    const s = this.hcwStatus.get(hcwId) ?? '';
    if (['pending', 'enrolled', ''].includes(s)) this.hcwStatus.set(hcwId, 'submitted');
  }
  async isRevoked(jti: string) {
    return this.revoked.has(jti);
  }
  async dlqAppend(r: DlqRow) {
    this.dlq.push(r);
  }
}
