# iPhone Frontier Ideas for Relic: Feasibility, Policy, Prior Art (validated October 2026)

Scope: seven iPhone design ideas for Relic, a local-first app that records the user's own activity on their own devices, with consent. This covers only sanctioned APIs and App Review policy. Nothing here bypasses iOS security or App Review. Research date: 2026-10-17. The App Review Guidelines page fetched today shows "Last Updated: October 16, 2026."

Summary verdicts (details below):

| # | Idea | Feasible? | Policy risk | Novelty |
|---|---|---|---|---|
| 1 | Broadcast-extension "eyes" + PiP/Live Activity guidance | Partly | Medium (PiP for non-video is a gray area) | Low for "AI sees screen" (Gemini Live, ChatGPT); medium for a persistent overlay that guides steps |
| 2 | Local VPN domain log + Screen Time usage | Partly (domains yes, but not per app; Screen Time data can't be exported) | Medium-high (5.4 VPN rules; Family Controls entitlement) | Low (Lockdown, DDG ATP) |
| 3 | Keyboard that logs the user's own typing | Partly (no secure fields; some apps opt out) | Medium-high (4.4.1 "only to enhance keyboard functionality") | Low-medium (BiAffect logs metadata only) |
| 4 | Cloud plans, local executes (placeholders) | Yes | Low | Low: active 2025-26 research area (CaMeL, PAPILLON, PlanTwin, PAAC) |
| 5 | Surprise-based retention | Yes (an algorithm question) | None | Medium: surprise-based segmentation exists for LLM context, but applying it to lifelog retention is sparse |
| 6 | On-device LoRA training on iPhone | Partly (MLX Swift can train; Apple FM adapters cannot be trained on device) | Low | Medium |
| 7 | "Follow the power" device cluster | Partly (Mac-to-Mac yes; the iPhone is a weak member) | Low | Low-medium (exo, MLX/JACCL; FL charging gating) |

---

## 1. "Eyes, voice, hands" co-pilot (ReplayKit broadcast extension + PiP / Live Activities)

### Takeaway
Partly feasible. A user-started Broadcast Upload Extension can receive screen frames, but it runs under a hard memory ceiling of about 50 MB. The main app is usually suspended while the user is in other apps, so it can't be relied on to process frames, which means OCR has to run inside the extension or be deferred. A floating guidance surface through non-video PiP is technically possible with `AVSampleBufferDisplayLayer`, but Apple has given no explicit approval for it. Live Activities are the safer surface for showing guidance.

### Cited Findings
- Developers report the broadcast extension has a "hard limit of 50MB." ReplayKit's own memory spikes, plus backed-up sample buffers (up to 8 on iPhone 7, 6 on iPad Pro), can push an extension using under 25 MB of its own over the limit. The practical budget may be about half the nominal limit when processing lags. — [Apple Dev Forums 651367](https://developer.apple.com/forums/thread/651367); [Fora Soft](https://www.forasoft.com/blog/article/how-to-implement-screen-sharing-in-ios-1193)
- Vision text recognition has a "fast" path with low memory and an "accurate" path that uses neural networks and is heavier. Language correction adds time and memory. A region of interest reduces the work. — [WWDC19 234 notes](https://wwdcnotes.com/notes/wwdc19/234/); [Apple: Recognizing text in images](https://developer.apple.com/documentation/vision/recognizing-text-in-images)
- Apple's iOS 27 Foundation Models framework lets the model call Vision tools such as OCR on-device ("Vision framework tools like OCR and barcode readers are available for your model to call directly, all on-device"). — [Apple WWDC26 iOS guide](https://developer.apple.com/wwdc26/guides/ios/)
- Communication between the extension and the app: a backgrounded main app is "almost always suspended or terminated," so the recommended channel is a shared App Group file container. — [Apple Dev Forums 755758](https://developer.apple.com/forums/thread/755758). Apple DTS (Quinn): iOS won't resume an app to deliver a Darwin notification, and a terminated app never gets it. — [Apple Dev Forums 769398](https://developer.apple.com/forums/thread/769398). Darwin notifications carry no payload. — [Fleksy](https://www.fleksy.com/blog/communicating-between-an-ios-app-extensions-using-app-groups)
- A developer reports a broadcast extension's socket transfer stopping once the main app went to the background; there was no confirmed fix. — [Apple Dev Forums 802718](https://developer.apple.com/forums/thread/802718)
- PiP with custom content: the public `AVPictureInPictureController.ContentSource(sampleBufferDisplayLayer:playbackDelegate:)` accepts any sample buffers. A developer asked in 2026 whether a "Float Note" (non-video) PiP would pass review and got no Apple reply. — [Apple Dev Forums 839424](https://developer.apple.com/forums/thread/839424); [Apple: Adopting PiP in a custom player](https://developer.apple.com/documentation/avkit/adopting-picture-in-picture-in-a-custom-player)
- A tutorial says PiP must be started only from user input, or App Review will reject the app. — [Kodeco](https://www.kodeco.com:443/24247382-picture-in-picture-across-all-platforms)
- App Review 2.5.14: "Apps must request explicit user consent and provide a clear visual and/or audible indication when recording, logging, or otherwise making a record of user activity. This includes any use of the device camera, microphone, screen recordings, or other user inputs." 2.5.4: background services may be used "only... for their intended purposes." — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- Live Activities render through a WidgetKit extension. Local starts happen when the app calls `Activity.request()` in the foreground, and remote updates go through ActivityKit push. — [Adobe tutorial](https://developer.adobe.com/client-sdks/edge/adobe-journey-optimizer/live-activities/ios/tutorial); [Apple: ActivityKit push](https://developer.apple.com/documentation/activitykit/starting-and-updating-live-activities-with-activitykit-push-notifications)
- Prior art: Gemini Live on iPhone shares the screen through the standard iOS "Start Broadcast" prompt (rolled out 2025). — [9to5Google](https://9to5google.com/2025/05/29/gemini-live-camera-iphone/); [TechRadar](https://www.techradar.com/computing/artificial-intelligence/gemini-live-is-now-free-for-everyone-on-android-and-ios-and-you-can-finally-share-your-screen-and-camera-on-iphone). ChatGPT Advanced Voice added screen sharing in Dec 2024. — [WhatPlugin newsletter](https://newsletter.whatplugin.ai/p/voice) (secondary)

### Inferences
- The proven pattern is "AI sees screen through a broadcast extension, talks back by voice." Gemini and ChatGPT both stream frames to the cloud. Relic's distinguishing feature would be on-device OCR plus a persistent guidance overlay.
- Voice output is the most reliable "hands" channel. A foreground audio session in the main app keeps that app alive while the broadcast runs, so it can receive text from the App Group and speak it. This plausibly also legitimizes the audio background mode, but it needs to be tested and justified to App Review: 2.5.4 says background audio must be for its intended purpose.
- For OCR inside the extension: downscale frames, throttle to about 1 fps, use `.fast` recognition with language correction off, and write only text and hashes to the App Group.
- Live Activity updates likely have to come from the main app (or push), not the broadcast extension. This is unverified; see Gaps.
- To meet 2.5.14, the system's red recording indicator plus an in-app consent screen probably suffice for screen capture.

### Gaps
- No Apple source confirms the exact memory cost of `VNRecognizeTextRequest`, or of iOS 26's `RecognizeTextRequest`, inside a 50 MB extension. This needs profiling.
- No Apple statement exists on non-video PiP (forum question unanswered). Apple's PiP docs and guidelines contain no explicit text on it.
- Unconfirmed whether ActivityKit `Activity.update` can be called from a broadcast upload extension.

### One-day test
Build a minimal app with a Broadcast Upload Extension. In `processSampleBuffer`, downscale frames to 720p and run fast OCR once per second, logging `os_proc_available_memory()`. Write recognized text to an App Group file. The main app holds a `.playback` audio session, polls the file every second, and speaks a canned "next step" with AVSpeechSynthesizer while also updating a Live Activity. Run it on the largest iPad and iPhone available for 30 minutes across Safari and Settings. Measure extension jetsam kills, OCR latency, and whether the main app stays alive. As an optional variant, add a user-tapped PiP showing rendered text and submit to TestFlight external review to get an early read on policy.

---

## 2. "Skeleton now, flesh later": local VPN domain log + Screen Time

### Takeaway
Partly feasible. An on-device `NEPacketTunnelProvider` or local DNS proxy can log the domains the device queries and when, without decryption, which is how Lockdown works. It cannot attribute flows to the app that made them unless the device uses per-app VPN, which in practice means MDM. Screen Time APIs can show per-app usage, but only inside a sandboxed `DeviceActivityReport` extension that cannot export data. Apple confirms this is by design. The policy load is significant: Guideline 5.4 requires an organization account and an on-screen data declaration before use, and forbids any data use or disclosure.

### Cited Findings
- 5.4 verbatim: "Apps offering VPN services must utilize the NEVPNManager API and may only be offered by developers enrolled as an organization. You must make a clear declaration of what user data will be collected and how it will be used on an app screen prior to any user action to purchase or otherwise use the service. Apps offering VPN services may not sell, use, or disclose to third parties any data for any purpose… Parental control, content blocking, and security apps, among others, from approved providers may also use the NEVPNManager API." — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- 4.10: apps may not monetize built-in Apple capabilities, including "Screen Time APIs." — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- Lockdown (open source, last commit Mar 2025): `PacketTunnelProvider` sets tunnel DNS to `127.0.0.1` with `matchDomains = [""]`, runs a local dnscrypt-proxy, and writes a blocklist to the shared container. It is a DNS-level on-device firewall, not a packet decryptor. — Source read in clone of [confirmedcode/Lockdown-iOS](https://github.com/confirmedcode/Lockdown-iOS) (`Lockdown Tunnel/PacketTunnelProvider.swift`). The App Store listing says the firewall "doesn't connect to any servers." — [App Store](https://apps.apple.com/us/app/lockdown-privacy-adblock-vpn/id1469783711)
- DuckDuckGo App Tracking Protection (Android) uses a local VPN, so no app data goes to DDG. It cannot run alongside a real VPN, and individual apps can be excluded. — [TechRadar](https://www.techradar.com/news/duckduckgo-now-wants-to-help-protect-your-android-phone); [MobileSyrup](https://mobilesyrup.com/2022/01/16/duckduckgos-app-tracking-protection-is-worth-trying-despite-issues/)
- On iOS, source-app information in a packet tunnel exists only in per-app (source-app routing) mode. In the default destination-IP routing it is absent, and per-app VPN is typically configured through MDM. — [Apple Dev Forums 794762](https://developer.apple.com/forums/thread/794762); [113826](https://developer.apple.com/forums/thread/113826); [736537](https://developer.apple.com/forums/thread/736537)
- Content filters (`NEFilterDataProvider`) on iOS require supervised devices unless used with Family Controls. The filter sandbox blocks network, IPC, and disk writes. Since iOS 16, `sourceAppIdentifier` reports a generic WebKit identifier for browser flows. — [Apple Dev Forums 709500](https://developer.apple.com/forums/thread/709500); [NEFilterProvider docs](https://developer.apple.com/documentation/networkextension/nefilterprovider); [719755](https://developer.apple.com/forums/thread/719755)
- DeviceActivityReport docs: "your extension runs in a sandbox. This sandbox prevents your extension from making network requests or moving sensitive content outside the extension's address space." Apple DTS (Quinn) says the read-only sandbox is intentional. Writes to the App Group silently do nothing. — [Apple Dev Forums 818297](https://developer.apple.com/forums/thread/818297); [736351](https://developer.apple.com/forums/thread/736351); [817516](https://origin-devforums.apple.com/forums/thread/817516)
- Workaround reported by developers: a `DeviceActivityMonitor` extension can write coarse threshold-crossing events, such as "app category X hit N minutes," to the App Group. On iOS 26.x, thresholds have been reported firing early or immediately (FB18061981). — [Apple Dev Forums 818297](https://developer.apple.com/forums/thread/818297); [838510](https://developer.apple.com/forums/thread/838510); [840907](https://developer.apple.com/forums/thread/840907)

### Inferences
- A domain-plus-timestamp "skeleton" is achievable. Relic would need to (a) enroll as an organization, (b) show a pre-use declaration screen, (c) state in the privacy policy that the log never leaves the device, and (d) accept that it occupies the device's single VPN slot, so it conflicts with the user's real VPN.
- Without app attribution, the "skeleton" is "device-wide DNS," and app identity has to be inferred from domain patterns. The data is noisier than DDG ATP on Android, which gets per-app UIDs.
- Screen Time can serve as an on-screen visualization inside Relic, through the report extension, but it cannot be a data source for Relic's memory store. Coarse threshold events from the Monitor extension are the only sanctioned export path, and they are unreliable on iOS 26.

### Gaps
- No Apple statement on whether a "personal logging" local VPN, as opposed to blocking/security, qualifies as an "approved provider" use under 5.4. Review is case by case.
- Whether iOS 27 changed the DeviceActivityReport sandbox: the WWDC26 iOS guide does not mention Screen Time.

### One-day test
Fork the structure of Lockdown's tunnel, without executing that code, into a minimal `NEPacketTunnelProvider` that routes DNS to a local resolver stub and appends `(timestamp, qname)` to an App Group SQLite file. Use the device for a normal day. Measure battery delta against a control day, the number of unique domains, and the share of domains that map clearly to an app. Separately, build a DeviceActivityMonitor with 15-minute thresholds on three apps and log when events arrive against actual Screen Time, to quantify the early-firing bug.

---

## 3. Custom keyboard that logs the user's own typing

### Takeaway
Partly feasible, with high policy and trust risk. The keyboard never sees secure text fields or phone pads, and any app can refuse custom keyboards. Without Full Access the keyboard can't share a container with its app, so local logging into Relic needs Full Access. Guideline 4.4.1 allows collecting user activity "only to enhance the functionality of the user's keyboard extension," which makes "general lifelog of typing" a likely rejection. Logging metadata only (BiAffect-style) or feeding typing into keyboard features is easier to defend.

### Cited Findings
- 4.4.1: keyboards must "Remain functional without full network access and without requiring full access" and "Collect user activity only to enhance the functionality of the user's keyboard extension on the iOS device." — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- "When a user taps in a secure text input object, the system temporarily replaces your custom keyboard with the system keyboard." Phone pad fields behave the same way. Apps can reject all custom keyboards with `application:shouldAllowExtensionPointIdentifier:`, for example banking or HIPAA apps. — [Apple App Extension Programming Guide: Custom Keyboard](https://developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/CustomKeyboard.html)
- "By default, a keyboard has no network access and cannot share a container with its containing app"; `RequestsOpenAccess` enables both. Apple's guidance: "do not store received keystroke or voice data beyond the time needed to provide text back to the user or to provide features that you explain to the user," and treat the lexicon as private. — [same guide](https://developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/CustomKeyboard.html)
- Keyboard extension memory is about 48 MB according to React Native docs; community estimates range from about 30 to 50 MB. — [React Native docs](https://reactnative.dev/docs/next/app-extensions); [Fleksy](https://fleksy.com/blog/limitations-of-custom-keyboards-on-ios)
- Prior art: BiAffect (UIC, NIMH-funded) ships an iOS custom keyboard that collects "keystroke metadata—such as typing speed, errors, and pauses—but not typed content." A JAMIA study used more than 14M keypresses from 250 users. — [App Store](https://apps.apple.com/us/app/-/id6451423106); [PMC7647317](https://pmc.ncbi.nlm.nih.gov/articles/PMC7647317)

### Inferences
- "Explained features" is the opening in Apple's guidance. If Relic's keyboard visibly uses the user's history to power autocomplete or "recall what I typed," storing text for that purpose fits 4.4.1 better than a passive archive does.
- Coverage is structurally incomplete: no passwords, no phone numbers, and none of the opted-out apps (banks, health). Users also often switch back to the system keyboard. Expect partial capture.
- The trust cost is high. The Full Access prompt warns users that keystrokes may be transmitted. Typed text from third parties, such as replies quoting others, raises secondary-consent issues.

### Gaps
- No public App Review precedent was found for a keyboard whose main purpose is personal typing archival.
- No official Apple number for keyboard memory.

### One-day test
Build a minimal keyboard with `RequestsOpenAccess`. It inserts characters and records per-session metadata (app-agnostic: session length, word count, timestamp), plus optional text into an App Group store behind an in-keyboard "recording" indicator. Use it for a day. Measure the percentage of text fields where it appears versus is replaced by the system keyboard, peak memory, and how often the user manually switches away. Draft the App Review notes explaining the "recall what I typed" feature.

---

## 4. Cloud plans, local executes (CaMeL-style placeholders)

### Takeaway
Feasible and well-trodden in research. CaMeL already separates a planner that sees only the user query from a quarantined model that handles data. PAPILLON, PlanTwin, PAAC and MemPrivacy (2024-2026) specifically target "local model as privacy proxy for cloud model," including typed placeholders that are resolved on-device. Apple's iOS 27 Foundation Models framework now accepts third-party cloud LLMs (Claude, Gemini) and PCC, which makes it a natural host. Novelty is low as an idea; the differentiation is in applying it to a personal lifelog store.

### Cited Findings
- CaMeL (Google/DeepMind/ETH): a Privileged LLM turns the user query into Python control flow and "sees only the user query." A Quarantined LLM parses untrusted data into a schema with no tool access, and an interpreter enforces capability-based data-flow policies. It solves 77% of AgentDojo tasks with provable security, against 84% undefended (earlier version: 67%). — [Simon Willison](https://simonw.substack.com/p/camel-offers-a-promising-new-direction); [MIT 6.858 reading](https://css.csail.mit.edu/6.858/2026/readings/camel.pdf). The code is released as a research artifact: "The interpreter implementation likely contains bugs… not a Google product… not planning to… maintain" (README, last commit Jun 2025). — [google-research/camel-prompt-injection](https://github.com/google-research/camel-prompt-injection)
- PAPILLON (NAACL 2025): "privacy-conscious delegation," with a local model proxying to an API model. On the PUPA benchmark (901 instances) it keeps 85.5% response quality with 7.5% privacy leakage, using Llama-3.1-8B local plus GPT-4o-mini. — [ACL Anthology 2025.naacl-long.173](https://aclanthology.org/2025.naacl-long.173)
- PlanTwin (arXiv 2603.18377, Mar 2026): projects the local environment into a sanitized abstract graph for a cloud planner, with a local gatekeeper enforcing disclosure budgets. Evaluated on 60 agentic tasks. — [UTS repository](https://opus.lib.uts.edu.au/handle/10453/195550)
- PAAC (arXiv 2605.08646, May 2026): "the cloud agent reasons over typed placeholder tokens that preserve each sensitive value's reasoning role while discarding its content"; a deterministic registry substitutes and reverses them on-device. MemPrivacy (May 2026) does the same for edge-cloud agent memory. — [paperswithcode.co entry](https://paperswithcode.co/paper/2605.08646) (found via search snippet; full text not fetched)
- Apple iOS 27: "You can now work with any language model, including Apple Foundation Models, cloud models like Claude and Gemini, or any other provider that conforms to the Language Model protocol." "Dynamic Profiles let you swap models, tools, and instructions on the fly." Small Business Program apps with fewer than 2M downloads get the next-gen Apple model on PCC "at no cloud API cost." — [Apple WWDC26 iOS guide](https://developer.apple.com/wwdc26/guides/ios/)
- PCC design claims: stateless computation, enforceable guarantees, no privileged runtime access, non-targetability, verifiable transparency (attestations plus a public transparency log). The guide was updated in July 2026. — [Edgeless Systems summary](https://www.edgeless.systems/blog/apple-private-cloud-compute-core-concepts-and-an-open-alternative); [ConductAtlas change log](https://conductatlas.com/change/2026-07-07-apple-intelligence-apple-private-cloud-compute-security-guide-3520/) (secondary sources, not Apple's own text)

### Inferences
- Design for Relic: the on-device Foundation Model or MLX model acts as quarantined LLM and placeholder registry. A cloud model (Claude via the FM `LanguageModel` protocol, or PCC) acts as planner over typed handles such as `<PERSON_1>` or `<MEMORY_ITEM_42>`. A local interpreter executes the plan. In CaMeL's threat model the user query itself still reaches the cloud, so Relic should also sanitize the query.
- PCC is the "trusted-cloud" tier. Placeholders matter more for third-party clouds.

### Gaps
- PAAC, MemPrivacy and PlanTwin full texts were not fetched (arxiv.org DNS-blocked here), so their quantitative results are unverified.
- No production iOS app was found that implements placeholder-based cloud planning.

### One-day test
Take 30 real Relic-style requests over a synthetic personal memory store, such as "email the person I met at the cafe Tuesday." Pipeline: an on-device model (FM framework) does NER into a typed placeholder map, a cloud planner (Claude) emits a tool plan over the placeholders, and a local executor resolves them. Score task success against a no-privacy baseline and count leaked raw values, scanning outbound prompts for registry values, in the PAPILLON style of reporting quality and leakage.

---

## 5. Surprise-based retention for lifelogs

### Takeaway
Feasible, since it is an algorithm choice with no platform risk. The ingredients are mature: Bayesian-surprise event segmentation in EM-LLM, surprise-gated memory updates with a forget gate in Titans, and classic lifelog event segmentation and keyframe selection. Directly applying surprise to decide what to retain long-term in a personal lifelog is sparsely covered, so this is Relic's most novel angle among the seven, though small open-source packages are converging on it.

### Cited Findings
- EM-LLM (Fountas et al., ICLR 2025) segments token streams into episodes "using a combination of Bayesian surprise and graph-theoretic boundary refinement in an online fashion," and retrieves by similarity plus temporal contiguity. It beats InfLLM on LongBench and ∞-Bench, works across about 10M tokens with no fine-tuning, and its boundaries correlate with human-perceived events. — [ICLR 2025 proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c05144b635df16ac9bbf8246bbbd55ca-Abstract-Conference.html)
- Titans (Google): long-term memory is a small network trained at test time. Surprise is the gradient of an associative loss, with momentum carrying recent surprise and adaptive weight decay acting as a forget gate. Scales beyond 2M tokens. — [Google Research blog](https://www.research.google/blog/titans-miras-helping-ai-have-long-term-memory/); [PoliTo reading group](https://dbdmg.polito.it/dbdmg_web/reading-group-16-may-2025/)
- Classic lifelogging: Doherty et al. segment SenseCam streams at sharp visual changes and pick one keyframe per event. Bolaños et al. cluster photostreams into events and summarize them for memory reinforcement. Aghazadeh et al. (CVPR 2011) extract novel events from egocentric recordings of daily repeated activities. — [Doherty CIVR 2008](https://doras.dcu.ie/636/1/civr2008-Doherty.pdf); [Bolaños arXiv 1511.00438](https://ar5iv.arxiv.org/html/1511.00438); [egocentric survey](https://arxiv.org/pdf/1501.02825)
- Recent agent-memory work: the "brainmem" PyPI package gates encoding on surprise. An "Activity Frames" preprint (arXiv 2608.05784) compiles screen activity for agent memory. A practitioner reports about 2,000 rows per day of screen-event capture, which motivates compression into episodes. — [PyPI brainmem](https://pypi.org/project/brainmem/); [HackerNoon](https://hackernoon.com/i-compiled-55-days-of-screen-activity-into-episodic-memory-for-my-ai-agent) (low-authority sources)

### Inferences
- A practical Relic design: compute per-event surprise as the negative log-likelihood of the event under an on-device predictive model of the user's routine (or embedding-distance novelty). Keep high-surprise events at full fidelity, compress low-surprise routine events to summaries or counts, and decay raw data. EM-LLM-style boundary detection gives the episode units.
- The novelty claim should be "surprise-gated retention and forgetting for consented personal lifelogs, evaluated on recall utility," not "surprise segmentation," which already exists.

### Gaps
- No study was found that measures whether surprise-gated retention improves a user's later recall or answers in a lifelog QA setting. The Activity Frames and brainmem methods were not verified.

### One-day test
Take one week of existing Relic capture (or a public lifelog such as NTCIR/LSC). Segment it with an embedding-surprise threshold, keep the top 20% of events by surprise plus summaries of the rest, and compare against uniform 20% sampling and recency-only retention. Use 50 self-written questions ("when did I last…", "what was unusual on…"). Report answer accuracy and storage used.

---

## 6. On-device personalization training on iPhone

### Takeaway
Partly feasible. MLX Swift supports LoRA training, and Apple's `LoRATrainingExample` builds for iOS. Memory caps it to small models: the example's 7B 4-bit model needs about 6 GB of physical RAM. Core ML `MLUpdateTask` still exists for small updatable models. Apple's Foundation Models adapter toolkit trains only on a Mac with at least 32 GB or on Linux GPUs, produces about 160 MB adapters, requires an entitlement to deploy, and its last version (26.0.0) is incompatible with OS 27. It is not a viable path for on-device personalization.

### Cited Findings
- mlx-swift-examples `Applications/LoRATrainingExample`: "adds LoRA adapters and trains the model." Its target's `SUPPORTED_PLATFORMS = "iphoneos iphonesimulator macosx xros xrsimulator"`. The Mistral-7B 4-bit model "requires a little over 4G of memory to load and train -- this may require ~6G of physical RAM." It doesn't persist adapters. — Read in clone of [ml-explore/mlx-swift-examples](https://github.com/ml-explore/mlx-swift-examples) (README and project.pbxproj)
- mlx-swift-lm lists LoRA/DoRA and full fine-tuning. — [sourcepulse summary](https://www.sourcepulse.org/projects/25556469)
- FM adapter toolkit: requires a "Mac with Apple silicon and at least 32GB memory, or Linux GPU machines"; "Each adapter will take approximately 160 MB"; "Each adapter is compatible with a single specific system model version"; deploying needs the Foundation Models Framework Adapter Entitlement; "Version 26.0.0 is the last release of this toolkit and is not compatible with macOS, iOS, iPadOS, or visionOS 27 and later." — [Apple: Foundation Models adapter](https://developer.apple.com/apple-intelligence/foundation-models-adapter/)
- iOS 27 introduces Core AI to "load, specialize, and run AI models entirely on-device." The guide does not mention on-device training. — [Apple WWDC26 iOS guide](https://developer.apple.com/wwdc26/guides/ios/)
- Core ML `MLUpdateTask` (iOS 13+) is still documented for updating updatable models on device, and no deprecation notice was found. — [Apple: MLUpdateTask](https://developer.apple.com/documentation/coreml/mlupdatetask); [Model personalization](https://developer.apple.com/documentation/coreml/model-personalization)
- Thermal and power, inference only: iPhones show more than 18 W spikes, sustained draws up to 13.8 W, 47.9°C surface temperature on iPhone 14 Pro, and throttling. MobileFineTuner (arXiv 2512.08211) reports full and LoRA fine-tuning on real phones (GPT-2, Gemma 3, Qwen2.5), with memory and energy as the main constraints. — [alphaxiv 2403.12844](https://www.alphaxiv.org/overview/2403.12844); [alphaxiv 2512.08211](https://alphaxiv.org/overview/2512.08211v1)
- Background GPU: `BGContinuedProcessingTask` GPU access (`.gpu` resource) returned false on every iPhone tested (15 Pro, 16 Pro) in iOS 26; it appears to be iPad-only. Apple has not replied. — [Apple Dev Forums 816774](https://developer.apple.com/forums/thread/816774)

### Inferences
- A realistic iPhone recipe: LoRA (rank 8-16) on a 0.5-1.5B 4-bit model via MLX Swift, trained in the foreground or in short CPU background chunks while charging. Heavier training goes to a Mac (see idea 7).
- The Apple FM adapter route is closed for on-device personalization. A Mac-trained per-user adapter would also need the entitlement and retraining for every OS model version.

### Gaps
- No published measurements of sustained LoRA training energy or thermals on a 2025-26 iPhone. The MobileFineTuner numbers were not read.
- No information on whether Core AI (iOS 27) adds training or fine-tuning APIs; only the guide was checked.

### One-day test
On an iPhone 16 Pro or 17 Pro, adapt `LoRATrainingExample` to Qwen2.5-0.5B-4bit with 200 personal Q/A pairs. Run 300 iterations in the foreground on battery, then again on charger. Log tokens/s, `ProcessInfo.thermalState` transitions, battery percent per 10 minutes, and peak memory. Compare adapter quality against the base model on 30 held-out personal questions.

---

## 7. "Follow the power" personal device cluster

### Takeaway
Partly feasible. Mac-to-Mac clustering is mature: exo, plus MLX distributed with JACCL RDMA over Thunderbolt 5 since macOS 26.2, which Apple presented at WWDC26. The iPhone is a poor cluster member. exo officially supports only Apple-silicon macOS, iPhone background GPU is unavailable, and Handoff moves user activities, not compute. The sanctioned iPhone role is "dispatcher plus opportunistic CPU worker," using `BGProcessingTask` with `requiresExternalPower`. Charging and idle gating has well-known prior art in federated learning such as Gboard.

### Cited Findings
- exo (last commit Oct 13, 2026): "connects all your devices into an AI cluster," with automatic discovery, RDMA over Thunderbolt 5, topology-aware tensor parallelism, MLX backend, and OpenAI/Claude/Ollama-compatible APIs. Its PLATFORMS.md Tier 1 lists only Apple Silicon macOS (M3 Ultra Studio, M4 Pro Mini, M4/M5 MacBook Pro). Linux CUDA and CPU are planned, and iOS is not listed. — Read in clone of [exo-explore/exo](https://github.com/exo-explore/exo)
- WWDC26 session 233: RDMA over Thunderbolt 5 starting with macOS 26.2. JACCL, Apple's open-source collective library, sits on top, and MLX uses it with launch tooling. The demo used 4 M3 Ultra machines. — [Apple WWDC26 video 233](https://developer.apple.com/videos/play/wwdc2026/233/)
- MLX issue #3442 (Apr 2026): `backend="any"` can silently pick ring and run as a single node. — [mirror of MLX issue](https://upd.dev/ml-explore/mlx/issues/3442)
- `BGContinuedProcessingTask` (iOS 26) is for continuing user-initiated work with system progress UI, not automatic maintenance. GPU access is gated by an entitlement, and no iPhone reports support. — [DEV summary](https://dev.to/arshtechpro/wwdc-2025-ios-26-background-apis-explained-bgcontinuedprocessingtask-changes-everything-9b5); [Apple Dev Forums 816774](https://developer.apple.com/forums/thread/816774). Background ML jobs reportedly run 4-5 times slower. — [Apple Dev Forums 807957](https://developer.apple.com/forums/thread/807957)
- Federated learning prior art: Google's Gboard on-device training runs only when the device is idle and on unmetered Wi-Fi. — [eWeek](https://www.eweek.com/de/innovation/google-tests-new-approach-to-training-machine-learning-models/)

### Inferences
- Architecture: the Mac (or a home Mac mini) is the always-on "power" node running exo or MLX. The iPhone captures, queues jobs (embedding, summarization, LoRA) to the Mac over the local network (Network.framework with Bonjour; this triggers iOS's Local Network privacy prompt) or through CloudKit when away. The phone runs only small jobs itself, under `BGProcessingTaskRequest.requiresExternalPower = true`.
- Novelty: "personal multi-device scheduler that routes lifelog AI jobs to whichever owned device is plugged in and idle" combines exo-style clustering with FL-style gating. Neither covers the iPhone as a scheduler-dispatcher for personal-memory jobs, so the novelty is moderate.

### Gaps
- `BGProcessingTaskRequest` docs could not be fetched with content, so `requiresExternalPower` semantics come from general knowledge. Verify against Apple docs.
- No Apple API was found for cross-device compute handoff. Handoff/Continuity (NSUserActivity) is for user-facing activity continuation; no source was fetched for this point.

### One-day test
Run exo or `mlx_lm.server` on one Mac. Build an iPhone app that queues 50 "summarize this capture chunk" jobs and dispatches them over Bonjour to the Mac when it's reachable, falling back to on-device FM-framework summarization inside a `BGProcessingTask` that requires external power. Plug the phone in overnight. Measure completion rate, latency, phone battery and thermal state, and how often iOS actually granted the background task, with timestamps logged.

---

## Blocked sources
- arxiv.org: DNS failure (`getaddrinfo ENOTFOUND`) on WebFetch. This blocked the full texts of PAAC (2605.08646), PlanTwin (2603.18377), Titans (2501.00663), Activity Frames (2608.05784) and MobileFineTuner (2512.08211). Claims about them come from search snippets and secondary summaries.
- emergentmind.com and opentrain.ai: DNS failure (paper mirrors for PAAC).
- developer.apple.com/documentation/uikit/creating-a-custom-keyboard and developer.apple.com/documentation/backgroundtasks/bgprocessingtaskrequest: the JS-rendered pages returned no body. The archived Extensibility guide was used for keyboards; BGProcessingTaskRequest semantics remain unverified.
- Apple's PCC Security Guide (security.apple.com) was not fetched; only secondary summaries were used.
