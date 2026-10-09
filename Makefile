# Local helpers. CI doesn't use this file.
.PHONY: usage usage-timer preview build clean

## Refresh data/claude-usage.json from ~/.claude logs and stage it for commit
usage:
	python3 scripts/claude_usage.py export
	git add data/claude-usage.json
	@echo "Staged. Now: git commit -m 'data: refresh Claude usage' && git push"

## Install the daily usage push (systemd user timer, 21:00). See README "Claude Code usage panel"
CLONE := $(HOME)/.local/share/yo-usage
usage-timer:
	test -f $(HOME)/.ssh/yo_usage_deploy || ssh-keygen -q -t ed25519 -N '' -C "yo-usage deploy key" -f $(HOME)/.ssh/yo_usage_deploy
	test -d $(CLONE) || git clone -q git@github.com:3ll34ndr0/yo.git $(CLONE)
	git -C $(CLONE) config core.sshCommand "ssh -i $(HOME)/.ssh/yo_usage_deploy -o IdentitiesOnly=yes"
	install -Dm755 scripts/push_usage.sh $(HOME)/.local/bin/yo-push-usage
	install -Dm644 -t $(HOME)/.config/systemd/user systemd/yo-usage.service systemd/yo-usage.timer
	systemctl --user daemon-reload
	systemctl --user enable --now yo-usage.timer
	@echo "Deploy key (add with write access in repo Settings → Deploy keys):"
	@cat $(HOME)/.ssh/yo_usage_deploy.pub

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
