"""Per-locale count of label objects in src/generated/items.ts that carry a dialect string."""
import io, os, re
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = io.open(os.path.join(APP, "src", "generated", "items.ts"), encoding="utf-8").read()
total = len(re.findall(r"\ben: '", s))
counts = {l: len(re.findall(r"\b" + l + r": '", s)) for l in ["fil", "ceb", "bis", "ilo", "hil", "war", "bcl"]}
print("label objects:", total)
print(" ".join(f"{l}{n}" for l, n in counts.items()))
print(" ".join(f"{l}{round(100 * n / total)}%" for l, n in counts.items()) if total else "")
