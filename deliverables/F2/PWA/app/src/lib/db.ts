import Dexie, { type Table } from 'dexie';

export type SubmissionStatus =
  | 'pending_sync'
  | 'syncing'
  | 'synced'
  | 'rejected'
  | 'retry_scheduled';

export interface DraftRow {
  id: string;
  hcw_id: string;
  updated_at: number;
  values: Record<string, unknown>;
}

export interface LastError {
  code: string;
  message: string;
}

export interface SubmissionRow {
  client_submission_id: string;
  hcw_id: string;
  status: SubmissionStatus;
  synced_at: number | null;
  submitted_at: number;
  spec_version: string;
  values: Record<string, unknown>;
  retry_count: number;
  next_retry_at: number | null;
  last_error: LastError | null;
}

export interface FacilityRow {
  facility_id: string;
  facility_name: string;
  facility_type: string;
  region: string;
  province: string;
  city_mun: string;
  barangay: string;
}

export interface ConfigRow {
  key: string;
  value: unknown;
}

export interface AuditRow {
  id?: number;
  event: string;
  occurred_at: number;
  payload?: Record<string, unknown>;
}

export interface EnrollmentRow {
  id: 'singleton';
  hcw_id: string;
  facility_id: string;
  facility_type: string;
  enrolled_at: number;
  /**
   * Per-tablet JWT issued by the Cloudflare Worker (spec §5).
   * Optional in the type for v4-era rows; runtime-required for sync.
   * Claims (facility_id, exp) are parsed from the JWT on demand, not cached.
   */
  device_token?: string;
}

export class F2Database extends Dexie {
  drafts!: Table<DraftRow, string>;
  submissions!: Table<SubmissionRow, string>;
  facilities!: Table<FacilityRow, string>;
  config!: Table<ConfigRow, string>;
  audit!: Table<AuditRow, number>;
  enrollment!: Table<EnrollmentRow, string>;

  constructor() {
    super('f2_pwa');
    this.version(1).stores({
      drafts: 'id, hcw_id, updated_at',
      submissions: 'client_submission_id, status, synced_at, hcw_id',
      facilities: 'id, region, province, name',
      config: 'key',
      audit: '++id, event, occurred_at',
    });
    this.version(2)
      .stores({
        submissions: 'client_submission_id, status, synced_at, hcw_id, next_retry_at',
      })
      .upgrade(async (tx) => {
        await tx
          .table<SubmissionRow, string>('submissions')
          .toCollection()
          .modify((row) => {
            if (row.retry_count == null) row.retry_count = 0;
            if (row.next_retry_at === undefined) row.next_retry_at = null;
            if (row.last_error === undefined) row.last_error = null;
          });
      });
    this.version(3).stores({
      facilities: null,
      enrollment: 'id',
    });
    this.version(4).stores({
      facilities: 'facility_id, facility_type, region, province',
    });
    // v5: device_token added to enrollment row (auth re-arch, spec 2026-04-26).
    // No index change; the upgrade clears any pre-v5 enrollment that lacks a
    // device_token so the PWA lands on the enrollment screen and the enumerator
    // re-enrols with a Worker-issued JWT.
    this.version(5)
      .stores({})
      .upgrade(async (tx) => {
        const rows = await tx.table<EnrollmentRow, string>('enrollment').toArray();
        for (const row of rows) {
          if (!row.device_token) {
            await tx.table<EnrollmentRow, string>('enrollment').delete(row.id);
          }
        }
      });
  }
}

export const db = new F2Database();
