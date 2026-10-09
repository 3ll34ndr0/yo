#!/usr/bin/env bash
# Daily refresh of data/claude-usage.json, run by the yo-usage systemd user timer
# (systemd/, installed with `make usage-timer` as ~/.local/bin/yo-push-usage).
# Works in its own clone, never in the working copy. Commits only when the
# numbers changed; the push touches data/** so the site workflow rebuilds.
set -euo pipefail

cd "${YO_USAGE_CLONE:-$HOME/.local/share/yo-usage}"
# The clone is disposable (the data is rebuilt from ~/.claude every time),
# so a hard reset beats any merge: a failed push yesterday can't wedge it.
git fetch -q origin main
git reset -q --hard origin/main
python3 scripts/claude_usage.py export
# generated_at changes on every export; ignore it
if git diff --quiet -I '"generated_at"' -- data/claude-usage.json; then
  git checkout -q -- data/claude-usage.json
  echo "usage unchanged, nothing to push"
  exit 0
fi
git commit -qm "data: refresh Claude usage" -- data/claude-usage.json
git push -q origin HEAD:main
echo "pushed"
