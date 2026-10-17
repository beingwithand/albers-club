# Phone-as-remote-control for agents running on the user's own computer / home server (state as of Oct 2026)

Scope: products and OSS where the agent (or at least its tools) runs on the user's Mac or home box and the phone is a remote control. These are the local counterparts to cloud agents such as xAI Grok Bot, OpenAI dots and Manus. Goal: architecture lessons for "Relic".

Method notes. Primary evidence comes from shallow clones, which were read only and never executed. They live under `/tmp/claude-0/-home-user-albers-club/3712d12f-853b-5b60-93d4-c8956af51529/scratchpad/clones/`:
- `openclaw` (github.com/openclaw/openclaw, HEAD c5733c4, 2026-10-16)
- `happy` (github.com/slopus/happy, HEAD 5ce2cd0, 2026-10-16)
- `omnara` (github.com/omnara-ai/omnara, HEAD 502124e, 2026-10-16)
- `codex` (github.com/openai/codex, HEAD 221e4e7, 2026-10-16)

The code.claude.com docs pages were fetched in full. Facts marked **[snippet]** come only from search-engine summaries and were not read on the page itself.

---

## 1. Self-hosted personal agents controlled via chat apps / companion apps (OpenClaw lineage)

### Takeaway
OpenClaw (formerly Warelay, then Clawdbot, then Moltbot) is the reference design. It has one always-on **Gateway** process on the user's machine. The Gateway owns sessions, credentials and chat-channel bridges, and binds only to loopback by default. Phones connect in two ways. They can write through existing chat apps (Telegram, WhatsApp, iMessage and others), which the Gateway bridges. Or they can use a native iOS "node" app over WebSocket, reached via the LAN, Tailscale Serve, an SSH tunnel or Cloudflare Access. Push notifications go through a hosted, attested APNs relay. Adoption was enormous, and so was the security fallout.

### Cited findings
- **Naming/lineage.** VISION.md says: "It evolved through several names and shells: Warelay -> Clawdbot -> Moltbot -> OpenClaw." License is MIT, "Copyright (c) 2026 OpenClaw Foundation" — `openclaw/VISION.md` lines 1–20, `openclaw/LICENSE` — [GitHub openclaw/openclaw](https://github.com/openclaw/openclaw). A rename after Anthropic trademark complaints in January 2026 is reported **[snippet]** — [LangWatch](https://langwatch.ai/blog/how-openclaw-clawbot-works-behind-the-scenes---and-why-agent-observability-matter), [Medium/kkamdar](https://medium.com/@kkamdar/clawbot-the-self-hosted-ai-agent-that-broke-github-and-changed-how-we-think-about-personal-ai-11db8086a77f).
- **Topology.** "OpenClaw runs one Gateway (the master) on a host and connects every client to it. The Gateway owns sessions, auth profiles, channels, and state; everything else is a client." Operators (CLI or macOS app) and **nodes** (iOS/Android) connect to the Gateway WebSocket — `docs/gateway/remote.md` lines 7–12 — [repo](https://github.com/openclaw/openclaw/blob/main/docs/gateway/remote.md).
- **Default bind.** The Gateway WebSocket "binds to **loopback** by default, on port `18789`." For remote use the docs list Tailscale Serve, a trusted LAN or tailnet bind, or an SSH tunnel (`ssh -N -L 18789:127.0.0.1:18789`). Suggested topologies are an always-on VPS or home server, a home desktop, or a laptop — `docs/gateway/remote.md` lines 17–31, 43–55.
- **Command flow.** "Telegram message arrives at the Gateway → Gateway runs the agent → Gateway calls the node over the Gateway WebSocket (`node.invoke` RPC) → Node returns result; Gateway replies to Telegram." — `docs/gateway/remote.md` lines 39–46. The agent loop always runs on the Gateway host, and phones are peripherals that expose capabilities.
- **Tailscale integration.** `gateway.tailscale.mode` accepts three values. `serve` is tailnet-only, and "the gateway stays on `127.0.0.1`". `funnel` is public HTTPS and requires a shared password. `off` disables it. Alternatively `bind: "tailnet"` plus token auth exposes `ws://<tailscale-ip>:18789` — `docs/gateway/tailscale.md` lines 9–20, 40–55.
- **Pairing.**
  - Two layers are stored in the Gateway's SQLite state: *device pairing*, which gates the `connect` handshake, and *node capability approval* (`node.pair.*`), which gates which commands a node may expose. "Until approval, node commands stay filtered."
  - Device-pairing requests expire after 5 minutes — `docs/gateway/pairing.md` lines 10–55.
  - The iOS app pairs by scanning a QR or setup code from the Control UI or `openclaw qr`.
  - "Plaintext LAN `ws://` setup is automatically limited for bearer-token safety". Full access needs `wss://` or Tailscale Serve — `docs/platforms/ios.md` ~lines 270–290.
- **iOS app.** Requires iOS 26.2 or later and is on the App Store.
  - Exposes these node capabilities: screen snapshot, camera, location, Talk mode, voice wake and Health summaries.
  - Has an **Approvals** inbox with a pending count. Per-session icons distinguish *question* from *approval*.
  - Includes a durable offline outbox (up to 50 messages, expiring after 48 h), an offline transcript cache, snooze and wake for sessions, and a sidebar with **Workboard** and **Automations** pages served by the Gateway dashboard.
  - "iOS may suspend these foreground connections after the app enters the background."
  - Source: `docs/platforms/ios.md` lines 15–110, ~284.
- **Push via a hosted APNs relay.** This is the most relevant pattern for Relic.
  - Official App Store builds use `https://ios-push-relay.openclaw.ai`.
  - The app registers with the relay using **App Attest plus a StoreKit app-transaction JWS**. It gets back an opaque relay handle and a "registration-scoped send grant" delegated to the specific paired Gateway's identity (`gateway.identity.get`). It then forwards that registration to the Gateway via `push.apns.register`.
  - The Gateway signs each send request with its device identity, and the relay verifies the signature. "The Gateway never stores the raw APNs token… the relay sends the final push to APNs."
  - Stated rationale: "keep production APNs credentials out of user Gateways… prevent one Gateway from sending wake pushes to iOS devices owned by a different Gateway."
  - Self-built apps fall back to direct APNs with `OPENCLAW_APNS_TEAM_ID/KEY_ID/PRIVATE_KEY_P8` on the gateway host.
  - Source: `docs/platforms/ios.md` lines 602–675; config `gateway.push.apns.relay.baseUrl` in `docs/gateway/config-gateway.md` lines 211–215.
- **Background liveness on iOS.** On a silent push, a background refresh (BGTaskScheduler) or a significant-location wake, the app "attempts a short node reconnect and then calls `node.event` with `event: \"node.presence.alive\"`". "iOS decides when they actually execute." — `docs/platforms/ios.md` lines 641–647.
- **Remote access behind Cloudflare Access.** The iOS app supports a Cloudflare Access sign-in in an in-app browser, followed by an "encrypted session transfer" before normal Gateway pairing — `docs/platforms/ios.md` "Cloudflare Access sign-in" section (~lines 125–160); see also `docs/gateway/cloudflare-access.md`.
- **Credentials.**
  - A `secrets` tool lets the agent *request* a credential the user types into a trusted prompt. The value "never appears in the chat, the session transcript, the tool result, or the model's context — the agent receives only entry metadata and its store SecretRef" — `docs/tools/secrets.md` lines 9–16.
  - The macOS app can sync allow-listed browser cookies, "decrypted locally on this Mac (one macOS Keychain or Touch ID prompt per session)", to a remote gateway over the encrypted Gateway connection — `docs/platforms/macos.md` line 281.
- **Browser and login takeover.** "When a site requires login, sign in manually in the host browser's `openclaw` profile. Automated logins often trigger anti-bot defenses". The agent uses a dedicated Chrome profile named `openclaw`. Passkeys require a headed profile — `docs/tools/browser-login.md` lines 9–40.
- **Exec approvals.** Policy modes are deny, allowlist, ask, auto and full. Approvals "are enforced locally on the execution host" and "can only tighten" config — `docs/tools/exec-approvals.md` lines 10–40.
- **Channels.** The `docs/channels/` directory lists Telegram, WhatsApp, Discord, Slack, Signal, iMessage (native via `imsg` JSON-RPC, or via BlueBubbles), Matrix, MS Teams, LINE, WeChat, Feishu, SMS, IRC, Nostr and others. For iMessage, "run the Gateway and `imsg` on the same signed-in macOS Messages host" — `docs/channels/imessage.md` lines 1–12.
- **Scheduling.** `openclaw automations` (alias `openclaw cron`), plus a "heartbeat" mechanism and "standing orders" — `docs/automation/cron-jobs.md` lines 7–14.
- **Adoption.** Star counts are unreconciled **[snippet]**: 250k+ (March 2026), 310k+ with 58k forks (April 2026), 346k+ (April) — [tenten.co](https://tenten.co/openclaw/en/docs/whats-new/march-2026), [openclawvps.io](https://openclawvps.io/blog/openclaw-statistics).
- **Security fallout [snippet]:**
  - About 135,000 exposed instances (attributed to Bitdefender).
  - JFrog: "93.4% of publicly reachable instances had critical authentication bypasses".
  - CVE-2026-25253, a one-click RCE rated CVSS 8.8, fixed in v2026.1.29.
  - 800–1,400 malicious ClawHub skills.
  - Sources: [clawdocs known vulns](https://clawdocs.org/security/known-vulnerabilities), [betterclaw](https://betterclaw.io/blog/openclaw-security-2026), [NVD CVE-2026-26322](https://nvd.nist.gov/vuln/detail/CVE-2026-26322). Aggregator figures, unverified.

### Inferences
- The OpenClaw "loopback plus a private overlay" default (Tailscale or SSH) is a *reaction* to the mass-exposure incident. Relic should never expose a listening port to the internet. Outbound-only connections, or a private overlay, should be the default.
- The attested push relay is the one piece of hosted infrastructure even a "fully local" product cannot avoid on iOS. APNs credentials belong to the app publisher. OpenClaw's design (App Attest, per-gateway delegated send grant, gateway-signed sends, relay holding the APNs token) is a strong template.
- Chat-app bridges (Telegram, iMessage) give zero-install phone access. The cost is that approval authority is handed to whoever can message the bot, so sender allowlists are mandatory.

### Gaps
- I did not read the OpenClaw protocol source to confirm the wire encryption used between the iOS app and the Gateway, beyond TLS, Tailscale and SSH. There is no evidence of an app-layer E2EE relay for chat traffic, so remote access relies on the overlay network.
- The ios.md does not mention a live-screen-preview / "take over the Mac" UX. The `screen` tool only arranges Control UI panes (`docs/tools/screen.md` lines 11–14).

---

## 2. Remote control of local coding/desktop agents from the phone

### Takeaway
Big vendors have converged on an **outbound-only connection from the host to a vendor relay, plus the vendor's phone app** model: Anthropic (Claude Code Remote Control), OpenAI (Codex in the ChatGPT app) and Cursor (Remote Control). There are no inbound ports, the vendor account is the identity, and transport is TLS to the vendor (not E2EE). Happy is the main OSS alternative and adds client-side E2EE over a blind, self-hostable relay. Omnara pivoted away from "remote for Claude Code" into a managed-agent platform in which the agent lives in a control plane and the user's machine is just an execution target.

### Cited findings — Claude Code Remote Control (Anthropic)
- "Claude keeps running locally the entire time, so your code execution and filesystem access stay on your machine". Filesystem, MCP servers and tools stay available. The session syncs across terminal, browser and phone. It reconnects automatically after sleep or network drops — [code.claude.com/docs/en/remote-control](https://code.claude.com/docs/en/remote-control).
- "Your local Claude Code session makes outbound HTTPS requests only and never opens inbound ports on your machine. When you start Remote Control, it registers with the Anthropic API and polls for work." Traffic goes "through the Anthropic API over TLS", using "multiple short-lived credentials, each scoped to a single purpose and expiring independently" — same page, Security section.
- **Plans.** Pro, Max, Team and Enterprise. API keys are not supported. Team and Enterprise require an Owner toggle. HIPAA orgs have it off — same page.
- **Server mode.** `claude remote-control` waits for remote connections and shows a URL and QR code. `--spawn worktree` gives each on-demand session its own git worktree. `--capacity` defaults to 32 concurrent sessions. `--chrome` lets Claude use Chrome on the machine. Crashed sessions are re-served when a message arrives. Server mode gives up after about 10 minutes offline — same page.
- **Trusted Devices.** Optional. Each phone or browser enrolls its own credential, only shortly after a full sign-in, and devices can be revoked individually — same page.
- **Push.**
  - Two toggles: "Push when Claude decides" (task finished, or proactive) and "Push when actions required" (permission prompts and questions).
  - Pushes are skipped while the user is focused on the terminal. `CLAUDE_CLIENT_PRESENCE_FILE` extends that presence suppression.
  - Permission prompts and AskUserQuestion stay open until answered. Other forwarded dialogs expire after 5 minutes.
  - Source: same page, "Mobile push notifications" and "Limitations".
- **Limitation.** "Local process must keep running": closing the terminal or app takes the session offline — same page.
- **Channels (research preview).**
  - A *channel* is an MCP server plugin that pushes chat messages into a running local session. Telegram and Discord use bot tokens and polling. iMessage reads `~/Library/Messages/chat.db` (needs Full Disk Access) and replies via AppleScript.
  - Sender allowlists are bootstrapped via pairing codes.
  - "Channel servers that declare the permission relay capability can forward these prompts to you so you can approve or deny remotely… Anyone who can reply through the channel can approve or deny tool use in your session."
  - Source: [code.claude.com/docs/en/channels](https://code.claude.com/docs/en/channels).
- Anthropic's own feature table also contrasts this with "Self-hosted environments" (cloud sessions on org-run runners) and Slack — [remote-control docs](https://code.claude.com/docs/en/remote-control) line ~299–301.

### Cited findings — OpenAI Codex remote / ChatGPT mobile
- **Launch and scope [snippet].** Preview on 14 May 2026 inside the ChatGPT app. From the phone you can start tasks, read terminal output, inspect diffs, approve risky commands, switch models and get notifications. Sessions keep running on the user's machine — [OpenAI blog](https://openai.com/index/work-with-codex-from-anywhere/), [Neowin](https://www.neowin.net/amp/openai-is-bringing-codex-to-the-chatgpt-mobile-apps-on-ios-and-android/).
- **Official docs [snippet].** "use the ChatGPT mobile app with a connected Mac or Windows device… A secure relay layer keeps trusted machines reachable across your authorized ChatGPT devices without exposing them to the public internet. Remote sessions use the host's own files, credentials, permissions, and plugins, and approval controls still apply." — [developers.openai.com/codex/remote-connections](https://developers.openai.com/codex/remote-connections).
- **Source code.**
  - Codex's app-server has a `remote_control` transport.
  - It enrolls at `wham/remote/control/server/enroll`, refreshes at `.../refresh`, pairs at `.../pair` and `.../pair/status` (with a `pairing_code` and a `manual_pairing_code`), then holds a `wss://` WebSocket to `.../wham/remote/control/server`.
  - Allowed hosts are restricted to `chatgpt.com`, `*.chatgpt.com` and staging (or localhost).
  - Large messages are segmented: 100 KB target segments, 150 KB max, 100 MB reassembled max.
  - Source: `codex/codex-rs/app-server-transport/src/transport/remote_control/protocol.rs` lines 193–240, `segment.rs` lines 19–23 — [openai/codex](https://github.com/openai/codex).
- **Mac mini detection.** Codex explicitly detects a **Mac mini host**: `MAC_MINI_HOST_DEVICE_KIND = "mac_mini"` is sent as header `x-codex-host-device-kind`, derived from `system_profiler` "Mac mini" — `remote_control/host_device.rs` lines 1–40. A daemon crate exists too (`codex-rs/app-server-daemon/src/remote_control_client.rs`, `update_loop.rs`, `thread_recovery.rs`).
- **No visible E2EE.** A grep for `noise|x25519|chacha` in `app-server-transport` and `app-server-daemon` returned nothing. A third-party blog describes "QR pairing + Noise relay" **[snippet]** — [codex.danielvaughan.com](https://codex.danielvaughan.com/2026/06/26/codex-remote-ga-qr-pairing-noise-relay-digitalocean-plugin-remote-first-development/). The two conflict. The open-source host code shows only TLS WebSocket to chatgpt.com.
- **Platform and region conflict [snippet].** One blog says macOS-only at launch and no EU/UK. The official docs say Mac or Windows.

### Cited findings — Cursor Remote Control (iOS app)
- **[snippet]**
  - You run `/remote-control` in an agent on your computer, which hands the session to a worker on the machine.
  - "The agent loop runs in Cursor's cloud, and every tool call (terminal commands, file edits, tests, and git) runs on your computer". The repo, secrets and credentials stay local.
  - Requires the machine to be awake and the workspace to be Git-backed. Team and Enterprise need admin enablement.
  - The iOS app is in public beta on paid plans, with push notifications for finished, needs-input and ready-for-review. There is no Android ETA.
  - Sources: [Cursor docs](https://cursor.com/docs/cloud-agents/mobile), [buildfastwithai](https://www.buildfastwithai.com/blogs/cursor-remote-agents-any-device-2026), [releases.sh](https://releases.sh/release/rel_STi3jW6nvPqWkFMe8-9vi-cursor-launches-ios-mobile-app-for-cloud-agents-with-remote-control).
  - The cursor.com fetch failed with DNS errors, so this is unverified on the page itself.

### Cited findings — Happy (happy.engineering, OSS)
- MIT, "Copyright (c) 2026 Happy Coder Contributors".
- Components: the mobile app (Expo; iOS, Android, web), the original CLI (`npm i -g happy`, then `happy claude` / `happy codex`), and `happy-server`, "the relay server for encrypted sync". A newer desktop app and the "Happy Agent" runtime live in separate repos. Now multi-provider (Claude, Codex, Grok) and "natively multiplayer".
- Source: `happy/README.md` lines 1–80, `happy/LICENSE` — [slopus/happy](https://github.com/slopus/happy).
- **E2EE design.**
  - "Keep the server blind to user content (end-to-end encryption on clients)."
  - Legacy variant: NaCl secretbox (XSalsa20-Poly1305) with a shared secret.
  - Current variant: per-session and per-machine **AES-256-GCM data keys**, wrapped with `tweetnacl.box` using an ephemeral keypair and stored as a `dataEncryptionKey` bundle. The server persists ciphertext in Postgres.
  - Source: `happy/docs/encryption.md` lines 1–155.
- **Auth and pairing.**
  - Public-key challenge-signature auth (`POST /v1/auth {publicKey, challenge, signature}`).
  - "Terminal auth request" flow: the CLI posts its public key, and the already-logged-in phone approves via `POST /v1/auth/response`. This is the QR pairing — `happy/docs/api.md` lines 13–37.
  - The Show HN post says keys are generated on the phone and paired with the terminal **[snippet]** — [Show HN](https://hn.svelte.dev/item/44904039).
- **Transport.**
  - One Socket.IO endpoint `/v1/updates` with `user-scoped` (app), `session-scoped` (one agent process) and `machine-scoped` (daemon) sockets.
  - RPC from phone to machine is routed via rooms `rpc:<userId>:<method>`. The server waits briefly for reconnect before failing a call.
  - Redis streams adapter for multi-replica deployments.
  - Source: `happy/docs/realtime-sync-and-rpc.md` lines 9–60.
- **Daemon.** The CLI runs a background daemon that spawns sessions and keeps machine state in sync (`daemon.state.json`) — `happy/docs/cli-architecture.md` lines 3–44.
- **Push.**
  - Expo push (`expo-server-sdk`), sent from the CLI (`packages/happy-cli/src/api/pushNotifications.ts` line 3, 128–155) and from the server (`packages/happy-server/sources/app/push/pushDispatch.ts`).
  - Only rich session events are pushed ("It's ready!", permission, question). Per-message pushes were removed because they produced "one buzz every 10s".
  - Push is suppressed if a UI client reports `app-state: active`. A `PushOutcome` is returned so "a total push outage" can't stay invisible (it previously went unnoticed "for two months").
  - Source: `pushDispatch.ts` lines 1–22.
- **Permissions.** Phone-selectable modes are `default | acceptEdits | bypassPermissions | plan | read-only | safe-yolo | yolo`, carried in encrypted message metadata and in the socket envelope — `happy/docs/permission-resolution.md` lines 10–60.
- **Handoff.** Pressing any key on the computer's keyboard takes control back from the phone **[snippet]** — [gitee mirror README](https://gitee.com/masx201/happy).

### Cited findings — Omnara
- The original product was a Python wrapper streaming Claude Code CLI messages to the phone. It was deprecated as "fragile" and rewritten on the Claude Agent SDK as a headless daemon. That version could resume a local session in the cloud if the machine went offline **[snippet]** — [PyPI omnara](https://pypi.org/project/omnara/), [Launch HN via brianlovin](https://brianlovin.com/hn/46991591).
- **Current repo.**
  - Apache-2.0, written in Go. It describes itself as "The open-source managed agent platform… A self-hostable alternative to Claude Managed Agents and OpenAI's Agents API."
  - Source: `omnara/README.md` lines 1–40, `omnara/LICENSE` — [omnara-ai/omnara](https://github.com/omnara-ai/omnara).
- **Machines model.**
  - "Every machine runs the same small daemon, `omnarad`, which connects outbound to the control plane. You do not need to open inbound ports…" and "**the machine does not own the agent**. Agents live in the control plane as event logs; machines are execution environments they can attach and release. Disconnecting a machine does not kill the agent."
  - Machine states are `online | asleep | offline`. BYO machines and cloud sandbox pools (Daytona, Modal and others) are interchangeable.
  - Source: `omnara/docs/machines/overview.mdx` lines 1–40.
- BYO machines register with a one-time machine token via `npx omnara machines create-local`. Per-machine `secret_env` injects secrets — `omnara/docs/machines/connect.mdx`.

### Cited findings — Perplexity "Personal Computer" (Mac mini)
- **[snippet]** Announced 11 March 2026.
  - Runs a persistent agent on a dedicated Mac mini 24/7, combining local resources with Perplexity's cloud.
  - Can read and write files in designated folders and works with iMessage, Mail and Calendar.
  - Remote-controllable, with logs and an emergency stop.
  - Max tier ($200/month) or waitlist.
  - Sources: [Gigazine](https://gigazine.net/gsc_news/en/20260312-perplexity-personal-computer), [letsdatascience](https://letsdatascience.com/news/perplexity-turns-mac-mini-into-local-ai-agent-83b6fcf8), [gend.co](https://www.gend.co/blog/perplexity-personal-computer-mac-mini). Mostly vendor-adjacent coverage, and the architecture details are not verified.

### Inferences
- There are three architectural splits. Relic should pick one deliberately:
  - **(A) Everything local, phone is a thin client over a relay.** Claude Code RC, Codex, Happy, OpenClaw.
  - **(B) Brain in the cloud, hands on the machine.** Cursor, and Omnara's current design. This is resilient to the laptop sleeping, but the model context leaves the device.
  - **(C) Brain and hands local, with optional cloud failover.** Omnara's earlier "resume in cloud".
- Vendor relays authenticate with the vendor account and terminate TLS, so the vendor can see content. Happy's "blind relay" (client-held AES keys wrapped per device) is the only surveyed design with true E2EE plus a public relay. It is also self-hostable. This is a differentiator Relic can copy.
- Codex detects a Mac mini host, and Perplexity sells a Mac-mini agent. Vendors are treating an always-on Mac mini as a first-class "agent server" device.
- Push hygiene lessons:
  - Push only on decision-required or done events.
  - Suppress pushes when the user is present.
  - Surface push-delivery failures.

### Gaps
- Warp, Termius-style SSH apps and ChatGPT desktop "work with apps" were not researched, due to the tool-call budget.
- Perplexity Comet was covered only through prompt-injection security reports. LayerX "BioShocking" and the Zenity calendar-invite to 1Password exfiltration show agent browsers using the user's logged-in context **[snippet]** — [The Decoder](https://the-decoder.com/a-calendar-invite-is-all-it-took-to-hijack-perplexitys-comet-browser-and-steal-1password-credentials/), [Brave](https://brave.com/blog/comet-prompt-injection/).
- I found no primary documentation of a "take over" button in ChatGPT agent or Comet.
- I could not confirm whether Codex's relay is E2EE. The code suggests TLS only, a blog claims Noise.

---

## 3. Connectivity options for phone → home box

### Takeaway
There are four practical options, in order of how often they appear in the surveyed products:
1. **Outbound WebSocket or long-poll from the host to a relay.** Used by Claude, Codex, Cursor, Happy and Omnara. It works on every network and needs no user setup.
2. **A private overlay**, Tailscale or Headscale. Used by OpenClaw.
3. **SSH tunnel.** A power-user fallback.
4. **Cloudflare Tunnel or Access.** OpenClaw supports it.

P2P (Iroh) is viable as an optimisation, but it still needs relays and does not solve iOS backgrounding.

### Cited findings
- **Tailscale on iOS.** The iOS client adds a default on-demand rule so the tunnel returns after restarts and crashes. Custom VPN On Demand rules are available since Tailscale 1.48 — [Tailscale docs](https://tailscale.com/kb/1291/ios-vpn-on-demand?tab=ios).
- **Headscale.** "self-hosted, open source alternative to the Tailscale control server… single Tailnet, suitable for personal use". The iOS and macOS GUI clients are proprietary Tailscale apps — [pkg.go.dev headscale](https://pkg.go.dev/github.com/juanfont/headscale).
- **Iroh.**
  - QUIC connections dialed by public key, with automatic NAT traversal and hole punching. Hole punching works roughly 9 times out of 10. Otherwise traffic goes through "encrypted, stateless" relays, which also help with address discovery.
  - Supports iOS, with Swift bindings mentioned **[snippet]**.
  - Sources: [iroh FAQ](https://docs.iroh.computer/about/faq), [iroh 1.0 roadmap](https://iroh.computer/blog/the-road-to-iroh-1-0).
  - I found no iOS-specific backgrounding guidance.
- **OpenClaw's matrix of options.** Loopback plus Tailscale Serve, tailnet bind, SSH tunnel with a client-managed `sshTarget`, pinned `wss://` with certificate fingerprint, or Cloudflare Access. Device tokens are scoped per route — `docs/gateway/remote.md` lines 20–120.
- **Claude Code Remote Control.** Outbound HTTPS polling only, port 443 — [remote-control docs](https://code.claude.com/docs/en/remote-control).

### Inferences
- For Relic the lowest-friction default is an outbound connection from Mac to relay, with E2EE à la Happy. Tailscale or Iroh direct paths can be an optional "LAN/P2P fast path". Requiring users to install Tailscale is acceptable only for power users. OpenClaw's audience tolerated it; consumers will not.

### Gaps
- I did not find Iroh or Tailscale battery and background measurements on iOS.

---

## 4. iOS constraints: APNs, background execution, keeping a session

### Takeaway
An iPhone cannot hold a persistent connection to the home box in the background. Every surveyed product connects while in the foreground, and uses APNs alert pushes to bring the user back for approvals. Silent or background pushes are throttled and unreliable, so approvals must be user-visible alerts.

### Cited findings
- **Apple DTS (forums) [snippet]:**
  - "Notifications sent at low priority (priority 5) are throttled, regardless of payload. Background push notifications are always sent at low priority."
  - "you may expect up to several background push notifications per hour across all apps on a device… it is entirely possible… that you may receive none at all."
  - Background pushes are never delivered if the app was force-quit or not launched for a while.
  - The device budget resets every 24 h.
  - The debugger disables throttling.
  - Apple recommends a Notification Service Extension.
  - Sources: [forum 757094](https://developer.apple.com/forums/thread/757094), [forum 745188](https://developer.apple.com/forums/thread/745188), [forum 760244](https://developer.apple.com/forums/thread/760244).
- **OpenClaw.** "iOS may suspend these foreground connections after the app enters the background." It uses silent push, BGTaskScheduler and significant-location wakes to send short "alive" beacons, and notes that "iOS decides when they actually execute" — `docs/platforms/ios.md` ~284, 641–647.
- **watchOS.** OpenClaw's direct watch node "uses short HTTPS polls… does not maintain a generic background connection" — `docs/platforms/ios.md` ~569.
- **APNs credentials.** These belong to the app publisher. Hence OpenClaw's hosted relay, Happy's use of Expo's push service, and the vendor-hosted push for Claude, Codex and Cursor — see sections 1 and 2.

### Inferences
- Relic should do the following:
  - Send *alert* pushes (priority 10, possibly the time-sensitive interruption level) for approvals, with notification actions (Approve/Deny) where the action is low-risk.
  - Open the app for anything requiring authentication.
  - Keep the agent fully autonomous on the Mac, never relying on the phone being connected.
  - Maintain a durable outbox and inbox on both sides, as OpenClaw's 48 h outbox does.
- If push content must be E2EE, use a Notification Service Extension to decrypt the payload on the device. Note that Happy's server-side push currently sends plaintext title and body, as inferred from `pushDispatch.ts` constructing `title`/`body` server-side. That is a leak in an otherwise E2EE design.

### Gaps
- I did not verify official Apple documentation numbers for limits, or the time-sensitive and critical alert entitlements.

---

## 5. UX patterns: approvals, live view, takeover, queues, schedules

### Takeaway
The common UX vocabulary is:
- an **approval inbox** with pending counts;
- **push only on needs-input or done**;
- **permission modes** chosen per session from the phone;
- **QR pairing**;
- **multi-session server or worktree isolation**;
- **scheduled automations**;
- **"press a key on the computer to take back control"**.

Live screen preview and remote takeover for passwords and 2FA are largely *absent*. Products instead route logins to the user doing them manually on the host browser profile, or to a secret-entry prompt that the model never sees.

### Cited findings
- **Approvals.**
  - OpenClaw: native approval inbox plus per-session question or approval badges — `docs/platforms/ios.md` lines 60–75.
  - Claude Code: permission prompts stay open until answered, and there is a "Push when actions required" toggle — [remote-control](https://code.claude.com/docs/en/remote-control).
  - Codex: approve risky commands from the phone **[snippet]**.
  - Claude Code channels: permission relay over Telegram, Discord or iMessage — [channels](https://code.claude.com/docs/en/channels).
- **Permission modes from the phone.** Happy offers `default/acceptEdits/plan/read-only/safe-yolo/yolo` — `happy/docs/permission-resolution.md`. Claude RC has `--permission-mode` for server sessions.
- **Concurrency and queues.**
  - Claude RC server mode: up to 32 sessions, with optional per-session git worktrees.
  - OpenClaw: Workboard, session snooze and wake, a durable offline outbox — `docs/platforms/ios.md`.
  - Omnara: agents as control-plane event logs that can re-attach to machines — `omnara/docs/machines/overview.mdx`.
- **Schedules.** OpenClaw `automations`/`cron`, heartbeat and standing orders — `docs/automation/cron-jobs.md`. Claude Code "Scheduled tasks" are referenced from the channels page — [channels](https://code.claude.com/docs/en/channels).
- **Credentials and takeover.**
  - OpenClaw: manual login in the host `openclaw` Chrome profile, and a `secrets` tool for typing credentials into a trusted prompt — `docs/tools/browser-login.md`, `docs/tools/secrets.md`.
  - Happy: press any key at the terminal to retake control **[snippet]**.
- **Live view.**
  - OpenClaw's iOS node exposes "Screen snapshot", but that is the *phone's* screen, as a node capability.
  - I found no surveyed product streaming the Mac's screen to the phone for live takeover.
  - Neko (`clones/neko`, WebRTC virtual browser) exists in the clones dir but was not analysed here.

### Inferences
- Live Mac-screen streaming plus phone takeover for 2FA and passwords is an open gap and a potential Relic differentiator. Possible building blocks: a WebRTC stream of an agent-owned browser or virtual display, plus a passkey or OTP handoff.
- If Relic builds it, it should be scoped to an agent-owned browser profile rather than the full desktop. That limits the blast radius, especially given the prompt-injection credential-theft research on Comet and Atlas.

### Gaps
- I did not verify Cursor and Codex mobile UX screens first-hand (DNS blocked).
- I did not find ChatGPT agent's "take over browser" behaviour in a primary source.

---

## Blocked sources
- `openai.com/index/work-with-codex-from-anywhere/`: WebFetch failed (getaddrinfo ENOTFOUND). Snippet only.
- `developers.openai.com/codex/remote-connections.md`: WebFetch failed (ENOTFOUND). Snippet only, partly compensated by reading the openai/codex source.
- `cursor.com/docs/cloud-agents/mobile`: WebFetch failed (ENOTFOUND). Snippet only.
- Perplexity Personal Computer, Comet takeover: no primary Perplexity page fetched (budget).
- Warp, Termius, ChatGPT desktop "work with apps": not searched (budget).
- Apple developer documentation on APNs priorities and interruption levels: forum snippets only.
