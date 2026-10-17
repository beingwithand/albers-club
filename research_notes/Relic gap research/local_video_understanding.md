# Local short-form video understanding for Relic (Mac, possibly Android), state as of Oct 2026

Method note: huggingface.co, arxiv.org and ai.google.dev could not be reached from this environment (see Blocked sources), so I could not read model cards or paper tables directly. Benchmark numbers below come from search-result snippets of those papers or from secondary sources, and each one says so. GitHub repos were cloned read-only (`git clone --depth 1`, never executed) into `/tmp/claude-0/-home-user-albers-club/3712d12f-853b-5b60-93d4-c8956af51529/scratchpad/clones/`. Repo READMEs are the vendors' own claims, so every benchmark number is **self-reported** unless marked otherwise.

## 1. Small (≤10B) video-capable models: benchmarks, licenses, Apple Silicon support

### Takeaway
On a Mac today, the practical choices are Qwen3-VL-2B/4B/8B (Apache-2.0, timestamp-aware video, mlx-vlm support), Qwen3.5 small (0.8B–9B, natively multimodal, mlx-vlm `qwen3_5` handles video), Gemma 4 E2B/E4B (Apache-2.0, video capped at about 60 s at 1 fps, plus audio up to 30 s), InternVL3.5-2B/4B/8B and MiniCPM-V 4.7-1B (Apache-2.0). Gemma 4 E4B and Qwen3-VL/Qwen3.5-4B fit the short-video job well: TikToks are mostly under 60 s, and a 4B model at 4-bit uses about 3.6 GB. FastVLM uses Apple's research-only model license and has no documented video support. VideoLLaMA3's online service is marked non-commercial.

### Cited Findings
**Qwen3-VL (Alibaba)**
- Qwen3-VL-4B and -8B (Instruct and Thinking) were released 2025-10-15, and Qwen3-VL-2B on 2025-10-21 — [Qwen3-VL README](https://github.com/QwenLM/Qwen3-VL)
- The README lists "Text–Timestamp Alignment" for timestamp-grounded event localization in video. Video sampling is controllable by `fps` (default 2) or `num_frames`, and `total_pixels` caps video tokens; the README recommends keeping it below 24576×32×32 — [Qwen3-VL README](https://github.com/QwenLM/Qwen3-VL)
- The Qwen3-VL Technical Report (arXiv 2511.21631, Nov 2025) covers dense 2B/4B/8B/32B plus MoE models and reports MVBench, Video-MME w/o sub, MLVU M-Avg and LVBench. I could not retrieve the actual numbers — [arXiv abs](https://arxiv.org/abs/2511.21631), [mirror PDF](https://aiskyeye.com/wp-content/uploads/2026/05/0402%E7%BB%84%E4%BC%9Aqwen3-vl.pdf)
- An aggregator lists MVBench = 68.7 for Qwen3-VL-8B-Instruct, but marks 0 of 14 rows as verified. Unverified — [Codesota](https://www.codesota.com/model/qwen3-vl-8b-instruct)
- mlx-vlm has a `qwen3_vl` model directory whose processor and model code handle video. Note that the README's "video chat" list still names only Qwen2-VL, Qwen2.5-VL, Idefics3, LLaVA, MiniMax M3, LLaVA-OneVision and Mage-VL (repo HEAD 2026-10-16) — [mlx-vlm](https://github.com/Blaizzy/mlx-vlm)
- Community benchmark for Qwen3-VL-4B-Instruct on a 16 GB M4 (10-core GPU) with oMLX at 1k context: 411 tok/s prompt processing, 37 tok/s generation, about 3.6 GB peak memory. On the 8-core M4: 311 PP / 36.8 TG at 1k context, and 284 PP / 30 TG at 4k context. These are text benchmarks, not video — [oMLX community benchmarks](https://omlx.ai/benchmarks/wzpmndv0)
- On an M4 Max with vllm-mlx, Qwen3-VL-8B analysed a 32-frame video in 9.4 s cold and 0.38 s on a cached repeat. Text generation at 4-bit ran at 159 tok/s for Qwen3-4B and 93 tok/s for Qwen3-8B — [vllm-mlx paper, arXiv 2601.19139](https://arxiv.org/html/2601.19139v1) (via search snippet)

**Qwen3.5 small**
- Qwen3.5-9B, -4B, -2B and -0.8B were released 2026-03-02. Their license file ships with the weights on HF/ModelScope, and the README shows small-model benchmarks only as an image — [Qwen3.5 README](https://github.com/QwenLM/Qwen3.5)
- mlx-vlm's `qwen3_5` architecture is "Hybrid Qwen3.5 text (gated-delta + full attention) + Qwen3-VL vision tower" with modalities "Text, image, video", and reuses the Qwen3-VL processor — [mlx-vlm qwen3_5 README](https://github.com/Blaizzy/mlx-vlm/blob/main/mlx_vlm/models/qwen3_5/README.md)

**Gemma 4 (Google)**
- Released 2026-04-02 under Apache 2.0 in E2B, E4B, 26B-A4B (MoE) and 31B sizes, all vision-capable. The small models use Per-Layer Embeddings — [Simon Willison](https://simonwillison.net/2026/Apr/2/gemma-4/)
- According to the model card as quoted by secondary sources, video supports at most 60 s assuming 1 frame/s, and E2B/E4B also take audio up to 30 s. Sources disagree on whether a "12B" variant exists or takes audio — [Unsloth Gemma 4 docs](https://unsloth.ai/docs/models/gemma-4), [Datature blog](https://datature.io/blog/gemma-4-what-computer-vision-engineers-actually-need-to-know), [dev.to guide](https://dev.to/pulkitgovrani/gemma-4s-audio-and-video-inputs-a-hands-on-guide-nobody-has-written-yet-2m2c)
- The mlx-vlm Gemma 4 config has `vision_soft_tokens_per_video_frame: int = 70`, so a 60-frame clip is about 4,200 visual tokens — [mlx-vlm gemma4/config.py](https://github.com/Blaizzy/mlx-vlm/blob/main/mlx_vlm/models/gemma4/config.py)
- E2B targets mobile and edge through LiteRT-LM/MediaPipe, which is relevant for Android — [LiteRT-LM Gemma 4](https://ai.google.dev/edge/litert-lm/models/gemma-4) (search snippet only; page blocked)
- I found no Video-MME score for Gemma 4 E2B/E4B. The DeepMind page lists only text and reasoning benchmarks — [DeepMind Gemma 4](https://www.deepmind.google/models/gemma/gemma-4)

**InternVL3.5 (OpenGVLab)**
- Sizes are 2B (0.3B ViT + 2.0B LLM), 4B (4.7B total) and 8B (8.5B total), with -HF variants — [InternVL README](https://github.com/OpenGVLab/InternVL)
- InternVL3.5-4B scores Video-MME 65.4 without subtitles and 68.6 with them, plus 71.2 on the next column (likely MVBench) and 70.4 / 60.8 / 64.9 on later columns, all self-reported in the paper's table. I could not verify the column mapping because arXiv was blocked — [InternVL3.5 paper](https://arxiv.org/html/2508.18265v1) (search snippet)
- mlx-vlm has `internvl_chat` with video code paths — [mlx-vlm](https://github.com/Blaizzy/mlx-vlm)

**MiniCPM-V 4.7 / 4.6 / MiniCPM-o 4.5 (OpenBMB)**
- MiniCPM-V 4.7 was released 2026-10-12 in 35B-A3B (MoE) and 1B sizes. It supports iOS, Android and HarmonyOS, is available on Ollama, and the weights are Apache-2.0 — [MiniCPM-V README](https://github.com/OpenBMB/MiniCPM-V), [model license](https://github.com/OpenBMB/MiniCPM-V/blob/main/docs/project_en.md)
- Video settings: `max_num_frames` defaults to 128; `stack_frames` (1 main frame plus N−1 sub-frames per second composited into a grid, recommended 3 or 5); `downsample_mode` of 16x (default) or 4x for visual-token compression. The vendor's example video prompt asks the model to "focus on on-screen text, interface changes, main actions, and scene changes" — [MiniCPM-V 4.7 doc](https://github.com/OpenBMB/MiniCPM-V/blob/main/docs/minicpm_v4dot7_en.md)
- MiniCPM-V 4.6 (2026-05-11) introduced mixed 4×/16× visual token compression. MiniCPM-o 4.5 is a 9B full-duplex omni model taking video and audio streams — [MiniCPM-V README](https://github.com/OpenBMB/MiniCPM-V)
- mlx-vlm runs MiniCPM-V 4.7-1B video with `--video x.mp4 --fps 1 --processor-kwargs '{"max_num_frames": 32, "max_slice_nums": 1}'` — [mlx-vlm minicpmv4_7 README](https://github.com/Blaizzy/mlx-vlm/blob/main/mlx_vlm/models/minicpmv4_7/README.md)
- Video benchmark numbers for MiniCPM-V 4.7 appear only as images in the README and were not extractable

**VideoLLaMA3 (DAMO)**
- 2B (Qwen2.5-1.5B LLM) and 7B variants. The code is Apache-2.0, but the "service is a research preview intended for non-commercial use ONLY", subject to the Qwen license and OpenAI/Gemini data terms. On 2025-01-24 the 7B was "the best 7B-sized model on VideoMME" (self-reported) — [VideoLLaMA3 README](https://github.com/DAMO-NLP-SG/VideoLLaMA3)

**SmolVLM2 (Hugging Face)**
- SmolVLM2-2.2B: Video-MME 52.1, MLVU 55.2, MVBench 46.27. These are secondary-source figures and could not be checked against the HF card — [KDnuggets](https://www.kdnuggets.com/local-video-summarization-pipeline-processing-frames-with-smolvlm2-2-2b)
- mlx-vlm has `smolvlm` with a video-capable processor — [mlx-vlm](https://github.com/Blaizzy/mlx-vlm)

**Apple FastVLM**
- Models ship under Apple's "Machine Learning Research Model" license, granted "for the sole purpose of scientific research", which is a blocker for a commercial app. The README has no video section — [ml-fastvlm LICENSE_MODEL](https://github.com/apple/ml-fastvlm/blob/main/LICENSE_MODEL), [README](https://github.com/apple/ml-fastvlm)
- mlx-vlm includes a `fastvlm` model — [mlx-vlm](https://github.com/Blaizzy/mlx-vlm)

**LLaVA-OneVision / LLaVA-Video**
- mlx-vlm lists LLaVA-OneVision as video-chat capable — [mlx-vlm README](https://github.com/Blaizzy/mlx-vlm)

**Benchmarks**
- Video-MME-v2 (arXiv 2604.05015) exists and includes Qwen3-VL-4B/8B-Think rows — [Video-MME-v2](https://arxiv.org/pdf/2604.05015)
- A frame-sampling benchmark paper argues that sampling strategy significantly changes small-VLM video scores — [arXiv 2509.14769](https://arxiv.org/html/2509.14769v2)

### Inferences
- For TikTok/Reels/Shorts (mostly 10–90 s, vertical, heavy on-screen text and speech), long-video benchmarks such as LongVideoBench and MLVU matter less than OCR-heavy short-clip comprehension. A 4B model at 1 fps with a capped token budget is adequate.
- Candidate shortlist: Qwen3-VL-4B or Qwen3.5-4B as the main captioner (Apache-2.0, timestamps, mlx-vlm), Gemma 4 E4B as an alternative that also reads ≤30 s of audio, and MiniCPM-V 4.7-1B or Qwen3.5-0.8B/2B as a fast triage tier or the Android option. I would avoid FastVLM because of its license, and VideoLLaMA3 because of its non-commercial terms.
- Benchmark numbers across vendors use different frame counts and settings and are not directly comparable.

### Gaps
- Official Video-MME/MVBench/LongVideoBench/MLVU numbers for Qwen3-VL-2B/4B/8B, Qwen3.5-small, Gemma 4 E2B/E4B and MiniCPM-V 4.7-1B: HF, arXiv and Google model-card pages were blocked.
- Qwen3.5 small license text (it ships with the weights; not verified).
- No published measurement of video seconds per clip in mlx-vlm on a 16 GB Mac; only text tok/s and an M4 Max figure.
- "Qwen3.5-VL" does not appear to be a separate product: Qwen3.5 small models are natively multimodal, inferred from mlx-vlm's `qwen3_5` docs.

## 2. Efficient pipeline: sampling, compression, caption→summarize, ASR, OCR, music, dedupe, storage

### Takeaway
The cheapest robust pipeline: dedupe by TikTok video ID first; sample at about 1 fps (or on scene changes); cap visual tokens; run one VLM call per clip that asks for a caption plus on-screen text; run separate ASR (Qwen3-ASR-0.6B/1.7B supports Korean); optionally run a local audio-fingerprint match against a user library; then summarize and tag with a small text LLM. Store a few thumbnails, the transcript, OCR text, the summary and embeddings, not the MP4.

### Cited Findings
- Qwen3-VL exposes `fps`/`num_frames` and a `total_pixels` token cap. MiniCPM-V offers `stack_frames` (sub-frames composited into a grid) and 16x token downsampling. Gemma 4 uses a fixed 70 tokens per frame in mlx-vlm — [Qwen3-VL README](https://github.com/QwenLM/Qwen3-VL), [MiniCPM-V 4.7 doc](https://github.com/OpenBMB/MiniCPM-V/blob/main/docs/minicpm_v4dot7_en.md), [mlx-vlm gemma4 config](https://github.com/Blaizzy/mlx-vlm/blob/main/mlx_vlm/models/gemma4/config.py)
- mlx-vlm CLI pattern: `mlx_vlm.generate --model ... --video path.mp4 --fps 1.0` — [mlx-vlm README](https://github.com/Blaizzy/mlx-vlm)
- mlx-vlm also ships vision feature caching, an OCR model family (DeepSeek-OCR, PaddleOCR-VL, GLM-OCR, dots-OCR) and a `privacy_filter` module — [mlx-vlm](https://github.com/Blaizzy/mlx-vlm)
- Prefix/vision caching sharply cuts repeat queries over the same video (32 frames: 9.4 s cold vs 0.38 s cached on M4 Max) — [vllm-mlx paper](https://arxiv.org/html/2601.19139v1)
- Qwen3-ASR-1.7B and -0.6B support 30+ languages including Korean (ko), Japanese, Chinese and English. The README benchmarks singing voice and songs with background music, and provides Qwen3-ForcedAligner-0.6B (Korean supported) for word timestamps — [Qwen3-ASR README](https://github.com/QwenLM/Qwen3-ASR)
- In the same README, Qwen3-ASR is compared against Whisper-large-v3, GPT-4o-Transcribe, Gemini-2.5-Pro and Doubao-ASR on public, multilingual and BGM benchmarks (self-reported) — [Qwen3-ASR README](https://github.com/QwenLM/Qwen3-ASR)
- Gemma 4 E2B/E4B can take audio directly (≤30 s), an alternative to a separate ASR pass for short clips — [Unsloth Gemma 4](https://unsloth.ai/docs/models/gemma-4)
- Local music identification: Olaf is a lightweight open-source landmark fingerprinter that runs on desktop, browser and microcontrollers (≥250 kB RAM) — [Olaf JOSS paper](https://joss.theoj.org/papers/10.21105/joss.05459.pdf). Panako handles pitch- and tempo-shifted audio but its docs warn about patents — [Panako readme](https://0110.be/releases/Panako/Panako-latest/readme.html). An audfprint-based Docker tool matches local-library tracks in videos even with dialogue over the music, with no internet — [music-identification](https://hub.docker.com/r/gpocali/music-identification)
- On TikTok itself, sound/track metadata is available without audio recognition: yt-dlp maps `music.title` → `track` and `music.authorName` → `artists` — [yt-dlp tiktok.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/tiktok.py)

### Inferences
- Music: for TikTok, take the "sound" name from page metadata (DOM, rehydration JSON or export), which is better than fingerprinting. Local fingerprinting only identifies songs already in a reference DB the user owns. There is no offline equivalent of Shazam's catalogue.
- Dedupe: key on the canonical numeric video ID (from `/@user/video/<id>` URLs; yt-dlp's `_VALID_URL` captures it, and vm.tiktok.com short links resolve to it). For screen-capture inputs with no ID, use a perceptual hash (pHash/dHash) of 2–3 keyframes plus the ASR text hash.
- Sampling: TikToks are short, so uniform 1 fps capped at about 32 frames, plus scene-change keyframes for fast-cut edits, is a sensible default. Reserve higher fps (Qwen default is 2) for an on-demand "re-analyse" action.
- Two-stage design (per-clip VLM caption plus OCR, then text LLM summary and tags) lets the expensive VLM run once per unique ID while summaries can be regenerated cheaply.
- Storage: about 3 JPEG thumbnails (~50–150 KB total) plus transcript, OCR, summary and embeddings come to a few hundred KB per video, versus 2–10 MB per MP4. Keeping MP4s also raises the ToS and copyright issues in section 3.

### Gaps
- No primary source found comparing scene-detection vs uniform sampling specifically on short vertical videos.
- No measured Korean WER for Qwen3-ASR or Whisper on social-media audio. The README's Korean rows I found were for forced alignment and LID, not WER.

## 3. Capturing TikTok on desktop: DOM, data export, DMA API, downloading

### Takeaway
On tiktok.com, the video page embeds a JSON blob (`__UNIVERSAL_DATA_FOR_REHYDRATION__` → `webapp.video-detail.itemInfo.itemStruct`) with ID, description/caption, author, music title and author, and like/share/comment/save counts. A browser extension can read the same data. The official data export and DMA Portability API give watch ("Browsing") history, Favorites and Likes, but only as a date plus a video link (no MP4, no watch duration). yt-dlp's TikTok extractor works again after August 2026 fixes but breaks periodically. Downloading others' videos conflicts with TikTok's terms (official ToS text not verified).

### Cited Findings
- yt-dlp extracts `<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">` from the page and reads `webapp.video-detail` → `itemInfo.itemStruct`. Field mapping: `diggCount`→like_count, `shareCount`→repost_count, `commentCount`→comment_count, `collectCount`→save_count, `music.title`→track, `music.authorName`→artists. Test cases include description, duration, uploader, uploader_id, upload timestamp and thumbnails — [yt-dlp tiktok.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/tiktok.py)
- yt-dlp TikTok extractors cover single video, user, sound, effect, tag, collection, vm.tiktok short links and live, but there are no "liked" or "favorites" feed extractors — [yt-dlp tiktok.py](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/tiktok.py)
- Status: there were breakages in early 2026 ("Unable to extract universal data for rehydration"; "failure to extract webpage data") — [issue #15506](https://github.com/yt-dlp/yt-dlp/issues/15506), [issue #16199](https://github.com/yt-dlp/yt-dlp/issues/16199). A challenge-solving fix (#16223) followed, then release 2026.08.19 with "Fix extractor" (#17452), "Fix formats extraction" (#17460) and "Support share URLs" (#17459). The repo HEAD I cloned is dated 2026-10-10 — [yt-dlp Changelog](https://github.com/yt-dlp/yt-dlp/blob/master/Changelog.md)
- The DMA Data Portability API data types under Activity include Favorite Videos (Date, link), Like List (Date, link), Browsing History (Date, "Video landing page link") and Search History. It also covers profile, posts and DMs — [TikTok Data Portability data types](https://developers.tiktok.com/doc/data-portability-data-types)
- The API was launched in March 2024 for the DMA. EEA users can authorise one-time or recurring transfers by category or for the full archive. It is open to applicants globally but requires a "well-defined use case" — [TechCrunch](https://techcrunch.com/2024/03/04/tiktok-rolls-out-data-portability-api-ahead-of-europes-dma-regulatory-deadline), [TikTok newsroom](https://newsroom.tiktok.com/en-eu/tiktoks-compliance-with-the-dma), [Social Media Today](https://www.socialmediatoday.com/news/tiktok-launches-data-portability-api-to-meet-new-eu-requirements/709266/)
- Manual export: Watch/Browsing history entries contain only a link and a view date, with no watch duration or discovery source. The "All data" option includes it, but choosing only "Activity" reportedly does not — [DTI Portmap](https://portmap.dtinit.org/articles/watch-history3.md/). A JSON export takes days to prepare — [tikfav (npm)](https://www.npmjs.com/package/tikfav). A third-party claim that in-app watch history keeps 180 days is unverified — [takeoutday.org](https://takeoutday.org/guides/how-to-export-tiktok-data)
- ToS: I found no official TikTok ToS text on downloading. Only unofficial paraphrases say it prohibits downloading or reproducing content you don't own and automated scraping — [unofficial copy](https://advaysnaptik.onrender.com/terms.html) (low reliability)

### Inferences
- Browser extension: on video-detail pages, parse the rehydration JSON. On the For You feed, items arrive through XHR/fetch API responses and are rendered into the DOM. The extension can read visible elements (author handle, caption, sound link, counts) and, crucially, record *dwell time*, which the export lacks. This is Relic's unique signal versus the export.
- The export or DMA API is the "backfill" source (IDs plus dates). The extension or capture is the "rich" source (what was actually on screen, how long it was watched). Enrich export links lazily by fetching public page metadata, not MP4s.
- Keep MP4 download opt-in, limited to the user's own favorites, local only, and documented as a ToS risk. yt-dlp's TikTok extractor breaks periodically, so it should not be a core dependency.

### Gaps
- Official TikTok ToS wording on downloading and automation (tiktok.com legal page not fetched).
- Whether the DMA API is available to non-EEA/UK users' own data in practice, and current approval timelines.
- Exact current DOM selectors on the tiktok.com For You feed (they change frequently; needs live inspection).

## 4. Cost/throughput on a 16 GB Mac; what to defer overnight

### Takeaway
Rough estimate, not measured: a 16 GB M4 running a 4-bit 4B VLM at 1 fps / ≤32 frames should take on the order of 10–30 s of VLM time per 30–60 s clip, or roughly 100–300 videos/hour for vision alone. ASR (0.6B–1.7B) and embeddings add much less. Heavy users watch hundreds of TikToks a day, so real-time analysis of everything is borderline. Capture metadata and thumbnails live and defer VLM captioning to idle or overnight, charging-only batches.

### Cited Findings
- Qwen3-VL-4B-Instruct on a 16 GB M4 measured about 300–410 tok/s prefill and about 30–37 tok/s generation at about 3.6 GB peak memory (text benchmark, community-reported) — [oMLX benchmarks](https://omlx.ai/benchmarks/wzpmndv0)
- Gemma 4: 70 visual tokens per frame (mlx-vlm config), with video at 60 s max at 1 fps — [mlx-vlm gemma4 config](https://github.com/Blaizzy/mlx-vlm/blob/main/mlx_vlm/models/gemma4/config.py), [Unsloth](https://unsloth.ai/docs/models/gemma-4)
- Qwen3-VL-8B processed 32 frames in 9.4 s cold on an M4 Max, a much faster GPU than a base M4 — [vllm-mlx paper](https://arxiv.org/html/2601.19139v1)

### Inferences
- Worked estimate (my arithmetic, unverified): 30 frames × 70 tokens = 2,100 visual tokens, plus a 300-token prompt, at about 300 tok/s prefill is about 8 s. Add the vision encoder (a few seconds) and a 150-token caption at about 35 tok/s (about 4 s): roughly 12–20 s per clip, or about 180–300 clips/hour for a 4B on a base M4. An 8B model is about 2× slower. Qwen3-VL at higher per-frame resolution could be 2–4× more tokens.
- What to run live: ID dedupe, metadata/DOM capture, 1–3 thumbnails, perceptual hash.
- What to defer overnight: VLM captioning/OCR, ASR, text-LLM summaries, embeddings and re-indexing.
- 16 GB budget: a 4-bit 4B VLM (about 3.6 GB), a 0.6B ASR model and a small embedding model can coexist. Load them sequentially in batch mode to keep the machine responsive.
- Android: Gemma 4 E2B via LiteRT-LM and MiniCPM-V 4.7-1B (Android support claimed) are the realistic on-device options. Expect far lower throughput, so the phone should capture and the Mac should analyse.

### Gaps
- No direct measurement of mlx-vlm video throughput on 8/16 GB base M-series chips; this needs a local benchmark.
- Thermal and battery behaviour under sustained batch inference on fanless MacBook Air.

## 5. Embeddings for video retrieval (text→video, multilingual)

### Takeaway
The strongest local option found is Qwen3-VL-Embedding (2B/8B; 30+ languages; text, image and video inputs) together with Qwen3-VL rerankers. mlx-vlm already supports `qwen3_vl_embedding` and Qwen3-VL rerankers that accept video. A cheaper path embeds the generated text (summary, transcript, OCR) with a multilingual text embedder, plus SigLIP2 or similar image embeddings of thumbnails. ColQwen2.5 (also in mlx-vlm) is document-oriented.

### Cited Findings
- Qwen3-VL-Embedding comes in 2B and 8B, supports 30+ languages and inputs up to 32k tokens, and scores 77.8 overall on MMEB-V2 (self-reported) — [Qwen3-VL-Embedding report, arXiv 2601.04720](https://arxiv.org/pdf/2601.04720v2)
- On the independent MVEB benchmark, Qwen3-VL-Embedding-8B leads text→video retrieval at 75.8 nDCG@10 and video→text at 72.6 — [MVEB, arXiv 2606.14958](https://arxiv.org/pdf/2606.14958)
- mlx-vlm includes `qwen3_vl_embedding`, `colqwen2_5`, `siglip`, `embedding_gemma2` and `lfm2_colbert` models, and Qwen3-VL rerankers accept `video`/`video_url` objects — [mlx-vlm README/models](https://github.com/Blaizzy/mlx-vlm)
- A FiftyOne plugin exists for Qwen3-VL embeddings — [Voxel51 docs](https://docs.voxel51.com/plugins/plugins_ecosystem/qwen3vl_embeddings.html)

### Inferences
- For Relic's use case ("that video where a guy cooks kimchi jjigae with subtitles in Korean"), text-side retrieval over transcript, OCR and caption probably carries most of the signal. Hybrid search (BM25 plus multilingual text embeddings plus Qwen3-VL-Embedding-2B on 4–8 frames) is a sensible design.
- Embed at most 8 frames per video, or a video-level embedding, to keep the index small. The 2B embedder is the 16 GB-friendly choice.

### Gaps
- No MSR-VTT or multilingual (Korean) text→video numbers found for Qwen3-VL-Embedding, SigLIP2 or InternVideo2.
- InternVideo2 and SigLIP2 current status and licenses were not verified (HF blocked).

---

### Blocked sources (could not reach)
- https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct (WebFetch DNS failure; git clone through proxy got 403)
- https://huggingface.co/Qwen/Qwen3.5-9B, https://huggingface.co/google/gemma-4-E4B-it, https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct, https://huggingface.co/OpenGVLab/InternVL3_5-8B (git clone 403, huggingface.co not allowed)
- https://ai.google.dev/gemma/docs/core/model_card_4 (DNS failure)
- https://arxiv.org/html/2511.21631 (Qwen3-VL Technical Report; DNS failure)
- https://arxiv.org/html/2508.18265 (InternVL3.5 paper; DNS failure)
- TikTok official Terms of Service page (not fetched; no official result surfaced in search)
