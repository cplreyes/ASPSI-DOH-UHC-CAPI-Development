#!/usr/bin/env python3
r"""make_mbtiles.py -- build a RASTER MBTiles offline base map for CSPro/CSEntry (N3).

Downloads {z}/{x}/{y} PNG tiles for a bounding box + zoom range and packs them into an
MBTiles SQLite file -- the format CSPro 8's `Map.setBaseMap()` / PFF `BaseMap=` consumes
(raster PNG/JPEG only; vector tiles are NOT supported). Stdlib only (sqlite3 + urllib).

LICENSING / SOURCE: tiles are (c) their provider. Default source = OpenStreetMap
((c) OpenStreetMap contributors, ODbL). The OSM tile-usage policy DISCOURAGES bulk
downloading, so this script is rate-limited and intended for SMALL, one-off offline
field-survey extracts of a clipped area. For a LARGE / national base map or wider
redistribution, point --url at a licensed source (MapTiler / Esri with a key, or
self-rendered tiles) -- nothing else changes. Always keep the attribution in metadata.

Usage:
  py make_mbtiles.py --bbox minlon,minlat,maxlon,maxlat --minzoom 8 --maxzoom 14 \
     --out survey_basemap.mbtiles \
     [--url "https://tile.openstreetmap.org/{z}/{x}/{y}.png"] [--delay 1.0] [--count-only]
"""
import argparse
import math
import sqlite3
import time
import urllib.request
from pathlib import Path


def deg2tile(lat, lon, z):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    lat_r = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n)
    return max(0, min(n - 1, x)), max(0, min(n - 1, y))


def tiles_for(bbox, z):
    minlon, minlat, maxlon, maxlat = bbox
    x0, y0 = deg2tile(maxlat, minlon, z)   # top-left
    x1, y1 = deg2tile(minlat, maxlon, z)   # bottom-right
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            yield x, y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbox", required=True, help="minlon,minlat,maxlon,maxlat")
    ap.add_argument("--minzoom", type=int, default=8)
    ap.add_argument("--maxzoom", type=int, default=14)
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", default="https://tile.openstreetmap.org/{z}/{x}/{y}.png")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--ua", default="ASPSI-DOH-UHC-CAPI offline-basemap one-off field extract (clreyes6@up.edu.ph)")
    ap.add_argument("--count-only", action="store_true")
    ap.add_argument("--map-id", default=None,
                    help="MapTiler raster map id (e.g. streets-v2); builds the api.maptiler.com URL "
                         "with the key read from --key-file. Overrides --url.")
    ap.add_argument("--key-file", default=".maptiler-key",
                    help="file holding the MapTiler API key (gitignored; never committed)")
    ap.add_argument("--attribution", default="(c) OpenStreetMap contributors (ODbL)")
    a = ap.parse_args()
    bbox = tuple(float(v) for v in a.bbox.split(","))

    if a.map_id:
        key = Path(a.key_file).read_text(encoding="utf-8").strip()
        a.url = f"https://api.maptiler.com/maps/{a.map_id}/{{z}}/{{x}}/{{y}}.png?key={key}"
        if a.attribution == "(c) OpenStreetMap contributors (ODbL)":
            a.attribution = "(c) MapTiler (c) OpenStreetMap contributors"

    total = sum(1 for z in range(a.minzoom, a.maxzoom + 1) for _ in tiles_for(bbox, z))
    print(f"tiles: {total}  (z{a.minzoom}-{a.maxzoom}, bbox {bbox}, ~{total * a.delay / 60:.1f} min @ {a.delay}s)")
    if a.count_only:
        return

    out = Path(a.out)
    db = sqlite3.connect(out)
    db.executescript(
        "CREATE TABLE IF NOT EXISTS metadata (name TEXT, value TEXT);"
        "CREATE TABLE IF NOT EXISTS tiles (zoom_level INT, tile_column INT, tile_row INT, tile_data BLOB);"
        "CREATE UNIQUE INDEX IF NOT EXISTS tiles_idx ON tiles (zoom_level, tile_column, tile_row);"
    )
    minlon, minlat, maxlon, maxlat = bbox
    meta = {
        "name": "UHC survey offline base map", "type": "baselayer", "version": "1",
        "format": "png", "minzoom": str(a.minzoom), "maxzoom": str(a.maxzoom),
        "bounds": f"{minlon},{minlat},{maxlon},{maxlat}",
        "center": f"{(minlon + maxlon) / 2},{(minlat + maxlat) / 2},{a.minzoom}",
        "attribution": a.attribution,
    }
    db.execute("DELETE FROM metadata")
    db.executemany("INSERT INTO metadata VALUES (?,?)", list(meta.items()))
    db.commit()

    done = got = skipped = failed = 0
    for z in range(a.minzoom, a.maxzoom + 1):
        for x, y in tiles_for(bbox, z):
            done += 1
            tms_y = (2 ** z - 1) - y          # MBTiles uses TMS (y flipped vs XYZ)
            if db.execute("SELECT 1 FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
                          (z, x, tms_y)).fetchone():
                skipped += 1
                continue
            url = a.url.format(z=z, x=x, y=y)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": a.ua})
                data = urllib.request.urlopen(req, timeout=30).read()
                db.execute("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?)", (z, x, tms_y, data))
                got += 1
                if got % 20 == 0:
                    db.commit()
                    print(f"  {done}/{total}  z{z}  ({got} fetched, {failed} failed)")
                time.sleep(a.delay)
            except Exception as e:
                failed += 1
                print(f"  ! {z}/{x}/{y}: {e}")
                time.sleep(a.delay)
    db.commit()
    size = out.stat().st_size / 1e6
    db.close()
    print(f"DONE: {got} fetched, {skipped} present, {failed} failed -> {out} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
