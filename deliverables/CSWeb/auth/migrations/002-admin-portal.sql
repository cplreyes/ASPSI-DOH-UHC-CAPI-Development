-- CAPI Console — Admin Portal schema delta (E9-ADMIN-005).     Carl, 2026-08-08
-- Design: deliverables/CSWeb/admin-portal/DESIGN.md §3
--
-- RUN AS ROOT. The application user `capi_auth` deliberately holds DML only
-- (SELECT/INSERT/UPDATE/DELETE) and no DDL, so it cannot run this file — that
-- is the point of the grant, not an oversight.
--
--   docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" \
--     --default-character-set=utf8mb4 < /opt/app/lamp/private/capi-auth/migrations/002-admin-portal.sql
--
-- Idempotent: safe to re-run. MySQL 8 has no `ADD COLUMN IF NOT EXISTS`
-- (that is MariaDB), so the guards below query information_schema first.
-- Re-running must be free, because this file will be applied to a database
-- that already holds the only copy of 18 live accounts.

USE capi_auth;

-- ---------------------------------------------------------------------------
-- Idempotency helpers. Dropped again at the end; nothing persists.
-- ---------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS capi_add_col;
DROP PROCEDURE IF EXISTS capi_add_idx;

DELIMITER $$

CREATE PROCEDURE capi_add_col(IN tname VARCHAR(64), IN cname VARCHAR(64), IN ddl TEXT)
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS
                  WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME   = tname
                    AND COLUMN_NAME  = cname) THEN
    SET @sql = CONCAT('ALTER TABLE `', tname, '` ADD COLUMN ', ddl);
    PREPARE st FROM @sql; EXECUTE st; DEALLOCATE PREPARE st;
  END IF;
END$$

CREATE PROCEDURE capi_add_idx(IN tname VARCHAR(64), IN iname VARCHAR(64), IN cols TEXT)
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.STATISTICS
                  WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME   = tname
                    AND INDEX_NAME   = iname) THEN
    SET @sql = CONCAT('ALTER TABLE `', tname, '` ADD INDEX `', iname, '` (', cols, ')');
    PREPARE st FROM @sql; EXECUTE st; DEALLOCATE PREPARE st;
  END IF;
END$$

DELIMITER ;

-- ---------------------------------------------------------------------------
-- console_users — optimistic concurrency and a change trail on the row itself
--
-- row_version exists because two admins on the same user record is a real
-- scenario at onboarding time, and "last write wins" silently discards the
-- other person's edit. The API requires the version the client read and
-- answers 409 when it has moved.
-- ---------------------------------------------------------------------------
CALL capi_add_col('console_users', 'row_version',
  'row_version INT UNSIGNED NOT NULL DEFAULT 1 AFTER status');
CALL capi_add_col('console_users', 'pw_changed_at',
  'pw_changed_at DATETIME NULL AFTER pw_algo');
CALL capi_add_col('console_users', 'updated_at',
  'updated_at DATETIME NULL AFTER created_by');
CALL capi_add_col('console_users', 'updated_by',
  "updated_by VARCHAR(64) NOT NULL DEFAULT '' AFTER updated_at");
CALL capi_add_col('console_users', 'disabled_at',
  'disabled_at DATETIME NULL AFTER updated_by');

-- pw_algo gains 'pbkdf2' NOW, in Phase 1, though nothing writes it until
-- Phase 2. F2 stores PBKDF2-SHA256 x100k; federating later would otherwise
-- mean an ALTER on live identity data in the middle of national rollout. The
-- guard keeps a re-run from rebuilding the table for nothing.
SET @cur_algo = (SELECT COLUMN_TYPE FROM information_schema.COLUMNS
                  WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'console_users' AND COLUMN_NAME = 'pw_algo');
SET @sql = IF(@cur_algo LIKE '%pbkdf2%', 'DO 0',
  "ALTER TABLE console_users
     MODIFY pw_algo ENUM('argon2id','bcrypt','apr1','pbkdf2')
     NOT NULL DEFAULT 'argon2id'");
PREPARE st FROM @sql; EXECUTE st; DEALLOCATE PREPARE st;

-- ---------------------------------------------------------------------------
-- console_audit — correlate a whole request, and search by who/what was touched
--
-- request_id is what turns "an error happened" into "these six rows are the
-- same failed request". It matters more than usual here: log_errors is Off on
-- this image, so console_audit IS the error log.
-- ---------------------------------------------------------------------------
CALL capi_add_col('console_audit', 'request_id',
  "request_id CHAR(32) NOT NULL DEFAULT '' AFTER id");
CALL capi_add_idx('console_audit', 'ix_aud_target', '`target`, `ts`');
CALL capi_add_idx('console_audit', 'ix_aud_req',    '`request_id`');

-- ---------------------------------------------------------------------------
-- console_idem — replay protection for non-idempotent mutations
--
-- The failure this prevents is specific and has bitten every admin tool ever
-- built: an admin double-clicks "reset password", two temp passwords are
-- minted, the second silently invalidates the one already copied into a chat
-- message, and the user is handed a credential that does not work. Storing the
-- first response and replaying it makes the second click a no-op.
--
-- body_sha256 catches the other case: the same Idempotency-Key sent with a
-- DIFFERENT body is a client bug, and answering 422 is safer than guessing.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS console_idem (
  idem_key    CHAR(64)     NOT NULL PRIMARY KEY,   -- sha256(actor|endpoint|client key)
  actor       VARCHAR(64)  NOT NULL DEFAULT '',
  endpoint    VARCHAR(160) NOT NULL DEFAULT '',
  status      SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  body_sha256 CHAR(64)     NOT NULL DEFAULT '',
  response    MEDIUMTEXT   NULL,
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_idem_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- console_svc_tokens — created EMPTY, for Phase 2 (F2 federation)
--
-- Same reasoning as the pw_algo ENUM: the shape is cheap now and expensive
-- mid-rollout. Nothing reads this table in Phase 1, and ACL_PREFIX denies
-- /docs/idp/svc/ outright, so an empty table is inert.
--
-- token_hash is SHA-256 of the bearer token. As with session cookies, a dump
-- of this table must not yield anything replayable.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS console_svc_tokens (
  id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name         VARCHAR(64)  NOT NULL,
  token_hash   CHAR(64)     NOT NULL,
  scopes       VARCHAR(255) NOT NULL DEFAULT '',
  status       ENUM('active','disabled') NOT NULL DEFAULT 'active',
  last_used_at DATETIME     NULL,
  expires_at   DATETIME     NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by   VARCHAR(64)  NOT NULL DEFAULT '',
  UNIQUE KEY uq_svc_name (name),
  UNIQUE KEY uq_svc_hash (token_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Backfill. The 18 imported accounts predate these columns; leaving
-- pw_changed_at NULL would read as "never set" rather than "set at import",
-- and the retention/expiry work in E9-ADMIN-043 keys off it.
-- ---------------------------------------------------------------------------
UPDATE console_users
   SET pw_changed_at = COALESCE(pw_changed_at, created_at),
       row_version   = GREATEST(row_version, 1)
 WHERE pw_changed_at IS NULL;

DROP PROCEDURE IF EXISTS capi_add_col;
DROP PROCEDURE IF EXISTS capi_add_idx;

-- Verification (expect: 5 new console_users columns, 1 new console_audit
-- column, 2 new tables).
SELECT COLUMN_NAME FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = 'capi_auth' AND TABLE_NAME = 'console_users'
   AND COLUMN_NAME IN ('row_version','pw_changed_at','updated_at','updated_by','disabled_at')
 ORDER BY COLUMN_NAME;
