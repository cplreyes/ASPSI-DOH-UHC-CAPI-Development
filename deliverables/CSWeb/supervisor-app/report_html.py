"""Render the 3-panel Supervisor-QA report as one self-contained HTML file.

PII-light by construction: only case keys, facility, enumerator IDs, statuses and
flag reasons are passed in — never names or answer values.
"""
from html import escape

_CSS = """body{font:14px system-ui,Arial;margin:24px;color:#1a1a1a}
h1{font-size:20px} h2{font-size:16px;margin-top:28px;border-bottom:2px solid #ccc}
table{border-collapse:collapse;margin-top:8px} td,th{border:1px solid #bbb;padding:4px 10px;text-align:left}
.behind{color:#b00;font-weight:bold} .muted{color:#777}"""


def _coverage_tbl(rows):
    if not rows:
        return "<p class=muted>No coverage data (no cases / no assignment lookup).</p>"
    out = ["<table><tr><th>Instr</th><th>Facility</th><th>Enumerator</th>"
           "<th>Done</th><th>Partial</th><th>Target</th><th>Remaining</th></tr>"]
    for r in rows:
        cls = " class=behind" if r.behind else ""
        out.append(f"<tr{cls}><td>{escape(r.instrument)}</td><td>{escape(r.facility)}</td>"
                   f"<td>{escape(r.enumerator_id)}</td><td>{r.done}</td><td>{r.partial}</td>"
                   f"<td>{r.target}</td><td>{r.remaining}</td></tr>")
    out.append("</table>")
    return "".join(out)


def _partials_tbl(rows):
    if not rows:
        return "<p class=muted>No partial / incomplete cases.</p>"
    out = ["<table><tr><th>Instr</th><th>Case</th><th>Facility</th><th>Reason</th></tr>"]
    for r in rows:
        out.append(f"<tr><td>{escape(r.instrument)}</td><td>{escape(r.case_key)}</td>"
                   f"<td>{escape(r.facility)}</td><td>{escape(r.reason)}</td></tr>")
    out.append("</table>")
    return "".join(out)


def _flags_tbl(flags):
    if not flags:
        return "<p class=muted>No data-quality flags.</p>"
    out = ["<table><tr><th>Case</th><th>Facility</th><th>Flag</th><th>Detail</th></tr>"]
    for f in flags:
        out.append(f"<tr><td>{escape(f.case_key)}</td><td>{escape(f.facility)}</td>"
                   f"<td>{escape(f.rule)}</td><td>{escape(f.detail)}</td></tr>")
    out.append("</table>")
    return "".join(out)


def render_report(coverage, partials, flags, cluster, generated):
    return (f"<!doctype html><html><head><meta charset=utf-8>"
            f"<title>Supervisor-QA — {escape(cluster)}</title><style>{_CSS}</style></head><body>"
            f"<h1>Supervisor-QA Report — {escape(cluster)} — {escape(generated)}</h1>"
            f"<h2>Coverage vs plan</h2>{_coverage_tbl(coverage)}"
            f"<h2>Partials / incomplete (#561)</h2>{_partials_tbl(partials)}"
            f"<h2>Data-quality flags</h2>{_flags_tbl(flags)}"
            f"</body></html>")
