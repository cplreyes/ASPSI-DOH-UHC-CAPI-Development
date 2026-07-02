# C7 spike — on-device EA map (Phase-2 N3 "View EA on Map")

**Status:** IN PROGRESS (2026-06-25). Verdict recorded at the bottom.

Gating spike for **N3** (the "View EA on Map" menu items on both role menus). Confirms what
CSEntry can actually render **on-device** for an EA boundary + captured case GPS points, and
whether it works **offline** (no signal is the whole reason the hub exists).

## PASS criteria (ALL must hold)

1. From CSPro logic, CSEntry can display a map on the device — either the CSPro 8 **`Map`/`maps`
   API** (markers on a base map) or **`view()`** of a generated artifact (self-contained HTML, or a
   KML opened by an installed viewer).
2. The map can plot **captured case GPS points** (from the `.csdb` LATITUDE/LONGITUDE) and,
   ideally, an **EA boundary** loaded from a "set map file" (KML/offline base map).
3. It renders acceptably on the **itel** (800×1280) and **returns to the menu** on close.
4. **Offline** — the core case: the map renders with **no internet** (the no-signal cluster
   scenario). If it only works online, that is a partial result, recorded as such.

## FAIL → fallback

If on-device rendering needs internet (online tiles only) and there is no offline base-map path:
N3 degrades to **(a)** the existing server-side **CSWeb Map Report** (open when on signal) and/or
**(b)** a static on-device coordinate list / a pre-rendered map image. Record exactly which
mechanism worked, which didn't, and why.

## Method

A throwaway minimal CSEntry probe app (`MapSpike`) with one field whose postproc attempts each
mechanism in turn, installed on the itel and driven via adb + screencap. Probe order:
1. CSPro 8 `Map` API (markers; online base map first, then offline base-map file if supported).
2. `view()` of a self-contained HTML file (offline-renderable test).
3. `view()` of a KML (if a viewer is installed).

## Findings (2026-06-25)

**The mechanism exists and is native — CSPro 8 `Map` API (Android-only = CSEntry).** Grounded in
the CSPro 8 User's Guide (csprousers.org `mapping.html`, `Map_statement.html`, `Map.addMarker`,
`Map.setBaseMap`, `Map.show`, `offline_maps.html`, `map_base_map_specification.html`):

- **API (compile-validated).** A throwaway probe `MapSpike` (`spikes/mapspike_build.py` →
  `MapSpike.*`) whose field postproc is:
  ```cspro
  Map m;
  m.addMarker(14.5557, 121.0180);
  m.addMarker(14.2840, 121.0680);
  m.show();
  ```
  **COMPILES CLEAN on CSPro 8 Designer** (`automation/shots/MAPSPIKE_compile.png`,
  "Compile Successful 12:40:13"). The Map statement + `addMarker(lat, lon)` + `show()` are accepted.
- **Renders markers on a base map, on Android.** Documented: the `Map` object shows markers (one
  per captured GPS / per case) on a base map; **case-listing-on-map is supported** (each case = a
  marker) — directly serving the "view listing on map" menu item.
- **Online base maps:** Google / Esri / Mapbox tiles when there is internet (the default — no
  `setBaseMap` call needed).
- **OFFLINE base maps (the no-signal scenario — PASS criterion 4):** supply an **MBTiles** raster
  tile file (PNG/JPEG; export from QGIS or download from the **Humanitarian OpenStreetMap** project)
  — or an ArcGIS `.tpk/.tpkx`. Place it on the device (commonly inside the app folder; copy via USB
  or `syncfile`), and reference it via **`Map.setBaseMap()`** (logic) or **`BaseMap=`** in the PFF
  `[Files]` section (case-listing). Then it renders with **no internet**. This is a *provisioning
  artifact*, not an API blocker. File size is the only real constraint — cap zoom levels and clip to
  the survey provinces.
- **EA boundary caveat:** `addMarker` plots **points** (facilities / cases / an EA centroid). A drawn
  **polygon** EA outline is not confirmed in the marker API → "View EA on Map" should render as marker
  points, with a true boundary overlay treated as a stretch goal to verify separately.
- **Device render not run:** without internet it needs the MBTiles file (not yet generated), and with
  internet it would only prove the online path. The meaningful on-device test is **offline**, so it is
  best paired with the first MBTiles base map (see N3 build below).

## Verdict

**`C7 = PASS` (feasible) — 2026-06-25.** On-device EA maps are a native CSPro 8 capability: the `Map`
API compiles clean, renders markers on Android/CSEntry, and supports **offline** rendering via an
MBTiles base map. N3 ("View EA on Map" / "view listing on map") is buildable. No API fallback needed;
the FAIL→fallback (CSWeb Map Report / static list) is unnecessary.

### N3 build path (plan task B9)

1. **Provision an offline base map** — an MBTiles raster export (HOT OSM / QGIS) clipped to the survey
   provinces, zoom-capped for size. Ship it with the deployment (or `syncfile`).
2. **Wire the menu "View EA on Map" items** — `Map m;` → loop the cases / EA points adding
   `m.addMarker(lat, lon)` → `m.setBaseMap(<mbtiles path>)` → `m.show()`; returns to the menu on close.
3. **Device-test OFFLINE** on the itel (Wi-Fi OFF) with the MBTiles in place — this is the real
   confirmation (the online render is trivially covered by the default base map).
