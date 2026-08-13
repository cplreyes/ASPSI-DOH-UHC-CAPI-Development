-- ============================================================================
-- PRETEST DATABASE CLEANUP  —  2026-07-14
-- ============================================================================
-- STATUS: Sections 1, 2, 3, 6 EXECUTED 2026-07-14 and verified.
--         Section 4 (identities) NOT RUN — deliberately held pending ASPSI's
--         final enumerator/supervisor list.
--
-- Host   : root@207.148.65.115  (container: lamp-mysql8)
-- Scope  : csweb_uhc_y2 (CSWeb: F1/F3/F4 + Supervisor Hub)
--          csweb_f2     (HCW survey store, post-July-9 migration)
--          csweb_f{1,3,4}_breakout  (the reporting mirrors — Section 6)
--
-- ---------------------------------------------------------------------------
-- ARCHIVED DATA — everything purged below still exists in these dumps
-- ---------------------------------------------------------------------------
-- The UAT data is GONE from the live databases but is NOT lost. Full pre-cleanup
-- dumps sit on the box (2026-07-14, taken immediately before each purge):
--
--   /root/csweb_uhc_y2_pre-pretest-cleanup_20260714.sql     161K
--       -> the 15 CSWeb test cases (F1 2 · F3 12 · Hub 1), F3's 6 verification
--          photos + 1 note, sync history (9 + 16), and the 618 access / 261
--          refresh device tokens. Table-scoped dump (not the whole DB — it
--          deliberately excludes the 2.36M-row PSGC table).
--
--   /root/csweb_f2_pre-pretest-cleanup_20260714.sql         210K
--       -> the full csweb_f2 database as it stood: 41 HCW test responses,
--          16 enrollments, 262 audit rows, 13 token-audit rows — including the
--          mis-encoded response from #831 (DEMO-FAC-RHU-QC-1, 2026-07-03 10:44).
--
--   /root/csweb_breakouts_pre-pretest-cleanup_20260714.sql  6.3M
--       -> full dumps of csweb_f1_breakout + csweb_f3_breakout +
--          csweb_f4_breakout, i.e. the expanded/sectioned mirrors of the same
--          14 test cases, plus each DB's cspro_meta dictionary schema.
--
-- Restore path:  docker exec -i lamp-mysql8 mysql -uroot -p"$RPW" [db] < <dump>
-- Note the oauth_* tables in the first dump are MyISAM — see trap #1; their
-- deletion was NOT transactional, so this dump is the ONLY way back for them.
-- These dumps are the audit trail for "what did the UAT rounds actually collect."
--
-- ---------------------------------------------------------------------------
-- !! TWO TRAPS — read before reusing this script !!
-- ---------------------------------------------------------------------------
-- 1. THE oauth_* TABLES ARE MyISAM, NOT InnoDB.
--    MySQL's GTID consistency REFUSES to mix non-transactional tables into a
--    transaction with InnoDB tables:
--      ERROR 1785 (HY000): Statement violates GTID consistency: Updates to
--      non-transactional tables can only be done in either autocommitted
--      statements or single-statement transactions...
--    So the oauth_* deletes MUST run OUTSIDE the transaction (Section 2b).
--    Consequence: THEY CANNOT BE ROLLED BACK. The dump is the only way back.
--    Non-InnoDB tables in csweb_uhc_y2: oauth_access_tokens, oauth_refresh_tokens,
--    oauth_authorization_codes, oauth_clients, oauth_jwt, oauth_scopes, oauth_users.
--
-- 2. DO NOT PASTE THIS INLINE OVER SSH (`mysql -e "<long sql>"`).
--    A long multi-line -e string gets mangled in transit and can FAIL SILENTLY
--    — returning no output while applying nothing. Copy the file to the box and
--    run `mysql ... < file.sql`. Always verify counts afterward; never trust
--    empty output as success.
--
-- ---------------------------------------------------------------------------
-- !! DO NOT TOUCH — deleting any of these breaks the pretest !!
-- ---------------------------------------------------------------------------
--   cspro_area_names ............ 2,360,637 rows (exact). The PSGC lookup.
--                                 EVERY case key on EVERY tablet is geo-validated
--                                 against this. Drop it and no enumerator can open
--                                 a case at any site, with no obvious error.
--   cspro_dictionaries (7) · cspro_dictionaries_schema · cspro_apps (6)
--   cspro_roles (5) · cspro_permissions · cspro_role_permissions
--   cspro_role_dictionary_permissions (12)  <- sync permissions. Dropping this
--                                 silently 403s every tablet sync.
--   cspro_config · oauth_clients · oauth_scopes · oauth_jwt · oauth_users
--   f2_facility_master (5) · f2_config (5) · f2_roles (4) · f2_settings
--   auth_kv (login throttles + P4 marker) · f2_files (3, admin file manager)
--
-- NOTE ON COUNTS: figures below are EXACT COUNT(*) values. Earlier drafts of
-- this script quoted information_schema.table_rows, which is an ESTIMATE for
-- InnoDB and reads LOW (it said PSGC=2,341,560 / roles=4 / syncperms=10).
-- Trust COUNT(*), not table_rows.
-- ============================================================================


-- ============================================================================
-- SECTION 0 — PRE-FLIGHT (state as found, 2026-07-14)
-- ============================================================================
--   csweb_uhc_y2:  F1=2  F3=12  F4=0  Spike=0  Supervisor=1  Login=0  Menu=0
--                  F3 photos=6  F3 notes=1
--                  access_tokens=618  refresh_tokens=261
--                  sync_history=9  binary_sync=16
--                  users=18  (9 Administrator · 7 Field Sync · 2 Supervisor QA)
--   csweb_f2:      responses=41  hcws=16  audit=262  token_audit=13
--                  admin users=10  facilities=5 (all DEMO/test)
--
-- All 41 F2 responses verified as test data before deletion: every one against
-- DEMO-FAC-* / FAC-00x facilities, dated 2026-04-22 .. 2026-07-06 (the UAT
-- window). No real respondent data existed in either store.


-- ============================================================================
-- SECTION 1 — CSWeb: purge the 15 UAT test cases        [EXECUTED 2026-07-14]
-- ============================================================================
-- InnoDB only -> safe inside a transaction.
-- Child tables (notes, binary/photo blobs) first, then the case rows.
USE csweb_uhc_y2;
START TRANSACTION;

DELETE FROM FACILITYHEADSURVEY_DICT_notes;
DELETE FROM FACILITYHEADSURVEY_DICT_case_binary_data;
DELETE FROM FACILITYHEADSURVEY_DICT;              -- 2 test cases

DELETE FROM PATIENTSURVEY_DICT_notes;             -- 1
DELETE FROM PATIENTSURVEY_DICT_case_binary_data;  -- 6 verification photos
DELETE FROM PATIENTSURVEY_DICT;                   -- 12 test cases

DELETE FROM HOUSEHOLDSURVEY_DICT_notes;
DELETE FROM HOUSEHOLDSURVEY_DICT_case_binary_data;
DELETE FROM HOUSEHOLDSURVEY_DICT;                 -- was already 0

DELETE FROM HOUSEHOLDSURVEYSPIKE_DICT_notes;
DELETE FROM HOUSEHOLDSURVEYSPIKE_DICT_case_binary_data;
DELETE FROM HOUSEHOLDSURVEYSPIKE_DICT;            -- was already 0

DELETE FROM SUPERVISORAPP_DICT_notes;
DELETE FROM SUPERVISORAPP_DICT_case_binary_data;
DELETE FROM SUPERVISORAPP_DICT;                   -- 1 hub relay case

DELETE FROM LOGINAPP_DICT_notes;
DELETE FROM LOGINAPP_DICT_case_binary_data;
DELETE FROM LOGINAPP_DICT;                        -- was already 0

DELETE FROM MENUAPP_DICT_notes;
DELETE FROM MENUAPP_DICT_case_binary_data;
DELETE FROM MENUAPP_DICT;                         -- was already 0

-- Sync history is InnoDB -> belongs in THIS transaction, not with the oauth tables.
DELETE FROM cspro_sync_history;                   -- 9
DELETE FROM cspro_binary_sync_history;            -- 16
DELETE FROM cspro_binary_sync_history_archive;

COMMIT;


-- ============================================================================
-- SECTION 2 — CSWeb: device sessions (MyISAM)           [EXECUTED 2026-07-14]
-- ============================================================================
-- MUST run outside a transaction — see trap #1. NOT rollback-able.
-- Clearing these forces every tablet to log in again. That is intentional: it
-- guarantees no device carries a stale UAT session into the field. Devices
-- simply re-authenticate on next sync.
USE csweb_uhc_y2;

DELETE FROM oauth_access_tokens;                  -- 618
DELETE FROM oauth_refresh_tokens;                 -- 261
DELETE FROM oauth_authorization_codes;

-- Optional, NOT run: cspro_log holds ~6,141 rows of UAT noise. Harmless to
-- keep; clearing it just makes pretest troubleshooting easier to read.
-- DELETE FROM cspro_log;


-- ============================================================================
-- SECTION 3 — F2 (HCW): purge test responses            [EXECUTED 2026-07-14]
-- ============================================================================
-- All InnoDB -> transactional.
-- The July 9 migration rotated the JWT signing key, so every existing HCW
-- enrollment was already dead. This cleared the test responses behind them so
-- Thursday's HCW interviews are the first real data in the store.
--
-- Also SATISFIES #831 (Shan, R6): "Remove the response submitted on 2026-07-03
-- 10:44AM (Facility: DEMO-FAC-RHU-QC-1) ... human error, encoded token on HCW
-- ID." That row went with this purge. No code fix was needed.
USE csweb_f2;
START TRANSACTION;

DELETE FROM f2_responses;        -- 41 test responses
DELETE FROM f2_hcws;             -- 16 test enrollments
DELETE FROM auth_token_audit;    -- 13 stale token records
DELETE FROM auth_revoked;        -- 0
DELETE FROM f2_dlq;              -- 0
DELETE FROM f2_audit;            -- 262 UAT audit rows

COMMIT;

-- NOT deleted (config / not test data):
--   f2_facility_master (5) · f2_config (5) · f2_roles (4) · f2_settings
--   f2_users (10)  <- admin portal accounts; see Section 4
--   f2_files (3)   <- admin file manager
--   auth_kv (4)    <- login throttles + P4 marker


-- ============================================================================
-- SECTION 4 — IDENTITIES  ***NOT RUN — STILL DO NOT RUN***
-- ============================================================================
-- Deliberately dead code. Do not delete a single user until ASPSI's final
-- enumerator/supervisor list is in hand and you know what replaces them.
--
-- Current state (18 users, unchanged by this cleanup):
--   Administrators (9): admin, cplreyes, kidd, aidan, alytest, daisy, shan,
--                       pattest, marriz
--       ^ these carry REAL staff names and map to the field roster:
--         kidd=K.Pura · aidan=A.Paraiso · alytest=A.Salazar
--         daisy=D.Ramos · shan=S.Lait · pattest=P.Crudo
--         MISSING from the field roster: A. Almendral (no account at all)
--       Administrators CAN sync from CSEntry — these people are NOT locked out.
--
--   Field Sync (7): se-001..se-006, setest   <- hub test identities ("Tester")
--   Supervisor QA (2): fs-01, fs-02          <- hub test identities
--
-- The se-*/fs-* accounts are what the Supervisor Hub's Bluetooth roster binds
-- to. If they are renamed or replaced, THE HUB PACKAGE MUST BE REDEPLOYED before
-- tablets can pull assignments — and any test sweep run before that redeploy
-- proves nothing. Correct order:
--
--   ASPSI list -> cleanup -> create users -> regenerate assignments
--     -> REDEPLOY HUB -> sweep -> close UAT Round 6
--
-- Replacements come from the normal path (bulk-import CSV -> Users dashboard),
-- not from SQL.
--
-- DELETE FROM cspro_users WHERE username LIKE 'se-%' OR username LIKE 'fs-%'
--                            OR username = 'setest';
-- (Never delete: admin, cplreyes.)
-- ============================================================================


-- ============================================================================
-- SECTION 5 — POST-CLEANUP VERIFICATION   [PASSED 2026-07-14]
-- ============================================================================
USE csweb_uhc_y2;
SELECT (SELECT COUNT(*) FROM FACILITYHEADSURVEY_DICT)           AS f1_want_0,
       (SELECT COUNT(*) FROM PATIENTSURVEY_DICT)                AS f3_want_0,
       (SELECT COUNT(*) FROM HOUSEHOLDSURVEY_DICT)              AS f4_want_0,
       (SELECT COUNT(*) FROM SUPERVISORAPP_DICT)                AS hub_want_0,
       (SELECT COUNT(*) FROM PATIENTSURVEY_DICT_case_binary_data) AS photos_want_0,
       (SELECT COUNT(*) FROM oauth_access_tokens)               AS tokens_want_0,
       (SELECT COUNT(*) FROM cspro_sync_history)                AS sync_want_0;
-- result 2026-07-14:  0 · 0 · 0 · 0 · 0 · 0 · 0   ✅

SELECT (SELECT COUNT(*) FROM cspro_area_names)                  AS psgc_want_2360637,
       (SELECT COUNT(*) FROM cspro_apps)                        AS apps_want_6,
       (SELECT COUNT(*) FROM cspro_dictionaries)                AS dicts_want_7,
       (SELECT COUNT(*) FROM cspro_roles)                       AS roles_want_5,
       (SELECT COUNT(*) FROM cspro_role_dictionary_permissions) AS syncperms_want_12,
       (SELECT COUNT(*) FROM cspro_users)                       AS users_want_18;
-- result 2026-07-14:  2360637 · 6 · 7 · 5 · 12 · 18   ✅

USE csweb_f2;
SELECT (SELECT COUNT(*) FROM f2_responses)       AS responses_want_0,
       (SELECT COUNT(*) FROM f2_hcws)            AS hcws_want_0,
       (SELECT COUNT(*) FROM f2_audit)           AS audit_want_0,
       (SELECT COUNT(*) FROM f2_facility_master) AS facilities_want_5,
       (SELECT COUNT(*) FROM f2_users)           AS admin_users_want_10;
-- result 2026-07-14:  0 · 0 · 0 · 5 · 10   ✅

-- If 'psgc' or 'syncperms' ever comes back LOW, stop — the tablets will fail in
-- the field and it will not be obvious why. Restore from the dumps above.
-- ============================================================================


-- ============================================================================
-- SECTION 6 — BREAKOUT DBs (the reporting mirrors)      [EXECUTED 2026-07-14]
-- ============================================================================
-- WHY THIS IS NOT OPTIONAL:
--   The monitoring dashboard reads from the BREAKOUT databases (via
--   csweb_reports), NOT from csweb_uhc_y2. Purging the main DB alone leaves the
--   breakouts still holding the deleted cases — and they DO NOT SELF-HEAL.
--   The `csweb:process-cases` cron runs EVERY MINUTE, but it is INCREMENTAL:
--   it adds new cases, it never removes breakout rows for deleted ones. Left
--   alone, the dashboard would have shown 14 phantom cases (F1 2 · F3 12) on
--   day 1 of the pretest, before a single real interview.
--
-- Executed via /root/purge_breakouts.sql — explicit named DELETEs across the
-- section/roster tables of all three breakout DBs (InnoDB, transactional,
-- FOREIGN_KEY_CHECKS=0 for the duration).
--
-- PRESERVED in every breakout DB:
--   cspro_meta  <- the dictionary schema (~8MB of JSON). This is what drives
--                  breakout expansion. Delete it and the whole reporting
--                  pipeline breaks.
--   cspro_jobs  <- process-cases job state.
--
-- NOT TOUCHED AT ALL:
--   csweb_reports — its only populated table is facility_names (1,521
--   facilities), which is REFERENCE data, not case data.
--
-- Verified 2026-07-14:  f1.cases=0 · f3.cases=0 · f4.cases=0 · cspro_meta=1 each
-- ============================================================================


-- ============================================================================
-- FINAL STATE — verified 2026-07-14
-- ============================================================================
--            F1   F3   F4   HUB
--   main      0    0    0    0     ✅
--   breakout  0    0    0    —     ✅
--   F2:  responses=0 · hcws=0                                       ✅
--
--   PRESERVED: psgc=2,360,637 · facility_names=1,521 · users=18 · f2_admins=10
-- ============================================================================


-- ============================================================================
-- KNOWN GAP SURFACED BY THIS CLEANUP (not fixed here)
-- ============================================================================
-- f2_facility_master holds ONLY demo facilities:
--   DEMO-FAC-DH-INFANTA · DEMO-FAC-LYING-IN-BAL · DEMO-FAC-RHU-QC-1
--   FAC-001 (Test Facility) · FAC-002 (Makati Facility)
--
-- NONE of the real pretest sites are present — no Laguna Provincial Hospital,
-- no Los Baños RHU. HCW responses carry a facility_id, so Thursday's F2 needs
-- the real facility frame (9-digit codes) AND the HCW list per facility before
-- tokens can be minted. This is the "F2 facility frame" ASPSI owes per
-- F2-Prod-Migration-Plan §8. Tracked on #836 (P5 re-enrollment smoke).
-- ============================================================================
