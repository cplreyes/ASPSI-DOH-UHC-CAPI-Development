---
project: UHC Survey Year 2 — CAPI Development
artifact: Harmonization ETL Specification (E4-INT-001)
version: 0.1 (draft, 2026-06-02)
status: draft
owner: Carl Patrick L. Reyes (data programmer)
closes: #176 (ETL spec); wires #178 (codebook-driven harmonization); feeds #177 (Looker dashboard)
builds-on: deliverables/data-harmonization/codebook.md (v0.2)
---

# Harmonization ETL Specification

**Goal:** a repeatable, auditable pipeline that pulls the four instruments from their two live backends, applies the **codebook v0.2** recodes, and produces a single **analysis-ready store** — clean per-instrument tables, a cross-instrument join layer, and a thin BI-facing load for the Looker prototype (#177).

This spec is the **E (extract) + L (load) + operations** layer. The **T (transform)** is already fully specified in `codebook.md` §1–§13 (13 cross-instrument dimensions, recodes, missing-value sentinels, output formats); this document does not duplicate it — it wires it.

> **Hard dependency:** the codebook's §15 open items (PSGC vintage #15.F, facility master list #15.G, `QUESTIONNAIRE_NO ≡ facility_id` #15.H, F4 `Other` sex #15.A) **block a correct production run** — joins fail silently without them. The pipeline can be **built and dry-run on test data now**; production delivery waits on those ASPSI sign-offs.

---

## 1. Architecture overview

```
  ┌─ F1/F3/F4 (CSEntry tablets) ──sync(TLS)──► CSWeb (Elestio VPS, SG) ─┐
  │                                            MySQL `csweb` DB          │  EXTRACT
  └─ F2 (PWA) ─► CF Worker ─► Apps Script ─► Google Sheets + R2 ────────┘
                                   │ (scheduled R2 CSV break-out — already built)
                                   ▼
        ┌──────────────────────  ETL runner (Python)  ──────────────────────┐
        │  extract/  →  raw per-instrument frames                            │
        │  transform/ → apply codebook.md §1–§13 (recode_*, sentinels)       │  TRANSFORM
        │  qa/       →  data-quality gates (counts, ranges, join integrity)  │
        │  load/     →  write harmonized store + BI load                     │  LOAD
        └───────────────────────────────────────────────────────────────────┘
                                   ▼
   ANALYSIS STORE  deliverables/data-harmonization/out/<run_date>/
     ├─ f1_clean.{csv,dta}  f2_clean.{csv,dta}  f3_clean.{csv,dta}  f4_clean.{csv,dta}
     ├─ shared_dimensions.csv         (long: instrument × respondent × dimension)
     ├─ f4_roster_clean.{csv,dta}     (per-member; F4 is two-level)
     ├─ manifest.json                 (run lineage: sources, row counts, hashes, codebook ver)
     └─ qa_report.md                  (gate results; run FAILS on a hard-gate breach)
                                   ▼
   BI LOAD (for #177 Looker)  →  BigQuery dataset `uhc_y2` (or a Google Sheet mirror)
```

**Design principles:** deterministic + idempotent (same inputs → same outputs); the dcf/spec are the source of truth (codebook §16); **de-identified by default** (identifiers dropped per the Data Privacy Plan §2 minimization unless a run is explicitly flagged `--with-identifiers` for the field-ops linkage table); every run leaves a manifest for lineage.

---

## 2. Extract

One adapter per source backend. Each adapter's job: produce a raw per-instrument DataFrame keyed to the dcf/spec field names the codebook expects.

### 2.1 F1 / F3 / F4 — from CSWeb (Elestio)
Three viable mechanisms, in order of preference:

1. **CSExport (preferred, supported, dcf-aware).** Run CSPro's `CSExport.exe` (or `cstab`/the export PFF) against the synced CSWeb data with each instrument's `.dcf` → flat CSV/Stata. CSExport understands the dictionary (items, value sets, multi-occurrence roster), so flattening F4's two-level roster is handled natively rather than hand-parsing case JSON. Produces `f1_raw.csv`, `f3_raw.csv`, `f4_raw.csv` (+ `f4_roster_raw.csv`).
2. **CSWeb REST API.** `GET` the cases for each dictionary from the CSWeb server API; parse the CSPro-8 JSON case format using the dcf. Use when CSExport can't run in the runner environment.
3. **Direct MySQL read.** Query the CSWeb `csweb` MySQL DB cases table; each row is a case (JSON payload + key fields). Most fragile (couples to CSWeb's internal schema) — fallback only.

**⟨DECISION⟩** Pick the extract mechanism after inspecting the live Elestio box (which CSPro CLI tools are installed there; whether the runner runs *on* the VPS or pulls remotely). Recommend **CSExport on the VPS**, output to a staging dir the runner reads. Extract is **read-only** against CSWeb; never writes back.

**Incremental:** CSWeb is append-mostly (cases arrive via sync). Default to **full re-extract each run** (survey-scale data is small — thousands of cases, not millions); the transform is cheap and full-refresh removes incremental-state bugs. Revisit only if volume demands it.

### 2.2 F2 — from the PWA backend
1. **R2 CSV break-out (preferred — already built).** The F2 Admin "Data Settings" scheduled break-out writes `F2_Responses` to R2 as CSV on an interval (the feature shipped in the admin portal). Point the extract at the latest R2 object → `f2_raw.csv`. Zero new backend work; reuses an existing, audited path.
2. **Admin API.** `GET /admin/api/dashboards/data/responses` (paginated) with a `dash_data` service token → assemble the frame. Use if a fresh pull is needed between break-outs.
3. F2 stores answers as `values_json`; the extract explodes `values_json` into columns keyed by the F2 item ids (`Q3`, `Q5`, …) per `app/src/generated/items.ts`, and carries the provenance columns (`hcw_id`, `facility_id`, `submitted_at_server`, `spec_version`, `device_fingerprint`, `source`).

**F2 geography** is **not** collected from the respondent — it is **joined from the facility master list via `facility_id`** (codebook §1/§2). The extract must therefore also load the facility master list (§2.3).

### 2.3 Facility master list (shared dimension input)
Load the single canonical facility master list (codebook §2, open item #15.G) → used to populate F2 geography + `facility_type`/`facility_name` for all instruments. **⟨DECISION⟩** until ASPSI publishes it, the pipeline uses the F2 placeholder list and **emits a loud warning** in `qa_report.md` that geography is provisional.

---

## 3. Transform

Apply `codebook.md` §1–§13 exactly. The codebook §14 already gives the per-instrument `harmonize()` shape and the `recode_*` function list. Implementation notes for the runner:

- One module per dimension (`transform/recode_psgc.py`, `recode_sex.py`, …) mirroring codebook sections, each pure `(df, instrument) → df`. Keeps each recode independently testable against the codebook's stated rules.
- **Missing-value sentinels** (codebook §0.2): map CSPro `NOTAPPL`→`.a`, `REFUSED`→`.b`, DK→`.c`, blank→`.` at the end of the per-instrument pass. Clean output should have **zero** `.` (hard QA gate §4).
- **F4 two-level**: harmonize the respondent-level frame and the roster frame separately; the roster keeps `MEMBER_LINE_NO` + the household key so it joins back. Roster age/sex/relationship/disability recodes reuse the same dimension modules.
- **Column naming** (codebook §0.1): `<instrument>_<qid>` for instrument-specific; canonical short names (`region_code`, `sex`, `age_years`, …) for the 13 shared dimensions; every row carries `_source_instrument`.
- **Outputs** (codebook §0.3): `*_clean.csv` (labels, not codes) + `*_clean.dta` (Stata 14 w/ variable + value labels via `pyreadstat`) + `shared_dimensions.csv` (long).
- **Codebook open items** that are still `⟨DECISION⟩` (F4 `Other` sex §15.A; F2/F1/F3/F4 consent & language adds) are handled by **config flags with documented defaults** so a run never silently picks a contested encoding — e.g. `SEX_OTHER_POLICY = 'dotc' | 'code3' | 'flag'`, defaulting to the codebook's conservative `.c` until §15.A is decided, and logged in the manifest.

---

## 4. Data-quality gates

Run after transform; results → `qa_report.md`; a **hard-gate** breach **fails the run** (non-zero exit, no store written) so bad data never reaches analysis/BI.

| Gate | Type | Rule (from codebook) |
|---|---|---|
| Row counts vs source | hard | harmonized row count == extracted case count per instrument (no silent drops) |
| No truly-missing | hard | zero `.` sentinels in clean output (all missing classified `.a/.b/.c`) |
| Join integrity | hard | every `facility_id` in F2/F3/F4 resolves in the facility master list (codebook §2 "silent join failure" guard) |
| Age sanity | soft | F1 age ∈ 18–90; F4 roster ≤ 120 (codebook §4) — flag rows, don't fail |
| PSGC width | hard | all geo codes are the canonical zero-padded width (codebook §1) |
| Consent present | hard | every retained CAPI row has `consent_given = 1` (codebook §9; refusals shouldn't reach the store) |
| Sex domain | hard | harmonized `sex` ∈ {1,2,.c} only — no raw `'Male'`/strings leaked (codebook §3) |
| Codebook drift | soft | warn if a source field referenced by a recode is missing/renamed in the dcf (catches instrument-spec changes) |

---

## 5. Load — the analysis store

**Primary (analyst) store:** the harmonized files in `out/<run_date>/` (§1). This is the canonical deliverable for Stata/R/Python analysis — versioned by run date, immutable once written.

**BI load for #177 (Looker Studio):** Looker connects cleanly to **BigQuery** or a **Google Sheet**.
- **⟨DECISION⟩ Recommend BigQuery** dataset `uhc_y2` (tables `f1`, `f2`, `f3`, `f4`, `f4_roster`, `shared_dimensions`): handles row volume + typed columns + a stable Looker connector, and keeps BI separate from the analyst `.dta` store. The load step truncates+writes each table from the harmonized CSVs.
- **Lighter alternative:** mirror the clean CSVs into a Google Sheet per instrument (zero infra, but row-limited + untyped). Fine for an early prototype; outgrow it quickly.
- The BI load receives the **de-identified** harmonized data only (no names/contact/precise GPS — Data Privacy Plan §3.3). Looker users never see identifiers.

---

## 6. Orchestration & scheduling

- **Runner:** a single Python package `deliverables/data-harmonization/etl/` (`extract/`, `transform/`, `qa/`, `load/`, `run.py`). `python -m etl.run --date YYYY-MM-DD [--with-identifiers] [--no-bi-load]`.
- **Where it runs — ⟨DECISION⟩:** recommend **on the Elestio CSWeb VPS** (the memory notes it's the "nightly sync + monitoring hub"), so extract is local to CSWeb and the run can chain after the nightly sync. Alternative: a scheduled GitHub Action / local cron that pulls remotely.
- **Schedule:** **nightly, after** the CSWeb sync window closes (so a run sees a consistent day's cases). Align with the existing nightly-sync cadence. Manual `--date` re-runs for ad-hoc refreshes.
- **Idempotent:** a given `--date` always overwrites that date's `out/` dir deterministically; safe to re-run.

---

## 7. Lineage, security, retention

- **Manifest** (`manifest.json` per run): source endpoints + extraction timestamps, per-instrument row counts in/out, codebook version, config-flag values (e.g. `SEX_OTHER_POLICY`), input file SHА-256s, runner git SHA. Full reproducibility + audit.
- **Security** (ties to `deliverables/security/Data-Privacy-and-Security-Plan.md`): the store holds sensitive PII → encrypted-at-rest volume; access least-privilege (Data Manager/Admin only); **de-identified by default** (§3 minimization — identifiers only in a separately-scoped, shorter-lived linkage table written only under `--with-identifiers`); the BI load is de-identified. Every export is audited (Privacy Plan §5).
- **Retention:** harmonized identifiable outputs follow the Privacy Plan §8 retention; de-identified analysis store per the DOH research protocol.

---

## 8. Build plan (phased — est. matches #176 `1d` for the spec; implementation is larger)

1. **Scaffold** `etl/` package + `run.py` + config (codebook open-item flags) + manifest writer.
2. **Transform first, on fixtures** (TDD): port codebook §1–§13 into `transform/recode_*` modules; unit-test each against the codebook's stated rules using small synthetic frames. (Transform is fully specified now → buildable without live data.)
3. **QA gates** (§4) over the transformed fixtures.
4. **Extract adapters:** F2 from an R2 break-out CSV first (available now); F1/F3/F4 via CSExport once the Elestio box + a sample synced dataset are reachable.
5. **Load:** harmonized files; then the BigQuery (or Sheet) BI load behind `--no-bi-load`.
6. **Dry-run end-to-end** on test/pretest data; iterate.
7. **Production run** — gated on codebook §15 ASPSI sign-offs (#15.A/F/G/H) + the live facility master list.

---

## 9. Open decisions (need confirmation before production)
| # | Decision | Owner | Default if unspecified |
|---|---|---|---|
| ETL-1 | Extract mechanism for CAPI (CSExport vs API vs DB) | Carl (after inspecting Elestio) | CSExport on the VPS |
| ETL-2 | BI target: BigQuery vs Google Sheet | Carl/ASPSI | BigQuery `uhc_y2` |
| ETL-3 | Where the runner runs (VPS vs CI vs local) | Carl | on the Elestio VPS, post-sync |
| ETL-4 | `--with-identifiers` linkage-table lifecycle | Carl + ASPSI (ties to Privacy Plan §2/§8) | de-identified default; linkage table destroyed at project close |
| — | **Codebook §15 open items** (#15.A sex-Other, #15.F PSGC vintage, #15.G master list, #15.H QUESTIONNAIRE_NO≡facility_id) | **ASPSI** | **block production**; pipeline dry-runs on test data meanwhile |

---

## Issue coverage
- **#176** (ETL spec) — this document.
- **#178** (codebook-driven harmonization wired into ETL) — §3 + the `transform/recode_*` design that ports `codebook.md` §1–§13 verbatim; the codebook is the single transform source of truth.
- **#177** (Looker prototype) — §5 BI load defines the store Looker connects to; dashboard build is the follow-on once a dry-run store exists.
