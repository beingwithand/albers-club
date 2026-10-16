# Backup plan: nothing lives only on one laptop

The old laptop's data was lost. This plan makes sure that losing any single machine, account or drive costs at most an hour of work.

## The 3-2-1 rule, applied

You keep **3** copies of everything that matters, on **2** different kinds of storage, with **1** copy offsite.

| What | Copy 1 (live) | Copy 2 | Copy 3 (offsite / independent) |
|---|---|---|---|
| Harness code: rules, skills, agents, ontology | `~/code/claude-harness` | GitHub `beingwithand/claude-harness` (private) | Time Machine / Backblaze |
| Harness data: logs, sessions, decisions, style memory | `~/harness-data` | GitHub `beingwithand/harness-data` (**private**), auto-committed every hour by launchd | Time Machine / Backblaze |
| Project text: CLAUDE.md, PROGRESS.md, decisions, code | project folder | GitHub (one private repo per project) | Time Machine / Backblaze |
| Files: PDFs, client work, translations, assets, art | Google Drive for desktop (Mirror mode) | Google's servers | Time Machine / Backblaze |
| Whole disk: apps, settings, `~/.claude`, everything else | the Mac | Time Machine (external drive at home) | Backblaze (cloud) |
| Secrets: passwords, API keys, 2FA recovery codes, FileVault recovery key | 1Password (or Bitwarden) | the password manager's cloud sync | **Emergency Kit printed on paper**, stored somewhere safe at home |

### Rules
- **Never use Google Drive or Dropbox on a git repo folder.** Sync tools corrupt `.git`, so text goes to GitHub only.
- **Never put secrets in git, Drive or the harness.** Use the password manager, or `op read` and `op run` at runtime.
- **The `harness-data` repo must be private.** It contains your prompts and client context.
- **Before you delete an original,** it must be in Drive, and `/intake` must have archived and verified it (BLUEPRINT §0.5).
- **Keep 2FA recovery codes in the password manager, and the password manager's own recovery details on paper.** Losing the phone and the laptop together should not lock you out.

## Setup checklist (new Mac)

- [ ] `gh auth login`, then clone `claude-harness`, and clone or create the private `harness-data` repo. The `repos` step of `mac/bootstrap.sh` does this.
- [ ] Load the hourly auto-commit agent: the `launchd` step of `mac/bootstrap.sh`, which installs `mac/launchd/com.harness.autocommit.plist`.
- [ ] Check it's working: `tail ~/Library/Logs/harness/autocommit.*.log`, and look on GitHub for a commit in the last hour.
- [ ] Google Drive for desktop: sign in, choose **Mirror files** for folders that must exist on disk, and add `~/Documents` and `~/Desktop` under "My Mac" if you want them in Drive. Exclude git repos.
- [ ] Time Machine: external drive, encrypted backups turned on. Go to System Settings > General > Time Machine.
- [ ] Backblaze (optional but recommended as the offsite copy): install, sign in, and confirm the first backup finishes. Store the private encryption key in the password manager.
- [ ] Password manager: every account imported, 2FA recovery codes saved, Emergency Kit printed.
- [ ] FileVault on, with the recovery key saved in the password manager (not only in iCloud).
- [ ] Turn on GitHub 2FA and save the recovery codes in the password manager. Do the same for Google, Anthropic and Apple ID.
- [ ] Claude: the plugin is installed from the private marketplace, and `~/.claude/settings.json` is merged from `config/settings.json`. Both can be rebuilt from GitHub.

## What is NOT covered (accept or fix)

- **Local Claude Code transcripts** (`~/.claude/projects/`) are covered by Time Machine and Backblaze only. Hook summaries go to `harness-data`.
- **Claude.ai chats** live on Anthropic's servers. Export them from Settings > Privacy > Export data (**verify** the menu path) quarterly if they matter.
- **Browser profiles and bookmarks:** use Chrome sync with your Google account.
- **Uncommitted work in project repos.** Auto-commit only covers `harness-data`. Commit and push project repos at every verified checkpoint (BLUEPRINT §0.5).

## Monthly restore drill (first weekend of the month, about 20 min)

A backup you haven't restored from doesn't count. Log each drill as an event in `harness-data` (type `drill`, with the outcome) so `/retro` can see failures.

- [ ] **GitHub:** clone `harness-data` into a temp folder (`gh repo clone beingwithand/harness-data /tmp/drill`). Confirm the latest commit is under an hour old and that yesterday's logs are there.
- [ ] **Harness:** in a temp folder, run `claude --plugin-dir ~/code/claude-harness` and confirm the skills and agents load. Run `claude plugin validate`.
- [ ] **Auto-commit agent:** run `launchctl print gui/$(id -u)/com.harness.autocommit`. Check the last exit code is 0 and the error log has no errors.
- [ ] **Google Drive:** open drive.google.com in a browser (not the synced folder), download one random PDF from last month, and open it.
- [ ] **Time Machine:** check the date of the latest backup (`tmutil latestbackup`). Restore one file from a week ago to the Desktop (Finder > Time Machine > Restore) and open it.
- [ ] **Backblaze:** sign in to the web console, restore one file, and check the "last backed up" date.
- [ ] **Password manager:** make sure you can unlock it on the phone without the laptop. Check that the 2FA recovery codes for GitHub, Google, Anthropic and Apple are present.
- [ ] **Secrets audit:** run `rg -l --hidden -g '!.git' '(sk-ant-|ghp_|github_pat_|AKIA|BEGIN .*PRIVATE KEY)' ~/code ~/harness-data`. Expect no hits.
- [ ] **Remote Control:** from the phone, open the Mac's Remote Control session and run a harmless command (`git status` in `~/code`).
- [ ] **Twice a year, the full "lost laptop" rehearsal:** on a spare user account or VM, follow the README's new-machine setup from scratch. Time it; the goal is about 20 minutes (BLUEPRINT §0 rule 5). Fix whatever slows you down.
