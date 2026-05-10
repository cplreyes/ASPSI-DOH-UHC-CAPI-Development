"""generate_dcf.py — emit sync_F1_app.dcf, the trivial input dict for the sync app.

The sync app's own primary dict only exists so the entry runtime has something
to "enter" (CSPro requires a primary dict). All useful work is in the .apc
preproc that fires syncdata(PUT, FACILITYHEADSURVEY_DICT) against the external
F1 dictionary declared in the .ent.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))

from cspro_helpers import numeric, record, build_dictionary, write_dcf


sync_rec = record(
    name="SYNC_REC", label="Sync Record", record_type="S",
    items=[
        numeric("SYNC_STATUS", "Sync Status", length=1),
    ],
)

dictionary = build_dictionary(
    dict_name="SYNC_DICT",
    dict_label="SyncDictionary",
    id_item_name="SYNC_APP_ID",
    id_item_label="Sync App ID",
    id_length=4,
    records=[sync_rec],
)

write_dcf(dictionary, HERE / "sync_F1_app.dcf")
