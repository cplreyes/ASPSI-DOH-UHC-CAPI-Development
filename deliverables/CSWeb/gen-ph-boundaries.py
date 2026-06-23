#!/usr/bin/env python3
r"""One-time / re-runnable: build a COMPACT PH admin-area asset (region + province
centroids, radii, and simplified polygons) that the Map Report's Tier B/C spatial
QA reads each run. Keeps the heavy geo sourcing out of the 15-min cron.

Source: faeldon/philippines-json-maps `2011/geojson/.../lowres` (GitHub raw is
reachable from the box; GADM's host is NOT). Fetched via curl (proven to work).
  - regions/lowres/regions.0.001.json          (1 file, all 17 regions)
  - provinces/lowres/provinces-region-<slug>.0.001.json   (17 files)

Join is by NAME (our breakout geo CODES are survey-internal, not PSGC): province
names match faeldon `PROVINCE` exactly; region names are word-reordered
("Region I (Ilocos Region)" vs "Ilocos Region (Region I)") so we key on a
sorted-token normalisation.

Vintage = 2011 PSGC names (pre Davao-de-Oro / Maguindanao-split / NIR etc.).
Newer province names simply log as unmatched in the generator rather than
mis-assigning — never a silent wrong answer.

Output: /opt/app/lamp/www/docs/assets/ph-areas.json  (coords stored [lat,lon]).
Run on the box:  python3 /opt/gen-ph-boundaries.py
First built 2026-06-21 (Map Report v3).
"""
import json, subprocess, math, re, pathlib

BASE = "https://raw.githubusercontent.com/faeldon/philippines-json-maps/master/2011/geojson"
OUT = "/opt/app/lamp/www/docs/assets/ph-areas.json"
REGION_SLUGS = [
    "autonomousregionofmuslimmindanaoarmm", "bicolregionregionv",
    "cagayanvalleyregionii", "calabarzonregioniva", "caragaregionxiii",
    "centralluzonregioniii", "centralvisayasregionvii",
    "cordilleraadministrativeregioncar", "davaoregionregionxi",
    "easternvisayasregionviii", "ilocosregionregioni", "metropolitanmanila",
    "mimaroparegionivb", "northernmindanaoregionx", "soccsksargenregionxii",
    "westernvisayasregionvi", "zamboangapeninsularegionix",
]


def norm(s):
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    return " ".join(sorted(s.split()))


def fetch(url):
    r = subprocess.run(["curl", "-fsSL", url], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout:
        raise SystemExit("fetch failed: " + url)
    return json.loads(r.stdout)


def rings_of(geom):
    """-> list of polygons; each polygon = list of rings; each ring = [[lon,lat],...]"""
    if not geom:
        return []
    t, c = geom["type"], geom["coordinates"]
    if t == "Polygon":
        return [c]
    if t == "MultiPolygon":
        return c
    return []


def shoelace(ring):
    """ring=[[lon,lat],...] -> (cx,cy,area) in lon/lat units."""
    a = cx = cy = 0.0
    n = len(ring)
    for i in range(n - 1):
        x0, y0 = ring[i]
        x1, y1 = ring[i + 1]
        cr = x0 * y1 - x1 * y0
        a += cr
        cx += (x0 + x1) * cr
        cy += (y0 + y1) * cr
    if a == 0:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        return sum(xs) / n, sum(ys) / n, 0.0
    a *= 0.5
    return cx / (6 * a), cy / (6 * a), abs(a)


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p = math.pi / 180
    dlat = (lat2 - lat1) * p
    dlon = (lon2 - lon1) * p
    x = math.sin(dlat / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def record(name, region, polys):
    tcx = tcy = ta = 0.0
    verts = []
    for poly in polys:
        ext = poly[0]
        cx, cy, a = shoelace(ext)
        tcx += cx * a
        tcy += cy * a
        ta += a
        verts.extend(ext)
    if ta > 0:
        clon, clat = tcx / ta, tcy / ta
    else:
        clon = sum(v[0] for v in verts) / len(verts)
        clat = sum(v[1] for v in verts) / len(verts)
    radius = max(haversine(clat, clon, v[1], v[0]) for v in verts)
    out_polys = [[[[round(pt[1], 4), round(pt[0], 4)] for pt in ring] for ring in poly]
                 for poly in polys]
    rec = {"name": name, "centroid": [round(clat, 5), round(clon, 5)],
           "radius_km": round(radius, 1), "polys": out_polys}
    if region:
        rec["region"] = region
    return rec


skipped = []
regions = {}
rd = fetch(BASE + "/regions/lowres/regions.0.001.json")
for ft in rd["features"]:
    nm = ft["properties"]["REGION"]
    polys = rings_of(ft["geometry"])
    if not polys:
        skipped.append("region:" + str(nm))
        continue
    regions[norm(nm)] = record(nm, None, polys)

provinces = {}
for slug in REGION_SLUGS:
    pd = fetch(BASE + "/provinces/lowres/provinces-region-%s.0.001.json" % slug)
    for ft in pd["features"]:
        nm = ft["properties"]["PROVINCE"]
        rg = ft["properties"].get("REGION")
        polys = rings_of(ft["geometry"])
        if not polys:
            skipped.append("province:" + str(nm))
            continue
        provinces[norm(nm)] = record(nm, rg, polys)

data = {"regions": regions, "provinces": provinces,
        "source": "faeldon/philippines-json-maps 2011 lowres", "coords": "[lat,lon]"}
pathlib.Path(OUT).write_text(json.dumps(data), encoding="utf-8")
print("regions=%d provinces=%d bytes=%d -> %s"
      % (len(regions), len(provinces), pathlib.Path(OUT).stat().st_size, OUT))
if skipped:
    print("skipped (null geometry):", skipped)
