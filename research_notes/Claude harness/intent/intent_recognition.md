# Intent / goal / plan recognition → automatic intent capture in the personal agent log (research notes, 2026-10-16)

Purpose: design an **intent layer** for the harness log (`claude-harness/schema/event.md`, ontology v0.2.0) so that
every user prompt (Korean, English, mixed) and every agent action carries machine-inferred, user-correctable
intent labels at five layers, from life goal down to the purpose of a single tool call.

Harness context read (repo, nothing run): `schema/event.md` (append-only JSONL; `intent/situation/meta` mandatory on
decision/correction/mishap/session_note; fixes via `corrects:` / `label` events with `labels_for:`),
`schema/ontology.yaml` (types `Event`, `Correction`, `Project`, `Task`, `Pattern`; enums `areas`, `language: [ko,en,mixed]`,
`confidence: [high,medium,low]`, pattern ladder `L0..L5`), `hooks/log_event.py` (prompt capture + bilingual regex
`correction_candidate`), `scripts/label_events.py` (weekly haiku labeling → `label` events). No hook logs tool calls
today; agent actions exist only in the session transcript (`transcript_path`).

Verification legend (same as sibling notes): **[V]** read on the primary page in this session; **[S]** search-engine
snippets / secondary pages only, verify before citing numbers; **[K]** from my background knowledge of the literature,
not re-fetched this session; **[?]** my design inference.

**Unreachable this session (DNS `ENOTFOUND` via the proxy):** arxiv.org, huggingface.co, plato.stanford.edu,
api.semanticscholar.org, simonwillison.net, zenml.io. So the Clio paper (arXiv 2412.13678), the NBER/OpenAI paper PDF,
the Don-Yehiya / Liu et al. feedback papers and SEP "Intention" were seen only through search snippets. Reached: anthropic.com
(Clio blog **[V]**). Naming collision warning: the harness already uses `L0..L5` for the *pattern* ladder; the intent
layers below are named **I0..I4** to avoid confusion.

---

## 0. Decisions in one screen (read first)

1. **Five layers, two speeds.** I0 life goal and I1 project objective change slowly and are owned by the user
   (the model proposes, the user confirms). I2 task, I3 prompt intent and I4 action purpose are inferred
   automatically. This follows the BDI split: desires (I0) are not commitments; intentions (I1/I2) are; plans
   decompose (I2→I4). [K: Bratman 1987; Rao & Georgeff 1995]
2. **I3 prompt intent is a tuple, not a single label:** `speech_act` (illocutionary force: what the utterance *does*)
   × `task_type` (what kind of work) × `mode` (how the human collaborates) × `feedback` (how it relates to the previous
   agent turn: backward-looking function). Multi-dimensional tagging is the central lesson of DAMSL and ISO 24617-2:
   one utterance can be both a correction and a new request. [S]
3. **Labels are append-only assertions with provenance** (`rule | model | user`) and `supersedes`, stored as new
   `label` events. The current label = the latest non-superseded assertion with the highest-authority source
   (user > model-with-high-agreement > rule). This matches the harness rule "never edit a past event".
4. **Corrections are the best intent evidence there is.** A correction tells you the previous interpretation was
   wrong and usually says what the intent really was. Every correction produces (a) a relabel of the *agent's*
   interpretation of the earlier prompt, (b) a constraint added to the active task, and (c) a gold training example
   for the labeler. [S: Don-Yehiya et al. 2024 feedback ontology; Liu, Zhang & Choi, EMNLP 2025]
5. **Drift is three different things.** Separate them: *user goal switch* (new task), *user refinement*
   (same task, new constraints; not drift), and *agent drift* (agent actions stop serving the user's intent).
   Detect each with different signals (§5).
6. **Evaluate against the user, not against a model.** Monthly blind relabel of a stratified sample; report
   Cohen's κ per dimension, precision at the auto-accept threshold, calibration, and segmentation error for
   task boundaries. The user's own test-retest agreement is the ceiling (§7).
7. **Privacy by Clio's recipe, scaled down:** summarise before clustering, strip identifiers in labels, keep raw
   text in `harness-data` (private), and only show cluster-level summaries above a minimum size when reports leave
   the private store. [V: Anthropic Clio blog]

---

## 1. Background: what each tradition contributes

### 1.1 Bratman's planning theory of intention → I1/I2 semantics [S/K]
- **Intentions are elements of partial, hierarchical plans** that the agent is committed to executing; they are not
  reducible to beliefs + desires. [S: SEP/UChicago Press summaries; Bratman, *Intention, Plans, and Practical Reason*, 1987]
- Three functional roles (Bratman; formalised by Cohen & Levesque) [S/K]:
  1. **Drive means-end reasoning**: an adopted end makes the agent search for means (our I2→I4 decomposition).
  2. **Filter of admissibility**: new options that conflict with existing intentions are filtered out (in a log:
     a new prompt that conflicts with an active task's constraint is either a correction or a goal switch, never
     silently both).
  3. **Coordination / stability**: intentions resist reconsideration; they persist until achieved, believed
     impossible, or the reason for them is gone.
- **Cohen & Levesque (1990), "Intention is Choice with Commitment"** (*AI* 42): a *persistent goal* P-GOAL p is held
  until the agent believes p is true or will never be true; a *relativised* P-GOAL is also dropped when a stated
  reason q stops holding. [S] → this gives the **termination conditions** for I1/I2 records:
  `achieved | impossible | reason_gone | superseded | abandoned`.
- Rational norms useful as checks: **consistency** (intentions should be co-achievable) and **means-end coherence**
  (an intention needs means planned at the right time). [K] → an I2 task with no I4 actions after N turns is
  "incoherent" (stalled); two active I2 tasks with contradicting constraints are "inconsistent".

### 1.2 BDI agents and intention reconsideration → when to re-infer [S/K]
- Rao & Georgeff, "BDI Agents: From Theory to Practice", ICMAS 1995, pp. 312–319. [S] Beliefs = information state,
  desires = options, intentions = chosen, committed options executed via plan libraries. [K]
- **Kinny & Georgeff (1991)**: *bold* agents (never reconsider) beat *cautious* agents (always reconsider) in static
  worlds and lose in fast-changing ones; Schut & Wooldridge (2001) let the agent choose the reconsideration policy at
  run time. [S]
- **Design consequence [?]:** do not re-infer I1/I2 on every prompt (cautious = expensive, flickering labels). Re-infer
  only on *reconsideration triggers* (§5.2): a declarative/cancel speech act, a correction, a boundary signal, or a
  drift score above threshold. Otherwise inherit the current task (bold).

### 1.3 Speech acts and dialogue-act taxonomies → I3 `speech_act` [S/K]
- **Austin (1962)**: locutionary / illocutionary / perlocutionary act; the illocutionary *force* is what the speaker
  does in saying something (request, promise, warn). [K]
- **Searle (1975/1979) taxonomy**, by illocutionary point, direction of fit and expressed psychological state [S]:
  | class | point | direction of fit | psych. state | prompt example |
  |---|---|---|---|---|
  | assertive | commit to truth | word→world | belief | "The deadline is Friday." |
  | directive | get hearer to act | world→word | want | "Fix the failing test." |
  | commissive | commit self to act | world→word | intention | "I'll review it tonight." |
  | expressive | express attitude | none / presupposed | feeling | "고마워, 완벽해." |
  | declaration | change status by saying | both | — | "From now on, always answer in Korean." / "Cancel that task." |
  For an agent log, **directives dominate**, and declarations are disproportionately important because they create
  standing policies and terminate tasks.
- **DAMSL (Core & Allen 1997)** [S]: *forward-looking* functions (Statement, Influencing-addressee-future-action =
  Action-directive vs Open-option, Info-request, Committing-speaker-future-action = Offer/Commit) and *backward-looking*
  functions (Agreement: accept/reject/maybe, Understanding: acknowledge/repeat-rephrase/completion, Answer,
  Information-relation). An utterance may take several tags. The "can the hearer reply *I can't do that*?" test
  separates directives from statements.
- **ISO 24617-2 (2012; 2nd ed. 2020) / DiAML, from DIT++ (Bunt)** [S]: a dialogue act = communicative function +
  semantic content + **dimension**. Nine dimensions: Task, Auto-Feedback, Allo-Feedback, Turn Management, Time
  Management, Discourse Structuring, Own Communication Management, Partner Communication Management, Social Obligations
  Management (DIT++ adds Contact Management). General-purpose functions include Inform, Propositional/Set/Choice
  Question, Answer, Confirm/Disconfirm, Request, Instruct, Suggest, Offer, Promise, Accept/Decline Request; plus
  **qualifiers** (certainty, conditionality, sentiment) and **relations** (functional dependence, feedback dependence,
  rhetorical). DialogBank holds gold annotations. [S]
- **What to borrow [?]:** (a) multi-dimensionality (Task vs Feedback vs Discourse Structuring are separate fields);
  (b) the *feedback dependence* relation = our `feedback.target_event`; (c) qualifiers → `certainty` and `sentiment`
  fields; (d) a deliberately *reduced* label set (full ISO is too fine for a single-annotator personal log; inter-annotator
  agreement collapses when you have >15 mutually exclusive labels).

### 1.4 Goal recognition / plan recognition as planning → I2 inference from actions [S/K]
- **Ramírez & Geffner 2009 (IJCAI)**: recognise goals using a domain model + off-the-shelf planner instead of a plan
  library; crisp version: goals whose optimal plans are compatible with observations. [S]
- **Ramírez & Geffner 2010 (AAAI, "Probabilistic Plan Recognition Using Off-the-Shelf Classical Planners")**: posterior
  P(G|O) ∝ P(O|G)P(G), with the likelihood a Boltzmann/sigmoid function of the **cost difference**
  Δ(G,O) = c(G, O) − c(G, ¬O) (cheapest plan for G that embeds the observations vs cheapest plan that avoids them);
  smaller Δ → higher probability; two planner calls per goal. Assumes deterministic actions and full initial state;
  struggles with noisy observations. [S]
- Successors (search-snippet level): landmark-based recognisers (Pereira, Oren & Meneguzzi, AAAI 2017), "plan
  recognition as planning revisited" (Sohrabi, Riabov & Udrea, IJCAI 2016), combinations with data-driven models
  (arXiv 2301.05608). [S]
- **Bayesian inverse planning / theory of mind (Baker, Saxe & Tenenbaum, *Cognition* 113(3), 2009)**: infer goals by
  inverting a model of approximately rational planning; formalises Dennett's intentional stance. [S]
- **LLM-era translation [?]:** we have no PDDL model of "the user's work", but the *structure* carries over:
  candidate goals G = active I2 tasks + "new task"; observations O = the prompt and the agent's recent actions;
  P(O|G) ≈ "how naturally does this observation continue a rational plan for G?" scored by an LLM judge (or by
  embedding similarity to the task's centroid as a cheap proxy); P(G) = recency/frequency prior. This is "plan
  recognition as planning" with an LLM as the cost model (§4.3).

### 1.5 Hierarchical task networks → I2→I4 decomposition [S]
- HTN planning (Erol, Hendler & Nau, UMCP 1994; SHOP2, Nau et al., JAIR 2003): **compound tasks** decompose via
  **methods** into partially ordered subtasks until **primitive tasks** (operators) remain. SHOP plans tasks in the
  order they will be executed, so the current state is always known. [S]
- Mapping: I2 task = compound task; *subgoals* = intermediate tasks (`verify tests pass`, `draft email`); I4 action =
  primitive task (a tool call). A recorded I2 task therefore holds a light **task network**: ordered subgoals with
  status, and each I4 action points to the subgoal it serves. This is what makes "action purpose" inferable:
  an action's purpose is its parent in the network. [?]

### 1.6 Intent taxonomies for LLM assistant usage → I3 `task_type` and `mode`
- **Anthropic Clio (Tamkin et al., Dec 2024, arXiv 2412.13678)** [V blog; S paper]: Claude extracts per-conversation
  **facets** (examples given: topic/request, number of turns, language), embeds them, clusters semantically (k-means
  per secondary sources [S]), writes a privacy-preserving title + summary per cluster, then organises clusters into a
  **multi-level hierarchy** browsable by facet. Privacy layers: summarisation instructed to omit private details;
  **minimum unique-user / conversation threshold** per cluster; a final Claude pass checks cluster summaries for
  identifying detail. Validation: correlation r = 0.71 with Trust & Safety classifiers on concerning clusters [V];
  ~94% reconstruction of a synthetic multilingual topic distribution and a 5,000-conversation privacy audit [S].
  Findings on 1M claude.ai conversations: web/mobile app development >10%, education >7%, business strategy ~6%;
  coding, writing, research dominate; notable cross-language differences (e.g., Japanese elder-care) [V/S].
  **Critique:** evaluation partly circular (Claude generates synthetic data, summarises and audits) [S];
  **Cliopatra (arXiv 2603.09781, 2026)** shows crafted "poison" chats can co-cluster with a target and leak private
  details into summaries [S]. → For a personal log the threat is small (one user), but the same rule applies if
  cluster summaries are ever shared.
- **OpenAI/NBER "How People Use ChatGPT" (Chatterji, Cunningham, Deming, Hitzig, Ong, Shan, Wadman; NBER WP 34255,
  Sept 2025)** [S]: automated privacy-preserving classifiers on a representative sample; intent rubric
  **Asking (≈49%) / Doing (≈40%) / Expressing (≈11%)**; topics led by Practical Guidance, Seeking Information, Writing
  (~80% together); ~30% work-related; writing is the top work use and ~2/3 of writing messages *modify user text*
  rather than create new text; work messages skew toward Doing. → `asking|doing|expressing` is a robust, cheap
  top-level I3 field that has been validated at scale; adopt it as `ado`.
- **Anthropic Economic Index (Feb 2025 onward)** [S]: maps conversations to O*NET tasks; splits **automation vs
  augmentation** (57% augmentation at launch) and finer **collaboration patterns**: *directive* (delegate whole task,
  minimal back-and-forth), *feedback loop* (task completed with environment feedback, e.g. pasting errors back),
  *task iteration* (collaborative refinement), *learning* (seek understanding), *validation* (check/improve the user's
  own work) [definitions K; names S]. Jan 2026 report adds "economic primitives" (task complexity, human/AI skill,
  use case…) [S]. → adopt the five patterns as I3/I2 `mode`.
- **TnT-LLM (Microsoft, Wan et al., 2024)** [S]: LLM generates and iteratively refines an intent taxonomy from a sample,
  then distils it into cheap classifiers; applied to Bing Copilot logs; the M365 Copilot Chat study (arXiv 2605.23958)
  merged a TnT-LLM taxonomy learned on **WildChat** with PM-curated intents [S]. → the recipe for growing our
  `task_type` list bottom-up from the user's own log while keeping a curated core.
- **WildChat (1M conversations, 2.5M turns) vs LMSYS-Chat-1M (Arena, evaluation-driven)** [S]: WildChat better reflects
  real needs; LMSYS skews to model testing. Use WildChat-derived taxonomies as the external reference when mapping.

### 1.7 Implicit feedback as intent evidence [S]
- **Don-Yehiya et al. (2024)** ontology, applied to WildChat + LMSYS by **Liu, Zhang & Choi (EMNLP 2025, "User Feedback
  in Human-LLM Dialogues: A Lens to Understand Users But Noisy as a Learning Signal")**: positive feedback vs negative
  feedback split into **Rephrasing**, **Make Aware without Correction**, **Make Aware with Correction**, **Ask for
  Clarification**. Findings: feedback is informative about users but noisy as a reward; helps on short questions
  (MT-Bench) not on long ones (WildBench). [S]
- **WildReward (arXiv 2602.08829)**: ~82% of follow-up turns carry no explicit feedback; unjustified negative feedback
  (e.g., after a correct refusal) is common. [S] → treat feedback as *evidence with a reliability weight*, never as
  ground truth; absence of feedback ≠ acceptance.
- Shaikh et al. (2025) grounding acts ("Reformulations" ≈ Rephrasing). [S]
- Agent-log-specific signals [?/K]: **acceptance** = user proceeds to next subgoal / commits / says "ㄱㄱ", "좋아",
  "진행해", "lgtm"; **abandonment** = session ends or switches task with the subgoal open; **undo** = user reverts files,
  `git checkout`, or says "되돌려"; **interrupt** = user presses Esc / stops the agent mid-turn (Claude Code exposes
  interrupts in the transcript); **re-ask** = near-duplicate prompt (cosine > 0.85) within the same task.

### 1.8 Theory of mind for agents [S]
- Benchmarks show LLMs still miss implied intent: IntInst (NAACL Findings 2025, pick the intended instruction among
  four), Instruction Inference / Tomcat (arXiv 2507.02935), "Beyond Words" epistemic divergence in user–agent
  interaction (arXiv 2602.13832), CLAMBER (ACL 2024, ambiguity/clarification), ToMBench (ACL 2024). [S]
- "The Severance Problem: LLMs are Unaware of the Person Beyond the Prompt" (arXiv 2607.14250) [S, title only] — the
  motivating gap for I0/I1: the agent sees the prompt, not the life/project it serves. The intent layer's job is to
  bring I0–I2 context into every new session cheaply.

### 1.9 Jobs-To-Be-Done → wording of I1/I2 [S]
- JTBD (Christensen; job stories by Klement): describe a goal as progress in a situation, not as a feature request:
  **"When I [situation], I want to [motivation], so I can [outcome]."** Jobs have **functional, emotional, social**
  dimensions, and a **job altitude** (too broad vs too narrow). "Jobs are stable; solutions change." [S]
- Use: I1 and I2 records carry a `job_story` field. It keeps the "so I can" (the *why*) that bare task names lose,
  and the situation clause maps onto the harness's existing `situation` field.

### 1.10 Intent / goal drift [S]
- Wang et al., "Detecting Intent Drift in Continuous Conversation via Temporal Transition Accumulation", ICDM 2025
  [S, citation only]. Arike et al., "Evaluating Goal Drift in Language Model Agents", AIES 2025: most agents drift
  substantially under goal-switching pressure [S]. "Drift No More? Context Equilibria in Multi-Turn LLM Interactions"
  (arXiv 2510.07777): drift reaches equilibria rather than growing without bound [S]. DeepContext (arXiv 2602.16935):
  stateful "intent distance" between user intent and agent actions [S]. AgentLAB (arXiv 2602.16901): adversarial
  *objective drifting* via individually benign injections [S]. Practitioner note (ARMO): drift shows up in chains of
  actions, not single-step anomaly scores [S].
- Classical change-point tools apply directly to a stream of prompt embeddings: Bayesian online change-point detection
  (Adams & MacKay 2007), CUSUM. Topic segmentation metrics: Pk (Beeferman et al. 1999), WindowDiff (Pevzner & Hearst
  2002). [K]

---

## 2. Recommended intent ontology (I0–I4)

```
I0  Life goal / domain        (desire-level; user-owned; months–years)     e.g. "Build a sustainable freelance career in KO↔EN translation + AI work"
 └─ I1  Project objective      (intention; committed; weeks–months)       e.g. "Get 3 paid annotation contracts by Dec" ; "Personal Claude harness v1"
     └─ I2  Task               (HTN compound task + job story; hours–days) e.g. "Design the automatic intent-capture layer for the log"
         ├─ subgoals           (task network nodes, ordered, with status)   e.g. "survey literature" → "draft ontology" → "write schemas" → "verify"
         └─ I3  Prompt intent  (per user turn; tuple)                       speech_act × ado × task_type × mode × feedback
             └─ I4  Action purpose (per agent tool call)                    means-end role + serves_subgoal + on/off-intent
```

| layer | BDI analogue | HTN analogue | changes when | owner / inference | where stored |
|---|---|---|---|---|---|
| I0 life goal | desire | — | user declares; quarterly review | user-curated; model proposes from I1 clusters | `global/intent/goals.yaml` (repo, reviewed) |
| I1 project objective | future-directed intention (P-GOAL) | top-level task | declaration, achievement, abandonment | model links I2→I1; new I1 only on user confirm | extend `Project.intent` + `intent_node` events |
| I2 task | present intention + partial plan | compound task + methods | boundary signal, explicit switch, completion | automatic (online), reconsidered on triggers | `intent_node` events (`level: I2`) |
| I3 prompt intent | communicative act toward the agent | — (it *edits* the plan) | every prompt | automatic (rule + cheap model at write time) | `label` event `labels_for: <prompt evt>` |
| I4 action purpose | means-end step | primitive task | every tool call | automatic, batch from transcript | `label` events or sidecar `actions/YYYY-MM.jsonl` |

Cross-cutting fields on every node: `scope` (existing grammar `global | <area> | <area>/<project>`), `language`
(`ko|en|mixed`), `status`, `confidence`, `provenance`, `supersedes`.

### 2.1 Status lifecycle for I1/I2 (from Cohen & Levesque termination conditions)
`proposed → active → (suspended ↔ active) → achieved | abandoned | impossible | superseded | reason_gone`
- `suspended`: user switched away without closing it (Bratman: intention retained, not being executed).
- `superseded`: replaced by a re-scoped version (keep the link; this is how "intent changed" is represented).
- Map to the existing `project_status` enum for I1: `active, paused(=suspended), completed(=achieved), cancelled(=abandoned), archived`.

---

## 3. Label taxonomy (bilingual-ready)

Each label has a stable ASCII id (used in data), an English and Korean display name, a definition, and cue lists in
both languages. Korean illocution is largely carried by **sentence-final endings**; those are listed as cues.

### 3.1 I3 `speech_act` (one primary + optional secondary; reduced Searle/DAMSL/ISO)

| id | EN | KO | definition (test) | KO cues | EN cues | ISO 24617-2 / DAMSL map |
|---|---|---|---|---|---|---|
| `request.action` | Request action | 실행 요청 | asks the agent to *do* something in the world; agent could reply "I can't do that" | -해줘, -해 주세요, -해라, -하자, -ㄹ래?, 부탁 | imperative verb, "please", "can you", "let's" | Task: Request/Instruct; DAMSL Action-directive |
| `request.info` | Ask / question | 질문 | asks for information or explanation; satisfied by an answer, not a change | -니?, -나요?, -어?, -ㄹ까?, 뭐, 왜, 어떻게, 알려줘 | wh-words, "?", "explain", "what is" | Set/Prop/Choice Question; Info-request |
| `request.option` | Ask for options / advice | 의견·제안 요청 | asks the agent to propose alternatives or recommend; user keeps the decision | 어떻게 생각해, 추천해줘, 뭐가 나아 | "should I", "what would you recommend", "options" | Suggest-request; Open-option |
| `inform.context` | Provide context | 정보 제공 | states facts, constraints, materials for the task without asking for action | -이야, -거든, 참고로, 여기 있어 | "FYI", "here is", "the X is Y" | Inform; DAMSL Statement-assert |
| `constrain` | Set constraint | 제약 지정 | narrows *how* the current task must be done (scope, format, tool, style) | -로 해줘, -만, -하지 마, 꼭, 반드시 | "only", "don't", "must", "use X" | Instruct + conditionality qualifier |
| `declare.policy` | Declare standing policy | 규칙 선언 | sets a rule beyond the current task ("from now on") | 앞으로, 항상, 이제부터, 절대 | "from now on", "always", "never" | Declaration (Searle); Discourse Structuring |
| `declare.goal` | Declare goal | 목표 선언 | announces a new or re-scoped objective (I1/I2) | 목표는, -하려고 해, 이번 주에 | "my goal is", "I want to", "the plan is" | Commissive/Inform about own intention |
| `declare.close` | Close / cancel | 종료·취소 | ends, cancels or pauses a task | 됐어, 그만, 중단, 취소, 나중에 하자 | "stop", "cancel", "never mind", "done", "park this" | Discourse Structuring (closing); Decline |
| `commit.self` | User commitment | 사용자 약속 | user commits to do something themselves (hand-off point) | 내가 할게, 나중에 확인할게 | "I'll do", "I will check" | Commissive; Promise |
| `feedback` | Feedback (see 3.4) | 피드백 | evaluates the previous agent turn; details in `feedback.type` | — | — | Allo-Feedback (positive/negative) |
| `answer` | Answer agent's question | 답변 | responds to a question/permission request from the agent | 응, 네, 1번, 그걸로 | "yes", "option B", "go with X" | Answer / Confirm / Disconfirm |
| `continue` | Continue / proceed | 계속 | turn-management only: "go on" with no new content | 계속, ㄱㄱ, 진행해, 다음 | "continue", "go", "next", "proceed" | Turn Management / Auto-Feedback |
| `express` | Express attitude | 감정 표현 | thanks, frustration, praise, social talk not about the task | 고마워, 짜증나, 대박, ㅋㅋ | "thanks", "ugh", "nice" | Social Obligations Mgmt; Searle expressive |

Rules: a prompt usually has one *primary* act (the one that determines what the agent must do next) and may have a
*secondary* (e.g. `feedback` + `request.action` in "아니 그거 말고 Gmail부터 해줘"). Long task specs (> 400 chars, as in
`log_event.py`) default to `request.action` + `inform.context` with `constrain` sub-items extracted into a list.

### 3.2 I3 `ado` (OpenAI/NBER-compatible top level)
`asking` (seek information/advice to decide) · `doing` (get output produced or an action performed) · `expressing`
(neither; reflection, venting, social). KO: 묻기 / 시키기 / 표현하기. Derived: `request.info|request.option → asking`;
`request.action|constrain|continue|answer → doing` (when inside a doing task); `express → expressing`.

### 3.3 I3/I2 `task_type` (curated core; grow bottom-up with TnT-LLM-style proposals)
Two-level ids `domain.kind`. Domains mirror harness `areas` where possible.

| id | EN / KO | definition |
|---|---|---|
| `code.build` | Build feature / 기능 구현 | create new code or config that adds capability |
| `code.debug` | Debug / 디버깅 | find and fix a defect from an error or symptom |
| `code.refactor` | Refactor / 리팩터링 | change structure without changing behaviour |
| `code.review` | Review / 코드 리뷰 | assess code for bugs/quality without (yet) changing it |
| `code.ops` | Setup & ops / 환경·운영 | install, configure, deploy, permissions, CI, hooks |
| `research.lookup` | Fact lookup / 사실 확인 | find a specific fact, doc, or reference |
| `research.synthesis` | Research synthesis / 리서치 종합 | gather multiple sources and produce a structured report |
| `writing.draft` | Draft text / 초안 작성 | produce new prose (email, doc, post) |
| `writing.edit` | Edit text / 글 수정 | improve, shorten, re-register the user's own text (NBER: ~2/3 of writing) |
| `translate` | Translate / 번역 | KO↔EN (or other) translation, incl. localisation and glossary |
| `annotate` | Annotation work / 데이터 라벨링 | AI-training/annotation task execution or QA |
| `data.analysis` | Data analysis / 데이터 분석 | compute, chart, query, inspect data |
| `comms.manage` | Communications / 메시지 관리 | triage inbox, draft replies, track threads/applications |
| `plan.decide` | Plan & decide / 계획·결정 | choose among options, prioritise, schedule |
| `learn.explain` | Learn / 학습 | understand a concept or tool |
| `create.visual` | Visual/creative / 시각 작업 | art, design, palette, image tasks |
| `admin.personal` | Personal admin / 개인 행정 | finances, invoices, forms, calendar |
| `meta.harness` | Agent/harness meta / 하네스 개선 | configure or improve the agent system itself (skills, hooks, memory) |
| `other` | Other / 기타 | none fits; triggers taxonomy proposal after N occurrences |

### 3.4 I3 `feedback.type` (backward-looking; Don-Yehiya/Liu ontology + agent-log extensions)

| id | EN / KO | definition | effect on intent state (§6) |
|---|---|---|---|
| `none` | none / 없음 | no evaluation of the previous turn (the ~82% case) | none (do **not** infer acceptance) |
| `accept` | accept / 수락 | explicit approval or proceeding to the next subgoal | close current subgoal as achieved; raise confidence of prior I3 interpretation |
| `praise` | praise / 칭찬 | positive evaluation beyond acceptance | as accept + style evidence |
| `rephrase` | rephrase / 재진술 | same request reworded because the response missed | prior interpretation wrong; relabel prior prompt's `interpreted_intent` |
| `aware_no_fix` | flag error / 오류 지적 | says the result is wrong without saying how | mark prior action/turn `outcome: failed`; ask-for-clarification trigger |
| `aware_with_fix` | correct / 수정 지시 | says it is wrong *and* how to fix it | add constraint to I2; relabel; gold example |
| `clarify_request` | ask for clarification / 설명 요구 | wants missing information in the response | answer gap, not intent change |
| `reject` | reject / 거절 | declines a proposal or plan | drop proposed subgoal(s) |
| `undo` | undo / 되돌리기 | asks to revert an action | mark actions reverted; subgoal reopened |
| `interrupt` | interrupt / 중단 | user stopped the agent mid-turn (transcript signal) | strong agent-drift evidence for the in-flight actions |
| `scope_change` | re-scope / 범위 변경 | same goal, but bigger/smaller/different deliverable | new I2 version `supersedes` old |

`feedback.target_event` = id of the agent turn (or action) being evaluated (ISO *feedback dependence*).

### 3.5 I3/I2 `mode` (Anthropic Economic Index collaboration patterns)
`directive` 위임형 (hand off whole task) · `feedback_loop` 피드백 루프형 (agent iterates on environment/user-pasted feedback
such as errors) · `task_iteration` 반복 다듬기형 (co-refining an artefact turn by turn) · `learning` 학습형 · `validation`
검증형 (check the user's own work). I2 `mode` = majority of its I3 modes; useful for "automation vs augmentation"
reporting per project.

### 3.6 I4 `action.purpose` (means-end role of a tool call)

| id | EN / KO | definition | typical tools |
|---|---|---|---|
| `orient` | orient / 파악 | read/explore to build beliefs about state | Read, Glob, Grep, ls, git status |
| `gather` | gather evidence / 자료 수집 | fetch external information | WebSearch, WebFetch, connector reads |
| `plan` | plan / 계획 | write plan/todos, decompose | TodoWrite, plan files |
| `produce` | produce / 산출 | create or modify the deliverable | Write, Edit, NotebookEdit, create_draft |
| `execute` | execute / 실행 | run code/commands to make something happen | Bash (build, install, run) |
| `verify` | verify / 검증 | check a postcondition (tests, lint, diff, re-read) | pytest, schema_check, git diff |
| `communicate` | communicate / 전달 | deliver to the user or others | publish, send_message, PR, email send |
| `delegate` | delegate / 위임 | spawn subagent / session | Task/Agent, create_session |
| `recover` | recover / 복구 | respond to an error, retry, workaround | Bash after a failure, retries |
| `housekeep` | housekeeping / 정리 | logging, memory, cleanup not serving the deliverable | log writes, temp cleanup |

Plus: `serves_subgoal` (id in the I2 task network), `on_intent` ∈ `on | tangential | off | unknown`, and
`side_effect_risk` ∈ `none | reversible | irreversible` (sends, deletes, pushes).

### 3.7 I1/I0 labels
- I1 `objective_kind`: `deliver` (client/output), `acquire` (job, contract, money), `build` (system/tool), `learn`,
  `maintain` (recurring upkeep), `explore` (open-ended). I1 also carries `area`, `deadline`, `success_criteria`
  (Bratman: the end against which means are checked), `job_story`.
- I0 `life_domain`: the harness `areas` (translation, annotation, job-search, art, code, research, personal) plus
  free-text `aspiration`. JTBD dimensions `functional|emotional|social` as optional tags.

---

## 4. How to infer each layer automatically

### 4.1 Pipeline overview [?]

| stage | when | model | input | output |
|---|---|---|---|---|
| S1 rule tagger | `UserPromptSubmit` hook (exists: `hooks/log_event.py`) | regex (KO+EN) | prompt | `correction_candidate` (exists), plus new `speech_act_hint`, `declare_hint`, `continue_hint`, `language` |
| S2 online I3 labeler | async right after the prompt (background, never blocks) or at session end | haiku-class | prompt, previous agent turn summary (≤ 600 chars), active I2 card | I3 tuple + `task_link` (continue/switch/new) |
| S3 action extractor | session end / `PostToolUse` hook (new, optional) | deterministic + haiku for linking | transcript tool calls | I4 records |
| S4 task segmenter + namer | session end | sonnet-class | ordered I3 + I4 + boundary features | I2 nodes, task network, boundaries |
| S5 project linker | nightly / weekly (`label_events.py` pass) | sonnet-class + embeddings | I2 cards, `Project` registry, cwd/scope | I2→I1 links; proposed new I1 |
| S6 goal proposer | monthly | opus/sonnet + Clio-style clustering | I1 history | proposed I0 changes for user review |

Rationale: write-time stages are cheap and local; expensive whole-session reasoning happens once per session; slow
layers (I1/I0) are batch and gated by the user — this is the bold/cautious trade-off from §1.2.

### 4.2 Signals per layer

| layer | strongest signals | weaker signals |
|---|---|---|
| I3 | sentence-final ending (KO) / mood (EN); explicit markers (앞으로, 말고, ㄱㄱ, "from now on"); whether the previous agent turn asked a question; interrupt flag | punctuation, length, emoji/ㅋㅋ |
| I4 | tool name + args (deterministic map), preceding error, file path vs task network nodes | agent's own stated rationale in text (useful but self-reported) |
| I2 | explicit declarations; cwd/repo/scope change; new entities/files; time gap > 45 min [?]; embedding distance to task centroid; `/clear`, new session | topic words, mode change |
| I1 | `scope` grammar (`area/project`), cwd → project mapping, `Project` registry, recurring entities (client names, platform), deadlines mentioned | similarity to past I2 under each I1 |
| I0 | user declarations; I1 clusters over months; time share per area | sentiment/emphasis |

### 4.3 PRP-lite: plan-recognition-as-planning with an LLM cost model (I2 linking) [?]
For prompt (or action window) O and candidate goals G ∈ {active I2s, suspended I2s in same scope, NEW}:

```
P(G | O) ∝ P(O | G) · P(G)
P(G)      = softmax(β_recency · recency(G) + β_scope · same_scope(G) + β_freq · log(1+n_events(G)))
P(O | G)  ≈ σ(−α · Δ̂(G,O))     # Ramírez–Geffner form
Δ̂(G,O)   = LLM-judged "extra effort/detour" if O is part of a rational plan for G (0 = natural next step … 4 = unrelated)
            cheap proxy: Δ̂ = k · (1 − cos(emb(O), centroid(G)))
P(O|NEW)  = constant floor τ (calibrated so that ~the user's real switch rate is reproduced)
```
Decision: link to argmax if its posterior ≥ 0.6 and margin over second ≥ 0.2; else `task_link: uncertain` (resolved
at S4 with full-session context). Report the posterior as the confidence.

### 4.4 Model prompts (drop-in; JSON-only output, matching `label_events.py` style)

**P-I3 (online prompt-intent labeler, haiku):**
```
You label ONE user prompt from a personal Claude Code work log. Prompts may be Korean, English or mixed.
Input JSON: {"prompt": ..., "prev_agent_turn": "<summary of what the agent just did/said>",
             "agent_asked_question": true|false, "interrupted": true|false,
             "active_task": {"id","title","job_story","subgoals":[{"id","title","status"}],"constraints":[...]},
             "rule_hints": {"speech_act_hint":..., "correction_candidate":..., "patterns":[...]}}
Output exactly one JSON object:
{"speech_act": {"primary": <one of: request.action, request.info, request.option, inform.context, constrain,
                declare.policy, declare.goal, declare.close, commit.self, feedback, answer, continue, express>,
                "secondary": <same set or null>},
 "ado": "asking|doing|expressing",
 "task_type": "<domain.kind from the list, or other:<proposed-id>>",
 "mode": "directive|feedback_loop|task_iteration|learning|validation",
 "feedback": {"type": "<none|accept|praise|rephrase|aware_no_fix|aware_with_fix|clarify_request|reject|undo|interrupt|scope_change>",
              "evidence": "<quoted words from the prompt, or ''>"},
 "constraints_added": ["<normalized constraint, English>", ...],
 "task_link": "continue|new|switch_to:<task id>|uncertain",
 "intent_summary_en": "<why the user asked this, <= 20 words, no names/emails/numbers>",
 "intent_summary_ko": "<같은 내용, 20단어 이내>",
 "confidence": 0.0-1.0}
Rules: Korean sentence endings decide force (-해줘 request, -니?/-나요?/-ㄹ까? question, 앞으로/항상 policy,
말고/아니 + instruction = aware_with_fix + request.action). If the agent just asked a question and the prompt is
short (응/네/yes/1번), speech_act=answer. "계속/ㄱㄱ/continue" alone = continue, feedback=accept only if the agent
had finished a subgoal. Absence of complaint is feedback "none", never "accept". Quote evidence, do not invent it.
```

**P-I4 (action purpose, haiku, batched per session):**
```
Given the task network {subgoals:[{id,title}]} and a list of tool calls [{i, tool, args_summary, result_status,
prev_error}], output one JSON line per call: {"i":..., "purpose": "<orient|gather|plan|produce|execute|verify|
communicate|delegate|recover|housekeep>", "serves_subgoal": "<id|null>", "on_intent": "on|tangential|off|unknown",
"side_effect_risk": "none|reversible|irreversible", "confidence": 0-1}. Use the deterministic default for the tool
unless args clearly indicate otherwise (e.g. Bash running pytest = verify). Mark "off" only when the call serves no
subgoal and no stated user constraint.
```

**P-I2 (task segmentation + naming, sonnet, per session):**
```
Input: the session's prompts with their I3 labels, action summaries, timestamps, cwd changes, and the list of
active/suspended tasks in this scope. Output:
{"segments": [{"task_id": "<existing id or NEW>", "start_event", "end_event",
   "title_en", "title_ko", "job_story": "When ..., I want to ..., so I can ...",
   "task_type", "mode", "subgoals": [{"id","title","status": "open|achieved|dropped"}],
   "constraints": [...], "status": "active|suspended|achieved|abandoned|superseded",
   "supersedes": "<task id|null>", "boundary_reason": "<declare|topic|cwd|gap|new_session|correction_scope_change>",
   "confidence": 0-1}]}
A refinement (new constraint on the same deliverable) is NOT a new task. A new deliverable is. Prefer continuing an
existing task when the user is still serving the same "so I can".
```

**P-I1 (project linking, weekly):** given I2 cards (title, job story, scope, entities) and the `Project` registry
(id, intent, success criteria), output `{"task_id","project_id|PROPOSE_NEW","fit":0-1,"why"}`. New projects are only
*proposed* (`status: proposed`), shown in the weekly review, and become `active` on user confirmation.

### 4.5 Confidence: how to make the number mean something [K/?]
- Verbalised LLM confidence alone is poorly calibrated. Combine:
  `conf = w1·rule_agreement + w2·self_consistency + w3·verbal_conf` where self-consistency = share of k=3 samples
  (temperature 0.7, or 3 cheap prompt variants) agreeing on the label; rule_agreement = 1 if S1 hint agrees, 0.5 if
  no hint, 0 if it disagrees.
- Fit w and the bands on the monthly gold set (§7) with isotonic/Platt scaling; publish the reliability diagram.
- Bands → harness enum `confidence`: `high ≥ 0.8` (auto-accept, used downstream), `medium 0.5–0.8` (used but flagged
  "tentative"; eligible for review sampling), `low < 0.5` (stored as `unknown` + candidate list; always queued for
  review if it is a correction or declaration).
- Never auto-commit I0/I1 changes regardless of confidence.

---

## 5. Detecting intent change and drift mid-session

### 5.1 Three phenomena, three detectors

| phenomenon | definition | detector | action |
|---|---|---|---|
| **Goal switch** (user) | user starts serving a different "so I can" | explicit `declare.goal/close` or `task_link: new/switch`; change-point on prompt embeddings; cwd/scope change; time gap | close/suspend old I2, open new; ask nothing (bold) unless conf < 0.5 |
| **Refinement / re-scope** (user) | same goal, new constraints or bigger/smaller deliverable | `constrain`, `aware_with_fix`, `scope_change`; low embedding distance but new constraint | append constraints; for `scope_change` create I2 v2 `supersedes` v1 |
| **Agent drift** | agent's actions stop serving the current intent | rolling share of I4 `on_intent ∈ {off,tangential}`; actions touching paths/entities outside the task network; `interrupt`; `aware_no_fix` after a long autonomous run; constraint-violation checks | write `drift_event`; in real time, a hook can surface a warning; review in weekly report |

### 5.2 Reconsideration triggers (when S2/S4 must re-evaluate I2 instead of inheriting)
1. speech act ∈ {`declare.goal`, `declare.close`, `declare.policy`} or feedback ∈ {`scope_change`, `reject`, `undo`, `interrupt`}
2. `correction_candidate` with confidence ≥ 0.8 (existing hook field)
3. change-point posterior ≥ 0.5 on the prompt-embedding stream (BOCPD with hazard 1/8 prompts [?]) **or**
   cosine(prompt, task centroid) < 0.35 for 2 consecutive prompts [?, tune on data]
4. cwd/repo/scope change, `/clear`, new session, or gap > 45 min
5. agent-drift score D ≥ 0.5 (below)

### 5.3 Agent-drift score [?]
Over a sliding window of the last W = 8 actions in a turn:
```
D = 0.5 · share(on_intent = off) + 0.25 · share(on_intent = tangential)
  + 0.15 · [any irreversible action not covered by a subgoal]
  + 0.10 · [constraint violated: e.g. edited a file the user excluded, used a tool the user banned]
```
Alert at D ≥ 0.5 (or immediately for an uncovered irreversible action). Following ARMO/DeepContext: score chains,
not single calls; a single exploratory `orient` read is never drift.

### 5.4 Distinguishing "rephrase" from "new task" (most frequent confusion)
- Rephrase: high similarity to the previous *user* prompt (cos > 0.8) **and** previous agent turn not accepted.
- Refinement: adds a constraint; deliverable unchanged.
- New task: deliverable noun phrase changes (e.g., "Gmail pipeline" → "Lark export"), or "so I can" changes.
The P-I2 prompt asks the model to state the deliverable and the "so I can" explicitly for both sides before deciding.

---

## 6. How corrections update intent labels

Corrections are handled as **event-sourced belief revision**: new assertions supersede old ones, nothing is edited.

1. **Detect** (S1 regex → S2 `feedback.type` ∈ {rephrase, aware_no_fix, aware_with_fix, reject, undo, interrupt, scope_change}).
2. **Locate target**: `feedback.target_event` = the agent turn being corrected; walk back to the prompt it answered
   (`prompt_evt`) and the actions it ran.
3. **Revise, by type:**

| feedback | relabel prior prompt's `interpreted_intent`? | I2 update | I4 update | training data |
|---|---|---|---|---|
| `rephrase` | yes: write `label` with `interpretation_status: misread` and the corrected intent (from the rephrase) | none (same task) | none | (prompt, wrong interpretation, right interpretation) pair |
| `aware_with_fix` | yes if the fix shows a misread; else `executed_badly` | append constraint (normalised, bilingual) with `source: correction` | mark served actions `outcome: failed` | constraint → Preference candidate (existing `Pattern` ladder) |
| `aware_no_fix` | `unclear` (queue for review) | subgoal back to `open` | `outcome: failed` | review queue |
| `reject` | — | dropped subgoal(s) `status: dropped` | — | — |
| `undo` | — | subgoal `open` | `outcome: reverted` | — |
| `interrupt` | `unclear` | — | in-flight actions `on_intent: off?` pending review | drift example |
| `scope_change` | — | new I2 version, `supersedes` old | — | — |
| user relabel in review | **gold**; supersedes all model labels | as stated | as stated | few-shot memory, eval set |

4. **Authority order** for the current label: `user` > `model` with conf ≥ 0.8 > `model` < 0.8 > `rule`. A later
   *model* label never supersedes a *user* label.
5. **Propagate**: a user relabel of one I3 record updates (a) its siblings that the model labeled with the same rule
   and conf < 0.8 in the same session (marked `propagated_from`), and (b) the few-shot example store used by P-I3
   (max 40 examples, stratified by label, newest win). This is the cheap way to "learn" without fine-tuning.
6. **Policy escalation**: the same constraint appearing in ≥ 3 corrections across ≥ 2 tasks becomes a
   `pattern_proposed` event (`pattern_kind: correction`) — this hooks into the existing pattern ladder instead of
   inventing a new mechanism.

---

## 7. Evaluation

### 7.1 Gold data with the user as annotator
- **Sample monthly**: 60 prompts + 60 actions + all task boundaries of 5 sessions, stratified by language (ko/en/mixed),
  `speech_act`, confidence band, and over-sampling corrections and declarations (rare, high-impact).
- **Blind first**: the user labels without seeing the model label (a small review page or CLI), then sees the model
  label and may adjust (the adjusted value is gold; the blind value is for agreement). Showing the model label first
  inflates agreement (anchoring) [K].
- **Test-retest ceiling**: 15 items from the month before are re-shown to the user unannounced; user-vs-self κ is
  the realistic ceiling for model-vs-user κ.
- **Guidelines**: this file's §3 tables are the codebook; ambiguous cases get added as worked examples.

### 7.2 Metrics

| what | metric | target to aim for [?] |
|---|---|---|
| I3 `speech_act` primary | Cohen's κ (model vs user blind); per-class precision/recall; confusion matrix | κ ≥ 0.70 (DA-tagging literature reports human–human κ ≈ 0.6–0.8 on reduced sets [K]) |
| I3 `ado` | κ | ≥ 0.80 |
| I3 `task_type` | hierarchical F1 (credit for correct `domain` even if `kind` wrong); κ at domain level | domain κ ≥ 0.80 |
| I3 `feedback.type` | precision/recall of "any negative feedback"; κ over types | recall ≥ 0.85 for corrections (cost of missing one is high) |
| multi-label (`secondary`, constraints) | Krippendorff's α (MASI distance) | ≥ 0.6 |
| I4 `purpose` | accuracy vs user; `on_intent=off` precision | off-precision ≥ 0.8 (false alarms erode trust) |
| I2 boundaries | Pk and WindowDiff vs user segmentation; boundary F1 with ±1-turn tolerance | WindowDiff ≤ 0.25 |
| I2→I1 linking | precision@1 | ≥ 0.9 |
| drift events | event-level precision/recall (±1 turn) | precision ≥ 0.7 |
| intent summaries | user rating 1–3 ("captures why I asked"); pairwise vs previous labeler version | mean ≥ 2.5 |
| calibration | ECE over confidence bands; precision within `high` band | `high`-band precision ≥ 0.9 |
| coverage | share of records with `confidence = high` | report, do not optimise alone |
| bilingual parity | every metric split by `language`; gap ko vs en | gap ≤ 0.05 κ |

### 7.3 Synthetic pre-checks (Clio-style)
Before relying on a new labeler version: generate 100 synthetic sessions with known I2 segments and injected
corrections (KO, EN, code-switched), check reconstruction (as Clio did for topic distributions), and keep them as a
regression eval in `evals/` (respect `hooks/guard_protected.py`). Caveat from the Clio critique: the generator and the
labeler should be different models or prompt families, or the test is circular.

---

## 8. Concrete JSON schemas (draft 2020-12)

### 8.1 `IntentLabel` (I3) — written as a `label` event (`labels_for: <prompt evt id>`)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "harness/intent/IntentLabel.v0.1",
  "type": "object",
  "required": ["labels_for", "level", "speech_act", "ado", "task_type", "feedback", "provenance", "confidence"],
  "properties": {
    "labels_for": {"type": "string", "pattern": "^evt_"},
    "level": {"const": "I3"},
    "language": {"enum": ["ko", "en", "mixed"]},
    "speech_act": {
      "type": "object", "required": ["primary"],
      "properties": {
        "primary": {"$ref": "#/$defs/speech_act"},
        "secondary": {"oneOf": [{"$ref": "#/$defs/speech_act"}, {"type": "null"}]}
      }
    },
    "ado": {"enum": ["asking", "doing", "expressing"]},
    "task_type": {"type": "string", "pattern": "^([a-z]+(\\.[a-z]+)?|other:[a-z0-9-]+)$"},
    "mode": {"enum": ["directive", "feedback_loop", "task_iteration", "learning", "validation", null]},
    "feedback": {
      "type": "object", "required": ["type"],
      "properties": {
        "type": {"enum": ["none", "accept", "praise", "rephrase", "aware_no_fix", "aware_with_fix", "clarify_request", "reject", "undo", "interrupt", "scope_change"]},
        "target_event": {"type": ["string", "null"]},
        "evidence": {"type": "string"}
      }
    },
    "constraints_added": {"type": "array", "items": {"$ref": "#/$defs/constraint"}},
    "task_link": {"type": "string", "pattern": "^(continue|new|uncertain|switch_to:int_.+)$"},
    "task_id": {"type": ["string", "null"], "pattern": "^int_"},
    "intent_summary": {"type": "object", "properties": {"en": {"type": "string"}, "ko": {"type": "string"}}},
    "interpretation_status": {"enum": ["ok", "misread", "executed_badly", "unclear", null]},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "confidence_band": {"enum": ["high", "medium", "low"]},
    "provenance": {"$ref": "#/$defs/provenance"},
    "supersedes": {"type": ["string", "null"], "pattern": "^evt_"},
    "propagated_from": {"type": ["string", "null"]}
  },
  "$defs": {
    "speech_act": {"enum": ["request.action", "request.info", "request.option", "inform.context", "constrain", "declare.policy", "declare.goal", "declare.close", "commit.self", "feedback", "answer", "continue", "express"]},
    "constraint": {
      "type": "object", "required": ["text_en"],
      "properties": {
        "text_en": {"type": "string"}, "text_ko": {"type": "string"},
        "kind": {"enum": ["scope", "format", "tool", "style", "language", "order", "prohibition", "quality"]},
        "persistence": {"enum": ["turn", "task", "project", "global"]},
        "source": {"enum": ["prompt", "correction", "policy"]}
      }
    },
    "provenance": {
      "type": "object", "required": ["source"],
      "properties": {
        "source": {"enum": ["rule", "model", "user"]},
        "model": {"enum": ["haiku", "sonnet", "opus", "fable", null]},
        "prompt_version": {"type": "string"},
        "k_samples": {"type": "integer"}, "agreement": {"type": "number"},
        "rule_patterns": {"type": "array", "items": {"type": "string"}}
      }
    }
  }
}
```

### 8.2 `IntentNode` (I0/I1/I2) — event-sourced, `type: intent_node` (new event type) or `label` with `level`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "harness/intent/IntentNode.v0.1",
  "type": "object",
  "required": ["node_id", "level", "title", "status", "provenance"],
  "properties": {
    "node_id": {"type": "string", "pattern": "^int_(g|p|t)_[0-9]{8}_[0-9a-f]{4}$"},
    "level": {"enum": ["I0", "I1", "I2"]},
    "parent": {"type": ["string", "null"], "pattern": "^int_"},
    "title": {"type": "object", "properties": {"en": {"type": "string"}, "ko": {"type": "string"}}, "required": ["en"]},
    "job_story": {"type": "string", "description": "When <situation>, I want to <motivation>, so I can <outcome>."},
    "scope": {"type": "string"},
    "project_id": {"type": ["string", "null"]},
    "task_type": {"type": ["string", "null"]},
    "mode": {"type": ["string", "null"]},
    "objective_kind": {"enum": ["deliver", "acquire", "build", "learn", "maintain", "explore", null]},
    "success_criteria": {"type": "array", "items": {"type": "string"}},
    "deadline": {"type": ["string", "null"], "format": "date"},
    "subgoals": {
      "type": "array",
      "items": {"type": "object", "required": ["id", "title", "status"],
        "properties": {"id": {"type": "string"}, "title": {"type": "string"},
                       "status": {"enum": ["open", "achieved", "dropped"]},
                       "order": {"type": "integer"}}}
    },
    "constraints": {"type": "array", "items": {"$ref": "IntentLabel.v0.1#/$defs/constraint"}},
    "status": {"enum": ["proposed", "active", "suspended", "achieved", "abandoned", "impossible", "superseded", "reason_gone"]},
    "boundary": {"type": "object", "properties": {"start_event": {"type": "string"}, "end_event": {"type": ["string", "null"]}, "reason": {"type": "string"}}},
    "supersedes": {"type": ["string", "null"]},
    "confidence": {"type": "number"},
    "provenance": {"$ref": "IntentLabel.v0.1#/$defs/provenance"},
    "user_confirmed": {"type": "boolean"}
  }
}
```

### 8.3 `ActionPurpose` (I4)
```json
{
  "$id": "harness/intent/ActionPurpose.v0.1",
  "type": "object",
  "required": ["action_ref", "purpose", "on_intent", "provenance"],
  "properties": {
    "action_ref": {"type": "object", "properties": {"session_id": {"type": "string"}, "tool_use_id": {"type": "string"}, "transcript_path": {"type": "string"}, "turn_of": {"type": "string", "pattern": "^evt_"}}},
    "tool": {"type": "string"},
    "args_summary": {"type": "string"},
    "purpose": {"enum": ["orient", "gather", "plan", "produce", "execute", "verify", "communicate", "delegate", "recover", "housekeep"]},
    "task_id": {"type": "string", "pattern": "^int_t_"},
    "serves_subgoal": {"type": ["string", "null"]},
    "on_intent": {"enum": ["on", "tangential", "off", "unknown"]},
    "side_effect_risk": {"enum": ["none", "reversible", "irreversible"]},
    "outcome": {"enum": ["pending", "worked", "failed", "reverted"]},
    "confidence": {"type": "number"},
    "provenance": {"$ref": "IntentLabel.v0.1#/$defs/provenance"}
  }
}
```

### 8.4 `DriftEvent`
```json
{
  "$id": "harness/intent/DriftEvent.v0.1",
  "type": "object",
  "required": ["kind", "at_event", "task_id", "score", "signals"],
  "properties": {
    "kind": {"enum": ["goal_switch", "refinement", "scope_change", "agent_drift"]},
    "at_event": {"type": "string"},
    "task_id": {"type": "string"},
    "new_task_id": {"type": ["string", "null"]},
    "score": {"type": "number"},
    "signals": {"type": "array", "items": {"enum": ["declaration", "embedding_changepoint", "centroid_distance", "cwd_change", "time_gap", "new_session", "off_intent_actions", "uncovered_irreversible", "constraint_violation", "interrupt", "correction"]}},
    "window": {"type": "object", "properties": {"from": {"type": "string"}, "to": {"type": "string"}}},
    "resolution": {"enum": ["auto", "user_confirmed", "user_rejected", "pending"]}
  }
}
```

### 8.5 Ontology wiring (proposed diff, for a reviewed PR) [?]
- `enums.event_type`: add `intent_node`, `drift`. `enums`: add `speech_act`, `ado`, `feedback_type`, `collab_mode`,
  `action_purpose`, `on_intent`, `intent_level: [I0, I1, I2, I3, I4]`, `intent_status`.
- `Event.fields`: add `level, speech_act, ado, task_type, mode, feedback, constraints_added, task_link, task_id,
  intent_summary, interpretation_status, confidence_band, provenance, supersedes, node_id, parent, job_story,
  subgoals, constraints, action_ref, purpose, serves_subgoal, on_intent, side_effect_risk`.
- Keep the existing free-text `intent` field: fill it from `intent_summary.en` so existing scripts keep working.
- `Project`: add `intent_node` (ref `int_p_`), `success_criteria`, `job_story`.
- New `hooks/log_event.py` S1 patterns: `declare.policy` (앞으로|이제부터|항상|from now on|always|never), `continue`
  (^(계속|ㄱㄱ|고고|진행(해)?|next|continue|go)\W*$), `declare.close` (그만|중단|취소|됐어|never ?mind|cancel|stop),
  `answer` (^(응|네|예|ㅇㅇ|yes|yep|[0-9]번|option [a-z])\W*$ when the previous agent turn ended with "?").

---

## 9. Example labeled records

**(a) Korean task request (start of a task)** — prompt `evt_20261016_090412_1a2b`:
"메시지 추출 리서치 바탕으로 Gmail 백필 파이프라인 먼저 만들어줘. 라벨은 건드리지 말고."
```json
{"type": "label", "labels_for": "evt_20261016_090412_1a2b", "level": "I3", "language": "ko",
 "speech_act": {"primary": "request.action", "secondary": "constrain"},
 "ado": "doing", "task_type": "code.build", "mode": "directive",
 "feedback": {"type": "none", "target_event": null, "evidence": ""},
 "constraints_added": [{"text_en": "Do not modify Gmail labels", "text_ko": "Gmail 라벨 수정 금지", "kind": "prohibition", "persistence": "task", "source": "prompt"}],
 "task_link": "new", "task_id": "int_t_20261016_7c3d",
 "intent_summary": {"en": "Build the Gmail backfill pipeline first, based on prior research", "ko": "이전 리서치를 바탕으로 Gmail 백필 파이프라인을 먼저 구축"},
 "intent": "Build the Gmail backfill pipeline first, based on prior research",
 "interpretation_status": "ok", "confidence": 0.91, "confidence_band": "high",
 "provenance": {"source": "model", "model": "haiku", "prompt_version": "P-I3.v0.1", "k_samples": 3, "agreement": 1.0, "rule_patterns": ["하지-마"]}}
```
Note: S1 flagged `말고` (correction_candidate 0.6); S2 overrode to `constrain` because there is no previous agent turn —
exactly the case the existing `NON_CORRECTION`/long-prompt logic cannot catch with regex alone.

**(b) The I2 node created for it**
```json
{"type": "intent_node", "node_id": "int_t_20261016_7c3d", "level": "I2", "parent": "int_p_20261001_harn",
 "title": {"en": "Gmail backfill pipeline (Feb–Oct 2026)", "ko": "Gmail 백필 파이프라인 (2026년 2–10월)"},
 "job_story": "When my job-application email is scattered across accounts, I want a read-only backfill into the KB, so I can track every application's status without manual searching.",
 "scope": "code/claude-harness", "task_type": "code.build", "mode": "directive",
 "subgoals": [{"id": "s1", "title": "choose backfill method", "status": "open", "order": 1},
              {"id": "s2", "title": "implement export script", "status": "open", "order": 2},
              {"id": "s3", "title": "verify against a sample month", "status": "open", "order": 3}],
 "constraints": [{"text_en": "Do not modify Gmail labels", "kind": "prohibition", "persistence": "task", "source": "prompt"}],
 "status": "active", "boundary": {"start_event": "evt_20261016_090412_1a2b", "end_event": null, "reason": "declare"},
 "confidence": 0.84, "provenance": {"source": "model", "model": "sonnet", "prompt_version": "P-I2.v0.1"}, "user_confirmed": false}
```

**(c) Agent actions (I4)**
```json
{"type": "label", "level": "I4", "action_ref": {"session_id": "sess_x", "tool_use_id": "toolu_01", "turn_of": "evt_20261016_090412_1a2b"},
 "tool": "Read", "args_summary": "research_notes/.../message_extraction.md §5", "purpose": "orient", "task_id": "int_t_20261016_7c3d",
 "serves_subgoal": "s1", "on_intent": "on", "side_effect_risk": "none", "outcome": "worked", "confidence": 0.95,
 "provenance": {"source": "rule"}}
{"type": "label", "level": "I4", "action_ref": {"session_id": "sess_x", "tool_use_id": "toolu_07"},
 "tool": "mcp__Gmail__label_thread", "args_summary": "add label 'applications' to 40 threads", "purpose": "produce",
 "task_id": "int_t_20261016_7c3d", "serves_subgoal": null, "on_intent": "off", "side_effect_risk": "reversible",
 "outcome": "reverted", "confidence": 0.9, "provenance": {"source": "model", "model": "haiku"}}
```
The second action violates the task constraint → `DriftEvent`:
```json
{"type": "drift", "kind": "agent_drift", "at_event": "toolu_07", "task_id": "int_t_20261016_7c3d", "score": 0.6,
 "signals": ["constraint_violation", "off_intent_actions"], "resolution": "pending"}
```

**(d) Mixed-language correction** — `evt_20261016_093015_9e0f`: "아니 label 붙이지 말라니까. revert하고 export만 해줘."
```json
{"type": "label", "labels_for": "evt_20261016_093015_9e0f", "level": "I3", "language": "mixed",
 "speech_act": {"primary": "feedback", "secondary": "request.action"},
 "ado": "doing", "task_type": "code.build", "mode": "directive",
 "feedback": {"type": "aware_with_fix", "target_event": "evt_20261016_092950_agent", "evidence": "아니 label 붙이지 말라니까"},
 "constraints_added": [{"text_en": "Export only; no write actions on Gmail", "text_ko": "내보내기만; Gmail 쓰기 작업 금지", "kind": "scope", "persistence": "task", "source": "correction"}],
 "task_link": "continue", "task_id": "int_t_20261016_7c3d",
 "intent_summary": {"en": "Undo the labeling and limit the agent to read-only export", "ko": "라벨 작업을 되돌리고 읽기 전용 내보내기로 제한"},
 "interpretation_status": "ok", "is_correction": true, "confidence": 0.95, "confidence_band": "high",
 "provenance": {"source": "model", "model": "haiku", "k_samples": 3, "agreement": 1.0, "rule_patterns": ["아니-start", "하지-마"]}}
```
Effects (§6): toolu_07 → `outcome: reverted`; drift event → `resolution: user_confirmed`; constraint appended to I2;
the same "no write actions on connectors without asking" constraint already appeared in 2 earlier tasks → third
occurrence emits `pattern_proposed` (`pattern_kind: correction`).

**(e) English rephrase (misread)** — prompt 1: "summarize the fanout doc" → agent writes a 2-page summary.
Prompt 2: "I mean just the tier table, in 5 lines".
```json
{"type": "label", "labels_for": "evt_20261016_110201_aa01", "level": "I3", "language": "en",
 "speech_act": {"primary": "feedback", "secondary": "request.action"}, "ado": "doing", "task_type": "writing.draft",
 "mode": "task_iteration", "feedback": {"type": "rephrase", "target_event": "evt_20261016_110150_agent", "evidence": "I mean"},
 "constraints_added": [{"text_en": "Only the tier table, max 5 lines", "kind": "format", "persistence": "turn", "source": "correction"}],
 "task_link": "continue", "confidence": 0.88, "confidence_band": "high", "provenance": {"source": "model", "model": "haiku"}}
{"type": "label", "labels_for": "evt_20261016_110140_9f00", "level": "I3", "supersedes": "evt_20261016_110141_lbl1",
 "interpretation_status": "misread",
 "intent_summary": {"en": "Wanted a 5-line digest of the fan-out tier table only", "ko": "팬아웃 티어 표만 5줄로 요약 원함"},
 "speech_act": {"primary": "request.action"}, "ado": "doing", "task_type": "writing.draft",
 "feedback": {"type": "none"}, "confidence": 0.85, "provenance": {"source": "model", "model": "sonnet", "prompt_version": "P-I2.v0.1"}}
```

**(f) Short answer and continue**
- Agent asked "Use Takeout or the connector?" → user "1번" → `speech_act: answer`, `feedback: none`, `task_link: continue`.
- After the agent reported "s2 done, tests pass" → user "ㄱㄱ" → `speech_act: continue`, `feedback: accept`, subgoal s2 →
  `achieved` (accept is inferred only because a subgoal had just been reported finished).

**(g) Goal switch** — "그건 일단 두고, ProZ 프로필 문구 영어로 다듬어줘" → `declare.close` (secondary, suspend) +
`request.action`, `task_type: writing.edit`, `mode: task_iteration`, `task_link: new`; I2 `int_t_20261016_7c3d` →
`suspended` (not abandoned: "일단 두고" = park); new I2 under I1 "job-search/proz-presence".

---

## 10. Implementation order (smallest useful first) [?]
1. Extend S1 regex in `hooks/log_event.py` with `declare.policy`, `declare.close`, `continue`, `answer` hints (KO+EN).
2. Extend `scripts/label_events.py` PROMPT to emit the I3 tuple (§4.4 P-I3) and keep writing the existing `intent`
   string; this alone gives speech act, ado, task type, feedback on every prompt.
3. Add a session-end pass that reads `transcript_path`, builds I4 records deterministically, and runs P-I2 for
   segmentation (sonnet, one call per session).
4. Add the weekly I2→I1 linking + review page (blind-first relabeling) and start the gold set.
5. Only then add online drift alerts (PostToolUse hook computing D) and the monthly I0 proposal.

---

## Sources
- Anthropic, "Clio: Privacy-preserving insights into real-world AI use" — https://www.anthropic.com/research/clio **[V]**
- Tamkin et al., "Clio: Privacy-Preserving Insights into Real-World AI Use", arXiv 2412.13678 — https://arxiv.org/abs/2412.13678 **[S, unreachable]**; review: https://pith.science/paper/2412.13678 [S]; OpenClio: https://github.com/Phylliida/OpenClio [S]
- Cliopatra, arXiv 2603.09781 — https://arxiv.org/html/2603.09781v2 [S]
- Chatterji et al., "How People Use ChatGPT", NBER WP 34255 — https://www.nber.org/papers/w34255 [S]; OpenAI post — https://openai.com/index/how-people-are-using-chatgpt/ [S]
- Anthropic Economic Index coverage — https://www.axios.com/2025/02/10/anthropic-economic-index-ai-use-data [S]
- TnT-LLM taxonomy appendix — https://hackernoon.com/tnt-llm-generated-taxonomies-user-intent-and-conversation-domain-labels [S]; M365 Copilot Chat usage, arXiv 2605.23958 [S]
- Liu, Zhang & Choi, "User Feedback in Human-LLM Dialogues…", EMNLP 2025 — https://aclanthology.org/2025.emnlp-main.133 (preview: https://preview.aclanthology.org/dashboard/2025.emnlp-main.133.pdf) [S]; WildReward, arXiv 2602.08829 [S]
- Ramírez & Geffner, "Probabilistic Plan Recognition Using Off-the-Shelf Classical Planners", AAAI 2010 — https://ojs.aaai.org/index.php/AAAI/article/view/7745 [S]; Pereira et al., AAMAS/AAAI 2017 landmarks — https://ifaamas.csc.liv.ac.uk/Proceedings/aamas2017/pdfs/p750.pdf [S]
- Baker, Saxe & Tenenbaum, "Action understanding as inverse planning", *Cognition* 2009 — https://dspace.mit.edu/handle/1721.1/60852 [S]
- Bratman, *Intention, Plans, and Practical Reason* (1987) — https://press.uchicago.edu/ucp/books/book/distributed/I/bo3629095.html [S]; Cohen & Levesque — https://sri.com/publication/persistence-intention-and-commitment [S]; Wooldridge survey — https://cs.ox.ac.uk/people/michael.wooldridge/pubs/ker95/subsubsectionstar3_2_6_2.html [S]
- Rao & Georgeff, "BDI Agents: From Theory to Practice", ICMAS 1995 — https://www.eecis.udel.edu/~decker/courses/886f06/pubs/GeorgeffBDI.pdf [S]; Kinny & Georgeff / Schut & Wooldridge (via https://nms.kcl.ac.uk/simon.parsons/publications/conferences/timr99.pdf) [S]
- Searle taxonomy summaries — https://www.asc.ohio-state.edu/roberts.21/Roberts.SpeechActs.pdf [S]
- DAMSL revised manual — https://www.cs.rochester.edu/research/speech/damsl/RevisedManual/ [S]; Core & Allen 1997 — https://www.eecis.udel.edu/~carberry/CIS-885/Papers/Core-Allen-Coding-Damsl.pdf [S]
- ISO 24617-2:2020 — https://iteh.es/catalog/standards/iso/7aab02cf-2656-4dd7-9e0f-22fe5daf1bf5/iso-24617-2-2020 [S]; Bunt et al. chapter — https://dialogbank.lsv.uni-saarland.de/wp-content/uploads/2015/12/MMI-standards-bookchapter_v06.pdf [S]; Bunt et al. 2017 — https://people.ict.usc.edu/~traum/Papers/iso-2017.pdf [S]
- HTN: https://en.wikipedia.org/wiki/Hierarchical_task_network [S]; Erol, Hendler & Nau UMCP — https://www.cs.umd.edu/~nau/papers/erol1994umcp.pdf [S]; SHOP2 — https://artlab.unist.ac.kr/~chiu/paper/Nau03shop2.pdf [S]
- ToM / intent benchmarks: arXiv 2507.02935, 2602.13832, 2607.14250; IntInst — https://preview.aclanthology.org/dashboard/2025.findings-naacl.330 [S]
- Drift: Arike et al., AIES 2025 — https://ojs.aaai.org/index.php/AIES/article/download/36541/38679/40616 [S]; arXiv 2510.07777, 2602.16935, 2602.16901, 2605.09863 [S]; ARMO — https://www.armosec.io/blog/detecting-intent-drift-in-ai-agents-with-runtime-behavioral-data/ [S]
- JTBD: https://studio.wadeinstitute.org.au/canvas-jobs-to-be-done.html ; https://trailhead.salesforce.com/content/learn/modules/jobs-to-be-done-framework-for-designers/craft-job-statements [S]
- Background, not re-fetched [K]: Austin 1962; Searle 1975/1979; Adams & MacKay 2007 (BOCPD); Beeferman et al. 1999 (Pk); Pevzner & Hearst 2002 (WindowDiff); Krippendorff's α / MASI (Passonneau 2006).
