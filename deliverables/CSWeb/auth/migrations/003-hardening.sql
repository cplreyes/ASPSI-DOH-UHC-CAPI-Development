-- CAPI Console — login throttle index + audit tamper-resistance.
-- E9-ADMIN-011 / E9-ADMIN-012.                                 Carl, 2026-08-09
--
-- RUN AS ROOT. Contains DDL and GRANT changes; `capi_auth` can do neither, and
-- the second half is specifically about taking a privilege away from it.
--
--   docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" \
--     --default-character-set=utf8mb4 < /opt/app/lamp/private/capi-auth/migrations/003-hardening.sql
--
-- Idempotent: safe to re-run.

USE capi_auth;

-- ---------------------------------------------------------------------------
-- E9-ADMIN-011 — index for the per-IP login throttle
--
-- auth_ip_fail_count() counts recent login.fail rows for one IP. Without this
-- index that is a scan of console_audit on every sign-in attempt, and
-- console_audit is the table that grows fastest after cutover.
-- ---------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS capi3_add_idx;
DELIMITER $$
CREATE PROCEDURE capi3_add_idx(IN tname VARCHAR(64), IN iname VARCHAR(64), IN cols TEXT)
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.STATISTICS
                  WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = tname AND INDEX_NAME = iname) THEN
    SET @sql = CONCAT('ALTER TABLE `', tname, '` ADD INDEX `', iname, '` (', cols, ')');
    PREPARE st FROM @sql; EXECUTE st; DEALLOCATE PREPARE st;
  END IF;
END$$
DELIMITER ;

CALL capi3_add_idx('console_audit', 'ix_aud_ip', '`ip`, `ts`');
DROP PROCEDURE IF EXISTS capi3_add_idx;

-- ---------------------------------------------------------------------------
-- E9-ADMIN-012 — make the audit trail append-only to the application
--
-- The application user held SELECT/INSERT/UPDATE/DELETE on capi_auth.*, which
-- included console_audit. An application that can delete its own audit trail
-- does not have an audit trail; it has a log that survives only until the
-- thing worth hiding happens.
--
-- MySQL has no "deny", so the schema-wide grant is replaced with per-table
-- grants: full DML on the tables the app genuinely mutates, and SELECT+INSERT
-- only on console_audit. Deletion and back-dating now require root.
--
-- If a future GC job needs to prune old audit rows (E9-ADMIN-043), give it its
-- OWN user with DELETE on this one table. Do not hand it back here.
-- ---------------------------------------------------------------------------
-- ORDER MATTERS: grant the replacements FIRST, then drop the wildcard. Doing
-- it the other way leaves a window — however small — in which the running
-- application has no privileges at all, and this runs against a live console.
-- A database-level REVOKE does not touch table-level grants (they live in
-- mysql.tables_priv), so the narrow grants below survive it.
--
-- Verified against the code before revoking: only INSERT and SELECT statements
-- reference console_audit anywhere in auth/ or admin/.

GRANT SELECT, INSERT, UPDATE, DELETE ON capi_auth.console_users      TO 'capi_auth'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON capi_auth.console_roles      TO 'capi_auth'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON capi_auth.console_role_perms TO 'capi_auth'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON capi_auth.console_user_roles TO 'capi_auth'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON capi_auth.console_sessions   TO 'capi_auth'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON capi_auth.console_idem       TO 'capi_auth'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON capi_auth.console_svc_tokens TO 'capi_auth'@'%';

-- The one that matters. No UPDATE, no DELETE.
GRANT SELECT, INSERT                  ON capi_auth.console_audit     TO 'capi_auth'@'%';

-- Now drop the wildcard that granted DELETE on everything, console_audit
-- included. IF EXISTS keeps a re-run free (MySQL 8.0.16+; this box is 8.4.11).
REVOKE IF EXISTS ALL PRIVILEGES ON capi_auth.* FROM 'capi_auth'@'%';

FLUSH PRIVILEGES;

-- Verification: console_audit must show only SELECT and INSERT.
SELECT TABLE_NAME, GROUP_CONCAT(PRIVILEGE_TYPE ORDER BY PRIVILEGE_TYPE) AS privs
  FROM information_schema.TABLE_PRIVILEGES
 WHERE GRANTEE = "'capi_auth'@'%'" AND TABLE_SCHEMA = 'capi_auth'
 GROUP BY TABLE_NAME ORDER BY TABLE_NAME;
