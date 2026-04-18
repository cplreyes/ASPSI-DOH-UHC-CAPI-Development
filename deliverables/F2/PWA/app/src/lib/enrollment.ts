import { db, type EnrollmentRow } from './db';

export interface SetEnrollmentInput {
  hcw_id: string;
  facility_id: string;
}

export async function getEnrollment(): Promise<EnrollmentRow | null> {
  const row = await db.enrollment.get('singleton');
  return row ?? null;
}

export async function setEnrollment(input: SetEnrollmentInput): Promise<EnrollmentRow> {
  const trimmedHcw = input.hcw_id.trim();
  if (trimmedHcw.length === 0) {
    throw new Error('hcw_id is required');
  }
  const facility = await db.facilities.get(input.facility_id);
  if (!facility) {
    throw new Error(`Unknown facility ${input.facility_id}`);
  }
  const row: EnrollmentRow = {
    id: 'singleton',
    hcw_id: trimmedHcw,
    facility_id: facility.facility_id,
    facility_type: facility.facility_type,
    enrolled_at: Date.now(),
  };
  await db.enrollment.put(row);
  return row;
}

export async function clearEnrollment(): Promise<void> {
  await db.enrollment.delete('singleton');
}
