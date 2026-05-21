"""gps_photo.py — auto-GPS + verification-photo capture block builder.

Emits the off-form capture record used by F1/F3/F4. The capture items are
wired via ``onfocus`` handlers in the .fmf/.apc (phase 4): ``CAPTURE_GPS``
calls ``ReadGPSReading()`` and ``CAPTURE_VERIFICATION_PHOTO`` calls
``TakeVerificationPhoto()`` from ``shared/Capture-Helpers.apc``.

The verification photo is stored as a filename reference (alpha item); CSEntry
syncs the JPG itself via its attachment mechanism — it is NOT a dictionary
binary item (that item class is flagged experimental in CSPro 8.0).
"""

from __future__ import annotations

from .cspro_helpers import alpha, numeric, record


def gps_fields(prefix=""):
    """Six GPS-metadata items + a capture-trigger button.

    ``prefix`` lets multiple GPS blocks coexist in one case
    (e.g. ``prefix="FACILITY_"`` -> ``FACILITY_GPS_LATITUDE`` ...).
    """
    capture_vs = [("Capture GPS now", "1")]
    return [
        alpha(  f"{prefix}GPS_LATITUDE",   "GPS Latitude",        length=12),
        alpha(  f"{prefix}GPS_LONGITUDE",  "GPS Longitude",       length=12),
        alpha(  f"{prefix}GPS_ALTITUDE",   "GPS Altitude (m)",    length=10),
        numeric(f"{prefix}GPS_ACCURACY",   "GPS Accuracy (m)",    length=3),
        numeric(f"{prefix}GPS_SATELLITES", "GPS Satellites",      length=2),
        alpha(  f"{prefix}GPS_READTIME",   "GPS Read Time (UTC)", length=19),
        numeric(f"{prefix}CAPTURE_GPS",    "Capture GPS",         length=1,
                value_set_options=capture_vs),
    ]


def photo_block(prefix=""):
    """Verification-photo filename item + a capture-trigger button."""
    capture_vs = [("Take verification photo", "1")]
    return [
        alpha(f"{prefix}VERIFICATION_PHOTO_FILENAME",
              "Verification Photo Filename", length=120),
        numeric(f"{prefix}CAPTURE_VERIFICATION_PHOTO",
                "Take Verification Photo", length=1,
                value_set_options=capture_vs),
    ]


def build_capture_record(name, label, record_type,
                         gps_prefix="", photo_prefix=""):
    """GPS + verification-photo capture record.

    Items are off-form (wired via ``onfocus`` in phase 4). ``record_type`` is
    conventionally "Z" so the capture record sorts last.
    """
    return record(name, label, record_type,
                   items=gps_fields(gps_prefix) + photo_block(photo_prefix))
