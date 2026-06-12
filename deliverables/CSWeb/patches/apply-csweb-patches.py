#!/usr/bin/env python3
"""Re-apply the ASPSI on-box patches to CSWeb after an upgrade/re-install.

Run ON the server as root:  python3 /root/csweb-patches/apply-csweb-patches.py

Idempotent: each patch is skipped if its marker is already present. If the
"old" text is missing AND the marker is absent, upstream changed that code —
the script stops loudly so you can review (the bug may be fixed upstream).

Covers the 5 patched files (see *.patch diffs in this folder for reference)
plus the two MySQL settings, then clears the Twig cache and restarts PHP.
Record: deliverables/CSWeb/CSWeb-Sync-Report-and-Case-Breakout-Setup.md
"""
import os, subprocess, sys

CSWEB = "/opt/app/lamp/www/csweb"

PATCHES = [
    # (file, marker-that-means-applied, old, new)
    (
        "src/AppBundle/CSPro/Dictionary/MySQLDictionarySchemaGenerator.php",
        "COLUMN_TYPE_STRING",
        "    public const COLUMN_TYPE_TEXT = 'text';",
        "    public const COLUMN_TYPE_TEXT = 'text';\n"
        "    public const COLUMN_TYPE_STRING = 'string';",
    ),
    (
        "src/AppBundle/CSPro/Dictionary/MySQLDictionarySchemaGenerator.php",
        "row-size limit (error 1118)",
        '        if ($item->getDataType() === "Numeric") {\n'
        "            return self::COLUMN_TYPE_DECIMAL;\n"
        "        } else {\n"
        "            return self::COLUMN_TYPE_TEXT;\n"
        "        }",
        '        if ($item->getDataType() === "Numeric") {\n'
        "            return self::COLUMN_TYPE_DECIMAL;\n"
        "        } elseif ($item->getLength() <= 255) {\n"
        "            // alpha items have fixed lengths; VARCHAR(len) avoids InnoDB's\n"
        "            // row-size limit (error 1118) on records with many alpha items\n"
        "            return self::COLUMN_TYPE_STRING;\n"
        "        } else {\n"
        "            return self::COLUMN_TYPE_TEXT;\n"
        "        }",
    ),
    (
        "src/AppBundle/CSPro/Dictionary/MySQLDictionarySchemaGenerator.php",
        '$options["length"] = max(1, (int) $item->getLength());',
        '        if ($itemType === self::COLUMN_TYPE_DECIMAL) {\n'
        '            $options["precision"] = $item->getLength();\n'
        '            $options["scale"] = $item->getDecimalPlaces();\n'
        "        }",
        '        if ($itemType === self::COLUMN_TYPE_DECIMAL) {\n'
        '            $options["precision"] = $item->getLength();\n'
        '            $options["scale"] = $item->getDecimalPlaces();\n'
        "        }\n"
        "        if ($itemType === self::COLUMN_TYPE_STRING) {\n"
        '            $options["length"] = max(1, (int) $item->getLength());\n'
        "        }",
    ),
    (
        "src/AppBundle/CSPro/DictionarySchemaHelper.php",
        "execute statements individually",
        '            $dictionarySQL = $schema->toSql($this->conn->getDatabasePlatform());\n'
        '            $dictionarySQL = implode(";" . PHP_EOL, $dictionarySQL);\n'
        '            $this->logger->debug("writing schema SQL " . $dictionarySQL);\n'
        "\n"
        "            $this->conn->prepare($dictionarySQL)->execute();",
        '            $dictionarySQL = $schema->toSql($this->conn->getDatabasePlatform());\n'
        "            // execute statements individually: a single multi-statement prepare()\n"
        "            // only reports first-statement errors and silently skips the rest\n"
        "            foreach ($dictionarySQL as $statementSQL) {\n"
        '                $this->logger->debug("writing schema SQL " . $statementSQL);\n'
        "                $this->conn->executeStatement($statementSQL);\n"
        "            }",
    ),
    (
        "src/AppBundle/Controller/api/ReportController.php",
        "convertGeocodesToAreaNames returns StreamedResponse",
        "function importAreaNames(Request $request): CSProResponse {",
        "function importAreaNames(Request $request) { "
        "// ASPSI 2026-06-12: convertGeocodesToAreaNames returns StreamedResponse; "
        "the CSProResponse return type made every successful import 500 with a TypeError",
    ),
    (
        "templates/mapReport.twig",
        "default to Philippines instead of fitWorld()",
        "mymap: L.map('mapid', {\n"
        "                                               }).fitWorld(),",
        "mymap: L.map('mapid', {\n"
        "                                               }).setView([12.88, 121.77], 6), "
        "// ASPSI 2026-06-12: default to Philippines instead of fitWorld()",
    ),
    (
        "templates/mapReport.twig",
        "Philippines, not fitWorld()",
        "                                                       if (this.fitWorld) {\n"
        "                                                           map.mymap.fitWorld();\n"
        "                                                       }",
        "                                                       if (this.fitWorld) {\n"
        "                                                           map.mymap.setView([12.88, 121.77], 6); "
        "// ASPSI 2026-06-12: Philippines, not fitWorld()\n"
        "                                                       }",
    ),
]

CSS_APPEND = """
/* ASPSI 2026-06-12: long dictionary names (e.g. "FACILITYHEADSURVEY_DICT")
   overflow the sidebar submenu box; let them wrap inside it */
.sidebar .nav-item .collapse .collapse-inner .collapse-item,
.sidebar .nav-item .collapsing .collapse-inner .collapse-item {
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: break-word;
}

/* ASPSI 2026-06-12: "View case" modal — Bootstrap's modal-lg max-width (800px)
   overrides the template's inline width:80%, clipping the record tables.
   Let the dialog actually use the viewport. */
#pointInfoModal .modal-dialog {
    max-width: 92vw;
    width: 92vw;
}
"""

def run(argv, **kw):
    return subprocess.run(argv, text=True, capture_output=True, **kw)

def main():
    applied = skipped = 0
    for relpath, marker, old, new in PATCHES:
        path = os.path.join(CSWEB, relpath)
        src = open(path).read()
        if marker in src:
            skipped += 1
            print(f"[skip]  {relpath}: marker present")
            continue
        if old not in src:
            sys.exit(f"[STOP]  {relpath}: neither marker nor original text found — "
                     f"upstream changed this code. Review {relpath} manually "
                     f"(the bug may be fixed upstream).")
        backup = path + ".orig-preapply"
        if not os.path.exists(backup):
            open(backup, "w").write(src)
        open(path, "w").write(src.replace(old, new, 1))
        applied += 1
        print(f"[patch] {relpath}")

    css = os.path.join(CSWEB, "dist/css/cspro-styles.css")
    src = open(css).read()
    if "overflow-wrap: anywhere" in src:
        print("[skip]  cspro-styles.css: marker present")
        skipped += 1
    else:
        open(css, "a").write(CSS_APPEND)
        print("[patch] cspro-styles.css (appended UI rules)")
        applied += 1

    # lint php
    for f in ("src/AppBundle/CSPro/Dictionary/MySQLDictionarySchemaGenerator.php",
              "src/AppBundle/CSPro/DictionarySchemaHelper.php",
              "src/AppBundle/Controller/api/ReportController.php"):
        r = run(["docker", "exec", "lamp-php8", "php", "-l",
                 f"/var/www/html/csweb/{f}"])
        if "No syntax errors" not in r.stdout:
            sys.exit(f"[STOP] php -l failed for {f}:\n{r.stdout}{r.stderr}")
    print("[ok]    php -l clean")

    # MySQL settings (idempotent)
    pw = next(l.split("=", 1)[1].strip() for l in open("/opt/app/.env")
              if l.startswith("MYSQL_ROOT_PASSWORD"))
    sql = ("SET PERSIST log_bin_trust_function_creators = 1; "
           "SET PERSIST sql_mode = (SELECT REPLACE(REPLACE(@@GLOBAL.sql_mode,"
           "'ONLY_FULL_GROUP_BY,',''),'ONLY_FULL_GROUP_BY',''));")
    r = subprocess.run(["docker", "compose", "exec", "-T", "database", "mysql",
                        "-uroot", f"-p{pw}", "-e", sql], cwd="/opt/app",
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    print("[ok]    MySQL settings persisted" if r.returncode == 0
          else f"[WARN]  MySQL settings failed: {r.stderr[:200]}")

    # twig cache + ownership + php restart
    run(["docker", "exec", "lamp-php8", "sh", "-c",
         "cd /var/www/html/csweb && rm -rf var/cache/*/twig; "
         "php bin/console cache:clear >/dev/null 2>&1; "
         "chown -R 33:33 var/cache var/logs"])
    run(["docker", "restart", "lamp-php8"])
    print(f"[done]  {applied} applied, {skipped} already present. "
          "Verify: sync-report renders, map opens on PH, then re-upload the "
          "labels CSV if cspro_area_names was lost.")

if __name__ == "__main__":
    main()
