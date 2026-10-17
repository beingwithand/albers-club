# Apple's agentic developer platform as of October 2026, for Relic

Scope: what third-party apps can do agentically on iOS/iPadOS 26–27 and macOS 26–27. Research date: 2026-10-17.

Source conventions:
- **[S]** marks a fact seen only in a search-engine snippet or summary. I could not open the page itself, usually because its domain did not resolve from this environment.
- Facts from WWDC session pages come from Apple's own transcript and code pages, read through a fetch-and-summarize tool. "Community digest" marks non-Apple summaries.
- Apple renamed versions to year numbers. "27" means the OS release shipped September 2026.

---

## 1. App Intents: what Relic can expose to Siri, Spotlight and Shortcuts (semantic index, schemas, donation, on-screen awareness, snippets, cross-app chaining)

### Takeaway
App Intents is Apple's only sanctioned agentic surface into a third-party app. In iOS 27 it covers:
- **Entity schemas.** Content goes into the on-device Spotlight semantic index, which Siri can use as personal context.
- **Intent schemas.** Siri can run actions from natural language with no predefined phrases.
- **Interaction donations.** The app tells the system what the user did in its UI.
- **On-screen awareness.** `NSUserActivity` covers one main item; view or entity annotations cover lists and multiple items.

The direction is one-way: Siri and Shortcuts call into apps. No public API lets a third-party app call another app's intents directly. The only route is triggering a user-built Shortcut through a URL scheme, which brings the Shortcuts app to the foreground.

### Cited Findings
**Schemas and the semantic index**
- Apple's WWDC26 Apple Intelligence guide:
  - App Schemas are "system-defined structures that Siri understands", covering categories such as task management, photo editing and communication.
  - **Entity schemas** contribute app content to the **Spotlight semantic index**, "enabling personal context understanding with attribution back to the app."
  - **Intent schemas** let people act on content in natural language "with no specific phrases to define." No code changes are needed as Siri expands to new languages.
  - Source: [WWDC26 Apple Intelligence guide](https://developer.apple.com/wwdc26/guides/apple-intelligence/)
- Declaration syntax and how schemas relate to intents:
  - An entity binds to a schema with `@AppEntity(schema: .messages.message)`. A schema is described as a "specialization of an App Intent."
  - Xcode flags incomplete schema sets as build errors with Fix-Its. Example: `sendMessage` without `draftMessage`.
  - Source: session 240 "Build intelligent Siri experiences with App Schemas" ([Apple session page](https://developer.apple.com/videos/play/wwdc2026/240/); [community digest](https://github.com/ivan-magda/wwdc26-notes/blob/main/sessions/240-intelligent-siri-experiences-app/digest.md))
- Three ways for Siri to find content (same session 240 digest):
  - **`IndexedEntity`** adds entities to the system semantic index. `indexingKey` marks searchable properties such as `\.textContent`.
  - **`EntityStringQuery`** is the fallback for data that can't be indexed ahead of time. The digest notes this path "loses semantic understanding."
  - **`IntentValueQuery`** resolves values coming from other apps (for example `IntentPerson`) to existing entities.
- Keeping the index current and handling content that can't be indexed. Source: session 343 "Explore advanced App Intents features for Siri and Apple Intelligence", [Apple session page](https://developer.apple.com/videos/play/wwdc2026/343/).
  - Adopt `IndexedEntity` and call `CSSearchableIndex.indexAppEntities`.
  - Keep the index current by indexing new entities, updating changed ones and deleting removed ones. Support reindexing with `IndexedEntityQuery`.
  - For content too large, remote or fast-changing to index, use `IntentValueQuery`.
  - `.system.searchInApp` "lets people search in your app with Siri… even if you don't index your entities."
- Session 345 states that Spotlight is "the primary way Siri is able to retrieve your content", including semantic search. `RelevantEntities.shared.updateEntities(_:for:)` surfaces content for contexts such as `AppEntityContext.audio(.workout(...))`. Source: [Session 345 "Discover new capabilities in the App Intents framework"](https://developer.apple.com/videos/play/wwdc2026/345/)
- Session 246 "LLM search using Core Spotlight" exists. Session 241 also describes a Foundation Models **Spotlight search tool** for "fully local Retrieval-Augmented Generation (RAG) using a Core Spotlight index." Sources: [Apple Intelligence guide session list](https://developer.apple.com/wwdc26/guides/apple-intelligence/); [Session 241](https://developer.apple.com/videos/play/wwdc2026/241/)

**Interaction donations**
- Session 343:
  - "Apple Intelligence can't learn from actions people take through your app's UI without your help."
  - Donate UI interactions only. Donations must use schema-conforming intents and are stored "in a temporary transcript."
  - The call is `IntentDonationManager.shared.donate(intent:result:)`.
  - "If your app donates excessively, the system may ignore those donations."
  - Source: [Session 343](https://developer.apple.com/videos/play/wwdc2026/343/)

**On-screen awareness (view and entity annotations)**
- Session 343:
  - Use `NSUserActivity` (the `.userActivity` modifier) for a primary item, and `.appEntityIdentifier` for "one item among many."
  - Collection annotations (`.appEntityIdentifier(forSelectionType:)`) let Siri find selected entities that have scrolled off screen.
  - UIKit and AppKit equivalents are `AppEntityAnnotatable`, `UICollectionViewAppIntentsDataSource` and `appEntityUIElementProvider`.
  - Entity annotations also attach to notifications (`UNMutableNotificationContent.appEntityIdentifiers`), Now Playing and AlarmKit.
  - "You can't use TransientAppEntity." Annotations need persistent identifiers.
  - Source: [Session 343](https://developer.apple.com/videos/play/wwdc2026/343/)
- Apple's guide calls this the "View Annotations API: maps views to entities for on-screen awareness." Source: [WWDC26 Apple Intelligence guide](https://developer.apple.com/wwdc26/guides/apple-intelligence/)
- Without annotations, Siri's understanding of the screen "is limited to exactly what's in the pixels." **[S]** Source: [search snippet of Apple session material](https://developer.apple.com/videos/play/wwdc2026/343/)
- Entity view annotations and interactive snippets first appeared in iOS 26. Coverage of the iOS 26 App Intents additions also lists `IntentValueQuery` for Visual Intelligence and `@DeferredProperty`. **[S]** Source: [blakecrosley.com App Intents 2.0 iOS 26](https://blakecrosley.com/blog/app-intents-2-ios-26-additions)

**Responses, confirmations and snippets**
- Dialog and snippet APIs (session 343):
  - `ProvidesDialog` takes `IntentDialog(full:supporting:)`. The full string is read aloud on voice-only devices such as AirPods.
  - `ShowsSnippetView` returns SwiftUI views through `.result(dialog:view:)`.
  - Mid-intent clarification uses `$param.requestValue(...)`.
  - Source: [Session 343](https://developer.apple.com/videos/play/wwdc2026/343/)
- **Confirmation behavior (session 343):**
  - "By default, Siri assumes your entities are private to the person, and may skip confirmations for them."
  - Shared or public content should conform to `OwnershipProvidingEntity`, returning `.shared`, `.public` or `.unknown`.
  - Relevance for Relic: memory entities are private, so Siri may run actions on them without confirming.
  - Source: [Session 343](https://developer.apple.com/videos/play/wwdc2026/343/)

**Other iOS 27 App Intents additions** (all from [Session 345](https://developer.apple.com/videos/play/wwdc2026/345/))
- **`LongRunningIntent`.** Standard intents have **30 seconds** to finish. `LongRunningIntent` goes beyond that limit and manages the background task lifecycle.
  - Progress shows as a Live Activity with a stop button. The intent must report progress through `ProgressReportingIntent`.
  - Work runs inside `performBackgroundTask {…} onCancel:`. `CancellableIntent` supports cleanup.
  - **Background GPU access** is available "on supported devices" for tasks such as "on-device inference" and requires a GPU entitlement. The session gives no maximum duration.
- **`EntityCollection<T>`** passes entity identifiers instead of resolved entities. Tagging 1000 photos went from slow to "almost instant."
- New parameter types: `Duration`, `PersonNameComponents`, and `@UnionValue`.
- **`SyncableEntity`** lets Siri conversations continue across devices. Entities need stable IDs; `SyncableEntityIdentifier(local:stable:)` pairs a local ID with a stable one.
- `ExecutionTargets` (`.main`, `.appIntentsExtension`, `.widgetKitExtension`) controls which process runs an intent.
- `ValueRepresentation(exporting:)` shares structured system types, for example passing a `PlaceDescriptor` to Maps through a Shortcut.

**Testing**
- The new **AppIntentsTesting** framework (session 295) validates intents through real Siri, Shortcuts and Spotlight pathways without UI automation. Source: [WWDC26 Apple Intelligence guide](https://developer.apple.com/wwdc26/guides/apple-intelligence/)

**How Siri chains actions across apps**
- In Apple's words from session 240, cross-app flows combine on-screen awareness with **content transfer**:
  - `Transferable` with `IntentValueRepresentation(exporting:)` lets other apps act on an entity. `IntentValueRepresentation(importing:)` creates new entities from incoming values.
  - The stated rule: "if the content already exists, resolve it; if not, import it."
  - Source: [Session 240 digest](https://github.com/ivan-magda/wwdc26-notes/blob/main/sessions/240-intelligent-siri-experiences-app/digest.md)
- I found no Apple page describing Siri's planner or how it orders multi-step chains.
- The Xcode/Apple Intelligence special presentation adds:
  - "Siri can now take action inside your app, driven entirely by natural language."
  - AlarmKit annotations let Siri act "even if my app isn't visible onscreen."
  - "The privacy architecture protecting Apple Foundation Models on-device and on Private Cloud Compute is the same one protecting App Intents."
  - Source: [Session 382 "Inside Apple Intelligence and Xcode"](https://developer.apple.com/videos/play/wwdc2026/382/)

**Status of the new LLM Siri ("Siri AI")**
- It was **not** in iOS 26.4. In February 2026 Gurman reported the features would be spread across iOS 26.5 and iOS 27. The reasons were slow responses and trouble with multi-step requests, and "App Intents functionality is also reportedly behind schedule." **[S]** Sources: [GSMArena](https://m.gsmarena.com/gurman_apples_new_siri_delayed_again_will_not_be_included_in_ios_264-news-71525.php); [Daring Fireball](https://daringfireball.net/linked/2026/02/12/)
- Apple announced "Siri AI" in June 2026 (newsroom). It shipped in **beta** with iOS 27 on about **14 September 2026**. **[S]** Sources: [Apple Newsroom Jun 2026](https://www.apple.com/newsroom/2026/06/apple-introduces-siri-ai-a-profoundly-more-capable-and-personal-assistant/); [Apple Newsroom Sep 2026](https://www.apple.com/newsroom/2026/09/siri-ai-a-profoundly-more-capable-and-personal-assistant-is-here/); [9to5Mac requirements](https://9to5mac.com/2026/09/14/here-are-the-requirements-to-get-siri-ai-in-ios-27/)
- Language and region rollout **[S]**:
  - English only at launch. French, Japanese, **Korean**, Portuguese and Spanish were promised "next month", which 9to5Mac expects with iOS 27.1 (no later than Oct 23).
  - Not available in the EU on iPhone or iPad, citing the DMA. Mac and Vision Pro in the EU are allowed. Not available in mainland China.
  - Sources: [Apple feature availability](https://www.apple.com/ios/feature-availability/); [Apple Newsroom Sep 2026](https://www.apple.com/newsroom/2026/09/siri-ai-a-profoundly-more-capable-and-personal-assistant-is-here/)
- Apple and Google announced in January 2026 that "the next generation of Apple Foundation Models will be based on Google's Gemini models and cloud technology." **[S]** Source: [MacRumors Siri chatbot guide](https://www.macrumors.com/guide/siri-chatbot/)
- Reports say Siri can hand questions to installed Claude or Gemini apps through extensions. **[S]**, reported only. Source: [MacRumors](https://www.macrumors.com/guide/siri-chatbot/)

**Can a third-party app call other apps' intents?**
- The documented route is the Shortcuts URL scheme. The app opens `shortcuts://run-shortcut?name=…`, or the x-callback-url variant `shortcuts://x-callback-url/run-shortcut?name=…&input=text&text=…&x-success=…`.
  - `x-success` receives a `result` parameter containing the shortcut's text output.
  - Source: [Apple Shortcuts User Guide: x-callback-url](https://support.apple.com/en-gb/guide/shortcuts/apdcd7f20a6f/ios) **[S]**
- The deep link switches to the Shortcuts app to run. Source: [SwiftRocks](https://swiftrocks.com/running-other-apps-siri-shortcuts-through-deep-links-in-swift) **[S]**
- Apple's WWDC26 sessions describe intents being called by Siri, Shortcuts, Spotlight, widgets and Visual Intelligence. None describes an app-to-app intent invocation API. Session 345 says the closest mechanism is passing structured values to Maps through a Shortcut. Source: [Session 345](https://developer.apple.com/videos/play/wwdc2026/345/)

### Inferences
- Relic's best agentic hooks on iPhone:
  - Expose memories as `IndexedEntity`, with an entity schema where one fits. Relic's memories then become personal context Siri can retrieve.
  - Donate interactions.
  - Annotate views so "this memory" works.
  - Make capture or recall actions `LongRunningIntent` where inference is heavy.
- Relic cannot act as an orchestrator that drives other apps' intents on iOS, except by running user-authored Shortcuts through the URL scheme, which is visible and app-switching. Cross-app agency belongs to Siri, not to third-party apps.
- Siri may skip confirmation for private entities. Relic's consent model should therefore gate destructive or sharing intents itself, using `requestConfirmation` or by marking entities shared. This is an inference, not an Apple statement.
- Korean Siri AI depends on the iOS 27.1 rollout, which I could not confirm had shipped.

### Gaps
- No Apple documentation explains how Siri plans multi-app chains, ranks competing apps, or caps the number of steps.
- No schema list was verified for a "notes/journal/memory" domain that Relic could adopt. The App Schema domain catalog was not retrieved.
- "Interactive snippets" (iOS 26) were not covered in the iOS 27 pages I read. I did not open their WWDC25 source.
- The claim that SiriKit is deprecated in iOS 27 appears only in low-quality blogs. It is unverified.

---

## 2. Foundation Models framework

### Takeaway
In the 2026 release:
- The on-device model was rebuilt. Its context is **4,096 tokens on OS 26.0** and **8,192 on OS 27.0 (newer devices)**.
- It accepts **image input**, and the framework is now a **model-agnostic runtime** through the `LanguageModel` protocol: Apple on-device, Apple PCC, Anthropic and Google Swift packages, Core AI and MLX local models, or any Chat-Completions server.
- **Private Cloud Compute is open to developers**:
  - `PrivateCloudComputeLanguageModel` has 32,768-token context and reasoning levels.
  - It needs no API keys and has no token cost.
  - Apps with fewer than 2M first-time downloads are eligible, by application or entitlement.
  - Each user has a daily quota.
- **Custom adapters are effectively dead for OS 27.** The adapter toolkit 26.0.0 is the final release and is incompatible with OS 27. Training only ever ran on a Mac (32 GB) or Linux GPUs, never on device.

### Cited Findings
**Model, context and versions**
- On-device model versions: `SystemLanguageModel` has 3 model versions, aligned with OS **26.0–26.3**, **26.4** and **27.0**. Apple "periodically updates" it in OS updates. Specialized use case: `.contentTagging`. APIs include `contextSize`, `supportedLanguages`, `supportsLocale(_:)`, `tokenCount(for:)` and `Guardrails`. Source: [Apple docs: SystemLanguageModel](https://developer.apple.com/tutorials/data/documentation/foundationmodels/systemlanguagemodel.md)
- Context sizes:
  - `SystemLanguageModel().contextSize` is **4096 on OS 26.0** and **8192 on OS 27.0 (newer devices)**.
  - `PrivateCloudComputeLanguageModel().contextSize` is **32768**.
  - The on-device model works offline with no request limits and no reasoning.
  - Source: [Session 319](https://developer.apple.com/videos/play/wwdc2026/319/)
- The 2026 on-device model is "rebuilt from the ground up… better at logic and tool calling." `contextSize` and `tokenCount` shipped in **iOS 26.4**. Guardrail false positives were reduced in 26.4 and again in 27. Source: [Session 241](https://developer.apple.com/videos/play/wwdc2026/241/)
- Parameter count: Apple's 2025 description is "a compact on-device model of roughly 3 billion parameters" (MacStories quoting Apple, **[S]**), plus a mixture-of-experts PCC server model. Sources: [MacStories](https://www.macstories.net/notes/i-have-many-questions-about-apples-updated-foundation-models-and-the-great-use-model-action-in-shortcuts/); [Apple Intelligence Foundation Language Models Tech Report 2025](https://arxiv.org/pdf/2507.13575)
- I found no published parameter count for the 2026 rebuilt model.

**Guided generation, tools and streaming**
- The 2025 core recaps unchanged: `@Generable` guided generation, snapshot streaming, and the `Tool` protocol. Source: [Session 241](https://developer.apple.com/videos/play/wwdc2026/241/); [Session 382](https://developer.apple.com/videos/play/wwdc2026/382/)
- New built-in tools are `OCRTool` and `BarcodeReaderTool`, backed by Vision, plus a Spotlight search tool for local RAG. Source: [Session 241](https://developer.apple.com/videos/play/wwdc2026/241/)
- Agentic APIs from session 242. Source: [Session 242 "Build agentic app experiences with the Foundation Models framework"](https://developer.apple.com/videos/play/wwdc2026/242/)
  - `LanguageModelSession.DynamicProfile` with `Profile` lets you swap model, tools and instructions mid-session. Modifiers include `.model()`, `.reasoningLevel(.deep)`, `.temperature()` and `.toolCallingMode(.allowed/.disallowed/.required)`.
  - `DynamicInstructions` and `historyTransform` are available. Utilities provide `.rollingWindow(size:)` and `.droppingCompletedToolCalls()`.
  - `@SessionProperty`, `.onResponse` and `.onToolCall` support summarization and compaction.
  - `transcriptErrorHandlingPolicy` is available, and `transcript` is now settable.
  - Two orchestration patterns: "baton-pass" between profiles and "phone-a-friend" child sessions.
  - Apple says transcript edits can be used for "redacting private data before moving to a less private model".
- The "Foundation Models framework utilities" package adds a **skills** API (`Skill(name:description:prompt:)`) and a Chat Completions-compatible language model. The **core framework will be open-sourced**, including for Linux. Source: [Session 241](https://developer.apple.com/videos/play/wwdc2026/241/)

**Image input**
- Images go in as `Attachment(UIImage(...))` inside the prompt builder. Accepted types: UIImage, NSImage, CGImage, CIImage, CVPixelBuffer and file URLs.
- "Any size and aspect ratio." Larger images "consume more tokens and incur more latency."
- Source: [Session 241](https://developer.apple.com/videos/play/wwdc2026/241/); see also [Session 237 "What's new in image understanding"](https://developer.apple.com/videos/play/wwdc2026/237/)

**Third-party and local models**
- The new `LanguageModel` protocol: "Anthropic and Google publish Swift packages for their frontier models… Everything downstream stays the same."
- Open-source `CoreAILanguageModel` and `MLXLanguageModel` run local models on the ANE or GPU.
- Apple's guidance: "Never store private keys in your app binary"; use OAuth and the Keychain. `response.usage` reports token counts.
- Source: [Session 241](https://developer.apple.com/videos/play/wwdc2026/241/); [Session 382](https://developer.apple.com/videos/play/wwdc2026/382/)

**Private Cloud Compute for developers (new in 2026)**
- Apple's statements in session 319:
  - "This model is available for apps with less than 2M downloads. And you can apply on the developer website today."
  - "PCC is only available on Apple Intelligence devices."
  - "No account setup, no authentication and no API keys"; "there are no token costs to you."
  - "Each user gets a daily limit… users can upgrade to iCloud+ to get higher limits." Requests count against the user's iCloud account.
  - "User data is never stored."
  - APIs: `PrivateCloudComputeLanguageModel`, `isAvailable`, `quotaUsage` (`isLimitReached`, `isApproachingLimit`, `limitIncreaseSuggestion`), and `ContextOptions(reasoningLevel: .light/.moderate/.deep)`. Reasoning tokens count toward context.
  - Also available on watchOS 27.
  - Source: [Session 319 "Build with the new Apple Foundation Model on Private Cloud Compute"](https://developer.apple.com/videos/play/wwdc2026/319/)
- The eligibility wording differs between Apple pages:
  - The guide says apps "enrolled in the App Store Small Business Program with fewer than 2 million total first-time App Store downloads." Source: [WWDC26 AI guide](https://developer.apple.com/wwdc26/guides/apple-intelligence/)
  - Session 241 says an entitlement is required. Source: [Session 241](https://developer.apple.com/videos/play/wwdc2026/241/)
  - Session 382 says "developers in the App Store Small Business Program with less than 2 million downloads." Source: [Session 382](https://developer.apple.com/videos/play/wwdc2026/382/)

**Adapters**
- Training and deployment:
  - Training requires a "Mac with Apple silicon and at least 32 GB of memory, or Linux GPU machines" and Python 3.11+. There is **no on-device training path**.
  - Adapters are about 160 MB each and are delivered through Background Assets.
  - Deployment needs the `com.apple.developer.foundation-model-adapter` entitlement, requested by the Account Holder.
  - Each adapter matches one specific base-model version.
  - Source: [Apple: Foundation Models adapter training](https://developer.apple.com/apple-intelligence/foundation-models-adapter/)
- **Toolkit 26.0.0 is "the last release"** and is **not compatible with macOS/iOS/iPadOS/visionOS 27 and later**. The page names no successor. Source: [Apple: Foundation Models adapter training](https://developer.apple.com/apple-intelligence/foundation-models-adapter/)
- The 2025 tech report describes the adapters as rank-32 LoRA. Source: [arXiv 2507.13575](https://arxiv.org/pdf/2507.13575)

**Languages and regions**
- Availability "depends on whether the device and region supports Apple Intelligence." Use `supportedLanguages` and `supportsLocale(_:)` to check. Source: [Apple docs: SystemLanguageModel](https://developer.apple.com/tutorials/data/documentation/foundationmodels/systemlanguagemodel.md)
- Apple Intelligence languages as of 26.1 include **Korean**, alongside English, Danish, Dutch, French, German, Italian, Norwegian, Portuguese, Spanish, Swedish, Turkish, Simplified and Traditional Chinese, Japanese and Vietnamese. **[S]** Source: [Apple Support 121115](https://support.apple.com/en-mt/121115)

**Developer tooling**
- `fm` CLI on macOS 27 (`fm chat`, pipeable), plus a Python SDK `apple_fm_sdk` that uses the same on-device model. The Evaluations framework and an Instruments FM instrument are also new. Source: [Session 241](https://developer.apple.com/videos/play/wwdc2026/241/)

### Inferences
- On-device context for a memory agent is small. 8K tokens on 27 (4K on 26.0–26.3) forces RAG through the Spotlight tool or Relic's own index, plus aggressive compaction.
- PCC (32K, reasoning) is a free, privacy-preserving "big brain" for small apps. Relic qualifies while it has fewer than 2M downloads, if accepted. PCC fits Relic's consent model better than third-party clouds, but it needs a network connection and is quota-limited per user.
- DynamicProfile with redaction before model switching maps directly onto a consent policy that keeps raw memories on device and sends summaries to PCC or Claude.
- Do not plan on custom adapters for OS 27. Use prompting, tools, evaluations, or local models through `CoreAILanguageModel`/`MLXLanguageModel` instead.
- Third-party model packages (Claude/Gemini) let Relic keep one code path across on-device, PCC and Claude.

### Gaps
- Whether Korean is in `SystemLanguageModel.supportedLanguages` was not confirmed from Apple developer docs. Test on device.
- No exact daily PCC quota number was found.
- The PCC application URL and eligibility criteria (whether Small Business Program membership is required) conflict between pages.
- No parameter count was found for the 2026 on-device model.
- No adapter successor for OS 27 was found.

---

## 3. Shortcuts: Use Model, automations, and what runs without the user

### Takeaway
iOS 27 Shortcuts changes:
- **Use Model** has four model choices: **On-Device, Cloud, Cloud Pro (PCC, extended context, optional web "Broad World Knowledge"), and Extension Model (ChatGPT)**.
- New **Storage** keeps data between runs and syncs it via iCloud.
- Automations moved into the editor, and three triggers were added: **Screenshot, Keyboard, and Notification-from-app with keyword filter**. Automations sync across devices.
- Shortcuts can be created from natural language.
- Personal automations can "Run Immediately" for most triggers. That is a user choice, not something an app can configure.

### Cited Findings
**Use Model**
- WWDC26 session 310:
  - Use Model has "access to the latest Apple Intelligence models with web retrieval."
  - The Transcript output property shows "exactly what was passed to the model."
  - Exposed `@Property` fields on `AppEntity` "shape what the model sees."
  - Source: [Session 310 "What's new in Shortcuts"](https://developer.apple.com/videos/play/wwdc2026/310/)
- Model choices: Apple's Shortcuts guide lists On-Device, Cloud, Cloud Pro ("Uses Apple's Private Cloud Compute… extended context… for even larger and more complex tasks") and Extension Model ("Uses ChatGPT"). **[S]** Source: [Apple Support: Use Apple Intelligence in Shortcuts on Mac](https://support.apple.com/en-mide/guide/shortcuts-mac/mchl91750563/mac)
- "AFM 3 Cloud models in Shortcuts" are listed among server features with daily limits. **[S]** Source: [TechRepublic](https://www.techrepublic.com/article/news-ios-27-ai-shortcuts-automations/)
- iOS 26 introduced Use Model with On-Device, PCC and ChatGPT options. **[S]** Sources: [Tom's Guide](https://www.tomsguide.com/phones/iphones/i-used-ios-26-shortcuts-to-build-some-ai-powered-workflows-heres-what-you-can-do-now); [MacStories](https://www.macstories.net/notes/i-have-many-questions-about-apples-updated-foundation-models-and-the-great-use-model-action-in-shortcuts/)
- iOS 27 beta 3 release notes:
  - "The Use Model action may fail to run when using the On-Device option for some output types."
  - "Writing Tools actions are unavailable in Shortcuts."
  - Source: [gist diff of Apple release notes, Jul 2026](https://gist.github.com/galenguyer/eef52cf39cbb7745fe98f2e32f453590)

**Automations and storage**
- New automation types (session 310):
  - Screenshot: "runs when a screenshot is saved".
  - Keyboard: external keyboard connected or disconnected.
  - Notification: "runs when a notification is received from a specific app" with keyword filters.
  - Automations now live in the editor.
  - Source: [Session 310](https://developer.apple.com/videos/play/wwdc2026/310/)
- Storage is "Get, Set, and global storage values that sync across all of someone's devices via iCloud." Source: [Session 310](https://developer.apple.com/videos/play/wwdc2026/310/)
- Shared automations arrive disabled on the recipient's device. Triggers are now actions and can be stacked. Automations sync. Apple Intelligence builds shortcuts from descriptions. **[S]** Sources: [MacStories iOS 27 review p.13](https://www.macstories.net/stories/ios-and-ipados-27-review/13/); [9to5Mac](https://9to5mac.com/2026/09/29/ios-27s-shortcuts-app-adds-35-new-improved-actions-heres-whats-new/)
- "Run Immediately" for personal automations dates from iOS 17. Run-immediately automations always notify. Older guides say Location, Bluetooth and Wi-Fi triggers were exceptions, but that list is probably outdated. **[S]** Sources: [Matthew Cassinelli](https://matthewcassinelli.com/sirishortcuts/automations); [iMore](https://www.imore.com/shortcuts-beta-adds-notify-when-run-toggle-hide-automations-summary-view)

### Inferences
- The notification trigger with keyword filter, combined with Use Model and Relic's App Intents, is a user-authored path for "when X arrives, summarize it into Relic" with no Relic background privilege. The user must build it, possibly helped by natural-language creation.
- Relic can ship shareable Shortcuts, but they arrive with automations disabled, which is consistent with consent.
- Relic should expose rich `@Property` fields so Use Model can reason over Relic entities.

### Gaps
- No official iOS 26 or 27 list of which triggers can run without confirmation was found.
- Whether Extension Model includes Claude or Gemini in 27 is unconfirmed. Docs mention only ChatGPT.

---

## 4. Visual Intelligence, Image Playground and Writing Tools APIs

### Takeaway
- **Visual Intelligence:** apps can provide image-search results (camera on iPhone, screenshots on iPad and Mac) through `IntentValueQuery` over a `SemanticContentDescriptor`. In 2026 this extends to iPadOS and macOS.
- **Image Playground:** generation now runs on a new PCC model through a SwiftUI modifier. The programmatic `ImageCreator` is deprecated.
- I found no new developer Writing Tools API for 2026.

### Cited Findings
- Visual Intelligence (session 297):
  - An app implements one `IntentValueQuery` that accepts a `SemanticContentDescriptor`. The documented input is `pixelBuffer`.
  - Results are `AppEntity` values; multiple types use `@UnionValue`. Each type needs an `OpenIntent`.
  - The `.visualIntelligence.semanticContentSearch` schema adds "More results."
  - On iOS the input is mostly camera; on iPad and Mac it is mostly screenshots. Mac pixel buffers are larger.
  - New in 2026: add-to-contacts, multiple calendar events, medical device logging to HealthKit, and iPadOS/macOS support.
  - Source: [Session 297](https://developer.apple.com/videos/play/wwdc2026/297/); docs: [Integrating your app with visual intelligence](https://developer.apple.com/documentation/VisualIntelligence/integrating-your-app-with-visual-intelligence)
- Image Playground (session 375) **[S]**:
  - "ImageCreator, the non-UI API… is deprecated." Integration is a SwiftUI view modifier.
  - Generation uses a new cloud (PCC) model and "your data is never stored or shared."
  - Usage limits are managed by the system and raised with iCloud+.
  - Source: [Session 375](https://developer.apple.com/videos/play/wwdc2026/375/)
- The WWDC26 guide says the Image Playground model runs on PCC and can produce photorealistic images. Source: [WWDC26 AI guide](https://developer.apple.com/wwdc26/guides/apple-intelligence/)

### Inferences
- Relic could register as a Visual Intelligence search provider, for example "find memories matching what the camera sees" using Vision feature prints over Relic's photos. This only runs when the user invokes Visual Intelligence.
- Since `ImageCreator` is deprecated, Relic cannot generate images headlessly in the background through Apple's API.

### Gaps
- No 2026 Writing Tools developer changes were found. Standard text views get Writing Tools automatically, per the 2024 behavior, which I did not re-verify.

---

## 5. MCP status

### Takeaway
There is **no official Apple MCP support in iOS/iPadOS/macOS App Intents as of October 2026** that I could verify. The September 2025 iOS 26.1 beta code findings never became a documented API. Apple's only official MCP surface is **Xcode**: plugins that carry MCP tools, plus the `xcrun mcpbridge` server for external agents.

### Cited Findings
- In September 2025, 9to5Mac, AppleInsider, Heise and Computerworld reported MCP-related code in the iOS 26.1 / macOS 26.1 beta 1, tied to App Intents. Commentators expected Apple to act as an MCP client. Coverage said "an official announcement is probably still some time away." **[S]** Sources: [9to5Mac](https://9to5mac.com/2025/09/22/macos-tahoe-26-1-beta-1-mcp-integration/); [AppleInsider](https://appleinsider.com/articles/25/09/22/ios-26-could-get-a-major-ai-boost-with-the-model-context-protocol); [Computerworld](https://www.computerworld.com/article/4061614/apple-to-deploy-mcp-support-for-powerful-ai-experiences.html)
- None of the Apple WWDC26 pages I read mention OS-level MCP: the AI guide and sessions 240, 241, 242, 310, 319, 343, 345 and 382. In 382, MCP appears only as Xcode plugin content: "a plugin can contain skills… It can contain MCP tools." Source: [Session 382](https://developer.apple.com/videos/play/wwdc2026/382/)
- The iOS 27 beta 3 release-notes diff contains no MCP mention. Source: [gist](https://gist.github.com/galenguyer/eef52cf39cbb7745fe98f2e32f453590)
- One low-quality blog (SoftwareSeni) claims "Apple also adopted MCP system-wide in iOS 27, making registered MCP servers callable by Siri AI." This is **unverified and contradicted** by the absence of anything in Apple's sessions. Another analysis says Apple Intelligence does not call MCP tools. **[S]** Sources: [SoftwareSeni](https://www.softwareseni.com/why-apple-is-retiring-sirikit-and-what-app-intents-means-for-developers/); [blakecrosley.com](https://blakecrosley.com/blog/app-intents-vs-mcp-tools-frontier)

### Inferences
- Relic should treat App Intents as the "MCP of Apple." If Relic wants MCP, it would host its own MCP server for desktop agents on Mac, outside Apple's frameworks. On iPhone there is no system MCP client to plug into.

### Gaps
- I could not open the original 2025 articles (domains blocked), so the exact framework names in the beta code are unconfirmed.
- No iOS 27.x final release notes were checked.

---

## 6. macOS: Shortcuts, App Intents, Xcode agentic coding, computer use

### Takeaway
On the Mac:
- Shortcuts, Use Model and App Intents work as on iPhone. Visual Intelligence now covers screenshots on Mac.
- **Xcode 26.3 and 27** are Apple's agentic showcase:
  - Built-in agents from Anthropic, OpenAI and Google.
  - Agent Client Protocol for any agent, including local ones.
  - Plugins in Anthropic's skills/MCP format.
  - The `xcrun mcpbridge` MCP server.
  - Kernel-level file-access gating for agent subprocesses in macOS 27.
- Apple announced **no general "computer use" API** for third-party agents to drive arbitrary Mac apps.

### Cited Findings
- Session 382 on Xcode agents:
  - "we worked with Anthropic, OpenAI, Google to bring their agents right into Xcode."
  - "with… the Agent Client Protocol you can bring in any agent, any model, including ones that run locally right on your Mac."
  - Plugins are "a format created by Anthropic" and can contain skills (markdown) and MCP tools. They install from a GitHub URL, and Figma and GitHub have shipped plugins.
  - "There's a new setting in Xcode that enables file access at the kernel level… the kernel asks Xcode first", leveraging "new features in macOS 27."
  - Source: [Session 382](https://developer.apple.com/videos/play/wwdc2026/382/)
- Session 382 also states that ACP support shipped in an update to Xcode 26. **[S]** Source: [Session 382 via search snippet](https://developer.apple.com/videos/play/wwdc2026/382/)
- `xcrun mcpbridge`, per community sources (provisional; commands changed between betas) **[S]**:
  - It translates MCP over stdio into XPC calls to the running Xcode, and has been available since Xcode 26.3 with about 20 tools.
  - In the Xcode 27 betas it grows to about 48 tools, adds an "Allow external agents to use Xcode tools" gate, and adds a headless `xcrun mcp-server` in beta 5.
  - Sources: [Daniel Vaughan](https://codex.danielvaughan.com/2026/06/11/xcode-27-codex-cli-mcp-bridge-apple-agentic-coding-ios-macos-development/); [Reda Lemeden](https://redalemeden.com/derived-data/2026/what-new-in-xcode-27-mcp-bridge/); [Mehmet Baykar](https://mehmetbaykar.com/posts/how-to-run-xcode-27-mcp-server-headless-with-claude-code/)
- The `fm` CLI on macOS 27 gives the terminal access to the on-device and PCC models. Source: [Session 241](https://developer.apple.com/videos/play/wwdc2026/241/)
- Session 382 contains no computer-use or agent-drives-Mac-apps API. Source: [Session 382](https://developer.apple.com/videos/play/wwdc2026/382/)
- Siri AI is available on Mac in the EU, unlike iPhone. **[S]** Source: [Apple Newsroom Sep 2026](https://www.apple.com/newsroom/2026/09/siri-ai-a-profoundly-more-capable-and-personal-assistant-is-here/)

### Inferences
- A Mac companion for Relic is the place where it can be an agent host: MCP server, `fm` CLI, and background work without iOS limits. The iPhone app stays a capture and recall surface exposed through App Intents.

### Gaps
- No Apple docs page for `mcpbridge` was retrieved.
- Mac-specific Shortcuts or App Intents differences in 27 were not covered by the sessions I read.

---

## 7. Background execution for AI work

### Takeaway
Three background mechanisms are relevant:
- **`BGProcessingTask`** stays opportunistic. It can require external power and network, and the scheduler decides when it runs.
- **`BGContinuedProcessingTask`** (iOS/iPadOS 26) must start from an explicit user action and show system progress UI. Automatic jobs such as backups and photo syncing get cancelled. In practice, background GPU access was iPad-only in iOS 26.
- **iOS/macOS 27** restricts background **Neural Engine** access, which now needs a new `continued-processing.inference` entitlement.

`LongRunningIntent` (iOS 27) is the App Intents path to more than 30 seconds of background work, with a Live Activity and optional GPU.

### Cited Findings
- Session 227 "Finish tasks in the background" (WWDC25). Source: [Session 227](https://developer.apple.com/videos/play/wwdc2025/227/)
  - "Background execution isn't guaranteed… opportunistic, often discretionary, and tightly managed."
  - Scheduling considers network, CPU load, device activity, thermal state and battery, plus user settings: Low Power Mode, Background App Refresh and Low Data Mode.
  - **`BGProcessingTask`**: `requiresExternalPower` and `requiresNetworkConnectivity` can restrict runs to charging and network. Use cases include "ML model runs" and DB maintenance. Tasks must be registered at launch.
  - **`BGContinuedProcessingTask`**:
    - It must "always start with an explicit action that someone performs in your app, like a button tap."
    - "Avoid automatic workloads like maintenance, backups, or photo syncing… may lead to your app's task being canceled."
    - Tasks that report no progress are expired. Submission strategy is queue (the default) or `.fail`.
    - Background GPU is available "on supported devices"; query `supportedResources`, and requests for unavailable resources are rejected.
- The Apple doc says the system shows progress "in a Live Activity" that the user can cancel. **[S]** Source: [Apple docs: BGContinuedProcessingTask](https://developer.apple.com/tutorials/data/documentation/backgroundtasks/bgcontinuedprocessingtask.md)
- Forum report, February 2026: `supportedResources.contains(.gpu)` returns false on iPhone 15 Pro and 16 Pro under iOS 26. No Apple reply. The GPU entitlement is `com.apple.developer.background-tasks.continued-processing.gpu`. Source: [Apple Developer Forums 816774](https://developer.apple.com/forums/thread/816774)
- A forum thread reports a CPU/ML-intensive job running 4–5× slower in the background under BGContinuedProcessingTask on iOS 26. **[S]** Source: [Forums 807957](https://developer.apple.com/forums/thread/807957)
- iOS/macOS 27 beta 3 release notes:
  - "The system now restricts background access to the Neural Engine, similar to GPU usage restrictions." Background ANE access "requires the new entitlement" `com.apple.developer.background-tasks.continued-processing.inference`.
  - This replaced beta 2's "You cannot access the Neural Engine when your app is in the background."
  - Source: [gist diff of Apple SDK release notes](https://gist.github.com/galenguyer/eef52cf39cbb7745fe98f2e32f453590)
- `LongRunningIntent` has background GPU "on supported devices" for "on-device inference." Source: [Session 345](https://developer.apple.com/videos/play/wwdc2026/345/)

### Inferences
- Relic's routine on-device indexing and embedding (for example nightly memory consolidation) should use `BGProcessingTask` with `requiresExternalPower = true`. Expect it to be throttled and possibly run on CPU only.
- User-initiated "process my week" jobs fit `BGContinuedProcessingTask`, or `LongRunningIntent` when triggered from Siri or Shortcuts. ANE or GPU use needs entitlements, and on iPhone it may be unavailable.
- Whether Foundation Models on-device inference runs while backgrounded on iPhone is not documented. Plan for foreground or charging-only heavy inference, or use PCC.

### Gaps
- No Apple-published numeric quotas for BGProcessingTask runtime were found.
- The status of iPhone background GPU in iOS 27 is unknown.
- The `continued-processing.inference` entitlement is confirmed only through a release-notes diff gist, not an Apple page I opened.

---

## Blocked sources
These domains returned DNS failures (ENOTFOUND) when fetched, so their facts are snippet-only **[S]**:
- matthewcassinelli.com (WWDC26 App Intents session notes)
- wwdc.ai (session 343 summary)
- www.macrumors.com (Siri chatbot guide)
- www.macstories.net (iOS 27 review, Use Model article)
- 9to5mac.com (iOS 27 Shortcuts article, Siri AI requirements, 2025 MCP article)
- www.apple.com (Newsroom: Siri AI launch Sep 2026, June 2026 announcement; feature-availability page)
- support.apple.com (Apple Intelligence languages 121115; Shortcuts guide pages)
- appleinsider.com (2025 MCP report)
- www.heise.de (2025 MCP report)
- redalemeden.com (Xcode 27 MCP bridge)
- dev.to ("Apple Goes Agentic" recap)
- blakecrosley.com (App Intents vs MCP)

No GitHub sample code was cloned. Apple session code excerpts were enough within the tool budget.
