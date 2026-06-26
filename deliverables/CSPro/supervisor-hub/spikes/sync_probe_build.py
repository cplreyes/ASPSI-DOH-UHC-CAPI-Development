#!/usr/bin/env python3
"""sync_probe_build.py — C2 throwaway probe: prove device-to-device Bluetooth case sync.

ONE app (SyncSpike), deployed to BOTH tablets. A single field SS_MODE drives the role:
  - MODE 7  -> the device is the HOST: runs syncserver(Bluetooth) and waits for a client.
  - MODE 9  -> the device is the CLIENT: syncconnect(Bluetooth) [picker] -> syncdata(PUT)
               -> syncdisconnect(); pushes this device's committed SyncSpike cases to the host.
  - MODE 1  -> payload no-op (just creates a case to later PUT).

Demo: on the Samsung (client) add cases key 001/002 (MODE 1) = payload; on the itel (host)
add case key 700 (MODE 7) -> server waits; on the Samsung add case key 009 (MODE 9) -> the two
committed payload cases PUT to the itel over Bluetooth. Then the itel's SyncSpike.csdb holds
001/002 (received) + 700 (its own) and the Samsung keeps 001/002/009 (non-destructive).

This validates the PROC sync API (syncserver/syncconnect/syncdata over Bluetooth) end-to-end.
NOT a shipped deliverable — a throwaway spike probe (mirrors mapspike_build.py). The same
syncdata call moves F3 PatientSurvey.csdb cases identically (also a CSPro DB).

Run:  python sync_probe_build.py
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

SYNC_APC = """\
{ SyncSpike — C2 Bluetooth peer-to-peer case-sync feasibility probe (throwaway, do not ship).
  Validates syncserver / syncconnect(Bluetooth) / syncdata(PUT) move PRIMARY case data
  device-to-device with no internet. The field SS_MODE selects the role at run time. }

PROC GLOBAL

PROC SS_MODE
postproc
  if SS_MODE = 7 then
    errmsg("HOST: starting Bluetooth server. Keep this screen open; now run MODE 9 on the client.");
    syncserver(Bluetooth);
    errmsg("HOST: syncserver finished — a client connected and synced.");
  endif;
  if SS_MODE = 9 then
    if syncconnect(Bluetooth) then
      syncdata(PUT, PATIENTSURVEY_DICT);
      syncdisconnect();
      errmsg("CLIENT: connected + syncdata(PUT) done — F3 cases pushed to the host.");
    else
      errmsg("CLIENT: Bluetooth connect FAILED (no host / not paired / server not running).");
    endif;
  endif;
"""

# syncdata requires an EXTERNAL dictionary backed by a CSPro DB (strict-compiler:
# "external dictionary name expected"). We declare the real F3 PATIENTSURVEY_DICT as
# external (data source = a copy of PatientSurvey.csdb) and sync THAT — so the probe
# moves the actual F3 case, no seeding. (Corrects the probe's first-pass main-dict use.)


def build():
    id_items = [{
        "name": "SS_KEY", "labels": [{"text": "Case key"}],
        "contentType": "numeric", "start": 2, "length": 3, "zeroFill": True,
    }]
    rec = record("SS_REC", "Sync spike record", "S",
                 [numeric("SS_MODE", "Mode: 1=payload  7=HOST(server)  9=CLIENT(connect+PUT)", length=1)])
    d = build_dictionary("SYNCSPIKE_DICT", "SyncSpike", records=[rec], id_items=id_items)
    write_dcf(d, HERE / "SyncSpike.dcf")
    _write(HERE / "SyncSpike.fmf",
           build_fmf(d, "SYNCSPIKE_FF", r".\SyncSpike.dcf", "SyncSpike", [("Sync", "SS_REC")]))
    _write(HERE / "SyncSpike.ent.qsf", build_qsf(d, "SYNCSPIKE_DICT"), bom=True)
    _write(HERE / "SyncSpike.ent.apc", SYNC_APC)
    _write(HERE / "SyncSpike.ent.mgf", _mgf("SyncSpike"))
    # bring the real F3 dictionary in as an external dict for syncdata to push
    import shutil
    f3_dcf = HUB.parent / "F3" / "PatientSurvey.dcf"
    shutil.copy(f3_dcf, HERE / "PatientSurvey.dcf")
    ent = build_ent("SYNCSPIKE", "SyncSpike", "SyncSpike.dcf", "SyncSpike.fmf",
                    "SyncSpike.ent.qsf", "SyncSpike.ent.apc", "SyncSpike.ent.mgf",
                    externals=["PatientSurvey.dcf"])
    _write(HERE / "SyncSpike.ent", json.dumps(ent, indent=2))
    _write(HERE / "SyncSpike.pff", _pff("SyncSpike.ent", "SyncSpike.csdb",
                                        externals={"PATIENTSURVEY_DICT": "PatientSurvey.csdb"}))
    print("SyncSpike probe built in", HERE, "(external PATIENTSURVEY_DICT)")


if __name__ == "__main__":
    build()
