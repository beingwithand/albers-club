# Continuous Screen/Activity Capture ("Screen Memory"): Technical State of the Art, Privacy-Safe Design, Local AI Indexing (as of Oct 2026)

Research note: 15 tool calls were used. learn.microsoft.com, blogs.windows.com, docs.screenpi.pe and ioactive.com could not be fetched directly (DNS failures in this sandbox), so some Microsoft and Screenpipe facts rely on search snippets of those primary pages. Items marked "(unverified, from background knowledge)" appear only under Inferences or Gaps and have no citation.

## 1. OS capture APIs and platform constraints (macOS, Windows, Linux, Android, iOS)

### Takeaway
Desktop capture is feasible but more and more gated by the OS. macOS re-prompts for screen-recording permission every month. Windows gives apps a capture-exclusion flag that sensitive apps use against Recall. On Android, consent applies to one MediaProjection session at a time, and Google Play bans using AccessibilityService for anything that isn't a real accessibility tool. iOS cannot do background, all-app, continuous capture. The only route is a user-started ReplayKit broadcast, which has a 50 MB memory cap.

### Cited Findings
**macOS**
- In the macOS Sequoia (15) betas, Apple added recurring screen-recording consent prompts. These started as weekly, changed to monthly in beta 6 ("Allow For One Month"), and the prompts after restart or logout were dropped — [9to5Mac](https://9to5mac.com/2024/08/14/macos-sequoia-screen-recording-prompt-monthly/); [TechRadar](https://www.techradar.com/computing/mac-os/on-macos-sequoia-youll-only-have-to-deal-with-screen-recording-permission-pop-ups-once-a-month-rather-than-once-a-week)
- Developers reported that the monthly prompt also applies to apps built on modern ScreenCaptureKit, not only to apps using deprecated APIs. A "Persistent Content Capture" entitlement was floated as a way around it, but Apple gave no public guidance on getting it. One admin said MDM supervision cannot override the prompt — [TidBITS forum](https://talk.tidbits.com/t/apple-reduces-excessive-sequoia-permission-requests-shifts-to-monthly/28621); [TidBITS forum on avoiding prompts](https://talk.tidbits.com/t/how-to-avoid-sequoia-s-repetitive-screen-recording-permissions-prompts/28957)
- The Sequoia 15.1 beta 6 release notes said apps using "deprecated content capture technologies now have enhanced user awareness policies" — [TidBITS forum](https://talk.tidbits.com/t/apple-reduces-excessive-sequoia-permission-requests-shifts-to-monthly/28621)
- On macOS 26.1 (Tahoe), unbundled command-line executables could still capture after approval but did not appear in the "Screen & System Audio Recording" list. A background Unix executable that worked on 26.0.1 broke on 26.1. In practice, a capture daemon should ship as a signed .app bundle — [Apple Dev Forums 807898](https://developer.apple.com/forums/thread/807898); [Apple Dev Forums 807323](https://developer.apple.com/forums/thread/807323)
- On the macOS 27 beta, CGWindowListCopyWindowInfo returns blank window-owner names for other apps unless Screen Recording is granted, which is tighter than Tahoe — [Apple Dev Forums 839069](https://developer.apple.com/forums/thread/839069)
- An Apple DTS-style reply says there are two documented consent paths for capture: SCContentSharingPicker (a per-share picker) or the Screen Recording TCC grant. Continuous capture needs the TCC grant — [Apple Dev Forums 849969](https://developer.apple.com/forums/thread/849969)

**Windows**
- `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)` (Windows 10 2004+) hides a window from capture. Microsoft's own API page says it is "not a security feature or a DRM implementation", but Microsoft's Recall docs call it "this DRM flag" — [Microsoft Learn: SetWindowDisplayAffinity](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowdisplayaffinity); [IOActive, "The DRM flag that isn't DRM"](https://www.ioactive.com/the-drm-flag-that-isnt-drm/)
- Apps can turn the flag on and off as needed, for example only while sensitive content is on screen. Electron's `win.setContentProtection()` calls it on Windows and uses NSWindow sharingType on macOS — [Meziantou](https://www.meziantou.net/how-to-exclude-your-windows-app-from-screen-capture-and-recall.htm); [Electron docs commit](https://ayakael.net/mirrors/electron/commit/44bd560068d545a51c8300a0255983c90a0dc3e7)
- IOActive published "Signal Windows Desktop contentProtection bypass" (Aug 26, 2026). The page title shows the exclusion flag can be bypassed, but I could not fetch the details — [IOActive](https://www.ioactive.com/signal-windows-desktop-contentprotection-bypass)
- Recall export: available only in the EEA. Users can run a one-time export (7 days, 30 days, or all) or a continuous export that reminds them every 30 days. Export is user-initiated and per user, off by default on managed devices (`AllowRecallExport` policy), and the exported snapshots are encrypted. A third-party app needs both the export code and the folder path, and Microsoft does not store the code — [Microsoft Support](https://support.microsoft.com/en-us/Accessibility/windows/copilot/use-a-screen-reader-to-export-recall-snapshots-in-windows); [Windows Insider build 26120.4441](https://blogs.windows.com/windows-insider/2025/06/13/announcing-windows-11-insider-preview-build-26120-4441-beta-channel/); [Manage Recall](https://learn.microsoft.com/windows/client-management/manage-recall)
- The Click to Do management policy does not affect Click to Do inside Recall — [Manage Recall](https://learn.microsoft.com/windows/client-management/manage-recall)
- In 2026, fewer than 10% of Windows 11 PCs could run Recall, because it requires a Copilot+ PC — [GeekWire](https://www.geekwire.com/2026/one-year-after-its-rocky-launch-microsofts-windows-recall-still-raises-security-red-flags/)

**Android**
- Apps must get consent before each MediaProjection session (one `createVirtualDisplay()` call). The consent token is single-use, and reusing it on Android 14+ throws a SecurityException. Android 14 QPR2 added single-app (partial) screen sharing, which excludes the status bar, navigation bar and notifications. Android 15 adds callbacks for customizing partial sharing — [Android Developers: Media projection](https://developer.android.com/media/grow/media-projection)
- A third-party guide says Android 15 ends capture on the lock screen, hides notification content during projection, and exposes a recording-state callback — [Fora Soft](https://www.forasoft.com/blog/article/android-webrtc-screen-sharing) (secondary source)
- Google Play policy: `isAccessibilityTool` is only for services that help people with disabilities. Google's examples of apps that do not qualify include automation tools, assistants, monitoring apps, password managers and launchers. Other apps must show prominent disclosure and get consent. Using the Accessibility API to autonomously plan and execute actions is banned, while deterministic rule-based automation is allowed. Remote call-audio recording through Accessibility is banned — [Google Play Console Help: AccessibilityService API](https://support.google.com/googleplay/android-developer/answer/10964491?hl=en); [Engadget](https://www.engadget.com/google-is-banning-third-party-call-recording-apps-from-the-play-store-093201443.html)

**iOS**
- A ReplayKit Broadcast Upload Extension has a hard memory cap of about 50 MB, and the OS kills it if it goes over. On iPad the native-resolution buffers can exceed the cap. Common mitigations are downscaling below 1280x720, H.264 hardware encoding, and throttling to 15–30 fps — [Apple Dev Forums 651367](https://developer.apple.com/forums/thread/651367); [Zego FAQ](https://www.zegocloud.com/docs/faq/ios-screen-sharing-crash); [Fora Soft](https://www.forasoft.com/blog/article/how-to-implement-screen-sharing-in-ios-1193); [Twilio issue](https://github.com/twilio/twilio-video-ios/issues/16)

### Inferences
- **macOS design:** ship a bundled, signed app. Use ScreenCaptureKit (SCStream with per-window or per-app content filters) for pixels, and the Accessibility API (AXUIElement) for text, which is cheaper and more accurate than OCR when apps expose it. Expect the monthly re-consent prompt and design the onboarding and "capture paused" states around it.
- **Windows design:** use Windows.Graphics.Capture for frames and UI Automation for text. Respect WDA_EXCLUDEFROMCAPTURE windows, which come back black, and treat a black frame as a "sensitive app" signal rather than content.
- **Android:** you cannot run silent continuous capture. A MediaProjection session needs fresh consent each time and shows a system indicator. AccessibilityService is a Play-policy risk for a "memory" app because it is not an accessibility tool. NotificationListenerService (a separate special-access grant) is the lower-risk way to collect message and notification text. Sideloading or F-Droid distribution avoids the Play policy but not the OS consent.
- **iOS:** continuous background capture of other apps is effectively impossible. A broadcast must be started by the user, shows the red recording indicator, and runs under the 50 MB cap. Realistic phone strategies are imports (Screen Time is not exportable, so other sources are needed), the share sheet, and data exports.

### Gaps
- I could not fetch Apple ScreenCaptureKit docs or Android 15/16 release notes. Whether a "persistent content capture" entitlement is grantable to third parties is unconfirmed.
- I found no source on the Android 15 status-bar chip for screen sharing, NotificationListener policy changes in 2025–26, or Linux PipeWire/xdg-desktop-portal specifics. From background knowledge (unverified): on Wayland, apps must go through the ScreenCast portal, which shows a user picker and can remember the choice via `restore_token` in portal v4+. There is no global window-text API comparable to AX/UIA, though AT-SPI exists.
- The IOActive Aug 2026 bypass details were not retrieved.

## 2. Capture pipeline: diffing, OCR/VLM, audio ASR and diarization, resource costs

### Takeaway
Current tools (Screenpipe, Recall) combine event-driven or low-FPS frame capture, OS-native OCR or accessibility text, and local ASR. Published resource figures are rough: Screenpipe reports about 5–15% CPU, roughly 0.6–3 GB RAM, and 5–30 GB/month of storage depending on capture mode. Recall defaults to 90-day retention with a 75 GB threshold. For ASR, Parakeet TDT 0.6B v3 is about 7–10x faster than Whisper large-v3-turbo with similar or better English WER, but covers only 25 European languages.

### Cited Findings
- **Screenpipe storage:** the official architecture docs say about 30 GB/month at 1 FPS. The screenpi.pe FAQ says about 5–10 GB/month with event-driven capture (frames saved only on screen change). A third-party guide says about 20 GB/month — [Screenpipe architecture docs](https://docs.screenpi.pe/architecture); [screenpi.pe/about](https://screenpi.pe/about); [Mintlify performance guide](https://www.mintlify.com/screenpipe/screenpipe/advanced/performance)
- **Screenpipe CPU/RAM:** the docs say about 10% CPU and about 600 MB RAM typical. Other listings say 5–15% CPU and 0.5–3 GB RAM — same sources as above
- **Recall (per TotalRecall Reloaded analysis):** the main DB is `ukg.db` (SQLite SEE, AES-256-GCM) with 17 core tables (WindowCapture, App, Web, File, an FTS5 text index). Semantic indexes are `SemanticTextStore.sidb` and `SemanticImageStore.sidb` using DiskANN graphs. Default retention is 90 days with a 75 GB storage threshold. Data includes OCR text with word positions, window titles, URLs, file paths, dwell time, and AI-derived entities, topics and activity descriptions — [xaitax/TotalRecall](https://github.com/xaitax/TotalRecall)
- **Rewind** (Mac screen and audio memory) was shut down after Meta acquired its parent Limitless in Dec 2025. Capture was disabled on Dec 19, 2025, and users in the EU, UK, Brazil, China, Israel, South Korea and Turkey had until then to export their data before deletion — [9to5Mac](https://9to5mac.com/2025/12/05/rewind-limitless-meta-acquisition/); [BetaNews](https://betanews.com/2025/12/08/meta-has-acquired-limitless-a-startup-that-produces-ai-powered-wearables/); [Neowin](https://www.neowin.net/news/meta-acquires-ai-startup-limitless-ending-sales-of-its-popular-pendant-wearable)
- **Parakeet TDT 0.6B v3 vs Whisper large-v3-turbo:**
  - Speed: about 10x faster in vendor comparisons, with leaderboard RTFx of about 3,333 vs about 350. In an app-level M4 Pro test on a 5-minute clip, Parakeet took 2.91 s (103x realtime) and Turbo took 20.92 s (14.3x).
  - Accuracy: Open ASR English WER of about 6.32% vs about 7.83%.
  - Languages: Parakeet covers 25 European languages; Whisper covers 99+.
  - Silence: Parakeet reportedly does not hallucinate in silence, while Whisper can.
  - Sources (vendor/blog quality): [Parakeety](https://www.parakeety.com/resources/parakeet-v3-vs-whisper-large-v3-turbo); [WhisperNotes](https://whispernotes.app/blog/parakeet-v3-default-mac-model); [Northflank](https://northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2026-benchmarks); [OpenWhispr](https://openwhispr.com/blog/parakeet-vs-whisper-vs-nemotron)
  - A counterpoint post argues for Whisper turbo in production because of language coverage — [Arun Baby](https://www.arunbaby.com/speech-tech/0073-whisper-vs-parakeet-asr-decision/)
  - Qwen3-ASR is a 2026 alternative — [SnailText](https://snailtext.app/blog/parakeet-vs-whisper-turbo-vs-qwen3-asr/)

### Inferences
- **Recommended pipeline:**
  1. Trigger capture on events (app/window switch, scroll end, typing pause, clipboard) rather than at a fixed FPS.
  2. Run a cheap perceptual-hash or SSIM diff and drop near-duplicate frames.
  3. Prefer accessibility-tree text (AX/UIA). Fall back to native OCR (Apple Vision / Windows.Media.Ocr, both on-device and fast), then cross-platform RapidOCR/PaddleOCR (ONNX) or Tesseract.
  4. Reserve small VLMs (Florence-2, Moondream, Qwen-VL class) for occasional captioning or summarization, not per-frame.
- **ASR choice:** default to Parakeet for English and European languages, and Whisper turbo (whisper.cpp / MLX) for Korean and other languages. Use VAD gating to save battery and avoid hallucinations. Diarization: pyannote-class models (no source retrieved).
- The roughly 6x spread in Screenpipe's own storage figures (5 vs 30 GB/month) shows that capture policy, not codec, dominates storage.

### Gaps
- I found no reliable published benchmarks for OCR accuracy or speed on screen text (Apple Vision vs Windows OCR vs PaddleOCR/RapidOCR vs Florence-2/Qwen3-VL/Moondream), for OpenRecall resource use, or for Rewind's historical CPU and storage. From background knowledge (unverified), Rewind marketed heavy compression of about 14 GB/month. No battery-impact measurements were found for any tool.
- No diarization benchmarks (pyannote 3.x / community-1, NeMo Sortformer) were retrieved.

## 3. Compression, retention, dedupe

### Takeaway
Little primary data was retrieved. The main lesson from Screenpipe and Recall is that event-driven capture plus storing frames as video chunks plus time- or size-based retention (Recall: 90 days or 75 GB by default) keeps storage in the tens of GB.

### Cited Findings
- Screenpipe: event-driven capture brings storage to about 5–10 GB/month, compared with about 30 GB/month at fixed 1 FPS — [screenpi.pe/about](https://screenpi.pe/about); [Screenpipe architecture](https://docs.screenpi.pe/architecture)
- Recall: 90-day default retention and a 75 GB threshold — [xaitax/TotalRecall](https://github.com/xaitax/TotalRecall)

### Inferences
- **Codec and keyframes:** store frames as short (about 1–5 min) H.265 or AV1 segments, using screen-content tools where available (AV1 SCC/palette mode, HEVC SCC). Use long GOPs with forced keyframes on app switches so seeking is cheap. Keep the OCR/AX text and a thumbnail separately, so search never needs to decode video.
- **Tiered retention:** full frames for N days, then keyframes and thumbnails only, then text and metadata only. Dedupe by perceptual hash, and dedupe text by window+content hash.

### Gaps
- No primary benchmarks were found comparing H.265 vs AV1 for screen recordings at timeline-scrubbing frame rates, or any tool's keyframe policy.

## 4. Local search and AI: FTS, vectors, local LLMs, MCP

### Takeaway
The proven design is SQLite with FTS5 for exact text plus an ANN vector index for semantic search, running entirely locally. Recall uses exactly this (FTS5 plus DiskANN-backed `.sidb` stores). Exposing the store to assistants through MCP is now common (Screenpipe ships an MCP server), but every such server widens the attack surface.

### Cited Findings
- Recall uses an SQLite (SEE-encrypted) DB with an FTS5 index, plus separate semantic text and image stores on DiskANN — [xaitax/TotalRecall](https://github.com/xaitax/TotalRecall)
- Screenpipe is listed in MCP server directories, which expose its local data to AI assistants — [Glama](https://glama.ai/mcp/servers/isb2i5urdu); [mcpservers.org](https://mcpservers.org/de/servers/mediar-ai/screenpipe)

### Inferences
- A suitable stack: SQLite + FTS5 (trigram tokenizer suits OCR noise and CJK), sqlite-vec or LanceDB for embeddings (a small multilingual text model, plus optionally a CLIP/SigLIP model for image search), and a local 3–8B LLM via llama.cpp, MLX or Ollama for summaries and Q&A.
- An MCP server should be read-only by default, scope queries by time and app, apply redaction before returning results, and require per-session user approval. Prompt injection from captured screen text is a real risk, because any web page you viewed becomes LLM input.

### Gaps
- No benchmarks were retrieved for sqlite-vec vs LanceDB at the scale of millions of snippets, or on embedding model choice.

## 5. Security & privacy: Recall backlash and redesign, exclusions, threat models

### Takeaway
Recall is the cautionary case. It shipped in 2024 with a plaintext SQLite DB (extracted by the original TotalRecall). It was redesigned with VBS enclaves, Windows Hello, opt-in and filtering, and relaunched in April 2025. In 2026 it was still shown to leak to same-user code: TotalRecall Reloaded injects into the timeline-rendering process after Hello unlock, and MSRC called this "Not a Vulnerability". Encryption at rest does not protect against malware running as the user once data is decrypted for display. Third-party apps (Signal) rely on a capture-exclusion flag that has accessibility costs and itself has published bypasses.

### Cited Findings
- **Original TotalRecall (June 2024):** Alex Hagenah's tool showed that Recall data could be read without encryption. Microsoft delayed Recall on June 13, 2024 and announced a VBS-enclave redesign — [Malwarebytes](https://www.malwarebytes.com/blog/news/2024/06/microsoft-recall-snapshots-can-be-easily-grabbed-with-totalrecall-tool); [xaitax/TotalRecall](https://github.com/xaitax/TotalRecall)
- **Redesigned architecture:**
  - Keys are held in the TPM, tied to the user's Windows Hello Enhanced Sign-in Security identity, and usable only inside a VBS enclave, so other local users cannot decrypt. Microsoft claims isolation from kernel and admin users — [Manage Recall](https://learn.microsoft.com/en-us/windows/client-management/manage-recall); [Microsoft Support privacy page](https://support.microsoft.com/en-us/windows/privacy-and-control-over-your-recall-experience-d404f672-7647-41e5-886c-a3c59680af15); [Windows blog Sept 2024](https://blogs.windows.com/windowsexperience/2024/09/27/update-on-recall-security-and-privacy-architecture/)
  - Sensitive-info filtering covers passwords, credit card numbers and national IDs — [Windows Central](https://www.windowscentral.com/software-apps/windows-11/windows-recall-security-improvements-2024)
  - Recall relaunched in April 2025 — [GeekWire](https://www.geekwire.com/2026/one-year-after-its-rocky-launch-microsofts-windows-recall-still-raises-security-red-flags/)
- **Kevin Beaumont (2025–26):** "you can just read the database as a user process." The DB contains undisclosed activity-tracking fields, and no AV or EDR alerts fired — [Beaumont, Mastodon](https://cyberplace.social/@GossiTheDog/114360392836835836); [CSO Online](https://www.csoonline.com/article/4159643/microsofts-windows-recall-still-allows-silent-data-extraction.html); [GovInfoSecurity](https://www.govinfosecurity.com/microsoft-recall-again-spills-secrets-a-31083)
- **TotalRecall Reloaded (released Apr 9, 2026):**
  - Technique: same-user code injection into AIXHost.exe, the timeline renderer, which receives decrypted screenshots and OCR after Hello auth. The author also claims pre-auth screenshot retrieval and deletion capability.
  - Timeline: reported to MSRC on Mar 6, 2026 (Case 109586) and closed Apr 3, 2026 as "Not a Vulnerability... within the current, documented security design."
  - The writeup is internally inconsistent about which process is PPL-protected.
  - Source: [xaitax/TotalRecall](https://github.com/xaitax/TotalRecall)
- **Signal's Screen Security (May 2025):**
  - Signal's Windows 11 app sets the DRM/capture-exclusion flag on its window by default, because "Microsoft has simply given us no other option" to exclude apps from Recall. Screenshots come out black.
  - It can break screen readers such as Narrator, and it only protects the local machine — [TechRadar](https://www.techradar.com/computing/windows/signal-blasts-microsoft-over-recall-privacy-failings-as-secure-messaging-app-is-forced-to-fudge-a-way-of-blocking-the-controversial-windows-11-feature); [BetaNews](https://betanews.com/2025/05/21/signal-declares-war-on-microsoft-recall-with-screenshot-blocking-on-windows-11/); [CyberInsider](https://cyberinsider.com/signal-deploys-countermeasure-to-shield-messages-from-windows-recall/)
  - IOActive argues that WDA_EXCLUDEFROMCAPTURE is not DRM and is marketed beyond its guarantees, and published a Signal contentProtection bypass in Aug 2026 — [IOActive](https://www.ioactive.com/the-drm-flag-that-isnt-drm/); [IOActive bypass](https://www.ioactive.com/signal-windows-desktop-contentprotection-bypass)

### Inferences
- **Threat model to design for:**
  1. Infostealers running as the user. This is the dominant threat: a screen-memory DB is a single high-value target holding credentials, chats and finances.
  2. Physical or co-located abusers (partners, family) with the device password, which raises stalkerware concerns.
  3. Prompt injection via MCP/LLM.
  4. Cloud or sync leaks.
  5. Vendor or acquirer policy change (the Rewind/Meta precedent).
- **Mitigations:**
  - Opt-in per source.
  - Visible capture indicator and pause hotkey.
  - Default exclusions: password managers, banking, incognito/private windows, any window with the capture-exclusion flag, secure text fields (AX `AXSecureTextField`, UIA `IsPassword`), and DRM content.
  - PII redaction before indexing (regex plus a NER model for cards, IDs, Korean RRN 주민등록번호, tokens, API keys).
  - Encryption at rest with keys bound to the OS keystore and biometric (Keychain/Secure Enclave, TPM/Hello, Android Keystore).
  - Re-auth to view, a short decrypted-in-memory window, and a hardened viewer process. Recall's AIXHost lesson: protect the viewer, not just the DB.
  - Local-only by default, no telemetry of content, one-click wipe, and data export in open formats.

### Gaps
- No primary source was retrieved for Recall's private-browsing / DRM auto-exclusion behavior or the Sept 2024 blog's full content (fetch failed). Microsoft Purview / enterprise filtering details are unverified.
- Stalkerware-specific analysis of screen-memory apps (e.g., Coalition Against Stalkerware) was not retrieved.

## 6. Legal: recording consent and capturing others' content

### Takeaway
Capturing your own screen is generally lawful. Recording audio of conversations is not: about 11–13 US states require all-party consent, and Korean law makes third-party interception a serious crime. An always-on audio feature must default to off or to the user's own mic only, with clear consent tooling. Under current Korean law, participant recording is not criminal but can create civil liability, and a 2022 bill to require all-party consent was proposed.

### Cited Findings
- **US:** the federal Wiretap Act allows one-party consent. Commonly listed all-party states are CA, CT, DE, FL, IL, MD, MA, MT, NV, NH, PA and WA, with MI and OR disputed or partial (Oregon is all-party for in-person conversations). Rules differ between phone and in-person recording. Interstate calls are usually treated under the stricter rule, and California claims jurisdiction — [Layer3 Labs guide (Aug 2026)](https://www.layer3labs.io/guides/two-party-consent-states); [Viirtue 2026](https://viirtue.com/call-recording-consent-laws-by-state-2026-guide/); [Brass Transcripts](https://brasstranscripts.com/blog/state-by-state-recording-laws-2026-guide) (secondary sources)
- **South Korea (통신비밀보호법, Communications Privacy Protection Act):**
  - A participant recording their own conversation is not criminal, but civil damages are possible under the "right of voice" (음성권).
  - A non-participant (third party) recording or eavesdropping faces 1–10 years in prison, even if one party consented.
  - A 2022 bill (Rep. Yoon Sang-hyun) proposed requiring all-party consent, with a 1–10 year penalty. Its passage was not confirmed.
  - Sources: [Segye Ilbo](https://www.segye.com/newsView/20220822516779); [Financial News](https://www.fnnews.com/news/202208231757456797)

### Inferences
- An app that captures meeting audio, including the other side of calls, makes the user the recorder. In all-party US states, and for any non-participant capture in Korea, this creates criminal exposure. Product defaults should be: mic-only or no audio by default, a per-meeting consent prompt or announcement, and geo-aware warnings.
- Screen capture of others' messages for personal use is broadly low-risk legally, but GDPR applies if data leaves the purely personal or household sphere (e.g., sync to a company cloud or sharing).

### Gaps
- Not retrieved: EU and member-state specifics (e.g., Germany's §201 StGB criminalizing non-public spoken-word recording; GDPR household exemption case law), the current status of the Korean 2022 bill, and Korea PIPA implications for an app vendor processing captured third-party data. These need primary statutory sources (law.go.kr, EUR-Lex) or counsel.
