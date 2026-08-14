-- CAPI Console identity provider — schema + role seed.        Carl, 2026-08-08
-- Plan: deliverables/CSWeb/capi-console-idp-option-c-plan.md §3.3–3.4
--
-- Idempotent: safe to re-run. Creates its own database so nothing here can
-- collide with CSWeb's tables or the csweb_f2 mirror.
--
-- ENGINE=InnoDB is stated on EVERY table on purpose. Parts of this estate are
-- MyISAM (the oauth_* tables), and a MyISAM table silently voids transaction
-- rollback — which is exactly the failure you never want in the table that
-- decides who may read respondent data.

CREATE DATABASE IF NOT EXISTS capi_auth
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE capi_auth;

-- ---------------------------------------------------------------------------
-- Identity
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS console_users (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(64)  NOT NULL,
  full_name     VARCHAR(128) NOT NULL DEFAULT '',
  email         VARCHAR(190) NOT NULL DEFAULT '',
  -- pw_algo is stored rather than sniffed from the hash prefix: the migration
  -- imports legacy $apr1$ (MD5-crypt) hashes and rehashes them to argon2id on
  -- the owner's next successful login (see lib.php verify_password).
  pw_hash       VARCHAR(255) NOT NULL,
  pw_algo       ENUM('argon2id','bcrypt','apr1') NOT NULL DEFAULT 'argon2id',
  must_change   TINYINT(1)   NOT NULL DEFAULT 1,
  totp_secret   VARBINARY(255) NULL,
  totp_enforced TINYINT(1)   NOT NULL DEFAULT 0,
  status        ENUM('active','disabled') NOT NULL DEFAULT 'active',
  failed_count  SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  locked_until  DATETIME NULL,
  last_login_at DATETIME NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by    VARCHAR(64)  NOT NULL DEFAULT '',
  UNIQUE KEY uq_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Roles. `version` is F2's trick, kept deliberately: bump it on any permission
-- change and every live session carrying the old number dies on its next
-- request. Without it, a demotion only takes effect at next login.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS console_roles (
  id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name         VARCHAR(48) NOT NULL,
  label        VARCHAR(96) NOT NULL,
  version      INT UNSIGNED NOT NULL DEFAULT 1,
  is_protected TINYINT(1)  NOT NULL DEFAULT 0,
  UNIQUE KEY uq_role (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Permissions are ROWS, not boolean columns. This is the single structural
-- decision that makes Phase 2 cheap: F2's eleven PERM_KEYS (dash_data,
-- dash_users, dict_capi_up, …) become additional rows beside the console's
-- own keys, with no ALTER on a live table and no query rewrite.
CREATE TABLE IF NOT EXISTS console_role_perms (
  role_id  INT UNSIGNED NOT NULL,
  perm_key VARCHAR(48)  NOT NULL,
  PRIMARY KEY (role_id, perm_key),
  CONSTRAINT fk_perm_role FOREIGN KEY (role_id)
    REFERENCES console_roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS console_user_roles (
  user_id INT UNSIGNED NOT NULL,
  role_id INT UNSIGNED NOT NULL,
  PRIMARY KEY (user_id, role_id),
  CONSTRAINT fk_ur_user FOREIGN KEY (user_id)
    REFERENCES console_users(id) ON DELETE CASCADE,
  CONSTRAINT fk_ur_role FOREIGN KEY (role_id)
    REFERENCES console_roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Sessions. Server-side and revocable — the capability the current
-- mod_session_cookie setup cannot provide at all (its logout is browser-side,
-- so a captured cookie stays valid for the full 8 h).
--
-- sid_hash stores SHA-256 of the cookie token, NEVER the token. A dump of this
-- table therefore yields nothing an attacker can replay.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS console_sessions (
  sid_hash     CHAR(64)     NOT NULL PRIMARY KEY,
  user_id      INT UNSIGNED NOT NULL,
  role_version INT UNSIGNED NOT NULL DEFAULT 0,
  issued_at    DATETIME     NOT NULL,
  last_seen_at DATETIME     NOT NULL,
  expires_at   DATETIME     NOT NULL,
  revoked_at   DATETIME     NULL,
  ip           VARCHAR(45)  NOT NULL DEFAULT '',
  user_agent   VARCHAR(255) NOT NULL DEFAULT '',
  KEY ix_sess_user (user_id),
  KEY ix_sess_exp  (expires_at),
  CONSTRAINT fk_sess_user FOREIGN KEY (user_id)
    REFERENCES console_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Audit. Covers authentication, permission denials, admin mutations AND reads
-- of respondent data — that last one is the current gap, and it is the one the
-- PH Data Privacy Act actually asks about.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS console_audit (
  id     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ts     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actor  VARCHAR(64)  NOT NULL DEFAULT '',
  verb   VARCHAR(32)  NOT NULL,
  target VARCHAR(255) NOT NULL DEFAULT '',
  detail JSON         NULL,
  ip     VARCHAR(45)  NOT NULL DEFAULT '',
  KEY ix_aud_ts    (ts),
  KEY ix_aud_actor (actor, ts),
  KEY ix_aud_verb  (verb, ts)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Seed: five roles (plan §3.4)
-- ---------------------------------------------------------------------------
INSERT INTO console_roles (name, label, is_protected) VALUES
  ('owner',            'Owner',            1),
  ('programme_admin',  'Programme Admin',  0),
  ('analyst',          'Analyst',          0),
  ('field_supervisor', 'Field Supervisor', 0),
  ('client_viewer',    'Client Viewer',    0)
ON DUPLICATE KEY UPDATE label = VALUES(label);

-- Permission grants. Rebuilt wholesale so re-running this file converges the
-- grants to exactly what the plan says, rather than accumulating stale rows.
DELETE p FROM console_role_perms p
  JOIN console_roles r ON r.id = p.role_id
 WHERE r.name IN ('owner','programme_admin','analyst','field_supervisor','client_viewer')
   AND p.perm_key LIKE '%.%';           -- console keys only; leaves F2 keys (Phase 2) alone

INSERT IGNORE INTO console_role_perms (role_id, perm_key)
SELECT r.id, k.perm_key FROM console_roles r JOIN (
  SELECT 'owner' role, 'monitoring.view'   perm_key UNION ALL
  SELECT 'owner','case.view'          UNION ALL
  SELECT 'owner','data.export'        UNION ALL
  SELECT 'owner','tabulations.view'   UNION ALL
  SELECT 'owner','admin.users'        UNION ALL
  SELECT 'owner','admin.system'       UNION ALL
  SELECT 'owner','audit.view'         UNION ALL

  SELECT 'programme_admin','monitoring.view'  UNION ALL
  SELECT 'programme_admin','case.view'        UNION ALL
  SELECT 'programme_admin','data.export'      UNION ALL
  SELECT 'programme_admin','tabulations.view' UNION ALL
  SELECT 'programme_admin','admin.users'      UNION ALL
  SELECT 'programme_admin','admin.system'     UNION ALL
  SELECT 'programme_admin','audit.view'       UNION ALL

  SELECT 'analyst','monitoring.view'  UNION ALL
  SELECT 'analyst','case.view'        UNION ALL
  SELECT 'analyst','data.export'      UNION ALL
  SELECT 'analyst','tabulations.view' UNION ALL

  -- Field Supervisor keeps case.view (Carl's 2026-07-30 decision — they hold
  -- equivalent access on the F2 portal already) but NOT data.export: reading
  -- one case for QC is not the same act as taking the whole microdata set.
  SELECT 'field_supervisor','monitoring.view'  UNION ALL
  SELECT 'field_supervisor','case.view'        UNION ALL
  SELECT 'field_supervisor','tabulations.view' UNION ALL

  -- Client Viewer exists so DOH can be given real access instead of
  -- screenshots, without respondent-level detail.
  SELECT 'client_viewer','monitoring.view'  UNION ALL
  SELECT 'client_viewer','tabulations.view'
) k ON k.role = r.name;

-- Bump every role version so any session minted before a re-run is invalidated.
UPDATE console_roles SET version = version + 1;
