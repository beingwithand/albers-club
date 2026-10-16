# Intent-embedded causal log: tracing, provenance and process mining for the Claude harness

Research date: 2026-10-16. Target: `claude-harness/` (plugin) writing to `$HARNESS_DATA/log/`.
This note extends `claude-harness/schema/event.md` (Event v0.2); it does not replace it (see section 11, migration).

---

## 0. TL;DR

- **One write model, many read models.** Hooks append immutable *facts* (span start/end, intent, intent assignment, feedback, relation, checkpoint) to a hash-chained JSONL log. Everything else (span tree, intent graph, OCEL 2.0 file, OTLP export to Phoenix/Langfuse, weekly report) is a rebuildable projection (event sourcing + CQRS).
- **Trace = Claude Code session; span = turn / llm request / tool call / subagent / hook / compaction.** Goals live *above* traces as intent nodes, because a goal spans many sessions. `gen_ai.conversation.id` = Claude Code `session_id`.
- **Intent is a first-class node (`prov:Plan`)**, and every span carries a resolved `harness.intent.id` plus *how* it got it (`explicit | inherited | override | inferred | relabeled`). Intent inherits down the span tree; overrides and later relabels are new `intent_assignment` facts, never edits.
- **Feedback attaches to a span, trace, session or intent node** using the OpenInference annotation fields (`name, score, label, explanation, annotator_kind, identifier, metadata`), the Langfuse score data types (`NUMERIC | CATEGORICAL | BOOLEAN | TEXT | CORRECTION`) and the LangSmith `correction` field. Post-hoc feedback is a carrier record with exactly one link to its target (the OpenInference rule).
- **Process mining:** project the log to **OCEL 2.0** (object types: session, turn, intent, file, subagent, skill, commit, feedback) and run pm4py: `discover_ocdfg`, `ocel_flattening(ocel, "intent")` then `discover_process_tree_inductive` / `discover_heuristics_net`, and conformance via `conformance_declare`, `fitness_alignments` and `conformance_temporal_profile` against each intent's declared plan. That shows the user's *actual* workflows and where they deviate.
- **Integrity:** RFC 8785 canonical JSON, SHA-256, a per-file `prev_hash` chain, RFC 6962-style Merkle checkpoints written hourly (matching the existing autocommit), and git push as an external witness (the role CT log gossip plays). Large or private content goes in content-addressed blobs (or HMAC refs for vault data), so it can be redacted without breaking the chain.

---

## 1. Sources and their state in 2026

| Source | How I read it | State and relevance |
|---|---|---|
| OTel GenAI semconv | `git clone` of **open-telemetry/semantic-conventions-genai** @ f3c6d0c (2026-10-14) | The GenAI conventions **moved out of the main repo into a dedicated repo**. `model/manifest.yaml`: `schema_url: https://opentelemetry.io/schemas/gen-ai-dev/1.42.0-dev`, `stability: development`, depends on core semconv 1.44.0. No tagged release in CHANGELOG yet; ~50 unreleased towncrier fragments, several **breaking** (#217, #242, #257, #289, #322, #374, #440, #469, #521). Everything is still `development`: **pin a version and keep a mapping table.** |
| OpenInference | clone **Arize-ai/openinference** @ 38b858d (2026-10-16), `spec/` | Has a new `spec/annotations.md` defining span, trace and session feedback, and the post-hoc carrier rule. Span kinds now include `DECISION`. |
| Langfuse | clone **langfuse/langfuse-python** @ 35f8e7e | Observation types: `span, generation, embedding, agent, tool, chain, retriever, evaluator, guardrail, event`. Score subjects: `trace, observation, session, experiment`. Score data types include **`CORRECTION`**. OTel attrs `langfuse.observation.*`, `langfuse.trace.*`, `session.id`, `user.id`. |
| LangSmith | clone **langchain-ai/langsmith-sdk** @ 290f06a | Run: `id, trace_id, parent_run_id, dotted_order, run_type, inputs, outputs, events, extra, tags, session_id` (= project). Threads: `thread_id`. Feedback: `key, score, value, comment, correction, feedback_source, run_id, trace_id, session_id, feedback_group_id`. |
| W&B Weave | clone **wandb/weave** @ 5b9bf0d | `CallSchema`: `id, op_name, trace_id, parent_id, thread_id, turn_id, started_at, ended_at, attributes, inputs, output, summary, exception`. Feedback: `feedback_type` (`wandb.reaction.1`, `wandb.note.1`, custom), `weave_ref`, `payload`, `annotation_ref`, `call_ref`. Objects are content-addressed: `weave:///entity/project/object/name:digest`. |
| Braintrust | clone **braintrustdata/braintrust-sdk** @ 5a8b3c5 (`generated_types.json`, `js/util/span_types.ts`) | Log event: `id, _xact_id, span_id, span_parents[], root_span_id, is_root, span_attributes{name,type,purpose,log_level}, input, output, expected, error, scores, metadata, metrics, tags, comments, audit_data, origin, facets, classifications`. Span types: `llm, score, function, eval, task, tool, automation, facet, preprocessor, classifier, review, question, log`. Note `span_parents` is a **list** (a DAG, not a tree). |
| Claude Code telemetry and hooks | `curl` of code.claude.com `monitoring-usage.md` and `hooks.md` (reachable) | Native beta traces: `claude_code.interaction` (one per prompt) → `claude_code.llm_request`, `claude_code.hook`, `claude_code.tool` → `tool.blocked_on_user`, `tool.execution`, plus subagent spans. Correlation ids: `session.id`, `prompt.id`, `event.sequence`, `tool_use_id` = `gen_ai.tool.call.id`, `agent_id`, `parent_agent_id`, `workflow.run_id`. Bash subprocesses inherit `TRACEPARENT`. Hook stdin includes `session_id, prompt_id, transcript_path, cwd, permission_mode, effort.level, hook_event_name, agent_id, agent_type`, and `tool_use_id` on tool events. |
| W3C PROV-O | clone **w3c/prov** @ aa82bd7 (ontology `.ttl`) | `prov:Plan ⊑ prov:Entity`. Its own comment: plans are represented "to validate the execution as represented in the provenance record, to manage expectation failures, or to provide explanations". That is exactly the intent → conformance link. |
| PROV-AGENT | web search (arXiv 2508.02866) | A research PROV extension for agent prompts, responses and decisions plus MCP. Not a W3C standard. Useful vocabulary only. |
| OCEL 2.0 / pm4py | clone **process-intelligence-solutions/pm4py** @ 0e07784, `__version__ = "2.7.23.11"` | OCEL 2.0 read/write (`read_ocel2_json/sqlite/xml`, `write_ocel2_*`), `discover_ocdfg`, `ocel_flattening`, `ocel_e2o_lifecycle_enrichment`, `conformance_ocdfg`, `discover_powl`, `discover_declare`, and `pm4py.llm.abstract_ocel*`. The OCEL object holds `events, objects, relations (E2O), o2o, e2e, object_changes`. **`e2e` is a pm4py extension, not in the OCEL 2.0 standard.** |
| W3C Trace Context | clone **w3c/trace-context** @ acab820 | `traceparent = 00-<32hex trace-id>-<16hex parent-id>-<2hex flags>`; Level 2 adds the `random-trace-id` flag (bit 1). |
| Merkle / CT | clone **transparency-dev/merkle** @ c39fbf3 (`rfc6962/rfc6962.go`) | Leaf hash = `H(0x00 ‖ data)`, node hash = `H(0x01 ‖ left ‖ right)` (RFC 6962 / RFC 9162). |
| Agent-trace mining papers | web search snippets only | TraceCompiler (arXiv 2608.02680, Aug 2026): admit a tool→tool dependency only when **data flow** supports it ("observed order ≠ structure"). Also: a 2026 evidence-tracing survey (arXiv 2606.04990) saying OTel lacks rationale and inter-agent-message objects; "Automata from Agent Traces" (2608.23670); SKILL-DISCO (2606.26669). I could not open these papers; I have the search snippets only. |

**Unreachable from this sandbox** (the proxy gateway answered 403 to CONNECT, or DNS failed): www.w3.org, opentelemetry.io, docs.smith.langchain.com, weave-docs.wandb.ai, braintrust.dev, langfuse.com, arize.com (Phoenix docs), ocel-standard.org (so the JSON schema was read from pm4py's exporter instead), arxiv.org, ceur-ws.org, rfc-editor.org, research.google (Dapper), docs.sigstore.dev, martinfowler.com, pm4py.fit.fraunhofer.de. Everything above was cross-checked against the GitHub sources. Dapper and event sourcing are described from general knowledge.

---

## 2. How the systems line up (concept crosswalk)

| Our concept | OTel GenAI | OpenInference | Langfuse | LangSmith | Weave | Braintrust | PROV | OCEL / XES |
|---|---|---|---|---|---|---|---|---|
| **Session** (Claude Code `session_id`) | `gen_ai.conversation.id` | `session.id` | `session.id` (session) | `thread_id` / metadata `session_id` | `thread_id` | (metadata) | `prov:Bundle` | object type `session`; a case notion |
| **Trace** (= one session here) | trace_id | trace | trace | trace_id (`dotted_order` root) | trace_id | `root_span_id` | Bundle | case |
| **Turn** (user prompt) | `invoke_agent` (internal) | `AGENT` / `CHAIN` | `agent` | run `chain` | call, `turn_id` | `task` | `prov:Activity` | event + object `turn` |
| **LLM request** | `chat {model}` (`gen_ai.client.inference`) | `LLM` | `generation` | `llm` | call | `llm` | Activity | event `llm_request` |
| **Tool call** | `execute_tool {tool}` | `TOOL` | `tool` | `tool` | call | `tool` | Activity used/generated Entities | event `tool:<name>` |
| **Subagent** | nested `invoke_agent {agent}` | `AGENT` | `agent` | `chain` | call | `task` | Activity + `prov:Agent` (`actedOnBehalfOf`) | object `subagent` |
| **Plan / decomposition** | `plan` op (new, #97) | `CHAIN` | `span` | `chain` | call | `task` | `prov:Plan` | event `plan` |
| **Skill load** | `execute_tool` + `gen_ai.skill.name` (#498) | `TOOL` | `tool` | `tool` | call | `tool` | Plan reuse | object `skill` |
| **Intent / goal** | — (none) | — | — | — | — | — | **`prov:Plan` via `prov:hadPlan`** | object `intent` |
| **Feedback / correction** | event `gen_ai.evaluation.result` | `annotations.*` / `evaluations.*`, `EVALUATOR` carrier | score (`CORRECTION` type) | feedback (`correction`) | feedback (`wandb.note.1`) | `scores`, `comments`, `review` span | `wasInvalidatedBy`, `wasRevisionOf` | event `feedback:*` + object `feedback` |
| **Artifact** (file, commit) | — | `retrieval.documents` | — | attachments | ObjectRef (`:digest`) | — | `prov:Entity`, `wasGeneratedBy`, `used` | object `file` / `commit` |

**No tracing standard has an intent node.** OTel, OpenInference and the vendors all stop at the operation level. PROV is the only standard with a *plan* concept, and OCEL is the only one that lets a goal be an object that many events touch. The design below therefore takes the span model from OTel/OpenInference, intent from PROV, and mining from OCEL.

---

## 3. Design principles

1. **Facts are immutable; meaning is projected.** This matches D6 (append-only) and the OpenInference rule "ended spans are immutable; post-hoc feedback MUST use a new carrier".
2. **Reuse names; namespace the rest.** Use `gen_ai.*` exactly where a GenAI attribute fits and `openinference.span.kind` for viewer compatibility. Our own attributes go under `harness.*`. Never invent `gen_ai.*` keys.
3. **Ids come from Claude Code wherever possible** (`session_id`, `prompt_id`, `tool_use_id`, `agent_id`). That makes facts joinable with native OTel telemetry and transcripts. Do not fabricate `gen_ai.conversation.id` (#219 says no generated UUIDs or hashes for it); use the real `session_id`.
4. **Causality has two kinds of edge.** *Control* edges (span parent/child, `prov:wasInformedBy`, follows-from) and *data* edges (`prov:used` / `prov:wasGeneratedBy` on file entities keyed by content hash). Mining uses the first, and TraceCompiler-style dependency claims need the second.
5. **Intent is bitemporal.** `effective` is the span it applies to; `recorded_at` is when we believed it. The weekly labeler's relabel never overwrites the hook-time guess. Both are kept, and the projection picks by authority.
6. **One writer per chain.** Hooks run concurrently, so take an `fcntl.flock` on append, or chain per writer and merge at checkpoints (section 9).

---

## 4. Data model

### 4.1 Layers

```
L0  facts/YYYY-MM.jsonl      hash-chained envelopes (write model, append-only)   <- hooks, skills, labeler
L0b blobs/sha256/ab/cd…       content-addressed payloads (prompts, tool I/O)     <- same writers
L1  projections/spans.sqlite  span tree + resolved intent per span               <- projector (rebuildable)
    projections/intents.json  intent graph (nodes + edges + status timeline)
    projections/ocel2.sqlite  OCEL 2.0 (pm4py.write_ocel2_sqlite)
    projections/otlp/*.json   OTLP/JSON for Phoenix or Langfuse (optional)
L2  existing reports          weekly_report.py, patterns.py read L1, not L0
```

### 4.2 Fact kinds

| `kind` | Written by | Meaning |
|---|---|---|
| `span_start` | hook at start (UserPromptSubmit, PreToolUse, SubagentStart, PreCompact, SessionStart) | Opens a span. Has ids, parent, kind, name, start time, initial intent. |
| `span_end` | hook at end (Stop/StopFailure, PostToolUse/PostToolUseFailure/PermissionDenied, SubagentStop, PostCompact, SessionEnd) | Closes it: status, end time, outputs (as blob refs), usage. |
| `span_event` | any hook | A timestamped point event on a span (permission decision, retry, `gen_ai.evaluation.result`). |
| `intent` | user (explicit), turn hook (inferred), labeler, `why` skill | Creates or revises an IntentNode. A revision is a new fact with `revision_of`. |
| `intent_assignment` | hook (override), labeler (relabel), user | Binds an intent to a span (or subtree) *after* span_start. |
| `feedback` | user, verifier agent, eval runner, implicit-signal detector | A score, label, note or correction aimed at a span, trace, session or intent. |
| `relation` | projector-free writers (hooks/skills) | A PROV or OCEL relation not implied by the span tree: `used`, `wasGeneratedBy`, `wasDerivedFrom`, `wasRevisionOf`, `follows_from`, `corrects`. |
| `checkpoint` | autocommit script | Merkle tree head over the leaves so far (section 9). |
| `legacy_event` | migration | Wraps an existing v0.2 Event line unchanged. |

### 4.3 Span kinds and how each maps out

| `harness.span.kind` | Opened / closed by hook | OTel span name | `gen_ai.operation.name` | `openinference.span.kind` | Langfuse type | PROV class | OCEL activity (classifier) |
|---|---|---|---|---|---|---|---|
| `session` | SessionStart / SessionEnd | `invoke_agent claude-code` | `invoke_agent` | `AGENT` | `agent` | Activity (assoc. user + Claude) | `session:start`, `session:end` |
| `turn` | UserPromptSubmit / Stop, StopFailure | `invoke_agent claude-code` (child) | `invoke_agent` | `AGENT` | `agent` | Activity | `user:prompt` → `turn:end:<status>` |
| `llm_request` | (from native OTel, if beta tracing is on) | `chat {model}` | `chat` | `LLM` | `generation` | Activity | `llm` (usually filtered out of mining) |
| `tool` | PreToolUse / PostToolUse, PostToolUseFailure, PermissionDenied | `execute_tool {tool}` | `execute_tool` | `TOOL` | `tool` | Activity | `tool:<Name>[:<class>]` |
| `permission` | PermissionRequest / tool_decision | `blocked_on_user` | — | `CHAIN` | `span` | Activity (assoc. user) | `user:allow`, `user:reject` |
| `subagent` | SubagentStart / SubagentStop | `invoke_agent {agent_type}` | `invoke_agent` | `AGENT` | `agent` | Activity + Agent `actedOnBehalfOf` parent | `subagent:<type>` |
| `skill` | PreToolUse(Skill) | `execute_tool Skill {skill}` | `execute_tool` + `gen_ai.skill.name` | `TOOL` | `tool` | Activity `hadPlan` skill Plan | `skill:<name>` |
| `plan` | ExitPlanMode tool / TaskCreated | `plan claude-code` | `plan` | `CHAIN` | `span` | Activity generating a Plan entity | `plan` |
| `workflow` | Workflow tool run (`workflow.run_id`) | `invoke_workflow {name}` | `invoke_workflow` | `CHAIN` | `chain` | Activity | `workflow:<name>` |
| `compaction` | PreCompact / PostCompact | `compact` | — (set `gen_ai.conversation.compacted=true` on the next inference) | `CHAIN` | `span` | Activity, `wasDerivedFrom` | `compact` |
| `hook` | (our own hooks, optional) | `hook {name}` | — | `GUARDRAIL` (for gates) | `guardrail` | Activity | `gate:<name>:<verdict>` |
| `feedback_carrier` | feedback writer (post-hoc) | `feedback {name}` | — | `EVALUATOR` | `evaluator` | Activity generating a feedback Entity | `feedback:<name>` |

**Ids:**
- `trace_id` = first 32 hex characters of `sha256("cc-session:" + session_id)`. This is deterministic so every hook can compute it without shared state. Set trace-flags to `00` or `01` (sampled) and **do not set `random-trace-id`**, because the id is derived.
- `span_id` (16 hex):
  - turn: from `prompt_id`
  - tool: from `tool_use_id`
  - subagent: from `agent_id`
  - session: from `session_id` + `"root"`
  - each derived as `sha256(kind+":"+native_id)[:16]`
- The derivation means start and end facts written by different hook processes agree on the id without passing state.
- `/clear` gives a new `session_id`, so it starts a new trace. Link it with `relation{type:"follows_from"}` to the previous session root, the OTel span-link idiom.

### 4.4 Intent

An **IntentNode** is a `prov:Plan`: something the activity was *meant to accomplish*, kept separate from what it did.

```
kind:    goal (multi-session outcome) | task (one deliverable) | subgoal (decomposition step)
         | constraint (must / must-not) | preference (style or how-to) | question (information need)
source:  user_stated | inferred | corrected | imported (from tasks.json / HANDOFF.md)
status timeline (OCEL object attribute changes):
         proposed -> active -> (satisfied | abandoned | superseded | blocked) ; any -> reopened
edges:   refines (child -> parent goal)   serves (task -> goal)   supersedes   conflicts_with
         constrains (constraint -> intent)   derived_from_feedback (-> feedback id)
```

Each span carries a **resolved intent** (written at `span_start` and re-resolved by the projector):

| Attribute | Type | Meaning |
|---|---|---|
| `harness.intent.id` | string `int_…` | The innermost intent this span serves. |
| `harness.intent.path` | string[] | Ancestor chain, root goal first (denormalized for mining and filtering). |
| `harness.intent.binding` | enum | `explicit` (stated on this span) / `inherited` (from the parent span) / `override` (an intent_assignment replaced the inherited one) / `inferred` (a model guessed it) / `relabeled` (a post-hoc labeler or human changed it). |
| `harness.intent.confidence` | float 0..1 | 1.0 for explicit or human-set. |
| `harness.intent.assigned_by` | string | `me`, `harness`, `agent:<name>`. |
| `harness.intent.rationale` | string? | Why this span serves the intent (optional; feeds `meta`). |
| `harness.intent.drift` | float 0..1? | Projector-computed distance between the span's own stated purpose (subagent prompt, Bash `description`) and the resolved intent. |

### 4.5 Propagation rules (inheritance and override)

Resolution for span *s* (the projector runs this; hooks run a cheap version at start):

```
resolve(s):
  1. a = latest intent_assignment targeting s directly, chosen by AUTHORITY then recorded_at
  2. if a exists                 -> (a.intent_id, binding = a.binding)
  3. elif s has explicit intent   -> (that, "explicit")        # e.g. user typed "goal: …", Agent tool prompt names one
  4. elif parent(s) exists        -> (resolve(parent).id, "inherited")
  5. elif session default intent  -> (that, "inherited")       # from SessionStart: HANDOFF.md / tasks.json active item
  6. else                          -> (null, "unbound")
AUTHORITY: me > verifier/human-review > labeler LLM > hook heuristic
subtree assignments (scope:"subtree") apply to s and every descendant that has no closer assignment.
```

- **Down the tree.** A turn inherits from the session default; tool and subagent spans inherit from the turn. A subagent gets a *child* intent of kind `subgoal` (`refines` the turn's intent) when its prompt states a narrower purpose. That keeps fan-out workers attributable.
- **Override.** If the user's next prompt redirects ("no, I meant the Mac setup"), the turn hook writes a new `intent` (source `corrected`, `supersedes` the old one) and an `intent_assignment` with `scope:"subtree"` over the *previous* turn. The span facts stay untouched; the projector re-resolves.
- **Across processes.** `TRACEPARENT` already reaches Bash subprocesses. Also export `HARNESS_INTENT_ID` (and optionally a W3C `baggage` entry `harness.intent.id=<id>`) from the SessionStart hook's environment file, so scripts the agent runs (`kb.py`, `eval_gate.py`) can stamp facts with the same intent.
- **Up the tree (rollup).** An intent is `satisfied` only when a verification feedback with `label:"pass"` targets a span bound to it, or the user says so. That matches the existing `verify_gate.py` idea.

### 4.6 Human feedback and corrections

Signals that become `feedback` facts automatically (`annotator_kind` in brackets):

| Signal | Source | Feedback |
|---|---|---|
| User rejects a tool call | `PermissionDenied` hook / `claude_code.tool_decision` `decision:"reject"`, `source:"user_reject"` | target = tool span; `name:"tool_permission"`, `label:"rejected"`, BOOLEAN 0 [HUMAN] |
| User interrupts (Esc) | `StopFailure` or a turn ending without Stop | target = turn; `name:"interrupted"` [HUMAN] |
| Correction phrasing in the next prompt | existing `detect_correction()` (`correction_candidate`, `correction_confidence`) | target = **previous turn**; `name:"correction"`, `data_type:"CORRECTION"`, `value`=the new prompt (blob ref), score=`confidence` [HUMAN, inferred] |
| User edits or reverts a file Claude wrote | FileChanged hook / git diff over a `wasGeneratedBy` entity | target = the tool span that generated the file version; `name:"human_edit"`, `correction`=diff ref [HUMAN] |
| Verifier verdict | skill `verify` | target = turn or intent; `name:"verification"`, `label: pass|fail|needs-human` [LLM or CODE] |
| Session survey | `claude_code.feedback_survey` `responded` | target = session; `name:"session_quality"` [HUMAN] |
| Weekly review | skill `review-week` correction | target = the span named by `corrects`; fields `agent_did`, `my_correction`, `my_reasoning` [HUMAN] |

Each feedback also says what it does to intent, through `intent_effect`:
- `none`: the work was wrong but the intent was understood.
- `refine`: the intent was underspecified. Write a new intent version with `revision_of` and add the constraint.
- `override`: the intent was misread. `supersedes` plus a subtree `intent_assignment`.
- `reject`: the intent itself is abandoned.

That keeps "did the wrong thing" separate from "misunderstood what I wanted", which is the labeling signal the improvement loop needs (D7).

---

## 5. JSON Schemas (field level)

All facts share one envelope. `payload` is one of the kind-specific schemas. JSON Schema 2020-12.

### 5.1 Envelope (`facts/YYYY-MM.jsonl`, one per line)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "harness://schema/fact/1.0.0",
  "type": "object",
  "required": ["v", "fid", "kind", "seq", "recorded_at", "writer", "prev", "hash", "payload"],
  "additionalProperties": false,
  "properties": {
    "v":           {"const": "1.0.0"},
    "fid":         {"type": "string", "pattern": "^f_[0-9a-f]{26}$", "description": "fact id = 'f_' + first 26 hex of hash"},
    "kind":        {"enum": ["span_start","span_end","span_event","intent","intent_assignment","feedback","relation","checkpoint","legacy_event"]},
    "seq":         {"type": "integer", "minimum": 0, "description": "0-based position in this chain (file)"},
    "recorded_at": {"type": "string", "format": "date-time"},
    "writer":      {"type": "string", "description": "hook:<name> | skill:<name> | agent:<name> | me | script:<name>"},
    "host":        {"type": "string", "description": "machine id (multi-Mac)"},
    "chain":       {"type": "string", "description": "chain id, e.g. 'main' or 'w:<host>:<writer>' when per-writer chains are used"},
    "prev":        {"type": "string", "pattern": "^(sha256:[0-9a-f]{64}|genesis)$"},
    "hash":        {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                    "description": "sha256(0x00 || JCS(envelope without 'hash' and 'fid'))"},
    "payload":     {"type": "object"}
  }
}
```

### 5.2 `span_start` / `span_end` payloads

```json
{
  "$id": "harness://schema/span_start/1.0.0",
  "type": "object",
  "required": ["trace_id", "span_id", "kind", "name", "start_time", "attributes"],
  "properties": {
    "trace_id":       {"type": "string", "pattern": "^[0-9a-f]{32}$"},
    "span_id":        {"type": "string", "pattern": "^[0-9a-f]{16}$"},
    "parent_span_id": {"type": ["string","null"], "pattern": "^[0-9a-f]{16}$"},
    "kind":           {"enum": ["session","turn","llm_request","tool","permission","subagent","skill","plan","workflow","compaction","hook","feedback_carrier"]},
    "name":           {"type": "string", "description": "OTel span name, e.g. 'execute_tool Edit'"},
    "otel_kind":      {"enum": ["INTERNAL","CLIENT"], "default": "INTERNAL"},
    "start_time":     {"type": "string", "format": "date-time"},
    "native": {
      "type": "object", "description": "Claude Code ids, verbatim",
      "properties": {
        "session_id": {"type": "string"}, "prompt_id": {"type": "string"},
        "tool_use_id": {"type": "string"}, "agent_id": {"type": "string"},
        "parent_agent_id": {"type": "string"}, "workflow_run_id": {"type": "string"},
        "transcript_path": {"type": "string"}, "transcript_uuid": {"type": "string", "description": "transcript JSONL uuid; parentUuid gives message-level causality"},
        "event_sequence": {"type": "integer"}, "native_traceparent": {"type": "string"}
      }
    },
    "attributes": {
      "type": "object",
      "description": "flat OTel attributes; keys from section 6. Values: string|number|bool|array of these.",
      "properties": {
        "gen_ai.operation.name":  {"enum": ["invoke_agent","execute_tool","chat","plan","invoke_workflow"]},
        "gen_ai.conversation.id": {"type": "string"},
        "gen_ai.agent.name":      {"type": "string"},
        "gen_ai.tool.name":       {"type": "string"},
        "gen_ai.tool.call.id":    {"type": "string"},
        "gen_ai.tool.type":       {"enum": ["function","extension","datastore"]},
        "gen_ai.skill.name":      {"type": "string"},
        "openinference.span.kind":{"enum": ["AGENT","CHAIN","LLM","TOOL","EVALUATOR","GUARDRAIL"]},
        "session.id":             {"type": "string"},
        "harness.span.kind":      {"type": "string"},
        "harness.intent.id":      {"type": ["string","null"], "pattern": "^int_[0-9a-z]{10,}$"},
        "harness.intent.path":    {"type": "array", "items": {"type": "string"}},
        "harness.intent.binding": {"enum": ["explicit","inherited","override","inferred","relabeled","unbound"]},
        "harness.intent.confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "harness.scope":          {"type": "string", "description": "ontology scope grammar"},
        "harness.permission_mode":{"enum": ["default","plan","acceptEdits","auto","dontAsk","bypassPermissions"]},
        "harness.effort":         {"enum": ["low","medium","high","xhigh","max"]},
        "harness.activity":       {"type": "string", "description": "process-mining classifier, e.g. 'tool:Bash:vcs'"}
      }
    },
    "input_ref": {"$ref": "#/$defs/contentRef"}
  },
  "$defs": {
    "contentRef": {
      "type": "object", "required": ["digest"],
      "properties": {
        "digest":   {"type": "string", "pattern": "^(sha256|hmac-sha256):[0-9a-f]{64}$"},
        "store":    {"enum": ["blobs","vault","inline","redacted"]},
        "bytes":    {"type": "integer"},
        "mime":     {"type": "string"},
        "preview":  {"type": "string", "maxLength": 280}
      }
    }
  }
}
```

```json
{
  "$id": "harness://schema/span_end/1.0.0",
  "type": "object",
  "required": ["trace_id", "span_id", "end_time", "status"],
  "properties": {
    "trace_id":  {"type": "string", "pattern": "^[0-9a-f]{32}$"},
    "span_id":   {"type": "string", "pattern": "^[0-9a-f]{16}$"},
    "end_time":  {"type": "string", "format": "date-time"},
    "status":    {"type": "object", "required": ["code"],
                  "properties": {"code": {"enum": ["UNSET","OK","ERROR"]},
                                 "message": {"type": "string"},
                                 "error.type": {"type": "string", "description": "OTel error.type, e.g. 'permission_denied', 'interrupted', 'tool_error'"}}},
    "attributes": {"type": "object", "description": "end-time attrs: gen_ai.usage.input_tokens, gen_ai.usage.output_tokens, gen_ai.usage.cache_read.input_tokens, gen_ai.response.finish_reasons, harness.cost_usd, harness.result_tokens"},
    "output_ref": {"$ref": "harness://schema/span_start/1.0.0#/$defs/contentRef"},
    "artifacts":  {"type": "array", "description": "PROV entities touched; becomes relation facts in projection",
                   "items": {"type": "object", "required": ["role","entity"],
                             "properties": {"role": {"enum": ["used","generated","invalidated"]},
                                            "entity": {"type": "string", "description": "file:<repo-rel-path>@sha256:<hex> | commit:<sha> | url:<...>"}}}}
  }
}
```

### 5.3 `intent` payload (IntentNode version)

```json
{
  "$id": "harness://schema/intent/1.0.0",
  "type": "object",
  "required": ["intent_id", "version", "kind", "statement", "source", "status"],
  "properties": {
    "intent_id":   {"type": "string", "pattern": "^int_[0-9a-z]{10,}$", "description": "stable across versions"},
    "version":     {"type": "integer", "minimum": 1},
    "revision_of": {"type": ["string","null"], "description": "fid of previous version (prov:wasRevisionOf)"},
    "kind":        {"enum": ["goal","task","subgoal","constraint","preference","question"]},
    "statement":   {"type": "string", "description": "one sentence, user's words where possible"},
    "source":      {"enum": ["user_stated","inferred","corrected","imported"]},
    "status":      {"enum": ["proposed","active","satisfied","abandoned","superseded","blocked","reopened"]},
    "scope":       {"type": "string"},
    "confidence":  {"type": "number", "minimum": 0, "maximum": 1},
    "success_criteria": {"type": "array", "items": {"type": "string"}},
    "expected_plan": {
      "type": "object", "description": "normative process for conformance (prov:Plan content)",
      "properties": {
        "skill":   {"type": "string", "description": "skill whose procedure is the plan, e.g. 'verify'"},
        "declare": {"type": "array", "description": "Declare constraints over harness.activity",
                    "items": {"type": "object", "required": ["template","a"],
                              "properties": {"template": {"enum": ["existence","absence","init","response","precedence","succession","not_succession","chain_response","responded_existence","coexistence"]},
                                             "a": {"type": "string"}, "b": {"type": "string"}}}},
        "process_tree": {"type": "string", "description": "pm4py process tree string, e.g. \"->( 'user:prompt', *( 'tool:Read', 'tool:Edit' ), 'tool:Bash:test' )\""}
      }
    },
    "edges": {"type": "array", "items": {"type": "object", "required": ["type","to"],
              "properties": {"type": {"enum": ["refines","serves","supersedes","conflicts_with","constrains","derived_from_feedback"]},
                             "to": {"type": "string"}}}},
    "origin_span": {"type": ["object","null"], "properties": {"trace_id": {"type":"string"}, "span_id": {"type":"string"}}},
    "intent_situation": {"type": "string", "description": "maps to Event.situation"},
    "meta": {"type": "object", "description": "same shape as Event.meta (kind_of_thing, repeat_how, prevent_how, generalizes_to)"}
  }
}
```

### 5.4 `intent_assignment` payload

```json
{
  "$id": "harness://schema/intent_assignment/1.0.0",
  "type": "object",
  "required": ["target", "intent_id", "binding", "scope", "authority"],
  "properties": {
    "target":    {"type": "object", "required": ["trace_id","span_id"],
                  "properties": {"trace_id": {"type":"string"}, "span_id": {"type":"string"}}},
    "intent_id": {"type": "string"},
    "binding":   {"enum": ["override","relabeled","inferred","explicit"]},
    "scope":     {"enum": ["span","subtree"]},
    "authority": {"enum": ["me","reviewer","labeler","heuristic"]},
    "confidence":{"type": "number"},
    "reason":    {"type": "string"},
    "caused_by": {"type": ["string","null"], "description": "fid of feedback that triggered it"}
  }
}
```

### 5.5 `feedback` payload (union of OpenInference, Langfuse, LangSmith and OTel)

```json
{
  "$id": "harness://schema/feedback/1.0.0",
  "type": "object",
  "required": ["feedback_id", "target", "name", "annotator_kind"],
  "anyOf": [{"required": ["score"]}, {"required": ["label"]}, {"required": ["explanation"]}, {"required": ["correction"]}],
  "properties": {
    "feedback_id":   {"type": "string", "pattern": "^fb_"},
    "target": {
      "type": "object", "required": ["scope"],
      "properties": {
        "scope":    {"enum": ["span","trace","session","intent"], "description": "OpenInference scopes + intent"},
        "trace_id": {"type": "string"}, "span_id": {"type": "string"},
        "session_id": {"type": "string"}, "intent_id": {"type": "string"}
      }
    },
    "name":          {"type": "string", "description": "OI annotation.name / Langfuse score name / LangSmith key / gen_ai.evaluation.name"},
    "data_type":     {"enum": ["NUMERIC","CATEGORICAL","BOOLEAN","TEXT","CORRECTION"], "description": "Langfuse score data types"},
    "score":         {"type": "number", "description": "OI annotation.score / gen_ai.evaluation.score.value"},
    "label":         {"type": "string", "description": "OI annotation.label / gen_ai.evaluation.score.label"},
    "explanation":   {"type": "string", "description": "OI annotation.explanation / gen_ai.evaluation.explanation / LangSmith comment"},
    "correction":    {"description": "LangSmith correction: the right answer (string, object, or contentRef)"},
    "annotator_kind":{"enum": ["HUMAN","LLM","CODE"]},
    "annotator":     {"type": "string", "description": "me | agent:verifier | script:eval_gate"},
    "identifier":    {"type": "string", "description": "OI annotation.identifier (stable per name+target, e.g. rubric id)"},
    "implicit":      {"type": "boolean", "description": "true if derived from behaviour (reject, revert, rephrase)"},
    "intent_effect": {"enum": ["none","refine","override","reject"]},
    "agent_did":     {"type": "string"}, "my_correction": {"type": "string"}, "my_reasoning": {"type": "string"},
    "metadata":      {"type": "object"},
    "carrier_span_id": {"type": "string", "description": "post-hoc carrier span (kind feedback_carrier) that links to target"}
  }
}
```

### 5.6 `relation` payload (PROV / OCEL edges not implied by parentage)

```json
{
  "$id": "harness://schema/relation/1.0.0",
  "type": "object",
  "required": ["type", "from", "to"],
  "properties": {
    "type": {"enum": ["used","wasGeneratedBy","wasInvalidatedBy","wasDerivedFrom","wasRevisionOf",
                      "wasInformedBy","actedOnBehalfOf","hadPlan","follows_from","corrects","o2o"]},
    "from": {"type": "string", "description": "span:<trace>/<span> | int_… | file:…@sha256:… | commit:… | fb_…"},
    "to":   {"type": "string"},
    "qualifier": {"type": "string", "description": "OCEL qualifier, e.g. 'reads', 'writes', 'part_of'"},
    "time": {"type": "string", "format": "date-time"}
  }
}
```

### 5.7 `checkpoint` payload

```json
{
  "$id": "harness://schema/checkpoint/1.0.0",
  "type": "object",
  "required": ["chain", "tree_size", "root_hash", "head_hash", "algo"],
  "properties": {
    "chain":     {"type": "string"},
    "tree_size": {"type": "integer", "description": "number of leaves (facts) covered, seq 0..tree_size-1"},
    "root_hash": {"type": "string", "description": "RFC 6962 Merkle root over leaf hashes"},
    "head_hash": {"type": "string", "description": "hash of fact seq tree_size-1"},
    "algo":      {"const": "rfc6962-sha256+jcs"},
    "prev_checkpoint": {"type": ["string","null"]},
    "witness":   {"type": "object", "description": "filled by autocommit after push", "properties": {"git_commit": {"type":"string"}, "remote": {"type":"string"}}}
  }
}
```

---

## 6. Exact attribute names to reuse

Pin: **semantic-conventions-genai schema `gen-ai-dev/1.42.0-dev`** (development; expect renames). Pin: **OpenInference spec @ 38b858d**.

**OTel GenAI (put these on our spans when we export):**

- *Operation and identity:*
  - `gen_ai.operation.name`: `invoke_agent | execute_tool | chat | plan | invoke_workflow | create_agent | retrieval | search_memory…`
  - `gen_ai.provider.name` = `anthropic`. #289 removed it as required from internal `invoke_agent`, so it is optional there.
  - `gen_ai.conversation.id`
  - `gen_ai.agent.name`, `gen_ai.agent.description`
  - `gen_ai.agent.id` is only for **hosted** agents with stable ids; #242 removed it from internal agent spans, so don't use it for subagents (put the Claude `agent_id` in `harness.agent_id`).
  - `gen_ai.workflow.name`
  - `gen_ai.main_agent.id` / `.name` / `.description` is an *entity* (resource), only for stable top-level agents.
- *Tools:*
  - `gen_ai.tool.name`, `gen_ai.tool.call.id`, `gen_ai.tool.type` (`function | extension | datastore`), `gen_ai.tool.description`
  - `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result` (opt-in), `gen_ai.tool.definitions`
- *Skills (#498):* `gen_ai.skill.name`, `gen_ai.skill.description`, `gen_ai.skill.source.uri`, `gen_ai.skill.resource.name`. Span refinements: `gen_ai.execute_tool.load_skill.internal`, `.read_skill_resource.internal`, `.command.internal` (Bash).
- *Model:* `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.response.id`, `gen_ai.response.finish_reasons`, `gen_ai.request.reasoning.level` (new, #258; maps to effort).
- *Usage:*
  - `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.usage.reasoning.output_tokens`
  - `gen_ai.usage.cache_read.input_tokens`, `gen_ai.usage.cache_write.input_tokens`. These were renamed from `cache_creation` (#440) and removed from internal `invoke_agent` (#469); put them on inference spans only.
- *Context:* `gen_ai.conversation.compacted` (bool, new #162; set only `true`). `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.system_instructions` are opt-in content.
- *Prompt versioning (#179):* `gen_ai.prompt.name`, `gen_ai.prompt.version`, `gen_ai.prompt.variable`. Use these for skill or CLAUDE.md versions on turns.
- *Evaluation event:* `gen_ai.evaluation.result` with `gen_ai.evaluation.name`, `gen_ai.evaluation.score.value`, `gen_ai.evaluation.score.label`, `gen_ai.evaluation.explanation`, and `gen_ai.response.id` for correlation. Parent it to the evaluated span.
- *Errors:* `error.type` (core semconv). MCP: `mcp.method.name`, `mcp.session.id`, `mcp.resource.uri`, `mcp.protocol.version`. MCP carries `traceparent` in `params._meta` (#220, SEP-414).
- *Span names:* `invoke_agent {gen_ai.agent.name}`, `execute_tool {gen_ai.tool.name}`, `plan {gen_ai.agent.name}`, `invoke_workflow {gen_ai.workflow.name}`, `{operation} {model}`.

**OpenInference (for Phoenix and other OpenInference-native viewers):**

- *Span kind:* `openinference.span.kind`, one of `AGENT | CHAIN | TOOL | LLM | EVALUATOR | GUARDRAIL | PROMPT | RETRIEVER | RERANKER | EMBEDDING | DECISION`.
- *Ids and I/O:*
  - `session.id`, `user.id`
  - `input.value`, `input.mime_type`, `output.value`, `output.mime_type`
  - `metadata` (JSON string), `tag.tags`
- *Agents and graph:* `agent.name`, `graph.node.id`, `graph.node.name`, `graph.node.parent_id`. The graph-node triple is a cheap way to draw the **intent graph** in Phoenix: set `graph.node.id = harness.intent.id`.
- *Tools:* `tool.name`, `tool.description`, `tool.parameters`, `tool.id`, `tool_call.id`, `tool_call.function.name`, `tool_call.function.arguments`.
- *Prompts:* `llm.prompt_template.template`, `llm.prompt_template.version`, `llm.prompt_template.variables`, `prompt.id`, `prompt.vendor`, `prompt.url`.
- *Feedback:* `annotations.<i>.annotation.{name,score,label,explanation,annotator_kind,identifier,metadata}`, with the scope prefixes `trace.annotations.*` and `session.annotations.*`. `evaluations.*` is the equivalent alias.

**Langfuse OTel ingestion (optional):** `langfuse.observation.type` (`agent|tool|chain|evaluator|guardrail|generation|span|event`), `langfuse.trace.name`, `langfuse.trace.tags`, `langfuse.trace.metadata.<k>`, `langfuse.observation.metadata.<k>`, `langfuse.observation.level`, `langfuse.observation.status_message`, `langfuse.observation.prompt.name` / `.version`, `langfuse.environment`, `langfuse.release`. Scores go through the API: `{name, value, dataType, traceId | observationId | sessionId, comment, metadata, configId, queueId}`.

**Claude Code native (join keys; copy verbatim into `native`):** `session.id`, `prompt.id`, `event.sequence`, `interaction.sequence`, `tool_use_id`, `agent_id`, `parent_agent_id`, `workflow.run_id`, `query_source_safe`, `tool_name_safe`, `bash_command_class`, `bash_argv0`, `request_id`, `client_request_id`, `stop_reason`, `effort`, and on `tool_decision`: `decision`, `source`, `tool_source`.

**Our namespace:** `harness.span.kind`, `harness.activity`, `harness.scope`, `harness.intent.{id,path,binding,confidence,assigned_by,rationale,drift}`, `harness.agent_id`, `harness.cost_usd`, `harness.fact_hash` (the hash of the span_end fact, so an exported span can be checked against the chain).

---

## 7. Process mining on the log

### 7.1 Event classifier (`harness.activity`)

The activity alphabet decides everything. Use a small closed set:

```
user:prompt  user:correction  user:allow  user:reject  user:interrupt  user:edit_file
turn:end:ok  turn:end:error   compact     session:start  session:end
tool:Read  tool:Edit  tool:Write  tool:Grep  tool:Glob  tool:WebSearch  tool:WebFetch
tool:Bash:<bash_command_class>      # vcs, package_manager, test?, other  (CC's own closed list)
tool:mcp:<server>                   # mcp_other if unknown
skill:<name>   subagent:<agent_type>   plan   workflow:<name>
gate:<hook>:<pass|block>   feedback:verification:<pass|fail|needs-human>
```

Leave `llm_request` out by default; it is high-volume and carries no meaning. Keep lifecycle as XES `lifecycle:transition = start|complete` from span_start/end, so `discover_performance_dfg` and `conformance_temporal_profile` get durations and waiting time (`tool.blocked_on_user` = user latency).

### 7.2 OCEL 2.0 projection

| OCEL object type | id | attributes (time-varying → `object_changes`) |
|---|---|---|
| `session` | session_id | scope, permission_mode, host |
| `turn` | prompt_id | correction_candidate, status |
| `intent` | intent_id | kind, **status** (timeline), scope, source |
| `subagent` | agent_id | agent_type, model |
| `skill` | skill name | version |
| `file` | repo-relative path | content hash (changes over time) |
| `commit` | sha | — |
| `feedback` | feedback_id | name, label, score, annotator_kind |

- **E2O qualifiers:** `in_session`, `in_turn`, `serves` (→ intent), `by_agent`, `uses_skill`, `reads` / `writes` (→ file), `creates` (→ commit), `targets` (feedback → span's objects).
- **O2O qualifiers:** `part_of` (turn→session), `refines` / `serves` / `supersedes` (intent→intent), `spawned_by` (subagent→turn), `about` (feedback→intent).
- **e2e:** pm4py's `e2e` table can hold span parent→child and `follows_from`. That is a pm4py extension, so keep it out of the standard JSON when interoperability matters.

```python
# projector sketch: run with python3 -I, reads L1 spans.sqlite
import pandas as pd, pm4py
from pm4py.objects.ocel.obj import OCEL
ev  = pd.DataFrame(rows_events)    # columns: ocel:eid, ocel:activity, ocel:timestamp, + attrs (harness.intent.binding, status, …)
obj = pd.DataFrame(rows_objects)   # ocel:oid, ocel:type, + static attrs
rel = pd.DataFrame(rows_e2o)       # ocel:eid, ocel:activity, ocel:timestamp, ocel:oid, ocel:type, ocel:qualifier
o2o = pd.DataFrame(rows_o2o)       # ocel:oid, ocel:oid_2, ocel:qualifier
chg = pd.DataFrame(rows_changes)   # ocel:oid, ocel:type, ocel:timestamp, ocel:field, <field value col>
ocel = OCEL(events=ev, objects=obj, relations=rel, o2o=o2o, object_changes=chg)
pm4py.write_ocel2_sqlite(ocel, "projections/ocel2.sqlite")   # or write_ocel2_json
```

### 7.3 Analyses (pm4py function names checked against 2.7.23.11)

1. **The user's actual workflows.**
   - `pm4py.discover_ocdfg(ocel)` gives an object-centric DFG across sessions, intents and files at once.
   - Then pick a case notion with `pm4py.ocel_flattening(ocel, "intent")` (or `"session"`, `"turn"`, `"file"`). This returns a classic dataframe with `case:concept:name`, `concept:name`, `time:timestamp`.
   - Run `discover_dfg`, `discover_heuristics_net` (noise-robust, good first view), `discover_process_tree_inductive` / `discover_petri_net_inductive` (sound models, needed for alignments) and `discover_powl` (partial orders, good for parallel fan-out).
   - Split by intent `kind` or `scope` (e.g. `translation/*` vs `code`) before discovering. Mixing them gives spaghetti.
2. **Variants.** `pm4py.get_variants` on the intent-flattened log, top-k per intent kind. A frequent variant that no skill documents is a candidate L2 `workflow` Pattern for `patterns.py`.
3. **Declarative habits.** `pm4py.discover_declare(log, min_support_ratio=…, min_confidence_ratio=…)` and `discover_log_skeleton` mine rules like `response(tool:Edit, tool:Bash:test)` or `precedence(tool:Read, tool:Edit)`. These are human-readable and map directly to encodings (rules or hooks).
4. **Conformance against intent plans** (the point of embedding intent):
   - Each intent's `expected_plan` comes from the skill's procedure or the user's own rules (`declare` list and/or `process_tree`).
   - Run `pm4py.conformance_declare(log_of_that_intent, declare_model)` per case for constraint violations.
   - Run `fitness_alignments(log, net, im, fm)` and `conformance_diagnostics_alignments` for step-level deviations (log moves = extra steps, model moves = skipped steps, e.g. "verify skipped before client deliverable").
   - Run `conformance_temporal_profile` for unusual waits (blocked_on_user spikes).
   - `conformance_ocdfg(ocel, model)` compares object-centric behaviour between weeks.
   - This is the PROV-O "manage expectation failures" use of `prov:Plan`.
5. **Deviation → correction coupling.** Join alignment deviations to `feedback` facts on the same span. A deviation followed by `user:correction` is a *harmful* deviation; a deviation the user never corrected is a candidate update to the plan, because the plan may be wrong rather than the behaviour. Feed both to `pattern_proposed`.
6. **Data-flow edges, not just order.** Before claiming "Edit depends on Grep", require a `used`/`wasGeneratedBy` path over a file entity (content hash). This is TraceCompiler's rule: observed order becomes structure only when data flow supports it.
7. **LLM summaries.** `pm4py.llm.abstract_ocel_ocdfg` / `abstract_variants` produce a text abstraction for the weekly review; give it to a model with `pm4py.llm.anthropic_query` or the harness's own call.

Practical notes:
- Turn-level cases are short and numerous; intent-level cases are long. Use the turn log for tool-habit mining and the intent log for workflow and conformance.
- Fan-out subagents run in parallel, so DFG edges between sibling subagents are noise. Use POWL / inductive miner, which model concurrency, or mine per subagent object.
- Filter `tool:Read`/`Grep` self-loops (`pm4py.filter_*` or collapse runs) before visualizing.

---

## 8. Event sourcing + CQRS specifics

- **Write side:** `hooks/_common.py` gains `append_fact(kind, payload)`. It takes the lock, reads the tail hash, builds the envelope, computes the hash, writes one line, and fsyncs. Hooks must stay under their timeout, so blob writes are content-addressed and idempotent (write if absent).
- **Pairing:** a `span_start` without a `span_end` (crash, kill, interrupt) is closed by the projector as `status:{code:"ERROR","error.type":"incomplete"}` at the next fact time in that trace, never by writing into the past.
- **Projectors are versioned** (`projector: spans@1.2`). A changed projection rule means rebuilding L1 from L0, never migrating L1 in place. The Braintrust `_xact_id` and LangSmith `dotted_order` show the same idea: a total order key separate from wall time. Here `(chain, seq)` is the order key, and `dotted_order`-style paths (`start_ts+span_id` joined by `.`) give a cheap sortable tree key for SQLite.
- **Read models:** `spans` (one row per span with the resolved intent), `intent_versions`, `intent_status_timeline`, `feedback_by_target`, `ocel2.sqlite`, and an optional OTLP export. Phoenix and Langfuse accept OTLP. Export is one-way; nothing reads back from a vendor.

---

## 9. Hash-chaining and integrity

1. **Canonicalize:** RFC 8785 JSON Canonicalization Scheme (sorted keys, ECMAScript number form, UTF-8). Exclude `hash` and `fid` from the hashed body.
2. **Leaf hash:** `hash = "sha256:" + hex(SHA256(0x00 ‖ JCS(envelope')))`. The 0x00 prefix makes leaf hashes identical to RFC 6962 Merkle leaves, so the same values serve both the linear chain and the tree.
3. **Linear chain:**
   - Within a chain, `prev` = the previous fact's `hash`.
   - The first fact of a new month file has `prev` = the last hash of the previous month.
   - The genesis fact has `prev:"genesis"`.
   - This detects deletion, reordering and edits locally, git-commit style.
4. **Concurrency:**
   - Default: one `main` chain per host with `fcntl.flock(LOCK_EX)` on `facts/.lock` around read-tail + append.
   - If lock contention shows up in hook latency, switch to per-writer chains (`chain:"w:<host>:<writer>"`). The checkpoint then commits to all chain heads, a Merkle root over the head hashes sorted by chain id.
   - Multiple Macs: one chain per `host`. Never interleave hosts in one file; `git` merges are then append-only unions with no conflicts.
5. **Merkle checkpoints (CT-style signed tree head without the signature):**
   - Hourly, `scripts/autocommit_data.sh` calls `checkpoint.py`. It computes the RFC 6962 root over the leaf hashes `0..n-1`, using node `H(0x01‖l‖r)` and RFC 6962's split at the largest power of two below n.
   - It appends a `checkpoint` fact, commits, and pushes. The pushed git commit is the *witness* (the git history on GitHub is a second, independently held hash chain).
   - Optional: sign the checkpoint with an SSH key (`ssh-keygen -Y sign`, which git also uses for signed commits) or add a `git notes` entry.
   - Consistency proofs between checkpoints (RFC 6962 §2.1.2) let `verify.py` show that checkpoint k+1 extends checkpoint k without re-reading everything. The `transparency-dev/merkle` Go repo is a reference; a ~60-line Python version is enough here.
6. **Content addressing and redaction:**
   - Prompts, tool inputs and outputs, and diffs go to `blobs/sha256/<2>/<62>` and are referenced by digest. Weave's `name:digest` object refs follow the same idea.
   - The chain covers the digest only, so deleting a blob (a privacy request, or a secret that leaked into a tool output) leaves the chain valid; `verify.py` reports it as "blob missing (redacted)".
   - For `msg-vault` material, use `hmac-sha256:` with a per-machine key kept in the vault. A plain SHA-256 of a short message is guessable by brute force, so it would leak content.
7. **Verification (`scripts/verify_chain.py`):**
   - Recompute every hash and check `prev` links and `seq` continuity.
   - Recompute each checkpoint root and compare it with git history (`git log -p` on the checkpoint line).
   - Report the first bad seq. Run it in the monthly restore drill (`docs/BACKUP.md`) and as a `drill` event.
8. **Threat model, stated honestly:** this detects accidental corruption, rewrites by a buggy agent, and any edit after a push. It does not stop an attacker with write access to both the local repo and the GitHub remote. D4 already keeps agents from editing evals; extend `guard_protected.py` to deny `Edit`/`Write`/`Bash` redirection onto `facts/*.jsonl`, so only `append_fact` writes there.

---

## 10. Worked example (abridged)

The user types "set up the Mac bootstrap; don't touch dotfiles", and Claude spawns an Explore subagent.

```jsonl
{"kind":"intent","payload":{"intent_id":"int_9f3k2m1q0a","version":1,"kind":"task","statement":"Set up the Mac bootstrap","source":"user_stated","status":"active","scope":"code","edges":[{"type":"serves","to":"int_goal_harness"}],"expected_plan":{"skill":"verify","declare":[{"template":"response","a":"tool:Edit","b":"tool:Bash:test"},{"template":"existence","a":"feedback:verification:pass"}]}}}
{"kind":"intent","payload":{"intent_id":"int_c0nstr4int","version":1,"kind":"constraint","statement":"Do not modify dotfiles","source":"user_stated","status":"active","edges":[{"type":"constrains","to":"int_9f3k2m1q0a"}]}}
{"kind":"span_start","payload":{"trace_id":"<sha(session)>","span_id":"<sha(turn:prompt_id)>","parent_span_id":"<root>","kind":"turn","name":"invoke_agent claude-code","native":{"session_id":"…","prompt_id":"…"},"attributes":{"gen_ai.operation.name":"invoke_agent","gen_ai.conversation.id":"…","openinference.span.kind":"AGENT","harness.activity":"user:prompt","harness.intent.id":"int_9f3k2m1q0a","harness.intent.binding":"explicit","harness.intent.confidence":1.0}}}
{"kind":"span_start","payload":{"…":"…","kind":"subagent","name":"invoke_agent Explore","native":{"agent_id":"a1"},"attributes":{"gen_ai.operation.name":"invoke_agent","gen_ai.agent.name":"Explore","harness.intent.id":"int_9f3k2m1q0a","harness.intent.binding":"inherited","harness.activity":"subagent:Explore"}}}
{"kind":"span_start","payload":{"…":"…","kind":"tool","name":"execute_tool Edit","native":{"tool_use_id":"toolu_…"},"attributes":{"gen_ai.operation.name":"execute_tool","gen_ai.tool.name":"Edit","gen_ai.tool.call.id":"toolu_…","gen_ai.tool.type":"function","openinference.span.kind":"TOOL","harness.activity":"tool:Edit","harness.intent.id":"int_9f3k2m1q0a","harness.intent.binding":"inherited"}}}
{"kind":"span_end","payload":{"…":"…","status":{"code":"ERROR","error.type":"permission_denied"},"artifacts":[]}}
{"kind":"feedback","payload":{"feedback_id":"fb_01","target":{"scope":"span","trace_id":"…","span_id":"<edit span>"},"name":"tool_permission","data_type":"BOOLEAN","score":0,"label":"rejected","annotator_kind":"HUMAN","implicit":true,"explanation":"Edit targeted ~/.zshrc","intent_effect":"none"}}
```

The projector shows the Edit span violating `int_c0nstr4int` (via a `writes` E2O to a `file:~/.zshrc` object that the constraint covers). Conformance flags a model move "missing `tool:Bash:test` after `tool:Edit`" if the turn ends without a test.

---

## 11. Migration from Event v0.2 and implementation order

1. **Keep `log/YYYY-MM.jsonl` (v0.2) as is**, and start `facts/YYYY-MM.jsonl` beside it. The projector reads both; v0.2 lines become `legacy_event` facts with derived spans:
   - `prompt` → turn span
   - `correction` → feedback (`CORRECTION`)
   - `label` → `intent` + `intent_assignment` (`relabeled`, authority `labeler`)
   - `verification` → feedback (`verification`)
   - `task` → subagent span
2. **Map v0.2 fields onto the new model:**
   - `intent` → IntentNode.statement
   - `situation` → `intent_situation`
   - `meta` → `meta`
   - `parent_event` → `parent_span_id` / relation
   - `corrects` → relation `corrects` + feedback target
   - `proof` → feedback `metadata.proof` or relation `used`
   - `outcome` → span status + intent status
3. **Hooks to add to `hooks.json`:** PostToolUse, PostToolUseFailure, PermissionDenied, SubagentStart, SubagentStop, StopFailure, TaskCreated / TaskCompleted, and the existing ones. Use `async`/fast paths; each writes one fact. Keep content out of the hook path: write a blob and reference it.
4. **Session default intent:** SessionStart reads HANDOFF.md / tasks.json and emits an `intent` (`source:"imported"`) plus env `HARNESS_INTENT_ID`.
5. **Scripts:**
   - `scripts/project_facts.py` (L0→L1, pm4py OCEL export)
   - `scripts/verify_chain.py`
   - `scripts/checkpoint.py` (called by `autocommit_data.sh`)
   - `scripts/mine_workflows.py` (section 7 analyses, output to the weekly report)
6. **Ontology:** add types `Fact`, `IntentNode`, `IntentAssignment`, `Feedback`, `Checkpoint` to `schema/ontology.yaml` (v0.3) through a reviewed PR, per the ontology header rule.
7. **Optional viewer:** turn on Claude Code beta tracing (`CLAUDE_CODE_ENABLE_TELEMETRY=1`, `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`, `OTEL_TRACES_EXPORTER=otlp`) into a local Phoenix. Our OTLP export adds intent and feedback on top of the native spans, joined by `session.id`, `prompt.id` and `tool_use_id`. The native spans are per-prompt traces (`claude_code.interaction` root), while ours are per-session. Join them via `native.native_traceparent` with an OTel span link, not parentage.

---

## 12. Open questions and risks

- **The GenAI semconv will change.** Many breaking fragments are unreleased (token metric rename, `cache_write`, `agent.id` scope). Keep `gen_ai.*` only in the *export* layer; facts store a `semconv` version and the projector maps.
- **Intent inference quality.** Hook-time intents from a cheap model will often be wrong. Keep `confidence`, let the weekly labeler relabel, and measure the relabel rate as a metric (a high rate means the inference prompt needs work).
- **Privacy.** With `OTEL_LOG_USER_PROMPTS` / `OTEL_LOG_TOOL_CONTENT`, native traces carry content. Point them only at a local Phoenix, never a SaaS backend, for client or NDA scopes (`docs/LOCAL_ONLY.md`).
- **Case-notion choice is a modelling decision.** Discovered "workflows" depend heavily on it. Report which notion each chart uses.
- **pm4py licence is AGPL-3.0** (its `LICENSE` file). Running it locally on personal data is fine. Don't bundle it into anything shipped.
- **Unverified items:** the details of AgentLTL / TraceCompiler / the evidence-tracing survey come from search snippets only (arXiv was unreachable). The OCEL 2.0 JSON field names were taken from pm4py's `ocel20_standard` exporter, not the official schema file, which was unreachable.
