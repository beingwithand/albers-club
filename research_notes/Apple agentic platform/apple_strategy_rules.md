# Apple AI / Agent Strategy, Partnerships and App Store Rules (as of 17 Oct 2026), for Relic

Method note: only developer.apple.com could be fetched directly in this session. apple.com newsroom, CNBC, Engadget, TheNextWeb, MacRumors, 9to5Mac, MacStories and others were blocked by the proxy (DNS failure or 403). Claims from those outlets come from search-result snippets and summaries, not full-text reads, and are marked as such. Items marked [primary] were read verbatim on developer.apple.com.

## 1. Partnerships: Gemini, ChatGPT, Anthropic/Claude and others, plus Apple's own models

### Takeaway
Apple's next-generation "Apple Foundation Models" are based on Google Gemini under a multi-year deal announced in a joint statement on 12 Jan 2026. Apple still serves the models on its own devices and on Private Cloud Compute (PCC). Anthropic's Claude is a first-class option for developers in two places: as an agent in Xcode 26.3 (via MCP), and as a pluggable provider in the iOS 27 Foundation Models framework, which Apple's own developer page names. Claude or Gemini as a user-selectable Siri backend ("Extensions") was reported by Bloomberg but is unconfirmed by Apple, and sources conflict on whether it shipped.

### Cited Findings
- **Gemini deal (joint statement, 12 Jan 2026):** "Apple and Google have entered into a multi-year collaboration under which the next generation of Apple Foundation Models will be based on Google's Gemini models and cloud technology." Apple said Google's technology "provides the most capable foundation," and that Apple Intelligence "will continue to run on Apple devices and Private Cloud Compute." The statement names a more personalized Siri "coming this year" as the first result. — [Google blog joint statement](https://blog.google/company-news/inside-google/company-announcements/joint-statement-google-apple/) (snippet; full page blocked); [Engadget](https://engadget.com/ai/apples-siri-ai-will-be-powered-by-gemini-153636649.html); [Droid Life](https://www.droid-life.com/2026/01/12/apple-to-use-gemini-to-power-new-features-on-iphone/)
- **The ~$1B/yr figure** comes from 2025 Bloomberg reporting. The joint statement does not state a price, and I found no primary confirmation of it. — (see Gaps)
- **Apple's developer positioning [primary]:** "Apple Intelligence is the personal intelligence system powered by next-generation Apple Foundation Models, bringing personal context understanding, app actions, and on-screen awareness across iPhone, iPad, Mac, Apple Watch, and Apple Vision Pro." — [Apple Developer: Apple Intelligence](https://developer.apple.com/apple-intelligence/)
- **Third-party models in the Foundation Models framework (iOS 27 SDK) [primary]:** "You can now work with any language model, including Apple Foundation Models, cloud models like Claude and Gemini, or any other provider that conforms to the Language Model protocol." Other new pieces: multimodal prompts, on-device Vision tools (OCR, barcodes) the model can call, "Dynamic Profiles" to swap models, tools and instructions mid-session, an Evaluations framework, an `fm` CLI and Python SDK, and Instruments profiling for "agentic app experiences". WWDC26 session titles include "Build agentic app experiences with the Foundation Models framework" and "Bring an LLM provider to the Foundation Models framework". — [Apple Developer: What's new in Apple Intelligence](https://developer.apple.com/apple-intelligence/whats-new/)
- **Free PCC model access for small developers [primary]:** apps in the App Store Small Business Program with fewer than 2M first-time downloads "can access the next generation of Apple Foundation Models running on Private Cloud Compute at no cloud API cost." — [Apple Developer: What's new](https://developer.apple.com/apple-intelligence/whats-new/)
- **PCC model access needs a managed entitlement [primary]:** `PrivateCloudComputeLanguageModel` is "a variant of Apple Foundation Models that runs on Private Cloud Compute… To develop with PCC you must meet certain eligibility requirements… request access to the managed entitlement." — [Apple docs: PrivateCloudComputeLanguageModel](https://developer.apple.com/documentation/foundationmodels/privatecloudcomputelanguagemodel)
- **Licence terms [primary]:** the June 8, 2026 DPLA update added "Section 3.2(h): Updated terms for use of and access to Apple models", "Section 3.3.11: Grouped AI and machine learning technologies under new subsection", and "3.3.11(A): Updated requirements for use of Foundation Models framework." The text of those terms was not retrieved. — [Apple Developer News, 8 Jun 2026](https://developer.apple.com/news/?id=a233fmpw)
- **Xcode 26.3 (Feb 2026):** shipped agentic coding with Anthropic's Claude Agent and OpenAI's Codex built in. It was the first Xcode with Model Context Protocol (MCP) support, so any MCP-compatible agent can connect. Developers sign in with a provider account or an API key. — [SD Times](https://sdtimes.com/ai/xcode-26-3-adds-agentic-coding-support/); [AlternativeTo](https://alternativeto.net/news/2026/2/xcode-26-3-adds-agentic-coding-with-claude-agent-codex-and-other-ai-tools-via-mcp); [TechRadar](https://www.techradar.com/pro/apple-launches-xcode-26-3-brings-even-more-ai-power-to-coding-on-mac); [Techloy](https://www.techloy.com/apple-brings-ai-coding-agents-to-xcode-in-new-26-3-update/)
- **Siri "Extensions" for third-party chatbots (reported):** Bloomberg/Gurman (Mar–May 2026) reported that iOS 27 would let Gemini, Claude and other chatbot apps plug into Siri, with the choice made in Settings. That would end ChatGPT's exclusivity. — [MacRumors, 26 Mar 2026](https://www.macrumors.com/2026/03/26/apple-ios-27-siri-chatbot-integration); [Tom's Guide](https://www.tomsguide.com/phones/iphones/beyond-chatgpt-ios-27-extensions-will-reportedly-allow-siri-to-use-google-gemini-and-claude); [Thurrott](https://www.thurrott.com/a-i/apple-intelligence/334259/now-apple-plans-to-open-up-siri-to-third-party-ai)
- **Whether Extensions was announced is contested:** TheNextWeb reports the system exists in iOS 27 beta code but Apple "refused to show it at WWDC". FelloAI's post-keynote check says it was not announced and that the beta still hands off only to ChatGPT. Several blogs (aiweekly, dev.to, wowhow, chatforest) claim it was announced, but they read like unverified or vendor content. — [TheNextWeb](https://thenextweb.com/news/apple-siri-extensions-third-party-ai-missing-wwdc); [FelloAI](https://felloai.com/wwdc-2026-preview/); contradicted by [aiweekly](https://aiweekly.co/node/2611), [ChatForest](https://chatforest.com/builders-log/wwdc-2026-keynote-confirmed-apple-ai-platform-builder-guide/)
- **ChatGPT:** it remains the built-in fallback/handoff in Siri. Before iOS 27 it was the only third-party chatbot tie-in. — [MacRumors](https://www.macrumors.com/2026/03/26/apple-ios-27-siri-chatbot-integration); [FelloAI](https://felloai.com/wwdc-2026-preview/)
- **Gemini-trained models (secondary):** Wikipedia summarizes WWDC26 as an improved Apple Intelligence "using a next-generation version of Apple's own models trained with the help of Gemini models." — [Wikipedia: Apple Intelligence](https://en.wikipedia.org/wiki/Apple_Intelligence)
- **Image generation shift [primary]:** the ImageCreator class (on-device image generation) is discontinued in iOS/macOS 27. Image Playground now uses a new model on PCC. — [Apple Developer News, 11 Jun 2026](https://developer.apple.com/news/); [Apple Developer: Apple Intelligence](https://developer.apple.com/apple-intelligence/)

### Inferences
- Apple's strategy is to own the orchestration and privacy layer: on-device models, PCC, App Intents schemas and the Spotlight semantic index. It buys frontier capability from Google and stays model-agnostic toward developers through the Language Model protocol. For Relic, an app that brings its own model provider (Claude, Gemini, local) through the Foundation Models framework is explicitly sanctioned.
- Free PCC access for small developers makes "Apple-hosted, privacy-attested cloud inference" a cheap fallback for Relic that keeps data inside Apple's privacy envelope. That may also ease the 5.1.2(i) third-party AI consent burden. This is an inference: whether Apple's own PCC counts as a "third-party AI" is not stated.

### Gaps
- No primary confirmation of the ~$1B/yr price or the "custom 1.2T-parameter Gemini" details. These are Bloomberg 2025 reports I could not fetch.
- Whether Siri Extensions (Claude/Gemini as a Siri backend) is live in iOS 27.0 or 27.1 as of Oct 2026 is unresolved. No Apple primary source found.
- I could not fetch the Apple Foundation Models 2025 and 2026 tech reports (machinelearning.apple.com blocked). From prior knowledge, the 2025 report (July 2025) described a ~3B-parameter on-device model and a server model on PCC. That is unverified in this session.
- No Anthropic- or Perplexity-specific consumer integration with Apple Intelligence was found beyond the reported Extensions and Xcode.

## 2. Agentic Siri timeline: what shipped and what was delayed (iOS 26.4 to iOS 27, Sep–Oct 2026)

### Takeaway
The personalized and agentic Siri missed iOS 26.4 (Gurman, Feb 2026: testing problems). It shipped as "Siri AI" in iOS 27 on 14 Sep 2026 with personal context, on-screen awareness and in-app actions, but with significant limits:
- English-only beta
- waitlist
- daily cloud limits
- iPhone 15 Pro or later
- not available in the EU (iPhone/iPad) or China

Hands-on reviews praise the features but contain no systematic reliability data.

### Cited Findings
- **iOS 26.4 slip:** Gurman (Feb 2026) reported that the new Siri would not ship in iOS 26.4 because testing showed it "doesn't always properly process queries or can take too long." Testers also saw unexpected handoffs to ChatGPT. Personal-data search and multi-app App Intents actions were the features most at risk, and some were pushed to 26.5 or iOS 27. — [GSMArena (Gurman)](https://www.gsmarena.com/gurman_apples_new_siri_delayed_again_will_not_be_included_in_ios_264-news-71525.php); [iGeeksBlog](https://www.igeeksblog.com/apple-delays-gemini-powered-siri-features-ios-26-4-ios-27/); [Macworld](https://www.macworld.com/article/3058849/apple-just-cant-get-siri-working-right.html)
- **iOS 27 release, 14 Sep 2026:** "Apple releases iOS 27, redesigned Siri AI." Siri AI uses LLMs to search personal data and the web. It ships as an English-only beta on iPhone 15 Pro, 15 Pro Max, iPhone 16 and later. Cloud features have daily limits, and Apple says expanded limits "may be available for a fee in the future." Excluded in the EU and China. — [CNBC](https://www.cnbc.com/2026/09/14/apple-releases-ios-27-redesigned-siri-ai.html) (snippet); [Engadget: waitlist](https://www.engadget.com/2261054/why-siri-ai-ios-27-waitlist/) (snippet); [Gadget Hacks](https://apple.gadgethacks.com/news/ios-27-new-features-what-siri-ai-does-and-who-gets-it/)
- **Features delayed past 27.0:** Suggestions in Messages and AI password fixes are "Coming in a future software update." — [iDrop News](https://www.idropnews.com/news/ios-27-official-release-delayed-features/268418/); [The Apple Post](https://www.theapplepost.com/2026/09/16/72279/ios-27-is-here-but-these-features-arent-available-yet/)
- **Developer plumbing for agentic Siri [primary]:**
  - App Intents *schemas* (system-defined intent and entity structures for categories such as task management, photo editing and communication).
  - *Entity schemas* feed the Spotlight semantic index for personal context, "with attribution back to your app".
  - A *View Annotations API* provides on-screen awareness by mapping views to entities.
  - An *App Intents Testing framework* runs tests through real Siri, Shortcuts and Spotlight pathways.
  - Shortcuts can now build automations from natural-language descriptions.
  - — [Apple Developer: What's new](https://developer.apple.com/apple-intelligence/whats-new/); [Apple Developer: Apple Intelligence](https://developer.apple.com/apple-intelligence/)
- **[primary]** "Apple Intelligence combines language models with your app's actions and content to power Siri AI… Index entities… Adopt schemas… Associate entities with views… Donate actions and content." Onscreen context "is private to your app" unless the app associates views with entities. — [Apple docs: Apple Intelligence and Siri AI](https://developer.apple.com/documentation/appintents/apple-intelligence-and-siri-ai)
- **Reviews:**
  - MacStories calls on-screen awareness combined with actions "one of my favorite aspects of Siri AI," and notes that effectiveness depends on third-party adoption. — [MacStories iOS 27 review](https://www.macstories.net/stories/ios-and-ipados-27-review/6/)
  - WSJ (Nicole Nguyen) reports that Siri "can see your screen, search your photos and get real work done." — [MacDailyNews quoting WSJ](https://macdailynews.com/2026/09/16/wsj-siri-finally-grows-up-apples-new-assistant-can-see-your-screen-search-your-photos-and-get-real-work-done/amp/)
  - MacRumors' beta hands-on covers multi-stop directions, photo edit and share, and email in the user's style. — [MacRumors](https://macrumors.com/2026/06/10/ios-27-siri-ai-hands-on)
  - Android Police says personal context is where Siri leads, but the experience is dry and users cannot pick the model. — [Android Police](https://www.androidpolice.com/gemini-has-nothing-to-fear-from-the-new-siri-ai/)
- **Agentic accessibility:** a May 2026 preview of natural-language Voice Control shares agentic capabilities with the new Siri (Gurman, per 9to5Mac). — [9to5Mac](https://9to5mac.com/2026/05/19/apple-just-revealed-an-ios-27-feature-that-hints-at-siris-new-powers/)

### Inferences
- Apple's agent model is "the system agent (Siri) drives apps through declared App Intents and indexed entities". It is not "third-party agents drive other apps." The supported path for Relic is to *be a well-described App Intents provider*: expose memories as entities in the Spotlight semantic index, annotate views, and adopt schemas. Relic should not try to be a cross-app agent itself on iOS.
- Siri AI now competes directly with Relic's "personal memory" value proposition, but it is gated: English-only, waitlisted, rate-limited, newer hardware, not in the EU on iPhone. Those gaps are openings, especially in the EU.

### Gaps
- I found no quantitative reliability testing (success rates) for Siri AI app actions. Reviews are qualitative and beta-era.
- What exactly shipped in iOS 26.4 and 26.5 (March–May 2026) for Siri is unconfirmed by a post-release source.

## 3. App Store Review Guidelines and developer rules on AI and agents (2025–Oct 2026)

### Takeaway
There is no dedicated "agent app" guideline. The binding rules for Relic are:
- **5.1.2(i):** explicit disclosure and permission before sharing personal data with third-party AI (added Nov 2025, still in the live text).
- **2.5.14:** explicit consent plus a visible or audible indicator for any recording or logging of user activity, including screen recordings.
- **2.5.2:** no downloading or executing code that changes app functionality.
- **4.7.x:** chatbots and plug-ins may not expose native APIs without permission, and may not share data or permissions without per-instance consent.
- **2.4.5:** Mac App Store sandboxing.
- **4.4.1:** keyboard limits.
- **5.4:** VPN rules.

On the Mac, Apple announced on 2 Oct 2026 that it will tighten Full Disk Access, explicitly citing AI agents.

### Cited Findings
- **5.1.2(i), live text [primary]:** "You must clearly disclose where personal data will be shared with third parties, including with third-party AI, and obtain explicit permission before doing so." — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- **When it was added [primary]:** 13 Nov 2025: "5.1.2(i): Clarifies that you must clearly disclose where personal data will be shared with third parties, including with third-party AI, and obtain explicit permission before doing so." The same update added 4.7.2 (software not embedded in the binary may not "extend or expose native platform APIs… without prior permission") and 4.1(c) (no use of another developer's brand in your app's icon or name). — [Apple Developer News, 13 Nov 2025](https://developer.apple.com/news/?id=ey6d8onl)
- **Enforcement example:** an App Review rejection under 5.1.1(i) and 5.1.2(i) asked the app to state what data goes to the AI service and who receives it, to obtain permission first, and to name the AI sharing in the privacy policy. Secondary sources say the disclosure should name the provider and purpose, but that wording is not in the guideline text. — [Apple Developer Forums thread 815109](https://developer.apple.com/forums/thread/815109); [ptkd.com](https://ptkd.com/journal/rejection-guideline-5-1-2-ai-data-sharing)
- **2.5.14 [primary]:** "Apps must request explicit user consent and provide a clear visual and/or audible indication when recording, logging, or otherwise making a record of user activity. This includes any use of the device camera, microphone, screen recordings, or other user inputs." — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- **2.5.2 [primary]:** apps "may not read or write data outside the designated container area, nor may they download, install, or execute code which introduces or changes features or functionality of the app, including other apps." — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- **2.5.4 [primary]:** background services only for their intended purposes ("VoIP, audio playback, location, task completion, local notifications, etc."). — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- **4.7 [primary]:** covers "chatbots, plug-ins". 4.7.1 requires following 5.1 privacy rules. 4.7.2 bars exposing native APIs without Apple's permission. 4.7.3 says the app "may not share data or privacy permissions to any individual software offered in your app without explicit user consent in each instance". — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- **1.2 [primary]:** user-generated-content rules explicitly include "AI content creation apps". On 16 Oct 2026, 1.2 was extended to nonconsensual intimate imagery "including imagery generated using AI tools". New 2.5.19 bars hidden, dormant or undocumented features (bait-and-switch). — [Apple Developer News, 16 Oct 2026](https://developer.apple.com/news/); [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- **4.4.1 keyboards [primary]:** must "remain functional without full network access and without requiring full access" and must "collect user activity only to enhance the functionality of the user's keyboard extension". They must not launch other apps besides Settings. — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- **5.4 VPN [primary]:** must use NEVPNManager. Only organization developers may offer them. Data must be declared before use, and apps "may not sell, use, or disclose to third parties any data for any purpose." — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- **2.4.5 Mac App Store [primary]:** apps "must be appropriately sandboxed… only use the appropriate macOS APIs for modifying user data stored by other apps." Packaging must use Xcode technologies, with no third-party installers. — [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- **Full Disk Access on macOS (2 Oct 2026) [primary]:** "Some developers are using Full Disk Access in ways that could put users at risk, exposing everything on their systems—including files, mail, messages, and even browsing history… we will introduce additional controls to ensure that users who genuinely wish to grant an app this extraordinary level of access can only do so with very explicit user action… As AI agents become increasingly capable and autonomous, the risks associated with this level of access will grow substantially." — [Apple Developer News: Updates to Full Disk Access in macOS](https://developer.apple.com/news/?id=p6zjojqw)
- **Developer ID:** the original Developer ID Sub-CA expires 1 Feb 2027. Developers must reissue certificates from the G2 CA. — [Apple Developer News, 1 Oct 2026](https://developer.apple.com/news/)
- **Other 2026 licence and guideline changes [primary]:**
  - Oct 13, 2026 DPLA: terms for a "Live Assistance API" (3.3.8(j)) and an "App Replacement Entitlement" (3.3.8(k)).
  - June 8, 2026 DPLA: terms for a "Suggested Actions API" (3.3.3(Q)) and a "Trust Insights framework" (3.3.3(R)).
  - The contents of these APIs were not retrieved.
  - — [Apple Developer News](https://developer.apple.com/news/); [8 Jun 2026](https://developer.apple.com/news/?id=a233fmpw)
- **ATT is a separate requirement:** commentary notes that ATT denial does not bar sending user-typed content to an LLM if separate AI consent is obtained. — [ptkd.com](https://ptkd.com/journal/rejection-guideline-5-1-2-ai-data-sharing)
- **MCP at the OS level:** iOS and macOS 26.1 betas contained code for MCP inside App Intents (9to5Mac, Sep 2025). Claims that MCP became "system-wide" in iOS/macOS 27 come only from blogs. Apple's App Intents "Apple Intelligence and Siri AI" doc page contains no MCP mention [primary check]. — [AlternativeTo](https://alternativeto.net/news/2025/9/apple-begins-testing-early-model-context-protocol-mcp-support-in-ios-ipados-and-macos); [ChatForest (unverified)](https://chatforest.com/builders-log/apple-ios-27-mcp-system-wide-siri-core-ai-builder-guide/); [Apple docs](https://developer.apple.com/documentation/appintents/apple-intelligence-and-siri-ai)

### Inferences
- Relic's consent-based design matches 5.1.2(i) and 2.5.14. Every cloud-LLM send of memories needs a provider-named, explicit opt-in, and the privacy policy must name AI sharing. Any passive capture (screen, mic, activity logging) needs explicit consent plus a persistent indicator.
- A "Recall-style" Mac app that relies on Full Disk Access or broad screen capture will face rising friction. Apple is explicitly framing broad access as an AI-agent risk. Developer ID distribution avoids sandboxing, but not the FDA and TCC prompts. Expect harder consent flows in macOS 27.x.
- On iOS, an app cannot automate other apps. Relic's "agent" must act only through its own capabilities, system share sheets and URL schemes, or by exposing App Intents to Siri and Shortcuts.

### Gaps
- No explicit Apple guideline on "agent apps" or apps that operate other apps beyond 2.5.2 and 4.7.2.
- I did not see the full text of the "Live Assistance API", "Suggested Actions API" or "App Replacement Entitlement".
- The specific new FDA controls in macOS 27.x have no announced date.

## 4. EU DMA and Japan MSCA: interoperability and third-party assistants

### Takeaway
The Commission's March 2025 specification decisions forced iOS connectivity interoperability: notifications to third-party wearables, proximity pairing, background execution, Wi-Fi and similar. In June 2026 Apple withheld Siri AI from iPhone and iPad in the EU. Apple says that DMA interoperability would require granting third-party assistants equivalent deep system access, and that the Commission rejected its "Trusted System Agent" intermediary and 18-month phase-in. The Commission says the choice not to launch is Apple's alone. In Japan, iOS 26.2 (Dec 2025) lets users map the side button to a third-party voice assistant app. No equivalent exists in the EU.

### Cited Findings
- **March 2025 decisions:** two specification decisions. One covers nine iOS connectivity features (incl. notifications, background execution, automatic audio switching, proximity pairing, Wi-Fi). The other covers the process for developers' interoperability requests. — [EU Commission DMA](https://digital-markets-act.ec.europa.eu/commission-provides-guidance-under-digital-markets-act-facilitate-development-innovative-products-2025-03-19_lv); [TechCrunch](https://techcrunch.com/2025/03/19/eu-sends-apple-first-dma-interoperability-instructions-for-apps-and-connected-devices/)
- **Apple's response:** Apple disabled iPhone–Apple Watch Wi-Fi sync in the EU rather than open Wi-Fi access (Nov 2025). — [MacRumors via scour.ing](https://scour.ing/p/https://www.macrumors.com/2025/11/06/iphone-apple-watch-wi-fi-sync-eu-ios)
- **Siri AI EU delay (8 Jun 2026):** Apple newsroom post "Due to DMA, Siri AI delayed in EU for iOS 27 and iPadOS 27". Siri AI remains available in the EU on macOS 27, watchOS 27 and visionOS 27. Apple says compliance would require giving third-party assistants the same deep access (reading messages, payments, acting across apps). Apple says it proposed a "Trusted System Agent" intermediary and an 18-month phased rollout, both rejected. There is no timeline. — [Apple Newsroom](https://www.apple.com/newsroom/2026/06/due-to-dma-siri-ai-delayed-in-eu-for-ios-27-and-ipados-27/) (blocked; via snippets); [TheNextWeb](https://thenextweb.com/news/apple-siri-ai-eu-dma-delay-ios-27); [Silicon UK: EU says Apple asked for 18-month exemption](https://www.silicon.co.uk/ai-2/eu-apple-siri-630206/amp)
- **The Commission's position:** spokesperson Thomas Regnier said the decision not to roll out is "Apple's and Apple's only… nothing in the DMA prohibits Apple from introducing new products in the EU." He said Apple did not propose interoperability solutions meeting EU privacy and security standards, and that an exemption is "not an option". — [Citizen Digital](https://citizen.digital/article/european-union-rejects-apple-blame-for-delayed-siri-ai-rollout-n384288); [Board Stewardship](https://boardstewardship.com/eu-rejects-apple-request-for-exemption-from-tech-rules-amid-siri-ai-rollout-delay/)
- **Commentary:** some argue the delay shows the DMA reducing competition. This is opinion. — [LawEconCenter](https://laweconcenter.org/apples-eu-siri-ai-delay-shows-dma-reducing-competition-auer-says/)
- **EU business terms (effective 1 Oct 2026) [primary]:** a single set of EU terms. The Core Technology Fee is replaced by a 5% "Core Technology Commission" on digital transactions in apps distributed outside the App Store. Alternative payments are allowed alongside IAP, and qualifications for web distribution and alternative marketplaces are expanded. — [Apple Developer News, 18 Aug 2026](https://developer.apple.com/news/)
- **Japan side button [primary]:** "In Japan, people might place an action on the side button of iPhone that instantly launches your voice-based conversational app." This requires an entitlement and an App Intent conforming to the relevant schema. The user's Apple Account region must be Japan and the user must be physically located in Japan. — [Apple docs: Launching your voice-based conversational app from the side button](https://developer.apple.com/documentation/appintents/launching-your-voice-based-conversational-app-from-the-side-button-of-iphone)
- **Japan licence terms [primary]:** DPLA 3.3.3(J) "Specified requirements for launching voice-based conversational apps via the side button on iPhone". iOS 26.2 brought MSCA changes (alternative marketplaces, payments). — [Apple Developer News, 17 Dec 2025](https://developer.apple.com/news/)
- **Japan, more detail:** there is no third-party wake word, and audio starts only after the app launches. The EU was not included. — [9to5Mac](https://9to5mac.com/2025/11/17/iphone-replace-siri-side-button-japan-ios-26-2/); [heise](https://heise.de/-11083304); [Michael Tsai](https://mjtsai.com/blog/?p=50097)
- **Brazil [primary]:** iOS 26.5 brought alternative marketplaces and payments under a CADE agreement. — [Apple Developer News, 18 Jun 2026](https://developer.apple.com/news/)

### Inferences
- The EU is currently the market where a third-party personal agent like Relic faces the least competition from Siri AI on iPhone. That situation may change if Apple and the Commission agree on a "Trusted System Agent"-style framework, which could in turn create a formal channel for third-party agents to get deep access. This is worth monitoring.
- In Japan, Relic could ship a side-button voice entry point (App Intents plus entitlement).

### Gaps
- I found no 2026 Commission decision that specifically grants third-party assistants access to iOS features, or default-assistant choice in the EU. The status of Apple's compliance with the 2025 interoperability measures in 2026 is unclear.
- The full Apple newsroom text could not be fetched (blocked).

## 5. Apple's privacy posture on AI (PCC, transparency) and statements on third-party agents and MCP

### Takeaway
Apple frames all of its first-party AI, including the Gemini-based models, as running "on Apple devices and Private Cloud Compute". Its newest public signal on third-party agents is defensive: broad system access by autonomous AI agents is a risk to be gated with "very explicit user action". Apple's EU stance treats deep assistant access as something only a trusted, system-mediated agent should get.

### Cited Findings
- **Gemini deal privacy commitment:** "Apple Intelligence will continue to run on Apple devices and Private Cloud Compute, while maintaining Apple's industry-leading privacy standards." — [Google/Apple joint statement](https://blog.google/company-news/inside-google/company-announcements/joint-statement-google-apple/) (snippet)
- **Image Playground [primary]:** "Images are generated on Private Cloud Compute, so photos are never stored or shared." PCC models carry "privacy guarantees." — [Apple Developer: Apple Intelligence](https://developer.apple.com/apple-intelligence/); [PCC model docs](https://developer.apple.com/documentation/foundationmodels/privatecloudcomputelanguagemodel)
- **Critics:** some outlets question whether data touches Google infrastructure despite the PCC claims. That claim is not substantiated by a primary source. — [Kersai (low-quality source)](https://kersai.com/apple-siri-google-gemini-upgrade-2026-complete-guide-ios-26-ios-27/); [Digital Applied](https://www.digitalapplied.com/blog/apple-siri-2026-gemini-powered-context-aware-ai)
- **Statement on AI agents [primary]:** "As AI agents become increasingly capable and autonomous, the risks associated with this level of access will grow substantially. We are committed to ensuring users clearly understand these risks before granting such access." — [Apple Developer News, 2 Oct 2026](https://developer.apple.com/news/?id=p6zjojqw)
- **"Trusted System Agent":** Apple's proposed DMA intermediary for third-party assistant access, reported via coverage of the June 2026 EU announcement. — [TheNextWeb](https://thenextweb.com/news/apple-siri-ai-eu-dma-delay-ios-27); [Silicon UK](https://www.silicon.co.uk/ai-2/eu-apple-siri-630206/amp)
- **Security research programs:** the developer site footer lists the Security Bounty Program and the Security Research Device Program. — [Apple Developer](https://developer.apple.com/apple-intelligence/)

### Inferences
- Apple's direction is a single privileged system agent (Siri AI) with deep access, reached by apps through declared intents and entities. Third-party agents get narrow, consented, auditable channels. Relic's local-first, consent-based positioning is aligned with Apple's stated values. Its main platform risks are capability ceilings (no cross-app automation on iOS; tighter Full Disk Access and screen capture on Mac), not policy hostility.

### Gaps
- PCC verifiable-transparency details were not re-verified this session because security.apple.com was blocked:
  - public software images
  - Virtual Research Environment (Oct 2024)
  - bounty up to $1M
- I found no primary statement on whether the Gemini-based PCC models are covered by the same transparency log and research access.
- No official Apple statement on MCP for third-party consumer agents was found. Only Xcode 26.3's MCP support is well sourced.

## Blocked sources
- www.apple.com (Newsroom, incl. "Due to DMA, Siri AI delayed in EU…" June 2026): DNS/403 via proxy
- machinelearning.apple.com (Foundation Models tech reports 2025/2026): 403
- security.apple.com (PCC blog/VRE): 403
- www.cnbc.com (iOS 27 release article): 403
- www.engadget.com, thenextweb.com, www.macrumors.com, 9to5mac.com, www.macstories.net, www.idropnews.com, blog.google, www.silicon.co.uk: DNS failure via WebFetch / 403 via curl
- WebFetch tool overall failed with getaddrinfo ENOTFOUND for all tested domains. Only developer.apple.com was reachable (via curl).
