# Day 1 on the new Mac: parallel rebuild plan (6–7 terminals)

Goal: everything rebuilt in parallel (harness, data, projects, backups, GitHub), with each terminal on its own track and its own git worktree or folder, so the tracks never step on each other. Use Ghostty tabs or tmux windows, one per track, named T1–T7.

## T0: first 30 minutes, alone (everything else depends on it)
1. `docs/SECURITY.md`: rotate passwords and revoke tokens (including the keys from commit `ea78134`).
2. `mac/bootstrap.sh`, step by step: Xcode CLT, Homebrew + Brewfile, Node, gh, Python, Claude Code (native installer), Claude desktop app, Tailscale, 1Password, FileVault, pmset.
3. `gh auth login` → install the plugin: `claude plugin marketplace add <owner>/claude-harness` → `claude plugin install harness@claude-harness --scope user`.
4. `mac/bootstrap.sh --only settings` (merges `config/settings.json`), then `claude doctor` and `/status`.
5. Create the private `harness-data` repo, run `install.sh`, and load the launchd autocommit job.
6. Turn on Remote Control (`/config`), phone push notifications, Chrome, and computer use.

## The parallel tracks
| Terminal | Track | First prompt (the orchestrator routes it) | Done when |
|---|---|---|---|
| **T1** | **Backups and GitHub** | "Set up the 3-2-1 backups in `docs/BACKUP.md`: harness-data remote, Drive for desktop (hub mirrored), rclone read-only remotes, Time Machine/Backblaze. Move claude-harness out of albers-club into its private repo, then delete the public branch." | `docs/BACKUP.md` restore drill passes |
| **T2** | **Harness verification** | "Run the full harness check: tests, `harness_index.py --check`, `run_evals.py --area harness`, live hook ID test, orchestrator routing test, step_check. Fix only surgically." | all green, logged |
| **T3** | **Data ingest** | "Run the Gmail hub + forwarding plan, Takeout exports per account, import the Gmail backfill (applications, platforms, clients), and the voice-harvest backfill since 2026-02-01." | records validate with `schema_check.py` |
| **T4** | **Resonance recovery** | "Check AWS (EC2 Mac volumes/snapshots/AMIs), Modal apps, and any old-Mac backup; then build `ocr-bench` and run it on 20 PDFs; then diff the app video against the June snapshot." | recovery report + bench report |
| **T5** | **Client project A** (e.g. Folio) | "Open `~/projects/<slug>` from the brief, restore its pipeline and documents via `/intake`, and list today's deliverables." | the project's PROGRESS.md is current |
| **T6** | **Client project B** (e.g. Agents Only / GMR sourcing) | Same as T5, plus "rebuild the document-harvesting automation from the brief." | automation re-runs on a sample |
| **T7** | **Admin** | "Follow-ups from the Gmail backfill summary: TOIN availability + invoice, Mercor Folio return date, Handshake verification, payments (Deel, Payoneer, Hyperwallet)." | each item drafted for my OK |

Project briefs (private, reconstructed from your sessions and email) are kept out of public repos. They go in each project's own private folder once the private harness repo exists.

## Rules for running many terminals
- **One track per terminal,** each in its own folder or git worktree (`claude --worktree` or `git worktree add`). Never two terminals editing the same repo checkout.
- **Watch usage.** The status line shows 5-hour and weekly use. With 6–7 terminals, the usage guard's levels (70%, 75%, 90%) apply across all of them because the limits are account-wide. Put bulk work (labeling, extraction) on Haiku and use Fable only where it's needed.
- **Hand off at about 200k context in each terminal** (`/handoff`, then `/clear`).
- **Everything is logged and verified.** The Stop gates enforce pipelines and verification in every terminal.
- **End of day:** run `/retro` in each terminal, then `/pattern-review`, then push everything.
