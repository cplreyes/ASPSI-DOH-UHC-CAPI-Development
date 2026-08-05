-- =============================================================================
-- f2-api tables — additions to csweb_f2 for the serving migration (Plan P2/P4).
-- csweb_f2.f2_responses + f2_facility_master already exist (mirror schema).
-- Idempotent. Apply from /opt/app:
--   docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" csweb_f2 \
--     < /opt/f2-api/ddl/f2_api_tables.sql
-- =============================================================================

-- HCW enrollment registry (ports the F2_HCWs sheet at P4; written by f2-api P1b).
CREATE TABLE IF NOT EXISTS f2_hcws (
  hcw_id               VARCHAR(64)  NOT NULL,
  facility_id          VARCHAR(64)  NULL,
  facility_name        VARCHAR(255) NULL,
  enrollment_token_jti VARCHAR(64)  NULL,
  token_issued_at      DATETIME     NULL,
  token_revoked_at     DATETIME     NULL,
  status               VARCHAR(32)  NOT NULL DEFAULT 'pending',  -- pending|enrolled|submitted|refusal|revoked
  created_at           DATETIME     NULL,
  qn                   VARCHAR(16)  NULL,
  -- Numbered short-link claim (design F2-Model-C-Numbered-Links-2026-07-16):
  -- a per-HCW readable slug + a keyed hash of its secret; claimed_at stamps the
  -- first successful /claim. Only the HMAC is stored — the plaintext secret is
  -- shown to the admin once at generation, never persisted.
  enroll_slug          VARCHAR(96)  NULL,
  enroll_secret_hmac   VARCHAR(64)  NULL,   -- HMAC-SHA256(secret, JWT signing key), hex
  claimed_at           DATETIME     NULL,
  PRIMARY KEY (hcw_id),
  KEY ix_facility (facility_id),
  -- P1b: qn is UNIQUE (NULLs exempt) — DB-level backstop for the qn-assignment
  -- transaction ("a sequence is never reused"). Blank qn is stored as NULL.
  -- If this table pre-exists with the old plain index, apply:
  --   ALTER TABLE f2_hcws DROP INDEX ix_qn, ADD UNIQUE KEY uq_qn (qn);
  UNIQUE KEY uq_qn (qn),
  UNIQUE KEY uq_enroll_slug (enroll_slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Idempotent add for DBs where f2_hcws pre-exists (prod): MySQL 8 has no
-- ADD COLUMN IF NOT EXISTS, so guard each add on information_schema. Re-applying
-- the whole file is a no-op once the columns/index exist.
SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='f2_hcws' AND COLUMN_NAME='enroll_slug');
SET @s := IF(@c=0, 'ALTER TABLE f2_hcws ADD COLUMN enroll_slug VARCHAR(96) NULL', 'DO 0');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='f2_hcws' AND COLUMN_NAME='enroll_secret_hmac');
SET @s := IF(@c=0, 'ALTER TABLE f2_hcws ADD COLUMN enroll_secret_hmac VARCHAR(64) NULL', 'DO 0');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;

SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='f2_hcws' AND COLUMN_NAME='claimed_at');
SET @s := IF(@c=0, 'ALTER TABLE f2_hcws ADD COLUMN claimed_at DATETIME NULL', 'DO 0');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;

SET @c := (SELECT COUNT(*) FROM information_schema.STATISTICS
           WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='f2_hcws' AND INDEX_NAME='uq_enroll_slug');
SET @s := IF(@c=0, 'ALTER TABLE f2_hcws ADD UNIQUE KEY uq_enroll_slug (enroll_slug)', 'DO 0');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;

-- Backfill (2026-07-17 "In progress" fix): handleSubmit now forward-only tags
-- the HCW row 'submitted' when its non-refusal response lands (mirror of the
-- #825 refusal tag). Rows submitted BEFORE the fix stayed 'enrolled' and kept
-- counting in the Facilities/Coverage "In progress" columns AND could never
-- trip /claim's already-completed gate. Same forward-only guard as the code
-- path; idempotent — converges to a no-op once every tagged row is closed.
UPDATE f2_hcws h
  JOIN (SELECT DISTINCT hcw_id FROM f2_responses
         WHERE status <> 'refusal' AND hcw_id IS NOT NULL AND hcw_id <> '') r
    ON r.hcw_id = h.hcw_id
   SET h.status = 'submitted'
 WHERE h.status IN ('pending','enrolled') OR h.status = '' OR h.status IS NULL;

-- Facility slug links (design F2-Facility-Slug-Links-2026-07-16): one clean,
-- readable public link per facility — `/f/<slug>` resolves to a facility and
-- self-registers the HCW. Bare slug, no secret; `active` is the soft per-link
-- kill (turn a facility's link off without deleting the row).
CREATE TABLE IF NOT EXISTS f2_facility_slugs (
  slug          VARCHAR(32)  NOT NULL,   -- lowercase ^[a-z0-9][a-z0-9-]{1,30}$
  facility_id   CHAR(9)      NOT NULL,   -- 9-digit PSGC facility code
  facility_name VARCHAR(160) NOT NULL,   -- shown on the StartScreen + written to the case
  active        TINYINT(1)   NOT NULL DEFAULT 1,
  created_at    DATETIME     NULL,
  created_by    VARCHAR(32)  NOT NULL DEFAULT '',
  PRIMARY KEY (slug),
  KEY ix_slug_facility (facility_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Facility master management (spec F2-Facility-Master-Mgmt-2026-07-16): archive
-- flag — soft-hide from pickers/lists, never delete (QNs embed facility_id and
-- cases reference it). Guarded ALTER, idempotent on re-apply.
SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='f2_facility_master' AND COLUMN_NAME='archived');
SET @s := IF(@c=0, 'ALTER TABLE f2_facility_master ADD COLUMN archived TINYINT(1) NOT NULL DEFAULT 0', 'DO 0');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;

-- Coverage report (spec F2-Coverage-Report-2026-07-17): per-facility HCW target
-- quota. NULL = no target yet (coverage % renders "—"); managed via the Edit
-- dialog and the optional 8th CSV import column. Guarded ALTER, idempotent.
SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='f2_facility_master' AND COLUMN_NAME='target_hcws');
SET @s := IF(@c=0, 'ALTER TABLE f2_facility_master ADD COLUMN target_hcws INT UNSIGNED NULL', 'DO 0');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;

-- GPS capture instrumentation (Reports-tab audit P1-4, 2026-07-17): why a
-- submission has/lacks coordinates — granted | denied | timeout | unavailable
-- | unsupported | not_requested; '' for rows ingested before this column.
-- Guarded ALTER, idempotent.
SET @c := (SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='f2_responses' AND COLUMN_NAME='gps_status');
SET @s := IF(@c=0, 'ALTER TABLE f2_responses ADD COLUMN gps_status VARCHAR(16) NOT NULL DEFAULT ''''', 'DO 0');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;

-- Config key/value (ports the F2_Config sheet at P4; seeded with AS defaults).
CREATE TABLE IF NOT EXISTS f2_config (
  k VARCHAR(64)  NOT NULL,
  v VARCHAR(512) NOT NULL DEFAULT '',
  PRIMARY KEY (k)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT IGNORE INTO f2_config (k, v) VALUES
  ('current_spec_version', '2026-07-02-r6'),
  ('min_accepted_spec_version', '2026-04-17-m1'),
  ('kill_switch', 'false'),
  ('broadcast_message', ''),
  ('spec_hash', '');

-- Dead-letter queue (parity with the AS F2_DLQ sheet — bad `values` payloads).
CREATE TABLE IF NOT EXISTS f2_dlq (
  dlq_id               VARCHAR(64) NOT NULL,
  received_at_server   DATETIME    NULL,
  client_submission_id VARCHAR(191) NULL,
  reason               VARCHAR(255) NULL,
  payload_json         JSON        NULL,
  PRIMARY KEY (dlq_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Token revocation (replaces CF KV `revoked:<jti>`).
CREATE TABLE IF NOT EXISTS auth_revoked (
  jti        VARCHAR(64) NOT NULL,
  revoked_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reason     VARCHAR(255) NULL,
  PRIMARY KEY (jti)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Token audit (replaces CF KV `token:<jti>`; written at reissue — P1b).
CREATE TABLE IF NOT EXISTS auth_token_audit (
  jti          VARCHAR(64)  NOT NULL,
  tablet_id    VARCHAR(64)  NULL,
  tablet_label VARCHAR(255) NULL,
  facility_id  VARCHAR(64)  NULL,
  issued_at    DATETIME     NULL,
  expires_at   DATETIME     NULL,
  PRIMARY KEY (jti)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- P1b — Admin Portal tables (port the F2_Users/F2_Roles/F2_Audit/F2_FileMeta/
-- F2_DataSettings sheets; row data migrates at P4).
-- =============================================================================

-- Admin users (F2_Users sheet). password_hash format is the Worker's PBKDF2
-- `<saltB64url>:<iters>:<hashB64url>` — existing hashes migrate verbatim.
CREATE TABLE IF NOT EXISTS f2_users (
  username             VARCHAR(32)  NOT NULL,
  first_name           VARCHAR(64)  NOT NULL DEFAULT '',
  last_name            VARCHAR(64)  NOT NULL DEFAULT '',
  role_name            VARCHAR(64)  NOT NULL,
  password_hash        VARCHAR(191) NOT NULL,
  password_must_change TINYINT(1)   NOT NULL DEFAULT 1,
  email                VARCHAR(191) NOT NULL DEFAULT '',
  phone                VARCHAR(64)  NOT NULL DEFAULT '',
  created_at           DATETIME     NULL,
  created_by           VARCHAR(32)  NOT NULL DEFAULT '',
  last_login_at        DATETIME     NULL,
  PRIMARY KEY (username),
  KEY ix_role (role_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- RBAC roles (F2_Roles sheet). `version` bumps on every perm change so JWTs
-- minted under the prior role_version fail rbac and force a re-login.
CREATE TABLE IF NOT EXISTS f2_roles (
  name                     VARCHAR(64) NOT NULL,
  is_builtin               TINYINT(1)  NOT NULL DEFAULT 0,
  version                  INT         NOT NULL DEFAULT 1,
  dash_data                TINYINT(1)  NOT NULL DEFAULT 0,
  dash_report              TINYINT(1)  NOT NULL DEFAULT 0,
  dash_apps                TINYINT(1)  NOT NULL DEFAULT 0,
  dash_users               TINYINT(1)  NOT NULL DEFAULT 0,
  dash_roles               TINYINT(1)  NOT NULL DEFAULT 0,
  dict_self_admin_up       TINYINT(1)  NOT NULL DEFAULT 0,
  dict_self_admin_down     TINYINT(1)  NOT NULL DEFAULT 0,
  dict_paper_encoded_up    TINYINT(1)  NOT NULL DEFAULT 0,
  dict_paper_encoded_down  TINYINT(1)  NOT NULL DEFAULT 0,
  dict_capi_up             TINYINT(1)  NOT NULL DEFAULT 0,
  dict_capi_down           TINYINT(1)  NOT NULL DEFAULT 0,
  created_at               DATETIME    NULL,
  created_by               VARCHAR(32) NOT NULL DEFAULT '',
  PRIMARY KEY (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- Bootstrap Administrator role (all perms). P4 migration upserts sheet truth
-- over this seed (INSERT IGNORE keeps whichever exists first).
INSERT IGNORE INTO f2_roles (name, is_builtin, version,
  dash_data, dash_report, dash_apps, dash_users, dash_roles,
  dict_self_admin_up, dict_self_admin_down, dict_paper_encoded_up,
  dict_paper_encoded_down, dict_capi_up, dict_capi_down, created_at, created_by)
VALUES ('Administrator', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, UTC_TIMESTAMP(), 'ddl');

-- Audit log (F2_Audit sheet: PWA columns + the 7 admin-context extensions).
-- Admin rows carry NULL audit_id (AS writeAuditRow parity) → surrogate PK.
CREATE TABLE IF NOT EXISTS f2_audit (
  id                 BIGINT       NOT NULL AUTO_INCREMENT,
  audit_id           VARCHAR(64)  NULL,
  occurred_at_server DATETIME     NULL,
  occurred_at_client VARCHAR(64)  NULL,
  event_type         VARCHAR(64)  NOT NULL,
  hcw_id             VARCHAR(64)  NULL,
  facility_id        VARCHAR(64)  NULL,
  app_version        VARCHAR(64)  NULL,
  payload_json       TEXT         NULL,
  actor_username     VARCHAR(32)  NULL,
  actor_jti          VARCHAR(64)  NULL,
  actor_role         VARCHAR(64)  NULL,
  event_resource     VARCHAR(255) NULL,
  event_payload_json TEXT         NULL,
  client_ip_hash     VARCHAR(64)  NULL,
  request_id         VARCHAR(64)  NULL,
  PRIMARY KEY (id),
  KEY ix_occurred (occurred_at_server),
  KEY ix_event_type (event_type),
  KEY ix_actor (actor_username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Admin file metadata (F2_FileMeta sheet). Bytes live on disk under
-- F2_FILES_DIR (default /opt/app/f2-files) keyed by file_id — R2 replacement.
CREATE TABLE IF NOT EXISTS f2_files (
  file_id      VARCHAR(64)  NOT NULL,
  filename     VARCHAR(255) NOT NULL,
  content_type VARCHAR(128) NOT NULL DEFAULT 'application/octet-stream',
  size_bytes   BIGINT       NOT NULL DEFAULT 0,
  uploaded_by  VARCHAR(32)  NOT NULL DEFAULT '',
  uploaded_at  DATETIME     NULL,
  description  VARCHAR(512) NOT NULL DEFAULT '',
  deleted_at   DATETIME     NULL,   -- soft delete; list hides stamped rows
  folder_path  VARCHAR(191) NOT NULL DEFAULT '/',
  is_folder    TINYINT(1)   NOT NULL DEFAULT 0,
  PRIMARY KEY (file_id),
  KEY ix_folder (folder_path)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Break-out CSV schedules (F2_DataSettings sheet). NOTE (P1b): CRUD + run-now
-- are served; the cron that consumes due rows is NOT ported yet.
CREATE TABLE IF NOT EXISTS f2_settings (
  setting_id           VARCHAR(64)  NOT NULL,
  instrument           VARCHAR(32)  NOT NULL DEFAULT 'F2',
  included_columns     TEXT         NULL,      -- JSON array string
  interval_minutes     INT          NOT NULL DEFAULT 60,
  next_run_at          DATETIME     NULL,
  output_path_template VARCHAR(255) NOT NULL DEFAULT '',
  last_run_at          DATETIME     NULL,
  last_run_status      VARCHAR(32)  NOT NULL DEFAULT '',
  last_run_error       VARCHAR(512) NOT NULL DEFAULT '',
  enabled              TINYINT(1)   NOT NULL DEFAULT 1,
  created_by           VARCHAR(32)  NOT NULL DEFAULT '',
  created_at           DATETIME     NULL,
  PRIMARY KEY (setting_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Generic auth KV (replaces CF KV for admin sessions): revoked_jti:<jti>,
-- revoked_user:<username>, throttle:login:*, as_quota:<date>. Rows past
-- expires_at are treated as absent; a periodic DELETE sweep is optional.
CREATE TABLE IF NOT EXISTS auth_kv (
  k          VARCHAR(191) NOT NULL,
  v          VARCHAR(512) NOT NULL DEFAULT '',
  expires_at DATETIME     NULL,
  PRIMARY KEY (k),
  KEY ix_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Least-privilege API user (P2, Carl runs with a generated password — value never in repo):
--   CREATE USER IF NOT EXISTS 'f2api'@'%' IDENTIFIED BY '<GENERATED>';
--   GRANT SELECT, INSERT, UPDATE, DELETE ON csweb_f2.* TO 'f2api'@'%';
--   FLUSH PRIVILEGES;
-- (P1b adds DELETE — admin users/roles/settings/DLQ deletes and auth_kv expiry.)
