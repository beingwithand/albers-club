# Levels of Abstraction and Levels of Learning: Thinkers, Criteria, and a Level Model for a Personal AI Harness

Research date: 2026-10-16. Purpose: ground a personal AI-harness ontology that separates raw observations from interpretations, decisions, patterns, principles and meta-patterns, using the major theories of abstraction levels and learning levels.

---

## 0. Method and source access

**Reachability.** From this session's network, every direct fetch failed. The egress proxy refused CONNECT (403) or DNS did not resolve for these hosts:
plato.stanford.edu (SEP), worrydream.com (Bret Victor), philarchive.org, link.springer.com, arxiv.org, en.wikipedia.org, zhang.ist.psu.edu (Frické PDF), vordenker.de (Bateson PDF). **No SEP entry could be read directly.** Sources were therefore verified only through extended web search, which returns snippets and summaries of the pages listed below. Claims that rest on my background knowledge of the primary texts, not on a retrieved snippet, carry the tag **[bk]**. Quote primary texts only after checking them against the PDFs listed at the end, all of which are publicly hosted.

**Format of each entry.** (a) the levels and their structure; (b) **criteria** that separate one level from the next; (c) how movement between levels happens; (d) failure modes; (e) **what it means for the harness** (tagging, level-jump detection, storing learning about learning).

---

## 1. Russell's theory of types, and Bateson's logical categories of learning (Learning 0 to IV)

### 1a. Russell (background for Bateson)
- **Structure [bk]:** Entities are stratified by type: individuals (type 0), classes of individuals (type 1), classes of classes (type 2), and so on. The ramified theory (Whitehead and Russell, *Principia Mathematica*, 1910–13) also stratifies propositional functions by *order*. The motive is the **vicious-circle principle**: "whatever involves all of a collection must not be one of the collection." This blocks Russell's paradox, the class of all classes that are not members of themselves.
- **Criterion:** An expression of type n may take arguments only of type less than n. A class is never a member of itself. A statement about a set of statements belongs to a higher type than the statements it covers.
- **Failure mode:** Self-reference and impredicative definitions produce paradox. In practical terms, a statement quantifies over a collection it belongs to.
- **Harness implication:** This is the root formal criterion. **A record's level is fixed by the level of the things it is *about*.** A record that quantifies over records of level n sits at level n+1 or higher. A record must never count itself as evidence. A meta-pattern such as "my patterns are usually wrong" must not appear in its own support set.

### 1b. Bateson, "The Logical Categories of Learning and Communication" (1964/1968; in *Steps to an Ecology of Mind*, 1972)
Search confirmed that Bateson applies Russell's theory of logical types to learning, and confirmed his own definitions:
- **Learning 0:** "specificity of response, which, right or wrong, is not subject to correction." Examples: receiving a signal, a fixed reflex, a thermostat reading.
- **Learning I:** "change in specificity of response by correction of errors of choice within a set of alternatives." Examples: classical and operant conditioning, habituation.
- **Learning II (deutero-learning):** "change in the process of Learning I, e.g. a corrective change in the set of alternatives from which choice is made, or ... a change in how the sequence of experience is punctuated." This is learning to learn: character, habits of perceiving contexts, transference. Bateson first described deutero-learning in 1942 as the observed speed-up of learning across repeated experiments, and he later renamed proto- and deutero-learning as Learning I and II (Lee et al., UGA).
- **Learning III:** "change in the process of Learning II, e.g. a corrective change in the system of sets of alternatives." Bateson calls it difficult and rare. He locates it in some psychotherapy, religious conversion and profound reorganizations of self, and warns that it can be dangerous **[bk]**.
- **Learning IV:** "change in Learning III." He suggests it probably does not occur in any adult living organism and may correspond to evolutionary or phylogenetic change **[bk]**. Secondary sources agree that he says little about it.

**Criteria between levels.** Each level is a **change in the process** of the level below. The test is *what is changing*:
- L0: nothing changes. The same stimulus produces the same response.
- LI: which item is chosen from a fixed set changes.
- LII: the set of alternatives, or the way contexts are punctuated or recognized, changes.
- LIII: the system of sets changes, meaning the premises that generate contexts.

**Movement.** Upward movement is driven by **contradiction or double bind** at the level below. A higher-level change follows repeated failure that the lower level cannot resolve **[bk]**. Bateson's account of schizophrenia is the canonical level-confusion pathology: an inability to distinguish messages from messages about messages (the frame or context markers). The double-bind theory treats it as a breakdown in discriminating logical types.

**Failure modes:**
- **Level confusion:** treating a context marker or frame as part of the message. In the harness, this is treating "the user was being sarcastic" (a frame) as if it were a fact about the content.
- **Over-ascension:** claiming LII or LIII change when only LI happened. Example: "I've transformed my approach" when only a preference flipped.
- **Under-ascension:** endlessly re-tuning LI choices when the alternative set itself is wrong.

**Harness implication.** Bateson gives the cleanest **operational test**. For every learning event, record the *delta object*:
- `delta: none` corresponds to L0, an observation only.
- `delta: choice` corresponds to LI. Example: picked tool B over tool A next time.
- `delta: option_set` or `delta: context_classification` corresponds to LII. Example: added a new option, or started treating "deploy requests" as a distinct context.
- `delta: option_set_generator` corresponds to LIII. Example: changed how the harness decides which contexts exist at all.

To detect a level jump, compare the diff's target type against the claimed level. Store "learning about learning" (LII) as records whose subject is a set of LI events. Example: "in the last 20 corrections, ~70% were in the `git` context". This mirrors the deutero-learning *rate* measure.

---

## 2. Argyris and Schön: single-, double- and triple-loop learning

- **Structure:** Argyris and Schön (*Theory in Practice*, 1974; *Organizational Learning*, 1978).
  - **Single-loop:** "an error is detected and corrected without questioning or altering the governing variables."
  - **Double-loop:** the governing variables themselves (values, norms, policies) are examined and changed.
  - **Deutero-learning:** in their usage, the organization learns how to carry out single- and double-loop learning.
  - Supporting distinctions: **espoused theory vs theory-in-use**, and **Model I** (defensive, unilateral control, win/don't lose; inhibits double-loop learning) vs **Model II** (valid information, free and informed choice, internal commitment; enables it).
- **Triple-loop:** Tosey, Visser and Saunders (2012) show that the term **does not occur in Argyris and Schön's published work**. Its conceptualizations are diverse, often weakly grounded and normatively driven. The review identifies three distinct readings: a level above double-loop, a restatement of deutero-learning, and Bateson's Learning III.
- **Criteria:**
  - Single-loop changes the *action strategy* and leaves the goal or value unchanged.
  - Double-loop changes the *governing variable* that defines success.
  - Triple-loop, in its most defensible reading, changes *how governing variables are chosen*: the learning process or identity.
- **Movement:** Double-loop learning is usually triggered by repeated single-loop failure, or by surfacing the gap between espoused theory and theory-in-use. Model I defensive routines suppress it.
- **Failure modes:**
  - **Defensive routines** and **skilled incompetence**: smoothly repeating single-loop fixes that hide the real problem.
  - The espoused/in-use gap: claiming a principle you do not follow.
- **Harness implication:**
  - (1) Store **principles in two fields**: `espoused` (written down) and `in_use` (inferred from decision logs). A recurring discrepancy is itself a high-value meta-record.
  - (2) Tag every correction event with `loop: single | double | triple` by what it changed:
    - `single`: the action or decision record.
    - `double`: a principle or policy record, its goal or criterion.
    - `triple`: the procedure that creates or revises principles. This corresponds to the harness's own learning rules (CLAUDE.md, memory-promotion rules).
  - (3) Level-jump alarm: N single-loop corrections in the same context with no double-loop review point to a possible governing-variable problem.

---

## 3. Robert Dilts: neurological ("logical") levels

- **Structure:** From the mid-1980s, adapted from Bateson for NLP:
  - **Environment** (where, when)
  - **Behavior** (what)
  - **Capabilities** (how)
  - **Beliefs and values** (why)
  - **Identity** (who)
  - **Spirit / purpose / "beyond identity"** (for whom, for what larger system)
- **Criteria:** These are question words, not formal criteria. Dilts holds that each higher level organizes and controls the one below, and that change at a higher level propagates downward more readily than the reverse.
- **Critiques:** Tosey and Mathison's work on NLP, Craft, and Woodsmall make these points:
  - The levels are neither *logical* in Russell's sense nor sharply delimited.
  - The model does not meet the criteria of a logical-type hierarchy. For example, Bateson places operant and associative learning at different levels, which the Dilts model collapses.
  - Placing "environment" at the bottom of a control hierarchy is anti-systemic.
  - Defenders call it a **heuristic checklist**, not a theory.
- **Failure mode:** It conflates **subject matter** with **logical level**. "Beliefs" can be stated at any abstraction: one belief about one meeting, or a general creed.
- **Harness implication:** Use Dilts as an **orthogonal "subject/scope" facet, not as the level axis**. Tag records with `about: environment | behavior | capability | belief | identity | purpose`, separately from the abstraction level. This avoids the classic NLP category error and still supports the useful query "which identity-level claims am I accumulating?"

---

## 4. Ackoff's DIKW hierarchy and its critiques

- **Structure:** Ackoff, "From data to wisdom," *Journal of Applied Systems Analysis* 16 (1989): 3–9, based on a 1988 ISGSR address. Ackoff writes: "Wisdom is located at the top of a hierarchy of types … Descending from wisdom there are understanding, knowledge, information, and, at the bottom, data. **Each of these includes the categories that fall below it.**"
  - **Data:** symbols that represent properties of objects and events; products of observation.
  - **Information:** data processed to be useful. It answers who, what, where, when and how many **[bk; Ackoff's question-word mapping is commonly attributed, but search did not confirm its exact wording]**.
  - **Knowledge:** know-how; makes possible the transformation of information into instructions.
  - **Understanding:** why.
  - **Wisdom:** evaluated understanding; adds value; judgement.
  - Ackoff himself did not draw the pyramid.
- **Critiques:**
  - **Frické (2009), "The knowledge pyramid: a critique of the DIKW hierarchy,"** *JIS* 35(2): 131–142. The hierarchy is "unsound and methodologically undesirable." It rests on **operationalism and inductivism**, the assumption that knowledge is mechanically inferred from accumulated data. That is a central logical error, because data is theory-laden and general knowledge does not follow from piles of data.
  - Frické's positive sketch: data is anything recordable in a semantically and pragmatically sound way; information and knowledge are both "weak knowledge"; wisdom is the possession and use of wide practical knowledge by an agent who recognizes its fallibility.
  - **Rowley (2007), "The wisdom hierarchy,"** *JIS* 33(2): 163–180, surveys textbook definitions and finds real disagreement on what separates the levels.
- **Criteria:** In Ackoff these are vague: added meaning, added purpose, added value. **This is the main lesson: DIKW names tiers without operational criteria.**
- **Failure modes:**
  - The **pipeline fallacy**: believing that more data produces knowledge automatically.
  - Ignoring that every observation is already selected at some level of abstraction (Floridi, Korzybski).
  - Treating wisdom as the top of a stack instead of a property of an agent using knowledge.
- **Harness implication:** Do not implement DIKW as a promotion pipeline. Use its *vocabulary* only with explicit criteria (section 17). Every record, including "raw" ones, must declare **what was selected and by whom**: the capture method and the observables. This acknowledges Frické's theory-ladenness point. Promotion requires an explicit inferential step with a named warrant, not mere accumulation.

---

## 5. Marr's three levels of analysis (*Vision*, 1982)

- **Structure:** Any information-processing system must be understood at three levels:
  - (1) **Computational theory:** what is computed, and *why*. The goal, and the logic of the strategy.
  - (2) **Representation and algorithm:** how the input and output are represented, and the procedure that transforms one into the other.
  - (3) **Hardware implementation:** how the representation and algorithm are physically realized.
  - Marr's illustrative example of the computational level is a cash register: the theory of addition explains why it works, independent of the gears or chips **[bk]**. Search did not confirm this example.
- **Criteria:** A level is defined by its **question** (why/what, how, with-what), and it can be specified somewhat independently of the levels below. Many algorithms realize one computation; many substrates realize one algorithm. Marr calls the levels "loosely related."
- **Movement:** Not learning but **explanation**. You move down by choosing a realization and up by abstracting the function served. Commentators (McClamrock; the OECS "Levels of Analysis" entry) note that the middle level is the most contested and that the levels are often blurred in practice.
- **Failure modes:**
  - Explaining a goal-level fact with an implementation detail, or the reverse.
  - Assuming the hierarchy is strictly independent. Hardcastle (2015) argues that brain breakdowns cross levels.
- **Harness implication:** Marr gives a facet that is **orthogonal to abstraction level**: `aspect: goal | method | substrate`. Example: a decision record "use worktrees for parallel agents" can carry a goal (avoid file collisions), a method (git worktree per agent) and a substrate (this machine and its disk). Patterns and principles should state which aspect they generalize. *Goal-level principles survive substrate changes; substrate-level patterns expire when tools change.* That difference gives a principled TTL rule.

---

## 6. Herbert Simon: hierarchy and near-decomposability ("The Architecture of Complexity," *Proc. Am. Phil. Soc.* 106, 1962)

- **Structure:** Complex systems are typically **hierarchic**: composed of interrelated subsystems, each of which is hierarchic in turn. The **watchmaker parable**: Tempus assembled watches of about 1000 parts in one piece, while Hora built stable subassemblies of about 10. An interruption costs Hora only the current subassembly, and stable intermediate forms let complexity evolve far faster.
- **Criterion (near-decomposability):** *Within*-subsystem interactions are much stronger and faster than *between*-subsystem interactions. In the short run each subsystem behaves approximately independently. In the long run only the aggregate behavior of the other components matters. So a level is a band of **interaction frequency**, not just of conceptual generality **[bk, consistent with search summaries]**.
- **Movement:** Higher levels arise from **stable intermediate forms**. A new level is warranted when a cluster is stable enough to be treated as a unit.
- **Failure modes:**
  - Decomposing along the wrong seams, so that strongly interacting parts are split.
  - Building the whole at once (Tempus), which is fragile.
- **Harness implication:**
  - (1) **Promotion only from stable subassemblies.** A pattern should be built from a cluster of episodes that already hold together, not from scattered singletons.
  - (2) Detect clusters empirically: records that co-reference, co-occur or co-change heavily form a module, which becomes a candidate for a pattern or principle namespace.
  - (3) Keep aggregation interfaces. A higher-level record should depend on summaries of lower clusters, not on every raw event. That keeps the ontology robust to interruption and partial loss (Hora).

---

## 7. Korzybski's structural differential, Hayakawa's ladder of abstraction, and Bret Victor

### Korzybski (*Science and Sanity*, 1933)
- **Structure [bk]:** The **structural differential**, a physical teaching device:
  - The **event**: the process level, a parabola with endless holes, meaning infinite characteristics.
  - The **object**: what the nervous system abstracts. A disc with fewer holes, with strings showing characteristics left out.
  - The **label / descriptive level**, then **inferences**, and inferences about inferences, indefinitely.
  - Slogan: "**A map is not the territory** it represents, but if correct, it has a similar structure to the territory."
  - Goal: "**consciousness of abstracting**," the awareness that every level omits characteristics.
- **Criterion:** Each step up **omits characteristics** of the level below. Higher levels are statements about statements.
- **Failure mode:** **Identification**, or confusion of orders of abstraction: treating a label or an inference as if it were the event. Related failures are "elementalism" and the "is of identity" ("he *is* lazy").

### Hayakawa (*Language in Action*, 1939; *Language in Thought and Action*, later editions)
- **Structure:** **Bessie the cow**. The ladder runs: the process-level cow (atoms, events) → the object we perceive → the word "Bessie" → "cow" → "livestock" → "farm assets" → "assets" → "wealth." The top rung depends on the field of discourse: an economist ends at "wealth," a biologist at "organism."
- **Criterion:** Each rung omits more particulars and includes more instances.
- **Failure modes [bk]:**
  - **"Dead-level abstracting."** Persistently low: endless particulars that never generalize. Persistently high: abstractions with no route back to instances.
  - Good thinking and writing move up and down the ladder.

### Bret Victor, "Up and Down the Ladder of Abstraction" (interactive essay, October 2011)
- **Structure:** Unverifiable directly; worrydream.com was unreachable, so this rests on secondary summaries. A system is understood by **abstracting over a variable**:
  - Start at the concrete level: one car, one road, one run, watched in real time.
  - Add a control for time and *abstract over time*: the whole trajectory shown as a line.
  - Then abstract over a parameter of the algorithm: many trajectories at once.
  - Then abstract over the environment: many roads.
  - Each step up replaces a *specific value* with *a range over that value*. You move back down to a concrete instance to build intuition.
- **Criterion:** A rung is defined by **which variables are bound (fixed) and which are free (ranged over)**.
- **Harness implication (all three):**
  - (1) Every record should list its **bound vs. free variables**: "In session S, at time t, with tool T, X happened" (all bound) vs. "With tool T, X tends to happen" (session and time free). **The abstraction level can be computed from how many contextual dimensions are quantified over.** This is the most testable criterion in this survey.
  - (2) Ban the "is of identity" in higher records. Use "tends to," "in contexts C," and an explicit scope.
  - (3) **Up-and-down navigability:** every abstraction must link down to concrete exemplars, and every exemplar should be reachable from at least one abstraction. This addresses Hayakawa's dead-level failure. A record with no down-links is an orphan abstraction; a cluster with no up-link is unharvested data.

---

## 8. Piaget: empirical vs reflective abstraction

- **Structure:**
  - **Empirical abstraction:** reading properties off objects (weight, colour).
  - **Pseudo-empirical abstraction:** reading off objects properties that the subject's own actions introduced (order, number when counting pebbles).
  - **Reflecting abstraction** (*abstraction réfléchissante*): abstracting from the **coordination of actions or operations**. It has two moments: *réfléchissement*, projection onto a higher plane, and *réflexion*, reorganization on that plane **[bk; search did not confirm the French terms]**.
  - **Reflected abstraction** (*abstraction réfléchie*): the conscious, thematized result. The subject becomes conscious of the *result* of their acts before becoming conscious of their *mechanism*.
  - Sources: Piaget, *Studies in Reflecting Abstraction* (trans. Campbell, 2001); Dubinsky's APOS theory builds on it (action → process → object → schema).
- **Criterion:** The source of the abstraction: object properties, properties the subject put into objects, or the subject's own coordinations. Reflecting abstraction produces a **new plane** on which the earlier coordinations become objects. **Dubinsky's "encapsulation"** is the test: a process becomes an object that can itself be acted upon.
- **Failure mode:** Mistaking pseudo-empirical regularities, which are artefacts of one's own method, for facts about the world.
- **Harness implication:**
  - (1) Tag patterns with `source: world | own_procedure | coordination_of_own_procedures`. A pattern such as "tests fail on Mondays" might be **pseudo-empirical**, an artefact of the harness's own Monday batch jobs. Flag patterns whose evidence was all produced by the harness's own actions.
  - (2) **Encapsulation test for meta-level:** a record reaches the meta-level when it treats a *procedure* (how I make decisions, how I promote patterns) as an object with properties.
  - (3) Expect the result-before-mechanism lag. Record "this keeps working" (outcome) before "why it works" (mechanism) as separate, linked records.

---

## 9. Floridi: the Method of Levels of Abstraction

- **Structure:** Floridi, "The Method of Levels of Abstraction," *Minds and Machines* 18(3): 303–329 (2008). It builds on Floridi and Sanders, "The Method of Abstraction" (2004), and *The Philosophy of Information* (2011).
  - An **observable** is a typed variable with a set of possible values, plus a feature of the system it stands for.
  - A **level of abstraction (LoA)** is a finite, non-empty set of observables. A *moderated* LoA adds predicates (behaviours) constraining their values.
  - A **gradient of abstraction (GoA)** is a set of LoAs plus relations linking their observables. GoAs are *nested*, where finer LoAs refine coarser ones, or *disjoint*, where they offer independent views.
  - Floridi's thesis of **epistemological levelism**: every claim is made at some LoA, explicit or not. Debates go wrong when parties use different LoAs without noticing. A question is meaningful only relative to an LoA. Floridi stresses this is epistemological, not a claim about ontological levels. Critique: van Leeuwen (2014), *Minds and Machines* 24(1): 5–17.
- **Criterion:** Formal and testable. One LoA is **finer** than another if there is a mapping (a relation) from its observables onto the coarser ones, meaning the coarse observables are definable from the fine ones. LoAs are compared through the **relations between observables**, not through vague "more abstract" talk.
- **Movement:** Choose an LoA suited to the purpose. Move along a GoA by refinement or coarsening.
- **Failure modes:**
  - Comparing claims made at different LoAs as if they conflicted.
  - Leaving the LoA implicit.
  - Choosing an LoA whose observables cannot answer the question.
- **Harness implication:** The most directly implementable theory.
  - (1) Each record type declares its **observables schema**, a typed field list. That schema *is* its LoA.
  - (2) A higher-level record must declare a **mapping** from lower observables. Example: `pattern.support_count` is computed from `episode.outcome` fields.
  - (3) Before merging or contradicting two records, check that they share an LoA, or that one is a declared refinement of the other. Otherwise flag "**LoA mismatch**, not contradiction."
  - (4) Make the "purpose" of an LoA explicit. Floridi stresses that LoAs are chosen for purposes, so the ontology's levels should be justified by the queries they serve.

---

## 10. Hofstadter (and Sander): analogy as the core of cognition

- **Structure:** Hofstadter and Sander, *Surfaces and Essences: Analogy as the Fuel and Fire of Thinking* (2013), with earlier work in *Fluid Concepts and Creative Analogies* (Copycat, Metacat).
  - Every concept owes its existence to a long succession of unconscious analogies, and categorization *is* analogy-making.
  - Concepts grow by **extension**, being applied to new cases, and by **abstraction and intercategory sliding** (a chapter title).
  - Higher abstraction means seeing a shared *essence* behind different *surfaces*.
- **Criterion:** Movement from **surface similarity** (shared features) to **structural similarity** (shared relational roles, the "essence"). Gentner's structure-mapping theory **[bk]** formalizes this: abstraction keeps relations and drops object attributes.
- **Movement:** Repeated cross-domain analogy. Metacat added self-watching, a trace of its own analogy-making, which is an explicit meta-level **[bk]**.
- **Failure modes:**
  - **Surface-level matching**: the right word, wrong essence.
  - **Over-sliding**: mapping that loses the essential relation.
  - Being stuck in one frame.
- **Harness implication:**
  - (1) A *pattern* must be stated **relationally**: roles and relations ("when the requester (role) lacks context (relation) on an irreversible action, ask first"), not keywords. Test: can the pattern be instantiated in two domains with no surface vocabulary in common? If so, it is a true pattern. If it holds in only one domain, it is a domain-local regularity.
  - (2) Store analogies as first-class edges: `analogous_to(A, B, mapping={role→role})`. These edges are the raw material of meta-patterns, which are patterns of which patterns are analogous.
  - (3) Keep a Metacat-style trace: log *which* past records were retrieved by analogy for each decision. That is data for learning about one's own learning.

---

## 11. Polanyi: tacit knowledge

- **Structure:** Polanyi, *Personal Knowledge* (1958); *The Tacit Dimension* (1966). "**We can know more than we can tell.**" Search confirmed the quote. Search did not retrieve the passages below on the from-to structure; the summary comes from **[bk]**.
  - Tacit knowing has a **from-to** structure. We attend *from* **subsidiary** particulars, the proximal term (the feel of the probe in the hand, facial features), *to* a **focal** whole, the distal term (the cavity explored, the recognized face).
  - Focusing directly on the subsidiaries destroys the performance; focusing on your fingers makes you stumble on the piano.
  - Its aspects are functional, phenomenal, semantic and ontological.
- **Criterion:** The distinction is not between levels of generality. It is about **role in attention**: whether something is used *as* a clue (subsidiary) or attended *to* (focal). Higher integrations rest on lower ones without being reducible to them; the "dual control" of comprehensive entities **[bk]**.
- **Failure modes:**
  - Assuming everything known can be made explicit.
  - Destroying a skill by over-articulating it.
  - Treating "explicitness" as the same thing as "abstraction."
- **Harness implication:**
  - (1) Add a `form: tacit | articulated` facet. Some of the most valuable "principles" exist only as *consistent behaviour across decisions*, an in-use pattern with no written rule. The harness can detect them statistically, as decision regularities, and store them as `tacit_candidate` records until the user confirms or articulates them.
  - (2) Do not assume a written principle captures the skill. Keep exemplars, the subsidiaries, linked to principles, the focal statements.

---

## 12. Nonaka: SECI and ba

- **Structure:** Nonaka (1994); Nonaka and Takeuchi, *The Knowledge-Creating Company* (1995). A spiral of four conversions:
  - **Socialization**: tacit to tacit, through shared experience.
  - **Externalization**: tacit to explicit, through metaphor, analogy and models.
  - **Combination**: explicit to explicit, through systematizing and combining documents.
  - **Internalization**: explicit to tacit, by learning by doing.
  - Each spiral moves knowledge from individual to group to organization. **Ba** is the shared space (physical, virtual or mental) in which conversion happens.
- **Criticisms:** These include over-reading Polanyi, since for him tacit and explicit are not two separable stocks but tacit is the ground of all knowing, and cultural specificity to Japanese firms (*Why Nonaka highlights tacit knowledge*, JKM).
- **Criterion:** The tacit/explicit status of source and target. This is *not* an abstraction level.
- **Movement:** The four conversions. Externalization uses **metaphor and analogy**, which links to Hofstadter.
- **Harness implication:** Map SECI onto record **operations**, not levels:
  - Socialization: the harness observes the user doing something, producing L0 traces.
  - Externalization: the harness proposes an articulated pattern or principle from behaviour.
  - Combination: merging or deduplicating explicit records and building indexes.
  - Internalization: a principle is turned into a default behaviour, hook or skill, so it no longer needs to be read each time.
  
  Log each operation as an event with `op: S|E|C|I`. That supports queries such as "which principles were externalized but never internalized (no hook or skill)?"

---

## 13. Kolb: experiential learning cycle (*Experiential Learning*, 1984)

- **Structure [bk; search did not cover Kolb]:** Four stages around two dialectics:
  - **Concrete Experience (CE)** to **Reflective Observation (RO)**, then **Abstract Conceptualization (AC)** to **Active Experimentation (AE)**, and back to CE.
  - The dialectics are grasping (CE vs AC) and transforming (RO vs AE). Rooted in Lewin, Dewey and Piaget.
  - Critiques: the cycle is too neat and sequential; the Learning Style Inventory has weak psychometrics and validity; it neglects social context and reflection *in* action (Schön).
- **Criterion:** The stage is defined by the **mode of the record**: having (CE), noticing (RO), generalizing (AC), testing (AE).
- **Movement:** A cycle, not a ladder. Abstraction (AC) is tested by deliberate action (AE).
- **Failure modes:**
  - Cycling without closing the loop: reflection that never produces a testable conceptualization.
  - Conceptualization that is never tested.
- **Harness implication:** This is the strongest argument for treating **decisions as experiments**. Every decision record that relies on a pattern or principle should record the **prediction** (`expected_outcome`), and a later observation closes it (`actual_outcome`). The harness can then compute each pattern's predictive track record. Patterns with no AE (no decision ever cited them) are untested hypotheses.

---

## 14. Boyd: "Destruction and Creation" (1976) and the OODA loop

- **Structure:** Boyd, "Destruction and Creation," a seven-page essay dated 3 September 1976 (PDF at coljohnboyd.com, unreachable from here; summaries via search). It is the epistemological basis of OODA.
  - We form mental concepts to shape and cope with the environment.
  - **Destructive deduction**: analyse and unstructure existing concepts into parts.
  - **Creative induction**: synthesize the parts into a new concept by finding common threads across domains. Boyd's example: skis, a boat's outboard motor, a tank's treads and handlebars recombined into a snowmobile **[bk]**.
  - Gödel (a system cannot be fully validated from inside), Heisenberg (observation limits) and the Second Law (a closed system's entropy rises) together argue that **any concept tested only against itself will degrade**. Mismatches accumulate as disorder and force rebuilding.
  - OODA: Observe, Orient, Decide, Act. **Orient** is central. It is shaped by cultural tradition, genetic heritage, previous experience, new information, and analysis/synthesis. Boyd later said the simple four-box loop misrepresents the model; implicit guidance and control links run from Orient straight to Act.
- **Criterion:** Not levels per se, but a **cycle of de-abstraction and re-abstraction** triggered by **mismatch**: anomalies accumulating against a concept.
- **Failure modes:**
  - A **closed system**: concepts validated only internally, so the harness checks its principles only against its own records.
  - Orientation lock-in.
  - Slow loops.
- **Harness implication:**
  - (1) Keep an **anomaly counter per pattern or principle**: counterexamples and failed predictions. When it crosses a threshold, schedule a "destruction" review that decomposes the principle into constituent claims, and a "creation" step that recombines claims, possibly across domains.
  - (2) Require **external validation** inputs, such as user confirmation or real outcomes, not only self-consistency. This is Boyd's open-system lesson, and it echoes the Gödel framing.
  - (3) Store `orientation` explicitly: the active set of principles and patterns loaded when a decision was made. Then each decision can be traced to the orientation that shaped it.

---

## 15. Wittgenstein's family resemblance, and Rosch's prototypes and basic level

- **Structure:**
  - **Wittgenstein** (*Philosophical Investigations*, §§65–77, 1953) **[bk]**: "games" share no common essence, only a network of overlapping similarities, a **family resemblance**. Concepts can have blurred edges and still be usable.
  - **Rosch**, "Principles of Categorization" (1978), confirmed via search:
    - (i) **Vertical dimension:** superordinate (furniture), **basic** (chair), subordinate (kitchen chair). The basic level is "the most inclusive (abstract) level at which the categories can mirror the structure of attributes perceived in the world." It maximizes **cue validity**: superordinates share too few attributes, and subordinates overlap too much with their contrast categories. Basic-level names are learned first, perceived first and used most.
    - (ii) **Horizontal dimension:** categories are organized around **prototypes**. Membership is graded by similarity to the prototype, not by necessary and sufficient features.
  - Critique: "basic" risks circularity if defined as maximal cue validity.
- **Criterion:** An *information-theoretic* criterion for the best level: maximize within-category similarity and between-category distinctiveness. This is cue validity and category utility.
- **Failure modes:**
  - Tagging at a level that is too general ("work stuff") or too specific (a unique per-incident tag).
  - Forcing crisp definitions on graded categories.
- **Harness implication:**
  - (1) **Tag taxonomy at the basic level.** Choose tag granularity by **category utility**: a tag is good if knowing it predicts a record's other fields well and separates it from sibling tags. Compute this from the corpus and periodically split or merge tags.
  - (2) Represent categories by **prototype exemplars plus a similarity threshold**, not only by rules. Each pattern stores 1–3 canonical exemplars.
  - (3) Accept graded membership: `membership: 0..1`.

---

## 16. Cross-cutting synthesis: what the theories agree on

| Theory | What defines a level | Movement up | Signature failure |
|---|---|---|---|
| Russell | type of what is quantified over | forming classes of classes | self-membership paradox |
| Bateson | what is being *changed* (response, choice, option set, set system) | contradiction or double bind at lower level | confusing message and meta-message |
| Argyris and Schön | action vs governing variable vs process of choosing variables | repeated single-loop failure; espoused/in-use gap | defensive routines |
| Dilts | subject matter (where/what/how/why/who) | heuristic | conflating subject with logical type |
| Ackoff / DIKW | added meaning/purpose (vague) | processing | pipeline/inductivist fallacy (Frické) |
| Marr | *question* asked (why / how / with what) | functional abstraction | cross-level explanation errors |
| Simon | interaction-frequency band | stable subassemblies | wrong decomposition seams |
| Korzybski / Hayakawa / Victor | characteristics omitted; variables bound vs free | quantifying over a variable | identification; dead-level abstracting |
| Piaget | source: object vs own action vs coordination | reflecting abstraction / encapsulation | pseudo-empirical artefacts read as facts |
| Floridi | set of typed observables + inter-level mapping | refinement/coarsening along a GoA | implicit or mismatched LoAs |
| Hofstadter | surface vs relational essence | analogy, intercategory sliding | surface matching |
| Polanyi | role in attention (subsidiary vs focal) | integration | over-articulation; "all is explicit" |
| Nonaka | tacit/explicit status | S-E-C-I conversions | knowledge stays in documents, not practice |
| Kolb | mode: experience/reflection/concept/test | cycle | untested concepts |
| Boyd | concept vs anomalies | destruction then creation | closed-system entropy |
| Rosch | cue validity / basic level | n/a (taxonomic) | wrong granularity |

**Four independent axes that the literature keeps separating, and that the harness must not collapse into one "level" field:**
1. **Abstraction / logical type**: what the record is *about* and how much it quantifies over (Russell, Bateson, Korzybski, Victor, Floridi). **This is the level axis.**
2. **Subject / scope**: environment, behaviour, capability, belief, identity, purpose (Dilts), and Marr's aspect (goal, method, substrate).
3. **Form**: tacit vs articulated (Polanyi, Nonaka).
4. **Epistemic status**: confidence, support, anomalies, tested or untested (Kolb, Boyd, Frické).

---

## 17. Proposed level model for the harness (with testable criteria)

### 17.1 The levels

**L0 Trace (raw observation).** Bateson L0 / Korzybski "object" level / Kolb CE.
- *What it is:* a verbatim capture of something that happened: a message, tool output, file diff, timestamped event.
- *Required fields:* `source`, `captured_at`, `capture_method` (observables selected: Floridi/Frické), `content` (verbatim or a hash pointer).
- **Tests:**
  - T0.1: content is reproducible from the source by replay or lookup.
  - T0.2: it contains **no inference tokens**: no causal connectives (because, so, therefore), no generalizing quantifiers (always, usually, tends to), no normative modals (should, must).
  - T0.3: all context variables are **bound** (one session, one time, one actor).

**L1 Episode / Fact (interpreted observation).** Korzybski "label/description" / Kolb RO.
- *What it is:* an interpretation of one or more L0 traces from **one episode** (one bounded context): "The deploy failed because env var X was missing."
- *Required:* `evidence: [L0 ids] (≥1)`, `interpretation`, `episode_id`, `confidence`.
- **Tests:**
  - T1.1: every L0 it cites shares a single `episode_id` (one context).
  - T1.2: it may contain causal or classificatory claims, but **no quantification across episodes**.
  - T1.3: no normative claim.

**L2 Decision.** Bateson LI / single-loop / Kolb AE.
- *What it is:* a choice **among alternatives within a given option set**, in one episode.
- *Required:* `context (L1 ids)`, `alternatives: [≥2]`, `chosen`, `rationale`, `governing_refs: [L3/L4 ids or none]`, `expected_outcome`, later `actual_outcome (L1 id)`.
- **Tests:**
  - T2.1: names ≥2 alternatives, explicit or recorded as implicit.
  - T2.2: scoped to one episode.
  - T2.3: is **evaluable**, with a stated expected outcome that a later L1 can confirm or refute.
  - T2.4: does *not* modify the option set. If it adds a new option *class* for future use, it is an L4 change too.

**L3 Pattern (empirical generalization).** Hayakawa's higher rungs / Victor "abstract over a variable" / Kolb AC / Rosch prototypes.
- *What it is:* a descriptive regularity **across episodes**: "When the user asks for research, they prefer a written file plus a short summary."
- *Required:* `statement` in relational form, `free_variables` (the contexts quantified over), `support: [L1/L2 ids]`, `counterexamples: [ids]`, `exemplars: [1–3 ids]`, `source: world | own_procedure`, `aspect: goal | method | substrate`.
- **Tests:**
  - T3.1: support spans **≥3 episodes across ≥2 distinct contexts or dates** (thresholds tunable).
  - T3.2: at least one context variable is **free** (quantified).
  - T3.3: it is **descriptive**: "tends to" or "when … then …", with no "should".
  - T3.4: it is **falsifiable**, naming an observation that would count as a counterexample.
  - T3.5 (Piaget check): if all support was produced by harness-initiated actions, mark `pseudo_empirical_risk`.
  - T3.6 (Hofstadter check, optional for "strong" patterns): it can be instantiated in ≥2 domains without shared surface keywords.

**L4 Principle / Policy (governing variable).** Argyris and Schön governing variable / Bateson LII (it changes the option set) / Marr computational-level "why".
- *What it is:* a **normative** rule that determines which alternatives are considered or how they are ranked in a class of contexts: "Never take irreversible actions without explicit confirmation."
- *Required:* `rule` (normative), `scope`, `exceptions`, `justification: [L3 ids and/or value statements]`, `espoused | in_use | both`, `adopted_at`, `revision_history`.
- **Tests:**
  - T4.1: contains a **normative modal** (should, must, prefer, never).
  - T4.2: it **constrains or generates option sets** for L2 decisions. The test is whether removing it would change which alternatives are listed or how they are ranked in future decisions.
  - T4.3: justified by ≥1 L3 pattern **or** an explicit value or user directive. A principle justified only by a single L1 is a **level-jump violation** (section 17.3).
  - T4.4: `in_use` status is computable from L2 `governing_refs` and compliance rate.

**L5 Meta-pattern / Learning-about-learning.** Bateson LII to LIII / deutero- and triple-loop / Piaget reflected abstraction / Boyd destruction and creation.
- *What it is:* a record **whose subject is other records or the harness's own record-forming process**. Examples:
  - "Patterns derived from fewer than 5 episodes were overturned 60% of the time."
  - "I keep externalizing principles that never get internalized as hooks."
  - "Corrections cluster in the `git` context; my option set there is wrong."
  - "Raise the promotion threshold for substrate-aspect patterns."
- *Required:* `subject_records: [ids] or subject_process: <procedure name>`, `statement`, `level_of_subjects` (max level of records referenced), `effect` (proposed change to promotion rules, thresholds, schemas or tag taxonomy).
- **Tests:**
  - T5.1 (**type test**): the predicate's arguments are *records, record sets, or harness procedures*, not world events.
  - T5.2: it is **not in its own support set** (Russell).
  - T5.3: its level is **max(level_of_subjects) + 1**, capped at 5. Meta-meta records stay at L5 with `order: 2, 3…`, to avoid an unbounded tower.
  - T5.4: if `effect` changes the procedure that creates or revises L4 records, set `loop: triple`. If it changes an L4 record, set `loop: double`.

### 17.2 Orthogonal facets (never encode these in the level)
- `about`: environment | behavior | capability | belief | identity | purpose (Dilts, demoted to a facet)
- `aspect`: goal | method | substrate (Marr). Substrate items get shorter review intervals.
- `form`: tacit_candidate | articulated | internalized (hook or skill exists) (Polanyi, Nonaka)
- `op` on change events: S | E | C | I (Nonaka)
- `loa`: the record type's observable schema id (Floridi)
- `status`: hypothesis | supported | contested | retired, with `support_n`, `counter_n`, `prediction_hit_rate` (Kolb, Boyd)
- `tags`: chosen at the **basic level** by category utility (Rosch)

### 17.3 Automatic checks (level-jump and level-confusion detectors)
1. **Skipped-rung promotion:** an L3 or L4 record whose evidence links go directly to L0 traces, or to a single L1, gets the flag `premature_abstraction` (Frické/Hayakawa). Rule: evidence must come from level n−1 or n−2, with ≥k items.
2. **Quantifier/modal lint:** an NLP or regex pass over the record text.
   - Generalizing quantifiers in an L0 or L1 record → misfiled up.
   - Normative modals in an L3 record → it is really an L4, or is smuggling a value.
   - Neither in a record filed as L4 → it is really an L3.
3. **Type test for L5:** if an L5 record's arguments resolve to world entities, not record ids or procedure names, it is misfiled. Conversely, an L3 record that cites other L3 records as *its subject*, rather than as *evidence*, should be promoted to L5.
4. **Self-reference:** reject any record that is in its own support closure.
5. **LoA mismatch before contradiction:** when two records conflict, first check that their `loa` and `free_variables` match. Otherwise label the conflict `scope_difference`, not `contradiction` (Floridi).
6. **Under-ascension alarm:** ≥N single-loop (L2) corrections in the same `context_tag` within a window, with no L4 revision event, triggers an auto-generated L5 candidate ("possible governing-variable problem in C") (Argyris/Bateson).
7. **Espoused vs in-use gap:** an L4 record whose compliance rate in L2 `governing_refs` falls below a threshold triggers an L5 candidate (Argyris).
8. **Anomaly threshold:** `counter_n / support_n` above θ on an L3 or L4 record schedules a destruction-and-creation review (Boyd).
9. **Orphans:** an L3 or higher record with no exemplars (no downward path) is an orphan abstraction. A dense L1 cluster with no L3 parent is unharvested; propose a pattern when the cluster is stable (Simon/Hayakawa).
10. **Pseudo-empirical guard:** an L3 record whose support was all generated by harness-initiated runs is flagged (Piaget).

### 17.4 Storing learning about learning concretely
- Make **revision events first-class records**: `{target_id, before, after, loop: single|double|triple, trigger_ids, op}`. L5 meta-patterns are mostly computed *over this revision log*: rates of overturn, time to retirement, which contexts generate double-loop changes. This is Bateson's deutero-learning measured as a change in the rate or character of learning.
- Keep **orientation snapshots**: the set of active L4 and L3 records injected into context for each L2 decision (Boyd). This makes it possible to ask "which principles actually shaped decisions?"
- Keep **analogy edges** `analogous_to(A,B,mapping)` between patterns. Meta-patterns are often clusters of analogous patterns (Hofstadter).
- The harness's **own promotion rules** (thresholds k, θ, N) live as versioned L4-procedure records. Only L5 records with `loop: triple` may change them, and changes need user confirmation. That keeps the meta-level open to outside correction (Boyd: no closed system).

### 17.5 Minimal decision procedure for assigning a level (the "type walk")
1. Is the predicate's subject other records or the harness's own procedures? → **L5**.
2. Else, does it contain a normative modal and constrain future option sets? → **L4**.
3. Else, does it quantify over ≥1 free context variable, with support from ≥3 episodes? → **L3**. If it quantifies but support is thinner, file it as an **L3 hypothesis**.
4. Else, does it select among ≥2 alternatives with an expected outcome? → **L2**.
5. Else, does it interpret (cause or classify) within one episode? → **L1**.
6. Else, it is verbatim, fully bound and inference-free → **L0**.

Each step is a mechanically checkable property (record-id argument types, modal lexicon, free-variable count plus support count, alternatives field, episode-id cardinality, inference-token lint). The assignment can therefore be validated automatically and audited.

---

## 18. Sources (verified via web search; direct fetch was blocked)

- Bateson, "The Logical Categories of Learning and Communication" (text): http://www.biolinguagem.com/ling_cog_cult/bateson_1972_%20logicalcategories_learningcommunication.pdf ; http://www.vordenker.de/vgo/logical-categories-of-learning.pdf ; summary https://wiki.p2pfoundation.net/Four_Levels_of_Learning
- Polycontextural reading of Bateson (Kybernetes): https://www.emerald.com/insight/content/doi/10.1108/03684920710777513/full/html
- Tosey, "Bateson's levels of learning: a framework for transformative learning?" (Surrey): https://openresearch.surrey.ac.uk/view/pdfCoverPage?instCode=44SUR_INST&filePid=13140358990002346&download=true
- Lee et al., learning to learn / deutero-learning (UGA): https://www.psychology.uga.edu/sites/default/files/inline-files/Learning%20to%20learn%20Final%20MS%2029%20May%202019_0.pdf
- Tosey, Visser and Saunders (2012), triple-loop learning critical review: https://journals.sagepub.com/doi/10.1177/1350507611426239
- Argyris summary (infed / aral): https://zeno-organisatieontwikkeling.nl/zeno/wp-content/uploads/2020/09/Argyris-C.-Theories-of-action-double-loop-learning-and-organizational-learning-revised-20-9-2011.pdf ; https://aral.com.au/resources/argyris.html
- Dilts logical levels and critiques: https://www.researchgate.net/publication/39018433_Neuro-linguistic_Programming_and_Learning_Theory_a_Response ; https://www.toolshero.com/communication-methods/logical-levels/ ; https://www.neurosemantics.com/neuro-logical-levels-in-four-quadrants/
- Ackoff and DIKW (ISKO Encyclopedia): https://isko.org/cyclo/dikw ; Rowley (2007): https://journals.sagepub.com/doi/10.1177/0165551506070706
- Frické (2009): https://journals.sagepub.com/doi/10.1177/0165551508094050 ; PDF https://zhang.ist.psu.edu/teaching/504/readings/Fricke.pdf ; Frické (2019) KO: https://article.imrpress.com/journal/KO/46/1/10.5771/0943-7444-2019-1-33/24065af3a6756c583a31e63457aa4f91.pdf
- Marr: McClamrock, https://www.albany.edu/~ron/papers/marrlevl.html ; Shagrir, https://openscholar.huji.ac.il/sites/default/files/oronshagrir/files/marr_on_computational-level_theories.pdf ; OECS, https://oecs.mit.edu/pub/ztivn7hx/ ; Hardcastle (2015), https://onlinelibrary.wiley.com/doi/10.1111/tops.12130
- Simon (1962) full text: https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/ArchitectureOfComplexity.HSimon1962.pdf ; CMU archive: http://iiif.library.cmu.edu/file/Simon_box00064_fld04924_bdl0001_doc0001/Simon_box00064_fld04924_bdl0001_doc0001.pdf
- Hayakawa ladder: http://saintperle.blogspot.com/2007/07/ladder-of-abstraction-as-described-by.html ; https://bigthink.com/the-learning-curve/ladder-of-abstraction/ ; https://www.toolshero.com/communication-methods/ladder-of-abstraction/
- Bret Victor (unreachable; secondary): http://worrydream.com/LadderOfAbstraction/ ; https://nohn.bearblog.dev/victors-up-and-down-the-ladder-of-abstraction/ ; https://metafilter.com/108300/The-Ladder-of-Abstraction
- Piaget: Dubinsky, https://people.math.wisc.edu/~rwilson/Courses/Math903/ReflectiveAbstraction.pdf ; von Glasersfeld, https://eric.ed.gov/?id=ED306120 ; https://link.springer.com/chapter/10.1007/978-3-031-47386-9_6 ; https://www.researchgate.net/publication/234022483_Piaget_on_Abstraction
- Floridi (2008): https://link.springer.com/article/10.1007/s11023-008-9113-7 ; https://philpapers.org/rec/FLOTMO ; "Levels of Abstraction and the Turing Test": https://philarchive.org/archive/FLOLOA ; Floridi and Sanders, "The Method of Abstraction": https://www.researchgate.net/publication/235223115_The_Method_of_Abstraction
- Hofstadter and Sander: https://books.google.com/books/about/Surfaces_and_Essences.html?id=XkQT5eTnurYC ; prologue PDF https://s3.amazonaws.com/arena-attachments/685495/a3bcc7b458a560b8e32bf24cac03ccf9.pdf
- Polanyi and Nonaka: https://academic-publishing.org/index.php/ejkm/article/download/770/733/766 ; https://en.wikipedia.org/wiki/SECI_model_of_knowledge_dimensions ; https://pmc.ncbi.nlm.nih.gov/articles/PMC6914727/ ; https://www.emerald.com/jkm/article-abstract/7/4/6/268042/Why-Nonaka-highlights-tacit-knowledge-a-critical
- Boyd (1976) essay PDF: https://www.coljohnboyd.com/static/documents/1976-09-03__Boyd_John_R__Destruction_and_Creation.pdf ; https://www.ooda.wiki/wiki/Destruction_and_Creation ; https://en.wikipedia.org/wiki/OODA_loop
- Rosch (1978) full text: https://commonweb.unifr.ch/artsdean/pub/gestens/f/as/files/4610/9778_083247.pdf ; https://link.springer.com/article/10.1007/s11196-022-09928-z
- SEP entries that would be the authoritative cross-checks (**unreachable this session**): "Type Theory," "Russell's Paradox," "Knowledge How," "Levels of Abstraction" (no dedicated entry known; see "Philosophy of Computer Science" and "Information"), "Concepts," "Analogy and Analogical Reasoning," "Wittgenstein."
- Kolb: not covered by search results; content is [bk]. Primary source: Kolb, D. A. (1984), *Experiential Learning*, Prentice Hall.
