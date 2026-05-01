var F2_RESPONSES_COLUMNS = [
  'submission_id',
  'client_submission_id',
  'submitted_at_server',
  'submitted_at_client',
  'source',
  'spec_version',
  'app_version',
  'hcw_id',
  'facility_id',
  'device_fingerprint',
  'sync_attempt_count',
  'status',
  'values_json',
  // Admin Portal extensions (Tasks 2.6, 2.7, 4.2). Order MUST match the
  // physical column order produced by Migrations.migrateExtendF2ResponsesColumns.
  'submission_lat',
  'submission_lng',
  'source_path',
  'encoded_by',
  'encoded_at',
];

var F2_AUDIT_COLUMNS = [
  'audit_id',
  'occurred_at_server',
  'occurred_at_client',
  'event_type',
  'hcw_id',
  'facility_id',
  'app_version',
  'payload_json',
];

var F2_CONFIG_COLUMNS = ['key', 'value'];

var F2_CONFIG_DEFAULTS = [
  ['current_spec_version', '2026-04-17-m1'],
  ['min_accepted_spec_version', '2026-04-17-m1'],
  ['kill_switch', 'false'],
  ['broadcast_message', ''],
  ['spec_hash', ''],
];

var FACILITY_MASTER_LIST_COLUMNS = [
  'facility_id',
  'facility_name',
  'facility_type',
  'region',
  'province',
  'city_mun',
  'barangay',
];

var F2_DLQ_COLUMNS = [
  'dlq_id',
  'received_at_server',
  'client_submission_id',
  'reason',
  'payload_json',
];

var TABS = {
  RESPONSES: 'F2_Responses',
  AUDIT: 'F2_Audit',
  CONFIG: 'F2_Config',
  FACILITIES: 'FacilityMasterList',
  DLQ: 'F2_DLQ',
};

if (typeof module !== 'undefined') {
  module.exports = {
    F2_RESPONSES_COLUMNS: F2_RESPONSES_COLUMNS,
    F2_AUDIT_COLUMNS: F2_AUDIT_COLUMNS,
    F2_CONFIG_COLUMNS: F2_CONFIG_COLUMNS,
    F2_CONFIG_DEFAULTS: F2_CONFIG_DEFAULTS,
    FACILITY_MASTER_LIST_COLUMNS: FACILITY_MASTER_LIST_COLUMNS,
    F2_DLQ_COLUMNS: F2_DLQ_COLUMNS,
    TABS: TABS,
  };
}
