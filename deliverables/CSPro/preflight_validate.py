#!/usr/bin/env python
"""
CSPro pre-flight validator — static symbol-resolution check of a .ent.apc
against its .dcf dictionary + #included shared logic. Catches the compile-error
class (PROC for a non-existent item; references to undefined dictionary symbols)
BEFORE a Designer compile, so the GUI round-trip is clean on the first try.

Not a substitute for the real compile — it can't catch syntax errors, type
mismatches, or function-arity errors. It is high-signal on item-name drift,
which is the documented failure mode (spec used shortened names != dcf).

Run:  python deliverables/CSPro/preflight_validate.py
Exit 0 = every PROC target resolves (no hard compile errors); exit 1 otherwise.
Re-run after editing any generate_apc.py and regenerating the .apc.
"""
import json, re, sys
from pathlib import Path

# --- CSPro reserved words + built-in functions (uppercase-relevant subset).
# Lowercase keywords/functions are excluded by the UPPER_SNAKE reference filter,
# so this only needs tokens that could appear UPPER_SNAKE in logic. We add the
# common all-caps ones defensively.
CSPRO_RESERVED = {
    # section/proc keywords
    'PROC', 'GLOBAL', 'PREPROC', 'POSTPROC', 'ONFOCUS', 'ONOCCCHANGE', 'KILLFOCUS',
    # control flow / statements (usually lowercase, listed for safety)
    'IF', 'THEN', 'ELSE', 'ELSEIF', 'ENDIF', 'DO', 'WHILE', 'ENDDO', 'FOR', 'ENDFOR',
    'SKIP', 'TO', 'NEXT', 'ENDLEVEL', 'REENTER', 'NOINPUT', 'ADVANCE', 'AND', 'OR', 'NOT',
    # common constants / system tokens
    'YES', 'NO', 'TRUE', 'FALSE', 'NOTAPPL', 'DEFAULT', 'MAXOCC', 'CUROCC', 'TOTOCC',
}


def _collect_dcf_names(node, names):
    """Recursively collect every 'name' under items/subitems/valueSets/records."""
    if isinstance(node, dict):
        if 'name' in node and isinstance(node['name'], str):
            names.add(node['name'].upper())
        for k, v in node.items():
            _collect_dcf_names(v, names)
    elif isinstance(node, list):
        for x in node:
            _collect_dcf_names(x, names)


def dcf_symbols(dcf_path):
    d = json.load(open(dcf_path, encoding='utf-8-sig'))
    names = set()
    # dict name + level/record/item/valueset/value names (recursive catch-all)
    _collect_dcf_names(d, names)
    return names


def fmf_symbols(fmf_path):
    """Form/group/form-file names declared in the .fmf (every `Name=` line).
    These are valid PROC targets — logic can attach to a form GROUP (e.g. a roster
    group like C_HOUSEHOLD_ROSTER_FORM), not only to dcf items."""
    syms = set()
    if not fmf_path or not Path(fmf_path).exists():
        return syms
    for line in open(fmf_path, encoding='utf-8-sig'):
        m = re.match(r'\s*Name=(.+)', line.rstrip('\r\n'))
        if m:
            syms.add(m.group(1).strip().upper())
    return syms


def strip_comments(src):
    """Remove CSPro { ... } brace comments, // line comments, and string
    literals (so identifiers quoted in errmsg/maketext text don't false-flag)."""
    src = re.sub(r'\{[^{}]*\}', ' ', src)          # most braces (non-nested)
    src = re.sub(r'\{.*?\}', ' ', src, flags=re.S)  # any spanning leftovers
    src = re.sub(r'//[^\n]*', ' ', src)
    src = re.sub(r'"(?:[^"\\]|\\.)*"', ' ', src)     # double-quoted strings
    return src


def declared_symbols(src):
    """Symbols DECLARED in this logic file: var declarations, PROC names,
    function defs, valueset defs — all valid non-dcf references."""
    decl = set()
    # numeric/string/alpha/array declarations:  numeric FOO, BAR;  /  numeric FOO = 0;
    for m in re.finditer(r'(?im)^\s*(?:numeric|string|alpha(?:\(\d+\))?|array(?:\([^)]*\))?)\s+([A-Za-z0-9_,\s\(\)]+?)\s*(?:=|;)', src):
        for name in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', m.group(1)):
            decl.add(name.upper())
    # PROC <name>
    for m in re.finditer(r'(?im)^\s*PROC\s+([A-Za-z_][A-Za-z0-9_]*)', src):
        decl.add(m.group(1).upper())
    # function <name>(  /  def <name>(
    for m in re.finditer(r'(?im)\b(?:function|def)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', src):
        decl.add(m.group(1).upper())
    # valueset <name>
    for m in re.finditer(r'(?im)\bvalueset\s+([A-Za-z_][A-Za-z0-9_]*)', src):
        decl.add(m.group(1).upper())
    return decl


def declared_vars(src):
    """ONLY working-variable declarations (numeric/string/alpha/array NAME...;).
    A provably-non-field set, used by the setvalueset lint."""
    dv = set()
    for m in re.finditer(r'(?im)^\s*(?:numeric|string|alpha(?:\(\d+\))?|array(?:\([^)]*\))?)\s+([A-Za-z0-9_,\s\(\)]+?)\s*(?:=|;)', src):
        for name in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', m.group(1)):
            dv.add(name.upper())
    return dv


def _balanced_paren(s, open_idx):
    """s[open_idx] must be '('. Return (inner, idx_after_close) or (None, -1)."""
    depth = 0
    for j in range(open_idx, len(s)):
        if s[j] == '(':
            depth += 1
        elif s[j] == ')':
            depth -= 1
            if depth == 0:
                return s[open_idx + 1:j], j + 1
    return None, -1


def _split_top(inner):
    """Split a paren-balanced, string-stripped arg list on TOP-LEVEL commas."""
    parts, depth, cur = [], 0, ''
    for c in inner:
        if c == '(':
            depth += 1; cur += c
        elif c == ')':
            depth -= 1; cur += c
        elif c == ',' and depth == 0:
            parts.append(cur); cur = ''
        else:
            cur += c
    parts.append(cur)
    return parts


def _count_args(inner):
    return 0 if inner.strip() == '' else len(_split_top(inner))


FUNC_DEF_RE = re.compile(r'(?i)\bfunction\b\s+(?:(?:numeric|string|alpha(?:\(\d+\))?)\s+)?([A-Za-z_]\w*)\s*\(')


def function_arities(src):
    """Map user-FUNCTION name -> declared param count, plus the set of def '(' indices."""
    arities, def_idx = {}, set()
    for m in FUNC_DEF_RE.finditer(src):
        open_idx = m.end() - 1            # the '(' the regex ended on
        inner, _ = _balanced_paren(src, open_idx)
        if inner is None:
            continue
        arities[m.group(1).upper()] = _count_args(inner)
        def_idx.add(open_idx)
    return arities, def_idx


def arity_problems(apc, shared_srcs):
    """Call sites of USER functions whose arg count != the declared param count.
    Only checks functions we can SEE a definition for (built-ins are skipped),
    so false positives are near-zero. Catches the 'function expects N arguments'
    compile-error class."""
    arities, local_def_idx = function_arities(apc)
    for s in shared_srcs:
        sh_ar, _ = function_arities(s)
        for k, v in sh_ar.items():
            arities.setdefault(k, v)       # local def wins on name clash
    problems = []
    for name, want in arities.items():
        for m in re.finditer(r'(?i)\b' + re.escape(name) + r'\s*\(', apc):
            open_idx = m.end() - 1
            if open_idx in local_def_idx:  # skip the definition itself
                continue
            inner, _ = _balanced_paren(apc, open_idx)
            if inner is None:
                continue
            got = _count_args(inner)
            if got != want:
                line = apc[:m.start()].count('\n') + 1
                problems.append((name, line, got, want))
    return problems


def setvalueset_problems(apc, working_vars, dcf):
    """setvalueset(X, ...) where X is provably a working variable (declared
    numeric/string/array, not a dcf field). Catches 'setvalueset: argument is
    not a field' — the F1 Q121 trap."""
    problems = []
    for m in re.finditer(r'(?i)\bsetvalueset\s*\(', apc):
        inner, _ = _balanced_paren(apc, m.end() - 1)
        if inner is None:
            continue
        first = _split_top(inner)[0].strip()
        idm = re.match(r'([A-Za-z_]\w*)', first)
        if not idm:
            continue
        ident = idm.group(1).upper()
        if ident in working_vars and ident not in dcf:
            problems.append((idm.group(1), apc[:m.start()].count('\n') + 1))
    return problems


# Identifier that "looks like" a dictionary reference: UPPER_SNAKE with at least
# one underscore or a leading Q-number, length >= 3. Keeps false positives low.
REF_RE = re.compile(r'\b([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+|Q\d+[A-Z0-9_]*)\b')
PROC_RE = re.compile(r'(?im)^\s*PROC\s+([A-Za-z_][A-Za-z0-9_]*)')


def validate(instrument, apc_path, dcf_path, shared_paths, fmf_path=None, extra_dcf_paths=()):
    dcf = dcf_symbols(dcf_path)
    apc_raw = open(apc_path, encoding='utf-8-sig').read()
    apc = strip_comments(apc_raw)

    known = set(dcf) | set(CSPRO_RESERVED)
    known |= declared_symbols(apc)
    # External dictionaries attached to the .ent (e.g. the 4 PSGC lookup dicts): their
    # records/items are valid references in the inlined cascade logic.
    for ed in extra_dcf_paths:
        if Path(ed).exists():
            known |= dcf_symbols(ed)
    # Form/group names from the .fmf are valid PROC targets (a roster group proc, etc.).
    form_syms = fmf_symbols(fmf_path)
    known |= form_syms
    shared_srcs = []
    working_vars = declared_vars(apc)
    for sp in shared_paths:
        if Path(sp).exists():
            sh = strip_comments(open(sp, encoding='utf-8-sig').read())
            shared_srcs.append(sh)
            known |= declared_symbols(sh)
            working_vars |= declared_vars(sh)

    # 1) PROC-target validation (the hard-error class): every PROC name must be
    #    GLOBAL, a form-flow proc (<DICT>_FF), or a dcf item/record/level name.
    #    Crucially, do NOT accept a name just because a PROC declares it — that
    #    would self-whitelist `PROC <typo>` for a non-existent item.
    proc_allowed = set(dcf) | set(CSPRO_RESERVED) | {'GLOBAL'} | form_syms
    proc_bad = []
    for m in PROC_RE.finditer(apc_raw):
        name = m.group(1)
        u = name.upper()
        if u in proc_allowed or u.endswith('_FF'):
            continue
        line = apc_raw[:m.start()].count('\n') + 1
        proc_bad.append((name, line))

    # 2) General undefined-reference scan.
    refs = {}
    for m in REF_RE.finditer(apc):
        tok = m.group(1)
        if tok.upper() not in known:
            refs[tok] = refs.get(tok, 0) + 1

    return {
        'instrument': instrument,
        'dcf_symbol_count': len(dcf),
        'proc_count': len(PROC_RE.findall(apc_raw)),
        'proc_bad': proc_bad,
        'undefined_refs': sorted(refs.items(), key=lambda x: -x[1]),
        'arity_bad': arity_problems(apc, shared_srcs),
        'setvalueset_bad': setvalueset_problems(apc, working_vars, dcf),
    }


def main():
    # Lives in deliverables/CSPro/ — resolve the instrument dirs relative to it.
    base = Path(__file__).resolve().parent
    shared = [base / 'shared' / 'Capture-Helpers.apc', base / 'shared' / 'PSGC-Cascade.apc']
    # The 4 PSGC external lookup dicts attached to every .ent (referenced by the cascade).
    psgc = [base / 'shared' / f'psgc_{x}.dcf' for x in ('region', 'province', 'city', 'barangay')]
    targets = [
        ('F1', base / 'F1' / 'FacilityHeadSurvey.ent.apc', base / 'F1' / 'FacilityHeadSurvey.dcf', base / 'F1' / 'FacilityHeadSurvey.fmf'),
        ('F3', base / 'F3' / 'PatientSurvey.ent.apc',      base / 'F3' / 'PatientSurvey.dcf',      base / 'F3' / 'PatientSurvey.fmf'),
        ('F4', base / 'F4' / 'HouseholdSurvey.ent.apc',    base / 'F4' / 'HouseholdSurvey.dcf',    base / 'F4' / 'HouseholdSurvey.fmf'),
    ]
    overall_clean = True
    for name, apc, dcf, fmf in targets:
        if not apc.exists() or not dcf.exists():
            print(f'[{name}] SKIP — missing apc or dcf')
            continue
        r = validate(name, apc, dcf, shared, fmf_path=fmf, extra_dcf_paths=psgc)
        print(f'\n========== {name} ==========')
        print(f'  dcf symbols: {r["dcf_symbol_count"]}   PROC blocks: {r["proc_count"]}')
        if r['proc_bad']:
            overall_clean = False
            print(f'  !! PROC targets NOT in dcf ({len(r["proc_bad"])}) — HARD compile errors:')
            for nm, ln in r['proc_bad']:
                print(f'       line {ln}: PROC {nm}')
        else:
            print('  OK — every PROC target resolves to a known symbol')
        if r['setvalueset_bad']:
            overall_clean = False
            print(f'  !! setvalueset() on a non-field working var ({len(r["setvalueset_bad"])}) — HARD compile errors:')
            for nm, ln in r['setvalueset_bad']:
                print(f'       line {ln}: setvalueset({nm}, ...)  — {nm} is a declared variable, not a field')
        else:
            print('  OK — no setvalueset() on a non-field')
        if r['arity_bad']:
            overall_clean = False
            print(f'  !! user-function arity mismatch ({len(r["arity_bad"])}) — HARD compile errors:')
            for nm, ln, got, want in r['arity_bad']:
                print(f'       line {ln}: {nm}() called with {got} arg(s), defined with {want}')
        else:
            print('  OK — user-function call arity matches definitions')
        if r['undefined_refs']:
            print(f'  ?? Unresolved UPPER_SNAKE references ({len(r["undefined_refs"])} distinct):')
            for tok, cnt in r['undefined_refs'][:60]:
                print(f'       {tok}  (x{cnt})')
        else:
            print('  OK — no unresolved dictionary-style references')
    print('\n' + ('ALL CLEAN' if overall_clean else 'ISSUES FOUND — see PROC errors above'))
    return 0 if overall_clean else 1


if __name__ == '__main__':
    sys.exit(main())
