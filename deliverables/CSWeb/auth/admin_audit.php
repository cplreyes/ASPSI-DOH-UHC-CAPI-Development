<?php
/**
 * CAPI Console — Admin API: audit trail (E9-ADMIN-007 / -024).
 * Design: deliverables/CSWeb/admin-portal/DESIGN.md §2         Carl, 2026-08-08
 *
 * Answers SC-3: "who looked at what". Append-only by construction — there is
 * no write path in this file at all, and the plan to remove the DELETE grant
 * the web user currently holds is E9-ADMIN-012.
 *
 * Paging is by cursor (`before_id`), not OFFSET. The table grows by one row
 * per protected request after cutover; OFFSET paging over that either skips or
 * repeats rows as new ones land while an operator reads page three.
 */
declare(strict_types=1);

const ADM_AUDIT_PAGE_MAX = 200;
const ADM_AUDIT_CSV_MAX  = 20000;

/**
 * @param array<int,string> $seg path segments after `audit`
 */
function adm_audit_route(string $method, array $seg): never
{
    $actor = adm_require_perm('audit.view');
    if ($method !== 'GET') { throw new AdmError('method', 'Method not allowed.', 405); }

    if ($seg === [])                { adm_audit_list(); }
    if ($seg === ['csv'])           { adm_audit_csv($actor); }
    if ($seg === ['verbs'])         { adm_audit_verbs(); }

    throw new AdmError('not_found', 'No such endpoint.', 404);
}

/**
 * Build the WHERE clause shared by the list and the export, so the CSV an
 * auditor receives is exactly the rows the operator was looking at. Two
 * separate filter implementations is how an export quietly widens scope.
 *
 * @return array{0:string,1:array<int,mixed>}
 */
function adm_audit_filters(): array
{
    $where  = ['1 = 1'];
    $params = [];

    $actorF = adm_str($_GET, 'actor', 64);
    if ($actorF !== '') { $where[] = 'a.actor = ?'; $params[] = $actorF; }

    $verb = adm_str($_GET, 'verb', 32);
    if ($verb !== '') {
        // Prefix match so `user.` selects the whole family without the caller
        // having to know every verb in it.
        if (str_ends_with($verb, '.')) {
            $where[]  = 'a.verb LIKE ?';
            $params[] = str_replace(['\\', '%', '_'], ['\\\\', '\\%', '\\_'], $verb) . '%';
        } else {
            $where[]  = 'a.verb = ?';
            $params[] = $verb;
        }
    }

    $target = adm_str($_GET, 'target', 255);
    if ($target !== '') {
        $where[]  = 'a.target LIKE ?';
        $params[] = '%' . str_replace(['\\', '%', '_'], ['\\\\', '\\%', '\\_'], $target) . '%';
    }

    $rid = adm_str($_GET, 'request_id', 32);
    if ($rid !== '') { $where[] = 'a.request_id = ?'; $params[] = $rid; }

    foreach (['from' => '>=', 'to' => '<='] as $key => $op) {
        $v = adm_str($_GET, $key, 25);
        if ($v === '') { continue; }
        // Accept a bare date; `to=2026-08-08` must mean the whole of that day,
        // not midnight, or the last day of a range silently returns nothing.
        if (preg_match('/^\d{4}-\d{2}-\d{2}$/', $v)) {
            $v .= $key === 'to' ? ' 23:59:59' : ' 00:00:00';
        } elseif (!preg_match('/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?$/', $v)) {
            throw adm_bad('Dates must be YYYY-MM-DD or YYYY-MM-DD HH:MM.', $key);
        }
        $where[]  = 'a.ts ' . $op . ' ?';
        $params[] = str_replace('T', ' ', $v);
    }

    return [implode(' AND ', $where), $params];
}

function adm_audit_shape(array $r): array
{
    return [
        'id'         => (int) $r['id'],
        'ts'         => $r['ts'],
        'actor'      => (string) $r['actor'],
        'verb'       => (string) $r['verb'],
        'target'     => (string) $r['target'],
        'ip'         => (string) $r['ip'],
        'request_id' => (string) ($r['request_id'] ?? ''),
        'detail'     => $r['detail'] === null ? null : json_decode((string) $r['detail'], true),
    ];
}

function adm_audit_list(): never
{
    [$where, $params] = adm_audit_filters();

    $limit  = adm_int($_GET, 'limit', 50, 1, ADM_AUDIT_PAGE_MAX);
    $before = adm_int($_GET, 'before_id', 0, 0);
    if ($before > 0) { $where .= ' AND a.id < ?'; $params[] = $before; }

    // Ask for one more than requested: if it comes back, there is another page.
    // Cheaper and more honest than a COUNT(*) over a growing table.
    $st = auth_db()->prepare(
        'SELECT a.id, a.ts, a.actor, a.verb, a.target, a.detail, a.ip, a.request_id
           FROM console_audit a
          WHERE ' . $where . '
          ORDER BY a.id DESC
          LIMIT ' . ($limit + 1)
    );
    $st->execute($params);
    $rows = $st->fetchAll();

    $hasMore = count($rows) > $limit;
    if ($hasMore) { array_pop($rows); }

    $entries = array_map('adm_audit_shape', $rows);

    adm_ok([
        'entries'    => $entries,
        'has_more'   => $hasMore,
        'next_before'=> $entries === [] ? null : $entries[count($entries) - 1]['id'],
        'limit'      => $limit,
    ]);
}

/** Distinct verbs and actors, for populating the filter dropdowns. */
function adm_audit_verbs(): never
{
    $db = auth_db();
    $verbs = $db->query(
        'SELECT verb, COUNT(*) AS n FROM console_audit GROUP BY verb ORDER BY verb'
    )->fetchAll();
    $actors = $db->query(
        "SELECT actor, COUNT(*) AS n FROM console_audit
          WHERE actor <> '' GROUP BY actor ORDER BY actor"
    )->fetchAll();

    adm_ok([
        'verbs'  => array_map(static fn($r) => ['verb' => (string) $r['verb'], 'count' => (int) $r['n']], $verbs),
        'actors' => array_map(static fn($r) => ['actor' => (string) $r['actor'], 'count' => (int) $r['n']], $actors),
    ]);
}

/**
 * CSV export.
 *
 * Built fully in memory before a single byte is sent. Streaming would be
 * cheaper, but the catch-all exception handler emits a JSON body — and a JSON
 * error object appended to half a CSV file produces a download that opens
 * without complaint and is quietly truncated. Bounded at ADM_AUDIT_CSV_MAX
 * rows, and the response says so rather than silently cutting the tail.
 */
function adm_audit_csv(array $actor): never
{
    [$where, $params] = adm_audit_filters();

    $st = auth_db()->prepare(
        'SELECT a.id, a.ts, a.actor, a.verb, a.target, a.detail, a.ip, a.request_id
           FROM console_audit a
          WHERE ' . $where . '
          ORDER BY a.id DESC
          LIMIT ' . (ADM_AUDIT_CSV_MAX + 1)
    );
    $st->execute($params);
    $rows = $st->fetchAll();

    $truncated = count($rows) > ADM_AUDIT_CSV_MAX;
    if ($truncated) { array_pop($rows); }

    $fh = fopen('php://temp', 'r+');
    fputcsv($fh, ['id', 'timestamp_utc', 'actor', 'verb', 'target', 'ip', 'request_id', 'detail']);
    foreach ($rows as $r) {
        fputcsv($fh, [
            $r['id'], $r['ts'], $r['actor'], $r['verb'], $r['target'],
            $r['ip'], $r['request_id'] ?? '', (string) ($r['detail'] ?? ''),
        ]);
    }
    if ($truncated) {
        fputcsv($fh, ['', '', '', 'TRUNCATED', 'Export limit of ' . ADM_AUDIT_CSV_MAX
                      . ' rows reached — narrow the date range', '', '', '']);
    }
    rewind($fh);
    $csv = (string) stream_get_contents($fh);
    fclose($fh);

    // Exporting the audit trail is itself an auditable act.
    auth_audit($actor['username'], 'audit.export', '', [
        'rows'      => count($rows),
        'truncated' => $truncated,
        'filters'   => array_intersect_key($_GET, array_flip(
            ['actor', 'verb', 'target', 'from', 'to', 'request_id'])),
    ]);

    $name = 'capi-audit-' . gmdate('Ymd-His') . '.csv';
    http_response_code(200);
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="' . $name . '"');
    header('Content-Length: ' . strlen($csv));
    header('X-Content-Type-Options: nosniff');
    header('Cache-Control: no-store, private');
    header('X-Request-Id: ' . adm_request_id());
    echo $csv;
    exit;
}
