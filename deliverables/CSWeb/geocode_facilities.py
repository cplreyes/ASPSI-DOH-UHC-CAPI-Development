#!/usr/bin/env python3
r"""Geocode the UHC facility masterlist via Nominatim (OpenStreetMap) -> facility_coords.csv.

CANDIDATE coordinates only. Every row still has to pass the map's validation (point-in-polygon
vs declared province, distance-to-captured-GPS, duplicate/centroid detection) before it is
trusted — this just fetches candidates in minutes instead of hand-pinning 1,500+.

Free-tier good citizen: 1 request/second, a descriptive User-Agent, graceful 429/503 backoff.
Resumable: re-running skips code9s already in the out CSV (append), so an interrupted run
continues. Confidence tiers let the map/RA review the low-confidence minority.

Input : targets.json ({targets:{inst:{code9:{name,region,province}}}}) — the masterlist.
Output: facility_coords.csv (code9 -> lat/lon + confidence + source), consumed by csweb-map-gen.py.

Usage: py geocode_facilities.py --targets prod-targets.json --out facility_coords.csv [--limit N] [--sleep 1.1]
"""
import json, csv, time, re, argparse, os
import urllib.parse, urllib.request, urllib.error

UA = "ASPSI-DOH-UHC-Survey2-facility-geocoder/1.0 (clreyes6@up.edu.ph)"
BASE = "https://nominatim.openstreetmap.org/search"
FIELDS = ["code9", "name", "declared_region", "declared_prov", "lat", "lon",
          "osm_class", "osm_type", "importance", "matched_name", "ret_prov",
          "prov_match", "confidence", "flag", "query"]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def load_facilities(path):
    """Accepts either targets.json ({targets:{inst:{code9:{name,region,province}}}}, no city)
    or a flat masterlist ({code9:{name,city,prov,region}}) — the latter (from Kidd's Patient
    Allocation sheet) carries City/Municipality, which lifts RHU/PCF geocoding hit rates."""
    d = json.load(open(path, encoding="utf-8"))
    fac = {}
    if isinstance(d, dict) and "targets" in d:
        for _inst, mp in (d.get("targets") or {}).items():
            for code, t in mp.items():
                r = fac.setdefault(code, {"name": "", "region": "", "prov": "", "city": ""})
                r["name"] = r["name"] or (t.get("name") or "")
                r["region"] = r["region"] or (t.get("region") or "")
                r["prov"] = r["prov"] or (t.get("province") or "")
    else:
        for code, t in d.items():
            fac[code] = {"name": t.get("name", ""), "region": t.get("region", ""),
                         "prov": t.get("prov", ""), "city": t.get("city", "")}
    return fac


def nominatim(q):
    url = BASE + "?" + urllib.parse.urlencode({
        "q": q, "format": "jsonv2", "countrycodes": "ph", "addressdetails": "1", "limit": "1"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(5 * (attempt + 1)); continue
            return []
        except Exception:
            time.sleep(3); continue
    return []


def classify(res, declared_prov):
    """-> dict of result fields + a confidence tier. high = a health-facility hit in the right
    province; med = a hit but province unconfirmed / non-facility class; low = geocoded to a
    town/admin area (centroid-ish), out of PH bounds, or no result at all."""
    o = {"lat": "", "lon": "", "osm_class": "", "osm_type": "", "importance": "",
         "matched_name": "", "ret_prov": "", "prov_match": "N", "confidence": "low", "flag": ""}
    if not res:
        o["flag"] = "no-result"; return o
    r = res[0]
    lat, lon = float(r["lat"]), float(r["lon"])
    cls = r.get("category") or r.get("class") or ""   # jsonv2 uses `category`
    typ = r.get("type", "")
    HEALTH_TYPES = ("hospital", "clinic", "doctors", "pharmacy", "health_post",
                    "dentist", "nursing_home", "healthcare")
    addr = r.get("address", {}) or {}
    retprov = (addr.get("province") or addr.get("state") or addr.get("county")
               or addr.get("region") or "")
    disp = r.get("display_name", "")
    inb = (4.5 <= lat <= 21.5 and 116.0 <= lon <= 127.0)
    pm = "Y" if (norm(declared_prov) and norm(declared_prov) in norm(retprov + " " + disp)) else "N"
    o.update(lat=round(lat, 6), lon=round(lon, 6), osm_class=cls, osm_type=typ,
             importance=r.get("importance", ""), matched_name=disp[:120], ret_prov=retprov,
             prov_match=pm)
    is_facility = (cls in ("amenity", "healthcare", "building", "office")
                   or typ in HEALTH_TYPES)
    if not inb:
        o["confidence"] = "low"; o["flag"] = "out-of-ph-bounds"
    elif cls in ("place", "boundary") or typ in ("administrative", "city", "town",
                                                  "municipality", "village"):
        o["confidence"] = "low"; o["flag"] = "geocoded-to-place-not-facility"
    elif is_facility and pm == "Y":
        o["confidence"] = "high"
    elif is_facility:
        o["confidence"] = "med"; o["flag"] = "province-mismatch"
    else:
        o["confidence"] = "med"; o["flag"] = "non-facility-match"
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="cap rows this run (0 = all)")
    ap.add_argument("--sleep", type=float, default=1.1, help="seconds between requests (>=1 per policy)")
    a = ap.parse_args()

    fac = load_facilities(a.targets)
    done = set()
    if os.path.exists(a.out):
        with open(a.out, encoding="utf-8", newline="") as f:
            done = {row["code9"] for row in csv.DictReader(f)}
    todo = [(c, m) for c, m in sorted(fac.items()) if c not in done]
    if a.limit:
        todo = todo[:a.limit]
    print("masterlist=%d already=%d todo=%d" % (len(fac), len(done), len(todo)), flush=True)

    new = not os.path.exists(a.out)
    with open(a.out, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        tally = {"high": 0, "med": 0, "low": 0}
        for i, (code9, m) in enumerate(todo, 1):
            # name + province beats name+city+province: adding city over-constrains Nominatim's
            # free-text match (drops valid hits). City is still captured in the masterlist and is
            # used for MUNICIPALITY-centroid placeholders in the map (tighter than province).
            q = ", ".join(x for x in [m["name"], m["prov"], "Philippines"] if x)
            o = classify(nominatim(q), m["prov"])
            row = {"code9": code9, "name": m["name"], "declared_region": m["region"],
                   "declared_prov": m["prov"], "query": q}
            row.update(o)
            w.writerow(row); f.flush()
            tally[o["confidence"]] += 1
            if i % 25 == 0 or i == len(todo):
                print("  %d/%d  high=%d med=%d low=%d" % (i, len(todo), tally["high"],
                      tally["med"], tally["low"]), flush=True)
            time.sleep(a.sleep)
    print("DONE this run: high=%d med=%d low=%d" % (tally["high"], tally["med"], tally["low"]),
          flush=True)


if __name__ == "__main__":
    main()
