# Home Agent Computer Security: Risks and Best Practices (as of Oct 2026)

Scope: a personal AI agent on a home computer that the user reaches from a phone and that logs into the user's accounts. The aim is to inform the safe design of Relic's "home agent computer".

Method note: about 16 search and fetch calls. Several primary sources (koi.ai, simonwillison.net, insiderllm.com) failed DNS resolution from this environment, so many findings come from search-result summaries of primary pages or from secondary coverage. Each finding is marked by how it was sourced. Treat figures marked "vendor" or "secondary" with caution.

## Q1. Documented incidents: exposed agent gateways, MCP servers, Ollama, prompt-injection exfiltration, malicious plugins and skills

### Takeaway
2025–2026 produced a clear pattern of incidents. Self-hosted agent gateways and model servers were left reachable from the internet, often without auth: OpenClaw/Clawdbot/Moltbot exposure was reported at tens of thousands to more than 100,000 instances, and Ollama at 1,100 to 25,000 or more depending on the source. One-click token theft worked even against loopback-bound gateways (CVE-2026-25253). Agent "skill" and MCP marketplaces were used to distribute infostealers and backdoors (ClawHavoc, postmark-mcp). Indirect prompt injection reliably turned browser and messaging agents into data-exfiltration tools (Comet OTP theft, WhatsApp MCP).

### Cited Findings

**OpenClaw / Clawdbot / Moltbot (same codebase, renamed)**
- January 2026: more than 1,100 publicly reachable Clawdbot gateway and control instances were found via Shodan and Censys. Many had no authentication, which could expose API keys and conversation history. Another source cites 1,673+ exposed gateways. — [breached.company](https://breached.company/over-1-000-clawdbot-ai-agents-exposed-on-the-public-internet-a-security-wake-up-call-for-autonomous-ai-infrastructure/); [Brandefense](https://brandefense.io/blog/unmanaged-shadow-ai-agent/)
- SlowMist flagged multiple unauthenticated public instances. It also said several code flaws could lead to credential theft and RCE. Decrypt reported that the Moltbot code is the same as Clawdbot's, so the problems carried over. — [Decrypt](https://decrypt.co/es/356247/clawdbot-moltbot-anthropic-hackeo-token-vulnerabilidades-seguridad/)
- Default gateway port 18789. Attackers query Shodan for live servers and then try to steal keys or tokens. In some cases commands ran with root privileges. — [DSCI threat advisory Jan 2026](https://www.dsci.in/files/content/advisory/2026/threat-advisory-january-2026.pdf)
- Later exposure counts: one source reports 40,000+ instances with unsafe defaults. It also says SecurityScorecard scans later found 135,000+ internet-exposed instances, of which 12,800+ were directly exploitable via the patched RCE. — secondary, via search summary of [Mothasa Substack](https://mothasa.substack.com/p/the-most-popular-ai-agent-on-github) and [clawdocs.org](https://clawdocs.org/security/known-vulnerabilities). I could not reach SecurityScorecard's original report; the figures are unverified.
- **CVE-2026-25253 (CVSS 8.8)**, a one-click RCE:
  - Root cause: the Control UI took a `gatewayUrl` query parameter without validating it and auto-connected on page load, which sent the stored auth token to an attacker-chosen host.
  - Follow-on: with the token, an attacker could connect to the gateway and change settings such as the sandbox and tool policies.
  - Loopback did not protect: it was exploitable even on loopback-bound instances, because the victim's browser makes the connection (cross-site WebSocket hijacking).
  - Fix: version 2026.1.29 (January 30, 2026), which now requires the user to confirm a new gateway URL. Discovered by Mav Levin (depthfirst). Public PoC available.
  - — [The Hacker News](https://thehackernews.com/2026/02/openclaw-bug-enables-one-click-remote.html); [SOCRadar](https://socradar.io/blog/cve-2026-25253-rce-openclaw-auth-token/); [HivePro](https://www.hivepro.com/threat-advisory/one-click-to-compromise-inside-openclaws-critical-rce-flaw/); [Endor Labs](https://www.endorlabs.com/vulnerability/cve-2026-25253); [GitLab advisory](https://advisories.gitlab.com/pkg/npm/clawdbot/CVE-2026-25253/). The sources disagree on whether prior authentication to the Control UI was needed: Endor says yes, HivePro says no.
- **ClawHavoc (malicious ClawHub skills):**
  - Koi Security audited 2,857 skills and found 341 malicious ones. 335 used a fake "Prerequisites" step that told users to install the macOS Atomic Stealer (AMOS).
  - Later counts: 1,184+ malicious skills confirmed by February 16, 2026 per one source; Bitdefender put it near 900 out of about 10,700 skills.
  - ClawHub responded with VirusTotal scanning of uploads and a reporting mechanism. Critics say it is still an unvetted supply chain. Guidance: treat skills installed before mid-February 2026 as untrusted.
  - — search summary of [Immersive Labs](https://www.immersivelabs.com/resources/c7-blog/openclaw-what-you-need-to-know-before-it-claws-its-way-into-your-organization), [eastondev](https://eastondev.com/blog/en/posts/ai/20260227-openclaw-security-alert/), [AI Incident Database](https://incidentdatabase.ai/reports/6951/). Koi's primary post was unreachable.

**Malicious MCP servers and tool poisoning**
- **postmark-mcp** (September 2025), the first malicious MCP server found in the wild:
  - The npm package copied the legitimate Postmark MCP server and added one line that BCC'd every outgoing email to the attacker.
  - The backdoor arrived in v1.0.16 (September 17, 2025), after 15 clean versions.
  - Scale: more than 1,643 downloads; Koi estimated about 500 affected organizations. Postmark was not involved.
  - Removing the package from npm does not remove it from machines that already installed it.
  - — [The Register](https://www.theregister.com/2025/09/29/postmark_mcp_server_code_hijacked/); [CSO Online](https://www.csoonline.com/article/4064009/trust-on-mcp-takes-first-in-the-wild-hit-via-squatted-postmark-connector.html); [Dark Reading](https://www.darkreading.com/application-security/malicious-mcp-server-exfiltrates-secrets-bcc)
- **Invariant Labs, WhatsApp MCP exploit** (April 2025):
  - A malicious co-installed MCP server poisoned its tool descriptions so the agent would send the user's WhatsApp history out through WhatsApp itself. This evades DLP because it looks like normal agent behavior.
  - A second variant needed no malicious server: a single injected WhatsApp message was enough to leak the contact list.
  - Tool poisoning means instructions hidden in tool descriptions, which the model sees and the user normally does not. "Rug pulls" are a related risk: a tool description changes after the user has approved it.
  - — [Invariant Labs](https://invariantlabs.ai/blog/whatsapp-mcp-exploited); [Docker blog](https://www.docker.com/blog/mcp-horror-stories-whatsapp-data-exfiltration-issue/); [Simon Willison](https://simonwillison.net/2025/Apr/9/mcp-prompt-injection/)
- **Exposed MCP servers:**
  - SANS ISC (July 2026) saw active scanning for MCP servers and AI-assistant credential files in honeypot logs, a category it had not seen documented before. It notes that an exposed MCP server is a machine-readable inventory of everything the agent can do. — [SANS ISC diary 33150](https://isc.sans.edu/diary/33150)
  - Aviatrix (July 2026) describes a similar scanning campaign. Its write-up is generic and unsourced. — [Aviatrix](https://aviatrix.ai/threat-research-center/mcp-server-ai-assistant-credential-scanning-july-2026)
  - A vendor blog cites a July 2025 Knostic scan that found 1,862 MCP servers, and a February 2026 audit finding 41% (214) of registry servers with no auth. — [MCP Playground (vendor; unverified)](https://mcpplaygroundonline.com/blog/mcp-server-security-complete-guide-2026)

**Ollama exposed on the internet**
- Cisco Talos (September 2025) found 1,100+ publicly reachable Ollama servers via Shodan. About 20% were actively serving models with no access control. Cisco noted that Ollama ships without authentication and that its default deployment offers little security guidance. — [Cisco blog](https://blogs.cisco.com/security/detecting-exposed-llm-servers-shodan-case-study-on-ollama); [BankInfoSecurity](https://www.bankinfosecurity.com/exposed-llm-servers-expose-ollama-risks-a-29354)
- Later counts: Trend Micro reported 10,000+. An April 2026 Shodan query returned 25,000+. A Twingate marketing post claims about 175,000 (unverified). CVE-2024-37032 ("Probllama") is an RCE triggered by a single HTTP request. — [Twingate (vendor)](https://www.twingate.com/blog/ollama-server-exposure); [Korben](https://korben.info/en/ollama-14000-ai-servers-exposed-internet.html)

**Prompt injection exfiltration from browser and messaging agents**
- Brave versus Perplexity Comet (August 2025): hidden text in a Reddit comment made Comet's assistant go to Gmail, read a one-time password, and post it back into the comment thread. The sources conflict on whether it was fully fixed. — [The Decoder](https://the-decoder.com/brave-discovers-a-security-flaw-in-perplexitys-comet-browser/); [Simon Willison](https://simonwillison.net/2025/Aug/25/agentic-browser-security/)
- Johann Rehberger (Embrace The Red), "Month of AI Bugs" (August 2025):
  - Daily disclosures across ChatGPT, Codex, Anthropic MCPs, Cursor, Amp, Devin, OpenHands, Claude Code, Copilot and Jules.
  - Findings included exfiltration channels, RCE, and getting Devin to run a command-and-control payload ("ZombAIs").
  - Later (November 2025): "cross-agent privilege escalation", where agents on one machine rewrite each other's config.
  - — [Simon Willison, "Summer of Johann"](https://simonwillison.net/2025/Aug/15/the-summer-of-johann/); [DEF CON SG talk PDF](https://media.defcon.org/DEF%20CON%20SG%201/DEF%20CON%20SG%201%20main%20stage%20presentations/Johann%20Rehberger%20-%20The%20Month%20of%20AI%20Bugs%20Lessons%20Learned%20Exploiting%20AI%20Computer-Use%20and%20Coding%20Agents.pdf)
- Anthropic's own red-teaming of Claude for Chrome (August 2025):
  - Prompt-injection attack success was 23.6% without mitigations and 11.2% with them, across 123 cases in 29 scenarios.
  - On a set of browser-specific attacks (hidden DOM fields, URL or tab-title injection), mitigations cut success from 35.7% to 0%.
  - Willison called 11.2% "still a catastrophic failure rate."
  - — [Anthropic](https://www.anthropic.com/news/claude-for-chrome); [Simon Willison](https://simonwillison.net/2025/Aug/26/piloting-claude-for-chrome/)
- OpenAI's CISO called prompt injection "a frontier, unsolved security problem" (Atlas launch, October 2025). — [Simon Willison quoting Dane Stuckey](https://simonwillison.net/2025/Oct/22/openai-ciso-on-atlas/)

### Inferences
- Running on a home box does not make it safe. CVE-2026-25253 shows that a localhost web UI plus a browser on the same machine can be attacked through cross-site WebSocket hijacking. Any local control UI needs strict Origin checks and must never auto-connect to a URL taken from a query parameter.
- Skill and plugin marketplaces are the main supply-chain risk. A store of community skills that can run shell commands or tell the user to install things is a malware distribution channel.
- Exfiltration through legitimate channels (email BCC, WhatsApp messages, posting comments) defeats network DLP. Controls must sit at the action and policy layer, not only at the network layer.

### Gaps
- SecurityScorecard's 135k figure, Koi's original ClawHavoc report and Bitdefender's count could not be checked against primary sources (domains unreachable or not searched).
- I found no confirmed reports of mass credential dumps from exposed OpenClaw gateways, only exposure and exploitability.
- I found no public data on incidents specifically involving an agent on a home machine logging into a victim's bank or email accounts and being exploited in the wild, beyond research PoCs.

## Q2. Design defenses for a phone-reachable home agent

### Takeaway
The consistent guidance:
- Never expose the agent on an inbound port. Use loopback, a tailnet or SSH tunnel, or an outbound-only relay, and require explicit device pairing.
- Keep credentials out of the model's context (vault-injected autofill with per-use human approval).
- Use a dedicated, isolated browser profile and sandbox.
- Add approvals for high-risk actions, origin and site allowlists, and audit logs.
- Most importantly, break the "lethal trifecta" structurally: CaMeL, dual-LLM, or a critic model. Model-level detection alone still fails about 1 time in 10.

### Cited Findings

**Network exposure and pairing**
- OpenClaw's official docs:
  - The Gateway WebSocket listens on 127.0.0.1:18789 by default. Binding beyond loopback requires a shared-secret token or password, or a trusted-proxy setup; newer revisions refuse to start without one.
  - Tailnet and LAN clients need explicit pairing approval; only direct loopback is auto-approved.
  - Remote access is recommended via SSH tunnel or Tailscale.
  - — [docs.openclaw.ai/network](https://docs.openclaw.ai/network)
- Community hardening guidance: bind to loopback, enable token or password auth, lock down file permissions, use Tailscale or a firewall rather than port forwarding, and run in a VM, container or devbox limited to one directory. — [Brandefense](https://brandefense.io/blog/unmanaged-shadow-ai-agent/); [glama.ai hardening doc (community, not official)](https://glama.ai/mcp/servers/@sandraschi/clawd-mcp/blob/e1377496603552204a25c38bdae1d4a28b48f16f/docs/SECURITY_HARDENING.md)
- After CVE-2026-25253, OpenClaw requires the user to confirm any new gateway URL, and advisories recommend rotating tokens after exposure. — [Endor Labs](https://www.endorlabs.com/vulnerability/cve-2026-25253); [HivePro](https://www.hivepro.com/threat-advisory/one-click-to-compromise-inside-openclaws-critical-rce-flaw/)

**Credentials kept out of the model (agentic autofill)**
- 1Password Secure Agentic Autofill (October 8, 2025, early access with Browserbase):
  - Credentials are injected straight into the browser only when a person approves.
  - It uses a new protocol on the Noise Framework, giving an end-to-end encrypted channel between the approving device and the extension.
  - The LLM never sees the secrets. It covers TOTP and keeps an audit trail. Admins define which logins an agent may use.
  - These claims are the vendor's own; I found no independent audit.
  - — [1Password blog](https://1password.com/blog/closing-the-credential-risk-gap-for-browser-use-ai-agents); [BusinessWire](https://www.businesswire.com/news/home/20251008408822/en); [Browserbase](https://www.browserbase.com/1password); [Dark Reading](https://www.darkreading.com/identity-access-management-security/1password-addresses-critical-ai-browser-agent-security-gap)

**Browser-agent vendor guidance**
- Anthropic, Claude for Chrome:
  - Requires user approval before high-risk actions (purchases, publishing, sharing sensitive data).
  - Per-site permissions, and default blocks on financial, adult and pirated-content sites.
  - Classifiers for suspicious instruction patterns.
  - — [Anthropic](https://www.anthropic.com/news/claude-for-chrome)
- OpenAI, Atlas:
  - "Logged-out mode" lets the agent act without the user's credentials, recommended when no in-account action is needed; logged-in mode is for narrow tasks on trusted sites.
  - "Watch mode" (no detail found on how it works).
  - Red-teaming with a reinforcement-learning-trained automated attacker, then adversarial training.
  - — [Simon Willison quoting OpenAI CISO](https://simonwillison.net/2025/Oct/22/openai-ciso-on-atlas/); [Zenity Labs](https://labs.zenity.io/p/hardening-atlas-the-relentless-challenge-of-securing-an-untrusted-browser-agent)
- Google Chrome agentic security (December 2025):
  - A "User Alignment Critic": a separate model that sees only metadata about proposed actions, never untrusted web content, and can veto actions that are off-task.
  - "Agent Origin Sets", which extend Site Isolation so the agent can only interact with origins relevant to the task. Without them an agent is effectively a Site Isolation bypass.
  - User confirmation for critical steps, real-time threat detection, and red-teaming.
  - — [Google blog](https://blog.google/security/architecting-security-for-agentic/); [The Hacker News](https://thehackernews.com/2025/12/google-adds-layered-defenses-to-chrome.html)

**Architectural patterns**
- Lethal trifecta (Simon Willison, June 2025): an agent that combines private data, exposure to untrusted content, and a way to communicate externally can be made to exfiltrate. The mitigation is to remove at least one of the three. — [simonwillison.net/2025/Jun/16/the-lethal-trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) (page unreachable from this environment; definition is well established and consistent with the cited Comet and WhatsApp cases)
- CaMeL (Google, Google DeepMind, ETH Zurich, "Defeating Prompt Injections by Design", arXiv 2503.18813):
  - How it works: a privileged LLM writes a plan (code) from the trusted user query only. A quarantined LLM parses untrusted data and has no tool access. A custom interpreter tracks data provenance (capabilities) and checks policies before each tool call, so injected text cannot change control flow.
  - Results: on AgentDojo it solves 77% of tasks with provable security, versus 84% undefended; one review cites 67% from an earlier version.
  - Limits: the authors say it does not cover every vector.
  - Code: github.com/google-research/camel-prompt-injection.
  - — [arXiv](https://arxiv.org/pdf/2503.18813)
- Tool poisoning and rug-pull defenses implied by Invariant's research: pin and review tool descriptions, re-approve when they change, and avoid co-installing untrusted MCP servers next to sensitive ones (WhatsApp, email). — [Invariant Labs](https://invariantlabs.ai/blog/whatsapp-mcp-exploited); [Simon Willison](https://simonwillison.net/2025/Apr/9/mcp-prompt-injection/)
- Supply chain: postmark-mcp shared the same name and 15 clean versions with the trusted package before turning malicious, so version pinning plus review of diffs on update matters. — [The Register](https://www.theregister.com/2025/09/29/postmark_mcp_server_code_hijacked/)

### Inferences (recommended Relic architecture, synthesized from the above)
1. **No inbound ports.** The home box makes only outbound connections, to a relay or a tailnet (Tailscale or WireGuard). Bind any local UI to loopback and enforce Origin/Host checks plus CSRF protection on WebSockets. This is the lesson of CVE-2026-25253.
2. **Device pairing with keys and E2EE.** Pair the phone to the box by QR code or code exchange, storing per-device keypairs in the Secure Enclave or StrongBox. Encrypt phone-to-box traffic end to end so the relay sees only ciphertext, similar to 1Password's Noise-based channel. Make every paired device revocable, and list them.
3. **Per-action approvals on the phone,** signed with the device key. Require them for: sending messages or emails, purchases, posting, new recipients, credential use, changes to settings or sandbox policy, and installing skills. Show a human-readable diff or preview of each action.
4. **Credential handling.** Use a vault (1Password or Bitwarden agent integration, or the OS keychain) to inject credentials into the browser and never into the LLM context. Prefer passkeys and keep the passkey ceremony with the user on the phone. Gate TOTP behind approval.
5. **A separate agent browser profile** (ideally a separate OS user or VM), never the user's everyday profile. Logged-out by default; log in per site, task by task, following Atlas's model. Keep an origin allowlist per task, following Chrome's Agent Origin Sets.
6. **Sandbox.** Run the agent runtime in a VM or container with no access to the host home directory. Apply an egress allowlist per tool. Separate high-trust tools (email, messages, bank) from content-reading tools.
7. **Break the trifecta.** A planner sees only the trusted user request. Untrusted content goes to a quarantined parser with no tools. A policy engine checks data-flow before any external send (CaMeL), plus an optional alignment-critic model (Chrome).
8. **Skills and plugins.** Use a curated, signed registry. Pin versions, show the permission manifest at install, re-prompt when tool descriptions or permissions change, and never let a skill tell the user to "install a prerequisite".
9. **Audit log and kill switch.** Keep an append-only log of every tool call and credential use, viewable from the phone. A one-tap kill switch revokes tokens, stops the agent and locks the vault. Add rate limits on sends, purchases and logins.

### Gaps
- I found no published Bitwarden agent-autofill details, and no OS-keychain agent APIs, in this pass.
- I did not get Trail of Bits or Zenity primary guidance beyond the Zenity Atlas piece. No authoritative benchmark of dual-LLM versus critic effectiveness in real home-agent setups was found.
- I found no details on Atlas "watch mode" mechanics.

## Q3. Account safety: bans, lockouts, device verification and keeping a human in the loop

### Takeaway
Platform risk is real but thinly documented:
- ToS clauses on automation are common, and X is reported to permanently suspend accounts for non-API automation.
- Amazon v. Perplexity produced a March 2026 preliminary injunction under the CFAA, centered on an agent accessing logged-in accounts without identifying itself. The Ninth Circuit reportedly vacated it in August 2026.

Running from the user's own home machine and residential IP is likely lower-risk than cloud browsers, but login, 2FA and device verification should stay human-driven.

### Cited Findings
- Amazon v. Perplexity (Comet shopping agent):
  - March 2026: the district court granted a preliminary injunction, finding Amazon likely to prevail under the CFAA. The claim centered on the agent accessing Amazon in a logged-in state without identifying itself as an AI agent. — [Cooley](https://www.cooley.com/news/insight/2026/2026-03-17-court-finds-ai-agent-may-violate-state-federal-law-by-accessing-amazon-accounts-without-authorization)
  - August 4, 2026: the Ninth Circuit reportedly vacated the injunction. — [JD Supra author page summary](https://www.jdsupra.com/authors/max-bernstein1/online-platforms/) (appellate reasoning not verified)
- Major SaaS ToS commonly prohibit automated account creation (advocacy source). — [anon.com](https://anon.com/blog/agent-signups-tos-violations-legal-risk)
- Platform automation rules differ:
  - Non-API automation of X "may result in the permanent suspension of your account."
  - Meta does not ban automation outright but restricts high-frequency automated activity.
  - — [Blotato guide, Aug 2026](https://www.blotato.com/blog/ai-agent-social-media-ban-rules)
- A conference anecdote describes an agent workflow that drew an account-ban warning from a model provider. — [AI Engineer World's Fair 2026 talk](https://www.ai.engineer/talks/26RtyAm9y_Q-dark-arts-web-automation-teaching-agents-use)
- OpenAI recommends logged-out mode by default, and logged-in mode only for narrow tasks on trusted sites. — [Simon Willison quoting OpenAI CISO](https://simonwillison.net/2025/Oct/22/openai-ciso-on-atlas/)
- 1Password's design keeps a human approving each credential and TOTP use. — [1Password](https://1password.com/blog/closing-the-credential-risk-gap-for-browser-use-ai-agents)

### Inferences
- A home box with the user's own residential IP and a stable, persistent browser profile should trigger fewer "new device or location" checks than cloud browsers. But a fresh agent profile still looks like a new device, so the first login per site should be done or approved by the user, ideally completing the device verification flow live via the phone (remote view or approval).
- Push 2FA prompts, SMS codes, CAPTCHAs and "Is this you?" challenges to the user instead of having the agent solve or bypass them. Bypassing them is both a ToS and a CFAA-adjacent risk, given the Amazon v. Perplexity framing around non-identification.
- Rate-limit and humanize volume (posting, messaging, purchases), keep per-platform allowlists, and consider identifying the agent where platforms support it (e.g., agent user-agent or Web Bot Auth). Prefer official APIs or OAuth connectors over UI automation for platforms with strict automation bans (X).
- Lockouts are an availability risk too. Ensure the user keeps their primary recovery methods (passkeys, recovery codes) off the agent box.

### Gaps
- I found no primary documentation from Google, Apple, Meta or banks on how they treat AI-agent logins or device verification for agents. I also found no data on ban rates for agent-driven logins from home machines.
- Web Bot Auth / agent identification standards were not researched in this pass.
- The Ninth Circuit reasoning in Amazon v. Perplexity is unverified.

### Blocked sources
- https://www.koi.ai/blog/clawhavoc-341-malicious-clawedbot-skills-found-by-the-bot-they-were-targeting — DNS failure (ENOTFOUND)
- https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/ — DNS failure (ENOTFOUND); content known only from search snippets
- https://insiderllm.com/guides/openclaw-security-report-january-2026/ — DNS failure (ENOTFOUND)
- I did not open embracethered.com, brave.com/blog/comet-prompt-injection, or SecurityScorecard and Bitdefender primary reports; their details come via secondary coverage.
