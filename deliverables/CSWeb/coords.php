<?php
/**
 * coords.php — facility coordinate intake for the UHC Survey Year 2 Map.
 *
 * Lets survey staff enter lat/long for the "awaiting exact location" facilities from the map UI
 * (inline per-facility, or by uploading the filled CSV template). Writes ONLY the lat/lon/note
 * columns onto EXISTING rows of facility_coords_manual.csv — the rows already in that file are the
 * allow-list (the map's generator seeds it with the facilities that still need coordinates). The
 * on-box map generator reads this same file on its 2-minute cron, so saved coordinates become
 * violet "manual" pins on the next refresh.
 *
 * Served from /docs/ (behind the site's HTTP basic auth) by the lamp-php8 container, whose docroot
 * is the bind-mounted /opt/app/lamp/www. Safe by construction: fixed file path, no code/SQL/shell,
 * PH-bounds-validated coordinates, code9 must already exist in the file, atomic write, provenance
 * recorded in `note`.
 *
 *   GET  ?download           -> streams the current template CSV as a download
 *   POST application/json    -> { code9, lat, lon }  or  { entries:[{code9,lat,lon},...] }
 *   POST multipart (file=csv)-> the filled template; matches rows by code9
 */

header('Content-Type: application/json; charset=utf-8');

$FILE = '/var/www/html/docs/data/facility_coords_manual.csv';
$COLS = array('code9','facility_name','municipality','province','region','lat','lon','note');
$LAT_MIN = 4.5; $LAT_MAX = 21.5; $LON_MIN = 116.0; $LON_MAX = 127.0;

function read_rows($file, $cols) {
    $rows = array();
    if (!file_exists($file)) return $rows;
    if (($h = fopen($file, 'r')) !== false) {
        fgetcsv($h); // header
        while (($r = fgetcsv($h)) !== false) {
            if (count($r) === 1 && trim($r[0]) === '') continue;
            $row = array();
            foreach ($cols as $i => $c) $row[$c] = isset($r[$i]) ? $r[$i] : '';
            $code = trim($row['code9']);
            if ($code !== '') $rows[$code] = $row;
        }
        fclose($h);
    }
    return $rows;
}

function write_rows_atomic($file, $cols, $rows) {
    $dir = dirname($file);
    $tmp = tempnam($dir, 'fc_');
    if ($tmp === false) return false;
    $h = fopen($tmp, 'w');
    // UTF-8 BOM so Excel opens it cleanly, matching the seeded template
    fwrite($h, "\xEF\xBB\xBF");
    fputcsv($h, $cols);
    foreach ($rows as $row) {
        $line = array();
        foreach ($cols as $c) $line[] = isset($row[$c]) ? $row[$c] : '';
        fputcsv($h, $line);
    }
    fclose($h);
    @chmod($tmp, 0664);
    return rename($tmp, $file); // atomic replace — the generator never sees a partial file
}

function valid_ll($la, $lo) {
    global $LAT_MIN, $LAT_MAX, $LON_MIN, $LON_MAX;
    if (!is_numeric($la) || !is_numeric($lo)) return false;
    $la = (float)$la; $lo = (float)$lo;
    return $la >= $LAT_MIN && $la <= $LAT_MAX && $lo >= $LON_MIN && $lo <= $LON_MAX;
}

$who   = isset($_SERVER['PHP_AUTH_USER']) && $_SERVER['PHP_AUTH_USER'] !== '' ? $_SERVER['PHP_AUTH_USER'] : 'web';
$today = date('Y-m-d');

// ---- download the template ----
if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['download'])) {
    if (!file_exists($FILE)) { http_response_code(404); echo json_encode(array('ok'=>false,'error'=>'template not found on server')); exit; }
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="facility_coords_manual.csv"');
    header('Content-Length: ' . filesize($FILE));
    readfile($FILE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(array('ok'=>false,'error'=>'POST required (or GET ?download)'));
    exit;
}

$rows = read_rows($FILE, $COLS);
if (!$rows) { http_response_code(500); echo json_encode(array('ok'=>false,'error'=>'no coordinate template on server')); exit; }

$updated = array();
$skipped = array();

function apply_entry(&$rows, $code, $la, $lo, $who, $today, &$updated, &$skipped, $src) {
    $code = trim($code);
    if (!isset($rows[$code])) { $skipped[] = array('code9'=>$code, 'reason'=>'unknown facility code'); return; }
    if (!valid_ll($la, $lo))  { $skipped[] = array('code9'=>$code, 'reason'=>'lat/lon missing, non-numeric, or outside PH'); return; }
    $rows[$code]['lat']  = round((float)$la, 6);
    $rows[$code]['lon']  = round((float)$lo, 6);
    $rows[$code]['note'] = $src . ' by ' . $who . ' ' . $today;
    $updated[] = array('code9'=>$code, 'name'=>$rows[$code]['facility_name'],
                       'lat'=>$rows[$code]['lat'], 'lon'=>$rows[$code]['lon']);
}

$ctype = isset($_SERVER['CONTENT_TYPE']) ? $_SERVER['CONTENT_TYPE'] : '';

if (strpos($ctype, 'application/json') !== false) {
    $in = json_decode(file_get_contents('php://input'), true);
    if (!is_array($in)) { http_response_code(400); echo json_encode(array('ok'=>false,'error'=>'bad JSON')); exit; }
    $entries = isset($in['entries']) && is_array($in['entries']) ? $in['entries'] : array($in);
    foreach ($entries as $e) {
        apply_entry($rows, isset($e['code9'])?$e['code9']:'', isset($e['lat'])?$e['lat']:'',
                    isset($e['lon'])?$e['lon']:'', $who, $today, $updated, $skipped, 'web entry');
    }
} elseif (isset($_FILES['csv']) && is_uploaded_file($_FILES['csv']['tmp_name'])) {
    if (($h = fopen($_FILES['csv']['tmp_name'], 'r')) !== false) {
        $hdr = fgetcsv($h);
        if ($hdr) {
            // strip a UTF-8 BOM on the first header cell, map columns by (lowercased) name
            if (isset($hdr[0])) $hdr[0] = preg_replace('/^\xEF\xBB\xBF/', '', $hdr[0]);
            $idx = array();
            foreach ($hdr as $i => $name) $idx[strtolower(trim($name))] = $i;
            if (!isset($idx['code9']) || !isset($idx['lat']) || !isset($idx['lon'])) {
                http_response_code(400);
                echo json_encode(array('ok'=>false,'error'=>'CSV needs code9, lat, lon columns'));
                fclose($h); exit;
            }
            while (($r = fgetcsv($h)) !== false) {
                $get = function($k) use ($r, $idx) { return isset($idx[$k]) && isset($r[$idx[$k]]) ? trim($r[$idx[$k]]) : ''; };
                $code = $get('code9'); $la = $get('lat'); $lo = $get('lon');
                if ($code === '') continue;
                if ($la === '' && $lo === '') continue; // still-blank row — silently skip
                apply_entry($rows, $code, $la, $lo, $who, $today, $updated, $skipped, 'csv import');
            }
        }
        fclose($h);
    }
} else {
    http_response_code(400);
    echo json_encode(array('ok'=>false,'error'=>'send JSON {code9,lat,lon} or a CSV file field named "csv"'));
    exit;
}

if ($updated) {
    if (!write_rows_atomic($FILE, $COLS, $rows)) {
        http_response_code(500);
        echo json_encode(array('ok'=>false,'error'=>'could not write the file (permissions?)'));
        exit;
    }
}

echo json_encode(array(
    'ok' => true,
    'updated' => $updated,
    'updatedCount' => count($updated),
    'skipped' => $skipped,
    'note' => 'Saved. Pins refresh on the map within ~2 minutes.'
));
