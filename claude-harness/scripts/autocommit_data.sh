#!/usr/bin/env bash
# Commit and push $HARNESS_DATA (the private data repo: log/, style/, sessions/, labels/, evals/results/)
# if anything changed. Meant to run hourly from launchd (macOS) or cron (Linux). Safe to re-run.
#
# Usage:  HARNESS_DATA=~/harness-data scripts/autocommit_data.sh [--no-push]
#
# cron (crontab -e):
#   7 * * * *  HARNESS_DATA="$HOME/harness-data" /path/to/claude-harness/scripts/autocommit_data.sh >>"$HOME/harness-data/.autocommit.log" 2>&1
#
# launchd (~/Library/LaunchAgents/club.albers.harness-autocommit.plist), then
# `launchctl load ~/Library/LaunchAgents/club.albers.harness-autocommit.plist`:
#   <plist version="1.0"><dict>
#     <key>Label</key><string>club.albers.harness-autocommit</string>
#     <key>ProgramArguments</key><array>
#       <string>/bin/bash</string><string>/path/to/claude-harness/scripts/autocommit_data.sh</string></array>
#     <key>EnvironmentVariables</key><dict><key>HARNESS_DATA</key><string>/Users/YOU/harness-data</string></dict>
#     <key>StartInterval</key><integer>3600</integer>
#     <key>StandardOutPath</key><string>/Users/YOU/harness-data/.autocommit.log</string>
#     <key>StandardErrorPath</key><string>/Users/YOU/harness-data/.autocommit.log</string>
#   </dict></plist>
#
# Multi-machine safety: the JSONL logs are append-only, so the script makes sure the data repo's
# .gitattributes uses git's built-in `union` merge driver for *.jsonl. Concurrent appends from two
# laptops then merge by keeping both sides' lines instead of conflicting.
#
# Exit codes: 0 committed/pushed or nothing to do; 1 not a git repo / bad setup; 2 another run holds the
# lock; 3 commit is local only (pull/rebase or push failed; it will be retried next hour).
set -euo pipefail

PUSH=1
[ "${1:-}" = "--no-push" ] && PUSH=0

DATA="${HARNESS_DATA:-$HOME/harness-data}"
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "[$(ts)] autocommit: $*"; }

if [ ! -d "$DATA" ]; then log "no data dir at $DATA"; exit 1; fi
if ! git -C "$DATA" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  log "$DATA is not a git repository (run install.sh)"; exit 1
fi

# Single-run lock (mkdir is atomic on POSIX). Stale locks older than 2 hours are removed.
LOCK="$DATA/.git/autocommit.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +120 2>/dev/null)" ]; then
    rmdir "$LOCK" 2>/dev/null || true
    mkdir "$LOCK" 2>/dev/null || { log "lock busy"; exit 2; }
  else
    log "another run is in progress"; exit 2
  fi
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

# Don't interfere with a rebase/merge someone left in progress.
GITDIR="$(git -C "$DATA" rev-parse --git-dir)"
case "$GITDIR" in /*) ;; *) GITDIR="$DATA/$GITDIR" ;; esac
if [ -d "$GITDIR/rebase-merge" ] || [ -d "$GITDIR/rebase-apply" ] || [ -f "$GITDIR/MERGE_HEAD" ]; then
  log "rebase/merge in progress in $DATA; resolve it by hand"; exit 3
fi

# Ensure union merge for append-only logs.
GA="$DATA/.gitattributes"
if ! grep -qs '^\*\.jsonl merge=union' "$GA"; then
  echo '*.jsonl merge=union' >>"$GA"
fi
if ! grep -qs '^finance/\*\.csv merge=union' "$GA"; then
  echo 'finance/*.csv merge=union' >>"$GA"
fi
# Keep local runtime files out of the repo.
GI="$DATA/.gitignore"
grep -qsx '.autocommit.log' "$GI" || echo '.autocommit.log' >>"$GI"

if [ -z "$(git -C "$DATA" status --porcelain)" ]; then
  log "no changes"
else
  git -C "$DATA" add -A
  n="$(git -C "$DATA" diff --cached --name-only | wc -l | tr -d ' ')"
  git -C "$DATA" commit -q -m "auto: data snapshot $(ts) from $(hostname -s 2>/dev/null || hostname) ($n files)"
  log "committed $n file(s)"
fi

[ "$PUSH" -eq 1 ] || exit 0
if [ -z "$(git -C "$DATA" remote)" ]; then
  log "no remote configured; commit is local only (git -C \"$DATA\" remote add origin <url>)"; exit 3
fi
BRANCH="$(git -C "$DATA" symbolic-ref --short HEAD 2>/dev/null || echo main)"
if git -C "$DATA" ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  if ! git -C "$DATA" pull -q --rebase origin "$BRANCH"; then
    git -C "$DATA" rebase --abort >/dev/null 2>&1 || true
    log "pull --rebase failed; local commit kept, will retry"; exit 3
  fi
fi
# Nothing to push if we're level with the remote.
if git -C "$DATA" rev-parse -q --verify "origin/$BRANCH" >/dev/null &&
   [ "$(git -C "$DATA" rev-list --count "origin/$BRANCH..HEAD")" = "0" ]; then
  log "up to date with origin/$BRANCH"; exit 0
fi
if git -C "$DATA" push -q -u origin "$BRANCH"; then
  log "pushed to origin/$BRANCH"
else
  log "push failed (offline?); will retry next run"; exit 3
fi
