#!/usr/bin/env bash
# One-time setup on a new machine. Safe to re-run.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DATA="${HARNESS_DATA:-$HOME/harness-data}"

# 1. Global CLAUDE.md -> symlink to this repo (back up any existing file)
mkdir -p "$HOME/.claude"
if [ -e "$HOME/.claude/CLAUDE.md" ] && [ ! -L "$HOME/.claude/CLAUDE.md" ]; then
  mv "$HOME/.claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md.bak.$(date +%s)"
fi
ln -sfn "$HERE/global/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
ln -sfn "$HERE/global/PRINCIPLES.md" "$HOME/.claude/PRINCIPLES.md"

# 2. Data directory (its own private git repo, e.g. beingwithand/harness-data)
mkdir -p "$DATA"/{log,style,sessions}
if [ ! -d "$DATA/.git" ]; then
  git -C "$DATA" init -q
  echo "Data repo initialised at $DATA. Add a private remote:  git -C \"$DATA\" remote add origin <url>"
fi

# 3. Persist HARNESS_DATA for future shells
for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
  [ -f "$rc" ] && ! grep -q HARNESS_DATA "$rc" && echo "export HARNESS_DATA=\"$DATA\"" >> "$rc"
done

echo "Settings: run  mac/bootstrap.sh --only settings  to merge config/settings.json into ~/.claude/settings.json (backs up first)."
echo "Done. Next: install the plugin (see README) and set up the hourly data auto-commit."
