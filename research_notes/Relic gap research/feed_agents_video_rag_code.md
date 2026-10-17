# Feed agents, app-control agents and video RAG: code-level teardown for Relic (as of 2026-10-17)

Purpose: learn the real implementation patterns (perception, action loop, video understanding, structured extraction, app access) from code, so Relic can capture and understand the user's own viewing on their own devices, with consent.

Method: shallow clones (`git clone --depth 1`) read only. Nothing was installed or run. Commits pinned below; all code links use `blob/<commit>/path#Lnn`.

| Repo | Commit | License |
|---|---|---|
| droidrun/droidrun (Python package now named `mobilerun`) | 3018561 | MIT |
| minitap-ai/mobile-use | 7b89fde | Apache-2.0 |
| TencentQQGYLab/AppAgent | 2c19004 | MIT |
| callstackincubator/agent-device | 4c1c786 | MIT |
| X-PLUG/MobileAgent (v1 to v3.5, GUI-Owl) | 11cea57 | MIT |
| google-research/android_world | 30583e2 | Apache-2.0 |
| browser-use/browser-use | ccd22fe | MIT |
| browserbase/stagehand | 10418f9 | MIT |
| HKUDS/VideoRAG (VideoRAG-algorithm + Vimo desktop) | c412a09 | Dual: MIT framework, plus "various licenses" for the bundled third-party model implementation |
| YueFan1014/VideoAgent (ECCV 2024) | 42e1b70 | Apache-2.0 |
| Breakthrough/PySceneDetect | 93ce59e | BSD-3-Clause |
| yt-dlp/yt-dlp | 8973412 | Unlicense (public domain) |
| netCrunch/LikeVault | 2c99d67 | GPL-3.0 (copyleft: study it, do not copy it) |

## Q1. Phone and app control agents: perception, action space, loop, scrolling and new-item detection, memory, recovery, ADB and accessibility mechanics, iOS

### Takeaway
The mature open-source phone agents all use **both** senses: an accessibility (a11y) tree as the primary, indexed and actionable representation, plus a screenshot for visual context and checking. They read the tree through an on-device accessibility service (droidrun Portal, the android_world a11y forwarder) or `uiautomator dump`, and they act through ADB `input` or an on-device service. The loop is planner, then executor, then reflector/verifier, with append-only notes as memory. "Did the scroll produce new content?" is answered by diffing before and after states. None of them has a dedicated "new feed item" detector; Relic has to build one, keyed on content IDs. iOS control in every repo needs XCTest/WebDriverAgent developer tooling, so it is not viable for consumer iOS.

### Cited Findings
**droidrun / mobilerun (MIT)**
- Perception goes through `StateProvider.get_state()`. `AndroidStateProvider` "fetches state from an Android device via `driver.get_ui_tree()`", with "retry logic with exponential backoff and mid-retry recovery (accessibility service restart) for robustness against intermittent Portal/a11y failures" — [provider.py#L208-L225](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/tools/ui/provider.py#L208).
- The tree comes from droidrun's on-device "Portal" APK. It is an accessibility service, also registered as an IME for text entry, and it is queried over an ADB content provider (`content query --uri ... state`) or over a socket server on port 8080 — [cli/doctor.py#L31, L292, L434, L456, L623](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/cli/doctor.py#L31).
- Vision mode resizes the screenshot to the model's exact grounding dimensions and overlays a labelled 10×10 coordinate grid, so model coordinates map back to device pixels — [provider.py#L180-L205](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/tools/ui/provider.py#L180).
- Tree filtering drops nodes that are off-screen or smaller than 5 px — [concise_filter.py#L19-L60](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/tools/filters/concise_filter.py#L19). The formatter flattens the tree into indexed elements and prepends a phone-state header (current app and package, keyboard visible, focused element) — [indexed_formatter.py#L24-L80](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/tools/formatters/indexed_formatter.py#L24).
- Action space: `click(index)`, `long_press(index)`, `click_at(x,y)`, `click_area`, `type_text`, `system_button(back/home/enter)`, `swipe`, `open_app`, `wait`, `complete`, `type_secret` — [agent/utils/actions.py#L258-L615](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/agent/utils/actions.py#L258).
- Manager prompt structure: `<user_request>`, `<app_card>` (per-app operating notes), `<potentially_stuck>` (error history listing action, summary and feedback), and guidelines. Memory is append-only `<add_memory>` with "At step X, I obtained [information] from [source]". An `output_schema` block lists required fields to collect before `<request_accomplished>` — [config/prompts/manager/system.jinja2](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/config/prompts/manager/system.jinja2).
- **Deterministic macro record and replay**: recorded trajectories replay as macros. Before each step, the saved UI state is compared to the live one with Jaccard similarity over semantic node keys (weight 0.85) plus phone-state similarity (0.15), threshold 0.85. On a mismatch the run hands off to the LLM agent (`run_agent_handoff`) — [macro/matcher.py#L18-L43](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/macro/matcher.py#L18), [macro/replay.py#L1-L40](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/macro/replay.py#L1).
- Counter-example (not described further): droidrun ships a "stealth" UI state that randomizes taps to look less automated — [stealth_state.py](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/tools/ui/stealth_state.py). Relic should not copy it.
- An iOS provider exists (`tools/ui/ios_provider.py`), and its docstring notes that iOS taps use XCTest points — [provider.py#L150-L158](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/tools/ui/provider.py#L150).

**minitap mobile-use (Apache-2.0)**
- Multi-agent LangGraph with planner, orchestrator, cortex, executor, contextor, hopper, summarizer, outputter and **video_analyzer** — [agents/](https://github.com/minitap-ai/mobile-use/tree/7b89fde/minitap/mobile_use/agents).
- Perception: `adb shell uiautomator dump /dev/tty` — [services/accessibility.py#L29-L60](https://github.com/minitap-ai/mobile-use/blob/7b89fde/minitap/mobile_use/services/accessibility.py#L29). It also takes a screenshot and gets the foreground app via `dumpsys window | grep mCurrentFocus` — [android_controller.py#L245-L250](https://github.com/minitap-ai/mobile-use/blob/7b89fde/minitap/mobile_use/controllers/android_controller.py#L245). iOS goes through WDA and IDB clients (`clients/wda_client.py`, `clients/idb_client.py`).
- Cortex prompt rules worth copying ([cortex.md](https://github.com/minitap-ai/mobile-use/blob/7b89fde/minitap/mobile_use/agents/cortex/cortex.md)):
  - "UI Hierarchy: find elements by resource-id, text, bounds — no visual info", and "Screenshot: visual context … can't reliably extract precise element coordinates", so "combine your 2 senses".
  - Targets carry `resource_id` + `resource_id_index` + `bounds` + `text` + `text_index`, with the fallback order ID, then bounds, then text.
  - "Unpredictable actions (back, launch_app, open_link, navigation taps) MUST be the ONLY action in that turn."
  - "Complete goals only on OBSERVED evidence."
  - "Data Fidelity: transcribe content exactly as-is."
  - Swipe physics: "swipe RIGHT → reveals LEFT page".
- Screen recording: `adb shell screenrecord --time-limit 180` is chained into segments by an auto-restart loop, joined with ffmpeg, then compressed to ≤14 MB for the API — [android_controller.py#L312-L345](https://github.com/minitap-ai/mobile-use/blob/7b89fde/minitap/mobile_use/controllers/android_controller.py#L312), [utils/video.py#L18-L26, L119-L180](https://github.com/minitap-ai/mobile-use/blob/7b89fde/minitap/mobile_use/utils/video.py#L18).
- Video analyzer: sends the whole mp4 (`mime_type video/mp4`) to a video-capable Gemini model — [video_analyzer.py#L22-L60](https://github.com/minitap-ai/mobile-use/blob/7b89fde/minitap/mobile_use/agents/video_analyzer/video_analyzer.py#L22). System prompt: focus on "UI elements and their states, text content, actions (taps, scrolls, transitions), notifications, changes over time, audio content (transcribe speech)", "use timestamps (e.g., 'At 0:05…')", "note uncertainty" — [video_analyzer.md](https://github.com/minitap-ai/mobile-use/blob/7b89fde/minitap/mobile_use/agents/video_analyzer/video_analyzer.md).
- App-lock "Contextor": if the foreground package differs from the locked app, the default is RELAUNCH unless the deviation is intentional, necessary and a valid pattern (OAuth, payment, permissions). Output is `{should_relaunch_app, reasoning}` — [contextor.md](https://github.com/minitap-ai/mobile-use/blob/7b89fde/minitap/mobile_use/agents/contextor/contextor.md).

**AppAgent (Tencent, MIT)**
- Perception and control are plain ADB: `screencap -p`, `uiautomator dump`, `input tap|text|swipe|keyevent KEYCODE_BACK`, and long-press done as a zero-distance swipe with a 1000 ms duration — [and_controller.py#L104-L178](https://github.com/TencentQQGYLab/AppAgent/blob/2c19004/scripts/and_controller.py#L104).
- Set-of-Marks: interactive elements from the XML are drawn as numeric tags on the screenshot. Actions are `tap(element)`, `text("...")`, `long_press(element)`, `swipe(element, dir, short|medium|long)`, plus `grid()` as a fallback for untagged areas — [prompts.py#L43-L83](https://github.com/TencentQQGYLab/AppAgent/blob/2c19004/scripts/prompts.py#L43).
- Exploration builds per-element "documentation" from before and after screenshots (`tap_doc_template`, `swipe_doc_template`, `refine_doc_suffix`), and the docs are reused at task time. This is the origin of droidrun's "app cards" — [prompts.py#L1-L41](https://github.com/TencentQQGYLab/AppAgent/blob/2c19004/scripts/prompts.py#L1).

**Mobile-Agent-v3 / Mobile-Agent-E (X-PLUG, MIT)**
- Agents: Manager, Executor, ActionReflector and Notetaker, sharing one `InfoPool` — [mobile_v3/utils/mobile_agent_e.py#L7-L351](https://github.com/X-PLUG/MobileAgent/blob/11cea57/Mobile-Agent-v3/mobile_v3/utils/mobile_agent_e.py#L7).
- **Reflector scroll-end rule (verbatim)**: "For swiping to scroll the screen to view more content, if the content displayed before and after the swipe is exactly the same, the swipe is considered to be C: Failed. The last action produces no changes. This may be because the content has been scrolled to the bottom." Outcomes are A (success), B (wrong page, go back) and C (no change) — [#L289-L308](https://github.com/X-PLUG/MobileAgent/blob/11cea57/Mobile-Agent-v3/mobile_v3/utils/mobile_agent_e.py#L289).
- **Notetaker (verbatim core)**: "Your goal is to take notes of important content relevant to the user's request… Do not take notes on low-level actions; only keep track of significant textual or visual information… Do not make up content…" Output is "### Important Notes ###", which merges old and new notes — [#L317-L351](https://github.com/X-PLUG/MobileAgent/blob/11cea57/Mobile-Agent-v3/mobile_v3/utils/mobile_agent_e.py#L317).

**android_world (Google, Apache-2.0)**
- There are two ways to get the a11y tree: `A11Y_FORWARDER_APP` (a custom gRPC wrapper around an a11y forwarding app, `latest_a11y_info_only=True`) or `UIAUTOMATOR` (`uiautomator dump`) — [android_world_controller.py#L125-L172](https://github.com/google-research/android_world/blob/30583e2/android_world/env/android_world_controller.py#L125).
- `UIElement` schema: text, content_description, class_name, bbox, bbox_pixels, hint_text, is_checked/checkable/clickable/editable/enabled/focused/focusable/long_clickable/scrollable/selected/visible, package_name, resource_name, tooltip, resource_id — [representation_utils.py#L53-L78](https://github.com/google-research/android_world/blob/30583e2/android_world/env/representation_utils.py#L53).
- Canonical JSON action space: answer, click, double_tap, input_text, keyboard_enter, long_press, navigate_back, navigate_home, open_app, scroll, status, swipe, wait — [json_action.py#L24-L37](https://github.com/google-research/android_world/blob/30583e2/android_world/env/json_action.py#L24). The M3A prompt warns that "the direction parameter for the `scroll` action can be confusing" (scroll is the opposite of swipe) — [agents/m3a.py#L113-L118](https://github.com/google-research/android_world/blob/30583e2/android_world/agents/m3a.py#L113).

**agent-device (Callstack, MIT)**
- Covers iOS, Android, HarmonyOS, TV, web, macOS and Linux. "Agents read token-efficient accessibility snapshots instead of reasoning over screenshots alone, act through refs and selectors." Refs are only valid in the latest snapshot, and `--settle` returns a diff — [README.md#L20, L78](https://github.com/callstackincubator/agent-device/blob/4c1c786/README.md#L20).
- Mechanics: "a local accessibility bridge for iOS Simulator snapshots and XCTest for iOS interactions, physical iOS, and tvOS; ADB and the snapshot helper on Android; … a local helper on macOS; and AT-SPI on Linux" — [README.md#L158](https://github.com/callstackincubator/agent-device/blob/4c1c786/README.md#L158). The iOS runner is an XCUITest bundle — [apple/runner/AgentDeviceRunner/AgentDeviceRunnerUITests/](https://github.com/callstackincubator/agent-device/tree/4c1c786/apple/runner/AgentDeviceRunner/AgentDeviceRunnerUITests).

### Inferences
- **New-item detection** happens in three places in the code:
  1. Mobile-Agent's whole-screen before/after equality, used to detect the end of a scroll.
  2. droidrun's Jaccard over semantic node keys, used for macro state matching.
  3. browser-use's set difference of node IDs (see Q2).

  For a feed, Relic should key on a **content identity** (video ID from a deep link or share URL, or caption + creator handle from a11y text, or a perceptual hash of the dominant frame) and keep a seen-set. None of the phone agents does this out of the box.
- The a11y tree from feed apps (TikTok, Reels, Shorts) often exposes creator handle, caption and like/comment counts as `content_description`/`text`, but video pixels are a SurfaceView with no text. So Relic needs a11y text for metadata plus screen capture for content. The repos show the a11y/screenshot fusion pattern but none tests it against feed apps specifically (unverified).
- On iOS, all control paths (WDA, IDB, XCTest) require a Mac with Xcode or developer signing, so iOS agentic control is out of scope for a consumer Relic.

### Gaps
- No repo has a feed-specific dwell-time tracker (time on each item). This is inferred as something Relic must build.
- I did not open droidrun's Portal APK source (a separate repo, droidrun-portal) to confirm exactly which AccessibilityEvent types it listens to.

## Q2. Browser agents relevant to feeds: DOM vs vision, extraction schemas, infinite scroll, action caching

### Takeaway
browser-use serializes a filtered DOM with indexed interactive elements, marks **new elements since the last step with `*`**, reports pages above and below for scroll context, and offers an `extract` action that converts page markdown to JSON Schema output, with chunking and `already_collected` de-duplication across pagination. That is the cleanest infinite-scroll extraction pattern found. Stagehand has moved to a Chrome-extension runtime (MV3, `debugger` permission) with zod-schema `extract()`, and its action/extract caching is now **server-side on Browserbase**, which makes it unsuitable for a local-first Relic.

### Cited Findings
- browser-use `extract` action description: "LLM extracts structured data from page markdown… Use start_from_char if previous extraction was truncated… When paginating across pages, pass already_collected with item identifiers (names/URLs) from prior pages to avoid duplicates." It uses `MAX_CHAR_LIMIT = 100000` and structure-aware chunking (`chunk_markdown_by_structure`) with an overlap prefix (for example, table headers) — [tools/service.py#L1067-L1145](https://github.com/browser-use/browser-use/blob/ccd22fe/browser_use/tools/service.py#L1067).
- browser-use structured-extraction system prompt (verbatim) — [tools/service.py#L1167-L1180](https://github.com/browser-use/browser-use/blob/ccd22fe/browser_use/tools/service.py#L1167):
  > You are an expert at extracting structured data from the markdown of a webpage. <input> You will be given a query, a JSON Schema, and the markdown of a webpage that has been filtered to remove noise and advertising content. </input> <instructions> - Extract ONLY information present in the webpage. Do not guess or fabricate values. - Your response MUST conform to the provided JSON Schema exactly. - If a required field's value cannot be found on the page, use null … - If the content was truncated, extract what is available from the visible portion. - If <already_collected> items are provided, skip any items whose name/title/URL matches those listed — do not include duplicates. </instructions>

  The JSON-Schema dict is converted to a Pydantic model via `schema_dict_to_pydantic_model` — [tools/extraction/schema_utils.py](https://github.com/browser-use/browser-use/blob/ccd22fe/browser_use/tools/extraction/schema_utils.py).
- New-node marking: if `(session_id, backend_node_id)` is not in `_previous_node_ids`, then `node.is_new = True`, and the serializer prefixes such elements with `*` — [dom/serializer/serializer.py#L759-L766, L1032](https://github.com/browser-use/browser-use/blob/ccd22fe/browser_use/dom/serializer/serializer.py#L759).
- Scroll context given to the LLM: "{pages_above:.1f} pages above, {pages_below:.1f} pages below", computed from `pixels_above/below ÷ viewport_height` — [agent/prompts.py#L267-L272](https://github.com/browser-use/browser-use/blob/ccd22fe/browser_use/agent/prompts.py#L267). The `scroll` action reads the actual viewport height via CDP — [tools/service.py#L1383-L1400](https://github.com/browser-use/browser-use/blob/ccd22fe/browser_use/tools/service.py#L1383).
- Stagehand extract system prompt: "You are extracting content on behalf of a user. If a user asks you to extract a 'list' of information, or 'all' information, YOU MUST EXTRACT ALL… Print the exact text from the DOM elements with all symbols, characters, and endlines as is. Print null or an empty string if no new information is found." It optionally includes a screenshot, and links are returned as element IDs, not text — [packages/extension/prompt.ts#L47-L87](https://github.com/browserbase/stagehand/blob/10418f9/packages/extension/prompt.ts#L47).
- Stagehand runtime is an MV3 extension with `permissions: ["debugger","offscreen","scripting","tabs"]`, `<all_urls>`, and a content script at `document_start` in all frames — [packages/extension/manifest.json](https://github.com/browserbase/stagehand/blob/10418f9/packages/extension/manifest.json).
- Caching: "the API server owns all cache-key computation (DOM shaping/hashing, URL normalization)" — [services/cacheService.ts#L27-L28](https://github.com/browserbase/stagehand/blob/10418f9/packages/extension/services/cacheService.ts#L27). The example says "Server-side caching requires a Browserbase browser session", and `extract(instruction, zodSchema, {cache:{threshold:1}})` — [sdk-ts/examples/caching.ts](https://github.com/browserbase/stagehand/blob/10418f9/packages/sdk-ts/examples/caching.ts).

### Inferences
- For Relic's desktop capture, an LLM browser agent is the wrong tool for **passive** capture. Interception (Q4) is cheaper and exact. browser-use's `already_collected` and `*new` patterns are still the right model for an **on-demand** agent ("go through my saved videos and summarize them").
- Stagehand's local-cache equivalent would have to be rebuilt. The cheapest pattern is droidrun-style recorded macros keyed by a DOM/a11y fingerprint, with LLM fallback.

### Gaps
- I did not verify whether browser-use has a dedicated infinite-scroll "until no new elements" helper. The behaviour seems to be emergent from the `*` marker plus `pages below`.

## Q3. Video understanding and video RAG pipelines: sampling, scene detection, captioning prompts, ASR, schemas, indexing

### Takeaway
Two working patterns exist:
1. **Whole-clip to a native video model** (mobile-use sends the mp4 to Gemini).
2. **Segment, sample frames, ASR, caption with a VLM using the transcript in the prompt, then index text and visual embeddings** (VideoRAG: 30 s segments, 5 frames each, faster-distil-whisper, MiniCPM-V captions, ImageBind embeddings, plus a LightRAG-style entity graph; VideoAgent: 2 s captions from 4 frames, with a SQL object-tracking memory and tool calls).

For short-form clips (≤3 min), scene-cut sampling (PySceneDetect or ffmpeg `select=scene`) plus pixel-diff dedup plus ASR plus one structured VLM call per clip is the right size.

### Cited Findings
- VideoRAG defaults: `video_segment_length = 30` s, `rough_num_frames_per_segment = 5`, `fine_num_frames_per_segment = 15`, `video_embedding_dim = 1024`, `chunk_token_size = 1200` — [videorag.py#L67-L94](https://github.com/HKUDS/VideoRAG/blob/c412a09/VideoRAG-algorithm/videorag/videorag.py#L67).
- Splitting uses `np.linspace(0, subvideo_length, num_frames_per_segment, endpoint=False)` over moviepy subclips — [_videoutil/split.py#L10-L42](https://github.com/HKUDS/VideoRAG/blob/c412a09/VideoRAG-algorithm/videorag/_videoutil/split.py#L10).
- ASR uses `faster_whisper.WhisperModel("./faster-distil-whisper-large-v3")` per segment — [_videoutil/asr.py#L5-L24](https://github.com/HKUDS/VideoRAG/blob/c412a09/VideoRAG-algorithm/videorag/_videoutil/asr.py#L5).
- Caption prompts (MiniCPM-V-2_6-int4; frames plus text) — [_videoutil/caption.py#L28, L73](https://github.com/HKUDS/VideoRAG/blob/c412a09/VideoRAG-algorithm/videorag/_videoutil/caption.py#L28):
  - Index-time prompt (verbatim): `"The transcript of the current video:\n{segment_transcript}.\nNow provide a description (caption) of the video in English."`
  - Query-time refinement prompt: `"...Now provide a very detailed description (caption) of the video in English and extract relevant information about: {refine_knowledge}"`
- Visual retrieval uses ImageBind segment embeddings and `encode_string_query` — [_videoutil/feature.py#L5-L20](https://github.com/HKUDS/VideoRAG/blob/c412a09/VideoRAG-algorithm/videorag/_videoutil/feature.py#L5). Graph extraction uses entity types `["organization","person","geo","event"]` with `<|>` / `##` delimiters — [prompt.py#L137-L140](https://github.com/HKUDS/VideoRAG/blob/c412a09/VideoRAG-algorithm/videorag/prompt.py#L137). Storage backends are nano-vectordb/hnswlib, networkx/neo4j and JSON KV — [_storage/](https://github.com/HKUDS/VideoRAG/tree/c412a09/VideoRAG-algorithm/videorag/_storage).
- VideoAgent memory: `seconds_per_caption = 2`, `frames_per_caption = 4` — [captioning.py#L24-L25](https://github.com/YueFan1014/VideoAgent/blob/42e1b70/captioning.py#L24). A SQL memory holds tables `Objects(object_id, category)`, `Segments(segment_id)` and `Objects_Segments` — [database.py#L48-L71](https://github.com/YueFan1014/VideoAgent/blob/42e1b70/database.py#L48). Tools are `query_database`, `retrieve_candidate_objects`, `caption_retrieval(start,end)`, `segment_localization` (text-embedding-3-large plus ViCLIP) and `visual_question_answering` — [tools.py#L57-L213](https://github.com/YueFan1014/VideoAgent/blob/42e1b70/tools.py#L57).
- PySceneDetect `ContentDetector` defaults are `threshold=27.0` and `min_scene_len=15` (frames) — [content_detector.py#L106-L107](https://github.com/Breakthrough/PySceneDetect/blob/93ce59e/scenedetect/detectors/content_detector.py#L106).
- claude-real-video (MIT) samples with one ffmpeg `select` pass for scene changes (`--scene 0.30`) plus a floor of one frame every 1.0 s, capped at 150 frames. Dedup is a pixel diff on downscaled RGB against the last 4 kept frames, keeping a frame only if ≥8% of pixels changed. Existing subtitles are preferred, with Whisper as the fallback. Optional 9-frame contact-sheet grids — [PyPI claude-real-video 0.7.0](https://pypi.org/project/claude-real-video/0.7.0/) (repo: https://github.com/HUANGCHIHHUNGLeo/claude-real-video; not cloned).
- The mobile-use video analyzer prompt (copied in Q1) is a ready-made screen-recording understanding prompt with timestamps — [video_analyzer.md](https://github.com/minitap-ai/mobile-use/blob/7b89fde/minitap/mobile_use/agents/video_analyzer/video_analyzer.md).

### Inferences
- VideoRAG's 30 s segments are sized for long lectures. For TikTok-length clips, one "segment" equals one video, so captioning collapses to a single structured call per watched item, and RAG works over a per-item record rather than over chunks.
- Putting the transcript into the caption prompt (VideoRAG) is the key trick: it grounds on-screen events in speech, which matters because short-form content is often talking-head.
- Prefer platform subtitles over local Whisper when available (claude-real-video's ordering; yt-dlp exposes TikTok `subtitleInfos`, see Q4).

### Gaps
- No repo found ships a validated JSON schema for short-video understanding. The schema in Q5 is a synthesis.
- vidwit and other "shorts summarizer" repos were only seen in search snippets, not cloned.

## Q4. Short-video data extraction: yt-dlp TikTok fields, and local watch-history extensions

### Takeaway
TikTok web pages embed the full item JSON in `<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">` under `__DEFAULT_SCOPE__["webapp.video-detail"].itemInfo.itemStruct`; the legacy location is `SIGI_STATE`. Feed and list API responses expose `itemList` / `item_list` / `aweme_list`. LikeVault (GPL-3.0) shows the exact local-first pattern: a MAIN-world content script wraps `fetch`/XHR, clones matching `item_list` responses, and `postMessage`s normalized items to an isolated content script that stores them in IndexedDB. It does this only for likes and favourites; Relic would extend the same idea to the For You feed and add dwell time.

### Cited Findings
- yt-dlp locates page data with `<script id="(SIGI_STATE|sigi-persisted-data)">` and `<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">` → `__DEFAULT_SCOPE__` — [extractor/tiktok.py#L109-L118](https://github.com/yt-dlp/yt-dlp/blob/8973412/yt_dlp/extractor/tiktok.py#L109). The video object is `webapp.video-detail → itemInfo → itemStruct`, and `statusCode` / `isContentClassified` mark gated posts — [#L327-L334](https://github.com/yt-dlp/yt-dlp/blob/8973412/yt_dlp/extractor/tiktok.py#L327).
- Field map in `_parse_aweme_video_web` — [#L659-L705](https://github.com/yt-dlp/yt-dlp/blob/8973412/yt_dlp/extractor/tiktok.py#L659):

  | Source in `itemStruct` | yt-dlp field |
  |---|---|
  | author/authorInfo `nickname` | channel |
  | `secUid`/`authorSecId` | channel_id |
  | `uniqueId` | uploader |
  | `id`/`uid`/`authorId` | uploader_id |
  | `music.title` | track |
  | `music.album` | album |
  | `music.authorName` | artists |
  | `music.duration` | (music) duration |
  | `desc` | title (truncated to 72) and description |
  | `video.duration` | duration |
  | `createTime` | timestamp |
  | `stats.playCount` | view_count |
  | `stats.diggCount` | like_count |
  | `stats.shareCount` | repost_count |
  | `stats.commentCount` | comment_count |
  | `stats.collectCount` | save_count |
  | `cover`/`originCover`/`dynamicCover` | thumbnails |

  Subtitles come from `video.subtitleInfos[].Url` — [#L338-L381](https://github.com/yt-dlp/yt-dlp/blob/8973412/yt_dlp/extractor/tiktok.py#L338). The canonical URL is `https://www.tiktok.com/@{user}/video/{id}` — [#L106-L107](https://github.com/yt-dlp/yt-dlp/blob/8973412/yt_dlp/extractor/tiktok.py#L106).
- LikeVault manifest: MV3, permissions `storage, tabs, scripting, alarms`, host `https://www.tiktok.com/*`; `network_bridge.js` runs at `document_start` in `"world": "MAIN"`, and `content_script.js` runs at `document_idle` — [extension/manifest.base.json](https://github.com/netCrunch/LikeVault/blob/2c99d67/extension/manifest.base.json).
- Interception: `window.fetch` and `XMLHttpRequest.open/send` are wrapped. URLs matching `/api/favorite/item_list/` or `/api/(user/)?collect(ion)?/item_list/` have `response.clone().json()` read; lists are taken from `itemList || item_list || items || aweme_list`, batched (max 80), de-duplicated by `source:cursor:firstId:length` (LRU of 120), and posted with `window.postMessage({type:"LIKEVAULT_FAVORITE_ITEM_LIST", items}, origin)` — [network_bridge.js#L1-L30, L155-L234](https://github.com/netCrunch/LikeVault/blob/2c99d67/extension/network_bridge.js#L155). When API data is missing, the content script falls back to SEO meta (`og:description`, `twitter:description`) for caption and creator — [content_script.js#L774-L805](https://github.com/netCrunch/LikeVault/blob/2c99d67/extension/content_script.js#L774). It is described as "Local-first TikTok likes crawler and searchable archive", stores records in IndexedDB, and holds metadata only — [README / search](https://github.com/netCrunch/LikeVault).
- TikTok's own "Download your data" export includes "Video Browsing History" with only a link and a date per item, and no watch duration — [portmap.dtinit.org](https://portmap.dtinit.org/articles/watch-history3.md/) (search snippet; not fetched).
- Counter-example (one line): "T-FYP Scraper" exports public FYP/search data. It is a scraper, not own-history capture — [addons.mozilla.org](https://addons.mozilla.org/firefox/addon/scraper-for-tiktok/).

### Inferences
- The For You feed's network endpoint (likely `/api/recommend/item_list/`) is **not** in LikeVault's matcher. Relic would add it. This is unverified because I did not observe live traffic.
- Item JSON from interception gives exact IDs, captions, music and stats for free. "Which item was on screen, and for how long" then needs a DOM signal: an IntersectionObserver on the active `<video>` element, or URL changes (`/video/{id}` on desktop).
- The data export is a good **backfill** source (links and dates) to join with live-captured dwell data.

### Gaps
- I could not confirm current TikTok For You endpoint names or Instagram Reels / YouTube Shorts equivalents from code. No open-source extension found does Reels or Shorts own-history capture.

## Q5. Recommended Relic design (synthesis)

### Takeaway
- **Desktop**: an MV3 extension that intercepts network JSON and tracks DOM dwell time.
- **Android**: a passive AccessibilityService that reads a11y events and text, plus user-initiated MediaProjection clips. It does not drive the UI.
- **Agentic operation of the user's own apps**: deterministic, user-authored macros with state matching (droidrun pattern). LLM planning stays off-device or in a separate ADB/desktop companion, not inside the Play-distributed accessibility service.
- **Per-video understanding**: subtitle or Whisper transcript, scene-cut keyframes, then one structured VLM call per item, indexed as text plus embeddings.

### Cited Findings
- **Play policy**: Google Play's AccessibilityService policy prohibits API use "that enables an app to autonomously initiate, plan, and execute actions or decisions". It "does not prohibit deterministic, rule-based automation" that follows a static, human-defined "if trigger X, perform action Y" script. `isAccessibilityTool="true"` apps are exempt only when they serve people with disabilities. Other apps need prominent disclosure and affirmative consent. Effective date reported as 2026-01-28 — [Play Console Help 10964491](https://support.google.com/googleplay/android-developer/answer/10964491?hl=en), [Play Console Help 16585319](https://support.google.com/googleplay/android-developer/answer/16585319). This comes from a search-result summary; the pages themselves were unreachable (see Blocked sources).
- Deterministic replay with state verification and LLM handoff: droidrun `compare_states` (threshold 0.85) — [macro/matcher.py#L18](https://github.com/droidrun/droidrun/blob/3018561/mobilerun/macro/matcher.py#L18).
- Verified-by-observation and scroll-end rules: Mobile-Agent Reflector — [mobile_agent_e.py#L298](https://github.com/X-PLUG/MobileAgent/blob/11cea57/Mobile-Agent-v3/mobile_v3/utils/mobile_agent_e.py#L298); minitap cortex — [cortex.md](https://github.com/minitap-ai/mobile-use/blob/7b89fde/minitap/mobile_use/agents/cortex/cortex.md).
- Interception pattern: LikeVault — [network_bridge.js](https://github.com/netCrunch/LikeVault/blob/2c99d67/extension/network_bridge.js). Field map: yt-dlp — [tiktok.py#L659](https://github.com/yt-dlp/yt-dlp/blob/8973412/yt_dlp/extractor/tiktok.py#L659).

### Inferences: the concrete design

**(a) Passive capture of the user's own feed viewing**

*Desktop (Chrome/Firefox MV3)*

1. A MAIN-world `document_start` bridge wraps `fetch`/XHR for allow-listed hosts (tiktok.com, youtube.com/shorts, instagram.com/reels). It parses list payloads (`itemList|item_list|aweme_list`) into an `item_cache[id]`, de-duplicated by `cursor:firstId:len` (LikeVault pattern). Write it from scratch: LikeVault is GPL-3.0.
2. An isolated content script runs an IntersectionObserver plus `play`/`pause`/`timeupdate` listeners on the visible `<video>`, and watches URL changes. It emits `view_event {item_id, platform, started_at, ended_at, watched_ms, loops, completed, interactions[like|share|save|comment_open]}`. It joins to `item_cache` for metadata, with SEO meta fallback.
3. Storage is IndexedDB in the extension, synced to the local Relic app via native messaging. No cloud by default. Add per-site toggles and a visible "recording" badge.

*Android (Play-distributed)*

1. A passive AccessibilityService with `packageNames` limited to the feed apps the user selected, `typeWindowContentChanged|typeViewScrolled|typeWindowStateChanged`, and `canRetrieveWindowContent=true`. On each event, build a debounced (~300 ms) fingerprint from visible text nodes (creator handle, caption, counts in `contentDescription`). A change in fingerprint marks a new item, and the time between fingerprints is the dwell time.
2. The service never calls `performAction` or `dispatchGesture` in this mode, so it stays clearly on the "not autonomous" side. Show prominent disclosure and a consent screen.
3. Optional pixel capture: MediaProjection, started by the user each session (the OS consent dialog), records 1–3 fps keyframes or short clips for items the user flags, or for all items under an explicit "deep mode". The mobile-use pattern of segmenting `screenrecord` at 180 s and joining with ffmpeg applies to the ADB/desktop companion path, not to a Play app.

*Backfill*: import the platform's data export (TikTok "Video Browsing History": links and dates) and join it on item ID.

**(b) Consent-based agent that operates the user's own apps**

- **Tier 1, in the Play app**: deterministic macros only. The user records a flow (droidrun `macro/recorder.py` pattern); Relic stores it as JSON steps with an a11y-state fingerprint for each step. Replay checks `compare_states ≥ 0.85` before each action and **stops and asks the user** on a mismatch. An LLM may help *author* a macro off-line, but the runtime is a static human-approved script. This matches the "if trigger X, perform action Y" carve-out. Re-check against current policy text.
- **Tier 2, outside the Play-distributed service** (desktop companion over ADB/USB debugging, or the user's own sideloaded build): a full LLM agent loop, Manager → Executor → Reflector → Notetaker.
  - Perception: a11y tree via `uiautomator dump`, or a Portal-like service, plus a screenshot, fused as in minitap cortex.
  - Action space: android_world's JSON set.
  - Copy the minitap rules: one unpredictable action per turn, complete goals only on observed evidence, and an app-lock contextor.
  - Copy Mobile-Agent's Reflector A/B/C outcome rule and the "content identical after swipe ⇒ end of feed" rule.
  - Keep a seen-set of item IDs to stop scrolling loops.
  - Need human confirmation for any write action (like, follow, comment, purchase). Never generate engagement.
- **iOS**: no agentic control (XCTest/WDA require developer tooling). Capture is limited to platform data exports and share-sheet ingestion.

**(c) Per-video understanding and structured extraction**

Pipeline per item:
1. Media: a local clip, or the URL resolved via the user's session (yt-dlp-style fields from interception, so no re-download is needed for metadata).
2. Transcript: platform subtitles (`video.subtitleInfos`) if available, otherwise faster-whisper (distil-large-v3, as in VideoRAG).
3. Keyframes: ffmpeg `select='gt(scene,0.30)'` plus a 1 fps floor, max about 24 for clips ≤60 s, then 8% pixel-diff dedup over the last 4 frames (claude-real-video). PySceneDetect `ContentDetector(threshold=27)` is an alternative.
4. One VLM call with the transcript in the prompt (VideoRAG trick), producing the schema below.
5. Index: text embedding of `summary + topics + transcript`, an optional image embedding of 1–3 keyframes, and an entity list into a local graph (VideoRAG/LightRAG style).

Prompt, synthesized from VideoRAG caption.py, the mobile-use video_analyzer and the browser-use extraction prompt:
```
System: You analyze one short-form video the user watched on their own device. Be precise and factual — only describe what you can see or hear; if unsure, say so (use null). Do not guess or fabricate values. Your response MUST conform to the JSON Schema exactly.
User: Platform metadata (trusted): {creator_handle, caption, music, hashtags, duration_s}
The transcript of the current video:
{transcript}
Keyframes (timestamps in seconds): [t=0.0] <img> [t=2.4] <img> ...
Now provide a structured description of the video using timestamps where relevant.
```
Schema (Pydantic; zod is equivalent):
```python
class Segment(BaseModel):
    start_s: float; end_s: float; description: str
class VideoUnderstanding(BaseModel):
    summary: str                       # 1-2 sentences
    format: Literal["talking_head","tutorial","skit","music_dance","vlog","news","product","slideshow","other"]
    topics: list[str]                  # 1-5 short noun phrases
    entities: list[dict]               # {name, type: person|org|product|place|event}
    on_screen_text: list[str]          # verbatim
    spoken_language: str | None
    key_claims: list[str]              # factual claims made, verbatim-ish
    segments: list[Segment]            # chronological
    call_to_action: str | None
    sponsored_or_ad: bool | None
    confidence: float                  # 0-1
```
Store it alongside the captured metadata. Its fields mirror yt-dlp: id, uploader, channel, description, track, artists, duration, timestamp, view/like/comment/repost/save counts. Add view_event fields (watched_ms, loops, completed). For queries, use a VideoAgent-style tool loop (`caption_retrieval`, `segment_localization`, `visual_question_answering`) over the per-item records.

### Gaps
- The exact current Play policy wording was not fetched directly. Verify the carve-out text and the effective date before relying on it.
- I have not measured a11y text coverage for TikTok, Instagram and YouTube on Android (how often creator and caption are exposed). This needs on-device testing.
- Network endpoint names for the For You page, Reels and Shorts were not verified from code.

### Blocked sources
- https://support.google.com/googleplay/android-developer/answer/10964491?hl=en — DNS failure (ENOTFOUND) via WebFetch
- https://support.google.com/googleplay/android-developer/answer/16585319 — DNS failure (ENOTFOUND)
- https://www.xda-developers.com/google-trying-limit-apps-accessibility-service/ — DNS failure (ENOTFOUND)
- VideoAgent project page (videoagent.github.io), vidwit, and HUANGCHIHHUNGLeo/claude-real-video — not attempted, because of the call budget. claude-real-video details come from PyPI.
