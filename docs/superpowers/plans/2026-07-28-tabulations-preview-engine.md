# Tabulations Deepened Preview Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Git is Carl's to handle** — do NOT auto-commit; the real checkpoint for these on-box generators is the deploy (scp + md5 + on-box run + read-back verify), which is independent of git.

**Goal:** Rework `csweb-tabulations-gen.py` into a hybrid preview engine that auto-generates ~118 plan-tied unweighted pretest preview tables (labeled, with committed breakdowns), plus hand-built multi-response tallies and F2 previews, and emits a tidy JSON + manifest that wire previews to committed table numbers for the Phase-2 page.

**Architecture:** One engine, two lanes (plan-driven auto + curated add-ons), three outputs (per-instrument `.xlsx`, tidy `tabulations-preview.json`, manifest + public catalog). Value labels come from the CSPro `.dcf` codebooks the SPSS gen already parses. Everything is pretest-only, unweighted, and stamped; the official weighted lane is untouched.

**Tech Stack:** Python 3 (`/opt/venvs/spss`), pandas, openpyxl, stdlib only. On-box hourly cron (`7 * * * *`, flock `/tmp/csweb-tabulations.lock`). Deploy key `~/.ssh/aspsi-csweb` → `root@207.148.65.115`.

## Global Constraints

- **Unweighted, pretest phase only** (`phase == "pretest"`); every sheet + the tidy JSON carry the bold unweighted / small-sample stamp. Show every previewable table even at small n.
- **Official weighted tables excluded** — no preview claims a committed weighted number; the Stata lane is untouched.
- **Catastrophic expenditure = `deferred`** (status-only): F3 OOP/capacity vars are fragmented + the definition is a documented alignment issue (`deliverables/tabulation-plan/CTP-catastrophic-expenditure-alignment-2026-07-06.md`). Never fake it.
- **No new on-box deps** — stdlib + pandas + openpyxl only. Runs in `/opt/venvs/spss`.
- **Atomic writes** (tempfile + `os.replace`); any missing input → `sys.exit(nonzero)`, previous outputs stay.
- **Data-room outputs are gated** behind the existing `/docs/data/.htaccess` (401); never overwrite RA-owned files — only the tabulations outputs + the gen change.
- **Labels** from `/opt/spss-meta` DCFs (reuse the SPSS gen's parser); **province breakdown** = `province_name`; **F1 facility-type** = `q7_ownership` (fallback `q8_service_level`) proxy, explicitly noted; **multi-code split width** read from the field's value-set codes (fallback 2).
- **Off-box runnable** via `--data-dir/--meta-dir/--out-dir/--public-out` so verification never needs MySQL.
- Plan `no` (e.g. `1.7`) is the join key between previews and the catalog throughout.

---

## File Structure

- **Modify/rework:** `deliverables/CSWeb/csweb-tabulations-gen.py` — orchestration + CLI args + packaging.
- **Create:** `deliverables/CSWeb/tabulation_lib.py` — pure, testable helpers: plan classification, DCF label loading (thin reuse of the SPSS gen's parser), breakdown resolution, Lane-1 tabulate, Lane-2 multi-tally, F2 explode. No I/O of final artifacts here.
- **Create:** `deliverables/CSWeb/tests/test_tabulation_lib.py` — unit tests on synthetic frames (no box, no fixtures).
- **Fixtures (ephemeral, job tmp):** pulled `f{1,3,4,2}_responses.csv`, the 3 `.dcf`, `f2-item-labels.json`, `tabulation-plan.csv` — for the end-to-end run only; never committed.

Verification tooling: `python -m pytest` for unit tests (pandas/openpyxl already present); `openpyxl` + `json` read-back for the end-to-end + on-box checks.

---

### Task 1: Shared lib scaffold + off-box fixture pull + plan classifier

**Files:**
- Create: `deliverables/CSWeb/tabulation_lib.py`
- Create: `deliverables/CSWeb/tests/test_tabulation_lib.py`
- Fixture pull into `$JOBTMP/tabfix/` (ephemeral)

**Interfaces:**
- Produces: `classify_rows(plan_rows, headers_by_inst) -> list[dict]` where each dict is
  `{"no","annex","inst","description","breakdown","source_var","klass","col"}` and
  `klass ∈ {"previewable","multi","partial","gap","f2"}`; `col` = resolved lowercase CSV column or `None`.
- Produces helpers: `first_var(source_variables:str) -> str` (first token before `(`/space, lowercased);
  `is_multi(source_variables:str) -> bool` (contains "checkbox" or "multi").

- [ ] **Step 1: Pull the fixture set once (ephemeral, for the end-to-end task later)**

```bash
KEY=~/.ssh/aspsi-csweb; H=root@207.148.65.115; F="$CLAUDE_JOB_DIR/tmp/tabfix"
mkdir -p "$F"
D=/opt/app/lamp/www/docs/data
scp -i $KEY $H:$D/f1_responses.csv $H:$D/f3_responses.csv $H:$D/f4_responses.csv $H:$D/f2_responses.csv "$F/"
scp -i $KEY $H:/opt/spss-meta/FacilityHeadSurvey.dcf $H:/opt/spss-meta/PatientSurvey.dcf $H:/opt/spss-meta/HouseholdSurvey.dcf $H:/opt/spss-meta/f2-item-labels.json "$F/"
scp -i $KEY $H:/opt/tabulation-plan.csv "$F/"
```

- [ ] **Step 2: Write the failing test for the classifier**

```python
# tests/test_tabulation_lib.py
import tabulation_lib as t
def test_classify_counts_match_grounded_numbers():
    # headers loaded from the pulled fixtures (conftest or a fixture-dir env)
    import csv, os
    F = os.environ["TABFIX"]
    heads = {}
    for i in ("f1","f3","f4"):
        with open(os.path.join(F,f"{i}_responses.csv"), encoding="utf-8-sig") as fh:
            heads[i] = set(c.strip().lower() for c in next(csv.reader(fh)))
    plan = list(csv.DictReader(open(os.path.join(F,"tabulation-plan.csv"), encoding="utf-8-sig")))
    rows = t.classify_rows(plan, heads)
    prev = [r for r in rows if r["klass"]=="previewable"]
    by = {i: sum(1 for r in prev if r["inst"]==i) for i in ("f1","f3","f4")}
    assert by == {"f1":20,"f3":70,"f4":28}, by
    assert sum(1 for r in rows if r["klass"]=="f2") == 20
```

- [ ] **Step 3: Run it, expect FAIL** — `TABFIX=$CLAUDE_JOB_DIR/tmp/tabfix python -m pytest deliverables/CSWeb/tests/test_tabulation_lib.py::test_classify_counts_match_grounded_numbers -v` → fails (module/func missing).

- [ ] **Step 4: Implement `first_var`, `is_multi`, `classify_rows` in `tabulation_lib.py`**

```python
import re
def first_var(sv):
    s = (sv or "").split("(")[0]
    m = re.match(r"\s*([A-Za-z0-9_]+)", s)
    return m.group(1).lower() if m else ""
def is_multi(sv):
    s = (sv or "").lower()
    return "checkbox" in s or "multi" in s
def classify_rows(plan, headers_by_inst):
    out = []
    for r in plan:
        inst = r["instrument"].strip().lower()
        sv, ms = r["source_variables"].strip(), r["mapping_status"].strip().lower()
        col = first_var(sv)
        if inst == "f2":
            klass = "f2"; col = None
        elif is_multi(sv):
            klass = "multi"
        elif ms == "gap" or not col:
            klass = "gap"
        elif ms == "partial":
            klass = "partial"
        elif ms == "mapped" and col in headers_by_inst.get(inst, set()):
            klass = "previewable"
        else:
            klass = "partial"
        out.append({"no": r["no"], "annex": r["annex"], "inst": inst,
                    "description": r["description"], "breakdown": r["breakdown"].strip().lower(),
                    "source_var": sv, "klass": klass,
                    "col": col if klass in ("previewable",) else None})
    return out
```

- [ ] **Step 5: Run test, expect PASS.** If F1/F3/F4 counts differ from 20/70/28, reconcile the classifier against the grounded numbers (do NOT change the assert to match a bug).

- [ ] **Step 6: Deploy checkpoint** — none yet (pure lib). Leave changes in the tree.

---

### Task 2: DCF value-label loader (reuse SPSS gen parser)

**Files:**
- Modify: `deliverables/CSWeb/tabulation_lib.py`
- Modify: `deliverables/CSWeb/tests/test_tabulation_lib.py`
- Reference: `deliverables/CSWeb/csweb-spss-gen.py` (its `.dcf` JSON parse → item/value labels)

**Interfaces:**
- Produces: `load_value_labels(meta_dir) -> {inst: {col_lower: {code_str: label}}}` and
  `load_var_labels(meta_dir) -> {inst: {col_lower: item_label}}`. Codes kept as strings (raw stored form).
- Consumes: the three `.dcf` files staged in `meta_dir`.

- [ ] **Step 1: Read how `csweb-spss-gen.py` parses the DCF** (JSON, CSPro 8.0 — its `prep_frame`/itemmap + value-label build). Prefer importing that parse function; if it's entangled with pyreadstat output, copy the minimal JSON-walk into `tabulation_lib.py`.

- [ ] **Step 2: Write the failing test** (value label for a known field)

```python
def test_value_labels_sex():
    import os
    vl = t.load_value_labels(os.environ["TABFIX"])
    # F1 q4_sex value set → e.g. {"1":"Male","2":"Female"} (confirm exact labels from the dcf)
    sex = vl["f1"].get("q4_sex", {})
    assert sex and set(sex.keys()) >= {"1","2"}
```

- [ ] **Step 3: Run, expect FAIL.**

- [ ] **Step 4: Implement `load_value_labels` / `load_var_labels`** walking each `.dcf` JSON: for every dictionary Item, key by `item.name.lower()`; for its ValueSet, map each value's `value`→`label`. Handle items with no value set (returns `{}`). Lowercase item names to match CSV columns.

- [ ] **Step 5: Run test, expect PASS** (adjust the expected labels to the dcf's actual text).

- [ ] **Step 6: Checkpoint** — pure lib, no deploy.

---

### Task 3: Lane-1 tabulate (frequency × committed breakdown, labeled)

**Files:**
- Modify: `deliverables/CSWeb/tabulation_lib.py`
- Modify: `deliverables/CSWeb/tests/test_tabulation_lib.py`

**Interfaces:**
- Produces: `resolve_breakdown(inst, breakdown_text, headers) -> (col_or_None, note_or_None)`
  (province→`province_name`; F1 "by facility type"→`q7_ownership` fallback `q8_service_level` with note `"proxy — true facility-type split applied in the weighted lane"`; else `(None,None)`).
- Produces: `tabulate(df, col, value_labels_for_col, breakdown_col=None, breakdown_labels=None) -> list[row]`
  where each row = `{"category","group","n","pct"}` (`group` = breakdown category label or `""`; `pct` = % within group; `category` label-applied, raw code fallback; `(no answer)` for blank/NaN).

- [ ] **Step 1: Failing test — total-only and grouped**

```python
import pandas as pd
def test_tabulate_total_and_grouped():
    df = pd.DataFrame({"q4_sex":["1","1","2",""],
                       "province_name":["Laguna","Laguna","Cavite","Laguna"]})
    lbl = {"1":"Male","2":"Female"}
    tot = t.tabulate(df, "q4_sex", lbl)
    d = {r["category"]: r["n"] for r in tot}
    assert d["Male"]==2 and d["Female"]==1 and d["(no answer)"]==1
    grp = t.tabulate(df, "q4_sex", lbl, breakdown_col="province_name")
    lag_male = [r for r in grp if r["group"]=="Laguna" and r["category"]=="Male"][0]
    assert lag_male["n"]==2 and round(lag_male["pct"],1)==66.7  # 2 of 3 Laguna
```

- [ ] **Step 2: Run, expect FAIL.**

- [ ] **Step 3: Implement `resolve_breakdown` + `tabulate`** (pandas value_counts within group; blank/NaN → `(no answer)`; apply value labels; round pct to 1).

- [ ] **Step 4: Run test, expect PASS.**

- [ ] **Step 5: Checkpoint** — pure lib.

---

### Task 4: Lane-2 multi-response tally

**Files:**
- Modify: `deliverables/CSWeb/tabulation_lib.py`
- Modify: `deliverables/CSWeb/tests/test_tabulation_lib.py`

**Interfaces:**
- Produces: `code_width(value_labels_for_col) -> int` (max code length in the value set; fallback 2).
- Produces: `multi_tally(df, col, value_labels_for_col) -> list[row]` where row =
  `{"category","n","pct_resp"}`; splits each nonblank cell into fixed-width chunks, drops `""`/all-zero chunks, counts respondents per option, `pct_resp` = % of respondents (n_resp = rows with ≥1 code); appends a `"(respondents)"` meta row carrying n_resp.

- [ ] **Step 1: Failing test**

```python
def test_multi_tally_fixedwidth():
    df = pd.DataFrame({"q149_lgu_support_forms":["01020304","01030499","",""]})
    lbl = {"01":"Funds","02":"Staff","03":"Supplies","04":"Training","99":"Other"}
    rows = t.multi_tally(df, "q149_lgu_support_forms", lbl)
    d = {r["category"]: r["n"] for r in rows if "category" in r}
    assert d["Funds"]==2 and d["Supplies"]==2 and d["Training"]==1 and d["Other"]==1
    # 2 respondents answered; Funds in both → 100%
    funds = [r for r in rows if r.get("category")=="Funds"][0]
    assert round(funds["pct_resp"],0)==100
```

- [ ] **Step 2: Run, expect FAIL.**

- [ ] **Step 3: Implement `code_width` + `multi_tally`** (width from value-set code lengths, fallback 2; chunk `[i:i+w]`; skip `""` and `"0"*w`; label via value set, raw-code fallback).

- [ ] **Step 4: Run test, expect PASS.**

- [ ] **Step 5: Checkpoint** — pure lib.

---

### Task 5: F2 explode + curated F2 previews

**Files:**
- Modify: `deliverables/CSWeb/tabulation_lib.py`
- Modify: `deliverables/CSWeb/tests/test_tabulation_lib.py`
- Reference: `csweb-spss-gen.py::prep_f2`, `f2-item-labels.json`

**Interfaces:**
- Produces: `explode_f2(df, f2_labels) -> (wide_df, {item_id: item_label})` — one column per item id from `values_json`, multi-selects joined "; " (mirror the SPSS gen exactly).
- Produces: `F2_PREVIEWS = [(item_id, plan_no, title), ...]` curated marquee list (sex, staffing gap, satisfaction, attrition intent — map to Annex-4 `no`s from the plan).

- [ ] **Step 1: Failing test** — one synthetic F2 row with a `values_json` explodes + tabulates.

```python
def test_explode_f2_basic():
    import json
    df = pd.DataFrame({"values_json":[json.dumps({"q3_sex":"2"}), json.dumps({"q3_sex":"1"})]})
    f2lab = {"q3_sex":{"label":"Sex","values":{"1":"Male","2":"Female"}}}  # shape per actual file
    wide, labels = t.explode_f2(df, f2lab)
    assert "q3_sex" in wide.columns and len(wide)==2
```

- [ ] **Step 2: Run, expect FAIL.**

- [ ] **Step 3: Implement `explode_f2`** copying the SPSS gen's `values_json` handling; confirm `f2-item-labels.json` shape from the pulled fixture and match it. Define `F2_PREVIEWS` from the plan's Annex-4 rows.

- [ ] **Step 4: Run test, expect PASS.**

- [ ] **Step 5: Checkpoint** — pure lib.

---

### Task 6: Rework the generator — packaging (xlsx + tidy JSON + manifest + public catalog)

**Files:**
- Modify: `deliverables/CSWeb/csweb-tabulations-gen.py` (major rework; import `tabulation_lib`)

**Interfaces:**
- Consumes: everything in `tabulation_lib`.
- Produces on disk: `tabulations/UHC-Y2-Tabulations-<INST>-preview.xlsx` (TOC + sheet per previewed table, sheet id `T<no>`), `tabulations-preview.json` (flat rows: `{table_no,instrument,annex,title,breakdown,note,category,group,n,pct,status}`), `tabulations-manifest.json` (adds per-table `status` + preview→`table_no` map + file list), public `tabulations.json` (adds per-annex preview counts + `preview_table_nos[]`, counts only).

- [ ] **Step 1: Add CLI args** `--data-dir` (default `/opt/app/lamp/www/docs/data`), `--meta-dir` (default `/opt/spss-meta`), `--plan` (default `/opt/tabulation-plan.csv`), `--out-dir` (default `<data>/tabulations`), `--manifest`, `--preview-json`, `--public` (default `/opt/app/capi-www/projects/uhc-y2/tabulations.json`). Keep existing defaults when args absent.

- [ ] **Step 2: Wire the pipeline** — load plan + headers → `classify_rows`; load labels; per instrument load `<inst>_responses.csv` filtered to `phase==pretest`; for each row by `klass`: `previewable`→`tabulate`, `multi`→`multi_tally`, `f2` handled via `explode_f2`+curated list, `partial`/`gap`→status-only, catastrophic-exp `no`s→`deferred`. Accumulate tidy rows + per-table status.

- [ ] **Step 3: Build the workbooks** — TOC sheet (hyperlinks to `T<no>`), one sheet per previewed table titled `"Preview of Table <no> — <description>"` + `STAMP` + the crosstab (+ the proxy note when present; + the multiple-response note for tallies). Atomic `os.replace`, `chmod 644`.

- [ ] **Step 4: Write tidy `tabulations-preview.json`, `tabulations-manifest.json`, public `tabulations.json`** — atomic tempfile+replace; manifest `status` per §3 semantics (`preview|partial|gap|deferred`); public = counts + `preview_table_nos` only (no cell numbers).

- [ ] **Step 5: End-to-end local run on the pulled fixtures**

```bash
F="$CLAUDE_JOB_DIR/tmp/tabfix"; O="$CLAUDE_JOB_DIR/tmp/tabout"; mkdir -p "$O/tabulations"
/opt/venvs/spss/bin/python deliverables/CSWeb/csweb-tabulations-gen.py \
  --data-dir "$F" --meta-dir "$F" --plan "$F/tabulation-plan.csv" \
  --out-dir "$O/tabulations" --manifest "$O/tabulations-manifest.json" \
  --preview-json "$O/tabulations-preview.json" --public "$O/tabulations.json" || true
# (locally: use the system python with pandas+openpyxl if /opt venv isn't present)
```

- [ ] **Step 6: Read-back assertions** — a small script: open each xlsx with openpyxl (assert ≥1 previewed sheet, labels are words not bare codes, stamp present); load `tabulations-preview.json` (assert schema keys, ≥118 distinct `table_no` with status `preview`, catastrophic-exp `no`s status `deferred`); load public json (counts only, no cell values).

- [ ] **Step 7: Checkpoint** — local outputs verified; not yet deployed.

---

### Task 7: Deploy to box + on-box verify

**Files:** none (deploy of Task 1/6 artifacts)

- [ ] **Step 1: Diff-guard** — `scp` the live `/opt/csweb-tabulations-gen.py` down; confirm the deployed source == the worktree base minus this rework (no on-box divergence to clobber). If diverged, reconcile before proceeding.

- [ ] **Step 2: Backup + upload** — on box `cp -p /opt/csweb-tabulations-gen.py /opt/csweb-tabulations-gen.py.bak-<ts>`; `scp` the reworked gen + `tabulation_lib.py` (LF-normalized) to `/opt/`; **md5-verify** each worktree == prod.

- [ ] **Step 3: Run once under the flock lock**

```bash
ssh -i ~/.ssh/aspsi-csweb root@207.148.65.115 \
 'flock -w 90 /tmp/csweb-tabulations.lock bash -c "/opt/venvs/spss/bin/python /opt/csweb-tabulations-gen.py" 2>&1 | tail -5'
```

- [ ] **Step 4: On-box read-back** — assert the 3–4 workbooks + `tabulations-preview.json` + manifest + public `tabulations.json` refreshed (mtime), preview count ≥118, catastrophic-exp `deferred`; `curl` a data-room output **without** auth → 401 (gate intact), and the public `tabulations.json` reachable (counts only).

- [ ] **Step 5: Report** — summary of what deployed + the preview/status counts. Leave the tree for Carl to git. **Do NOT** commit/push.

---

## Self-Review

**1. Spec coverage:** Lane 1 (T1,T3) · Lane 2 multi (T4) · F2 (T5) · labels/codebook reuse (T2) · breakdowns incl. F1 proxy (T3) · three outputs + status semantics + preview→table_no map (T6) · honesty guards + atomic + deferred catastrophic-exp (Global + T6) · deploy/md5/401 (T7) · off-box runnability (T6 args). Phase-2 page is out of scope (separate spec) — covered by producing `tabulations-preview.json` in T6. ✔

**2. Placeholder scan:** each code step carries real code or a concrete command; expected label text in T2/T3 is flagged to confirm against the actual dcf (data-dependent, not a placeholder in logic). No TODO/TBD.

**3. Type consistency:** `classify_rows` dict keys (`no,inst,klass,col,breakdown`) are consumed unchanged in T6; `tabulate`→`{category,group,n,pct}`, `multi_tally`→`{category,n,pct_resp}`, tidy JSON keys fixed in T6; label loaders keyed by lowercase col throughout. Consistent.
