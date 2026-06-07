#!/usr/bin/env bash
# SessionStart hook: auto-write today's standup and seed retro if sprint end.
# Scoped to the ASPSI-DOH-CAPI-CSPro project via .claude/settings.local.json.
# Silent on success; errors logged by the Python scripts themselves.
# Never blocks the session — always exits 0.

set +e

# Resolve project root from this script's location (two levels up from .claude/hooks/).
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "${script_dir}/../.." && pwd)"

# Prefer `py` (Windows launcher) then `python` then `python3`.
pybin=""
for cand in py python python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    pybin="$cand"
    break
  fi
done

if [ -z "$pybin" ]; then
  echo "[session-start-scrum] no python interpreter found on PATH" >&2
  exit 0
fi

"$pybin" "${repo}/.claude/scripts/generate_standup.py" --repo "$repo" >/dev/null 2>&1 || true
"$pybin" "${repo}/.claude/scripts/generate_retro.py"    --repo "$repo" >/dev/null 2>&1 || true

exit 0
