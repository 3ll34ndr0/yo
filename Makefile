# Local helpers. CI doesn't use this file.
.PHONY: usage preview build clean

## Refresh data/claude-usage.json from ~/.claude logs and stage it for commit
usage:
	python3 scripts/claude_usage.py export
	git add data/claude-usage.json
	@echo "Staged. Now: git commit -m 'data: refresh Claude usage' && git push"

## Live preview at http://localhost:8080 (full rebuild so the panels are fresh)
preview: clean
	nicolino auto

build:
	nicolino build

## `nicolino clean` keeps its cache (.kvstore/.croupier), which also caches the
## shortcode output of the home panels, so wipe it too.
clean:
	nicolino clean
	rm -rf output .kvstore .croupier .nicolino.lock
