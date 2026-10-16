# Abstraction layers and decision rationale: knowledge-representation and ontology-engineering techniques for the harness ontology

Date: 2026-10-16. Target: `claude-harness/schema/ontology.yaml` v0.2.0 and `schema/STORAGE.md`.
Question: how should a JSONL/YAML personal-harness ontology represent (a) several layers of abstraction (raw → episode → pattern → rule → principle) and (b) decision rationale, using what established KR practice already knows?

**Source access, stated plainly.** In this sandbox, `WebFetch` and `curl` could not reach w3.org, arxiv.org, wikipedia.org, ontologydesignpatterns.org, schema.org, basic-formal-ontology.org, tana.inc or loa.istc.cnr.it (DNS failure or proxy 403). The only reachable host was GitHub. So the evidence comes from:
- **Primary files read directly from shallow, read-only clones** in `/tmp/claude-0/-home-user-albers-club/1397d302-c3cb-5329-ad06-e45b2c66c6d1/scratchpad/abs/`:
  - `w3c/prov`: `ontology/prov-o.ttl`, the normative PROV-O source. Term definitions below are quoted from it.
  - `BFO-ontology/BFO-2020`: `21838-2/owl/bfo-core.ttl`, the ISO/IEC 21838-2 release.
  - `information-artifact-ontology/IAO`: `iao.owl`.
  - `schemaorg/schemaorg`: `data/schema.ttl`, `docs/howwework.html`, `docs/extension.html`.
  - `adr/madr`: `template/adr-template.md` and CHANGELOG (v4.0.0, 2024-09-17).
  - `microsoft/graphrag`: `docs/index/outputs.md` and `default_dataflow.md`.
  - `parthsarthi03/raptor`: `raptor/cluster_utils.py`, `tree_structures.py`.
  - `NatLibFi/Skosify` and `w3c/sdw` were also cloned.
- **WebSearch result snippets** for W3C SKOS/OWL text, the papers (IBIS, QOC, DRL, Toulmin, FCA, OntoClean, multi-level modeling, GraphRAG) and practitioner tools. These are marked *(via search)*. Where only secondary summaries were available I say so. Treat any specific clause numbers I don't quote as unverified.
- **Unreachable and not substituted:** the ODP portal catalogue pages, the DOLCE D18 full text, the Compendium documentation, Tana's own docs (only the "extend" guide surfaced), and Roam's documentation.

---

## 0. TL;DR

1. **Abstraction is currently encoded only by record type.** The ladder Event → Correction/Mishap → Lesson → Principle, StylePair → StyleGuide, and Document → WikiPage is implicit. `scope` measures *where* something applies, not *how abstract* it is. The fix is a third, orthogonal axis, `abstraction_level` (raw | episode | pattern | rule | principle | meta), with a per-type default and a per-record override. Add one validation rule: derivation links point **downward** (to equal or lower levels), and every rule or principle is **grounded** in at least one episode. This follows the multi-level modeling literature and OntoClean: levels are a *property* of records, never a parallel tree of types.
2. **Free-text tags become a SKOS concept scheme.** Today `labels`, `tags`, `meta.kind_of_thing`, `repeat_pattern` and `generalizes_to` are uncontrolled strings. Replace them with `Concept` records (`cpt-` ids): `pref_label`, `alt_labels`, `definition`, `broader`, `related`, `in_scheme`, `mappings`, `status`. Records point at them through `about` (the W3C "classes as values" problem, solved the SKOS way: no punning). Store `broader` only, and derive `narrower`. Enforce the SKOS integrity conditions: `broader` acyclic, `related` disjoint with the transitive closure of `broader`, and one pref_label per scheme.
3. **Generated summaries are a separate type, `Abstraction` (`abs_`).** It covers RAPTOR tree nodes, GraphRAG community reports, and FCA formal concepts. It has `members`, `parent`/`children`, `tier`, `method`, `model`, `input_hash` and `as_of`. It is append-only, regenerable and never hand-edited. A curated `Concept` is a *meaning*; an `Abstraction` is a *summary of an extent*. A human-approved promotion (`promoted_to`) is the only route from an Abstraction to a Lesson, Principle or Concept.
4. **Decision becomes IBIS + QOC + Toulmin + MADR.** This means an `Issue` (`iss-`) plus a `Decision` (D-) holding embedded `options`, `criteria`, `assessments` (option × criterion × polarity, carrying Toulmin grounds/warrant/qualifier/rebuttal) and IBIS `arguments`. It also gets `chosen`, `rationale`, `consequences`, MADR `confirmation`, the existing `expected_outcome`/`review_date`, and a status of proposed | accepted | rejected | deprecated | superseded. Store it as JSONL so `schema_check` can parse it, and make `decisions.md` a rendered view. The constraints: `chosen` ∈ options; ≥2 options unless `forced`; every criterion assessed; rationale cites a criterion or argument.
5. **PROV-O alignment needs no field renames.** Add a `prov:` key to each relation (wasDerivedFrom, wasGeneratedBy, wasAttributedTo, actedOnBehalfOf, wasRevisionOf, wasQuotedFrom, wasInvalidatedBy). Recognize that label batches are PROV *Bundles* (provenance of provenance).
6. **Bitemporal validity.** `ts` is already transaction time. Add `valid_from`/`valid_to` (valid time) to rule-level and stateful records. The transaction-time end is *derived* from the append-only log: it is the `ts` of the superseding line, so it is never written. "Newest wins" becomes "newest recorded among records valid at t". Overlapping valid intervals with no `supersedes` raise a conflict warning, which is the Graphiti/Zep invalidation pattern.
7. **Tested:** all proposed YAML parses with the harness's own YAML-subset loader (`scripts/schema_check.py yaml_load`). The existing checks (required, enums, refs prefix, id_pattern, formats) already work on the new types. The new `abstraction:` and `constraints:` keys are ignored until `schema_check.py` learns them (§4.6).

---

## 1. Diagnosis of the current design (v0.2.0)

Strengths to keep:
- **Append-only plus correction records** (`supersedes`, `corrects`, label events, latest-wins ids) already make this a transaction-time log. Bitemporality is half done.
- **The `coverage: {provenance, intent, meta}` triple per type** is a lightweight form of PROV plus rationale. It is unusual and good.
- **The `relations:` block (domain/range/via)** is an RDFS-like property layer that can be mapped to PROV/SKOS without changing data.
- **Ids carry type** (`evt_`, `L-`, `D-`), and `refs` checks prefixes. That is a cheap form of typed links.

Gaps relevant to this question:

| Gap | Where it shows | Consequence |
|---|---|---|
| Abstraction level is implicit in the type | Lesson vs Principle vs StyleGuide vs Mishap.repeat_pattern | You cannot query "everything at pattern level about client X". The question "is this Lesson grounded in any episode?" is not checkable. Adding a level means adding a type (the "levels as types" anti-pattern, §2.2). |
| `scope` is overloaded as generality | `meta.generalizes_to: ["global", ...]` | Breadth (where it applies) and abstraction (how far it is from observation) are different. A global *episode* exists ("a hook crashed on every project"), and so does a narrow *principle*. |
| Uncontrolled vocabularies | `Event.labels`, `ResearchNote.tags`, `Asset.tags`, `meta.kind_of_thing`, `Mishap.repeat_pattern`, `Evaluation.rubric` | Synonyms split clusters ("scope creep" vs "scope-creep" vs "범위 확대"). There is no hierarchy, so nothing rolls up. FCA/RAPTOR-style abstraction has no stable attributes to work on. |
| Decision is flat prose | `Decision` store is `decisions.md` (format md, not parsed); `alternatives` is free text | There are no criteria and no per-option assessments. Supersession between decisions is untracked, the record can't be machine-checked, and decisions can't be revisited per criterion when a driver changes. |
| Provenance field names are heterogeneous | `source_event`, `learned_from`, `derived_from`, `evidence`, `source_id`, `source_thread`, `origin` | That is fine for writers but unclear for readers. Each field already maps to a PROV term, so the mapping should be recorded once in `relations`. |
| Only transaction time | `ts` everywhere; Preference "newest per (topic, scope) wins" | You can't say "this rate applied Jan–Mar" or "this reviewer rule was in force until the platform changed it". You can't do as-of queries or detect conflicts. |
| `refs` has a single target, prefix only | `refs: {account: Account}` | A member list spanning several types (Abstraction.members) can't be typed. Cross-record rules (acyclicity, "chosen ∈ options") aren't expressible. |

---

## 2. Techniques: what each contributes, its constructs, and how to apply it here

### 2.1 SKOS (W3C Recommendation, 2009)

**Contributes:** a light, non-logical model for *concept schemes* (thesauri, taxonomies, tag sets) that avoids OWL class semantics. Concepts are *individuals*, so hierarchy among them carries no instance inheritance. This is exactly what a personal tag system needs.

**Constructs** (SKOS Reference; via search, plus the SKOS RDF file that Skosify validates against):
- Classes: `skos:Concept`, `skos:ConceptScheme`, `skos:Collection`, `skos:OrderedCollection`.
- Scheme membership: `inScheme`, `hasTopConcept` / `topConceptOf`.
- Labels: `prefLabel`, `altLabel`, `hiddenLabel` (misspellings and search-only forms). There is at most one prefLabel per language tag, and pref/alt/hidden labels are pairwise disjoint.
- Notes: `note` ⊃ `definition`, `scopeNote`, `example`, `historyNote`, `editorialNote`, `changeNote`.
- Semantic relations: `broader`, `narrower` (inverse), `related` (symmetric). **`broader` is not transitive.** `broaderTransitive` and `narrowerTransitive` are the transitive super-properties, and by convention they are not asserted, only inferred. "By convention, skos:broader and skos:narrower are only used to assert an immediate (i.e. direct) hierarchical link" *(via search, SKOS Reference)*.
- Integrity condition: **`skos:related` is disjoint with `skos:broaderTransitive`** *(via search; also in skos.rdf)*. A concept can't be both related to and an ancestor of another.
- Mapping properties, for links *across* schemes: `exactMatch` (transitive), `closeMatch`, `broadMatch`, `narrowMatch`, `relatedMatch`, all under `mappingRelation`.
- Integrity conditions *define inconsistency*; they don't add inferences *(via search: "defining circumstances under which data are not consistent with respect to the SKOS data model")*.

**Apply:**
- New types `ConceptScheme` (`cs-`) and `Concept` (`cpt-`) in `harness-data/concepts/` (§4.2). Initial schemes:
  - `cs-failure-mode`, for Mishap.repeat_pattern and correction labels.
  - `cs-decision-criterion`, for QOC criteria reused across decisions: cost, reversibility, privacy, time-to-done, client-visible.
  - `cs-topic`, for domain topics: translation registers, platforms, art techniques.
  - `cs-style-feature`, for StylePair labels and StyleGuide rules.
  - `cs-record-kind`, which replaces `meta.kind_of_thing`.
- **Store only `broader`.** Derive `narrower` at read time, which avoids the two-sided update problem in an append-only log.
- Use `hidden_labels` for Korean/English variants and typos. That makes concept lookup bilingual (the user works ko↔en), and `alt_labels` keep surface forms.
- Use `mappings: [{kind: exact, target: "https://schema.org/Invoice"}]` to tie concepts to schema.org, Wikidata or ISO terms when useful. Mapping is *how* to stay interoperable without importing anything.
- Validation:
  - `broader` must be acyclic.
  - `related` must not hit the `broader` closure.
  - `pref_label` must be unique per scheme. SKOS's "one per language" is relaxed to "one per scheme" here because labels are mixed-language; use `alt_labels` for the other language.
  - Every `about` value must resolve to a non-deprecated concept. A deprecated concept is allowed only with a `superseded_by` hop, which gives a warning.

### 2.2 OWL class hierarchies vs instances: punning, metaclasses, and the "levels" anti-patterns

**Contributes:** guidance on *where to put abstraction*, and what not to do.

- **Classes as values** *(W3C SWBP Note, Noy ed., 2005; via search)*. The canonical problem is "a book's subject is a class in a subject hierarchy". OWL DL forbids classes as property values. The note's alternatives are: use the class directly (OWL Full only); create instances that stand for the subject; or use restrictions or a parallel hierarchy. SKOS later became the standard answer, with subjects as `skos:Concept` *individuals*. **Apply:** `about: [cpt-...]` is that answer. Never make "ScopeCreepMishap" a type.
- **Punning** (OWL 2 *metamodeling*). The same IRI is used as a class and as an individual, but under the Direct Semantics they are *two unrelated things* sharing a name, so nothing you say about the individual constrains the class *(via search: W3C semantic-web list; CEUR Vol-1350 paper-55)*. Some projects *forbid* punning with SHACL to keep TBox and ABox separate *(via search: NFDI MatWerk "no-punning" pattern)*. **Apply:** the ontology's `types:` are the TBox and the JSONL records are the ABox. Keep them separate. A record type name must never also appear as a Concept id. Validation: `Concept.pref_label` must not equal a key of `types:` (case-insensitive) unless it carries a `mappings: [{kind: exact, target: "type:<Name>"}]` that makes the link explicit.
- **Multi-level modeling** (Atkinson & Kühne 2001, potency and deep instantiation; Carvalho & Almeida 2016–18, MLT with orders and the powertype/categorization/partitioning relations) *(via search)*. When a domain truly has types of types ("Lesson" is a type, "translation-register lesson" is a kind of lesson, and a specific lesson is an instance), MLT says: give each type an *order*, and only allow `instance_of` between adjacent orders and `subclass_of` within the same order. Brasileiro, Almeida, Carvalho & Guizzardi (WWW 2016 Companion) found "a significant number of problematic classification and taxonomic statements" in Wikidata, arising from "an inadequate use of instantiation and subclassing" *(via search)*. **Apply:** our abstraction levels are **not** type orders. A Lesson does not *instantiate* a Mishap; it is *derived from* it. Model the ladder with **derivation relations plus a level attribute**, not instantiation. This avoids the Wikidata failure mode in a JSONL setting.
- **OntoClean** (Guarino & Welty) *(via search)*. Meta-properties rigidity, identity and unity. Rule: an anti-rigid class (Student) can't subsume a rigid one (Human). **Apply:**
  - `status` values (proposed/approved, lead/applied) are *anti-rigid phases*, so keep them as fields, not types. The ontology already does this, which is good.
  - `abstraction_level` is also a phase-like attribute: a pattern can be promoted to a rule. So it must be a field with history (a new line or a `promoted_to` link), never a type change.

### 2.3 Formal Concept Analysis (Wille 1982; Ganter & Wille 1999)

**Contributes:** *automatic, canonical* abstraction. Given a formal context (objects G, attributes M, incidence I), the derivation operators form a Galois connection. A *formal concept* is a pair (extent ⊆ G, intent ⊆ M), where the extent is exactly the objects having all intent attributes and vice versa. Ordered by extent inclusion, the concepts form a complete lattice, unique per context *(via search)*. Attribute implications (the Duquenne–Guigues basis) give minimal rules of the form "all records with A also have B".

**Apply:**
- Objects are records (e.g. Mishaps and Corrections in an area). Attributes are their `about` concepts plus enum values (scope, noticed_how, model, register).
- Compute the lattice periodically (`method: fca`). Each lattice node with extent ≥2 and a non-trivial intent is a *candidate pattern*: an `Abstraction` with `members` = extent and `intent_concepts` = intent. Its position in the lattice gives `parent`/`children`, as a DAG, not a tree.
- Attribute implications with high support become *candidate Lessons* ("every Mishap with `cpt-skipped-verify` also has `cpt-deadline-pressure`"). They are proposed, never auto-approved.
- Why FCA as well as LLM clustering: it is deterministic, explainable (the intent *is* the explanation), and needs no model call, which suits the `fanout` cost policy. It depends on a controlled vocabulary (§2.1). That is another reason to do SKOS first.

### 2.4 Ontology Design Patterns (ODP portal; Gangemi & Presutti)

**Contributes:** small reusable modelling solutions ("Content ODPs") extracted from foundational ontologies, mainly DOLCE+DnS Ultralite (DUL). DUL is "a simplification of some parts of the DOLCE Lite-Plus library … pattern-based architecture … modules, called 'content ontology design patterns'" *(via search: DUL documentation; Presutti & Gangemi, ER 2008)*. The portal's live catalogue was unreachable.

Patterns that matter here:
- **Descriptions and Situations (DnS).** A *Description* (plan, norm, rule, theory) *defines* concepts and roles. A *Situation* *satisfies* a description when its entities play those roles. **This is the cleanest account of our ladder**:
  - Events, Mishaps and Corrections are Situations.
  - Lessons, Principles, Preferences, ReviewerRules and Rubrics are Descriptions.
  - `learned_from` is the inverse of "satisfies, as evidence".
  - A verification Event *checks whether a Situation satisfies a Description*.
  - Apply DnS by naming the relation: add `satisfies` / `violates` from Event to Lesson or ReviewerRule (§4.3). Then "how often was this lesson followed vs violated" becomes countable, which is the feedback signal the improvement loop needs.
- **Information Object / InformationRealization.** The content (a Lesson's statement) is separate from its realization (a line in a `.md` file). It explains why one Lesson can live in several files and why `sha256` identifies realizations, not content.
- **Situation / TimeIndexedSituation.** An n-ary relation with a time interval. It is the basis for valid-time on facts (§2.13).
- **Participation, Collection, Sequence/Plan.** Task/ProgressItem `blocks` is Sequence (precedes). Abstraction.members is Collection.

### 2.5 Upper ontologies: BFO 2020 (ISO/IEC 21838-2) and DOLCE; information entities (IAO)

**Contributes:** the top-level split everything else hangs on.
- BFO, quoted from `bfo-core.ttl`:
  - **continuant**: "an entity that persists, endures, or continues to exist through time while maintaining its identity".
  - **occurrent**: "an entity that unfolds itself in time or it is the start or end of such an entity or it is a temporal or spatiotemporal region".
  - **generically dependent continuant (GDC)**: "exists in virtue of the fact that there is at least one of what may be multiple copies which is the content or the pattern that multiple copies would share".
  - **concretizes**: links a GDC to the process or specifically dependent continuant that carries it.
- IAO, quoted from `iao.owl`:
  - **information content entity (ICE)**: "A generically dependent continuant that is about some thing".
  - **is about**: "A (currently) primitive relation that relates an information artifact to an entity".
  - **plan specification**: "a directive information entity with action specifications and objective specifications as parts …".
  - **document**: "A collection of information content entities intended to be understood together as a whole".
- DOLCE *(via search)* splits endurants, perdurants, qualities (values in *regions* among the abstracts) and abstracts. Endurants participate in perdurants.

**Apply** (as *documentation-level* alignment; no OWL reasoning needed):
- Add `upper:` to each type (optional, ignored by the validator):
  - `occurrent` for Event, Task and session-level activities.
  - `ice` for Lesson, Principle, Decision, WikiPage, Concept and Abstraction.
  - `directive-ice` for Rubric, ReviewerRule, Preference, Lesson and Decision. They are prescriptive, which matches the `rule` level.
  - `continuant` for Organization, Contact, Account and Platform.
  - `realization` for files (Document is the *bearer/concretization*; its WikiPage content is the ICE).
- The **`about` relation is IAO `is_about`**, so SKOS concepts are the targets of aboutness. This is principled justification for §2.1.
- The upper split yields two validation rules. **Only occurrents get `ts` as an event time**: for ICEs `ts` is recording time, and their "when" lives in `valid_from/valid_to`. And **only directive ICEs may be `satisfies`/`violates` targets.**

### 2.6 PROV-O (W3C Recommendation, 2013)

**Contributes:** a standard vocabulary for derivation, generation, attribution and revision, the "where did this come from" half of the coverage triple. Quoted from `prov-o.ttl`:
- **Starting point.**
  - `Entity` ("a physical, digital, conceptual, or other kind of thing with some fixed aspects").
  - `Activity` ("something that occurs over a period of time and acts upon or with entities").
  - `Agent` ("bears some form of responsibility for an activity taking place, for the existence of an entity, or for another agent's activity").
  - Properties: `used`, `wasGeneratedBy`, `wasDerivedFrom` ("a transformation of an entity into another, an update … or the construction of a new entity based on a pre-existing entity"), `wasAttributedTo`, `wasAssociatedWith`, `actedOnBehalfOf`, `wasInformedBy`, `startedAtTime`, `endedAtTime`.
- **Expanded.**
  - `wasRevisionOf` ("a derivation that revises an entity into a revised version").
  - `wasQuotedFrom` ("derived from an original entity by copying, or 'quoting', some or all of it").
  - `hadPrimarySource`, `generatedAtTime`, `invalidatedAtTime` ("no longer usable"), `wasInvalidatedBy`, `alternateOf`, `specializationOf`.
  - `Plan` ("a set of actions or steps intended by one or more agents to achieve some goals").
  - `Bundle` ("a named set of provenance descriptions, and is itself an Entity, so allowing provenance of provenance").
  - `SoftwareAgent`, `Person`.
- **Qualified pattern:** `qualifiedAssociation` → `Association` with `hadPlan` and `hadRole`, for "agent X ran activity Y following plan Z in role R".

**Apply (mapping only, no renames):**

| Harness field | PROV term |
|---|---|
| `Event.actor`, `model` | `wasAssociatedWith` (agent = `agent:<name>` + model as SoftwareAgent; `me` as Person) |
| `agent:<name>` acting for the user | `actedOnBehalfOf` me |
| `Task.agent` + skill used | `qualifiedAssociation{agent, hadPlan: skills/<name>/SKILL.md, hadRole: worker\|verifier}` |
| `Lesson.learned_from`, `WikiPage.derived_from`, `Abstraction.members` | `wasDerivedFrom` |
| `supersedes` (StylePair, Preference, Lesson, Decision) | `wasRevisionOf` (inverse direction) |
| `StylePair.source`, `ReviewerRule.quote` | `wasQuotedFrom` (+ `hadPrimarySource` = Message/Document) |
| `label` events and `labels/batch_*.jsonl` | `Bundle`: provenance *about* provenance; `source_batch` = the bundle id |
| Decision `deprecated`/`superseded`, Concept `deprecated` | `wasInvalidatedBy` / `invalidatedAtTime` (transaction-time end, §2.13) |
| `Document.sha256`, `Abstraction.input_hash` | identity of the Entity version (`specializationOf` a logical document) |

Rule from PROV semantics worth enforcing: **derivation must be time-consistent.** A record can't be derived from something recorded later. `ts(derived) ≥ ts(source)` for every `learned_from`/`derived_from`/`members`/`evidence` link, with a warning when violated. This catches back-filled or mis-linked ids.

### 2.7 IBIS: Issue-Based Information System (Kunz & Rittel, 1970); gIBIS, QuestMap, Compendium

**Contributes:** the grammar of deliberation on "wicked problems". *Issues* (questions) are answered by *positions* (ideas/options), which are supported or objected to by *arguments* (pro/con). Arguments can raise new issues, and issues can *generalize* or *specialize* other issues. "IBIS is meant to support coordination and planning of political decision processes", guiding how groups "identify, structure, and settle the issues" *(via search: Kunz & Rittel 1970 abstract as quoted)*. Conklin's gIBIS led to QuestMap and then **Compendium** (Selvin & Sierhuis at NYNEX; later the Open University KMi). Compendium's default node types were question, answer, pro, con, note, decision, reference, argument, list and map *(via search: Wikipedia Compendium, unverified against Compendium docs)*. Dialogue mapping = shared display + facilitator + conversational grammar.

**Apply:**
- `Issue` as a first-class record (`iss-`). It can be open with no decision, can have `parent_issue` (specialization, acyclic), and can be `reopened` when a later Correction contradicts the decision. That is the case IBIS handles and flat ADRs don't.
- `Argument` (embedded) with `role: pro|con|question`. A `question` argument has `raises_issue: iss-…`, which is IBIS's "objection opens a new issue".
- The harness already captures IBIS material in passing: `/why` prompts, `dead_ends` in SessionNote, and `alternatives`. The `why` skill should emit Issue + Decision lines instead of prose.

### 2.8 QOC: Questions, Options, Criteria (MacLean, Young, Bellotti & Moran, *HCI* 1991)

**Contributes:** design-space analysis. *Questions* frame key issues, *Options* answer them, and *Criteria* are the bases for choosing. A fourth element, *Assessments*, records whether an option supports or challenges a criterion: a solid line for positive, dashed for negative *(via search: AcaWiki summary of the paper)*. QOC is narrower than IBIS: it is a condensed, post-hoc view of the design space, not a full argument history.

**Apply:**
- Decision gets `criteria[]` (embedded `Criterion`, optionally pointing to a reusable `cpt-` in `cs-decision-criterion`) and `assessments[]` (option × criterion × polarity × strength).
- Cross-decision analytics become possible: "which criteria do I actually decide on?" and "when *reversibility* was rated low, how often was the decision later superseded?". This turns `review_date` predictions into learnable data.
- Constraints:
  - Every criterion is referenced by at least one assessment (no decorative criteria).
  - Each option is assessed against each `must: true` criterion.
  - `chosen` must not be `opposes` on any `must` criterion unless `rationale` explains it (a warning).

### 2.9 DRL: Decision Representation Language (Jintae Lee, MIT AI Lab WP-325, 1989; SIBYL 1990)

**Contributes:** DRL represents "the alternatives being evaluated, goals to satisfy, and the arguments evaluating the alternatives". It adds *services* over the recorded rationale: management of **dependency, plausibility, viewpoints, and precedents** *(via search: WP-325 abstract)*. Its distinctive move is that claims about claims are first-class, so you can argue about an argument's plausibility. Detailed relation names such as "achieves" or "supports" could not be verified here.

**Apply:**
- **Dependency:** Decision `depends_on: [D-…, pref_…, L-…]`. When a Preference or Lesson it depends on is superseded, flag the Decision for review. This one feature is worth more than all the others.
- **Plausibility:** Assessment `strength` plus Toulmin `qualifier`.
- **Viewpoints:** `decision_makers` / `consulted` (MADR). For a solo user, "viewpoint" can mean the scope-specific stakeholder (client X, platform Y).
- **Precedents:** `about` concepts plus `issue` similarity let `/why` retrieve earlier decisions on the same concept before recording a new one.

### 2.10 Toulmin's argument model (*The Uses of Argument*, 1958)

**Contributes:** the internal structure of one argument. **Claim**, from **Data/grounds**, licensed by a **Warrant**, supported by **Backing**, hedged by a **Qualifier**, defeasible under **Rebuttal** *(via search: Verheij, *Argumentation* 19, 2005)*. Data, warrant, backing and claim form the positive chain; qualifier and rebuttal form the default/negative part.

**Apply** (inside Assessment and Argument; also on Lesson):
- `grounds` must be *pointers*: evt ids, proof refs or URLs. That is where the existing `Proof` type plugs in.
- `warrant` is the general rule that makes the grounds relevant. Often it is a Lesson or Principle id, which links the decision layer to the abstraction ladder.
- `qualifier` → `confidence` enum (high/medium/low already exists).
- `rebuttal` gives the conditions under which the conclusion fails. Store it as text plus an optional `cpt-`. Rebuttals turn into Lesson `scope_note`s and review triggers.
- Lessons get the same treatment: `Lesson.statement` = claim, `learned_from` = grounds, `warrant` optional, `rebuttal` = "doesn't apply when …". This is the cheapest way to stop over-generalized lessons.

### 2.11 Architecture Decision Records: Nygard (2011) and MADR 4.0 (2024-09-17)

**Contributes:** a *practical, file-based* decision format that teams actually keep up.
- Nygard *(via search)*: Title, **Status** (proposed/accepted; later deprecated/superseded), **Context** ("value-neutral … simply describing facts"), **Decision** ("We will …"), **Consequences** ("all consequences … not just the positive ones").
- MADR (`template/adr-template.md`, read directly):
  - Front-matter: `status: {proposed | rejected | accepted | deprecated | … | superseded by ADR-0123}`, `date`, `decision-makers`, `consulted`, `informed`.
  - Sections: Context and Problem Statement; **Decision Drivers**; **Considered Options**; **Decision Outcome**: `Chosen option: "…", because …`; **Consequences** (Good/Bad because …); **Confirmation**, defined as "how the implementation / compliance of the ADR can/will be confirmed … automated or manual fitness function"; **Pros and Cons of the Options** (Good/Neutral/Bad, because …); More Information.

**Apply:**
- MADR is QOC in Markdown: Decision Drivers are Criteria, Considered Options are Options, and the Good/Neutral/Bad bullets are Assessments with polarity. So `decisions.md` can be *rendered* from the JSONL Decision with MADR headings, and `/why` stays human-friendly.
- **Confirmation** maps directly onto the harness's verify culture. `confirmation` should name a check: a test, an eval id, or a `verify` criterion. A later `verification` Event with `items: [D-…]` closes it.
- MADR status vocabulary goes into `decision_status`. "superseded by ADR-x" becomes `status: superseded` + `superseded_by: D-…`, which must be consistent both ways.

### 2.12 Knowledge graphs with hierarchical summaries: GraphRAG and RAPTOR

**GraphRAG** (Edge et al., Microsoft, arXiv:2404.16130; `microsoft/graphrag` docs read directly):
- Entities and relationships are extracted, then "Hierarchical Leiden … recursive community-clustering … until we reach a community-size threshold … navigate and summarize the graph at different levels of granularity".
- The `communities` table has `community, parent, children, level, title, entity_ids, relationship_ids, text_unit_ids, period, size`. "Communities are strictly hierarchical."
- `community_reports` has `level, title, summary, full_content, rank, rating_explanation, findings[{summary, explanation}], period, size`.
- Optional `covariates` (claims) carry `status: TRUE|FALSE|SUSPECTED, start_date, end_date, source_text, text_unit_id`.
- Global search maps over community summaries at a chosen level (C0 = root … C3) and then reduces *(via search)*.

**RAPTOR** (Sarthi et al., ICLR 2024, arXiv:2401.18059; code read directly):
- Leaves are text chunks. Embeddings are reduced with UMAP and clustered with a **Gaussian Mixture Model with soft assignment**: `labels = [np.where(prob > threshold)[0] …]`, default threshold 0.1, `reduction_dimension 10`, `max_length_in_cluster 3500` tokens.
- Each cluster is summarized into a parent `Node(text, index, children, embeddings)`, recursively.
- Because assignment is soft, **one chunk can sit under several parents**: the "tree" is really a DAG.
- Retrieval either traverses the tree or searches a "collapsed tree" (all levels at once).

**Contributes:** a concrete, proven *schema for generated abstraction layers*. The pieces are numeric level, parent/children, member ids at the leaf level, generated title/summary/findings, rank, and a period for incremental updates.

**Apply:** the `Abstraction` type (§4.2) takes these fields almost one-for-one: `tier` (numeric depth, as in GraphRAG `level`), `parent`, `children`, `members`, `title`, `summary`, `findings`, `rank`, `as_of` (≈ `period`), `method` (leiden | raptor-gmm | fca | llm-cluster | rollup). Plus what they lack and we need:
- `input_hash` (sha256 of sorted member ids + member `ts`), so a regeneration with unchanged input is a no-op and staleness is detectable.
- `model` and `generated_by`, for provenance.
- `level` on the *semantic* axis (pattern by default, rule only after promotion).
- `promoted_to`, the human gate.

Rules:
- Abstractions are **derived data**. The reader must never treat them as evidence. A Lesson may cite an Abstraction *only together with* at least one member episode (the grounding rule).
- Allow multiple parents (RAPTOR soft clustering, FCA lattices). So `parent` is a list in practice; a single parent is allowed for GraphRAG-style strict trees.
- Use **GraphRAG-style claims (covariates) with status TRUE/FALSE/SUSPECTED** for LLM-extracted facts from messages, if that pipeline is built later. That is a ready-made "unverified fact" schema.

### 2.13 Temporal validity: bitemporal data (Snodgrass; SQL:2011; Graphiti/Zep)

**Contributes:** two independent time axes. **Valid time** is when a fact is true in the world. **Transaction time** is when the system held that version *(via search: Snodgrass's definitions as summarized)*. SQL:2011 implements them as *application-time period tables* (valid time) and *system-versioned tables* (transaction time, controlled by the DBMS; an update closes the current row and keeps it as history). The two combine into what the literature calls bitemporal tables; the standard itself does not use that word. Periods are declared over two existing date columns (`PERIOD FOR`) instead of a new interval type *(via search)*. Graphiti (Zep's temporal KG, arXiv:2501.13956) puts `valid_at`/`invalid_at` (world time) and `created_at`/`expired_at` (system time) on edges. On contradiction it **sets `invalid_at` on the old edge rather than deleting it**, choosing which edge to expire by ordering on `valid_at` *(via search: Graphiti docs, Zep blog)*.

**Apply** (fits the append-only log perfectly):
- `ts` = transaction-time start. It already exists everywhere.
- **Transaction-time end is derived, never written:** it is the `ts` of the first later line with the same id (latest-wins types), or of a record whose `supersedes` names it. This is exactly SQL:2011 system versioning, implemented by the log itself.
- Add **`valid_from` / `valid_to`** (format `date`; `datetime` where needed) to the record types that state facts or rules that can stop holding: Preference, Lesson, Principle, ReviewerRule, GlossaryTerm, StyleGuide, Concept, ConceptScheme, Decision, Issue, Client (rates), Account (forwarding), Platform (account status). Defaults: `valid_from` = date(ts), `valid_to` = open.
- **Query semantics.** `as_of(valid=t1, known=t2)` returns the records with `ts ≤ t2` that are not superseded by any line with `ts ≤ t2`, and whose valid interval contains t1. The current Preference rule, "newest per (topic, scope) wins", becomes "newest *recorded* among those *valid now*". This fixes the case where a preference is recorded *in advance* ("from November, invoice in KRW") or recorded late ("I've been doing X since June").
- **Validation:**
  - `valid_from ≤ valid_to`.
  - Two transaction-current records of the same type with the same key ((topic concept, scope) for Preference; (source, dir, client) for GlossaryTerm) and **overlapping** valid intervals, neither superseding the other, give a *conflict warning*. That is Graphiti's contradiction detection as a lint.
  - A record with `valid_to` in the past and no successor, if it is a `rule`-level type in current use, gives an "expired rule" warning, analogous to the existing `lesson_status: expired`.

### 2.14 Practitioner patterns: Tana supertags, Roam, Obsidian MOCs, Heptabase

- **Tana supertags.** A supertag is a type with fields attached to a node. **"Extend"** makes one supertag the base of another, "very similar to inheritance in object-oriented programming": adding a field to the base gives it to every extension, and "a search on the base tag will return all hits to #todo, and any other supertags that extend it" *(via search: Tana guide "When to use extend in supertags")*. User requests show that extension doesn't inherit everything, such as title construction. **Lesson for us:** type inheritance is valuable mainly for *query roll-up* and *shared field definitions*. Add an optional `extends:` to ontology types for shared field sets. Lesson, ReviewerRule, Preference and StyleGuide could extend a `Rule` base with `statement, scope, valid_from, valid_to, about, status`. Keep it single-inheritance, and resolve it in `schema_check`. Don't use it for abstraction levels.
- **Roam Research.** Everything is a block, a page is a block with a title, and block references transclude content *(via search; informal secondary)*. **Lesson:** stable, fine-grained ids plus reference-not-copy. The harness already does this with evt ids and `pointers`. The new rule "Abstraction cites ids, never copies text from vault records" is the Roam lesson applied to privacy.
- **Obsidian MOCs** (Nick Milo, *Linking Your Thinking*). A Map of Content is "simply notes linked to other related notes"; one note can sit on several maps or none. Create one at the "mental squeeze point", when there are too many notes to juggle *(via search: secondary blogs)*. **Lesson:** a hand-curated, *multi-parent* index that is created *on demand* when a cluster gets too big. It maps to `Abstraction` with `method: manual`. Trigger it automatically: when a concept's `about` count in a scope passes N (say 12), propose an MOC-style Abstraction.
- **Heptabase.** Cards live in a flat library and are placed on (nested) whiteboards, with sections inside a board. The vendor advises "two layers of sub-whiteboards" and using sections before adding a third layer *(via search: wiki.heptabase.com)*. **Lesson:** **cap the depth** of the hand-maintained hierarchy (about 2–3 tiers) and keep the underlying cards flat. For us: Concept `broader` depth ≤ 4 (a lint), and Abstraction tiers ≤ 3 for manual ones. Generated trees can be deeper, but are browsed collapsed (RAPTOR "collapsed tree").

### 2.15 schema.org's approach to extensibility

Read directly from `docs/howwework.html`, `docs/extension.html` and `data/schema.ttl`:
- Types form a tree under `Thing`, and multiple supertypes are rare. Properties attach through **`domainIncludes` / `rangeIncludes`**: *expected*, not logically entailing (1,230 `domainIncludes` statements in `schema.ttl`).
- **"schema.org does not define any notion of 'mandatory' property."** Requiredness belongs to consumers.
- **Deprecation, not deletion.** "It is exceptionally rare for a property, type or enumerated value to be deleted/removed without leaving it in the system as 'supersededBy' another." There are 88 `supersededBy` statements; retired terms move to the *attic*.
- A **`pending`** area holds experimental terms: "After a period of time of being in a pending status, depending on usage, adoption, discussions etc. a term will be incorporated into the core or get dropped." Hosted extensions were folded into core but "remain tagged with a label".
- **`additionalType`** adds a type from an external vocabulary to an item. **`Role`** "represents additional information about a relationship or property", for example that a membership "occurred during a particular time period". This is an n-ary/qualified relation pattern. **`DefinedTerm`/`DefinedTermSet`** play the SKOS role inside schema.org.

**Apply:**
- Adopt the **pending → stable | dropped** lifecycle for both ontology types and Concepts. The ontology already has `status: planned|active` for stores; add `concept_status: [pending, stable, deprecated]`. Concepts proposed by an LLM pass start `pending`, and only the user promotes them (consistent with "the user approves" elsewhere).
- **Never delete a type, field, enum value or concept. Mark it `superseded_by`.** The existing `renamed:` map is the type-level version; extend it to enum values (`value_aliases` already does this). This keeps old JSONL lines valid forever, which is essential in an append-only store.
- Keep the harness's `required` minimal and push "expected" fields to `expected_when`. That is schema.org's "no mandatory properties" made into a warning tier, which this ontology already does. Good.
- Use the **Role pattern** when a relation needs its own time or attributes: Contact *at* Organization *in role* recruiter *from* 2026-03. Model it as an embedded `{org, role, valid_from, valid_to}` object, not a new link type.

---

## 3. Design principles distilled

1. **Three orthogonal axes, never collapsed:** *type* (what kind of record), *scope* (where it applies), *abstraction_level* (how far it is from observation). Add *time* as a fourth (valid and transaction). Each is a field, not a type.
2. **Derivation, not instantiation, links the levels** (MLT/OntoClean; PROV `wasDerivedFrom`). Links go downward toward evidence. Higher levels must be **grounded**: at least one episode reachable through derivation links.
3. **Concepts are data, types are schema.** SKOS concepts give aboutness, and record types give structure. No punning. Hierarchy among concepts is `broader` (non-transitive assertion, transitive inference).
4. **Generated abstractions are derived, versioned by input hash, and promotable only by a human.** This follows RAPTOR/GraphRAG mechanics, with the harness's approval gate on top.
5. **Rationale is structured as Issue → Options × Criteria → Assessments → Chosen + Rationale → Confirmation → Review**: IBIS for the grammar, QOC for the matrix, Toulmin for the inside of each argument, MADR for the file shape, and DRL for dependency-triggered review.
6. **Deprecate, never delete; pending before stable** (schema.org).
7. **Valid time is written; transaction time is derived from the log** (SQL:2011 system versioning via append-only).

---

## 4. Proposed ontology extension (v0.3.0)

Everything below follows `ontology.yaml` conventions: one-line `store:` flow maps, one-line `fields`/`required` lists, `refs`, `enums` and `formats`, plus `#` comments. I tested it by loading `ontology.yaml` plus these blocks with `scripts/schema_check.py`'s own `yaml_load` and `Ontology`. It parses, and a malformed sample Decision produced the expected errors: missing required fields, a bad enum, a bad datetime, a bad `cpt-` ref prefix, a bad id pattern. The test script is `/tmp/claude-0/-home-user-albers-club/1397d302-c3cb-5329-ad06-e45b2c66c6d1/scratchpad/abs_scripts/test_ext.py`. Two new per-type keys, **`abstraction:`** and **`constraints:`**, are inert until the validator implements them (§4.6). `schema_check` ignores unknown type keys today, so adding them is safe.

### 4.1 New enums

```yaml
enums:
  # Distance from raw observation. Orthogonal to record type and to scope (scope = where it applies).
  abstraction_level: [raw, episode, pattern, rule, principle, meta]
  #   raw        bytes/text as received: Message, Attachment, Document, transcript
  #   episode    one occurrence, one time: Event, Task, Correction, Mishap, StylePair, Application line
  #   pattern    a regularity over >=2 episodes, descriptive ("this keeps happening"): Abstraction (cluster summary), Mishap.repeat_pattern
  #   rule       prescriptive, scoped guidance: Lesson, Preference, StyleGuide rule, ReviewerRule, Decision
  #   principle  cross-scope rule distilled from >=2 rules/scopes: Principle
  #   meta       about the representation itself: Concept, ConceptScheme, Rubric, the ontology
  concept_status: [pending, stable, deprecated]          # schema.org-style lifecycle (pending -> core | dropped)
  mapping_kind: [exact, close, broad, narrow, related]   # SKOS mapping properties, for links to external vocabularies
  abstraction_method: [manual, llm-cluster, fca, leiden, raptor-gmm, rollup]
  issue_status: [open, resolved, dropped, reopened]
  decision_status: [proposed, accepted, rejected, deprecated, superseded]   # MADR 4.0 status values
  assessment_polarity: [supports, opposes, neutral, n/a]  # QOC assessment (solid / dashed line); MADR good / bad / neutral
  argument_role: [pro, con, question]                     # IBIS argument kinds; `question` = an objection that opens a sub-issue
  strength: [strong, moderate, weak]
```

Why six levels, and why these names: they match the record types the harness already has, so each existing type gets a default without migration. They also separate *descriptive* generalization (pattern: "X keeps happening") from *prescriptive* generalization (rule: "do Y"), a split that DnS (Situation vs Description) and IAO (ICE vs directive ICE) both draw. Keep the values ASCII and ordered; the validator compares them by list index.

### 4.2 New types: Concept scheme (SKOS) and Abstraction (RAPTOR/GraphRAG/FCA)

```yaml
types:
  ConceptScheme:
    desc: a controlled vocabulary (skos:ConceptScheme), e.g. failure modes, decision criteria, topics; says which record fields draw from it
    store: {root: harness-data, path: concepts/schemes.jsonl, format: jsonl, append_only: true, privacy: harness-data, status: planned, writer: "skills/distill-principles, skills/review-week (proposals); the user approves"}
    id_prefix: cs-
    id_pattern: '^cs-[a-z0-9-]+$'
    unique_id: false
    fields: [id, ts, title, definition, top_concepts, used_by, status, superseded_by, valid_from, valid_to, attributed_to]
    required: [id, ts, title, used_by]
    refs: {top_concepts: Concept, superseded_by: ConceptScheme}
    enums: {status: concept_status}
    formats: {ts: datetime, valid_from: date, valid_to: date}
    abstraction: {default: meta}
    coverage: {provenance: [attributed_to], intent: definition, meta: [used_by]}

  Concept:
    desc: one SKOS concept (a meaning, not a record type); records point at concepts through `about`; newest line per id wins
    store: {root: harness-data, path: concepts/concepts.jsonl, format: jsonl, append_only: true, privacy: harness-data, status: planned, writer: "skills/review-week, skills/distill-principles (status pending); the user promotes to stable"}
    id_prefix: cpt-
    id_pattern: '^cpt-[a-z0-9-]+$'
    unique_id: false
    fields: [id, ts, pref_label, alt_labels, hidden_labels, definition, scope_note, example, in_scheme, broader, related, mappings, status, superseded_by, valid_from, valid_to, attributed_to, evidence, level_hint]
    required: [id, ts, pref_label, in_scheme, status]
    refs: {in_scheme: ConceptScheme, broader: Concept, related: Concept, superseded_by: Concept}
    enums: {status: concept_status, level_hint: abstraction_level}
    formats: {ts: datetime, valid_from: date, valid_to: date}
    abstraction: {default: meta}
    constraints:
      - {rule: acyclic, field: broader}                          # no concept is its own ancestor
      - {rule: disjoint_closure, field: related, with: broader}  # SKOS: related is disjoint with broaderTransitive
      - {rule: unique_label, field: pref_label, per: in_scheme}  # SKOS: at most one prefLabel per language; here unique per scheme
      - {rule: requires_if, field: superseded_by, when: {status: deprecated}}
    coverage: {provenance: [attributed_to, evidence], intent: definition, meta: [in_scheme, broader]}

  Mapping:      # embedded in Concept.mappings
    desc: a link from a Concept to a term in another vocabulary (skos:exactMatch | closeMatch | broadMatch | narrowMatch | relatedMatch)
    store: {root: harness-data, path: concepts/concepts.jsonl, format: embedded, append_only: true, privacy: harness-data, status: planned, writer: "as Concept"}
    fields: [kind, target, note]
    required: [kind, target]
    enums: {kind: mapping_kind}

  Abstraction:
    desc: a generated summary node over a set of records (RAPTOR tree node / GraphRAG community report / FCA formal concept); derived, regenerable, never hand-edited
    store: {root: harness-data, path: "abstractions/<area>/YYYY-MM.jsonl", format: jsonl, append_only: true, privacy: harness-data, status: planned, writer: "scripts/abstract.py (planned), skills/review-week"}
    id_prefix: abs_
    id_pattern: '^abs_\d{8}_[0-9a-f]{6}$'
    unique_id: true
    fields: [id, ts, level, tier, method, scope, members, member_types, parent, children, intent_concepts, title, summary, findings, rank, model, generated_by, input_hash, as_of, valid_from, valid_to, superseded_by, promoted_to, status]
    required: [id, ts, level, method, members, summary, input_hash]
    refs: {parent: Abstraction, children: Abstraction, intent_concepts: Concept, superseded_by: Abstraction, generated_by: Event}
    enums: {level: abstraction_level, method: abstraction_method, status: concept_status}
    formats: {ts: datetime, as_of: datetime, valid_from: date, valid_to: date, scope: scope, input_hash: sha256}
    abstraction: {default: pattern, allowed: [pattern, rule]}
    constraints:
      - {rule: min_items, field: members, n: 2}
      - {rule: acyclic, field: parent}
      - {rule: level_monotone, field: members}                   # every member is at a lower level, or a lower tier of Abstraction
    coverage: {provenance: [members, method, model, generated_by, input_hash], intent: null, meta: [intent_concepts, level]}
```

Notes:
- **Concept vs Abstraction.** A Concept is an *intension* (a definition, curated, stable ids, shared across scopes). An Abstraction is an *extension summary* (a set of member records plus a generated text, as of a date). An FCA formal concept is the bridge: its intent is a set of Concepts and its extent is an Abstraction's `members`.
- **Privacy.** `Abstraction.summary` over vault records (Message/Thread) must stay in `msg-vault`. Add a second store path or forbid vault members. Proposed rule: if any member has `privacy: vault`, the Abstraction's store root must be `msg-vault`. Validator rule: `privacy_floor`.
- **Ids for Concept** are human slugs (`cpt-scope-creep`), so they read well inside other records and in Markdown. `unique_id: false` plus newest-line-wins gives the concept history, and its definition changes are SKOS `changeNote`s for free.

Example lines:

```json
{"id":"cs-failure-mode","ts":"2026-10-16T22:10:00+00:00","title":"Failure modes","definition":"Recurring ways work goes wrong","used_by":["Mishap.about","Correction.about","Event.labels"],"top_concepts":["cpt-verification-skipped","cpt-scope-misread"]}
{"id":"cpt-verification-skipped","ts":"2026-10-16T22:11:00+00:00","pref_label":"verification skipped","alt_labels":["no verify","검증 생략"],"hidden_labels":["verfication skipped"],"definition":"A step was reported done without a verification event","in_scheme":"cs-failure-mode","broader":["cpt-process-gap"],"status":"pending","attributed_to":"agent:librarian"}
{"id":"abs_20261016_a1b2c3","ts":"2026-10-16T23:00:00+00:00","level":"pattern","tier":1,"method":"fca","scope":"translation","members":["evt_20261002_101500_ab12","evt_20261009_141200_cd34","evt_20261014_090100_ef56"],"intent_concepts":["cpt-verification-skipped","cpt-deadline-pressure"],"summary":"Three translation deliveries in October skipped QA under deadline pressure.","input_hash":"<sha256>","model":"sonnet"}
```

### 4.3 Decision rationale: Issue and Decision (IBIS + QOC + Toulmin + MADR)

```yaml
  Issue:
    desc: an open question (IBIS issue / QOC question); one issue can get several Decisions over time
    store: {root: project, path: rationale/issues.jsonl, format: jsonl, append_only: true, privacy: repo, status: planned, writer: "skills/why, skills/retro"}
    id_prefix: iss-
    id_pattern: '^iss-\d{8}-\d+$'
    unique_id: false
    fields: [id, ts, question, context, scope, status, parent_issue, raised_by, about, drivers, source_event, valid_from, valid_to]
    required: [id, ts, question, status]
    refs: {parent_issue: Issue, about: Concept, source_event: Event}
    enums: {status: issue_status}
    formats: {ts: datetime, scope: scope, valid_from: date, valid_to: date}
    abstraction: {default: episode}
    coverage: {provenance: [raised_by, source_event], intent: question, meta: [about, drivers]}

  Decision:
    desc: a choice on an Issue among >=2 Options, judged on Criteria, with rationale and a checkable prediction (skill `why`); a status change appends a new line with the same id
    store: {root: project, path: rationale/decisions.jsonl, format: jsonl, append_only: true, privacy: repo, status: planned, writer: "skills/why (decisions.md becomes a rendered view)"}
    id_prefix: D-
    id_pattern: '^D-\d{8}-\d+$'
    unique_id: false
    fields: [id, ts, issue, claim, status, options, criteria, assessments, arguments, chosen, rationale, qualifier, rebuttals, consequences, confirmation, expected_outcome, review_date, decided_on, decision_makers, consulted, scope, about, evidence, supersedes, superseded_by, valid_from, valid_to, event, intent, situation, meta, forced, reasons, alternatives]
    required: [id, ts, claim, status, options, chosen, rationale]
    refs: {issue: Issue, about: Concept, supersedes: Decision, superseded_by: Decision, event: Event}
    enums: {status: decision_status}
    aliases: {reasons: rationale}
    formats: {ts: datetime, review_date: date, decided_on: date, valid_from: date, valid_to: date, scope: scope}
    abstraction: {default: rule}
    constraints:
      - {rule: ref_in, field: chosen, in: "options[].id"}
      - {rule: min_items, field: options, n: 2, unless: forced}
      - {rule: ref_in, field: "assessments[].option", in: "options[].id"}
      - {rule: ref_in, field: "assessments[].criterion", in: "criteria[].id"}
      - {rule: covered, field: criteria, by: "assessments[].criterion"}   # every criterion is used by some assessment
      - {rule: cites, field: rationale, any_of: ["criteria[].id", "arguments[].id"]}   # no "seemed best"
      - {rule: requires_if, field: superseded_by, when: {status: superseded}}
      - {rule: date_order, fields: [decided_on, review_date]}
      - {rule: interval, from: valid_from, to: valid_to}
    coverage: {provenance: [evidence, event, decision_makers], intent: intent, meta: meta}

  Option:       # embedded in Decision.options
    desc: one considered option (IBIS position / QOC option / MADR considered option)
    store: {root: project, path: rationale/decisions.jsonl, format: embedded, append_only: true, privacy: repo, status: planned, writer: "as Decision"}
    fields: [id, title, description, pointer]
    required: [id, title]

  Criterion:    # embedded in Decision.criteria
    desc: a basis for choosing (QOC criterion / MADR decision driver); `concept` makes it reusable across decisions
    store: {root: project, path: rationale/decisions.jsonl, format: embedded, append_only: true, privacy: repo, status: planned, writer: "as Decision"}
    fields: [id, statement, concept, weight, must]
    required: [id, statement]
    refs: {concept: Concept}

  Assessment:   # embedded in Decision.assessments; a Toulmin argument about one option x criterion
    desc: how one option fares on one criterion, with grounds and warrant
    store: {root: project, path: rationale/decisions.jsonl, format: embedded, append_only: true, privacy: repo, status: planned, writer: "as Decision"}
    fields: [option, criterion, polarity, strength, grounds, warrant, backing, qualifier, rebuttal]
    required: [option, criterion, polarity]
    enums: {polarity: assessment_polarity, strength: strength}

  Argument:     # embedded in Decision.arguments; IBIS pro/con not tied to a single criterion
    desc: an IBIS argument for or against an option
    store: {root: project, path: rationale/decisions.jsonl, format: embedded, append_only: true, privacy: repo, status: planned, writer: "as Decision"}
    fields: [id, option, role, claim, grounds, warrant, source, raises_issue]
    required: [id, option, role, claim]
    enums: {role: argument_role}
```

Compatibility with today's `Decision`:
- The id format is unchanged (`D-YYYYMMDD-n`). The old fields `reasons`, `alternatives`, `evidence`, `expected_outcome`, `review_date`, `intent`, `situation`, `meta`, `scope` and `event` remain allowed, and `aliases: {reasons: rationale}` maps the old name.
- Migration of each `decisions.md` entry:
  - claim → claim
  - Reasons → rationale
  - "Alternatives rejected and why" → one `options[]` item per alternative plus `arguments[]` with `role: con`, while `chosen` is the claim's option
  - status: accepted
  - `forced: true` when only one option was recorded, so old records pass `min_items`.
- `decisions.md` becomes a **MADR-shaped rendering**: Context and Problem Statement = Issue.question + context; Decision Drivers = criteria; Considered Options; Decision Outcome "Chosen option: … because …"; Consequences; Confirmation; Pros and Cons per option from assessments and arguments. Humans keep reading Markdown, and machines validate JSONL.
- Store choice: the project root and `repo` privacy match where decisions live today. Cross-project decisions (harness design) go into the harness repo's own `rationale/`, so ADRs for `claude-harness` itself use the same schema.

Add to Lesson (Toulmin) and to Event (DnS feedback):

```yaml
  # Lesson: add fields; keep everything else as in v0.2
  #   fields: [..., about, level, warrant, rebuttal, valid_from, valid_to, superseded_by]
  #   refs:   {about: Concept, superseded_by: Lesson}
  #   formats: {..., valid_from: date, valid_to: date}
  #   abstraction: {default: rule}
  # Event: add `satisfies` / `violates` (lists of L- | R- | pref_ | D- ids) for verification, correction and mishap events,
  # so "how often was lesson L followed vs broken" is countable (Descriptions-and-Situations).
```

Example Decision line:

```json
{"id":"D-20261016-1","ts":"2026-10-16T22:00:00+00:00","issue":"iss-20261016-1","claim":"Store decisions as JSONL with a rendered decisions.md","status":"accepted",
 "options":[{"id":"o1","title":"JSONL + rendered md"},{"id":"o2","title":"md only (today)"}],
 "criteria":[{"id":"c1","statement":"machine-checkable by schema_check","concept":"cpt-validatable","must":true},{"id":"c2","statement":"readable by the user without tools","concept":"cpt-human-readable"}],
 "assessments":[{"option":"o1","criterion":"c1","polarity":"supports","strength":"strong","grounds":["scripts/schema_check.py PARSED_FORMATS"]},
                {"option":"o2","criterion":"c1","polarity":"opposes","strength":"strong","warrant":"md stores are listed but not parsed"},
                {"option":"o1","criterion":"c2","polarity":"neutral","rebuttal":"only if the renderer is run after every append"}],
 "chosen":"o1","rationale":"o1 meets must-criterion c1; c2 is held by rendering","consequences":["Good: constraints checkable","Bad: one more script to keep in sync"],
 "confirmation":"schema_check --type Decision passes on all projects; verify event items:[D-20261016-1]","expected_outcome":"0 unparsed decisions by 2026-11-30","review_date":"2026-11-30","scope":"global","about":["cpt-validatable"]}
```

### 4.4 Abstraction axis on existing types (defaults, no data migration)

Add an `abstraction:` key to every existing type. Records may carry `level` only to *override* the default. That should be rare; Lesson may be `pattern` while still descriptive.

| level | types (default) |
|---|---|
| raw | Message, Attachment, Thread, Document, StyleSample, BackcatalogRow, SyncCursor |
| episode | Event, Task, Correction, Mishap, SessionNote, Handoff, ProgressItem, StylePair, Application, JobLead, IntakeLogEntry, Evaluation, EvalRun, Invoice, LedgerEntry, Asset, Palette, Issue |
| pattern | Abstraction; WikiPage (*descriptive summary of a source*, `allowed: [pattern]`) |
| rule | Lesson, Preference, StyleGuide, ReviewerRule, GlossaryTerm, Decision, EvalTask |
| principle | Principle |
| meta | Concept, ConceptScheme, Rubric, (the ontology itself) |
| n/a | Project, Client, Organization, Contact, Account, Platform, HarnessState: *continuants*, not claims; set `abstraction: {default: null}` |

The YAML shape on each type:

```yaml
  Lesson:
    # ... unchanged keys ...
    abstraction: {default: rule, allowed: [pattern, rule]}
  Principle:
    abstraction: {default: principle}
    constraints:
      - {rule: grounded, via: [evidence], min_episodes: 2, min_scopes: 2}   # "distilled from 2+ sources" made checkable
```

### 4.5 Relations: PROV/SKOS alignment and the new links

```yaml
# New key per relation: `prov` = the PROV-O / SKOS term it specializes (documentation + export), `level` = expected direction on the abstraction axis.
relations:
  - {name: about,          domain: [Event, Mishap, Lesson, Principle, Decision, Issue, ResearchNote, StylePair, WikiPage, Abstraction], range: [Concept], via: "<type>.about (cpt- ids)", prov: "dcterms:subject / iao:is_about"}
  - {name: broader,        domain: [Concept], range: [Concept], via: "Concept.broader", prov: "skos:broader", constraint: acyclic}
  - {name: related,        domain: [Concept], range: [Concept], via: "Concept.related", prov: "skos:related", constraint: "disjoint with broader closure"}
  - {name: in_scheme,      domain: [Concept], range: [ConceptScheme], via: "Concept.in_scheme", prov: "skos:inScheme"}
  - {name: summarizes,     domain: [Abstraction], range: [Event, Mishap, Correction, StylePair, Lesson, ResearchNote, Abstraction], via: "Abstraction.members", prov: "prov:wasDerivedFrom", level: up}
  - {name: promoted_to,    domain: [Abstraction], range: [Lesson, Principle, Concept], via: "Abstraction.promoted_to", prov: "prov:wasInfluencedBy", level: up}
  - {name: generalizes,    domain: [Lesson, Principle, StyleGuide], range: [Mishap, Correction, SessionNote, Lesson, StylePair, Abstraction], via: "Lesson.learned_from, Principle.evidence, StyleGuide.evidence", prov: "prov:wasDerivedFrom", level: up}
  - {name: decides,        domain: [Decision], range: [Issue], via: "Decision.issue", prov: "prov:wasGeneratedBy (of the decision activity)"}
  - {name: sub_issue_of,   domain: [Issue], range: [Issue], via: "Issue.parent_issue", prov: null, constraint: acyclic}
  - {name: generated_by,   domain: [Abstraction, Decision, Lesson, Concept], range: [Event], via: "Abstraction.generated_by, Decision.event, Lesson (via the announcing Event)", prov: "prov:wasGeneratedBy"}
  - {name: attributed_to,  domain: [Event, Concept, ConceptScheme, Decision], range: [agent+model], via: "Event.actor+model, Concept.attributed_to, Decision.decision_makers", prov: "prov:wasAttributedTo"}
  - {name: on_behalf_of,   domain: [Event], range: [agent+model], via: "actor agent:<name> acting for `me` (implicit)", prov: "prov:actedOnBehalfOf"}
  - {name: quoted_from,    domain: [StylePair, ReviewerRule, StyleSample], range: [Message, Document], via: "StylePair.source, ReviewerRule.quote+source, StyleSample.message_id", prov: "prov:wasQuotedFrom"}
  # add to new relations (not yet in v0.2):
  #   - {name: satisfies / violates, domain: [Event], range: [Lesson, ReviewerRule, Preference, Decision], via: "Event.satisfies / Event.violates", prov: null}   # DnS
  #   - {name: depends_on, domain: [Decision], range: [Decision, Preference, Lesson, Principle], via: "Decision.depends_on", prov: "prov:wasInfluencedBy"}  # DRL dependency mgmt
```

Also annotate the **existing** relations with `prov:`:
- `derived_from` → `prov:wasDerivedFrom`
- `produced_by` → `prov:wasAttributedTo` (+ `wasAssociatedWith` for activities)
- `supersedes` → `prov:wasRevisionOf` (inverse direction)
- `evidence_for` / `proven_by` → `prov:wasDerivedFrom` (Toulmin grounds)
- `corrects` → `prov:wasRevisionOf` + `wasInvalidatedBy`
- `labels` → `prov:Bundle` membership
- `part_of` → `dcterms:isPartOf`

The relations block parses with the harness loader (13 entries, tested).

### 4.6 Bitemporal fields and validation rules for `schema_check.py`

Fields:
- Add `valid_from`, `valid_to` (`formats: date`) to Preference, Lesson, Principle, StyleGuide, ReviewerRule, GlossaryTerm, Client, Account, Platform, Concept, ConceptScheme, Issue, Decision.
- Add `superseded_by` where `supersedes` exists, for readability only. In append-only stores the canonical link is the *later* record's `supersedes`, and `superseded_by` must agree if present.
- Do **not** add `recorded_to`/`tx_to`: the transaction-time end is derived.

Constraint engine (new; each rule is small and stdlib-only). Run it after folding latest-wins ids:

| rule | meaning | severity |
|---|---|---|
| `acyclic(field)` | no cycle along `field` (Concept.broader, Abstraction.parent, Issue.parent_issue) | error |
| `disjoint_closure(field, with)` | no `related` target is in the transitive `broader` closure (either direction) | error |
| `unique_label(field, per)` | label unique among current records sharing `per` | error |
| `requires_if(field, when)` | `field` present when condition holds (deprecated ⇒ superseded_by) | error |
| `min_items(field, n, unless)` | list length ≥ n unless boolean flag set | error |
| `ref_in(field, in)` | value(s) of a nested path exist in another nested path of the same record | error |
| `covered(field, by)` | every item id of `field` is referenced by `by` | warning |
| `cites(field, any_of)` | free-text field mentions at least one id from the listed paths | warning |
| `date_order(fields)` | dates non-decreasing in the given order | error |
| `interval(from, to)` | `from ≤ to` when both present | error |
| `level_monotone(field)` | every linked record's level ≤ this record's level (Abstraction: member tier < own tier) | error |
| `grounded(via, min_episodes, min_scopes)` | following derivation links reaches ≥ N `episode` records in ≥ M distinct scopes | warning |
| `time_consistent` (global) | `ts(derived) ≥ ts(source)` for every derivation link | warning |
| `valid_overlap(key)` (global) | two transaction-current records with the same key and overlapping valid intervals, neither superseding the other | warning |
| `privacy_floor` (global) | a record that copies or summarizes a `vault` record must be stored in `msg-vault` | error |
| `no_pun` (global) | Concept.pref_label ≠ any `types:` key unless an explicit `type:` mapping exists | warning |

Validator extensions needed:
- `refs` accepts a **list of target types**. Today `str(v)` would stringify a list, so `refs: {members: [Event, Mishap, Abstraction]}` needs a two-line change in `validate_records`: accept if any target prefix matches.
- An `abstraction:` reader that checks `level` ∈ `allowed`.
- A `--as-of VALID[,KNOWN]` flag for the fold. That makes the bitemporal query a CLI feature (`schema_check --as-of 2026-09-01 --type Preference`) and gives `skills/interview` a correct "current preferences" function.

### 4.7 Rollout order (smallest useful first)

1. **Concepts (SKOS)**: seed `cs-failure-mode` and `cs-decision-criterion` from existing `labels`/`repeat_pattern`/`kind_of_thing` values (one `review-week` pass), all `pending`. Add `about` to Event/Mishap/Lesson/Decision. Everything after this depends on a controlled vocabulary.
2. **Abstraction axis**: add `abstraction:` defaults (pure ontology change; no data), plus `level_monotone` and `grounded` warnings. Run them over existing Lessons and Principles to find ungrounded ones.
3. **Decision JSONL**: change skill `why` to write Issue + Decision lines and render `decisions.md`. Migrate old entries with `forced: true`.
4. **Bitemporal**: add `valid_from/valid_to` to Preference first (biggest win), then Lesson, ReviewerRule and GlossaryTerm. Add `--as-of`.
5. **Abstraction generation**: `method: fca` first (deterministic, free). Use `llm-cluster`/`raptor-gmm` only for large scopes, under the fanout policy. Promotion to Lesson/Concept stays a human approval.
6. **PROV export** (optional): a script that emits PROV-O Turtle from the log plus the `relations.prov` mapping, for audit or graph tooling. Nothing in the harness needs RDF at runtime.

### 4.8 Anti-patterns to avoid (and why)

- **One type per level or per topic** ("PatternLesson", "TranslationMishap"). That is the Wikidata instance/subclass confusion and OntoClean's anti-rigid-subsumes-rigid. Use fields and concepts instead.
- **Storing both `broader` and `narrower`.** In an append-only log they will drift. Store one direction.
- **Treating generated summaries as evidence.** RAPTOR/GraphRAG nodes are lossy and model-dependent. Require episode grounding.
- **Hard-deleting or renaming enum values or concepts.** Old lines become invalid. Use `superseded_by`, `value_aliases` and `renamed:` (schema.org practice).
- **Writing transaction-end timestamps.** That duplicates what the log already proves and invites inconsistency.
- **Free-text rationale only.** Without criteria and assessments, you can't learn which drivers predict superseded decisions, so the improvement loop has nothing to learn from.

---

## 5. Sources

Primary files read from local clones (`/tmp/claude-0/-home-user-albers-club/1397d302-c3cb-5329-ad06-e45b2c66c6d1/scratchpad/abs/`):
- W3C PROV-O source: https://github.com/w3c/prov (`ontology/prov-o.ttl`); Recommendation at https://www.w3.org/TR/prov-o/ (unreachable here)
- BFO 2020 / ISO/IEC 21838-2: https://github.com/BFO-ontology/BFO-2020 (`21838-2/owl/bfo-core.ttl`)
- Information Artifact Ontology: https://github.com/information-artifact-ontology/IAO (`iao.owl`)
- schema.org: https://github.com/schemaorg/schemaorg (`docs/howwework.html`, `docs/extension.html`, `data/schema.ttl`)
- MADR 4.0.0: https://github.com/adr/madr (`template/adr-template.md`, `CHANGELOG.md`)
- GraphRAG: https://github.com/microsoft/graphrag (`docs/index/outputs.md`, `docs/index/default_dataflow.md`)
- RAPTOR: https://github.com/parthsarthi03/raptor (`raptor/cluster_utils.py`, `raptor/tree_structures.py`)
- Skosify (SKOS validation tool): https://github.com/NatLibFi/Skosify

Via web search (snippets; full text not fetched):
- SKOS Reference: https://www.w3.org/TR/skos-reference/ ; SKOS RDF: https://www.w3.org/2009/08/skos-reference/skos.rdf ; Primer: https://www.w3.org/TR/skos-primer/ ; Baker et al., "Key choices in the design of SKOS": https://www.sciencedirect.com/science/article/pii/S1570826813000176
- Noy (ed.), *Representing Classes As Property Values on the Semantic Web*, W3C Note 2005: https://www.w3.org/TR/swbp-classes-as-values/
- OWL 2 punning discussion: https://lists.w3.org/Archives/Public/semantic-web/2011Jan/0061.html ; https://www.ceur-ws.org/Vol-1350/paper-55.pdf ; no-punning SHACL pattern: https://nfdi.fiz-karlsruhe.de/matwerk/shapes/no-punning/pattern/
- Multi-level modeling: https://link.springer.com/article/10.1007/s10270-016-0565-6 ; https://link.springer.com/article/10.1007/s10270-022-00987-1 ; Brasileiro et al., WWW 2016: https://nemo.inf.ufes.br/wp-content/papercite-data/pdf/applying_a_multi_level_modeling_theory_to_assess_taxonomic_hierarchies_in_wikidata_2016.pdf
- OntoClean: https://en.wikipedia.org/wiki/OntoClean ; Guarino & Welty overview: https://pubs.dbs.uni-leipzig.de/dc/files/GuarinoWeltyOntoCleanv3.pdf
- Formal Concept Analysis: https://en.wikipedia.org/wiki/Formal_concept_analysis ; https://galactic.univ-lr.fr/theory/concepts.html
- ODP / DUL: https://istc.cnr.it/en/node/72377 (Presutti & Gangemi, ER 2008); DUL docs (archived): https://akswnc7.informatik.uni-leipzig.de/dstreitmatter/archivo/ontologydesignpatterns.org/ont--dul--DUL--owl/2025.05.24-011855/ont--dul--DUL--owl_type=generatedDocu.html
- DOLCE: https://arxiv.org/pdf/2308.01597 ; https://www.loa.istc.cnr.it/old/Papers/DOLCE-EKAW.pdf ; WonderWeb D18: https://www.loa.istc.cnr.it/old/Papers/D18.pdf
- IBIS (Kunz & Rittel 1970), via https://eight2late.com/category/issue-based-information-system/page/6 ; Compendium: https://en.wikipedia.org/wiki/Compendium_(software) ; https://research-archive.stem.open.ac.uk/stemra-data/uploads/files/papers/SBS-HT02-Compendium.pdf
- QOC (MacLean et al. 1991): https://acawiki.org/Questions,_Options,_and_Criteria:_Elements_of_design_space_analysis ; https://europe.naverlabs.com/history/past-research/design-space-analysis/
- DRL (Lee 1989): https://dspace.mit.edu/handle/1721.1/41499 ; SIBYL: https://dspace.mit.edu/handle/1721.1/49037
- Toulmin: Verheij, *Argumentation* 19 (2005): https://www.ai.rug.nl/~verheij/publications/pdf/toulmin2005.pdf ; https://icar.cnrs.fr/dicoplantin/layout-of-argument-toulmin-e/
- Nygard ADR (2011) as reproduced: https://docs.arc42.org/tips/9-5/ ; https://faq.arc42.org/questions/C-9-3/
- GraphRAG paper: https://arxiv.org/abs/2404.16130 ; RAPTOR paper: https://arxiv.org/abs/2401.18059
- Bitemporal / SQL:2011: https://old.dbs.uni-leipzig.de/file/Temporal%20features%20in%20SQL2011.pdf ; https://www2.cs.arizona.edu/~rts/sql3.html ; Graphiti temporal model: https://mintlify.com/getzep/graphiti/concepts/temporal-model ; https://blog.getzep.com/beyond-static-knowledge-graphs/
- Tana extend: https://tana.inc/articles/when-to-use-extend-in-supertags ; Obsidian MOCs: https://obsidian.rocks/maps-of-content-effortless-organization-for-notes/ ; Heptabase: https://wiki.heptabase.com/organize-knowledge-and-projects ; Roam (informal): https://aisotools.com/compare/heptabase-vs-roam-research

Unreachable from this sandbox (DNS/403): w3.org, arxiv.org, wikipedia.org, ontologydesignpatterns.org (portal catalogue), schema.org (site; repo used instead), basic-formal-ontology.org, loa.istc.cnr.it, tana.inc docs, dl.acm.org, semanticscholar.org. GitHub repos that needed auth (so probably nonexistent names): `dolce-ontology/dolce`, `iaoverse/iao`, Compendium source.
