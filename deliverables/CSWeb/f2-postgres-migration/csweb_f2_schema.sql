-- =============================================================================
-- csweb_f2 — F2 Healthcare-Worker (PWA) READ-MIRROR schema  (MySQL 8, on the box)
-- =============================================================================
-- Engine decision (2026-07-07): F2's store becomes a REAL database on the CSWeb
-- box, MySQL 8, living in the SAME `lamp-mysql8` container as csweb_f1/f3/f4_breakout
-- — so the unified Sync Dashboard reads F2 through its EXISTING q() docker-exec path,
-- exactly like the other three instruments. No new container, no new engine.
--
-- Scope decision: READ-MIRROR. This DB is a queryable copy of F2's Google-Sheet
-- store (kept fresh by sync_f2_to_mysql.py). Sheets + Apps Script remain F2's WRITE
-- authority; the Elestio end-state is untouched. Making the app write here directly
-- (retiring the Sheet) is a separate, Carl-gated step — NOT built by this schema.
-- Because we are NOT building the write path, the write-path machinery the Postgres
-- design carried (f2_config gate, f2_hcws enrollment registry, dead-letter, batch
-- semantics) is deliberately absent — a mirror needs only the response rows + a
-- facility→area lookup for the dashboard's by-NAME geo rollup.
--
-- Idempotent: safe to re-run. Apply on the box:
--   docker compose exec -T database mysql -uroot -p"$MYSQL_ROOT_PASSWORD" \
--     < /opt/f2-postgres-migration/csweb_f2_schema.sql
-- (run from /opt/app so `database` resolves; the poller/generator connect the same way).
--
-- NOTE ON CONSTRAINTS: this mirror deliberately uses lenient columns (soft defaults,
-- NO CHECK constraints on client-influenced fields like status/source_path). A mirror's
-- job is to never SILENTLY drop a row the Sheet accepted; the poller isolates and
-- surfaces genuinely bad rows (malformed JSON) via per-row retry + non-zero exit,
-- rather than a constraint rejecting them mid-batch.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS csweb_f2
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- f2_responses — one row per F2 submission, mirrored from the F2_Responses sheet.
-- Column set = the 18 canonical sheet columns (Schema.js), + a synced_at freshness
-- stamp. `client_submission_id` is the idempotency key (UNIQUE) the poller upserts on.
-- -----------------------------------------------------------------------------
-- Column sizing is deliberately GENEROUS (real Sheet data proved messier than spec on
-- first backfill, 2026-07-08: a 301-char hcw_id + a third status value 'synced'). Free-text
-- identity fields are TEXT (unindexed, so free); bounded fields get headroom. A mirror must
-- accept whatever the Sheet accepted — never reject on width.
CREATE TABLE IF NOT EXISTS csweb_f2.f2_responses (
  id                   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  submission_id        VARCHAR(128) NULL,                          -- AS server-assigned id
  client_submission_id VARCHAR(191) NOT NULL,                      -- device-generated idempotency key (UNIQUE-indexed → bounded)
  submitted_at_server  DATETIME     NULL,                          -- UTC; drives trend + freshness
  submitted_at_client  DATETIME     NULL,                          -- UTC (device clock)
  source               VARCHAR(32)  NOT NULL DEFAULT 'PWA',
  spec_version         VARCHAR(64)  NOT NULL DEFAULT '',
  app_version          VARCHAR(64)  NULL,
  hcw_id               TEXT         NULL,                          -- free text in practice (301 chars seen)
  facility_id          VARCHAR(64)  NULL,                          -- geo lookup key → f2_facility_master
  qn                   VARCHAR(16)  NULL,                          -- 12-digit Questionnaire Number (facility-9 +
                                                                   -- HCW-seq-3, F1/F3/F4-aligned; added 2026-07-08;
                                                                   -- NULL/'' for pre-qn rows)
  device_fingerprint   TEXT         NULL,
  sync_attempt_count   INT          NOT NULL DEFAULT 1,
  status               VARCHAR(32)  NOT NULL DEFAULT 'stored',     -- 'stored' | 'refusal' | 'synced' (legacy) — treat non-refusal as Submitted
  values_json          JSON         NOT NULL,                      -- the answer dict (validated JSON)
  submission_lat       DOUBLE       NULL,                          -- usually NULL (self-administered)
  submission_lng       DOUBLE       NULL,
  source_path          VARCHAR(32)  NOT NULL DEFAULT 'self_admin', -- 'self_admin' | 'paper_encoded'
  encoded_by           TEXT         NULL,
  encoded_at           DATETIME     NULL,
  synced_at            TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP,             -- poller last-touch (freshness);
                          -- the poller ALSO sets it explicitly in its ODKU so re-seen unchanged
                          -- rows still bump it (a no-op ODKU would not fire ON UPDATE) → a
                          -- MAX(synced_at) heartbeat reliably tracks poller liveness.
  PRIMARY KEY (id),
  UNIQUE KEY uq_client_submission_id (client_submission_id),
  KEY ix_submitted_at_server (submitted_at_server),               -- watermark + trend
  KEY ix_status (status),
  KEY ix_facility_id (facility_id),
  KEY ix_qn (qn)                                                  -- coverage joins on LEFT(qn,9)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- f2_facility_master — facility_id → area NAMES for the dashboard's by-NAME rollup.
-- The unified dashboard joins every instrument's area by NAME (not code), so region /
-- province here MUST be seeded byte-identical to CSWeb's F1/F3/F4 region_name /
-- province_name (same PSGC/facility CSVs CSPro reads). Until it is seeded, the
-- generator's LEFT JOIN yields NULL → '(unknown)', which degrades gracefully.
-- Seeding this from the CAPI facility frame is the DEFERRED geo-harmonization step
-- (there is no F2 sample frame yet — same reason F2 coverage-vs-target is deferred).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS csweb_f2.f2_facility_master (
  facility_id    VARCHAR(32)  NOT NULL,
  facility_name  VARCHAR(255) NULL,
  region         VARCHAR(128) NULL,   -- MUST match CSWeb region_name exactly when seeded
  province       VARCHAR(128) NULL,   -- MUST match CSWeb province_name exactly when seeded
  city_mun       VARCHAR(128) NULL,
  PRIMARY KEY (facility_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- AS-BUILT (P4 serving cutover, deliverables/F2/PWA/server/deploy/p4-box-steps.sh
-- step 0): two guarded ALTERs bring this table to the FacilityMasterList sheet's
-- 7-column shape, which f2-api's readFacilities SELECTs:
--   ALTER TABLE f2_facility_master ADD COLUMN facility_type VARCHAR(64)  NULL AFTER facility_name;
--   ALTER TABLE f2_facility_master ADD COLUMN barangay      VARCHAR(128) NULL AFTER city_mun;
-- P4 also ports the sheet's rows here (facility_id repaired to 9 digits where
-- Sheets' numeric coercion stripped a leading zero).

-- =============================================================================
-- The generator reads csweb_f2 via the SAME q() docker-exec path as the breakouts;
-- the F2 area/disposition derivation lives INLINE in csweb-dashboard-gen.py's F2
-- query (parallel to F1/F3/F4), NOT in a DB view — one source of truth for the
-- derivation, so there is no second/contradictory view definition to drift from.
-- =============================================================================
