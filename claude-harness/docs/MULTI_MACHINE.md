# Working on both desktop and laptop

Goal: open either machine and carry on, with the same harness, the same memory and the same projects. Nothing lives on only one machine (principle 12).

## What syncs, and how
| Layer | Mechanism | Conflict model |
|---|---|---|
| **Harness** (agents, skills, hooks, rules) | Private GitHub `beingwithand/claude-harness`, installed as a plugin on each machine (`claude plugin install harness@claude-harness --scope user`). Plugin auto-update is on, or run `/plugin` → update. Edit it in one checkout (`~/code/claude-harness`) and push. | git (one writer at a time; pull before editing) |
| **Global settings + CLAUDE.md** | `install.sh` symlinks `~/.claude/CLAUDE.md` and `PRINCIPLES.md` to the repo, and `bootstrap.sh --only settings` merges `config/settings.json`. Run both on each machine. | from the repo |
| **Logs and learned data** (`~/harness-data`) | Private GitHub repo, auto-committed hourly by launchd. **One log file per machine per month** (`log/YYYY-MM/<host>.jsonl`), so the machines never write the same file. Union merge stays as a safety net. | append-only, so no conflicts by design |
| **Claude auto memory** (`~/.claude/projects/*/memory/`) | Machine-local by default, so it's **mirrored into `harness-data/memory/<host>/`** by the hourly job. The other machine reads the mirror as reference. Project facts belong in project files, not auto memory. | per-host folders |
| **Session transcripts** (`~/.claude/projects/*.jsonl`) | `cleanupPeriodDays: 365`, and copied to the vault at session end. | per-host |
| **Projects** (`~/projects/<slug>/`) | Each is its own git repo (private), with large originals archived to Drive. Pull before working; the Stop gate pushes before you stop (the claim gate verifies the push). | git |
| **Drive files** | Google Drive for desktop on both machines: the hub account mirrored and personal accounts streamed. | Drive |
| **Vault** (`~/msg-vault`, raw messages and client text) | Phase 1: **primary on one machine**, with an encrypted offsite copy (restic/age). Phase 2, if both machines need it: Syncthing between the two Macs only, over Tailscale, with no cloud. Encrypted at rest by FileVault on both. | Syncthing versioning |
| **Secrets** | 1Password on both machines; never in any repo. | password manager |

## Rules for two machines
1. **Start of a session:** `git pull` the project (the SessionStart hook reminds you), and the plugin checks for updates.
2. **End of a session:** `/retro` → changelog → commit → **push, verified by the claim gate** (`ls-remote` = HEAD). Never leave unpushed work on one machine.
3. **Don't edit the same project on both machines at once.** If you need to, use separate branches or worktrees, and merge later.
4. **Remote Control on both.** Each machine's `claude remote-control` shows up in the Claude phone app, so you can drive either from your phone.
5. **The usage limits are shared** across both machines, since it's one account. The status line on each shows the same 5-hour and 7-day numbers.
6. **Host name in every record** (`host` field), so the logs show which machine did what.

## Setup on the second machine (about 20 minutes)
Same as `docs/DAY1.md` T0, skipping the data migration: run `bootstrap.sh`, install the plugin, clone `harness-data` (don't re-init it), let `install.sh` set `HARNESS_DATA`, sign in to Drive, then run the vault step (restore from the encrypted backup, or set up Syncthing).
