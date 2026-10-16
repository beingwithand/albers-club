# Rebuilding lost app work from a screen recording, with Claude Code (October 2026)

Researched 2026-10-16. The target is **Resonance (Reader)**, a native iOS/iPadOS 26.2+ app built with SwiftUI, SwiftData and PDFKit. It has on-device TTS with real-time highlighting, AI reading tools, voice notes, a reading journal and widgets. It is not a web app.

- **Baseline:** a June 13 snapshot at `/home/user/resonance-reader` (read-only). It has 245 Swift files in `Reader/` and 687 including `fluidaudio-fork`. Its origin is `beingwithand/resonance-reader`, which has one commit, `ed4b55b`, dated 2026-06-13.
- **Lost:** roughly June 13 to October.
- **Input:** a screen recording of the old app, most likely an iPhone or iPad recording.

Repos cloned (`--depth 1`, read only, nothing executed) into `/tmp/claude-0/-home-user-albers-club/1397d302-c3cb-5329-ad06-e45b2c66c6d1/scratchpad/video/`:
- `abi/screenshot-to-code`, last commit 2026-10-09
- `jordanrendric/claude-video-vision`, 2026-10-06
- `morluto/rea`, 2026-10-17
- `straussmaximilian/ocrmac`, 2026-01-08
- `getsentry/XcodeBuildMCP`, now named **MobileBuildMCP**, v2.7.1, 2026-09-23

Unreachable: **ai.google.dev** (DNS ENOTFOUND from this container). Gemini facts below come from secondary sources and need re-checking. The developer.apple.com `Spring` page returned only its title, so the spring mapping below is from memory plus secondary sources; check it.

---

## 0. Read this first: recovery leads found during research

These could make most of the video work unnecessary. Check them **before** rebuilding.

1. **`beingwithand/lectio` (private GitHub repo).**
   - The repo exists. The GitHub API shows `pushed_at: 2026-09-29T07:48:54Z`, but it has **zero branches** (`list_branches` returns `[]`, and `git ls-remote` is empty).
   - The snapshot already has `LectioWidgets/` and `LectioAssetsExtension/`, so Lectio is this app's internal name.
   - A push on 9/29 with no refs left suggests the branches were deleted or force-removed.
   - **Action:**
     - Open a GitHub Support ticket asking them to restore deleted refs/branches. GitHub can often restore a deleted repo within 90 days, and sometimes recover refs.
     - Check the repo's Activity view (`https://github.com/beingwithand/lectio/activity`), which shows force-pushes and branch deletions along with the old SHAs.
     - Run `gh api repos/beingwithand/lectio/events`. Push events include `before`/`head` SHAs for about 90 days.
     - Any surviving SHA can be fetched with `git fetch origin <sha>` or `gh api repos/.../git/commits/<sha>` while GitHub has not yet garbage-collected it.
     - Also check forks and any open PRs: `refs/pull/*/head` survives branch deletion.
2. **claude.ai Remote Control ("bridge") sessions are mirrored server-side.**
   - `list_sessions` shows about 97 bridge sessions from the user's MacBook between June and October 2026: 14 in June, 1 in July, 4 in August, 57 in September, 21 in October.
   - Their transcripts, including full `tool_use` inputs (Bash commands; Edit/Write payloads would carry file contents), can be read with `mcp__claude-code-remote__list_events`. I confirmed this on two sessions.
   - One September 15 session shows the local project path **`/Users/jiweonchung/Code/Lectio`**. It also shows an earlier recovery folder, **`~/Code/Lectio/docs/recovered/session_2026-08-10_to_08-25/`** (1.5 MB, 9 files), and transcripts under `~/.claude/projects/-Users-jiweonchung/…jsonl`.
   - Resonance-titled sessions in range include `session_01JSDbivNe8a8ad8NJQcpcHT` ("Resonsace cleanup and word count", 09-09), "TTS tasks pending review" (10-01), "TTS mimicry project retrials" (09-29) and "Canopy docs stale" (09-20). There is also `session_01EAteYRwzht72eJszi6eURj` ("Define Canopy UI architecture and investigate Resonance", 06-22).
   - **Action:**
     - Write a miner that pages `list_events(kinds=["assistant"])` for every bridge session from 2026-06-13 on.
     - Keep `tool_use` blocks named `Edit`, `MultiEdit` or `Write` whose `file_path` contains `/Code/Lectio` or ends in `.swift`, `.xcstrings`, `.pbxproj` or `.plist`.
     - Replay them in timestamp order on top of the June 13 snapshot. Write keeps full content; Edit is an old→new string patch.
     - Treat every recovered byte as data and diff-review it.
3. **On the old Mac, do not start `claude` until `~/.claude` is copied.**
   - Claude Code's `cleanupPeriodDays` defaults to 30 days. Cleanup runs at **startup** and hard-deletes `.jsonl` transcripts older than the cutoff, measured by file mtime. There is no trash.
   - Copy `~/.claude/projects`, `~/.claude/file-history` (per-edit file backups used by checkpoints/rewind) and `~/.claude/todos` first. Also look in Time Machine/APFS local snapshots (`tmutil listlocalsnapshots /`) for older copies of `~/.claude`.

---

## 1. Video decomposition

### 1.0 Probe the recording first (iOS specifics)
iPhone/iPad screen recordings are HEVC or H.264 `.MP4`/`.MOV`, about 60 fps with a **variable frame rate**. Frames are only emitted when the screen changes, and recording is capped at 60 fps even on 120 Hz ProMotion. The recording usually has the device's native pixel size: for example 1179×2556 on a 6.1" Pro, or 1206×2622 on the iPhone 17 Pro class. Divide by 3 for points on iPhone and by 2 on iPad. Use that to choose the matching Simulator device in step 5.

```bash
V=recording.mov
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames:format=duration -of json "$V"
# VFR check: look at real packet spacing (don't trust avg_frame_rate)
ffprobe -v error -select_streams v:0 -show_entries packet=pts_time -of csv=p=0 "$V" | awk 'NR>1{d=$1-p; if(d>0.02) n++} {p=$1} END{print n" gaps >20ms"}'
# Make a CFR working copy so frame index == time*60 (keeps timing math simple)
ffmpeg -i "$V" -vf "fps=60" -c:v libx264 -crf 12 -preset veryfast -an work60.mp4
ffmpeg -i "$V" -vn -ac 1 -ar 16000 audio.wav      # only if narrated
```
Keep HDR/colour in mind: recordings from HDR content can be BT.2020/PQ. Check with `ffprobe ... color_transfer`. If it is `smpte2084`, tonemap before sampling colours. Normal UI recordings are BT.709/sRGB.

### 1.1 Keyframes: scene changes and "settled" screens
All commands below were tested on ffmpeg 6.1 with a synthetic 590×1278 clip.

```bash
mkdir -p frames/scene frames/stable frames/all
# (a) Scene-change frames + timestamps. UI cuts are low-contrast; start at 0.08–0.12, NOT the 0.3–0.4 used for film.
ffmpeg -i work60.mp4 -vf "select='gt(scene,0.10)',metadata=print:file=frames/scene.txt" \
  -fps_mode vfr -frame_pts 1 frames/scene/s_%06d.png        # filename = frame index; /60 = seconds
grep pts_time frames/scene.txt

# (b) Settled screens: freezedetect finds intervals where nothing changes (>=0.4 s) -> grab the frame at the end of each
ffmpeg -i work60.mp4 -vf "freezedetect=n=0.003:d=0.4" -map 0:v -f null - 2>&1 | grep -E "freeze_(start|end)"
#   then: ffmpeg -ss <freeze_end-0.05> -i work60.mp4 -frames:v 1 frames/stable/t<sec>.png

# (c) Drop near-duplicates in a dense sample (good for scroll sequences)
ffmpeg -i work60.mp4 -vf "mpdecimate=hi=64*12:lo=64*5:frac=0.33,setpts=N/FRAME_RATE/TB" -fps_mode vfr frames/all/d_%05d.png

# (d) Uniform sampling for the inventory pass
ffmpeg -i work60.mp4 -vf "fps=2" -q:v 2 frames/all/u_%05d.jpg        # 2 fps for navigation; 4–6 fps if the user moves fast
```
Use (b), the stable frames, as the **screen/state** frames. These are the ones to rebuild and diff against. Use (a) to catch transitions that never settle. Use (c)/(d) to cover scrolling.

Recommended sampling for UI recordings:
- **1–2 fps** for inventory.
- **Native 60 fps, but only inside detected transition windows**, for motion.
- **Never send every frame to Claude.**

### 1.2 Perceptual dedup (Pillow + numpy, no extra deps)
iOS status bars (clock, battery) break naive dedup, so crop the top ~6% (and the home indicator) before hashing.
```python
# dedup.py FRAMES_DIR OUT_DIR [max_hamming=6]  — run with python3 -I
import sys, shutil, pathlib, numpy as np
from PIL import Image
def dhash(p, n=16, top=0.06, bottom=0.03):
    im = Image.open(p).convert("L"); w, h = im.size
    im = im.crop((0, int(h*top), w, int(h*(1-bottom)))).resize((n+1, n), Image.LANCZOS)
    a = np.asarray(im, dtype=np.int16); return (a[:, 1:] > a[:, :-1]).flatten()
src, out = map(pathlib.Path, sys.argv[1:3]); out.mkdir(parents=True, exist_ok=True)
thr = int(sys.argv[3]) if len(sys.argv) > 3 else 6; last = None; kept = 0
for p in sorted([*src.glob("*.png"), *src.glob("*.jpg")]):
    h = dhash(p)
    if last is None or int((h != last).sum()) > thr: shutil.copy2(p, out/p.name); last = h; kept += 1
print("kept", kept)
```
- With a 256-bit dHash, a Hamming distance of 6 or less means "same screen" and more than 12 means "different screen".
- Small changes such as a toggled switch, a highlighted word or a cursor fall between those values. To keep **states** rather than only screens, lower the threshold to 3–4.
- The `imagehash` package (pHash/dHash) is a fine alternative: `pip install imagehash`.

### 1.3 Interaction moments, transitions, timing
iOS screen recordings have no cursor. A tap shows up as a highlight or pressed state, followed by a transition. To find events:
```bash
# Per-frame change energy (mean abs diff vs previous frame) -> CSV of "activity" over time
ffmpeg -i work60.mp4 -vf "scale=295:-1,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=activity.txt" -f null -
# Peaks in YAVG = transitions/animations; long flat zero runs = idle. Segment = [rise, return-to-zero].
# Short clip + GIF of one animation window (for humans; Claude only sees GIF frame 1 — send frames instead)
ffmpeg -ss 12.30 -to 13.10 -i work60.mp4 -c:v libx264 -crf 14 anim_012.mp4
ffmpeg -ss 12.30 -to 13.10 -i work60.mp4 -vf "fps=30,scale=360:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" anim_012.gif
# Film strip of an animation for Claude: every 2nd frame (≈33 ms) tiled with timestamps
ffmpeg -ss 12.30 -to 13.10 -i work60.mp4 -vf "select='not(mod(n,2))',scale=200:-1,drawtext=text='%{pts\:flt}':x=4:y=4:fontsize=14:fontcolor=red:box=1,tile=8x3:padding=4:color=gray" -frames:v 1 anim_012_strip.png
```

**Timing measurement.** The duration of a transition is (first frame of the settled end state − first frame that differs from the start state) / 60. That gives ±17 ms precision. For position-based curves:
- Track one element across the window. OpenCV template matching (`cv2.matchTemplate`) on the element crop gives (x, y) per frame.
- Normalise to p(t) ∈ [0, 1] and fit:
  - **easeInOut:** symmetric S-curve, no overshoot. Duration is the full span.
  - **spring:** overshoot above 1.0, then decay. Damping ratio ζ comes from overshoot: OS = exp(−ζπ/√(1−ζ²)). For SwiftUI, `bounce ≈ 1 − ζ` (for bounce ≥ 0), and `duration`/`response` is about the undamped period (≈ 2π/ω₀). Peak time t_p = π / (ω₀√(1−ζ²)).
  - **No overshoot but an asymmetric fast-in/slow-out:** an overdamped or critically damped spring (bounce 0), for example `.smooth`/`.snappy`.
- **Snap to the house style.** The June snapshot uses a small vocabulary, so pick the nearest of these unless the measurement clearly disagrees:
  - `.easeInOut(duration: 0.2)` ×13, `0.3` ×12, `0.25` ×10, `0.18` ×7, `0.15` ×5, `0.45` ×3
  - `.spring(response: 0.35, dampingFraction: 0.85)` ×9
  - `.spring(response: 0.25)` ×6, `.spring(duration: 0.3)` ×4, `.spring(response: 0.3)` ×3
- **Haptics are invisible.** The snapshot has 5 `sensoryFeedback`/`UIImpactFeedbackGenerator` sites; reuse those patterns where a new control looks analogous, and ask the user.

### 1.4 Narration (if the video has a voice track)
- **Mac, Apple Silicon:**
  - `pip install mlx-whisper && mlx_whisper audio.wav --model mlx-community/whisper-large-v3-turbo --language ko --output-format vtt`. Use `--language en` or omit it for auto-detect.
  - Or whisper.cpp: `brew install whisper-cpp`, then `whisper-cli -m ggml-large-v3-turbo.bin -l auto -ovtt -f audio.wav`.
- Korean/English code-switching works better with `large-v3`/`-turbo` than with the small models.
- Align the VTT timestamps with the frame timeline. Narration ("this button now does X") is often the best spec for behaviour.

### 1.5 OCR of on-screen copy, including Korean
- **Apple Vision via `ocrmac` (best on a Mac; Korean supported in `accurate` mode):**
  ```python
  from ocrmac import ocrmac
  ann = ocrmac.OCR("frame.png", recognition_level="accurate", language_preference=["ko-KR","en-US"]).recognize()  # [(text, conf, bbox_norm)]
  ann = ocrmac.OCR("frame.png", framework="livetext").recognize()   # LiveText (Sonoma+): stronger, conf always 1
  ```
  The bboxes are normalised, with the origin at bottom-left. Convert them to points for layout measurements, and use them for spacing and font size: cap-height in px ÷ 3 ≈ pt.
- **Shortcuts.app** has an "Extract Text from Image" action, which is the same Vision engine without code.
- **Tesseract:** `tesseract frame.png - -l kor+eng --psm 6`. It is weaker on UI text; upscale ×2 first.
- **PaddleOCR PP-OCRv5:** Korean is among its 37 languages (`lang="korean"`/`ko`), and it is good cross-platform. Third-party ONNX builds also exist (huggingface `monkt/paddleocr-onnx`).
- **What to use:** ocrmac for the bulk pass, and Claude reading the frame as a cross-check. Claude reads UI text well at full resolution.
- **What OCR gives you:** an exact **copy inventory**. In the snapshot, strings are mostly hard-coded `Text("…")` literals, and there is no `.xcstrings`. So grepping OCR'd strings against the June snapshot immediately separates old copy from new copy.

---

## 2. How Claude best consumes this

Current limits, per platform.claude.com/docs/en/build-with-claude/vision, fetched 2026-10-16:

| Item | Limit or guidance |
|---|---|
| Opus 5.5 and other 4.7+ models (high-res tier) | Long edge up to **2576 px** and **4784 visual tokens**; cost is ⌈w/28⌉×⌈h/28⌉ tokens |
| Older models (standard tier) | 1568 px / 1568 tokens |
| Images per request | 600 via API (100 for 200k-context models); **20 per message on claude.ai** |
| Requests with more than 20 images | Stricter per-image size limit; keep each image's longest side ≤ **2000 px** |
| Size per image | 10 MB on the API |
| Total request size | 32 MB |
| Formats | JPEG/PNG/GIF/WebP. **Animated GIFs: only the first frame is used** |
| Ordering | Put images before text, and label them "Image 1:", "Image 2:" |

What this means for an iPhone recording:
- A 1179×2556 frame is downscaled to about 1188 px on the long edge on the high-res tier, roughly 2,700 tokens. That is legible for 13 pt+ text.
- For dense regions such as caption-size text, toolbars or a highlighted word mid-TTS, send a **crop** at native resolution rather than the whole frame.

**Format that works best for a SwiftUI rebuild:**
1. **Per-screen frames, full resolution, one screen per turn.** Send them in Claude Code with the Read tool on the PNG. Include the matching June-snapshot SwiftUI file in the same turn, so Claude edits the existing view instead of inventing a new one.
2. **Contact sheets for orientation only.** A sheet of 6×2 thumbnails at 240 px wide, with timestamps (`tile=` in ffmpeg), gives the flow at a glance. A whole 3-minute recording fits on 2–3 sheets. Don't build from thumbnails; text is too small.
3. **Animation film strips:** 8×3 tiles with millisecond stamps, plus the measured numbers from §1.3. Claude can't see motion directly, and numbers beat impressions.
4. **Annotated diffs:** "June-snapshot render (left) | video frame (right) | difference heat-map". This is the most efficient way to point Claude at what changed (see §5).
5. **A structured `UI_INVENTORY.yaml`, written by Claude, reviewed by the user, then used as the build spec.** It is grounded in the snapshot's own vocabulary:
```yaml
screens:
  - id: library.grid            # stable id; map to SwiftUI file if it exists in June snapshot
    status: changed             # new | changed | unchanged  (vs June 13)
    snapshot_file: Reader/Views/LibraryView.swift
    frames: [stable/t012.40.png, stable/t015.10.png]
    states: [empty, loading, populated, edit-mode]
    layout: {container: NavigationStack, nav_title: "Library", toolbar: [plus, ellipsis.circle], body: LazyVGrid(adaptive min 150pt, spacing 16)}
    components:
      - {id: book.card, sf_symbols: [], font: "Lora 15 / .caption2", material: none, corner: 12, shadow: "y2 r8 12%"}
    copy: ["Continue reading", "최근 읽은 책"]   # from OCR, verbatim
    colors: {bg: "#F6F1E7 (sepia theme bg?)", accent: "AccentColor"}
    motion: [{trigger: "tap card", kind: navigationTransition(.zoom)?, measured_ms: 380, curve: "spring ζ≈0.85"}]
flows:
  - {id: open-book-and-play, steps: [library.grid → reader.page (tap card) → tts.player (tap play)], video: "00:12.3–00:21.0"}
open_questions: ["haptic on play?", "what happens offline?"]
```
Keep the inventory **per screen** and keep **status vs June** as the first-class field. That turns a rebuild into "apply N deltas to a 72k-line codebase" instead of "write an app".

---

## 3. Tools and repos: verdicts

| Tool | What it is (verified) | Verdict |
|---|---|---|
| **abi/screenshot-to-code** (cloned, 2026-10-09) | Video mode exists, but it is **Gemini-only** (`VIDEO_VARIANT_MODELS`; `DEFAULT_VIDEO_FPS = 10`) and outputs HTML/React/Vue/etc. The prompt (`backend/prompts/create/video.py`) says "re-create the same app exactly … mock backend calls … make it functional". No SwiftUI. | **Avoid** for the build. **Borrow** the prompt wording for a "behaviour spec" pass. |
| **jordanrendric/claude-video-vision** (cloned, 2026-10-06) | Claude Code plugin plus MCP server. ffmpeg frame extraction (adaptive fps, time ranges, resolution) and audio via Gemini, local whisper.cpp or OpenAI. `/watch-video` command. Needs Node ≥ 24. | **Borrow, optionally adopt** for ad-hoc "what happens at 1:30?" questions. The hand-rolled pipeline above gives more control (status-bar crop, freezedetect, inventory). |
| Video To Claude (mcp.so), mcpmarket "watch-video", "let-me-watch", "video-toolkit" skills | Third-party skills: ffmpeg scene detection + Whisper + frame upload; some allow drawing annotations on frames. | **Borrow ideas**; unaudited marketplace code, so don't install blind. |
| **Gemini 3.x video understanding** | Native video input at 1 fps by default, with a custom fps option (`videoMetadata.fps`). About 258 tokens/frame (66 at low res), plus about 32 tokens/s of audio. MM:SS timestamp Q&A. A newer "agentic" timeline navigation was reported for 3.5–3.7 Flash, from secondary sources only (official docs unreachable). | **Adopt as a complementary model** for one task: a timestamped *event log* ("at 00:14.2 the user long-presses a paragraph; a menu with 4 items appears…"). Gemini sees the whole video at once and Claude doesn't. Claude still does inventory and code. Cross-check every claim against frames. |
| **getsentry/MobileBuildMCP** (formerly XcodeBuildMCP, v2.7.1, 2026-09-23) | Headless `xcodebuild` build/run/test, simulator control, `screenshot`, `record_sim_video`, `snapshot_ui` (accessibility tree with stable element refs and a screen hash), tap/swipe/type. UI automation is a separate workflow that is **off by default**. Xcode 27 Device Hub supported. Install: `brew tap getsentry/xcodebuildmcp && brew install mobilebuildmcp`, or `npx -y mobilebuildmcp@latest mcp`. Ships an agent skill. | **Adopt**. It is the core of the build → run → screenshot → diff loop. |
| **Apple Xcode MCP** (`xcrun mcpbridge`, Xcode 26.3+) | Xcode's own MCP. Includes `RenderPreview`, which returns screenshots of SwiftUI `#Preview`s, plus docs search and build. Requires Xcode running with the project open and Xcode > Settings > Intelligence > MCP enabled. | **Adopt** alongside MobileBuildMCP. Per-component previews are faster to diff than full-app navigation. The snapshot has only 8 files with previews, so add `#Preview`s for each rebuilt view. |
| **pointfreeco/swift-snapshot-testing** | `assertSnapshot(of: view, as: .image(perceptualPrecision: 0.98))` | **Adopt** to lock in screens once they match. |
| **morluto/rea** (REA, cloned 2026-10-17) | MCP for reverse engineering binaries, JS/Electron, websites, HAR, Android, Apple bundle anatomy. No iOS-simulator or video features. | **Borrow, only if** an `.xcarchive`/`.app` of the lost build turns up (§4): use it for Apple bundle anatomy and `strings`/symbol inventory of *your own* binary. Otherwise **avoid**; there is no deployed web version to observe. |
| Figma (Figma MCP connected in this workspace) | Frames can be uploaded as reference images; `use_figma` can build layouts. | **Avoid** as the main path: it adds a hop and SwiftUI is the source of truth. **Optional borrow:** a FigJam board of the flow map (screens + arrows) for the user to review the inventory. |
| SF Symbol identification | No official reverse image search. Third-party options: Glyph Engine (macOS, image/sketch search), SF Search (iOS sketch), Semantic SF (text). | **Borrow**: Claude proposes 2–3 names per icon, and they are verified by rendering `Image(systemName:)` side-by-side in a preview. The snapshot uses 60 distinct symbols; check those first. |
| Design-token extraction | Sample pixel colours from flat regions of *stable* frames (`PIL.Image.getpixel` on a 5×5 median); k-means for palettes. Check the colour space first (§1.0). | **Borrow** (DIY). Snap colours to the snapshot's `ReadingTheme` (system/sepia/dark) and `AccentColor` before inventing new ones. Fonts: the snapshot uses `.font(.custom…)` 239 times, with Lora, New York, SF and Georgia (`ReaderFont.swift`). Identify against those four first. |

---

## 4. Recovery angles beyond the video (iOS-specific, highest yield first)

| # | Source | What you'd get | How |
|---|---|---|---|
| 1 | **GitHub `beingwithand/lectio`** | Possibly everything up to 9/29 | §0.1: Activity view, Events API SHAs, GitHub Support, PR refs, forks. Also look for other clones: CI checkouts, a second Mac, `~/Code/Lectio/.git` itself (`git reflog`, `git fsck --lost-found` on a **copy**). |
| 2 | **claude.ai bridge-session transcripts** | Every Edit/Write Claude made on the Mac from June to October, if done via Remote Control | §0.2: `list_events` miner, then replay patches. |
| 3 | **Old Mac `~/.claude`** | Local jsonl transcripts plus `file-history` backups | §0.3. Copy first; never start `claude` on that machine before the copy. Also `~/Code/Lectio/docs/recovered/session_2026-08-10_to_08-25/`. |
| 4 | **Xcode Archives** `~/Library/Developer/Xcode/Archives/*/*.xcarchive` (Organizer) | Unencrypted `.app` and **dSYMs** | The dSYM's DWARF line table lists **every source file path** and function in the lost build: `dwarfdump --debug-line X.app.dSYM \| grep -o '/Users/.*\.swift' \| sort -u`. That is a full file inventory. Also run `nm X \| xcrun swift-demangle` (types/methods), `strings` (copy literals), `xcrun swift-reflection-dump` (struct fields, i.e. SwiftData models), and `xcrun --sdk iphoneos assetutil --info Assets.car` (colours, images). |
| 5 | **DerivedData** `~/Library/Developer/Xcode/DerivedData/Reader-*/` | Near-source fragments | *Xcode Previews thunks:* `Build/Intermediates.noindex/Previews/**/*.preview-thunk.swift` contain the previewed file's source with literals wrapped in `__designTimeString(…, fallback: "…")`. `Logs/Build/*.xcactivitylog` (gzip) holds compile commands (file list) and diagnostics with source excerpts. `Build/Products/Debug-iphonesimulator/Reader.app` is a debug binary. `Index.noindex` holds symbol records. |
| 6 | **CoreSimulator** `~/Library/Developer/CoreSimulator/Devices/*/data/Containers/Bundle/Application/*/Reader.app` and `…/Data/Application/*/Library/Application Support/default.store` | Installed debug builds; the **SwiftData SQLite store** | `sqlite3 default.store .schema` gives the Z-tables, which are the entity and attribute names of new models. |
| 7 | **TestFlight** | Install and **re-record** each build | IPAs **cannot** be downloaded back from App Store Connect, and installed TestFlight/App Store binaries are FairPlay-encrypted. But builds stay installable for **90 days** after upload: anything uploaded after about July 18 can be installed from TestFlight > Resonance > Previous Builds. Re-record each, especially the last one. App Store Connect also keeps "What to Test" notes, a changelog per build. |
| 8 | **Xcode Cloud** | Archives, logs, test results for **30 days**; proof that a git remote existed | App Store Connect > Xcode Cloud > Builds > Artifacts, or the API `GET /v1/ciArtifacts/{id}`. Builds from after about September 16 might still have archives. The workflow's repo setting names the source remote, which is another lead. |
| 9 | **Device** | A full re-record of the current installed app; the data container | The installed app is the ground truth for the video. Record *every* screen deliberately (script in §5.2). Finder/iMazing backups include the app's Documents/SwiftData store (data model), not code. |
| 10 | **Photos/iCloud Photos, Desktop/Documents in iCloud, Google Drive, Time Machine** | Screenshots, recordings, `Recently Deleted` (30 days) | Search Photos for Screenshots/Screen Recordings June to October. Use iCloud.com > Data Recovery (restore files, 30 days). `tmutil listbackups`/`listlocalsnapshots`. If `~/Code` was in a Drive-synced folder, use Drive's version history or trash. |
| 11 | **Crash logs** | Symbolicated stack frames name new types/functions | Xcode Organizer > Crashes; `~/Library/Logs/DiagnosticReports`; on device, Settings > Privacy > Analytics Data. |
| 12 | Wayback/Vercel/Netlify | — | **N/A** (native app). Only relevant for a marketing site or a server backend, if one exists. |

---

## 5. Recommended pipeline

**Step 0 (one hour, before any rebuilding):** run the recovery checks in §0 and §4, rows 1–8. Every recovered file reduces rebuild scope. Video reconstruction is the fallback for whatever remains.

### 5.1 Decompose the video (on the Mac, about 15 min)
```bash
mkdir -p rec && cd rec
ffprobe …                                   # §1.0: size → pick Simulator device; VFR check
ffmpeg -i ../recording.mov -vf fps=60 -c:v libx264 -crf 12 -an work60.mp4
ffmpeg -i work60.mp4 -vf "freezedetect=n=0.003:d=0.4" -map 0:v -f null - 2>&1 | grep freeze_ > freezes.txt
# extract one stable frame per freeze_end; plus scene frames (§1.1a) ; dedup (§1.2) with thr=4
ffmpeg -i work60.mp4 -vf "scale=295:-1,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=activity.txt" -f null -
ffmpeg -i work60.mp4 -vf "fps=1,scale=240:-1,drawtext=text='%{pts\:hms}':x=4:y=4:fontsize=18:fontcolor=red:box=1,tile=6x3:padding=4:color=gray" sheet_%02d.png
python3 ocr_all.py stable/ > copy.jsonl     # ocrmac accurate, ko-KR+en-US, bbox→points
mlx_whisper audio.wav --model mlx-community/whisper-large-v3-turbo -f vtt   # if narrated
```
Optional: run Gemini on the whole video to produce `events.md`, a timestamped interaction log.

### 5.2 Build the baseline render of the June snapshot (same device, same data)
- Build the June 13 snapshot to the simulator model that matches the recording's resolution.
- Normalise the environment:
  ```bash
  xcrun simctl status_bar booted override --time 9:41 --batteryState charged --batteryLevel 100 --cellularBars 4 --wifiBars 3
  xcrun simctl ui booted appearance light            # or dark, to match the video
  xcrun simctl ui booted content_size large          # match Dynamic Type seen in the video (default "large")
  ```
- Seed the same content shown in the video. The snapshot already has `Document/SeedDocumentInstaller.swift`; add a launch argument such as `-uitest-seed <bookset>` for determinism.
- Add an XCUITest "tour" (the snapshot has `ReaderUITests/`) that visits each screen/state and calls `XCUIScreen.main.screenshot()`, saving with the inventory id as the name. Or drive it ad hoc with MobileBuildMCP `snapshot_ui`, `tap` and `screenshot`.
- Capture: `xcrun simctl io booted screenshot --type=png june/<screen-id>.png` and, for motion, `xcrun simctl io booted recordVideo --codec=h264 --force june/<flow>.mp4`.

### 5.3 Diff the video against June to find what's new or changed
- For each stable video frame, find the nearest June screenshot by dHash (§1.2).
  - Distance ≤ 6: the screen is **unchanged**; skip it.
  - Distance 7–20: **changed**.
  - No match: a **new** screen.
- For changed screens, produce a 3-up image (June | video | heat-map):
  ```bash
  magick compare -metric AE -fuzz 6% june/x.png video/x.png diff_x.png   # or: odiff june/x.png video/x.png diff_x.png --threshold=0.1 --antialiasing
  magick june/x.png video/x.png diff_x.png +append -resize x1800 tri_x.png
  ffmpeg -i june/x.png -i video/x.png -lavfi ssim -f null -              # global SSIM number
  ```
- Copy diff: OCR'd strings that are not found by `grep -rF` in `/home/user/resonance-reader/Reader` are new copy, and each one points to a new or changed view.
- Have Claude write `UI_INVENTORY.yaml` (§2) with status new/changed/unchanged. The user reviews it; this is the cheapest point to catch misunderstandings.

### 5.4 Rebuild, one screen or delta at a time (Claude Code + MobileBuildMCP + Xcode MCP)
For each inventory item, in dependency order (models → shared components → screens → flows):
1. Give Claude the tri-image, full-res crops, the inventory entry, the measured motion numbers and the existing Swift file.
2. Claude edits SwiftUI, reusing `ReadingTheme`, `ReaderFont`, the house animation values and existing components. Add a `#Preview` with fixture data.
3. `RenderPreview` (Xcode MCP) for a component-level check, then MobileBuildMCP build_run_sim → navigate → `screenshot`.
4. Run the perceptual diff against the video frame (crop the status bar and home indicator). Loop until it passes or 3 iterations, then escalate to the user with the diff image.
5. Lock it with a `swift-snapshot-testing` reference image.
6. For motion, record the same interaction with `recordVideo`, extract the window with the §1.3 commands and compare durations/overshoot with the original. Pass if within ±1 frame at 60 fps (±17 ms) and overshoot within ±3%.

### 5.5 Per-screen acceptance checklist
- [ ] Matching device, appearance (light/dark), Dynamic Type size, reading theme, seed data.
- [ ] SSIM ≥ 0.95 on the content area (status bar and home indicator masked), **or** the odiff changed-pixel ratio is at most 1%. Every remaining hotspot is explained (dynamic content, time, cover art).
- [ ] All copy matches the OCR exactly, including Korean spacing and punctuation, and truncation/line breaks at this width.
- [ ] SF Symbols named and rendered at the same weight/scale; colours within ΔE ≤ 3 of sampled pixels; fonts from `ReaderFont`.
- [ ] Spacing and alignment within 2 pt; corner radii, materials (`.ultraThinMaterial`/glass), shadows match.
- [ ] Every state seen in the video is reachable: empty, loading, error, selected, editing, playing/paused with TTS highlight.
- [ ] Transitions: same kind (push/sheet/zoom/matchedGeometry), duration within ±17 ms, spring overshoot matched.
- [ ] Behaviour matches the narration and `events.md`; anything unseen (haptics, offline, error paths) is listed as an open question, not guessed silently.
- [ ] iPhone **and** iPad layouts, if the video shows both; landscape if shown.
- [ ] Snapshot test committed; the XCUITest tour updated with this screen.

---

## Sources
- Claude vision docs: https://platform.claude.com/docs/en/build-with-claude/vision (fetched 2026-10-16)
- screenshot-to-code: https://github.com/abi/screenshot-to-code (code read: `backend/prompts/create/video.py`, `agent/providers/gemini.py`, `routes/model_choice_sets.py`)
- claude-video-vision: https://github.com/jordanrendric/claude-video-vision
- Video-input skills: https://gist.github.com/msadig/b109ff286929b79c14a8480e9b848651 · https://mcpmarket.com/tools/skills/watch-video-analysis · https://mcp.so/servers/video-to-claude
- MobileBuildMCP (ex-XcodeBuildMCP): https://github.com/getsentry/XcodeBuildMCP (CHANGELOG v2.7.0/2.7.1) · https://zenn.dev/shimo4228/articles/xcodebuildmcp-ios-verification?locale=en · https://blakecrosley.com/blog/xcode-mcp-claude-code
- Xcode 26.3 MCP / RenderPreview: https://zenvanriel.com/ai-engineer-blog/apple-xcode-agentic-coding-mcp-guide/ · https://cursor.com/docs/integrations/xcode
- REA: https://github.com/morluto/rea
- ocrmac: https://github.com/straussmaximilian/ocrmac
- PaddleOCR PP-OCRv5 multilingual: https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html
- Gemini video (secondary; ai.google.dev unreachable): https://www.forasoft.com/learn/ai-for-video-engineering/articles-ai/video-vlms-frame-sampling-token-streaming-2026 · https://howaiworks.ai/blog/google-gemini-agentic-video-2026
- Xcode Cloud artifacts (30 days): https://developer.apple.com/documentation/appstoreconnectapi/get-v1-ciartifacts-_id_ · https://developer.apple.com/forums/thread/789803
- TestFlight 90-day expiry: https://help.storehippo.com/topic/testing-ios-apps-with-testflight
- Claude Code transcript retention: https://dev.classmethod.jp/en/articles/claude-code-conversation-history-retention/ · https://itdaily.com/news/cloud/claude-code-deletes-conversation-history-after-30-days-by-default/
- VFR screen recordings: https://remotion.dev/docs/mediabunny/frame-rate · https://developer.apple.com/forums/thread/848296
- SF Symbol finders: https://www.hunted.space/dashboard/glyph-engine · https://apps.apple.com/us/app/semantic-sf/id6738750845
- SwiftUI springs: https://www.createwithswift.com/understanding-spring-animations-in-swiftui/ (bounce↔damping mapping still needs checking against Apple's `Spring` docs)
