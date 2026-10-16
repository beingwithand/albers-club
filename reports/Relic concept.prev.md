# Relic (working name): a product concept

**One-line pitch:** Relic keeps a private, searchable record of what you do on your devices, with a local AI and local agents that work for you. None of it leaves hardware you own unless you send it.

## The problem

Your digital life is recorded in detail, but not for you. Platforms and data brokers keep your activity and increasingly train AI on it. The copy you're allowed is a ZIP file whose download link expires within days. The "own your memory" products have disappeared into Big Tech. Meta bought Limitless, Rewind's parent, and Rewind's capture was switched off in December 2025. Bee went to Amazon. Humane's pin was bricked.

## Who it's for

Privacy-minded knowledge workers on desktop who want a "second brain" but won't trust a cloud company with it; then former Rewind users, people leaving Google, and EU and Korean users with new portability rights. Relic is not for monitoring anyone else.

## How it works

**Local capture.** A signed desktop app snapshots the screen only when something changes. It reads exact text from the operating system's accessibility layer first and falls back to on-device OCR. Audio is off by default, and when turned on it records only the user's own microphone and transcribes locally. Retention is tiered: recent days keep full frames, older ones keep text only, for roughly 5–10 GB a month. Password fields, private windows, password managers, banking apps and any window an app has hidden from capture are never recorded.

**On-device AI.** SQLite full-text and vector search sit under a local 3–8B model that can answer questions like "what was that pricing page I saw in March?" A read-only, scoped MCP server lets assistants query the record when the user approves it.

**Local agents.** Agents are scripted "recipes", for example requesting your Google Takeout or filing an AI-training objection. A local model steps in only to repair a step that broke. You handle logins and two-factor prompts yourself, and the model never sees passwords, cookies or tokens. Agents run in an isolated browser profile, can visit only allowlisted sites, cannot take destructive actions, and keep a log you can replay.

**The vault.** Keys are bound to the device's hardware (Secure Enclave, TPM or Android Keystore), and viewing requires a biometric unlock. Data lives on your own drive or NAS, plus an encrypted offsite copy.

**Imports and purge.** Relic imports official exports (Takeout, Meta, Spotify), EU and Korean portability feeds, email, and iMessage from your Mac. A rights dashboard then handles AI-training opt-outs and deletion requests, and checks later that deletion happened.

## What makes it different

Each rival gives up something important:

- **Screenpipe** is source-available rather than open, and it is aimed at company workflows.
- **Recall** runs on fewer than 10% of Windows 11 PCs and has no agents.
- **Timelinize** only imports archives; it does not capture.

Relic alone combines local capture, local AI and agents: "the agentic stuff Apple should be doing", built by someone with no incentive to read your data.

## Safety and consent principles

- Relic records only the device owner, and it is set up on the device with the owner's biometric.
- There is no hidden mode, no remote viewing and no "monitor your partner" feature. Removing the app takes one step and wipes the vault.
- Relic never reads credentials, cookies, tokens or keys, and it never bypasses encryption or capture protections.
- Every capture source is opt-in, and there is no telemetry of content.
- The code is open, with reproducible builds, and the project pledges never to sell or transfer the app or its extension to another owner.

## Business model

The core app is free and open source. Revenue comes from an encrypted offsite backup and sync plan, an optional preconfigured NAS "Relic box", and a maintained library of agent recipes. Relic never sells data, runs ads or trains on user data.

## MVP (about 6 months)

The first release is a macOS app with:

- event-driven capture, reading accessibility text first and falling back to OCR
- an encrypted vault, a timeline and local search
- local Q&A over your record, plus a read-only MCP server
- iMessage and email import
- three agent recipes: Google Takeout, Meta export and Spotify history

Windows follows.

## Key risks

- **Infostealers:** the vault becomes their richest target on the device.
- **Prompt injection:** a malicious page or message could hijack an agent.
- **Platforms:** sites may ban accounts or bring legal action over agents.
- **OS friction:** monthly macOS re-consent; no iOS capture.
- **Audio law:** all-party-consent US states and Korea.
- **Acquisition:** Relic itself could be bought, which is why open code and the non-transfer pledge matter.
