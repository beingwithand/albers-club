# On-device models for Relic (state as of 16 Oct 2026)

Scope: choosing local models for each Relic job on Macs with 8–32 GB unified memory, and possibly Android. Method note: Hugging Face, arXiv, os-world.github.io, gui-agent.github.io, Apple's developer and ML sites and most blogs were **blocked** from this sandbox (DNS failure or proxy 403; see the list at the end). Primary evidence therefore comes from **GitHub READMEs and LICENSE files** (shallow-cloned on 2026-10-16; each repo's last-commit date is noted) and from **web-search summaries**. A search summary is a paraphrase of a page I could not open, so treat any number cited only to a search result as lower confidence. Unless marked otherwise, every benchmark number is **self-reported by the model's authors**. "Independent" means a third party's table or an "evaluated by us" asterisk in a competitor's README.

## Q1. GUI grounding / computer-use models ≤ ~9B (ScreenSpot, ScreenSpot-Pro, OSWorld(-Verified), AndroidWorld; licenses)

### Takeaway
The field moved a long way between mid-2025 and October 2026. In 2025 the best 7B models (UI-TARS-1.5-7B, OpenCUA-7B, GTA1-7B, Holo1.5-7B) scored about 50–58% on ScreenSpot-Pro and about 27% on OSWorld. The best Qwen3-VL/Qwen3.5-based models of 2026 at 2–9B claim 57–73% on ScreenSpot-Pro, 43–71% on OSWorld-Verified and 68–80% on AndroidWorld: GUI-Owl-1.5, MAI-UI, UI-Venus-2-9B, Step-GUI-4B and Fara1.5. **Current shortlist for Relic:** UI-Venus-2-9B, which has the highest self-reported scores; GUI-Owl-1.5-4B or 8B, which has a full 2B/4B/8B ladder and MIT code; and MAI-UI-2B or 8B (Apache-2.0) for grounding. The 2025 model to keep is OpenCUA-7B, which is MIT and allows commercial use. Avoid GTA1 (CC-BY-NC-SA data, model licence unclear) and Holo1.5-3B (Qwen Research licence).

### Cited Findings
**2026 generation (Qwen3-VL / Qwen3.5 backbones)**
- **UI-Venus-2 (inclusionAI, released Aug 2026, 9B and 27B; repo licence badge Apache-2.0).** Self-reported numbers for UI-Venus-2-9B: ScreenSpot-Pro 73.0, OSWorld-G-R 78.5, VenusBench-GD 77.1, OSWorld-Verified 70.8 (150-step budget), AndroidWorld 80.2, MobileWorld 65.8. In the same README, the authors' own re-runs put Qwen3.5-9B at 41.8 on OSWorld-Verified and 57.8 on AndroidWorld, and list MAI-UI-8B at 65.8 on ScreenSpot-Pro and 70.7 on AndroidWorld. The authors caveat that baselines "may use model-specific action scaffolds". — [inclusionAI/UI-Venus README (commit 2026-09-17)](https://github.com/inclusionAI/UI-Venus)
- **GUI-Owl-1.5 (Alibaba Tongyi/X-PLUG, released 2026-02-14).** The family comes in 2B/4B/8B/32B/235B sizes with Instruct and Thinking variants, built on Qwen3-VL. Self-reported end-to-end scores:

  | Model | OSWorld-Verified | AndroidWorld |
  |---|---|---|
  | 2B-Instruct | 43.5 | 67.9 |
  | 4B-Instruct | 48.2 | 69.8 |
  | 8B-Instruct | 52.3 | 69.0 |
  | 8B-Thinking | 52.9 | 71.6 |

  Grounding scores (ScreenSpot-v2/Pro) appear only in the technical report (arXiv 2602.16855, not reachable). The repository is MIT-licensed. I could not read the model-card licence. — [X-PLUG/MobileAgent Mobile-Agent-v3.5 README](https://github.com/X-PLUG/MobileAgent/tree/main/Mobile-Agent-v3.5); [MobileAgent README news](https://github.com/X-PLUG/MobileAgent)
- **MAI-UI (Alibaba Tongyi-MAI).** The 2B and 8B weights were released on 2025-12-29. The authors report ScreenSpot-Pro scores of 57.4 for 2B, 65.7 for 8B and 67.9 for 32B, and say these were "#1 in all size categories" on the ScreenSpot-Pro leaderboard as of 2026-01-13. The MAI-UI-235B variant scored 76.7 on AndroidWorld. The successor, Qwen-UI-Agent-27B, is Apache-2.0. — [Tongyi-MAI/MAI-UI README (commit 2026-08-19)](https://github.com/Tongyi-MAI/MAI-UI)
- **Step-GUI (StepFun).** Self-reported ScreenSpot-Pro scores: 8B 62.6, 4B 60.0. The UI-Venus-2 table reproduces Step-GUI-4B at 60.0 on ScreenSpot-Pro and 66.9 on OSWorld-G-R. — [search summary of arXiv 2512.15431](https://arxiv.org/pdf/2512.15431); [UI-Venus README](https://github.com/inclusionAI/UI-Venus)
- **GELab-Zero-4B-preview (StepFun, Nov 2025, MIT).** Reports 75.86% on AndroidWorld. The README describes running it locally through Ollama, with Q4_K_M and Q8_0 builds. — [stepfun-ai/gelab-zero README](https://github.com/stepfun-ai/gelab-zero)
- **GroundGUI-8B (arXiv preprint, Oct 2026).** Self-reported scores: ScreenSpot-Pro 63.9, ScreenSpot-V2 95.2, OSWorld-G 65.4. — [search summary, arXiv 2610.19100](https://arxiv.org/html/2610.19100)
- **Fara1.5 (Microsoft, released 2026-07-22, 4B/9B/27B on Qwen3.5; repo MIT).** These are web/browser agents. Scores on WebVoyager and Online-Mind2Web:

  | Model | WebVoyager | Online-Mind2Web |
  |---|---|---|
  | Fara1.5-4B | 80.8 | 57.3 |
  | Fara1.5-9B | 86.6 | 63.4 |
  | Fara-7B (older) | 73.5 | 34.1 |

  The README reports no ScreenSpot or OSWorld numbers. — [microsoft/fara README](https://github.com/microsoft/fara)
- **Holo2 (H Company).** Holo2-8B is listed at 58.9 and Holo2-4B at 57.2 on ScreenSpot-Pro, but only by an aggregator (BenchLM), which is low confidence. The UI-Venus README lists Holo2-30B-A3B at 66.1 on ScreenSpot-Pro. H Company has since released Holo3-35B-A3B. — [BenchLM Holo2-8B](https://benchlm.ai/md/compare/blsp-7b-vs-holo2-8b.md); [BenchLM Holo2-30B-A3B](https://www.benchlm.ai/models/holo2-30b-a3b)
- **Qwen3-VL (2B/4B/8B released Oct 2025) and Qwen3.5 small models (0.8B/2B/4B/9B released 2026-03-02).** These are general VLMs with native GUI-agent ability. I could not reach the per-size agent tables in the Qwen3-VL tech report. Re-runs by the UI-Venus authors put Qwen3.5-9B at 41.8 on OSWorld-Verified and 57.8 on AndroidWorld. Qwen3.5 small models are reported as Apache-2.0 with 262K context. — [QwenLM/Qwen3-VL README](https://github.com/QwenLM/Qwen3-VL); [QwenLM/Qwen3.5 README](https://github.com/QwenLM/Qwen3.5); [VentureBeat on Qwen3.5-9B](https://venturebeat.com/technology/alibabas-small-open-source-qwen3-5-9b-beats-openais-gpt-oss-120b-and-can-run). The Qwen3.5 README now also covers Qwen3.6 (27B, 35B-A3B) and Qwen3.8 (27B released 2026-08-14). No new small sizes were listed.

**2025 generation (Qwen2.5-VL backbones)**
- **UI-TARS-1.5-7B (ByteDance, open-sourced 2025-04-16; repo Apache-2.0).** OSWorld 27.5 (100 steps), ScreenSpot-Pro 49.6. The full, unreleased UI-TARS-1.5 scores 42.5 and 61.6. UI-TARS-2 (Sep 2025) is described in a tech report. The README gives no small open-weight UI-TARS-2. — [bytedance/UI-TARS README & LICENSE](https://github.com/bytedance/UI-TARS)
- **OpenCUA-7B (XLANG, MIT, "research, educational, and commercial purposes").** OSWorld-Verified 24.3 at 15 steps, 27.9 at 50 steps and 26.6 at 100 steps. Grounding: OSWorld-G 55.3, ScreenSpot-V2 92.3, ScreenSpot-Pro 50.0, UI-Vision 29.7. In the same table, the base Qwen2.5-VL-7B scores 27.6 on ScreenSpot-Pro. vLLM supports it. — [xlang-ai/OpenCUA README](https://github.com/xlang-ai/OpenCUA)
- **GTA1-7B (Salesforce, Oct 2025 update).** ScreenSpot-Pro 50.1 (GTA1-7B-2507) and OSWorld-G 55.1. The updated line in the README reads "93.4%, 55.5%, and 60.1%" for "Screenspot-Pro, Screenspot-V2, and OSWorld-G", which is clearly a label-order error: 93.4 must be ScreenSpot-V2 and 55.5 ScreenSpot-Pro. The repository says the **dataset is CC-BY-NC-SA 4.0, non-commercial**. — [Yan98/GTA1 README](https://github.com/Yan98/GTA1)
- **Holo1.5 (H Company, Sep 2025).** ScreenSpot-Pro: 3B 51.4, 7B 57.9, 72B 63.3. Licences: **7B is Apache-2.0**, **3B is under the Qwen Research License** (no commercial use), and 72B is research-only/CC BY-NC. — [search summary of hub.hcompany.ai and HF cards](https://hub.hcompany.ai/models/Holo1.5/aboutholo1.5); [MarkTechPost](https://www.marktechpost.com/2025/09/18/h-company-releases-holo1-5-an-open-weight-computer-use-vlms-focused-on-gui-localization-and-ui-vqa/)
- **Older baselines.** OS-Atlas-7B scored 18.9% on ScreenSpot-Pro in the original benchmark paper. SE-GUI scored 47.2 at 7B and 35.9 at 3B. Phi-Ground reports 55.0 on ScreenSpot-Pro (under 10B). JEDI-7B is about 52.6 per a Papers-with-Code mirror. — [ScreenSpot-Pro repo README](https://github.com/likaixin2000/ScreenSpot-Pro-GUI-Grounding); [search summary](https://www.sota2.com/research/sota/gui-grounding-on-screenspot-pro-test); [Phi-Ground](https://arxiv.org/html/2507.23779v1)
- **OSWorld-Verified rules.** OSWorld-Verified launched on 2025-07-28. Results appear on the verified leaderboard only if the maintainers run the agent themselves, so leaderboard entries are **independent** but README numbers are not. — [xlang-ai/OSWorld README (commit 2026-09-15)](https://github.com/xlang-ai/OSWorld)
- **llm-stats ScreenSpot-Pro leaderboard.** It shows implausible entries (e.g. "GPT-6 Astra 0.927"), so I excluded it as unreliable. — [llm-stats](https://llm-stats.com/benchmarks/screenspot-pro)

### Inferences
- For Macs, a 4B grounding model (GUI-Owl-1.5-4B, MAI-UI-2B/8B, Step-GUI-4B) at 4-bit should fit comfortably in 8 GB machines. 8–9B models (UI-Venus-2-9B, GUI-Owl-1.5-8B) suit 16 GB and up. All of these are Qwen-VL derivatives, so the MLX-VLM and llama.cpp mtmd paths for Qwen3-VL/Qwen3.5 should apply. Check per-model support.
- The jump in OSWorld-Verified scores (e.g. 70.8 for a 9B model) is self-reported, uses each lab's own scaffold, and is not yet confirmed on the verified leaderboard. Expect lower real-world success on macOS: OSWorld is mostly Ubuntu, and AndroidWorld is Android.
- A pragmatic architecture is a small grounding model (click-point prediction) plus Apple Accessibility-tree data, rather than a fully end-to-end small agent.

### Gaps
- I could not read the official ScreenSpot-Pro or OSWorld-Verified leaderboards (blocked), so I have no independent confirmation of any 2026 number.
- Model-card licences are unverified for GUI-Owl-1.5 weights, UI-Venus-2 weights, MAI-UI-2B/8B weights, Holo2, GTA1 weights and Qwen3-VL (believed Apache-2.0 but not verified here).
- I found no small-model results on macOS-specific benchmarks such as macOSWorld.
- I found no data on ShowUI, Aguvis or Jedi beyond older figures, or on Phi-vision or Gemma 3/3n/4 GUI grounding. They appear to be uncompetitive or not reported.

## Q2. Structured extraction / summarization LLMs (3–9B), constrained decoding, Korean

### Takeaway
The default open choice is **Qwen3.5-4B or 9B** (Apache-2.0, multimodal, 201 languages claimed for the Qwen3.6 generation), or Qwen3-4B/8B. Gemma 4 E2B/E4B (Apache-2.0 since April 2026) is the strongest Google option and the best fit for Android. For Korean, Qwen3-8B is far ahead of Gemma 3 4B on KMMLU. Korea-specific EXAONE 4.0 1.2B is competitive for its size, but its licence is not established here. **Apple's Foundation Models** (on-device, about 3B parameters, 2-bit) gives free guided generation via `@Generable`, gained image input at WWDC26 and covers Korean through Apple Intelligence. Its context window is small: 4,096 tokens is the most cited figure. llama.cpp (GBNF/JSON-schema) and mlx-lm (logits processors) both support constrained decoding.

### Cited Findings
- **Qwen3.5 small models.** The 0.8B/2B/4B/9B models were released on 2026-03-02. — [QwenLM/Qwen3.5 README](https://github.com/QwenLM/Qwen3.5). They are reported as Apache-2.0, natively multimodal, with 262K context (one source says 32K for 2B/4B, so sources conflict). Qwen3.5-9B reportedly scores 81.7 on GPQA-Diamond against 80.1 for gpt-oss-120b; another source gives conflicting numbers. — [VentureBeat](https://venturebeat.com/technology/alibabas-small-open-source-qwen3-5-9b-beats-openais-gpt-oss-120b-and-can-run); [Enclave AI blog](https://enclaveai.app/blog/2026/03/08/qwen-3-5-complete-model-family-local-ai/)
- **Qwen3.6 language coverage.** Qwen3.6 claims "201 languages and dialects". — [QwenLM/Qwen3.5 README](https://github.com/QwenLM/Qwen3.5)
- **Gemma 4.** Released 2026-04-02 under **Apache-2.0**, replacing the earlier custom Gemma terms. Sizes are E2B (2.3B effective, 5.1B total), E4B (4.5B effective, 8B total), 26B MoE and 31B dense. Context is 128K, with text, image, video and audio input. Approximate Q4 memory is 3.2 GB for E2B and 5 GB for E4B. — [implicator.ai](https://www.implicator.ai/google-releases-gemma-4-under-apache-2-0-dropping-its-custom-ai-license/); [emelia.io guide](https://emelia.io/hub/gemma-4-open-source-guide)
- **Korean knowledge (independent paper, KMMLU-Redux / KMMLU-Pro).**

  | Model | KMMLU-Redux | KMMLU-Pro |
  |---|---|---|
  | Qwen3-8B, non-thinking | 49.25 | 46.92 |
  | Qwen3-8B, thinking | 58.79 | 55.27 |
  | EXAONE 4.0 1.2B, non-reasoning | 40.43 | 37.48 |
  | EXAONE 4.0 1.2B, reasoning | 46.85 | 42.69 |
  | Qwen3-1.7B | 28.99 | 30.42 |
  | Gemma 3 4B IT | 25.09 | 32.86 |

  — [KMMLU-Redux→Pro paper](https://arxiv.org/html/2507.08924v2); [EXAONE-4.0-1.2B card](https://huggingface.co/LGAI-EXAONE/EXAONE-4.0-1.2B)
- **Licences of other small models (secondary sources only).** Phi-4-mini: MIT. SmolLM3-3B: Apache-2.0, 6 languages. Llama 3.2 3B: Llama Community License (commercial use allowed under 700M MAU), 8 official languages, **Korean not among them**. Ministral 3 3B/8B (2512): Apache-2.0. — [tinyweights](https://tinyweights.dev/posts/smollm3-3b-vs-phi-4-mini/); [dev.co Phi-4-mini](https://dev.co/ai/llms/phi-4-mini-instruct); [anotherwrapper](https://anotherwrapper.com/llm-pricing/phi-4-mini/ministral-3-8b-instruct-2512)
- **Apple Foundation Models: model.** An on-device model of about 3B parameters, using KV-cache sharing (37.5% less KV memory) and 2-bit quantization-aware training. A PT-MoE server model runs on Private Cloud Compute. — [Apple FM Tech Report 2025 (arXiv 2507.13575, via search)](https://machinelearning.apple.com/research/apple-foundation-models-tech-report-2025)
- **Apple Foundation Models: guided generation.** `@Generable` and `@Guide` constrain output to Swift types (value sets, regex-like patterns). — [WWDC25 "Deep dive into the Foundation Models framework"](https://developer.apple.com/videos/play/wwdc2025/301/)
- **Apple Foundation Models: context.** `contextSize` and token-counting APIs arrived in iOS/macOS 26.4. The on-device context is most often cited as **4,096 tokens**; one write-up shows 8,192, so sources conflict. Read `SystemLanguageModel.default.contextSize` at runtime. The PCC model is said to offer 32K (third-party claim). — [WWDC26 session 319](https://developer.apple.com/videos/play/wwdc2026/319/); [blakecrosley.com](https://blakecrosley.com/blog/apple-foundation-models-framework); [ivanmagda.dev](https://ivanmagda.dev/posts/wwdc26-foundation-models-year-two/)
- **Apple Foundation Models: WWDC26 changes.** The on-device model gained image input (UIImage, NSImage, CGImage, pixel buffers, URLs) and has improved reasoning and tool calling. — [WWDC26 session 241](https://developer.apple.com/videos/play/wwdc2026/241/); [blakecrosley iOS 27 image input](https://blakecrosley.com/blog/foundation-models-image-input-ios-27)
- **Apple Intelligence and Korean.** Korean is a supported Apple Intelligence language on macOS/iOS 26.1 and was already in the WWDC25 list. — [Apple Support 121115](https://support.apple.com/en-mt/121115); [9to5Mac](https://9to5mac.com/?p=1020829)
- **llama.cpp constrained decoding.** llama.cpp supports GBNF grammars and converts JSON Schema to grammar per request (`json_schema`, or `response_format` on `/chat/completions`). The schema constrains output but is not injected into the prompt. — [ggml-org/llama.cpp grammars/README](https://github.com/ggml-org/llama.cpp/tree/master/grammars)
- **mlx-lm constrained decoding.** mlx-lm exposes `logits_processors` and custom samplers, which is the hook used by Outlines-style constrained decoding. It has no built-in JSON-schema flag in its README. — [ml-explore/mlx-lm README (commit 2026-10-16)](https://github.com/ml-explore/mlx-lm)

### Inferences
- Apple FM is ideal for short, schema-bound extractions (a single email or a screenshot caption) at zero download cost. Its roughly 4K context makes it unsuitable for long-document summarization, which should go to Qwen3.5-4B/9B or Gemma 4 E4B through MLX or llama.cpp with JSON-schema grammars.
- For Korean-heavy content, prefer the Qwen family, or evaluate EXAONE. Avoid Gemma 3 4B and Llama 3.2 3B.

### Gaps
- I found no KMMLU numbers for Qwen3.5, Gemma 4 or Apple FM, and no independent Korean evaluation of Apple's on-device model.
- The Outlines MLX integration status was not verified (pages blocked).
- I could not read official model cards for Phi-4-mini, SmolLM3 or Ministral 3 (HF blocked), so their licences rest on secondary sources.

## Q3. OCR on Mac (Apple Vision, Korean, PaddleOCR, small VLM OCR)

### Takeaway
Use **Apple Vision `RecognizeTextRequest` (macOS 15+) as the default**. It is free, fast and on the Neural Engine, and Korean ("ko-KR") is supported in revision 3, whereas the older revision 2 lacked Korean. Use **PaddleOCR** as an open fallback: it has a dedicated Korean PP-OCRv5 model, and PaddleOCR-VL (0.9B) covers 109+ languages including Korean. For full document parsing to Markdown, small VLM OCR is now strong: dots.ocr (1.7B, MIT) and dots.mocr (3B), PaddleOCR-VL-1.5/1.6 (0.9B), and olmOCR-2-7B. Most of these are CUDA/vLLM-first, and I found no Apple Silicon speed numbers.

### Cited Findings
- **Apple Vision, revision 2.** `VNRecognizeTextRequestRevision2` accurate mode supported English, Chinese, Portuguese, French, Italian, German and Spanish, with no Korean. — [Apple Dev Forums 684807](https://developer.apple.com/forums/thread/684807)
- **Apple Vision, revision 3.** On `RecognizeTextRequest` revision 3 (iOS 18 / macOS 15+), `supportedRecognitionLanguages` includes Korean (developer forum report). An AppleScript output on macOS also lists "ko-KR". — [Apple Dev Forums 765905](https://developer.apple.com/forums/thread/765905); [Apple docs: supportedRecognitionLanguages](https://developer.apple.com/documentation/vision/recognizetextrequest/supportedrecognitionlanguages.md); [MacScripter](https://www.macscripter.net/t/image-png-to-text-through-applescript/74490?page=2)
- **PP-OCRv5 Korean.** The `korean_PP-OCRv5_mobile_rec` model (Korean and English) reports **88.0% accuracy** on PaddleOCR's own dataset, +65.0 points over the previous generation. PaddleOCR is Apache-2.0. — [PaddleOCR PP-OCRv5 multi-language doc](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.en.md)
- **PP-OCRv6 (PaddleOCR 3.7.0, 2026-06-11).** The unified model covers 50 languages: Chinese, English, Japanese and 46 Latin-script languages. **Korean is not in the unified v6 model**, so keep the v5 Korean model. — [PaddleOCR README (commit 2026-09-16)](https://github.com/PaddlePaddle/PaddleOCR)
- **PaddleOCR-VL.** PaddleOCR-VL-0.9B (ERNIE-4.5-0.3B decoder, Oct 2025) covers 109 languages including Korean. Version 1.5 (Jan 2026) covers 111 languages. Version 1.6 (May 2026) reports 96.3% on OmniDocBench v1.6. PaddleOCR.js runs PP-OCRv5 in the browser. — [PaddleOCR README](https://github.com/PaddlePaddle/PaddleOCR)
- **dots.ocr and dots.mocr.** dots.ocr (1.7B LLM, July 2025, MIT) scores 79.1 on olmOCR-bench. dots.mocr (3B, renamed from dots.ocr-1.5 in Mar 2026) scores 83.9.

  Other olmOCR-bench scores from the same table:

  | Model | olmOCR-bench |
  |---|---|
  | olmOCR v0.4.0 (olmOCR-2-7B) | 82.4 |
  | Chandra OCR 0.1.0 | 83.1 |
  | PaddleOCR-VL | 80.0 |
  | DeepSeek-OCR | 75.7 |
  | Nanonets-OCR2-3B | 69.5 |
  | Mistral OCR API | 72.0 |

  In the same README's Elo ranking (judged by Gemini 3 Flash), dots.mocr ranks above HunyuanOCR, PaddleOCR-VL-1.5 and GLM-OCR. — [rednote-hilab/dots.ocr README](https://github.com/rednote-hilab/dots.ocr)
- **olmOCR-2-7B-1025 (Oct 2025).** Served with vLLM in FP8, which is a GPU-oriented pipeline. — [allenai/olmocr README](https://github.com/allenai/olmocr)
- **Qwen3.5-9B on OmniDocBench.** Reported at 87.7 on OmniDocBench v1.5 (secondary source). — [VentureBeat](https://venturebeat.com/technology/alibabas-small-open-source-qwen3-5-9b-beats-openais-gpt-oss-120b-and-can-run)

### Inferences
- A sensible OCR pipeline is Vision `RecognizeTextRequest` for screenshots and Live-Text-style capture, which is fast and handles Korean. Escalate to a small VLM (dots.ocr, PaddleOCR-VL or Qwen3.5-4B via MLX) only for layout, tables or low-confidence pages.
- GOT-OCR and the original Nanonets-OCR have been overtaken by the models above.

### Gaps
- I found no independent accuracy numbers for Apple Vision on Korean, no Live Text language list, and no speed figures for any of these OCR VLMs on Apple Silicon.
- I found no PaddleOCR Core ML or MLX port status.

## Q4. Embeddings and rerankers (multilingual, including Korean; screenshots)

### Takeaway
**Qwen3-Embedding-0.6B** (Apache-2.0, 32K context, 1024-dim with Matryoshka/MRL, MMTEB-multilingual 64.33) is the best quality-per-size open choice for Korean and English text. It pairs with **Qwen3-Reranker-0.6B**. Step up to the 4B model (69.45) on 32 GB Macs. bge-m3 and multilingual-e5-large are MIT-licensed fallbacks, at 59.56 and 63.22 for the -instruct variant. EmbeddingGemma-308M is the best model under 500M for Android. For screenshot retrieval, the ColQwen2.5 / colSmol family is Apache-2.0. Avoid jina-embeddings-v4 for commercial use unless you get a licence.

### Cited Findings
- **Qwen3-Embedding / Qwen3-Reranker family.**

  | Model | Embedding dim | Context | MRL | MMTEB-multilingual (mean task) |
  |---|---|---|---|---|
  | Qwen3-Embedding-0.6B | 1024 | 32K | yes | 64.33 |
  | Qwen3-Embedding-4B | 2560 | 32K | yes | 69.45 |
  | Qwen3-Embedding-8B | 4096 | 32K | yes | 70.58 |

  Rerankers come in 0.6B, 4B and 8B. Comparison rows from the same table: BGE-M3 59.56, multilingual-e5-large-instruct 63.22, gemini-embedding-exp 68.37. Korean is listed among 100+ languages. Instructions should be written in English and add 1–5%. These scores are self-reported in the authors' README table. — [QwenLM/Qwen3-Embedding README](https://github.com/QwenLM/Qwen3-Embedding)
- **Embedding licences (secondary source).** Qwen3-Embedding: Apache-2.0. BGE-M3: MIT. multilingual-e5: MIT. jina-embeddings-v4: **Qwen Research License, commercial use only with a separate licence** (one blog says Apache, so sources conflict). — [premai blog](https://blog.premai.io/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting)
- **EmbeddingGemma-308M.** "Highest ranking open multilingual text embedding model under 500M on MTEB", trained on 100+ languages. — [Google Developers Blog](https://developers.googleblog.com/en/introducing-embeddinggemma/). Licence reports conflict: the original Gemma terms vs Apache-2.0 (an "EmbeddingGemma 2" claim is unverified). — [eesel.ai](https://www.eesel.ai/blog/embeddinggemma-2)
- **ViDoRe document-retrieval scores.**

  | Model | ViDoRe | Licence |
  |---|---|---|
  | colqwen2.5-v0.2 | 89.4 | Apache-2.0 |
  | colqwen2-v1.0 | 89.3 | Apache-2.0 |
  | colSmol-500M | 82.3 | Apache-2.0 |
  | colSmol-256M | 80.1 | Apache-2.0 |
  | colpali-v1.3 | 84.8 | Gemma licence |

  Sentence-Transformers v6 integrates these models. — [illuin-tech/colpali README](https://github.com/illuin-tech/colpali)

### Inferences
- Relic could embed OCR text with Qwen3-Embedding-0.6B (about 0.4 GB at 4-bit or about 1.2 GB at fp16, estimated from parameter count) and optionally index screenshots with colSmol-500M. Multi-vector ColQwen storage is heavy, so reserve it for documents and slides.

### Gaps
- I could not read the current MMTEB leaderboard (HF space blocked), and found no Korean-specific retrieval benchmark (e.g. Ko-StrategyQA) numbers for these models.
- I did not verify the jina-v3 licence (believed CC-BY-NC).

## Q5. Speech (ASR), including Korean

### Takeaway
For Korean, **Parakeet is out**: it covers 25 European languages plus Japanese, with no Korean. The options are **Whisper large-v3-turbo** (WhisperKit Core ML, MIT, Korean supported), **Qwen3-ASR-0.6B or 1.7B** (Apache-2.0, 30 languages including Korean, released Jan 2026, and reportedly better than Whisper on Korean FLEURS), and Apple's **SpeechAnalyzer/SpeechTranscriber** on macOS 26, which reportedly includes Korean. Use Parakeet TDT v3 (via FluidAudio) only for English/European content.

### Cited Findings
- **Qwen3-ASR.** The 0.6B and 1.7B models (2026-01-29, Apache-2.0) support 30 languages, including Korean, plus 22 Chinese dialects. Qwen3-ForcedAligner-0.6B supports Korean timestamps. — [QwenLM/Qwen3-ASR README](https://github.com/QwenLM/Qwen3-ASR)
- **Korean FLEURS CER (vendor blog, not primary).**

  | Model | Korean CER |
  |---|---|
  | Qwen3-ASR-1.7B | 3.54 |
  | Whisper Large (V3 or Turbo; the row label is ambiguous) | 4.25 |
  | Apple Speech | 4.31 |
  | Whisper Small | 7.30 |
  | SenseVoice | 7.85 |

  — [whispernotes.app Apple Speech vs Whisper](https://whispernotes.app/blog/apple-speech-vs-whisper)
- **Parakeet TDT v3 (0.6B) via FluidAudio.** It runs on Core ML and FluidAudio says it supports "25 European languages and Japanese". Many Mac dictation apps use it (VoiceInk, Spokenly, Hex). Models are on HF under permissive licences. — [FluidInference/FluidAudio README](https://github.com/FluidInference/FluidAudio); Parakeet lacks Korean per [spokenly.app](https://spokenly.app/blog/parakeet-vs-whisper)
- **WhisperKit (Argmax, MIT).** Ships Core ML large-v3-turbo builds, including a compressed 626 MB variant "recommended across iOS and macOS". Korean is among its listed languages. — [argmaxinc/WhisperKit README](https://github.com/argmaxinc/WhisperKit)
- **Apple SpeechTranscriber.** It requires macOS/iOS 26 and launched with Cantonese, Chinese, English, French, German, Italian, Japanese, **Korean**, Portuguese and Spanish (secondary source citing WWDC25 session 277). Developers report the `supportedLocales` list has been unreliable across betas. — [Addpipe](https://blog.addpipe.com/apple-speechanalyzer-api/); [Apple Dev Forums 797835](https://developer.apple.com/forums/thread/797835)

### Inferences
- A good default is SpeechTranscriber (zero download) on macOS 26+, with WhisperKit large-v3-turbo or Qwen3-ASR as a fallback for older macOS and higher Korean accuracy. Qwen3-ASR on Mac would need an MLX or llama.cpp port. I did not verify one exists.

### Gaps
- I found no primary-source Korean WER/CER for distil-whisper; distil models are English-only for large-v3-based variants (not re-verified here).
- I found no Apple Silicon real-time factor for Qwen3-ASR.

## Q6. Runtimes and real performance on Apple Silicon and Android (tokens/sec, memory at 4-bit)

### Takeaway
On M-series chips, **MLX (mlx-lm / mlx-vlm / MLX-Swift)** generally matches or beats llama.cpp on decode for 3–8B 4-bit models. llama.cpp is competitive on quality per byte and often better on long-context prefill. Ollama adds overhead. Rough decode speed for an 8B 4-bit model is about 32–45 tok/s on M3 Pro / M2-class Pro chips, and much higher on Max chips. A 4-bit 8B model needs about 5 GB, which leaves 8 GB Macs tight. Plan for 3–4B models on 8 GB machines and 8–9B on 16 GB and up. On Android, Google's **LiteRT-LM** is the best-documented path (Gemma 4 E2B: about 47–52 tok/s decode on an S26 Ultra, per Google).

### Cited Findings
- **Llama 3.1 8B, MLX vs llama.cpp.** One comparison reports MLX 4-bit at about 45 tok/s against llama.cpp Q4_K_M at about 42 tok/s, and 36 vs 32 tok/s on M3 Pro. The two are roughly tied for 1–7B models. — [search summary of compute-market / local-llm.net comparisons](https://www.compute-market.com/blog/mlx-vs-llama-cpp-apple-silicon-2026)
- **MLX-Swift on M4 Max.** A reproducible benchmark on M4 Max shows MLX-Swift 4-bit at 177.8 tok/s against llama.cpp Q4_K_M at 127.1 tok/s (1.4–1.8x after early-2026 kernel updates). Its harness also covers Apple Core AI, Core ML and LiteRT-LM on iPhone 17 Pro. — [john-rocky/apple-silicon-llm-bench](https://github.com/john-rocky/apple-silicon-llm-bench)
- **Counter-evidence.** One 2026 comparison measured llama.cpp at 71.3 tok/s against MLX at 65.8, with llama.cpp marginally better in quality at equal file size, and found MLX slower on long-context prefill. On an M4 Pro running Qwen3-Coder-30B-A3B, MLX reached about 130 tok/s against about 43 tok/s through Ollama. — [yage.ai MLX vs llama.cpp (M5 Neural Accelerators, Ollama switching to MLX)](https://yage.ai/share/mlx-apple-silicon-en-20260331.html); [towardsai](https://pub.towardsai.net/apples-mlx-runs-local-llms-3x-faster-than-llama-cpp-until-your-context-hits-40k-715ec441afbb?gi=663fd87322f7)
- **Memory.** Gemma 4 at Q4 needs about 3.2 GB for E2B and about 5 GB for E4B. — [emelia.io](https://emelia.io/hub/gemma-4-open-source-guide). The Gemma 4 E4B LiteRT-LM file is 3.66 GB. — [search summary of HF litert-community](https://huggingface.co/litert-community/gemma-4-E4B-it-litert-lm)
- **LiteRT-LM (Google's claim).** Prefill and decode are 1.8–3.7x faster than llama.cpp, MLX and ONNX. Multi-token prediction gives a 2.2x decode speedup for E4B. Gemma 4 E2B on an S26 Ultra runs at 47 tok/s decode on CPU and 52 on GPU, with 3,808 tok/s prefill on GPU. An anecdotal user report on a Snapdragon 8 Elite gives E4B decode at about 17.8 tok/s. llama.cpp Hexagon NPU support is still immature. — [Google Developers Blog, Gemma 4 edge](https://developers.googleblog.com/bring-state-of-the-art-agentic-skills-to-the-edge-with-gemma-4/); [InfoQ](https://infoq.com/news/2026/06/google-litertlm-gemma4)
- **Ollama runs GUI agents locally.** Ollama can host GUI agents locally, as GELab-Zero-4B shows with Q4_K_M and Q8_0 builds. — [stepfun-ai/gelab-zero](https://github.com/stepfun-ai/gelab-zero)

### Inferences
- **Proposed Relic stack.** Use MLX-Swift (in-process, Swift-native) for the LLM and VLM, Apple FM for short guided-generation tasks, Vision for OCR and SpeechAnalyzer or WhisperKit for ASR, with llama.cpp as a fallback for GGUF-only models and grammar-heavy extraction. On Android, use LiteRT-LM with Gemma 4 E2B/E4B.
- **Memory budget on an 8 GB Mac**, roughly 6–7 GB available to apps in total:

  | Component | Approx. memory |
  |---|---|
  | One 4B 4-bit model | ~2.5–3 GB |
  | Embedder | ~0.5 GB |
  | ASR | ~0.6 GB |

  Running the GUI-grounding VLM and the text LLM at the same time is impractical at 8 GB, so swap models or use Apple FM as the text model.

### Gaps
- I found no first-party throughput numbers for Qwen3-VL/Qwen3.5 VLMs on M-series chips with screenshot inputs (image prefill dominates latency), and no ExecuTorch numbers for 2026 models.
- I found no Core ML conversions of GUI-grounding models.
- Several throughput sources are secondary blogs with unclear method. Benchmark on target hardware.

---
### Blocked sources (could not reach from this sandbox: DNS ENOTFOUND or proxy CONNECT 403)
- https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct
- https://huggingface.co/Hcompany/Holo1.5-7B
- https://huggingface.co/xlangai/OpenCUA-7B
- https://huggingface.co/mPLUG/GUI-Owl-7B
- https://huggingface.co (all model cards, MTEB leaderboard space, ViDoRe space)
- https://arxiv.org/html/2511.21631v1 (Qwen3-VL tech report) and arXiv generally (2602.16855 GUI-Owl-1.5, 2512.22047 MAI-UI, 2602.09082 UI-Venus-1.5, 2509.02544 UI-TARS-2, 2507.13575 Apple FM)
- https://os-world.github.io/ (OSWorld-Verified leaderboard)
- https://gui-agent.github.io/grounding-leaderboard/ (ScreenSpot-Pro leaderboard)
- https://machinelearning.apple.com/research/apple-foundation-models-2025-updates
- https://dev.to/hariharanjagan/whats-new-in-apples-foundation-models-framework-at-wwdc-2026-5227
- GitHub repos xlang-ai/os-world.github.io and gui-agent/gui-agent.github.io (clone failed: they do not exist under those names)
