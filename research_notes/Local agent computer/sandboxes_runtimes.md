# Local "agent computer" sandboxes and runtimes (as of 2026-10-17)

Scope: how to build a persistent, home-hosted "agent computer" (Mac or home Linux box) with its own desktop, browser and apps, operated by an AI agent, with the iPhone acting only as remote control and viewer. This is for Relic's "home agent computer" design.

Method notes: repo facts come from shallow clones (read-only, never executed) under `/tmp/claude-0/-home-user-albers-club/3712d12f-853b-5b60-93d4-c8956af51529/scratchpad/clones/<repo>`. That directory already held earlier clones (OpenHands, software-agent-sdk, claude-cookbooks and others), so it was not empty. New clones were trycua/cua (HEAD 2026-10-16), cirruslabs/tart (2026-10-16), m1k1o/neko (2026-10-16), steel-dev/steel-browser (2026-10-13), apple/containerization, apple/container, budtmo/docker-android, remote-android/redroid-doc, browser-use/browser-use (2026-10-16) and simular-ai/Agent-S (2026-10-08). Paths below are relative to `clones/`. "[snippet]" means the fact rests only on a search-engine summary that I did not open in full.

---

## Q1. Sandboxed desktops/VMs on Apple Silicon (Cua/Lume, Tart, UTM, Virtualization.framework, Apple containerization, Lima/Colima, Docker Desktop) and resource use on a Mac mini

### Takeaway
On a Mac, the most complete open-source base as of Oct 2026 is the Cua stack. It has these parts:
- **Lume:** macOS and Linux VMs on Virtualization.framework (MIT).
- **cua-spacesd:** an in-guest daemon that serves the control API, MCP and H.264/Opus streaming (FSL-1.1-MIT).
- **Cua Driver:** background, no-focus-steal control of host macOS apps (MIT).

Apple's license and Virtualization.framework hard-cap you at **2 concurrent macOS guests per Mac**, so "one macOS agent computer per user" plus Linux containers for browsers is the practical layout. Tart is now owned by OpenAI, and the copy in the repo is still FSL-licensed. Apple's `container` (macOS 26 only) is a credible Docker-free way to run Linux browser containers, with one microVM per container.

### Cited Findings
**Cua (trycua/cua)**
- Cua now ships several pieces:
  - **Cua Spaces:** "a desktop app that gives your agents full desktops… a macOS VM built locally on your Mac, or a Linux or Omarchy image." Spaces run "on your Mac, on other machines you own, and in your own cloud account."
  - **Teleport:** moves a signed-in app (Chrome, Slack) into a Space with sessions kept in an encrypted "Cua Keyvault".
  - **Multiplayer:** "You and your agents work on the same desktop, each with your own cursor. Step in to make a choice, then hand the desktop back."

  Installing Spaces requires macOS 26 or later. Spaces is free for individuals, with Pro at $18/mo and Teams at $30/seat/mo. — `cua/README.md` (Cua Spaces section)
- **Licensing:** "Everything outside Cua Spaces and Cua Driver Bench is MIT-licensed… the cua SDK… Cua Driver, Lume". Cua Spaces (apps, cua-spacesd, Keyvault, teleport, streaming client/codecs/viewers) is source-available under **FSL-1.1-MIT**: "free to use, self-host and build on, with no competing hosted service, and each release becomes MIT two years after it ships." The streaming wire protocol stays MIT. The optional `cua-som` package is AGPL-3.0, and the optional `cua-perception` extension bundles an AGPL OmniParser model. — `cua/README.md` (Licensing section, lines ~267-292)
- **cua-spacesd architecture:**
  - One port, **3211**: gRPC/gRPC-Web services (`System, Process, Filesystem, Computer, Windows, Accessibility, Driver, Stream, Presence, Teleport, Tunnel`), `/mcp` (Streamable-HTTP MCP), `/files`, `/tunnel`, and `/media` plus QUIC on 3212 for H.264 video and Opus audio.
  - It "replaces the former in-image services (computer-server on 8000…) and is not wire-compatible with them."
  - A token is required for any non-loopback bind.
  - `cua-spacesd join --relay wss://…` publishes a machine behind NAT over one outbound WSS connection (yamux), with no inbound port needed.

  — `cua/libs/cua-spacesd/README.md`. (Relic note: the old "computer-server" named in the task brief is superseded.)
- **Hosting on a spare Mac:**
  - The "Host Spaces on a spare Mac" guide supports the cua.ai relay, or **Tailscale/LAN direct mode with no sign-in** (`cua host setup --direct 100.x.x.x:3211`).
  - Default limits: "macOS VMs on one Mac: 2 — Apple's macOS license allows two macOS VMs per Mac, and Apple Virtualization (which Lume runs on) enforces it", and "Spaces at once: 4" (configurable).
  - Every remote create/delete is written to a hash-chained audit log, `~/.cua/host/spaces-audit.jsonl`.

  — `cua/docs/content/docs/start-here/host-spaces-on-your-spare-mac.mdx`
- **Lume requirements:** "Host: Apple silicon, macOS 13 or later; Memory: 8 GB free (16 GB for an 8 GB guest); Disk: 50 GB free per macOS guest plus its restore image; Concurrency: Up to two macOS guests at a time (Apple's limit)". Lume exposes a CLI, a local HTTP API and an MCP server. — `cua/docs/content/docs/lume/index.mdx`
- **Lume unattended setup:** `lume create macos-tahoe --ipsw … --unattended tahoe` creates user `lume` (password `lume`), enables SSH and autologin, and disables sleep and screen lock. Telemetry is **on by default** and can be turned off with `lume config telemetry disable`. — `cua/libs/lume/README.md`
- **Cua SDK runtime matrix:**
  - `Image.linux()` runs as a Docker/Podman rootfs container, using gVisor when `runsc` is present.
  - `Image.macos()` runs as a Lume VM, "local only".
  - `Image.android()` is "Android 14 — Legacy Android emulator adapter" (local only).
  - Without a container engine you are told to "install Colima or Docker Engine".
  - The default sandbox memory in the daemon protocol is 4096 MiB.

  — `cua/docs/content/docs/cua-sdk/reference/runtime-support.mdx`; `cua/docs/content/docs/cua-sdk/reference/protocol/daemon-spaces.mdx`
- **Cua Driver:** "Background computer-use driver for any agents. Speaks MCP over stdio; drives native macOS apps without stealing focus." It needs Accessibility and Screen Recording grants, which macOS attributes to a "responsible app identity". — `cua/libs/cua-driver/README.md` (lines 3, 132, 218)
- Cua's own docs say "Cua Driver operates your host Mac; Lume hosts isolated VMs." [snippet] — [cua.ai comparison](https://cua.ai/docs/cua-driver/guide/getting-started/comparison)

**Tart**
- Tart is "a virtualization toolset to build, run and manage macOS and Linux virtual machines (VMs) on Apple Silicon". It uses Virtualization.Framework and can push and pull VMs from OCI registries. README image links now point at `github.com/openai/tart`. — `tart/README.md`
- The license in the clone is **Functional Source License 1.1, ALv2 Future License**. Permitted purposes include "your internal use and access", but it excludes a "Competing Use". — `tart/LICENSE`
- OpenAI brought the Cirrus Labs team (makers of Tart) into its Agent Infrastructure team, announced 2026-04-07. Reports say Tart, Vetu and Orchard "will adopt more permissive open-source licenses", Cirrus CI shut down on 2026-06-01, and the repo moved to OpenAI's GitHub org. [snippet] — [AI IDE List](https://aiidelist.com/blog/openai-brings-tart-team-into-agent-infrastructure.md), [hyper.ai](https://hyper.ai/en/stories/b3d3a83e59314f2d514382873e0d0610). The clone's LICENSE was still FSL on 2026-10-16, so the announced relicense does not appear in the repo yet.

**Apple Virtualization.framework and the macOS license**
- The macOS SLA §2B(iii) allows up to two additional macOS instances in VMs per Apple computer, for development, testing, macOS Server or personal non-commercial use. It excludes "service bureau, time-sharing, terminal sharing or similar services". Virtualization.framework enforces the cap, so a third concurrent macOS guest fails to start. [snippet] — [Eclectic Light](https://eclecticlight.co/2022/08/04/virtualisation-on-apple-silicon-macs-8-how-apple-limits-vms/), [threedots.ovh](https://threedots.ovh/blog/2020/12/macos-eula-licensing-restrictions-affecting-virtualisation/)

**Apple containerization and `container`**
- **Containerization (Swift package):** "executes each Linux container inside of its own lightweight virtual machine… sub-second start times using an optimized Linux kernel". Clients can give each container a dedicated IP. It supports Rosetta 2 for amd64 images. Building it requires macOS 26 and Xcode 26. It now also has a Linux backend (cloud-hypervisor + KVM). License: Apache-2.0. — `containerization/README.md`, `containerization/LICENSE`
- **`container` CLI:** "create and run Linux containers as lightweight virtual machines on your Mac… supported on macOS 26". It consumes and produces OCI images. License: Apache-2.0. — `container/README.md`
- Memory overhead claims conflict:
  - One source says Apple's approach uses less memory than Docker's shared VM.
  - Another says per-container overhead is slightly higher.
  - A third says memory freed inside the VM is not returned to the host (no full ballooning support).

  [snippet] — [pinggy](https://pinggy.io/blog/apple_container_tool_linux_containers_mac/), [mintlify apple/container](https://mintlify.com/apple/container/architecture/virtualization), [instagit](https://instagit.com/apple/container/what-are-performance-considerations-for-apple-container)
- Docker Desktop runs all containers in one shared Linux VM. Guides put its idle footprint at 2–4 GB or more, but I could not verify those numbers. [snippet] — [macos-tahoe.com guide](https://macos-tahoe.com/blog/apple-container-vs-docker-developer-guide-2026/)

### Inferences
- **Mac mini sizing**, derived from Lume's "16 GB for an 8 GB guest" guidance plus a 4 GB default per Linux sandbox:
  - **16 GB:** one macOS guest at about 6–8 GB, or two or three Linux browser containers; not both comfortably.
  - **24 GB:** one macOS guest (8 GB) plus two or three Linux browser/desktop containers.
  - **32 GB:** two macOS guests, or one macOS guest plus several Linux containers.

  These are inferences, not measured benchmarks.
- For Relic, a sensible default is:
  - a Linux container (Apple `container`, or Colima/Docker) for the agent's persistent browser profile;
  - optionally one Lume macOS guest for macOS-only and iPad apps;
  - avoiding agent control of the user's own logged-in host session except through an explicit "host mode" (Cua Driver).
- The macOS SLA's "service bureau/time-sharing" exclusion suggests a home agent computer is best framed as the user's own personal machine and VM, not a hosted service Relic resells.
- Cua's FSL terms would forbid Relic offering Spaces as a competing hosted service. Self-hosted use on the user's own Mac looks permitted, but this needs legal review.

### Gaps
- No primary benchmark of idle RAM and CPU per Lume macOS guest, Apple `container` or Docker Desktop on an M4 Mac mini.
- UTM and Lima/Colima were not cloned or verified this round. Both are known Virtualization.framework/QEMU front-ends, but this round produced no cited 2026 facts for them.
- I did not open Apple's current macOS 26 SLA text; the clause wording comes from secondary sources.

---

## Q2. Linux desktop and browser containers for agents (Anthropic reference container, OpenHands, E2B, Daytona, Kasm, webtop, neko, Steel, browserless; persistent profiles; CDP)

### Takeaway
For a home box, the strongest Apache/MIT options are:
- **neko** (Apache-2.0): a WebRTC multi-user desktop/browser with built-in takeover.
- **Steel** (Apache-2.0): a CDP browser API with session persistence and a live-view UI.
- **browser-use** (MIT): can attach to a local Chrome profile over CDP.
- **E2B** (Apache-2.0): self-hostable on AWS/GCP via Terraform, but it is cloud-oriented.

browserless is SSPL, and Daytona went closed-source in June 2026 (its last open release was AGPL).

### Cited Findings
- **neko:**
  - It is a "self-hosted virtual browser that runs in Docker and uses WebRTC". It is "not only limited to a browser… you can install a full desktop environment (e.g. XFCE, KDE)", and supports multiple users with "multi-participant control".
  - It lists "Persistent browser — own browser with persistent cookies" and "Automated browser — you can install playwright or puppeteer and automate tasks while being able to actively intercept them."
  - Compared with Guacamole and noVNC it claims "Smooth video because it uses WebRTC and not images sent over WebSockets", plus built-in audio.
  - Its stack references GStreamer, Pion (Go WebRTC), x264 and Xorg.
  - App images include chromium, google-chrome, firefox, brave, microsoft-edge, xfce, kde and vlc.
  - License: Apache-2.0.

  — `neko/README.md`, `neko/LICENSE`, `neko/apps/`, `neko/server/go.mod`
- **Steel browser:**
  - "Uses Puppeteer and CDP for complete control over Chrome instances", with "Session Management: Maintains browser state, cookies, and local storage across requests", extension support, and a debug/live UI.
  - Runs with `docker run -p 3000:3000 -p 9223:9223 ghcr.io/steel-dev/steel-browser`. Mac Silicon users need `DOCKER_DEFAULT_PLATFORM=linux/arm64`.
  - It also advertises "Anti-Detection" stealth plugins, which are out of scope and not researched.
  - License: Apache-2.0.

  — `steel-browser/README.md`, `steel-browser/LICENSE`
- **browser-use:**
  - The Python library is MIT. It can control "a local browser, a Browser Use Cloud browser, or an existing remote browser over CDP".
  - `Browser.from_system_chrome()` reuses a Chrome profile.
  - It records sessions with CDP `Page.screencastFrame`.

  — `browser-use/README.md` (lines ~169, 299, 311), `browser-use/browser_use/browser/watchdogs/recording_watchdog.py`
- **OpenHands:**
  - The main repo is now "OpenHands Agent Canvas", which runs OpenHands, Claude Code, Codex, Gemini and other ACP agents "across local, remote, and cloud backends". Agents can run "on a dedicated computer like a Mac Mini".
  - "Option 1: Without a Sandbox" warns that the agent gets full filesystem access.
  - License: MIT.

  — `OpenHands/README.md`, `OpenHands/LICENSE`
- **Anthropic computer-use reference:** the demo container publishes 5900 (VNC), 6080 (noVNC) and 8501 (Streamlit). I did not verify the official Dockerfile. [snippet] — [nerdleveltech course](https://nerdleveltech.com/courses/claude-computer-use-mastery/learn/development-environment/docker-sandbox)
- **E2B:** its core stack (SDKs, CLI, runtime, Firecracker microVM layer, desktop sandbox) is Apache-2.0. The computer-use desktop is Ubuntu 22.04 with XFCE. Self-hosting is via Terraform to your own AWS/GCP. [snippet] — [e2b.dev/open-source](https://e2b.dev/open-source), [E2B computer use docs](https://www.e2b.dev/docs/use-cases/computer-use)
- **Daytona:** it announced in June 2026 that it was going closed source. The last AGPL-3.0 release was v0.190.0 (2026-06-23). One source says the repo was archived on 2026-10-03, another that it is frozen but forkable. The self-hosted footprint is about 14 containers plus Postgres. [snippet] — [agent37](https://www.agent37.com/blog/daytona-alternative), [helix.ml](https://helix.ml/blog/self-hosted-agent-sandboxes), [selfhostedworld](https://selfhostedworld.com/software/daytona)
- **LinuxServer webtop / Selkies:** Selkies is "the stack behind Webtop", the Chromium/Firefox containers and 100+ single-app containers. It uses WebSockets by default, with opt-in WebRTC (`SELKIES_MODE=webrtc`) carrying video, Opus audio and input over UDP. A TURN relay or reachable ports are needed. [snippet] — [docs.linuxserver.io Selkies WebRTC](https://docs.linuxserver.io/selkies/user-guide/webrtc/)
- **Kasm:** Cua vendors a Kasm-based image under MIT. — `cua/README.md` (third-party licenses), `cua/libs/kasm/`
- **browserless:**
  - Dual-licensed **SSPL-1.0** or commercial.
  - Commercial or closed-source use requires a commercial license.
  - The open Docker image is for open-source projects, prototyping and evaluation.

  [snippet] — [browserless GitHub](https://github.com/browserless/browserless), [browserless self-hosted](https://www.browserless.io/platform/self-hosted)

### Inferences
- **Persistent home browser:** neko (WebRTC view and takeover) plus Playwright/CDP inside the same container gives a "watch and take over" browser with a persistent profile volume, all under Apache-2.0.
- **Agent-friendly API:** Steel adds CDP session management with a UI.
- **Avoid as an embedded dependency:** browserless (SSPL), and Daytona (frozen AGPL).

### Gaps
- I did not clone anthropic-quickstarts, so the computer-use-demo Dockerfile details are unverified.
- The Kasm Workspaces (commercial product) license and the KasmVNC license were not checked.
- No first-hand check of E2B's self-host on a single home box (non-cloud).

---

## Q3. Running real mobile apps locally (Android emulator on Apple Silicon, Redroid/Waydroid, Genymotion; iPad apps on Mac; iPhone Mirroring)

### Takeaway
Android options:
- **Mac:** the Android emulator works with arm64-v8a images on Hypervisor.framework.
- **Linux home box:** Redroid (arm64 and amd64, Android 8.1–16, scrcpy/adb) is the container option.
- **Not on macOS:** docker-android needs Linux with KVM.

iOS options:
- iPhone/iPad apps run on Apple Silicon Macs only when the developer has not opted out. Opt-out is a per-app App Store Connect toggle, and Meta's apps were historically opted out.
- iPhone Mirroring plus macOS Accessibility and OCR is a working but fragile route to driving the user's real iPhone.

### Cited Findings
- **Android emulator on Apple Silicon:** use `arm64-v8a` system images, e.g. `system-images;android-36;google_apis;arm64-v8a`, or the `google_apis_playstore` arm64 images. It runs headless through `sdkmanager`/`avdmanager`. HAXM was removed, and macOS uses Hypervisor.framework. [snippet] — [buildwithmatija](https://www.buildwithmatija.com/blog/android-development-macbook-silicon-2026-baseline), [codersera](https://codersera.com/blog/android-emulators-complete-guide-2026/)
- **Genymotion:**
  - Desktop 3.4 added native Apple Silicon support, and its arm64 images are compatible with "almost all Google Play apps". [snippet] — [Genymotion 3.4](https://rozz.genymotion.com/pages/genymotion-desktop-3-4-is-released.html)
  - Genymotion SaaS is arm64-only from 2026-03-30. [snippet] — [codersera](https://codersera.com/blog/android-emulators-complete-guide-2026/)
- **Redroid:**
  - It is "a GPU accelerated AIC (Android In Cloud) solution" running in Docker, podman or k8s on Linux. It "supports both arm64 and amd64".
  - Images cover Android 8.1 through 16 (incl. 64-bit-only variants).
  - It needs the `binder_linux` and `ashmem_linux` kernel modules, and is viewed with `scrcpy -s localhost:5555`.
  - GMS can be added via Open GApps, MicroG or MindTheGapps.
  - License: Apache, with kernel modules under GPLv2.

  — `redroid-doc/README.md` (lines 16-50, 74-75, 158, 188-192)
- **docker-android (budtmo):**
  - It offers VNC/noVNC (port 6080, `WEB_VNC=true`) and a beta HTTP MCP server.
  - "For OSX and Windows OS user, you need to use Virtual Machine… the image can be run under Ubuntu OS only", and it requires `/dev/kvm`.
  - License: "Custom Apache 2.0 License" with amendments on forks and data processing.

  — `docker-android/README.md` (lines 13, 19, 60-75), `docker-android/LICENSE.md`
- **Waydroid** runs Android as a Linux container that shares the host kernel. Google Play Services are not installed by default. [snippet] — [Waydroid README mirror](https://glassweightruler.freedombox.rocks/gitweb/waydroid.git/blob_plain/3d1a46939bfd4ba32f0e745a5ef6410ade42182b:/README.md)
- **iOS apps on Mac:**
  - Compatible iPhone/iPad apps appear on the Mac App Store for Apple silicon "unless you edit your apps' availability". Developers opt out in App Store Connect, under Pricing and Availability → "iPhone and iPad Apps on Apple Silicon Mac".
  - Apps that depend on unavailable frameworks or hardware cannot be listed.

  [snippet] — [Apple App Store Connect Help](https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/manage-availability-of-iphone-and-ipad-apps-on-macs-with-apple-silicon)
- **Which apps are available:**
  - At the 2020 launch, Facebook kept Instagram, WhatsApp, Messenger and Facebook off Apple-silicon Macs, and Google opted out of YouTube and Maps. [snippet] — [iMore](https://www.imore.com/major-developers-opt-out-mac-app-store-ahead-apple-silicon-launch), [Macworld](https://www.macworld.com/article/675595/new-macs-will-run-ios-apps-but-not-facebook-google-maps-or-youtube.html)
  - Sideloading IPAs was later blocked unless the app is on the Mac App Store. [snippet] — [9to5mac](https://9to5mac.com/?p=691192)
  - WhatsApp now has a native Mac app (Mac App Store since Nov 2023). [snippet] — [Macwelt](https://www.macwelt.de/article/2898097/instagram-fur-ipad-endlich-da-mit-reels-als-start-option.html)
  - Instagram shipped a dedicated iPad app in 2025. I found no source confirming whether Instagram or TikTok are installable on Mac today. [snippet] — [Galaxus](https://www.galaxus.it/en/page/instagram-has-finally-made-it-to-the-ipad-39412)
- **iPhone Mirroring as an agent route:** open-source tools (Phone Harness, mirroir-mcp, iphone-mirror-mcp) drive the real iPhone through macOS iPhone Mirroring using Accessibility and Screen Recording permissions, plus Vision OCR. They need macOS Sequoia+ and a one-time pairing on the phone. "Unlocking the physical phone pauses mirroring", which is a hard limit for unattended use. [snippet] — [scriptbyai Phone Harness](https://www.scriptbyai.com/phone-harness-ai-agent-iphone/), [glama mirroir-mcp](https://glama.ai/mcp/servers/jfarcand/mirroir-mcp), [mcpservers iphone-mirror-mcp](https://mcpservers.org/servers/nickatnight96/iphone-mirror-mcp)
- **Cua's local Android sandbox** is an "Android 14 — legacy Android emulator adapter". Cua also has a QEMU/KVM Android container (`libs/qemu-docker/android`). — `cua/docs/content/docs/cua-sdk/reference/runtime-support.mdx`, `cua/libs/qemu-docker/android/README.md`

### Inferences
- iPhone Mirroring conflicts with Relic's model. If the iPhone is the remote control, the user unlocking it pauses mirroring, so this route only suits occasional, attended use.
- For Android apps, a Mac-hosted Android emulator (arm64 image) is the zero-extra-hardware option. Redroid on a Linux box scales better.
- App ToS and Play Integrity / attestation may block many social and banking apps in emulators. This was deliberately not researched (no evasion research), and Relic should prefer official web or desktop clients and APIs.
- Instagram and TikTok should be assumed unavailable as Mac "iPad apps" unless verified on the Mac App Store. Plan on web clients in the agent browser instead.

### Gaps
- Current (2026) Mac App Store status of Instagram and TikTok iPad apps is unverified.
- No primary Google doc confirming Play Store image licensing in Redroid/Genymotion.
- No measured RAM/CPU for the Android emulator on an M4 Mac mini.

---

## Q4. Live view and takeover (WebRTC, noVNC, CDP screencast, Apple Screen Sharing; latency; how cloud products do "watch live / take over")

### Takeaway
Cloud products expose the agent's own cloud computer and browser for live watching and hand the screen to the human at login or sensitive steps. Locally, the options are:
- **WebRTC:** neko (Pion/GStreamer), or Selkies in webtop.
- **H.264 over WebSocket/QUIC:** cua-spacesd.
- **noVNC:** the simplest but highest-latency option.
- **CDP screencast:** browser-only.

Remote access from the iPhone goes through a relay (Cua relay, Tailscale) rather than inbound ports.

### Cited Findings
- **cua-spacesd streaming:** `OpenMedia` returns a short-lived ticket bound to a target (a display or a single window), codec and policy, and media flows over WebSocket or QUIC. Options include `max_fps`, `codecs=["h264"]` and audio. The decoding client ships with Spaces under FSL, but "the wire contract… is open source, so any client can attach". — `cua/docs/content/docs/spaces/guides/stream-a-desktop.mdx`, `cua/libs/cua-spacesd/README.md`
- **Multiplayer takeover in Cua Spaces:** "each with your own cursor. Step in to make a choice, then hand the desktop back." — `cua/README.md`
- **neko:** WebRTC with multi-participant control and the ability to "actively intercept" Playwright/Puppeteer automation. — `neko/README.md`
- **Evidence on latency:** a 2020 ACM TOMM study found VNC, noVNC and RDP "vulnerable to imperfect network conditions", with longer latency, while WebRTC was "the most robust technology under bad network conditions". noVNC goes through a websockify WebSocket-to-TCP proxy. [snippet] — [NYCU TOMM 2021 PDF](https://people.cs.nycu.edu.tw/~chuang/pubs/pdf/2021tomm.pdf), [xmodulo](https://www.xmodulo.com/access-vnc-remote-desktop-web-browser.html)
- **CDP screencast:** `Page.screencastFrame` is used by browser-use for session recording. — `browser-use/browser_use/browser/watchdogs/recording_watchdog.py`
- **OpenAI dots (announced at DevDay, 2026-09-29):**
  - Each dot "works on its own cloud computer, which users can open at any time to inspect its work". Linking a personal computer is optional and off by default.
  - Custom Rules and auto-review apply, and password changes always stay with the user.
  - Secondary sources only, with some inconsistencies (availability tier).

  [snippet] — [flaviocopes](https://flaviocopes.com/openai-dots/), [betanews](https://betanews.com/article/openai-dots-agents-chatgpt/), [Bloomberg Tax](https://news.bloombergtax.com/private-equity/openai-unveils-always-on-ai-agent-dots-new-500-paid-tier)
- **ChatGPT Work login handoff (release notes 2026-08-25):**
  - ChatGPT shows the site's login screen so the user enters credentials or a code. OpenAI says the model cannot see them.
  - The session can stay signed in, and can be cleared per site under Settings > Cloud browser.
  - The earlier ChatGPT agent asked the user to "take over" the browser for logins and forms.

  [snippet] — [Decrypt](https://decrypt.co/376757/openai-agentic-chatgpt-work-signs-in-without-you), [Crypto Briefing](https://cryptobriefing.com/openai-chatgpt-work-autonomous-login/), [loopcv](https://blog.loopcv.pro/what-is-chatgpt-agent-mode/)
- **xAI Grok Bot (beta around 2026-08-11):** "runs on a persistent cloud computer where it can open a browser, read and write files, run terminal commands"; each bot has its own computer and signs in with the user's credentials. Vendor and aggregator sources only, and dates conflict. [snippet] — [Vellum](https://www.vellum.ai/blog/official-grok-bot-breakdown), [Enterprise DNA](https://enterprisedna.co/resources/ai-pulse/ai-pulse-2026-08-17-xai-ships-grok-bot-always-on-agents-with-their-own-cloud-com), [techjacksolutions](https://techjacksolutions.com/?p=84230)
- **Manus "My Computer" (2026-03-16):** a Manus Desktop app for macOS and Windows that runs CLI commands locally, with per-command approval ("Allow Once" / "Always Allow"). Meta acquired Manus in late 2025. [snippet] — [The Next Web](https://thenextweb.com/news/meta-manus-my-computer-desktop-ai-agent), [GIGAZINE](https://gigazine.net/gsc_news/en/20260317-manus-my-computer)

### Inferences
- **Relic iPhone viewer:**
  - Use WebRTC (neko-style) or H.264 over WebSocket/QUIC (cua-spacesd-style) for the desktop.
  - Use CDP screencast as a cheap fallback for browser-only tasks.
  - Use a relay or Tailscale for NAT traversal. Selkies docs show that WebRTC needs TURN/UDP reachability, not just a reverse proxy.
- **"Take over for login" pattern:** the agent pauses, the human gets input control on the phone, and the session cookie persists in the agent's profile. This matches ChatGPT Work and Cua multiplayer, and it means credentials never pass through the model.
- Apple Screen Sharing/VNC into a Lume guest works for debugging, but it is not a good phone UX.

### Gaps
- No measured glass-to-glass latency numbers for neko, cua-spacesd or noVNC over cellular to an iPhone.
- No official OpenAI or xAI docs were retrieved, so implementation details of their live view are unknown.

---

## Q5. End-to-end open-source "agent computer" projects

### Takeaway
Cua is the closest open-source analogue of a "persistent agent computer". It covers VMs/containers, an in-guest daemon, streaming, a relay, multiplayer and a host-Mac driver. Agent-S, browser-use, OpenHands and UFO2 are agent layers that sit on top of such a computer.

### Cited Findings
- **Cua:**
  - SDK in Python, TS, Swift and Kotlin; `cua sb create ubuntu` (gVisor container).
  - Spaces on your own Mac or hosts; relay or Tailscale; Cua Driver MCP.

  — `cua/README.md`, `cua/docs/content/docs/start-here/host-spaces-on-your-spare-mac.mdx`
- **Agent-S (Simular):**
  - An Apache-2.0 open computer-use agent framework supporting Linux, Mac and Windows.
  - Agent S3 reports 72.60% on OSWorld with Best-of-N (claimed above human level).
  - Simular's hosted Sai claims 73% on OSWorld 2.0 (Aug 2026).
  - A Simular API for "always-on computer agents" launched 2026-10-01.

  These are vendor claims. — `Agent-S/README.md` (lines 10-11, 68-72, 96-123), `Agent-S/LICENSE`
- **browser-use:** an MIT library that drives local Chrome (including the user's real profile) or a remote CDP browser. — `browser-use/README.md`
- **OpenHands Agent Canvas:** a self-hosted, always-on control center for agents, with local, Docker or VM backends (MIT). — `OpenHands/README.md`
- **Microsoft UFO2 (paper arXiv 2504.14603):**
  - Uses a HostAgent with AppAgents, and fuses Windows UIA with vision.
  - Its "Picture-in-Picture" virtual desktop uses an RDP loopback session so the agent and user work simultaneously.
  - One mirror listed PiP as "coming soon", so its shipped status is unclear.

  [snippet] — [Microsoft Research](https://www.microsoft.com/en-us/research/publication/ufo2-the-desktop-agentos/), [alphaxiv](https://alphaxiv.org/overview/2504.14603v2)

### Inferences
- **Recommended Relic home stack:**
  1. **Host:** a Mac mini (24–32 GB) or Linux box.
  2. **Default agent computer:** a Linux container with a persistent Chromium profile volume, neko or Steel for view and takeover, and CDP for agent control.
  3. **Optional:** one Lume macOS guest (count against the 2-VM cap) with cua-spacesd for macOS/iPad apps.
  4. **Optional Android:** an emulator on the Mac, or Redroid on Linux.
  5. **Remote access:** a relay or Tailscale to the iPhone app.

  Build on the MIT pieces (Lume, Cua Driver, SDK, wire protocol), and treat the FSL Spaces components as needing a license check.
- UFO2's PiP (RDP loopback) idea maps onto macOS as "agent works in a separate VM or user session, not the user's foreground desktop". This is the Lume/Space approach.

### Gaps
- Open-Interface was not researched this round, and no data was gathered on its maintenance status.
- No independent evaluation compares Cua Spaces' reliability against neko/Steel for long-lived home use.

---

### Blocked sources
- No fetches failed. WebFetch was not needed, and all repo facts came from clones.
- Not attempted or not retrieved:
  - Official OpenAI dots and ChatGPT Work help pages (search returned only secondary coverage).
  - xAI Grok Bot official docs.
  - Apple's current macOS 26 SLA PDF.
  - anthropic-quickstarts repo (not cloned).
  - Current Mac App Store listings for Instagram/TikTok (no source found).
  - Google Android emulator official docs.
  - UTM, Lima/Colima and Open-Interface repos (not cloned, due to the time budget).
