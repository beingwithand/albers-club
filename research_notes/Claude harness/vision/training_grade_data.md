# Training-grade data: a training-readiness spec for the harness logs

Research date: 2026-10-16. Target: `claude-harness/` (ontology v0.2.0) and `$HARNESS_DATA`.
This note puts VISION.md goal 1 into practice: "Every record carries its provenance, its rights and consent, a PII status, whether it is human or synthetic, and how its label was made. Client, NDA and third-party content is never exported for training."
It builds on `schema/ontology.yaml`, `schema/event.md`, `schema/STORAGE.md`, `intent/tracing_process_mining.md` (facts, feedback, blobs, hash chain) and `intent/intent_recognition.md` (label provenance, κ evaluation).

Confidence tags: **[S]** read in the source or repo; **[W]** web search snippet only, not verified at the primary source; **[K]** general knowledge; **[?]** my design proposal or judgement.

**Not legal advice.** Section 5 summarizes terms and laws so the gates can be designed. Before training or sharing any model built from this data, a lawyer should confirm the parts marked as risky.

---

## 0. TL;DR (decisions on one screen)

1. **Training readiness is a projection, not an edit.** The log stays append-only. Governance metadata (rights, consent, PII, authorship, label provenance, quality, split) is attached by new `data_label` facts. A deterministic, deny-by-default exporter builds versioned dataset folders from those facts. Each folder has a Croissant 1.1 + RAI manifest, a dataset card, a gate report and an exclusion list. **[?]**
2. **The biggest constraint is legal, not technical: most of the text in these logs is Claude output.** The Anthropic AUP page (dated "Effective November 12, 2026") forbids using "outputs to train an AI model (e.g., 'model scraping' or 'model distillation') without prior authorization from Anthropic". The Consumer Terms (Oct 8, 2025) forbid developing competing products "including to develop or train any artificial intelligence or machine learning algorithms or models". The Commercial Terms (June 17, 2025) §D.4 forbid using the Services "to build a competing product or service, including to train competing AI models". **[S]**
   - This also covers **Claude-made labels**. The intent labels from `label_events.py` come from `claude -p --model haiku` [S], so they are Claude outputs.
   - So every record carries `authorship` per segment.
   - **Training exports by default contain only human-authored text, human or rule labels, and code/test-derived rewards.**
   - Claude outputs may go into **eval** exports, which test a model rather than train one, and into training exports only when `vendor_authorization_ref` is set.
3. **Never export** (hard gates, no override flag; §6):
   - vault data and raw messages
   - client and NDA content
   - annotation-platform tasks and the user's answers to them
   - other people's personal data without a legal basis
   - secrets
   - special-category data
   - holdout or gold eval items into training
   - revoked or erased subjects
   - unscanned text
4. **Five export targets, one shared row envelope** (§4):
   - `sft.jsonl`: OpenAI/TRL conversational `messages` + `tools`
   - `prefs.jsonl`: TRL explicit-prompt `prompt/chosen/rejected`, plus an unpaired KTO view, plus an OpenAI DPO converter
   - `rm.jsonl` and `steps.jsonl`: reward model and process rewards
   - `trajectories/`: **ATIF v1.8** (Harbor RFC-0001), one file per session or intent segment
   - `evals/`: **Harbor task folders** (`instruction.md`, `task.toml`, `tests/` writing `/logs/verifier/reward.{txt,json}`) plus the existing `EvalTask` YAML and rubrics
5. **Quality layer** (§7):
   - exact and MinHash-LSH dedupe (datasketch)
   - 13-gram plus canary-GUID contamination checks against evals
   - Presidio with the Korean recognizers turned on (they are **off by default**) plus a Korean NER model
   - label quality from a blind user relabel (Cohen's κ, Krippendorff's α), with Dawid-Skene aggregation when several labelers disagree
   - a per-row `quality.score` with its components kept
6. **Splits are by group and by time, and frozen.**
   - The group key is the I2 intent (fallback: session), hashed into buckets.
   - Test/val come from a later time window.
   - Eval `holdout` and `gold` items are quarantined from all training exports.
   - A leak check rejects any export where a group or near-duplicate cluster crosses splits.
7. **Urgent fix found while reading the code:** events store only `transcript_path`, which points to `~/.claude/projects/*.jsonl` [S: hooks/_common.py, log_event.py]. Claude Code deletes those transcripts after **30 days by default** (`cleanupPeriodDays`) [S: code.claude.com/docs/en/data-usage].
   - So the agent traces, the part most valuable for trajectories, are disappearing now.
   - Raise `cleanupPeriodDays` and copy transcripts into content-addressed blobs at `SessionEnd` (§9 step 0).

---

## 1. Sources and their state (2026-10-16)

| Source | How read | What matters here |
|---|---|---|
| Anthropic AUP | `curl` of anthropic.com/legal/aup | Page says "Effective November 12, 2026" and links a "Previous Version". Under "Do Not Abuse Our Platform": "Use outputs to train an AI model (e.g., 'model scraping' or 'model distillation') without prior authorization from Anthropic". **[S]** The page is dated 27 days from now. Treat it as the binding direction either way, and re-check on Nov 12. |
| Anthropic Consumer Terms | `curl` (Effective Oct 8, 2025) | Use restriction: "To develop any products or services that compete with our Services, including to develop or train any artificial intelligence or machine learning algorithms or models". Outputs are assigned to the user "Subject to your compliance with our Terms". Anthropic trains on Materials "unless you opt out", and even then on Feedback and safety-flagged items. **[S]** |
| Anthropic Commercial Terms | `curl` (Effective June 17, 2025) | §B: the customer owns Outputs; "Anthropic may not train models on Customer Content from Services." §D.4: no access "to build a competing product or service, including to train competing AI models … except as expressly approved by Anthropic". **[S]** |
| Claude Code data usage | WebFetch code.claude.com/docs/en/data-usage | Consumer training toggle covers Claude Code: 5-year retention if on, 30 days if off. Commercial (Team/Enterprise/API): no training unless opted in (Development Partner Program). `/feedback` transcripts are kept 5 years. **Local transcripts under `~/.claude/projects/` are kept 30 days by default (`cleanupPeriodDays`).** **[S]** |
| Anthropic fine-tuning | platform.claude.com glossary; web search | "The Claude API does not currently offer fine-tuning, but ask your Anthropic contact" **[S]**. Claude 3 Haiku fine-tuning on Bedrock reached end of life on 2026-09-10, per AWS **[W]**. **There is no self-serve Claude fine-tuning target**, so exports aim at open-weight trainers (TRL) and generic formats. |
| OpenAI fine-tuning formats | developers.openai.com **unreachable** (proxy 403); web search snippets | SFT: `{"messages":[…], "tools":[…]}`; assistant messages may carry `weight` 0/1 [K]. DPO: `{"input":{"messages":[…],"tools":[…]}, "preferred_output":[…], "non_preferred_output":[…]}`, text only [W: Azure docs / OpenAI guide snippet]. RFT: per-row tools and graders (`string_check`, `text_similarity`, `score_model`, `python`, `multi`), and graders read `item.*` fields [W/K]. OpenAI Terms also forbid using Output "to develop models that compete" [W]. |
| HF TRL | `git clone` huggingface/trl @ 6d6901c, VERSION 1.17.0.dev0 | `docs/source/dataset_formats.md` [S]. Formats: standard/conversational; tool-calling rows need a `tools` column of JSON schemas. Types: language modeling, prompt-only, prompt-completion, preference (explicit prompt recommended), unpaired preference (`completion` + `label`). Trainer→type table: DPO/CPO/ORPO = preference, KTO = unpaired or preference, RewardTrainer = preference (implicit prompt), GRPO/RLOO/OnlineDPO = prompt-only, SFT = LM or prompt-completion. **Stepwise supervision / PRM is no longer in the main table.** TRL has `experimental/harbor` and `examples/async_grpo_harbor` (GRPO through installed agents incl. `claude-code`). |
| Harbor / ATIF | clone harbor-framework/harbor @ 62db0c1 | `rfcs/0001-trajectory-format.md`: **ATIF v1.8** (April 2026) [S]. Root: `schema_version, session_id, trajectory_id, agent{name,version,model_name,tool_definitions,extra}, steps[], notes, final_metrics, continued_trajectory_ref, subagent_trajectories, extra`. Step: `step_id, timestamp, source(system/user/agent), model_name, reasoning_effort, message, reasoning_content, tool_calls[{tool_call_id,function_name,arguments,extra}], observation{results[{source_call_id,content,subagent_trajectory_ref,extra}]}, metrics{prompt/completion/cached tokens, cost_usd, prompt_token_ids, completion_token_ids, logprobs}, llm_call_count, is_copied_context, extra`. `extra.context_management.boundary="replace"` marks compaction. **ATIF has no outcome or status field** [W: tracelint PR], so rewards go in `extra`. `src/harbor/agents/installed/claude_code.py` already converts Claude Code session JSONL (including `subagents/agent-*.jsonl`) to ATIF (`convert_trajectory`, `_convert_events_to_trajectory`) and back (`atif_to_native_trajectory`). Tasks: `instruction.md`, `task.toml` (`[metadata]`, `[environment]`, `[[steps]]` with agent/verifier timeouts), `environment/`, `solution/solve.sh`, `tests/test.sh`. The verifier writes `/logs/verifier/reward.txt` or `reward.json` (rewardkit). RFC-0002 covers simulated users. |
| PrimeIntellect verifiers | clone @ 1f5ada9 (pins `harbor==0.24.0`) | `docs/env.md`: `Env.run(task, agents)` → `Episode`. Built-ins `AgenticJudgeEnv`, `UserSimEnv`, `BestOfNEnv`. `@vf.reward` / `@vf.metric` on a `Task`, isolated scoring with `stage_verifier` (private tests installed only at scoring). **[S]** |
| Croissant | clone mlcommons/croissant @ ec24358 | `croissant-spec-1.1.md` ("Version 1.1, Published: 2026-01-29") with `dct:conformsTo http://mlcommons.org/croissant/1.1`, `sdLicense`, PROV (`prov:wasDerivedFrom`, `prov:wasGeneratedBy`, `prov:wasAttributedTo`), and split classes `cr:TrainingSplit` etc. (`docs/definitions`). **RAI 1.0** (`croissant_rai.ttl`) properties: `dataCollection, dataCollectionType, dataCollectionRawData, dataCollectionMissingData, dataCollectionTimeframe, dataPreprocessingProtocol, dataManipulationProtocol, dataImputationProtocol, dataAnnotationProtocol, dataAnnotationPlatform, dataAnnotationAnalysis, annotationsPerItem, annotatorDemographics, machineAnnotationTools, dataBiases, dataLimitations, dataUseCases, dataSocialImpact, personalSensitiveInformation, dataReleaseMaintenancePlan`. **[S]** |
| HF dataset cards | clone huggingface/hub-docs @ 2c56ca8 (`datasetcard.md`); template via raw.githubusercontent | YAML: `license, license_name, license_link, annotations_creators, language_creators, source_datasets, task_categories, size_categories, configs, extra_gated_fields/prompt`. Template sections: Description, Sources, Uses (Direct / Out-of-Scope), Structure, Creation (Curation Rationale, Source Data, Annotations, Personal and Sensitive Information), Bias/Risks/Limitations, Citation, Card Authors/Contact. **[S]** |
| Datasheets / Data Cards / Data Statements | from knowledge | Gebru et al., Datasheets for Datasets (2018; CACM 2021): seven question groups (motivation, composition, collection, preprocessing, uses, distribution, maintenance). Pushkarna et al., Data Cards (FAccT 2022): modular "telescope/periscope/microscope" layers. Bender & Friedman, Data Statements (TACL 2018; v3 guide 2021): curation rationale, language variety, speaker and annotator demographics, speech situation, text characteristics. **[K]** |
| Data Provenance Initiative | web search | Longpre et al., audit of 1,858 fine-tuning datasets: more than 70% of licences on popular hubs were "unspecified", and many were wrong. Published in Nature Machine Intelligence 2024. Provides the Data Provenance Explorer. No 2026 update found. **[W]** Lesson: record licence **and** the terms of the model that generated the text, per record. |
| Presidio | clone microsoft/presidio @ 2523c7b, analyzer 2.2.364 | `predefined_recognizers/country_specific/korea/`: `KR_RRN, KR_FRN, KR_BRN, KR_DRIVER_LICENSE, KR_PASSPORT`, language `ko`. **All are `enabled: false` in `conf/default_recognizers.yaml`, and `supported_languages` defaults to `[en]`.** **[S]** Korean names and addresses need a `ko` NLP engine (e.g. spaCy `ko_core_news_lg` or a Stanza/transformers NER) [K]. |
| datasketch | clone ekzhu/datasketch @ c7eaaee (MIT) | `MinHashLSH(threshold=0.9, num_perm=128, …)` defaults **[S]**. |
| Korean PIPA | Korean press via web search; law.go.kr and pipc.go.kr **unreachable** | Art. 28-2: pseudonymized data may be processed without consent for statistics, scientific research and public-interest archiving [W/K]. **New AI-development special provision**: lawfully collected personal data may be used for AI development without consent where pseudonymized or anonymized data is not enough and there is public or social need, after PIPC deliberation and with stronger safeguards. Reported passed 2026-08-20, promulgated 2026-09-08 (Act No. 21910), **effective 2027-03-09** [W: lawtimes.co.kr, newspim, etnews]. Article numbers are not confirmed. |
| GDPR / EU AI Act | knowledge + web search | GDPR Art. 5 (purpose limitation, minimization), Art. 6 (lawful basis), Art. 9 (special categories), Art. 15/17/21 (access, erasure, objection) [K]. EDPB Opinion 28/2024: a model trained on personal data is not automatically anonymous [K]. AI Act Art. 53(1)(d): the GPAI training-data summary template applies from 2025-08-02. A fine-tuner becomes a "provider" only above roughly one-third of the original training compute [W]. Not relevant for personal fine-tunes. |
| Rubric rewards, learning from edits | web search | Rubrics as Rewards (Gunjal et al., ICLR 2026, arXiv 2507.17746): instance rubrics as RL reward beat Likert judges. Checklists / RLCF (Viswanathan et al., NeurIPS 2025): checklist scores → DPO pairs. OpenRubrics and pairwise rubric work (2026). PRELUDE/CIPHER (Gao et al., NeurIPS 2024): learn latent preference from user edits; edit cost as the metric. **[W]** |
| Contamination | web search | BIG-bench canary GUID convention; 8–13-gram overlap checks; clean-mirror re-tests. No 2026 standard threshold found. **[W/K]** |

**Unreachable** (proxy 403 or DNS): developers.openai.com, platform.openai.com, privacy.claude.com, iapp.org, law.go.kr, pipc.go.kr, gdpr-info.eu, lexology.com, pebblous.ai. OpenAI formats are therefore from snippets and knowledge. Check them before building the OpenAI converters.

---

## 2. What the harness has, mapped to training uses

| Harness record (ontology v0.2) | Who authored the text | Best training/eval use | Default export status [?] |
|---|---|---|---|
| `Event type=prompt` (`actor: me`) | **the user** | intent classifier input; user-simulator seeds; prompt-only RL tasks | trainable once PII is scrubbed and no client text is inside |
| `label` events (from `label_events.py`) | **Claude (haiku)** | weak labels and features; *not* training targets | eval/analysis only, unless authorized |
| User gold labels (intent_recognition §7.1 blind relabel) | **the user** | intent-classifier targets, judge calibration, golden set | trainable; gold labels → `gold` split |
| `correction` events (`agent_did`, `my_correction`, `my_reasoning`) | agent_did: Claude; my_correction and my_reasoning: **the user** | preference pairs; rubric criteria; reward-model data; critique SFT (user-written reasoning) | pair uses Claude text as `rejected` → restricted; `my_correction`/`my_reasoning` alone are trainable |
| `StylePair` (draft → final) | draft: usually Claude; final: user-edited Claude text (**mixed**) | DPO/KTO pairs; edit-cost reward (PRELUDE); style guides | restricted (both sides contain Claude output); eval and few-shot use allowed |
| `StyleSample` (vault) | the user, inside third-party threads | style SFT on the user's own sentences | vault → **never** leaves; a future "own sentences only" extractor needs per-item review |
| `verification` events, `Evaluation`, `EvalRun` | judge = Claude; checks = code | rewards (code checks are clean); judge scores are restricted | code-check rewards trainable; judge scores eval-only |
| `EvalTask` + `Rubric` | the user | Harbor tasks, RL environments, rubric rewards | eval export; never in train |
| `Decision`, `Mishap`, `Lesson`, `SessionNote` | mixed (skills draft, user approves) | critique/reflection data; eval cases from mishaps | authorship per field; mostly restricted |
| Agent traces (Claude Code transcripts, subagents, tool calls) | Claude, with the user's prompts in between | trajectories (SFT/RL), process mining, replayable tasks | restricted for training; eval and replay allowed; **at risk of 30-day deletion** |
| Tool outputs (file reads, web pages, command output) | third parties / environment | observations in trajectories | carry the *source's* rights; web content often unlicensed → strip or keep in eval-only exports |
| `PermissionDenied` / Esc interrupts / reverts (tracing note §4.6) | user behaviour about Claude actions | unpaired negatives (KTO), process labels | the label is the user's; the action text is Claude's → restricted pair |
| `Application`, `JobLead`, `Contact`, ledger | user + third parties | none for training | **never** (third-party personal data, finance) |
| `annotation/*` projects | platform tasks + the user's paid answers | none | **never** (platform-owned, NDA; often other labs' training data) |

The practical point: a **clean, unrestricted training corpus exists today** (user prompts, user corrections and reasoning, user gold labels, rubrics, eval tasks, code-check rewards). It is enough for an intent classifier, a correction detector, a small reward model on user-written critiques, and user-simulator seeds. Everything that pairs or trains on Claude text needs `vendor_authorization_ref`. Without it, that material is still usable as **evals, rubrics, few-shot memory and RL environments** (where the policy generates its own outputs). **[?]**

---

## 3. The per-record governance envelope (`dataprops`)

### 3.1 Where it lives
- A new fact or event kind, **`data_label`**, targets a record id (`evt_…`, `sp_…`, `fb_…`, a span id, an EvalTask id) through `labels_for`. It works like the existing `label` events: latest non-superseded wins, higher authority wins, and the original line is never edited.
- Authority order: `me` > `script:gate` (deterministic scans) > `agent:*`.
- **Where writers can know the values at write time, they fill them in directly:**
  - hooks know `authorship` and `rights.source_kind` from cwd/scope
  - `style_pairs.py` knows `origin`
- The exporter **joins** the record with its `dataprops`. Unknown values default to the most restrictive setting.

### 3.2 Schema (JSON Schema 2020-12, field level)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "harness://schema/dataprops/0.1.0",
  "type": "object",
  "required": ["target", "rights", "authorship", "consent", "pii", "synthetic", "split"],
  "properties": {
    "target": {"type": "string", "description": "record id (evt_, sp_, fb_, span id, eval task id)"},
    "content_hash": {"type": "string", "pattern": "^(sha256|hmac-sha256):[0-9a-f]{64}$", "description": "hash of the exact content the props describe (re-scan if it changes)"},

    "rights": {
      "type": "object", "required": ["source_kind", "confidentiality"],
      "properties": {
        "source_kind": {"enum": ["self", "employer", "client", "platform", "third-party", "public-licensed", "public-unlicensed", "unknown"]},
        "owner": {"type": "string", "description": "me | org-… | client-… | plat-… | url"},
        "license": {"type": "string", "description": "SPDX id (CC-BY-4.0, MIT…), 'proprietary-self', 'proprietary-employer', or 'none'"},
        "confidentiality": {"enum": ["public", "internal", "confidential", "nda"]},
        "nda_ref": {"type": ["string", "null"], "description": "pointer to the contract or ToS clause"},
        "client": {"type": ["string", "null"], "pattern": "^client-"},
        "written_permission_ref": {"type": ["string", "null"], "description": "pointer to the client/employer email or contract allowing training use"},
        "vendor_authorization_ref": {"type": ["string", "null"], "description": "pointer to written authorization from the model vendor (e.g., Anthropic) to train on its outputs"}
      }
    },

    "authorship": {
      "type": "array", "minItems": 1,
      "description": "one entry per segment/field of the record; the exporter checks each field it uses",
      "items": {
        "type": "object", "required": ["field", "author"],
        "properties": {
          "field": {"type": "string", "description": "content | draft | final | agent_did | my_correction | labels | step[3].message …"},
          "author": {"enum": ["human:me", "human:other", "model", "tool", "environment", "mixed"]},
          "model": {"type": ["string", "null"], "description": "vendor/model id, e.g. anthropic/claude-haiku-…"},
          "model_terms": {"enum": ["anthropic-consumer", "anthropic-commercial", "openai", "google", "open-weights", "none", null]},
          "human_edit_ratio": {"type": ["number", "null"], "minimum": 0, "maximum": 1, "description": "for mixed: character-level share changed by the human"}
        }
      }
    },

    "consent": {
      "type": "object", "required": ["subjects", "basis", "scopes"],
      "properties": {
        "subjects": {"enum": ["self-only", "includes-others", "unknown"]},
        "basis": {"enum": ["own-data", "consent", "contract", "legitimate-interest", "pseudonymized-research", "pipa-ai-special", "none"]},
        "consent_ref": {"type": ["string", "null"]},
        "scopes": {"type": "array", "items": {"enum": ["analysis", "eval", "sft", "prefs", "reward-model", "rl-env", "share-internal", "share-external", "publish"]}},
        "revoked_at": {"type": ["string", "null"], "format": "date-time"},
        "dsr_tombstone": {"type": ["string", "null"], "description": "id of an erasure/objection request that covers this record"}
      }
    },

    "pii": {
      "type": "object", "required": ["status"],
      "properties": {
        "status": {"enum": ["unscanned", "clean", "redacted", "pseudonymized", "contains-pii", "special-category"]},
        "scanner": {"type": "string", "description": "e.g. presidio-analyzer@2.2.364+kr+ko_core_news_lg; gitleaks@x.y"},
        "entities": {"type": "object", "additionalProperties": {"type": "integer"}, "description": "{PERSON: 2, EMAIL_ADDRESS: 1, KR_RRN: 0}"},
        "secrets": {"enum": ["unscanned", "clean", "found-removed", "found"]},
        "third_party_persons": {"type": "boolean"},
        "pseudonym_key_id": {"type": ["string", "null"], "description": "HMAC key id; the key itself stays in msg-vault (PIPA Art. 28-4: keep the additional information separately)"},
        "scanned_at": {"type": "string", "format": "date-time"}
      }
    },

    "synthetic": {
      "type": "object", "required": ["origin"],
      "properties": {
        "origin": {"enum": ["human-authored", "human-edited-model", "model-generated", "model-generated-human-verified", "simulated-user", "programmatic", "mixed"]},
        "generator": {"type": ["string", "null"], "description": "model + prompt_version, or script@sha"},
        "seed": {"type": ["integer", "null"]}
      }
    },

    "label_provenance": {
      "type": "array",
      "items": {
        "type": "object", "required": ["label", "source"],
        "properties": {
          "label": {"type": "string", "description": "which label: intent.speech_act, is_correction, verdict, rubric.correctness …"},
          "source": {"enum": ["user", "rule", "model", "code-check", "platform", "aggregate"]},
          "annotator": {"type": "string", "description": "me | script:… | agent:… | dawid-skene(v)"},
          "model": {"type": ["string", "null"]}, "prompt_version": {"type": ["string", "null"]},
          "blind": {"type": "boolean", "description": "user labeled without seeing the model label"},
          "k_samples": {"type": ["integer", "null"]}, "agreement": {"type": ["number", "null"]},
          "adjudicated": {"type": "boolean"},
          "posterior": {"type": ["number", "null"], "description": "Dawid-Skene / calibrated confidence of the final label"}
        }
      }
    },

    "quality": {
      "type": "object",
      "properties": {
        "score": {"type": "number", "minimum": 0, "maximum": 1},
        "components": {"type": "object", "description": "{label_conf, verifier, completeness, length_ok, lang_ok, dup_penalty, toxicity}"},
        "dup_cluster": {"type": ["string", "null"], "description": "MinHash cluster id; one representative per cluster per split"},
        "contamination": {"enum": ["unchecked", "clean", "overlaps-eval", "canary-hit"]},
        "is_gold": {"type": "boolean"},
        "verdict": {"enum": ["pass", "fail", "needs-human", null]}
      }
    },

    "split": {
      "type": "object", "required": ["name"],
      "properties": {
        "name": {"enum": ["unassigned", "train", "val", "test", "gold", "holdout", "quarantine"]},
        "group_key": {"type": "string", "description": "int_… (I2 task) > session_id > project scope"},
        "bucket": {"type": "integer", "minimum": 0, "maximum": 99},
        "time_window": {"type": "string", "description": "e.g. 2026Q4"},
        "frozen": {"type": "boolean"},
        "assigned_by": {"type": "string"}, "assigned_at": {"type": "string", "format": "date-time"}
      }
    },

    "lineage": {
      "type": "object",
      "properties": {
        "derived_from": {"type": "array", "items": {"type": "string"}},
        "transforms": {"type": "array", "items": {"type": "string"}, "description": "pii_scrub@v, dedupe@v, atif_convert@harbor-sha"},
        "exports": {"type": "array", "items": {"type": "string"}, "description": "dataset@version list this record went into (needed for erasure follow-up)"}
      }
    },

    "retention": {"type": "object", "properties": {"delete_after": {"type": ["string", "null"], "format": "date"}, "reason": {"type": "string"}}},

    "language": {"enum": ["ko", "en", "mixed"]},
    "area": {"type": "string"}, "scope": {"type": "string"}, "register": {"type": "string"}
  }
}
```

### 3.3 Defaults (the "unknown means no" rule) [?]

| Field | Default when no `data_label` exists | Who usually sets it |
|---|---|---|
| `rights.source_kind` | `self` for `global`, `code`, `research`, `personal` scopes; **`client`** for `translation/*`; **`platform`** for `annotation/*`; `employer` for a scope tagged with an employer; else `unknown` | hook from `scope`/`scope_hint`; project `CLAUDE.md` `client:` field |
| `confidentiality` | `nda` if `source_kind ∈ {client, platform, employer}`, else `internal` | same |
| `authorship` | `prompt` by `actor: me` → `human:me`; agent output, `label`, `verification` judge → `model`; tool results → `tool`/`environment`; StylePair `draft` → `model`, `final` → `mixed` | writers (known at write time) |
| `consent.subjects` | `unknown` until a PII scan has run; `self-only` if the scan finds no third-party persons | `pii_scan.py` |
| `consent.scopes` | `[analysis, eval]` for self data; `[analysis]` for anything else | the user, through a `/data-consent` command |
| `pii.status` | `unscanned` (blocks all exports) | `pii_scan.py` |
| `synthetic.origin` | from authorship (`human-authored`, `model-generated`, `human-edited-model`) | writers |
| `split.name` | `unassigned` (blocks training exports; assigned by `split_assign.py`) | script |

---

## 4. Export pipelines

### 4.1 Common shape
```
$HARNESS_DATA/exports/<dataset>/<semver>/      # dataset ∈ intent-cls | corrections | prefs | sft | trajectories | evals
  manifest.json          # Croissant 1.1 + RAI 1.0 (§8.2), sha256 of every file
  README.md              # dataset card (§8.1)
  data/<split>.jsonl     # or trajectories/<split>/<id>.json, or tasks/<id>/
  gate_report.json       # per gate: checked, passed, excluded count; exporter git sha; policy hash
  excluded.jsonl         # {"id","gate","reason"} only, never content
  lineage.jsonl          # {"row_id","source_ids","content_hash"}
```
- **Exporter rules** [?]:
  - pure function of (log facts up to a cut-off `recorded_at`, policy file, exporter sha); the same inputs give a byte-identical output
  - `--dry-run` prints the gate report only
  - the export folder is in `harness-data`, never in a public place
  - a "publish" step is a separate, manual command that re-runs every gate with `scope=share-external`
- **Common row envelope.** Every JSONL row has the trainer fields at the top level (so TRL/OpenAI loaders read them directly) plus one `meta` object:

```json
"meta": {
  "row_id": "intent-cls/1.0.0/train/000123",
  "source_ids": ["evt_20261016_143205_ab12"],
  "split": "train", "group_key": "int_9f3k2m1q0a",
  "language": "ko", "area": "code",
  "authorship": {"prompt": "human:me", "label": "human:me"},
  "synthetic": "human-authored",
  "label_source": "user", "label_blind": true,
  "quality": 0.91, "pii": "redacted", "license": "proprietary-self",
  "consent_scopes": ["sft", "eval"]
}
```
Before training, drop `meta` or move it to a side file (`remove_unused_columns`).

### 4.2 `intent-cls` (classification; the cleanest set today)
- **Row:** `{"text": "<redacted prompt>", "prev_agent_summary": null, "labels": {"speech_act": "constrain", "ado": "doing", "task_type": "code.fix", "feedback": "aware_with_fix"}, "meta": {…}}`.
- **Targets:** user gold labels only (`label_source: user`). Rule labels may be included with `label_source: rule`, a lower weight and `posterior` from Dawid-Skene.
- **Model labels:** go to a separate `features_model_labels` column, *eval-only*, or are dropped by default (they are Claude outputs).
- `prev_agent_summary` would be Claude text. Leave it null, or fill it with a user-written or rule summary.

### 4.3 `sft.jsonl`
- **Format:** conversational, matching OpenAI SFT and TRL `SFTTrainer` (language-modeling or prompt-completion type). Example row: `{"messages":[{"role":"system","content":"…"},{"role":"user","content":"…"},{"role":"assistant","content":"…","weight":1}],"tools":[…JSON schemas…],"meta":{…}}` **[K/S]**.
  - The OpenAI-style `weight: 0` marks assistant turns that should not be learned.
  - The TRL equivalent is `assistant_only_loss` / `completion_only_loss` with a prompt-completion split.
- **Gate:** every assistant message with `weight: 1` must have `authorship ∈ {human:me}`, unless `vendor_authorization_ref` is set. Concretely, today that allows:
  1. **Critique SFT:** user prompt + Claude output as *context* (weight 0) → the user's `my_correction`/`my_reasoning` as the target. This is gray: Claude text as model *input* is still "using outputs to train" in a broad reading. **Default: off**, with a policy flag `allow_model_text_as_context` and a note in the card. [?]
  2. **User-voice SFT:** pairs where both prompt and answer are by the user (e.g. answers the user wrote in an `interview` skill, or user-written final texts that the user wrote from scratch, `human_edit_ratio ≥ 0.9` *and* `origin: human-authored`).
- Translation, email and annotation finals are **client/platform content**, so they are blocked by the rights gate whoever wrote them.

### 4.4 `prefs.jsonl` (DPO / ORPO / CPO; reward model; KTO)
- **Primary format:** TRL preference, explicit prompt, conversational: `{"prompt":[…messages…], "chosen":[{"role":"assistant","content":"…"}], "rejected":[{"role":"assistant","content":"…"}], "meta":{…, "pair_source":"correction|style_pair|verifier_retry|best_of_n|permission_denied", "strength":"strong|weak", "annotator_kind":"HUMAN|CODE|LLM", "same_prompt": true, "tie": false}}` **[S: TRL dataset_formats.md]**.
- **Derived views:**
  - `kto.jsonl` (unpaired): `{"prompt", "completion", "label": true|false}`. Use it for one-sided signals: a PermissionDenied tool call is `label:false`; an accepted turn with no correction in the next prompt is a weak `true`.
  - `openai_dpo.jsonl`: `{"input":{"messages":[…],"tools":[…]}, "preferred_output":[…], "non_preferred_output":[…]}` [W]. Re-check this shape against the live OpenAI page before use.
  - `rm.jsonl`: implicit-prompt preference for `RewardTrainer` (prompt folded into chosen/rejected) **[S]**.
- **Pair sources and their quality** [?]:

| Source | chosen | rejected | Strength | Notes |
|---|---|---|---|---|
| `correction` event | `my_correction` (human) | `agent_did` (model) | strong, HUMAN | `my_reasoning` → rubric criterion (§10.3) |
| `StylePair` | `final` (mixed) | `draft` (model) | strong if `edited` and the edit distance is above a threshold; weak for cosmetic edits | keep `edit_distance` and the PRELUDE "edit cost" in meta |
| verifier retry | passing attempt | failing attempt, same prompt | strong, CODE (if checks) / LLM (if judge) | only with same prompt and same tools |
| best-of-N (`BestOfNEnv`, eval runs) | top-scored | bottom-scored | weak to strong by margin | needs margin ≥ τ; record judge ≠ producer |
| PermissionDenied / revert | — | the action | KTO negative only | no chosen side |

- **Rights:** every row contains model text on at least one side, so the whole `prefs` export is **restricted**. Exception: the rare pairs where both sides are human (two user rewrites).
  - Without `vendor_authorization_ref`, build it only as an **eval set for judges and reward models**: "does the judge prefer the user's version?"
  - That is allowed, and it is useful for calibrating the harness's own LLM judges. [?]

### 4.5 Process / step rewards (`steps.jsonl`)
- TRL's main docs no longer list a stepwise-supervision trainer **[S: 1.17.0.dev0]**, so use a self-describing format [?]: `{"prompt":…, "completions":["step 1 …","step 2 …"], "labels":[true,false], "meta":{…, "label_source":"user|code-check|model", "first_error_step":2}}`.
- **Sources:**
  - the tool span a `feedback` (correction, human_edit, permission reject) targets → `false` for that step
  - steps before it that a later verification pass covers → `true`
  - code checks per step (Harbor multi-step tasks have a verifier per step **[S]**)
- Same restriction as prefs (steps are Claude actions).

### 4.6 `trajectories/` (ATIF v1.8)
- **Converter:** reuse Harbor's `ClaudeCode.convert_trajectory` / `_convert_events_to_trajectory` (it reads `<session>.jsonl` plus `subagents/agent-*.jsonl`) **[S]**, through `python3 -I` on a pinned Harbor version. Don't hand-write a new parser.
- **One file per session** (`trajectory_id = sha256("cc-session:"+session_id)[:32]`, the same derivation as the tracing note's trace_id):
  - `subagent_trajectories` embedded
  - compaction marked with `extra.context_management.boundary = "replace"`
  - `/clear` continuations linked with `continued_trajectory_ref`
- **Optional segment view:** one trajectory per I2 intent (slice by `harness.intent.id`, set `is_copied_context` on copied steps).
- **Harness extensions go in `extra` only** (the spec reserves `extra` at root, step, tool-call and observation level **[S]**):
  - root `extra.harness`: `{intent_ids, scope, dataprops_digest, outcome, reward: {value, source, verifier}, feedback_ids, split, rights_summary}`
  - step `extra.harness`: `{span_id, intent_id, binding, feedback: [{name, label, score, annotator_kind}]}`
  - ATIF has no outcome field, so `extra.harness.outcome` and `final_metrics.extra.reward` carry it.
- **Token ids and logprobs:** Claude Code does not expose them, so `prompt_token_ids` / `completion_token_ids` / `logprobs` stay empty. These trajectories are **off-policy demonstrations**. For on-policy RL, use them as *tasks* (§10), not as rollouts.
- **Redaction:**
  - Tool observations from `client`/`platform` scopes are replaced by `"[redacted:<rights>:<sha256>]"`.
  - Web page content is stored as a URL plus hash, not the text.
  - Any trajectory with a blocked segment the task cannot do without goes to `excluded.jsonl`.
- **Rights:** restricted for training (Claude actions). Eval and replay use is fine.

### 4.7 `evals/` (Harbor tasks + existing EvalTask)
- **Built from `EvalTask` YAML** (only the user edits these; `guard_protected.py` protects them):
```
evals/<area>-NNN/
  instruction.md         # from EvalTask.input (redacted), plus the user's original prompt if self-owned
  task.toml              # [metadata] author_name="me", difficulty (routine|hard|known-failure), category=<area>, tags; [environment]; [verifier] timeout
  environment/Dockerfile # pinned image; fixtures copied in by sha256; repo at commit
  tests/test.sh          # runs expected_checks; writes /logs/verifier/reward.json {"correctness":…, "checks_passed":…}
  tests/rubric.json      # rubric criteria (+ task-specific) for an LLM judge or rewardkit
  solution/solve.sh      # reference_output when one exists (keeps the task solvable = validity check)
  CANARY                 # one canary GUID per eval set, also embedded in instruction.md as a comment
```
- **Split handling:**
  - `split: holdout` tasks never go to any optimizer or training export.
  - `split: train` tasks may serve as RL environments (§10).
- Keep `eval_set_sha256` (evals/README) as the Harbor dataset version.

---

## 5. Legal and terms: what it means for the gates

### 5.1 Model-vendor terms (the binding one for this data)

| Rule | Text (verbatim where read) | Consequence for gates [?] |
|---|---|---|
| Anthropic AUP (page dated Nov 12, 2026) | "Use outputs to train an AI model (e.g., 'model scraping' or 'model distillation') without prior authorization from Anthropic" **[S]** | Applies to *any* AI model, not only competing ones, and to all plans. **Claude outputs (text, labels, judge scores, tool-call choices) cannot be trained on without authorization.** Gate G7. |
| Anthropic Consumer Terms §3 | "To develop any products or services that compete with our Services, including to develop or train any artificial intelligence or machine learning algorithms or models" **[S]** | Applies when the harness runs under Pro/Max. Same direction as the AUP. |
| Anthropic Commercial Terms §D.4 | "access the Services to build a competing product or service, including to train competing AI models … except as expressly approved by Anthropic" **[S]** | Applies to API/Team/Enterprise use (e.g. company work). Plus the AUP. |
| Output ownership | Consumer: "we assign to you all of our right, title, and interest—if any—in Outputs" (subject to compliance). Commercial: "Customer … owns its Outputs" **[S]** | Ownership does not cancel the use restriction. Keep both facts on the card. |
| Anthropic training on *your* data | Consumer: trained on unless opted out; 5-year retention if on. Commercial: "Anthropic may not train models on Customer Content" **[S]** | Separate question (vendor → you). Record the account type per session (`model_terms`) because it changes this and the retention. Client/NDA work should run under commercial terms, or with the consumer training toggle **off**. |
| OpenAI Terms | do not use Output "to develop models that compete with OpenAI" [W] | The same gate covers any vendor (`model_terms`). |

- **What stays allowed** [?]:
  1. Training on human-authored text and human/rule/code labels.
  2. Evals, benchmarks and judge calibration that *use* model outputs as test material (no model is trained on them).
  3. RL where the *policy's own* rollouts are rewarded by human-written rubrics or code checks; logged Claude traces define tasks, not targets.
  4. Prompt optimization (GEPA/ACE) and few-shot memory, which train no model.
  5. Anything with written vendor authorization, recorded in `vendor_authorization_ref`.
- Using Claude *as the judge* inside your own RL loop is itself "using outputs to train" in a broad reading. Prefer code checks and human rubrics as the reward, and ask Anthropic if a Claude judge is needed. [?]

### 5.2 Client, employer, platform and third-party content
- **Translation clients:** source texts, drafts and finals are client confidential (`docs/LOCAL_ONLY.md` already forbids cloud tools). Training a model on them, even locally, is a new purpose the contract usually does not cover. Gate G2, overridable only by `written_permission_ref`.
- **Annotation / AI-training platforms** (`platform_kind: annotation | ai-training-marketplace | ai-data-vendor`):
  - Task content and the user's answers are typically work-for-hire owned by the platform or its lab customer, under NDA, and often forbidden to copy off-platform at all (LOCAL_ONLY.md notes this).
  - **Never exportable; no override.**
  - The harness should not even keep task text in harness-data. Keep only pointers.
- **Employer/company work:** IP and confidentiality belong to the employer. Exportable only with `written_permission_ref`, and only into datasets that stay inside the company.
- **Tool observations:** web pages, docs and repos carry their own licences (Data Provenance lesson: licences are often missing or wrong [W]). Default: URL + hash only. Text from permissively licensed sources may be kept, with the SPDX id.

### 5.3 Personal data
- **Korean PIPA:**
  - Names, emails, phone numbers and IDs of recruiters, clients and colleagues inside prompts, tool outputs and messages are personal information of third parties [K].
  - Without consent, the realistic route is **pseudonymization for scientific research (Art. 28-2)**, which needs:
    - the additional information (the HMAC key) kept separately (Art. 28-4)
    - no re-identification
    - records of processing [W/K]
  - The new AI-development special provision (effective 2027-03-09 per press) needs PIPC deliberation and public need. It is not a route for a personal fine-tune [W].
  - Unique identifiers (RRN, passport, driver licence, foreigner registration) and sensitive information (health, beliefs etc.) have stricter rules → gates G5/G6. **[K]**
- **GDPR** (EU clients or contacts):
  - lawful basis per purpose (Art. 6); purpose limitation (Art. 5(1)(b))
  - special categories (Art. 9)
  - rights to access, erasure and objection (Art. 15/17/21)
  - EDPB Opinion 28/2024: a model trained on personal data is not automatically anonymous, so rights can reach the model.
  - **Implementation:**
    - a `dsr` fact (`{subject_hmac, right, received_at, scope}`) tombstones every record whose PII index matches
    - the exporter excludes them
    - `lineage.exports` lists the dataset versions that already contained them, so you know what to rebuild or retrain [?]
- **The user's own data:** consent is implicit for analysis, but scopes are still explicit (`consent.scopes`), so "share-external" or "publish" is never assumed.

### 5.4 EU AI Act
Only relevant if a model trained on this data is put on the EU market as a GPAI model, or if a high-risk system is built. A personal or company-internal fine-tune is far below the "one-third of original compute" modifier threshold [W]. Keep the dataset card anyway: it is the same information the training-data summary template asks for.

---

## 6. Gates

### 6.1 Hard gates (never exported; no CLI flag can override; the exporter exits non-zero if a gate's input is missing)

| # | Gate | Rule |
|---|---|---|
| G1 | Vault | any record whose store `privacy: vault` (msg-vault: Message, Thread, Attachment, StyleSample, SyncCursor), and any content pulled from it, including HMAC'd copies of bodies |
| G2 | Client / NDA | `rights.source_kind ∈ {client, employer}` or `confidentiality = nda` **without** `written_permission_ref`; with permission, only into `share-internal` datasets |
| G3 | Annotation platforms | `source_kind = platform` or scope `annotation/*`: always blocked, permission or not (task content and answers) |
| G4 | Secrets | `pii.secrets ∈ {unscanned, found}`; any match of gitleaks/trufflehog rules or the harness's token patterns after redaction |
| G5 | Unscanned or third-party PII | `pii.status ∈ {unscanned, contains-pii}`, or `third_party_persons = true` and `basis ∉ {consent, pseudonymized-research}` |
| G6 | Special-category / unique identifiers | `pii.status = special-category`, or any `KR_RRN`/`KR_FRN`/`KR_PASSPORT`/`KR_DRIVER_LICENSE`/`US_SSN`/credit-card hit (even redacted rows are dropped, to be safe) |
| G7 | Vendor output in training targets | for training datasets (sft, prefs, rm, steps, trajectories-for-training, intent-cls targets): any used field with `author ∈ {model, mixed}` and no `vendor_authorization_ref` |
| G8 | Eval contamination | rows whose source id, group key or MinHash cluster appears in any `holdout`/`gold`/`test` item; any canary hit; 13-gram overlap with eval inputs above τ |
| G9 | Revoked / erased | `consent.revoked_at` set, `dsr_tombstone` set, or `retention.delete_after` passed |
| G10 | Scope not consented | target dataset purpose ∉ `consent.scopes` |
| G11 | Finance and job-search identities | LedgerEntry, Invoice, Application, JobLead, Contact, Organization, Account: never in any training export (derived counts only, in reports) |
| G12 | Integrity | a source fact fails hash-chain verification (`verify_chain.py`), or its blob is missing (redacted) |

### 6.2 Soft gates (default on; can be relaxed per dataset in `policy.yaml`, and the change is recorded in the card)
- `quality.score < 0.5` → excluded from train (kept for analysis).
- `label_source = model` as a target → excluded unless `allow_model_labels` (also needs G7 clearance).
- `language` imbalance: report ko/en/mixed shares; warn if a split differs from the overall share by more than 10 points.
- Rows whose `pii.status = redacted` but where more than 20% of tokens are redaction placeholders → excluded (not useful).
- `allow_model_text_as_context` (Claude text as non-target context) → default **off** (§4.3).

### 6.3 Gate report
`gate_report.json`: `{"policy_sha":…, "exporter_sha":…, "cutoff":…, "gates":{"G1":{"checked":N,"excluded":k}, …}, "splits":{…counts…}, "leak_check":"pass", "contamination_check":"pass", "pii_scanner":"presidio-analyzer@2.2.364 +KrRrn,KrFrn,KrBrn,KrPassport,KrDriverLicense; ko NER=…"}`.

---

## 7. Quality pipeline

### 7.1 PII and secrets (`scripts/pii_scan.py`, local only)
- **Presidio analyzer 2.2.364** with:
  - `supported_languages: [en, ko]`
  - the five Korean recognizers set to `enabled: true` in a local copy of `default_recognizers.yaml`
  - `PhoneRecognizer` with `supported_regions` including `KR` (010-xxxx-xxxx forms)
  - a `ko` spaCy/transformers NER for PERSON/LOCATION/ORG **[S/K]**
- Add custom recognizers for the user's world:
  - client names from `clients.jsonl` / project CLAUDE.md
  - platform worker ids
  - Korean bank account formats
  - KakaoTalk/Viber handles
- **Operators:**
  - `replace` with typed placeholders for exports (`<PERSON_1>` stable within one row)
  - `hash` with the vault HMAC key for pseudonymized research sets (consistent across rows; key id in `pii.pseudonym_key_id`)
- **Secrets:** gitleaks (or trufflehog) over every text field, plus the harness's own token regexes.
- Run the scan at **export time** and also **at write time for blobs**, so harness-data does not accumulate secrets.
- Model-based PII detection (a local model) can be added as a second pass. Never use a cloud API (LOCAL_ONLY.md).

### 7.2 Dedupe
- **Exact dedupe:** sha256 of normalized text (NFKC, whitespace-collapsed, placeholders normalized).
- **Near-dupe:**
  - datasketch `MinHash` (num_perm 128) over **character 5-gram shingles** (work for Hangul and code) or word 3-grams for English
  - `MinHashLSH(threshold=0.8)` (library default 0.9 is strict for re-asked prompts) [S/?]
- **Cluster handling:** one cluster id per near-dup group. A cluster lives in exactly one split. In train, keep the highest-quality representative or down-weight (`1/size`).
- **Agent-trace specific:** dedupe trajectories by `(intent statement hash, tool-call sequence)`, so repeated retries don't dominate.

### 7.3 Contamination
- Every eval file carries a canary GUID (BIG-bench convention) [W/K]. The exporter refuses train rows containing any canary.
- 13-gram overlap (8-gram for Korean character n-grams) between train rows and eval `input`/`reference_output`. Any hit above 1 n-gram match per 200 tokens → G8.
- Overlap by id/group/cluster with eval `source_event` (EvalTasks are built from log events [S: evals/README]), so the very events an eval task was built from never enter train.
- When the eval set changes (`eval_set_sha256`), re-run contamination on all train exports.

### 7.4 Label quality
- **Gold:** the blind user relabel from intent_recognition §7.1 (monthly 60 prompts + 60 actions, stratified, blind first, then adjust).
  - The adjusted value is gold.
  - The blind value measures agreement.
  - 15 test-retest items give the ceiling **[S: intent_recognition.md]**.
- **Metrics:**
  - Cohen's κ per dimension (model vs user, rule vs user)
  - Krippendorff's α (MASI) for multi-label
  - precision at the auto-accept threshold; ECE calibration
  - bilingual parity (κ gap ko vs en ≤ 0.05)
- **Aggregation:** with several noisy labelers (rule, haiku k-samples, sonnet, later a local model), fit Dawid-Skene (e.g. Toloka `crowd-kit` `DawidSkene`, or a 40-line EM) on the items that have user gold for initialization. Write the posterior into `label_provenance[].posterior`, use it as `quality.components.label_conf`, and as a sample weight [K].
- **Golden set:**
  - user-labeled, frozen, hash-pinned
  - `split: gold`
  - used to accept or reject any labeler or judge change (like `eval_gate.py`)
  - never in train

### 7.5 Quality score [?]
`score = label_conf^0.4 × verifier^0.2 × completeness^0.2 × (1 − dup_penalty)^0.1 × lang_ok^0.1`, where:
- `verifier` = 1 for a code-check pass, 0.7 for an LLM-judge pass, 0.3 for no verdict, 0 for a fail (for chosen sides)
- `completeness` = required fields present (`intent`, `situation`, `meta` for decision/correction/mishap/session_note, as the ontology requires)
- `lang_ok` = the language detector agrees with `language`

Keep `components`, so trainers can re-weight without re-exporting.

---

## 8. Documentation: dataset card and Croissant manifest

### 8.1 Dataset card template (`templates/dataset_card.md`)
It merges the HF card sections **[S]**, the Datasheets question groups **[K]**, Data Statements fields **[K]** and the Croissant-RAI keys **[S]**, so the manifest can be generated from the same answers.

```markdown
---
pretty_name: "<harness> <dataset> v<semver>"
license: other
license_name: proprietary-self            # or the SPDX id when every row allows it
license_link: LICENSE.md
annotations_creators: [expert-generated]  # the user; add machine-generated only when model labels are included
language_creators: [expert-generated]
language: [ko, en]
size_categories: [n<1K]
task_categories: [text-classification]    # | text-generation | reinforcement-learning | …
source_datasets: [original]
configs: [{config_name: default, data_files: [{split: train, path: data/train.jsonl}, {split: validation, path: data/val.jsonl}, {split: test, path: data/test.jsonl}]}]
extra_gated_prompt: "Personal work logs. Internal use only. Do not attempt re-identification."
harness:
  exporter_sha: "<git sha>"   ; policy_sha: "<sha>" ; cutoff: "<datetime>"
  gates_passed: [G1..G12]     ; vendor_output_in_targets: false
  canary: "<GUID>"            # for eval datasets
---
# Dataset Card for <name>

## Dataset Details
### Dataset Description
- What one row is, how many rows per split, period covered (`rai:dataCollectionTimeframe`).
- Curated by / owner: me. Contact. Status: internal | shareable.
### Dataset Sources
- Harness version, ontology version, log months, commit of the exporter.

## Uses
### Direct Use                (`rai:dataUseCases`)
### Out-of-Scope Use          (training any model on vendor outputs; re-identification; any use outside consent scopes)

## Dataset Structure
- Fields (top level + `meta`), splits and how they were made (group key, buckets, time window), dedupe clusters.

## Dataset Creation
### Curation Rationale       (Data Statements: why this data, which improvement-loop question it answers)
### Source Data
#### Data Collection and Processing   (`rai:dataCollection`, `rai:dataCollectionType` = "logged interactions with an AI agent harness", `rai:dataPreprocessingProtocol`: PII scan, redaction, dedupe, ATIF conversion; `rai:dataCollectionMissingData`)
#### Who are the source data producers? (Data Statements speaker profile: one bilingual ko/en professional, translation/annotation/code/research work; agent text by <models> under <terms>)
#### Text characteristics / speech situation (Data Statements: chat prompts to a coding agent, code-switched ko/en, imperative, short)
### Annotations
#### Annotation process      (`rai:dataAnnotationProtocol`: codebook = intent_recognition §3; blind-first protocol; `rai:annotationsPerItem`; `rai:machineAnnotationTools`: rules, models + prompt versions)
#### Who are the annotators? (`rai:annotatorDemographics`: the user only; compensation n/a)
#### Annotation quality      (`rai:dataAnnotationAnalysis`: κ per dimension, test-retest ceiling, Dawid-Skene posterior summary)
#### Personal and Sensitive Information (`rai:personalSensitiveInformation`: scanner + version, entity counts before/after, pseudonymization method, key custody, third-party persons policy, special categories excluded)

## Rights, Consent and Provenance
- Licence per row class; `model_terms` mix; vendor authorization refs (or "none: vendor outputs excluded from targets");
  excluded counts per gate (from gate_report.json); erasure handling.

## Bias, Risks, and Limitations   (`rai:dataBiases`, `rai:dataLimitations`, `rai:dataSocialImpact`)
- Single user; area and language skew; label drift; survivorship (only finished sessions); redaction artefacts.
### Recommendations

## Maintenance                     (`rai:dataReleaseMaintenancePlan`)
- Rebuild cadence, deprecation, how erasure requests flow to dataset versions.

## Citation / Glossary / Card Authors / Contact
```

### 8.2 Croissant manifest (`manifest.json`)
- `@context` includes `cr`, `rai`, `prov`, `dct`, `sc`; `"dct:conformsTo": ["http://mlcommons.org/croissant/1.1", "http://mlcommons.org/croissant/RAI/1.0"]` **[S]**.
- **`distribution`:** one `cr:FileObject` per data file with `sha256`. **`recordSet`:** fields with `dataType`. Splits via a `cr:Split` record set (`cr:TrainingSplit` / `cr:ValidationSplit` / `cr:TestSplit`) **[S]**.
- **Provenance:** dataset-level `prov:wasGeneratedBy` (the exporter run: start/end time, sha); field-level `prov:wasDerivedFrom` (e.g. `labels` ← `harness://fact/label`) **[S: spec 1.1 §PROV]**.
- **RAI fields** are filled from the card answers (one source of truth; `export_dataset.py` writes both).
- Validate with `mlcroissant validate --jsonld manifest.json` (the `mlcroissant` package from the same repo) **[S/K]**.

---

## 9. Splitting without leakage

0. **Prerequisite: keep the raw material.**
   - Set `cleanupPeriodDays` high in user settings.
   - At `SessionEnd`, copy the transcript (and `subagents/*.jsonl`) into `blobs/sha256/…`, as tracing note §9.6 describes.
   - Record the digest in the `session_end` event.
   - Run a secret scan before the copy is committed to the GitHub-synced harness-data, or keep transcripts in a non-synced blob store if the scan finds anything.
1. **Group key:** I2 intent id (`int_…`) when present, else `session_id`, else `<scope>/<date>`. All rows from one group share a split, including subagents, retries, label events, corrections and style pairs that point at the same session.
2. **Time first:**
   - Pick a cut-off per release (e.g. the last 20% of time).
   - Groups that *start* after the cut-off go to `test`/`val`; earlier groups go to `train`.
   - This mirrors how the model will be used (future prompts) and avoids training on later corrections of the same habit. Forward-chaining for repeated releases: each new release's test window is new; older test windows may move to train **only** after they have been used for a decision and are archived.
3. **Within a window:** `bucket = int(sha256(group_key)[:8], 16) % 100`; e.g. 0–9 → val. Deterministic, so re-exports agree.
4. **Freeze:** split assignments are append-only `split_assignment` facts (`frozen: true`). Re-labeling never moves a row. A new row of an existing group inherits that group's split.
5. **Quarantine:** EvalTask `holdout`, `gold` labels, anything with an eval canary, and their source events, groups and dup clusters → `quarantine` for all training datasets.
6. **Leak check** (gate G8 + a final test): no group key, dup cluster, or source event in two splits; no 13-gram overlap train↔test above τ. A failure aborts the export.
7. **Stratification report:** per split, the counts by area, language, speech_act, correction share and register. Warn on large imbalance. Do not re-balance by moving groups after freezing.

---

## 10. From logs to RL environments and evals

### 10.1 Replayable task = Harbor task
For a finished `task`/intent with a known outcome:
- **Freeze the input:**
  - repo at commit (`git_commit` from Handoff/precompact snapshot)
  - fixtures by sha256
  - the user's first prompt (redacted), plus the constraints added later by corrections (they become part of the instruction or of the tests)
- **Write the verifier from what decided success:**
  - `expected_checks` (tests, numbers, placeholders)
  - verify-skill criteria with proof
  - for code: the test command the user ran
  - The verifier writes `/logs/verifier/reward.json` with named components (e.g. `correctness`, `constraint_respected`, `cost`) **[S: Harbor]**.
- **Private tests are staged only at scoring time** (`stage_verifier` in verifiers, a separate verifier environment in Harbor) **[S]**, so the policy cannot read them. This is the same idea as `guard_protected.py`.
- **Validity checks:**
  - `solution/solve.sh` from the user's final state must score 1
  - the original failing agent state (when the log has it) must score below 1
  - Tasks that fail either check are dropped (an unsolvable or trivially passing environment teaches nothing). [?]
- **Training use:** an RL environment's reward is computed on the *new* policy's own rollouts, so the vendor-output gate does not touch the reward. The task instruction is human text. Logged Claude traces only give the reference and the difficulty.

### 10.2 User simulator for multi-turn tasks
- Seed simulated users from the user's own prompt sequences (human-authored, so trainable) with the speech-act and feedback distributions from intent labels: verifiers `UserSimEnv`, Harbor RFC-0002 simulated users **[S]**.
- Mark such data `synthetic.origin: simulated-user` and the generator model. If a Claude model plays the user, the simulated turns are Claude outputs (G7).

### 10.3 Rewards from corrections and edits [?]
- **Correction → rubric criterion:**
  - each `my_reasoning` becomes a yes/no criterion bound to the task type or scope ("keeps 계약 해지 as 'contract termination'", "does not touch dotfiles"). This is the RaR / checklist idea **[W]**.
  - The user approves criteria (the pattern-review ladder: correction → Pattern → Encoding kind `rubric-criterion` or `eval-task`, which already exists in the ontology **[S]**).
- **Reward** = weighted share of satisfied criteria + code checks.
  - Prefer code checks for each criterion where possible (regex/glossary/test).
  - Use an LLM judge only for the rest, with judge ≠ producer (evals/README rule) and the §5.1 caveat on Claude-as-judge.
- **Edit-cost reward (PRELUDE)** [W]: for StylePair-like tasks, reward = −normalized edit distance between the policy output and the user's final. Usable as an eval metric now; as an RL reward only on human-owned tasks.
- **Implicit signals as process rewards:** PermissionDenied, interrupts, reverts and rephrases (tracing note §4.6) → negative step labels with `implicit: true`, down-weighted against explicit corrections.
- **Reward-hacking guard:**
  - verifier files are read-only to the policy
  - the eval gate must not regress on locked tasks
  - inspect the top-reward rollouts by hand monthly (a known pattern for catching rubric gaming)

### 10.4 Evals first
- The eval exports (§4.7) are usable **today** with no vendor authorization: run any model (Claude via API, open models) against Harbor tasks with `harbor run`, score with rubrics and tests, and compare with `eval_gate.py`.
- That is also the honest way to decide whether a fine-tune is worth doing at all (BLUEPRINT: fine-tune "only for narrow, high-volume tasks").

---

## 11. Ontology and code changes (for a reviewed PR; ontology v0.3)

| Change | Detail |
|---|---|
| New embedded type `DataProps` | fields from §3.2; `store: {root: harness-data, path: log/YYYY-MM.jsonl (data_label events) or facts/…, format: embedded}` |
| New event types | `data_label` (labels_for → target), `split_assignment`, `consent` (scopes per area or project, by the user), `dsr` (erasure/objection; subject as HMAC), `export` (dataset, version, gate_report pointer, counts) |
| New enums | `source_kind`, `confidentiality`, `author_kind`, `model_terms`, `consent_basis`, `consent_scope`, `pii_status`, `synthetic_origin`, `label_source`, `split_name` (extends `eval_split: [train, holdout]` with `val, test, gold, quarantine`), `contamination` |
| Writer changes | `log_event.py`/`_common.py`: add `authorship` and `rights.source_kind` from scope; add `account_plan` (consumer/commercial) per session from settings → `model_terms`. `label_events.py`: write `label_provenance` (model, prompt_version, k). `style_pairs.py`: set `origin` and `human_edit_ratio`. |
| New scripts (stdlib + pinned local deps, run with `python3 -I`) | `pii_scan.py` (Presidio + gitleaks wrapper), `dedupe.py` (MinHash), `split_assign.py`, `export_dataset.py <dataset> --policy policy.yaml [--dry-run]`, `contamination.py`, `make_card.py` (card + Croissant), `to_atif.py` (calls pinned Harbor converter), `to_harbor_task.py` (EvalTask → task folder) |
| Policy file | `config/data_policy.yaml` in the repo: gate thresholds, soft-gate toggles, allowed scopes per dataset type. Protected like `rubrics/` (user-only edits) |
| Guard | extend `guard_protected.py` to deny agent writes under `$HARNESS_DATA/exports/` and to `config/data_policy.yaml` |
| Docs | `docs/TRAINING_DATA.md` (short form of this note), `templates/dataset_card.md` |

---

## 12. Implementation order (smallest useful first) [?]

0. **This week:** stop the loss.
   - raise `cleanupPeriodDays`
   - archive transcripts to blobs at SessionEnd (with a secret scan)
   - record account type per session
1. **Defaults without new UI:** scope-based `rights` and `authorship` defaults written by hooks; `split_assignment` by group + time; `pii_scan.py` dry run to measure how much is personal.
2. **First dataset, `intent-cls`** (human-only, clean):
   - monthly blind relabel → gold
   - Dawid-Skene over rule and model labels
   - card + Croissant
   - All gates exercised end to end.
3. **`evals/`:** EvalTask → Harbor tasks with canaries; run baseline models; wire into `eval_gate.py`.
4. **`trajectories/`** via the Harbor converter, eval/replay use only, with `extra.harness` rewards.
5. **`prefs`/`steps`** as judge-calibration eval sets. They become training sets only if `vendor_authorization_ref` is obtained (ask Anthropic, or rebuild pairs from open-model rollouts scored by the human rubrics, which yields clean on-policy data).
6. **RL environments** from §10 for one narrow area (e.g. translation QA with glossary checks) only after evals show a gap worth training for.

---

## 13. Open questions and risks
- **AUP scope:** "Use outputs to train an AI model" read broadly covers labels, judge scores and context text. This spec takes the broad reading. Written clarification from Anthropic would unlock the corrections/StylePair preference sets, which are the most valuable rows.
- **Human-edited outputs:** whether a user's heavily edited final (`human_edit_ratio` high) is still "outputs" is unsettled. The spec keeps `mixed` restricted, and `human_edit_ratio` is recorded so the policy can change without re-labeling.
- **AUP date:** the AUP page shows a date 27 days in the future. Re-read the page on 2026-11-12 and diff it against the "Previous Version".
- **PIPA status:** article numbers and the effective date (2027-03-09) of the AI special provision come from press reports. Confirm on law.go.kr.
- **OpenAI formats:** DPO/RFT shapes are from snippets (developers.openai.com was unreachable). Verify before building `openai_*.jsonl` converters.
- **Korean PII recall:** Presidio's Korean coverage is regex-only for IDs, and names depend on the NER model. Measure recall on a hand-labeled sample of 100 ko/mixed prompts before trusting `pii.status = clean`.
- **Single-annotator data:** κ against yourself (test-retest) is the ceiling. Any external annotator would need their own consent and a Data Statements annotator profile.
- **Volume:** one person's logs are small. Expect hundreds to low thousands of clean rows per year. The main value is evals, rubrics and environments, not raw SFT volume.

---

## Sources
- Anthropic Acceptable Use Policy (page dated "Effective November 12, 2026"): https://www.anthropic.com/legal/aup
- Anthropic Consumer Terms (Effective Oct 8, 2025): https://www.anthropic.com/legal/consumer-terms
- Anthropic Commercial Terms (Effective June 17, 2025): https://www.anthropic.com/legal/commercial-terms
- Anthropic, Updates to Consumer Terms (Aug 28, 2025): https://www.anthropic.com/news/updates-to-our-consumer-terms
- Claude Code data usage: https://code.claude.com/docs/en/data-usage
- Claude Platform glossary (fine-tuning): https://platform.claude.com/docs/en/about-claude/glossary
- AWS Bedrock Claude 3 Haiku fine-tuning: https://aws.amazon.com/blogs/aws/fine-tuning-for-anthropics-claude-3-haiku-model-in-amazon-bedrock-is-now-generally-available/ ; https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-supported.html
- OpenAI DPO guide: https://platform.openai.com/docs/guides/direct-preference-optimization (unreachable; snippets) ; Azure DPO: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/fine-tuning-direct-preference-optimization
- OpenAI RFT: https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning (unreachable) ; https://openai.com/index/introducing-agentkit/
- OpenAI Terms: https://www.openai.com/terms
- Harbor (ATIF RFC-0001 v1.8, tasks, rewardkit, Claude Code converter): https://github.com/harbor-framework/harbor @ 62db0c1 ; https://www.harborframework.com/docs/training-workflows/sft
- Terminal-Bench paper: https://arxiv.org/pdf/2601.11868
- HF TRL dataset formats: https://github.com/huggingface/trl/blob/main/docs/source/dataset_formats.md @ 6d6901c
- PrimeIntellect verifiers: https://github.com/PrimeIntellect-ai/verifiers @ 1f5ada9
- MLCommons Croissant 1.1 and RAI 1.0: https://github.com/mlcommons/croissant @ ec24358
- HF dataset card spec and template: https://github.com/huggingface/hub-docs/blob/main/datasetcard.md ; https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/datasetcard_template.md
- Microsoft Presidio: https://github.com/microsoft/presidio @ 2523c7b
- datasketch: https://github.com/ekzhu/datasketch @ c7eaaee
- Data Provenance Initiative: https://arxiv.org/abs/2310.16787 ; https://www.nature.com/articles/s42256-024-00878-8 ; https://github.com/Data-Provenance-Initiative/Data-Provenance-Collection
- PIPA AI special provision (Korean press): https://www.lawtimes.co.kr/news/articleView.html?idxno=226510 ; https://www.newspim.com/news/view/20260820001186 ; https://www.etnews.com/20260820000393 ; https://view.asiae.co.kr/article/2026051413143976225
- PIPC generative AI guidance (secondary): https://connectontech.bakermckenzie.com/south-korea-sets-ai-standard-pipcs-guidelines-for-generative-ai-present-obligations-opportunity/
- EU GPAI training data template: https://wilmerhale.com/en/insights/blogs/wilmerhale-privacy-and-cybersecurity-law/european-commission-releases-mandatory-template-for-public-disclosure-of-ai-training-data ; https://www.mishcon.com/news/gpai-model-guidance-and-training-data-templates-published-by-commission
- Rubrics as Rewards (ICLR 2026): https://proceedings.iclr.cc/paper_files/paper/2026/hash/cfd7bee7a651ee9af525098ef67a9e45-Abstract-Conference.html ; Open Rubric System: https://arxiv.org/pdf/2602.14069 ; Rubric-ARM: https://arxiv.org/pdf/2602.01511 ; Rubrics survey: https://github.com/RUC-NLPIR/Rubrics_Survey
- PRELUDE/CIPHER (learning from user edits): https://arxiv.org/abs/2404.15269 ; https://github.com/gao-g/prelude
- Contamination background: https://arxiv.org/pdf/2502.17521
- From knowledge (not re-fetched): Gebru et al., "Datasheets for Datasets" (CACM 2021); Pushkarna et al., "Data Cards" (FAccT 2022); Bender & Friedman, "Data Statements for NLP" (TACL 2018); Dawid & Skene (1979); Cohen's κ; Krippendorff's α; EDPB Opinion 28/2024; GDPR Arts. 5, 6, 9, 15, 17, 21; PIPA Arts. 15, 23, 24, 28-2, 28-4.
