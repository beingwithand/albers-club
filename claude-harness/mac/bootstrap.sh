#!/usr/bin/env bash
# =============================================================================
# mac/bootstrap.sh: set up a new Mac for the claude-harness.
#
# Goals: nothing is ever lost again, Claude Code is fully set up, Remote
# Control works from the phone, computer use works, and permissions are wide
# open but fenced.
#
# Properties:
#   * Idempotent: each step checks first and skips what is already done.
#   * Every step asks first. Steps that use sudo, change system settings or
#     replace files default to "No".
#   * Skip steps without being asked:  SKIP="pmset,backblaze" ./bootstrap.sh
#     List the step names:             ./bootstrap.sh --list
#     Run a single step:               ./bootstrap.sh --only brew
#   * Answer "yes" to every SAFE step: ./bootstrap.sh --yes
#     (Steps that are destructive or use sudo still ask.)
#
# Usage (after cloning the repo):
#   git clone https://github.com/beingwithand/claude-harness ~/code/claude-harness
#   ~/code/claude-harness/mac/bootstrap.sh
# (On a brand-new Mac, `git` triggers the Xcode CLT install prompt first. That's fine.)
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
DATA="${HARNESS_DATA:-$HOME/harness-data}"
GH_OWNER="${GH_OWNER:-beingwithand}"
SKIP="${SKIP:-}"
ONLY=""
ASSUME_YES=0

STEPS=(xcode brew bundle node git python claude desktop computeruse tailscale \
       passwords repos settings launchd filevault pmset backup)

# ----- helpers ---------------------------------------------------------------
c_bold=$'\033[1m'; c_dim=$'\033[2m'; c_yel=$'\033[33m'; c_grn=$'\033[32m'; c_off=$'\033[0m'
say()  { printf '%s\n' "${c_bold}==> $*${c_off}"; }
note() { printf '%s\n' "${c_dim}    $*${c_off}"; }
warn() { printf '%s\n' "${c_yel}!!  $*${c_off}"; }
ok()   { printf '%s\n' "${c_grn}ok  $*${c_off}"; }
have() { command -v "$1" >/dev/null 2>&1; }

# ask "question" [default y|n]: returns 0 for yes. --yes only applies to steps whose default is y.
ask() {
  local q="$1" def="${2:-y}" ans prompt
  if [ "$def" = y ]; then prompt="[Y/n]"; else prompt="[y/N]"; fi
  if [ "$ASSUME_YES" = 1 ] && [ "$def" = y ]; then note "$q $prompt -> yes (--yes)"; return 0; fi
  read -r -p "    $q $prompt " ans </dev/tty || ans=""
  ans="${ans:-$def}"
  [[ "$ans" =~ ^[Yy] ]]
}

# should_run <step> "<description>" [default]: honours SKIP / --only, then asks.
should_run() {
  local step="$1" desc="$2" def="${3:-y}"
  if [ -n "$ONLY" ] && [ "$ONLY" != "$step" ]; then return 1; fi
  if [[ ",$SKIP," == *",$step,"* ]]; then note "skip $step (SKIP)"; return 1; fi
  echo; say "[$step] $desc"
  ask "Run this step?" "$def"
}

# ----- args ------------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    --yes|-y) ASSUME_YES=1 ;;
    --only)   ONLY="${2:?--only needs a step name}"; shift ;;
    --list)   printf '%s\n' "${STEPS[@]}"; exit 0 ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *) warn "unknown arg: $1"; exit 2 ;;
  esac
  shift
done

if [ "$(uname -s)" != "Darwin" ]; then
  warn "This script is for macOS. Exiting."; exit 1
fi

# =============================================================================
# 1. Xcode Command Line Tools (git, make, compilers). Homebrew needs them.
# =============================================================================
step_xcode() {
  should_run xcode "Xcode Command Line Tools" || return 0
  if xcode-select -p >/dev/null 2>&1; then ok "CLT already installed ($(xcode-select -p))"; return 0; fi
  xcode-select --install || true
  warn "A GUI installer opened. Finish it, then press Enter."
  read -r _ </dev/tty || true
}

# =============================================================================
# 2. Homebrew. Its official installer is a curl|bash. Read it first if you
#    like: https://brew.sh
# =============================================================================
step_brew() {
  should_run brew "Homebrew" || return 0
  if ! have brew && [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi
  if have brew; then ok "Homebrew present: $(brew --version | head -1)"; return 0; fi
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
  # Persist brew on PATH for zsh (macOS default shell), once.
  grep -q 'brew shellenv' "$HOME/.zprofile" 2>/dev/null || \
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
}

# =============================================================================
# 3. brew bundle: installs everything in mac/Brewfile (gh, node, python, jq,
#    ripgrep, tmux, Tailscale, 1Password + op, Claude desktop, Google Drive,
#    Chrome, Backblaze). Edit the Brewfile to remove what you don't want.
# =============================================================================
step_bundle() {
  should_run bundle "brew bundle (mac/Brewfile)" || return 0
  have brew || { warn "Homebrew missing; run the brew step first."; return 0; }
  brew bundle --file="$HERE/Brewfile"
}

# =============================================================================
# 4. Node: needed for npx-based MCP servers and tools. Installed via the
#    Brewfile. This step only checks it.
# =============================================================================
step_node() {
  should_run node "Check Node.js (for npx tools / MCP servers)" || return 0
  if have node; then ok "node $(node --version), npm $(npm --version)"; else
    warn "node not found. Run: brew install node"; fi
}

# =============================================================================
# 5. git + gh: identity, sane defaults, GitHub auth. Use the gh credential
#    helper so no token sits in a plain file you might lose.
# =============================================================================
step_git() {
  should_run git "git config + GitHub CLI login" || return 0
  local name email
  name="$(git config --global user.name || true)"
  email="$(git config --global user.email || true)"
  if [ -z "$name" ]; then read -r -p "    git user.name: " name </dev/tty; git config --global user.name "$name"; fi
  if [ -z "$email" ]; then
    note "Tip: use your GitHub noreply address (Settings > Emails) to keep your email private."
    read -r -p "    git user.email: " email </dev/tty; git config --global user.email "$email"
  fi
  git config --global init.defaultBranch main
  git config --global pull.rebase true
  git config --global fetch.prune true
  git config --global push.autoSetupRemote true
  ok "git identity: $(git config --global user.name) <$(git config --global user.email)>"
  if have gh; then
    if gh auth status >/dev/null 2>&1; then ok "gh already logged in"; else gh auth login; fi
    gh auth setup-git
  else
    warn "gh not installed (run the bundle step)."
  fi
}

# =============================================================================
# 6. Python: hooks/log_event.py runs with python3 -I. This step only checks it.
# =============================================================================
step_python() {
  should_run python "Check Python 3 / jq / ripgrep / tmux" || return 0
  if [ ! -f "$HOME/.tmux.conf" ] || ! grep -q allow-passthrough "$HOME/.tmux.conf"; then
    if ask "Add 'set -g allow-passthrough on' to ~/.tmux.conf (terminal notifications inside tmux)?" y; then
      echo 'set -g allow-passthrough on' >> "$HOME/.tmux.conf"; fi
  fi
  for t in python3 jq rg tmux; do
    if have "$t"; then ok "$t: $(command -v "$t")"; else warn "$t missing (brew bundle)"; fi
  done
}

# =============================================================================
# 7. Claude Code CLI: official native installer (it auto-updates).
#    VERIFY AGAINST CURRENT DOCS before running:
#    https://code.claude.com/docs/en/setup
#    At the time of writing: curl -fsSL https://claude.ai/install.sh | bash
#    It installs to ~/.local/bin/claude.
# =============================================================================
step_claude() {
  should_run claude "Claude Code CLI (official installer, verify the command against current docs)" || return 0
  export PATH="$HOME/.local/bin:$PATH"
  if have claude; then ok "claude present: $(claude --version 2>/dev/null || echo '?')"; else
    note "Running: curl -fsSL https://claude.ai/install.sh | bash"
    if ask "Proceed with the official installer?" y; then
      curl -fsSL https://claude.ai/install.sh | bash
    fi
  fi
  grep -q '.local/bin' "$HOME/.zshrc" 2>/dev/null || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
  note "Use the native installer, not npm: the npm route is outdated."
  if have claude; then
    note "Next: run 'claude' once to log in (Max plan account), then run 'claude doctor'."
    note "Plugin: claude plugin marketplace add $GH_OWNER/claude-harness && claude plugin install harness@claude-harness --scope user"
  fi
}

# =============================================================================
# 8. Claude desktop app: installed by the Brewfile (cask "claude"). Check it.
# =============================================================================
step_desktop() {
  should_run desktop "Claude desktop app" || return 0
  if [ -d "/Applications/Claude.app" ]; then ok "Claude.app installed"; else
    if have brew && ask "Install the Claude desktop app (brew install --cask claude)?" y; then brew install --cask claude; fi
  fi
}

# =============================================================================
# 9. Computer use + Claude in Chrome. Needs macOS privacy grants, which only
#    you can click. This step opens the right panes.
#   Desktop app: Settings > This computer > System > Computer use (enable),
#                 then grant Accessibility + Screen Recording to Claude.
#   CLI:          inside claude, run /mcp -> computer-use -> Enable.
#   Chrome:       inside claude, run /chrome -> "Enabled by default".
#   Per-app approvals last only for the session (by design).
# =============================================================================
step_computeruse() {
  should_run computeruse "Computer use permissions (opens System Settings panes)" || return 0
  open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility" || true
  note "Add/enable Claude in Accessibility. Press Enter for Screen Recording."
  read -r _ </dev/tty || true
  open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture" || true
  note "Enable Claude in Screen & System Audio Recording. Then in the Claude app: Settings > This computer > System > Computer use."
}

# =============================================================================
# 10. Tailscale: private network to reach this Mac from your phone (SSH,
#     Screen Sharing) without exposing ports. Remote Control itself goes
#     through Anthropic and does not need Tailscale. Tailscale is the backup
#     path when Claude is stuck.
# =============================================================================
step_tailscale() {
  should_run tailscale "Tailscale (log in, optionally enable Remote Login/SSH)" || return 0
  if [ -d "/Applications/Tailscale.app" ]; then open -a Tailscale; note "Log in from the menu bar icon, then install Tailscale on your phone."
  else warn "Tailscale.app missing (brew bundle)."; fi
  if ask "Enable macOS Remote Login (SSH) so you can reach this Mac over Tailscale? (sudo)" n; then
    sudo systemsetup -setremotelogin on || warn "Enable it in System Settings > General > Sharing > Remote Login instead."
  fi
}

# =============================================================================
# 11. Password manager. 1Password (`op`) is the default. Alternatives:
#     Bitwarden (`bw`), Proton Pass. Store ALL secrets and 2FA recovery codes
#     here, never in files or the harness repo.
#     Enable 1Password > Settings > Developer > "Integrate with 1Password CLI"
#     so `op` unlocks with Touch ID.
# =============================================================================
step_passwords() {
  should_run passwords "Password manager CLI (1Password op)" || return 0
  if have op; then ok "op $(op --version)"; op account list 2>/dev/null || note "Sign in: open 1Password, enable CLI integration, then 'op signin'."
  else warn "op missing (brew bundle, or swap for 'bw' if you use Bitwarden)."; fi
  note "Use secrets at runtime, e.g.: export ANTHROPIC_API_KEY=\$(op read 'op://Private/Anthropic/credential')"
}

# =============================================================================
# 12. Clone the harness + private data repo, then run install.sh.
# =============================================================================
step_repos() {
  should_run repos "Clone claude-harness + harness-data, run install.sh" || return 0
  mkdir -p "$HOME/code"
  [ -d "$HOME/code/claude-harness/.git" ] || gh repo clone "$GH_OWNER/claude-harness" "$HOME/code/claude-harness"
  if [ ! -d "$DATA/.git" ]; then
    if gh repo view "$GH_OWNER/harness-data" >/dev/null 2>&1; then gh repo clone "$GH_OWNER/harness-data" "$DATA"
    else note "No $GH_OWNER/harness-data repo yet. install.sh will init $DATA locally. Create the PRIVATE repo with:"
         note "  gh repo create $GH_OWNER/harness-data --private --source \"$DATA\" --push"; fi
  else ok "data repo present at $DATA"; fi
  "$HOME/code/claude-harness/install.sh"
}

# =============================================================================
# 13. ~/.claude/settings.json from config/settings.json. Never overwrites
#     the file: merges with jq and backs up the original first. See
#     config/settings.README.md.
# =============================================================================
step_settings() {
  should_run settings "Merge config/settings.json into ~/.claude/settings.json (backs up first)" n || return 0
  have jq || { warn "jq missing"; return 0; }
  local tpl="$REPO/config/settings.json" dst="$HOME/.claude/settings.json" tmp
  mkdir -p "$HOME/.claude"
  [ -f "$dst" ] || echo '{}' > "$dst"
  cp "$dst" "$dst.bak.$(date +%Y%m%d-%H%M%S)"
  tmp="$(mktemp)"
  # Deep-merge: existing values win for scalars and objects; the permission
  # arrays are unioned so your own rules are kept and the template's fences are added.
  jq -s '
    .[0] as $old | .[1] as $new
    | ($new * $old)
    | .permissions.allow = ((($old.permissions.allow // []) + ($new.permissions.allow // [])) | unique)
    | .permissions.deny  = ((($old.permissions.deny  // []) + ($new.permissions.deny  // [])) | unique)
    | .permissions.ask   = ((($old.permissions.ask   // []) + ($new.permissions.ask   // [])) | unique)
  ' "$dst" <(sed "s#__HOME__#$HOME#g" "$tpl") > "$tmp"
  jq -e . "$tmp" >/dev/null && mv "$tmp" "$dst" && ok "merged into $dst (backup saved alongside)"
}

# =============================================================================
# 14. launchd agents: hourly data auto-commit + always-on Remote Control.
#     The plists use __HOME__ / __RC_DIR__ placeholders. launchd does not
#     expand ~ or $HOME in paths, so this step fills them in.
#     Run `claude remote-control` ONCE interactively in that folder first:
#     the first run asks you to enable Remote Control and trust the directory.
# =============================================================================
step_launchd() {
  should_run launchd "Install launchd agents (autocommit, remote-control)" || return 0
  local la="$HOME/Library/LaunchAgents" uid; uid="$(id -u)"
  mkdir -p "$la" "$HOME/Library/Logs/harness"
  local rc_dir
  read -r -p "    Folder for Remote Control sessions [$HOME/code]: " rc_dir </dev/tty || rc_dir=""
  rc_dir="${rc_dir:-$HOME/code}"
  for name in com.harness.autocommit com.harness.remote-control; do
    if [ "$name" = com.harness.remote-control ] && ! ask "Install always-on Remote Control agent (unofficial recipe)?" y; then continue; fi
    sed -e "s#__HOME__#$HOME#g" -e "s#__RC_DIR__#$rc_dir#g" "$HERE/launchd/$name.plist" > "$la/$name.plist"
    plutil -lint "$la/$name.plist" >/dev/null || { warn "$name.plist failed lint"; continue; }
    launchctl bootout "gui/$uid/$name" 2>/dev/null || true
    launchctl bootstrap "gui/$uid" "$la/$name.plist" && ok "loaded $name"
  done
  note "Logs: ~/Library/Logs/harness/. Check status: launchctl print gui/$uid/com.harness.remote-control"
}

# =============================================================================
# 15. FileVault: full-disk encryption. A lost or stolen Mac then leaks nothing.
#     Store the recovery key in the password manager, NOT only in iCloud.
#     Trade-off: after a power failure, a FileVault Mac waits at the unlock
#     screen, so the always-on agents don't come back until someone types the
#     password. Keep FileVault on anyway. For planned reboots, use
#     `sudo fdesetup authrestart`.
# =============================================================================
step_filevault() {
  should_run filevault "FileVault check" || return 0
  local st; st="$(fdesetup status 2>/dev/null || echo unknown)"
  if [[ "$st" == *"On"* ]]; then ok "$st"; else
    warn "FileVault: $st"
    if ask "Turn on FileVault now? (sudo; shows a recovery key: save it to the password manager)" n; then
      sudo fdesetup enable
    else note "Or: System Settings > Privacy & Security > FileVault."; fi
  fi
}

# =============================================================================
# 16. pmset: keep the Mac awake for Remote Control. The phone can't drive a
#     sleeping Mac, so on power adapter (-c) we disable system sleep:
#       sleep 0         never sleep the system on AC
#       disksleep 0     never spin down disks on AC
#       displaysleep 10 the screen may still turn off after 10 min (saves the panel)
#       womp 1          wake on network access ("Wake for network access")
#       tcpkeepalive 1  keep network connections alive
#       autorestart 1   restart automatically after a power failure (desktops; may be ignored on laptops)
#     Laptops: with the lid closed, macOS still sleeps unless an external
#     display is connected, so leave the lid open. Battery settings (-b) are
#     left alone. Undo: sudo pmset -c sleep 1 ; sudo pmset restoredefaults
#     The Claude desktop app also has a "Keep computer awake" setting for
#     scheduled tasks, and the remote-control launchd agent wraps itself in
#     `caffeinate -ims`, so it keeps the Mac awake on its own.
#     Dedicated always-on machine: `sudo pmset -a sleep 0 displaysleep 0 disksleep 0`.
#     Avoid the undocumented `pmset disablesleep`.
# =============================================================================
step_pmset() {
  should_run pmset "pmset always-on (no sleep on power, autorestart). Uses sudo" n || return 0
  note "Current settings:"; pmset -g custom | sed 's/^/      /' || true
  if ask "Apply: sudo pmset -c sleep 0 disksleep 0 displaysleep 10 womp 1 tcpkeepalive 1; sudo pmset -a autorestart 1 ?" n; then
    sudo pmset -c sleep 0 disksleep 0 displaysleep 10 womp 1 tcpkeepalive 1
    sudo pmset -a autorestart 1 || warn "autorestart not supported on this model"
    ok "pmset applied"; pmset -g | sed 's/^/      /'
  fi
}

# =============================================================================
# 17. Backups: third copy. See docs/BACKUP.md. GitHub covers text and Google
#     Drive covers files; this step covers the whole disk.
# =============================================================================
step_backup() {
  should_run backup "Time Machine / Backblaze reminder" || return 0
  if tmutil destinationinfo 2>/dev/null | grep -q 'Name'; then ok "Time Machine destination configured"; tmutil latestbackup 2>/dev/null || true
  else warn "No Time Machine destination. Plug in an external drive and go to System Settings > General > Time Machine."; fi
  if [ -d "/Applications/Backblaze.app" ] || [ -d "/Library/Backblaze.bzpkg" ]; then ok "Backblaze installed: open it and confirm it's backing up"
  else note "Backblaze not installed (optional offsite copy: brew install --cask backblaze)."; fi
  note "Google Drive: open Google Drive.app, sign in, use 'Mirror files' for the folders you must never lose."
  note "Monthly restore drill: docs/BACKUP.md"
}

# ----- run -------------------------------------------------------------------
say "claude-harness Mac bootstrap  (repo: $REPO, data: $DATA)"
for s in "${STEPS[@]}"; do "step_$s"; done
echo; ok "Bootstrap finished. Next: docs/SECURITY.md (urgent checklist) and docs/BACKUP.md."
