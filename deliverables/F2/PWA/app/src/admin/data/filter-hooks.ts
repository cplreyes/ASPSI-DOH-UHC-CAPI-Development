/**
 * F2 Admin Portal — shared filter-bar data hooks for the Data dashboard tabs.
 *
 * Split from filter-controls.tsx (react-refresh wants component files to
 * export only components): option-fetching hooks + the select-option
 * builders live here; the visual controls stay in filter-controls.tsx.
 */
import { useEffect, useMemo, useState } from 'react';
import { adminFetch } from '../lib/api-client';

export interface FacilityOption {
  facility_id: string;
  facility_name: string;
}

export interface SelectOption {
  value: string;
  label: string;
}

/**
 * Facility dropdown options — fetched once per tab mount from
 * /dashboards/data/facility-options (dash_data). On failure the dropdown
 * degrades to "All facilities" (+ any deep-linked id); it never blocks the
 * tab's own list.
 */
export function useFacilityOptions(
  apiBaseUrl: string,
  token: string | null,
  fetchImpl?: typeof fetch,
): FacilityOption[] {
  const [options, setOptions] = useState<FacilityOption[]>([]);
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const r = await adminFetch<{ rows: FacilityOption[] }>(
        `${apiBaseUrl}/admin/api/dashboards/data/facility-options`,
        {},
        {
          ...(token ? { token } : {}),
          ...(fetchImpl ? { fetchImpl } : {}),
        },
      );
      if (cancelled || !r.ok) return;
      setOptions((r.data.rows ?? []).filter((f) => f.facility_id && f.facility_name));
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, token, fetchImpl]);
  return options;
}

/**
 * Audit event-type dropdown options — distinct values straight from f2_audit
 * via /dashboards/data/audit-event-types, so the list never drifts from the
 * events the system actually writes.
 */
export function useAuditEventTypes(
  apiBaseUrl: string,
  token: string | null,
  fetchImpl?: typeof fetch,
): string[] {
  const [types, setTypes] = useState<string[]>([]);
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const r = await adminFetch<{ rows: string[] }>(
        `${apiBaseUrl}/admin/api/dashboards/data/audit-event-types`,
        {},
        {
          ...(token ? { token } : {}),
          ...(fetchImpl ? { fetchImpl } : {}),
        },
      );
      if (cancelled || !r.ok) return;
      setTypes((r.data.rows ?? []).filter(Boolean));
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, token, fetchImpl]);
  return types;
}

/**
 * Options for a facility <select>: "All facilities" first, then the master
 * rows by name. A deep-linked / archived facility_id that isn't among the
 * options is appended as a raw-id entry so the select never hides an active
 * filter.
 */
export function useFacilitySelectOptions(
  options: FacilityOption[],
  currentId: string,
): SelectOption[] {
  return useMemo(() => {
    const opts: SelectOption[] = options.map((f) => ({
      value: f.facility_id,
      label: f.facility_name,
    }));
    if (currentId && !options.some((f) => f.facility_id === currentId)) {
      opts.push({ value: currentId, label: currentId });
    }
    return [{ value: '', label: 'All facilities' }, ...opts];
  }, [options, currentId]);
}

/** Same raw-value fallback for a plain string-valued select (event types). */
export function useStringSelectOptions(
  values: string[],
  currentValue: string,
  allLabel: string,
): SelectOption[] {
  return useMemo(() => {
    const opts: SelectOption[] = values.map((v) => ({ value: v, label: v }));
    if (currentValue && !values.includes(currentValue)) {
      opts.push({ value: currentValue, label: currentValue });
    }
    return [{ value: '', label: allLabel }, ...opts];
  }, [values, currentValue, allLabel]);
}
