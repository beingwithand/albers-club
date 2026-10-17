# Local research handoff

What to do on your own computer, where fewer things are blocked, to finish what this cloud session couldn't. It covers verifying facts, reading primary sources and running hands-on tests on a real Mac.

## 1. Set up
1. Clone the research branch:
   ```
   git clone -b research/personal-data-ownership https://github.com/beingwithand/albers-club relic-research
   cd relic-research
   ```
2. Open it with Claude Code. The `reports/` folder has every report, `research_notes/` has the source notes, and `reports/CORRECTIONS.md` has the corrections log and standing checks.
3. Start the session with:
   > Read reports/CORRECTIONS.md and reports/Local research handoff.md. Work through section 3 (verification) using WebFetch on primary sources. For each item, record verified / corrected / still unverifiable with the URL, update the affected report with an errata line, and add a CORRECTIONS.md row for anything that changed. Then do section 4.

## 2. What was blocked in the cloud session
These hosts were rejected by the network proxy or failed to resolve, so findings that depend on them came from search-result summaries:
- **Papers:** arxiv.org and export.arxiv.org, so every paper was read through summaries or its code repo.
- **Vendors:** openai.com, help.openai.com, about.fb.com, research.meta.ai, developers.google.com, Google Workspace help, learn.microsoft.com, blogs.windows.com, the Android Developers blog, signal.org, brave.com, tailscale.com, iroh.computer.
- **Projects:** immich.app, nextcloud.com, docs.mem0.ai, docs.screenpi.pe, the Zep blog, sia.tech, filecoin.io, ipshipyard.com, automerge.org, Hugging Face (model and dataset cards).
- **Press and researchers:** techcrunch.com, infoq.com, selfh.st, simonwillison.net, embracethered.com, ioactive.com.
- **GitHub REST API** (star counts, release dates). Plain `git clone` worked.

The gap-research notes (in `research_notes/Relic gap research/`) each end with a "Blocked sources" list. Deduplicated, they add:
- **Papers:** all of arxiv.org, including the ABC paper (2507.02825), GKD (2306.13649), the Qwen3-VL tech report (2511.21631), GUI-Owl-1.5 (2602.16855), MAI-UI (2512.22047), UI-Venus-1.5 (2602.09082), UI-TARS-2 (2509.02544) and the Apple FM tech report (2507.13575).
- **Hugging Face:** every model and dataset card (including Qwen3-VL-8B-Instruct, Holo1.5-7B, OpenCUA-7B, GUI-Owl-7B and the AgentNet dataset), plus the MTEB leaderboard and ViDoRe spaces.
- **Leaderboards:** os-world.github.io (OSWorld-Verified), gui-agent.github.io/grounding-leaderboard (ScreenSpot-Pro), and xlang.ai/blog/osworld-verified.
- **Apple:** machinelearning.apple.com/research/apple-foundation-models-2025-updates.
- **Google:** the Play Console Help pages for the AccessibilityService policy (support.google.com/googleplay/android-developer/answer/10964491), the 30 Oct 2025 announcement (answer/16550159) and the policy deadlines table (table/12921780); the Android Developers Blog post on developer verification (2026/03); ai.google.dev/gemini-api/terms and ai.google.dev/gemma/terms.
- **Microsoft:** support.microsoft.com, "Experimental agentic features" page.
- **OpenAI:** openai.com/policies/terms-of-use and /policies/services-agreement; open.windriver.com (archived OpenAI ToU 2024-12-11); conductatlas.com (OpenAI EU terms provision).
- **Others:** thinkingmachines.ai/blog/on-policy-distillation; mjtsai.com (Sequoia Screen Recording and the persistent-content-capture entitlement); dev.to (WWDC26 Foundation Models write-up); the github.com/a2aproject/A2A web page (the repo itself cloned fine).
- **GitHub clones that failed** (auth prompt; possibly renamed or private): microsoft/GKD, jxzhangjhu/MiniLLM, GUI-World/GUI-World, Yiheng-Xu/AgentTrek, xlang-ai/os-world.github.io, gui-agent/gui-agent.github.io.

## 3. Verification checklist (highest value first)
**Product claims that rest on search summaries:**
- [ ] OpenAI "dots" (DevDay, 29 Sep 2026): the official post, model name ("GPT-6 Astra" is unverified), memory behaviour, pricing.
- [ ] Meta Muse: the Muse Spark, Muse app and Muse Wonder announcements; the Active Memory and "forget" behaviour; the TIME article of 6 Oct 2026.
- [ ] ChatGPT memory "Dreaming" (about 4 Jun 2026): the official page and its date.
- [ ] OpenAI Atlas: discontinued in Aug 2026, or not?
- [ ] The Claude in Chrome GA date and the reported attack-success figures.
- [ ] Ninth Circuit, Amazon v. Perplexity (about Aug 2026): read the opinion itself.

**Papers to read in full (arXiv):**
- [ ] Mem0 (2504.19413): hyperparameters, and paper versus code (see the build guide).
- [ ] Zep/Graphiti (2501.13956), HippoRAG 2, LightRAG, MemGPT (2310.08560), sleep-time compute (2504.13171), MemOS, A-MEM, Generative Agents. Check the recency formula against the code bug we found.
- [ ] LongMemEval, LoCoMo, MemoryAgentBench, BEAM: how they're constructed, and their critiques.
- [ ] Walrus Red Stuff (2505.05370) and the IMC '26 NAT-traversal study (2510.27500), if the shared-storage idea comes back.

**Docs and policies:**
- [ ] Google Play's accessibility policy, and its ban on autonomous AI agents (exact text and date).
- [ ] macOS Screen Recording re-prompt behaviour, and whether a Mac App Store (sandboxed) build can do capture plus accessibility.
- [ ] Google's Data Portability API country list, and the Gmail restricted-scope / CASA cost.
- [ ] Anthropic, OpenAI and Google terms on using outputs to train models (exact clauses).
- [ ] Licenses of each candidate open teacher and student model, and of the GUI datasets (commercial use?).
- [ ] Weight licences on the Hugging Face model cards for **GUI-Owl-1.5**, **UI-Venus-2** and **MAI-UI** (only the repo code licences were seen: MIT, an Apache-2.0 badge and Apache-2.0).
- [ ] The 2026 GUI benchmark claims, checked independently on the official leaderboards (OSWorld-Verified at os-world.github.io, ScreenSpot-Pro at gui-agent.github.io): especially UI-Venus-2-9B's 70.8 on OSWorld-Verified, and GUI-Owl-1.5 and MAI-UI.
- [ ] The exact current clauses on training with outputs in **OpenAI's** Terms of Use and Services Agreement, and **Google's** Gemini API Additional Terms, Cloud Service Specific Terms and current Gemma terms (does Gemma 4 under Apache-2.0 drop the "Model Derivatives" clause?).
- [ ] Hugging Face dataset cards for **AITW, AndroidControl, AMEX, OS-Atlas, Aguvis, GUI-World, Rico and Multimodal-Mind2Web**: the licence, and whether commercial training is allowed.

**Numbers to replace with real data:**
- [ ] GitHub stars and release dates for the build guide's license table.
- [ ] Screenpipe's current license text and pricing.

## 4. Hands-on tests on your Mac (the most important part)
These can't be done in the cloud at all:
1. **Korean text recognition:** screenshot Korean pages (KakaoTalk, Naver, Instagram in Korean) and compare Apple Vision (Live Text / VNRecognizeTextRequest) against PaddleOCR. Note accuracy and speed.
2. **Accessibility text coverage:** how much on-screen text the accessibility API returns in Chrome, Safari, KakaoTalk, Slack, Instagram on the web and Electron apps, compared with OCR.
3. **Local model speed and memory:** with MLX or llama.cpp, run the 3–4B and 7–8B candidates from `on_device_models.md` at 4-bit. Record tokens per second, RAM, and quality on 20 fact-extraction examples.
4. **Permission flow:** build a tiny signed test app that requests Screen Recording, Accessibility and Automation. Record every prompt, and how often it re-prompts.
5. **The 2-week test** (from the build guide): 50–100 of your real tasks, local models versus a frontier model. This decides where the hybrid line goes.

## 5. When you're done
- Commit the updated reports and CORRECTIONS.md to `research/personal-data-ownership`.
- Check that the files are actually in the commit (`git show --stat HEAD`) before pushing. This rule exists because of CORRECTIONS row 13.

## Added 2026-10-17 (video feeds round)
- [ ] xAI Grok Bot: read xAI's own docs/news post (launch 11 Aug 2026, pricing, connectors, MCP rules, whether it uses screenshots or DOM, video analysis method). Find any demo of it scrolling TikTok.
- [ ] TikTok's official Terms of Service: the automation and download clauses.
- [ ] Hugging Face model cards and weight licenses: Qwen3-VL, Qwen3.5 (VLM), Gemma 4, InternVL3.5, SmolVLM2, MiniCPM-V 4.7. Official Video-MME, MVBench and MLVU scores.
- [ ] Gemini video-understanding docs (ai.google.dev): tokens per second, frame rate options.
- [ ] Hands-on: Qwen3-VL-4B video on your Mac via mlx-vlm. Measure seconds per TikTok clip and Korean caption quality.
- Blocked this round: huggingface.co, arxiv.org (Qwen3-VL and InternVL3.5 reports), ai.google.dev, xAI pages, TikTok terms.
- [ ] iPhone Mirroring on your Mac: can a Mac agent reliably click and type into the mirrored iPhone? Does the window expose accessibility text? What do Apple's terms say? Test it with TikTok and Instagram.


## Decision 2026-10-17: English only
Skip the Korean-specific checks: Korean OCR comparison, Korean ASR, Korean name keys, Kakao/Naver exports, Korean law. Instead, test English OCR and accessibility coverage, Parakeet versus Whisper speed on your Mac, and US-specific items (CCPA authorized-agent flow, two-party-consent states).
