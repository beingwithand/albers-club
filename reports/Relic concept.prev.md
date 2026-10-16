# Relic (working name): a product concept

**One-line pitch:** Relic keeps a private memory of your digital life. It uses the same memory techniques as ChatGPT, Claude, Gemini and Apple, runs them on hardware you own, and lends that memory to any AI you choose.

## The problem

Platforms record your activity and train AI on it, and assistants now build memories of you on their servers. The "own your memory" products keep disappearing: Meta bought Limitless, Rewind's parent, and switched off Rewind's capture in December 2025.

## Who it's for

Privacy-minded desktop knowledge workers, then former Rewind users and EU and Korean users with new portability rights. Relic is not for monitoring anyone else.

## How it works

**1. Onboarding backfill.**

- **Exports first.** On day one Relic requests every official export (Google Takeout, Meta, Reddit, TikTok, the X archive) and tracks each one until it can be downloaded.
- **A visible agent for the gaps.** It fills only what the exports miss, such as X bookmarks and Instagram collections. It works in a separate Relic browser window, with a progress banner and per-platform Pause and Stop.
- **You handle logins.** You sign in and complete two-factor yourself, and the model never sees passwords or cookies.
- **Paced and resumable.** The agent runs at a modest pace under daily caps, saves checkpoints, and stops for the day at the first warning screen.
- **Disclosed risk.** Each platform card says that its terms may forbid automated collection, so you opt in platform by platform.

Once the backfill is done, the agent retires. Official APIs, scheduled exports and live capture take over.

**2. Local capture.** The app snapshots the screen when something changes (accessibility text first, OCR second), and a browser extension records saves and visits. Audio is off by default. Password fields, private windows and banking apps are never recorded.

**3. The memory layer.** Relic copies the cloud assistants' mechanisms and runs them locally:

- **Raw record:** immutable and encrypted.
- **Episodes:** time-stamped and searchable by text, meaning and image.
- **Facts:** people, places and preferences, each with dates of validity, so old facts are retired rather than overwritten.
- **Profile:** a short memory file you can edit. It works like Muse's memory file and ChatGPT's memory summary, and it sits in a cached prompt prefix.
- **Procedures:** how assistants should behave. Only you change these.

Nightly "dreaming" jobs, like ChatGPT's, write digests, update facts and propose profile changes for you to review. Models are sized to the job: about 3B parameters for extracting facts into fixed fields (as Apple's on-device model does), 3–8B for answers, and an optional home box for heavy overnight work. Every item links to its sources. Deleting a source, person or topic therefore removes everything derived from it, and Relic verifies that nothing still surfaces.

**4. Memory for any AI, through MCP.** Claude, ChatGPT, Cursor or a local assistant can use Relic as its memory:

- Reads are scoped per assistant, redacted by default and cited.
- When an assistant wants to remember something, the proposal goes to a review queue that you approve inside Relic, never in the chat.
- Assistants cannot delete anything.
- Relic implements Claude's `/memories` file interface, so those files live on your disk.

**5. Agents and vault.** Agents follow scripted recipes in an isolated profile with a domain allowlist and no destructive actions. Vault keys are hardware-bound and opening it needs a biometric. Data lives on your drive or NAS, plus an encrypted offsite copy.

## Unobtrusive, not invisible

Relic opens no windows and sends no notifications during normal use. A small menu-bar icon always shows its state (capturing, paused or agent running), and one click pauses everything. It is never invisible:

- **Operating systems require it.** OS capture indicators and the monthly re-consent on macOS can't be suppressed.
- **Hiding is what stalkerware does.** Hidden capture gets apps banned from stores, flagged by antivirus software and sued.
- **The owner stays in control.** Setup happens on the device and requires the owner's biometric. There is no hidden mode and no remote viewing, and uninstalling Relic wipes the vault in one step.

## What makes it different

Cloud deletion is best-effort: Meta says Muse "may still remember" deleted items. Local rivals each lack something:

- **Screenpipe** is source-available and aimed at company workflows.
- **Recall** runs on fewer than 10% of Windows 11 PCs.
- **Timelinize** only imports archives.

Relic alone combines backfill, capture, layered memory, agents and verifiable deletion, all of it local.

## Business model

A free, open-source app; paid encrypted backup, an optional "Relic box" home server and an agent-recipe library. No data sales, ads or training.

## MVP (about 6 months)

The first release is a macOS app with:

- capture, a vault, a timeline and search
- the memory tiers, with nightly dreaming and an editable profile
- a scoped MCP server with a review queue
- backfill for Google, Meta, Reddit and X bookmarks

## Key risks

- **Infostealers** targeting the vault.
- **Memory poisoning and prompt injection** from captured content.
- **Platforms** blocking accounts over the agent.
- **Local model quality** limiting how good the memory is.
- **Audio-consent laws.**
- **Acquisition**, which is why the code is open and Relic pledges not to transfer it.
