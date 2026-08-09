<?php
/**
 * CAPI Console — identity garbage collection (E9-ADMIN-043).   Carl, 2026-08-09
 *
 *   docker compose exec -T webserver php /var/www/private/capi-auth/gc.php
 *   docker compose exec -T webserver php /var/www/private/capi-auth/gc.php --dry-run
 *
 * Runs nightly from cron. Two jobs, both about not keeping personal data
 * longer than it is useful:
 *
 *   console_sessions — every row carries an IP address and a user-agent
 *     string. That is personal data under RA 10173 and it had no stated
 *     retention at all, which is the finding an audit makes first. Dead rows
 *     older than the window below are removed.
 *
 *   console_idem — replay-protection records. Useful for hours, kept a day,
 *     pointless after that.
 *
 * console_audit is deliberately NOT touched. It is append-only to the
 * application by grant (E9-ADMIN-012) and its retention is engagement end
 * plus six months — see admin-portal/RETENTION.md. Pruning it will need a
 * separate user with a DELETE grant on that one table, created at the time and
 * removed afterwards.
 */
declare(strict_types=1);

require_once __DIR__ . '/lib.php';

/** How long a dead session row is kept for incident investigation. */
const GC_SESSION_RETAIN_DAYS = 30;
/** Idempotency keys stop being useful once no client could still retry. */
const GC_IDEM_RETAIN_HOURS   = 24;

$dry = in_array('--dry-run', $argv, true);
$db  = auth_db();

function scalar(PDO $db, string $sql, array $args = []): int
{
    $st = $db->prepare($sql);
    $st->execute($args);
    return (int) $st->fetchColumn();
}

// --- what would go -----------------------------------------------------------
$deadSessions = scalar($db,
    'SELECT COUNT(*) FROM console_sessions
      WHERE (revoked_at IS NOT NULL AND revoked_at < DATE_SUB(NOW(), INTERVAL ? DAY))
         OR (expires_at < DATE_SUB(NOW(), INTERVAL ? DAY))',
    [GC_SESSION_RETAIN_DAYS, GC_SESSION_RETAIN_DAYS]);

$staleIdem = scalar($db,
    'SELECT COUNT(*) FROM console_idem WHERE created_at < DATE_SUB(NOW(), INTERVAL ? HOUR)',
    [GC_IDEM_RETAIN_HOURS]);

$liveSessions = scalar($db,
    'SELECT COUNT(*) FROM console_sessions
      WHERE revoked_at IS NULL AND expires_at > NOW()
        AND last_seen_at > DATE_SUB(NOW(), INTERVAL ? SECOND)', [AUTH_IDLE_SECS]);

$auditRows = scalar($db, 'SELECT COUNT(*) FROM console_audit');
$oldest    = $db->query('SELECT COALESCE(MIN(ts), "-") FROM console_audit')->fetchColumn();

printf("capi-auth GC %s\n", $dry ? '(DRY RUN — nothing will be deleted)' : '');
printf("  sessions live now              : %d\n", $liveSessions);
printf("  sessions eligible for removal  : %d  (dead > %d days)\n", $deadSessions, GC_SESSION_RETAIN_DAYS);
printf("  idempotency keys to remove     : %d  (older than %d h)\n", $staleIdem, GC_IDEM_RETAIN_HOURS);
printf("  audit rows (never pruned here) : %d, oldest %s\n", $auditRows, $oldest);

if ($dry) { exit(0); }

// --- do it -------------------------------------------------------------------
$st = $db->prepare(
    'DELETE FROM console_sessions
      WHERE (revoked_at IS NOT NULL AND revoked_at < DATE_SUB(NOW(), INTERVAL ? DAY))
         OR (expires_at < DATE_SUB(NOW(), INTERVAL ? DAY))'
);
$st->execute([GC_SESSION_RETAIN_DAYS, GC_SESSION_RETAIN_DAYS]);
$goneSessions = $st->rowCount();

$st = $db->prepare('DELETE FROM console_idem WHERE created_at < DATE_SUB(NOW(), INTERVAL ? HOUR)');
$st->execute([GC_IDEM_RETAIN_HOURS]);
$goneIdem = $st->rowCount();

printf("  removed: %d sessions, %d idempotency keys\n", $goneSessions, $goneIdem);

// The GC run is itself an auditable event: "those session records are gone"
// should be answerable from the trail rather than from inference.
if ($goneSessions > 0 || $goneIdem > 0) {
    auth_audit('system', 'gc', 'capi_auth', [
        'sessions_removed' => $goneSessions,
        'idem_removed'     => $goneIdem,
        'session_retain_days' => GC_SESSION_RETAIN_DAYS,
    ]);
}
exit(0);
