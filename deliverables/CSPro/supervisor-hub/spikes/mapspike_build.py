#!/usr/bin/env python3
"""mapspike_build.py — C7 throwaway probe: a minimal CSEntry app that shows a map.

One field; its postproc declares a Map, adds two markers (test EA points in Laguna),
and shows it. Validates the CSPro 8 Map API (Map/addMarker/show) compiles + renders on
the itel. NOT a shipped deliverable — a spike probe. Reuses the build_hub_apps emitters.

Run:  python mapspike_build.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # supervisor-hub/spikes
HUB = HERE.parent                               # supervisor-hub
sys.path.insert(0, str(HUB))                    # build_hub_apps
sys.path.insert(0, str(HUB.parent))             # deliverables/CSPro (cspro_helpers)

from cspro_helpers import numeric, record, build_dictionary, write_dcf  # noqa: E402
from build_hub_apps import build_fmf, build_qsf, build_ent, _pff, _mgf, _write  # noqa: E402

MAP_APC = """\
{ MapSpike — C7 on-device map feasibility probe (throwaway, do not ship).
  Validates the CSPro 8 Map API: declare a Map, add markers at captured-GPS-style
  coordinates, and show it (online base map by default; offline needs a base-map file). }

PROC GLOBAL

PROC MS_GO
postproc
  Map m;
  m.addMarker(14.5557, 121.0180);   { test point A — Metro Manila }
  m.addMarker(14.2840, 121.0680);   { test point B — Binan, Laguna }
  m.show();
"""


def build():
    id_items = [{
        "name": "MS_SESSION", "labels": [{"text": "Session"}],
        "contentType": "numeric", "start": 2, "length": 1, "zeroFill": True,
    }]
    rec = record("MS_REC", "Map spike record", "M",
                 [numeric("MS_GO", "Show map (enter 1)", length=1)])
    d = build_dictionary("MAPSPIKE_DICT", "MapSpike", records=[rec], id_items=id_items)
    write_dcf(d, HERE / "MapSpike.dcf")
    _write(HERE / "MapSpike.fmf",
           build_fmf(d, "MAPSPIKE_FF", r".\MapSpike.dcf", "MapSpike", [("Map", "MS_REC")]))
    _write(HERE / "MapSpike.ent.qsf", build_qsf(d, "MAPSPIKE_DICT"), bom=True)
    _write(HERE / "MapSpike.ent.apc", MAP_APC)
    _write(HERE / "MapSpike.ent.mgf", _mgf("MapSpike"))
    ent = build_ent("MAPSPIKE", "MapSpike", "MapSpike.dcf", "MapSpike.fmf",
                    "MapSpike.ent.qsf", "MapSpike.ent.apc", "MapSpike.ent.mgf")
    _write(HERE / "MapSpike.ent", json.dumps(ent, indent=2))
    _write(HERE / "MapSpike.pff", _pff("MapSpike.ent", "MapSpike.csdb"))
    print("MapSpike probe built in", HERE)


if __name__ == "__main__":
    build()
