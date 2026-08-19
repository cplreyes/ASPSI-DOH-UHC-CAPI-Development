"""R25 caption gate - proves the on-form question de-duplication holds for an instrument.

Ruling R25 (2026-08-19, Task C1) makes every question field's on-form fmf caption a numeral
tag, so the question itself appears once per screen, in the .qsf pane that follows the
language setting. This checks the result rather than trusting it, by running the instrument's
own generate_fmf.build_fmf() in-process and comparing every emitted caption against that
field's .qsf question text.

Three assertions, in descending order of how badly a failure would hurt:

  1. NO-PROMPT       every on-form field must have .qsf question text. A numeral caption on a
                     field without one would leave the enumerator with nothing to read. This
                     is the check that made R25 safe to ship; it must stay at 0.
  2. COLLISIONS      no two fields on one DisplayTogether screen may derive the same caption.
                     Fix a collision by adding a SHORT_FORM_LABELS entry in that generator,
                     never by hand-editing the .fmf.
  3. DUPLICATION     how many captions still reproduce their qsf question stem. Non-zero is
                     expected and fine: roster grid COLUMNS keep their labels by design
                     (#1182) and long FIELD-CONTROL/GPS admin labels are labels, not questions
                     printed twice. The breakdown by kind is printed so the residual can be
                     read rather than guessed at.

Exit 0 if 1 and 2 hold, 1 otherwise. Duplication is reported, never enforced - the right
number is a judgement, not a constant.

Run:
    python aug17-tools/r25_caption_check.py F3
    python aug17-tools/r25_caption_check.py F1 F3 F4
"""
import html
import importlib
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

CSPRO = Path(__file__).resolve().parent.parent
QSF = {'F1': 'F1/FacilityHeadSurvey.ent.qsf',
       'F3': 'F3/PatientSurvey.ent.qsf',
       'F4': 'F4/HouseholdSurvey.ent.qsf'}

# A caption stem shorter than this is a field LABEL ("GPS Latitude", "Month"), not a question.
# Such a label is trivially a substring of its own prompt, and counting it as duplication
# overstates the defect by ~10% - it is not what PSA/DOH raised.
STEM_MIN = 25


def qsf_texts(path):
    """-> {field: EN question text}. Scanned line by line rather than parsed as YAML: the
    file carries megabytes of base64 image data and only the name/EN pairs are wanted."""
    out, cur, grab, buf = {}, None, False, []
    for line in path.read_text(encoding='utf-8-sig', errors='replace').split('\n'):
        m = re.match(r'^  - name: [A-Z0-9_]+\.([A-Z0-9_]+)\s*$', line)
        if m:
            if cur and buf:
                out.setdefault(cur, '\n'.join(buf))
            cur, grab, buf = m.group(1), False, []
            continue
        if cur is None:
            continue
        if re.match(r'^\s+EN: \|', line):
            grab, buf = True, []
        elif grab:
            if re.match(r'^\s{0,12}\S', line) and not line.startswith('            '):
                grab = False
            else:
                buf.append(line.strip())
    if cur and buf:
        out.setdefault(cur, '\n'.join(buf))
    return out


def parse_fmf(text):
    """-> [{name, roster, fields:[{name,caption}], blocks:[{name,fields}]}] from emitted fmf.

    A [Block]'s Position indexes the group's item sequence in which each EARLIER block also
    occupies one slot, so the real item start is Position minus the blocks emitted before it.
    """
    groups, cur, in_level, field, blk = [], None, False, None, None
    for line in text.split('\r\n'):
        if line == '[Level]':
            in_level = True
        if not in_level:
            continue
        if line == '[Group]':
            cur = {'name': None, 'roster': False, 'fields': [], 'blocks': []}
            groups.append(cur)
            field = blk = None
        elif line == '[EndGroup]':
            cur = None
        elif cur is None:
            continue
        elif line == '[Field]':
            field = {}
        elif line == '[Block]':
            blk = {}
            cur['blocks'].append(blk)
        elif line.startswith('Name='):
            if field is not None and 'name' not in field:
                field['name'] = line[5:]
            elif blk is not None and 'name' not in blk:
                blk['name'] = line[5:]
            elif cur['name'] is None:
                cur['name'] = line[5:]
        elif line.startswith('Type=Record'):
            cur['roster'] = True
        elif line.startswith('Text=') and field is not None:
            field['caption'] = line[5:]
            cur['fields'].append(field)
            field = None
        elif line.startswith('Position=') and blk is not None:
            blk['pos'] = int(line[9:])
        elif line.startswith('Length=') and blk is not None:
            blk['len'] = int(line[7:])
            blk = None
    for g in groups:
        for k, b in enumerate(g['blocks']):
            s = b['pos'] - k
            b['fields'] = [f['name'] for f in g['fields'][s:s + b['len']]]
    return groups


def plain(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def check(inst):
    texts = qsf_texts(CSPRO / QSF[inst])
    # build in a child process: each instrument ships its own generate_dcf/generate_fmf and
    # importing two of them in one interpreter collides in sys.modules.
    # Write the fmf to stdout as explicit UTF-8 BYTES and decode it here. Letting Python pick
    # an encoding fails on Windows: the generators' own diagnostics carry cp1252 em-dashes,
    # and a utf-8 text-mode pipe dies on them before the fmf is ever read.
    code = ('import sys;sys.path.insert(0,r"%s");sys.path.insert(0,r"%s");'
            'import generate_fmf as g;r=g.build_fmf();'
            'sys.stdout.buffer.write((r[0] if isinstance(r,tuple) else r).encode("utf-8"))'
            % (CSPRO / inst, CSPRO))
    p = subprocess.run([sys.executable, '-c', code], capture_output=True)
    if p.returncode != 0:
        print(f'{inst}: build_fmf FAILED\n{p.stderr.decode("utf-8", "replace")[-2000:]}')
        return False
    groups = parse_fmf(p.stdout.decode('utf-8'))

    noprompt, clashes, dup = [], [], defaultdict(int)
    kinds = defaultdict(int)
    total = 0
    for g in groups:
        derived = {}
        for f in g['fields']:
            total += 1
            cap = f['caption']
            kind = ('roster' if g['roster'] else
                    'keep-full' if not re.match(r'^\s*\d+(?:\.\d+)*\s*[.)]', cap) else
                    'specify' if '(specify)' in cap else
                    'numeral' if re.fullmatch(r'\d+(?:\.\d+)*\.', cap) else 'component')
            kinds[kind] += 1
            derived[f['name']] = cap
            t = plain(texts.get(f['name'], ''))
            if not t:
                noprompt.append((g['name'], f['name'], cap))
                continue
            stem = re.sub(r'^\s*\d+(?:\.\d+)*[.)]?\s*', '', cap).strip()[:60].rstrip(' .,;:-')
            if len(stem) >= STEM_MIN and stem.lower() in t.lower():
                dup[kind] += 1
        if g['roster']:
            continue
        for b in g['blocks']:
            seen = defaultdict(list)
            for fn in b['fields']:
                seen[derived[fn]].append(fn)
            for cap, names in seen.items():
                if len(names) > 1:
                    clashes.append((g['name'], b['name'], cap, names))

    ok = not noprompt and not clashes
    print(f'--- {inst}: {total} on-form captions ---')
    print('    kinds: ' + '  '.join(f'{k}={v}' for k, v in sorted(kinds.items())))
    print(f'    [{"PASS" if not noprompt else "FAIL"}] fields with no qsf prompt: {len(noprompt)}')
    for gn, fn, cap in noprompt:
        print(f'        {gn}.{fn}  caption={cap!r}')
    print(f'    [{"PASS" if not clashes else "FAIL"}] same-screen caption collisions: {len(clashes)}')
    for gn, bn, cap, names in clashes:
        print(f'        {gn}/{bn}: "{cap}" <- {names}')
    tot_dup = sum(dup.values())
    print(f'    [info] captions still matching their qsf stem: {tot_dup}'
          + (('  (' + '  '.join(f'{k}={v}' for k, v in sorted(dup.items())) + ')') if tot_dup else ''))
    if dup.get('numeral') or dup.get('specify'):
        print('    NOTE: a numeral/specify caption should not be able to match a question stem'
              ' - investigate before deploying.')
    return ok


def main():
    names = [a.upper() for a in sys.argv[1:]] or ['F1', 'F3', 'F4']
    bad = [n for n in names if not check(n)]
    print(('\nR25 caption gate: PASS' if not bad else f'\nR25 caption gate: FAIL {bad}'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
