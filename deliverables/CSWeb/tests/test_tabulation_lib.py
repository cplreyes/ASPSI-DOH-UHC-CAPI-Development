# -*- coding: utf-8 -*-
"""Unit tests for tabulation_lib.

Synthetic-frame tests run anywhere. The classifier + label tests need the pulled
fixture set; point TABFIX at it, e.g.:

    TABFIX=$CLAUDE_JOB_DIR/tmp/tabfix python -m pytest deliverables/CSWeb/tests -v

Fixture-dependent tests skip cleanly when TABFIX is unset.
"""
import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import tabulation_lib as t   # noqa: E402

TABFIX = os.environ.get("TABFIX")
needs_fix = pytest.mark.skipif(not TABFIX, reason="set TABFIX to the pulled fixture dir")


# ---- classifier (fixture) ----

@needs_fix
def test_classify_counts_match_grounded_numbers():
    import csv
    heads = {i: t.read_headers(os.path.join(TABFIX, "%s_responses.csv" % i))
             for i in ("f1", "f3", "f4")}
    plan = list(csv.DictReader(open(os.path.join(TABFIX, "tabulation-plan.csv"),
                                    encoding="utf-8-sig")))
    rows = t.classify_rows(plan, heads)
    prev = [r for r in rows if r["klass"] == "previewable"]
    by = {i: sum(1 for r in prev if r["inst"] == i) for i in ("f1", "f3", "f4")}
    assert by == {"f1": 20, "f3": 70, "f4": 28}, by
    assert sum(1 for r in rows if r["klass"] == "f2") == 20
    # every previewable/multi row carries its resolved column
    assert all(r["col"] for r in rows if r["klass"] in ("previewable", "multi"))


def test_first_var_and_is_multi():
    assert t.first_var("Q149_LGU_SUPPORT_FORMS (checkbox multi)") == "q149_lgu_support_forms"
    assert t.first_var("") == ""
    assert t.is_multi("Q65_ACCRED_DIFFICULT (checkbox multi)") is True
    assert t.is_multi("Q51_YK_ACCRED") is False


# ---- value labels (fixture) ----

@needs_fix
def test_value_labels_present():
    vl = t.load_value_labels(TABFIX)
    assert "f1" in vl
    sex = vl["f1"].get("q4_sex", {})
    assert sex and set(sex.keys()) >= {"1", "2"}


# ---- tabulate (synthetic) ----

def test_tabulate_total_and_grouped():
    df = pd.DataFrame({"q4_sex": ["1", "1", "2", ""],
                       "province_name": ["Laguna", "Laguna", "Cavite", "Laguna"]})
    lbl = {"1": "Male", "2": "Female"}
    tot = t.tabulate(df, "q4_sex", lbl)
    d = {r["category"]: r["n"] for r in tot}
    assert d["Male"] == 2 and d["Female"] == 1 and d[t.NO_ANSWER] == 1
    grp = t.tabulate(df, "q4_sex", lbl, breakdown_col="province_name")
    lag_male = [r for r in grp if r["group"] == "Laguna" and r["category"] == "Male"][0]
    assert lag_male["n"] == 2 and round(lag_male["pct"], 1) == 66.7


def test_tabulate_missing_col():
    assert t.tabulate(pd.DataFrame({"a": [1]}), "nope") == []


# ---- multi tally (synthetic) ----

def test_multi_tally_fixedwidth():
    df = pd.DataFrame({"q149": ["01020304", "01030499", "", ""]})
    lbl = {"01": "Funds", "02": "Staff", "03": "Supplies", "04": "Training", "99": "Other"}
    rows = t.multi_tally(df, "q149", lbl)
    d = {r["category"]: r["n"] for r in rows if "category" in r}
    # row1 01·02·03·04, row2 01·03·04·99 -> 04(Training) is in both
    assert d["Funds"] == 2 and d["Staff"] == 1 and d["Supplies"] == 2
    assert d["Training"] == 2 and d["Other"] == 1
    funds = [r for r in rows if r.get("category") == "Funds"][0]
    assert round(funds["pct_resp"], 0) == 100
    meta = [r for r in rows if r.get("meta") == "respondents"][0]
    assert meta["n"] == 2


def test_code_width_infers_and_defaults():
    assert t.code_width({"01": "a", "12": "b"}) == 2
    assert t.code_width({}) == 2
    assert t.code_width({"1": "a", "2": "b"}) == 1


# ---- F2 explode (synthetic) ----

def test_explode_f2_basic():
    rows = [{"values_json": json.dumps({"Q5": "Nurse", "facility_id": "x"})},
            {"values_json": json.dumps({"Q5": "Doctor", "Q6": "Pediatrics"})}]
    f2lab = {"Q5": {"label": "Role", "type": "single"},
             "Q6": {"label": "Specialty", "type": "single"}}
    df, labels = t.explode_f2(rows, f2lab)
    assert "Q5" in df.columns and "facility_id" not in df.columns
    assert labels["Q5"] == "Role"
    tab = t.tabulate(df, "Q5")   # F2 answers are English text; no code map needed
    d = {r["category"]: r["n"] for r in tab}
    assert d["Nurse"] == 1 and d["Doctor"] == 1
