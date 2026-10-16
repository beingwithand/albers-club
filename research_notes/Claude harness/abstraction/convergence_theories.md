# How different ideas converge: theories and methods for a convergence detector (2026-10-16)

**Goal.** Design part of the personal harness that notices when ideas from separate areas of work converge into one
shared abstraction. The areas are translation work, data annotation, app development, design and job search. The
harness should tell a real convergence (deep shared structure) apart from a superficial one (shared words or
surface features). It should also stop the user from locking onto a convergence too early.

**Method and reachability.** Sources were gathered with WebSearch in extended mode. **WebFetch failed for every
host tried** (matt.colorado.edu, andymatuschak.org, en.wikipedia.org, themarginalian.org): the fetcher got
`ENOTFOUND`, and the egress proxy returned `403 connect_rejected` for en.wikipedia.org when tested with curl. No
primary PDF was opened in full. The claims below rest on search-engine extracts of primary and secondary pages, as
listed in §17. Treat the exact quotations as *reported wording* and check them against the primary text before
citing. Claims that only secondary sources support are flagged as such.

**How each section is laid out.** Every theory gets the same five headings:
- **Mechanism:** how convergence happens.
- **Deep vs surface signal:** what shows that two ideas share deep structure rather than surface features.
- **Representation:** how to store the convergence.
- **Failure modes:** how it goes wrong.
- **Implementation:** record types, link types, scoring and human review.

§15 merges these into one `Convergence` record and §16 into a detection pipeline. The pipeline is meant to sit in
the existing KB slot (`scripts/kb.py`, `knowledge/raw`, wiki) and LEARN slot (librarian weekly loop) described in
`../scout_architecture.md`.

---

## 1. Koestler: bisociation (*The Act of Creation*, 1964)

**Mechanism.** A creative act perceives one situation or idea "in two self-consistent but habitually incompatible
frames of reference". Koestler calls these frames *matrices*, written M1 and M2. Routine thought runs on a single
plane. In the creative act the situation "vibrates on two wavelengths" at once. One theory covers three domains:
- **Humour (Haha):** the two frames collide, and the result is a laugh.
- **Science (Aha):** the two frames are fused into a new, larger matrix.
- **Art (Ah):** the two frames are juxtaposed and both held in view.

Koestler also notes that a scientific bisociation needs a "ripe" cultural preparation: the pieces have to exist
before they can be joined.

**Deep vs surface signal.** The link is valuable to the degree that the two matrices are *normally unrelated*. The
two frames have separate rule sets (codes), yet one concrete item, the "link", is lawful in both. A pun links two
matrices only through sound, which makes it the textbook surface bisociation. A scientific bisociation links them
through rules.

**Representation.** Store three things: `matrix_A` (domain, its governing rules or code), `matrix_B`, and the
`link`, meaning the concrete item, event or problem that is valid under both codes. Add an `outcome_mode` field
with one of three values:
- `collision`: the result is a joke or an insight about where the frames break.
- `fusion`: a new abstraction.
- `juxtaposition`: a useful tension that is kept rather than resolved.

**Failure modes.**
- **Pun-level links.** The two ideas share a word and nothing else. For example, "label" in data annotation and
  "label" in UI design.
- **Ripeness misjudged.** The idea is right but the supporting pieces don't exist yet, so it can't be acted on.
- **A secondary-source tension.** Koestler sometimes demands that the matrices be orthogonal, yet elsewhere
  describes them as "previously believed incompatible", which implies they were already linked. A detector
  should not *require* zero prior relation.

**Implementation.**
- Compute `domain_distance` between the two source domains: the user's five areas plus subtopics, or embedding
  distance between their centroids. Use it as a **novelty multiplier, never as evidence**. Distance makes a
  convergence interesting. It does not make it true.
- Flag any candidate whose only shared tokens are lexical, with no shared relation, as `bisociation:pun` and
  auto-demote it.
- Human review asks one question: "Which rule from each domain does the link item obey?" If the user cannot name a
  rule on both sides, reject.

## 2. Fauconnier and Turner: conceptual blending (*The Way We Think*, 2002)

**Mechanism.** The basic network has four mental spaces:
- two **input spaces**;
- a **cross-space mapping** between their counterparts;
- a **generic space**, which holds the structure the inputs share;
- a **blended space**, which receives *selective* projection from both inputs.

**Emergent structure** arises in the blend through three operations:
- **Composition** creates relations that exist only once elements from both inputs are put together.
- **Completion** recruits background frames. In their "boat race" example, a ship sailing in 1993 and a ship
  sailing in 1853 on the same route are blended into a race.
- **Elaboration** runs the blend like a simulation.

*Optimality / governing principles* (from ch. 16, per secondary extracts) rank candidate blends:
- Topology
- Pattern Completion
- Integration
- Maximization and Intensification of Vital Relations
- Web (keep the links to the inputs)
- Unpacking (the blend should let you rebuild the whole network)
- Relevance

*Vital relations* are the relation types that recur in compressions, such as time, space, cause-effect, change,
identity, part-whole, analogy and disanalogy. A blend can compress one of these into another, for example
representing time as space.

**Deep vs surface signal.** The convergence is real if (a) the **generic space is non-trivial**, meaning it holds
relations and roles rather than just "both are work things", and (b) the blend has **emergent structure** that
neither input had: a new inference, prediction or tool. A blend with no emergent structure is a restatement.

**Representation.** This model gives the *storage format* for a convergence: `inputs[]`, `cross_space_mapping[]`
(counterpart pairs), `generic_space` (roles and relations, stated without domain words), `blend`
(`projected_from_A`, `projected_from_B`, `emergent[]`), and `vital_relations[]`. The **Unpacking** principle gives
a usable test: from the blend text alone, could someone reconstruct both inputs?

**Failure modes.** The theory has been criticized as too permissive and hard to falsify: almost anything can be
described as a blend. Without the optimality filters it **over-generates**. A second failure is selective
projection that quietly drops the input element that would break the blend.

**Implementation.**
- Make `generic_space` a **required, domain-neutral sentence**. Lint it: it must not contain any vocabulary
  specific to either input domain.
- Require at least one `emergent` item, typed as one of `inference`, `prediction`, `tool`, `question` or
  `reframe`. Without one, the record stays `candidate` forever.
- Score Unpacking automatically: give an LLM only the blend and generic space, and ask it to name both source
  domains and the main counterpart pairs. Compare its answer with the record.
- Human review: confirm every emergent item, and list anything projection dropped ("what did we leave out?").

## 3. Gentner: structure-mapping theory (1983) and its descendants

**Mechanism.** An analogy maps knowledge from a **base** to a **target** under two principles:
- (a) **Relations** between objects are mapped. Object **attributes** are not.
- (b) Which relations get mapped is decided by **systematicity**. Gentner's wording: "A predicate that belongs to a
  mappable system of mutually interconnecting relationships is more likely to be imported into the target than is
  an isolated predicate." In practice this means relations governed by *higher-order* relations such as CAUSE and
  IMPLIES. In her Rutherford example, solar system to atom, distance and attraction carry over. The Sun's being
  hotter than the planets does not, because it connects to nothing else in the system.

The mapping also needs **one-to-one correspondence** and **parallel connectivity**: if two relations are matched,
their arguments must be matched too.

Gentner's taxonomy of comparisons:
- **Literal similarity:** many shared attributes and many shared relations.
- **Analogy:** few shared attributes, many shared relations.
- **Mere appearance:** shared attributes only.
- **Abstraction:** the base is itself an abstract relational system.

**Retrieval vs soundness** (Gentner, Rattermann and Forbus 1993; MAC/FAC, Forbus, Gentner and Law 1995):
- *Surface* similarity dominates what memory **retrieves**.
- *Structural* similarity decides which matches are **inferentially sound**.
- Purely structural remindings are rare but real.

MAC/FAC therefore runs in two stages. MAC is a cheap, non-structural content-vector filter. FAC then runs the
Structure-Mapping Engine (SME) on the survivors.

**Schema induction** (Gick and Holyoak 1983): with no source analog, only about 10% of people solved Duncker's
radiation problem with the convergence solution. One analog barely helped. **Comparing two analogs** first
produced an abstract "convergence schema" and much better transfer. Gentner's later work calls this *analogical
encoding*. The induction account has been partly challenged by later studies.

**Deep vs surface signal.** This is the most usable theory for the distinction:
- **Deep:** many shared relations, especially relations *connected by higher-order relations* (causal chains,
  enablement, constraint). Corresponding arguments sit in parallel positions.
- **Surface:** shared attributes, shared vocabulary, shared entity types, with no relational system behind them.
- **Systematicity score:** the size and depth of the largest connected matched relational subgraph.

**Representation.** A pair of small relational graphs plus a mapping:
- `base.relations[]` as `REL(arg1,arg2)` with explicit higher-order nodes, e.g. `CAUSE(AMBIGUOUS(spec), DIVERGE(outputs))`.
- `target.relations[]` in the same form.
- `mapping[]`: `{base_entity → target_entity}`, one-to-one.
- `candidate_inferences[]`: base relations that would be carried over into the target. This is where the payoff is.

**Failure modes.**
- **False analogy by mere appearance.** Same words, no relations.
- **Cherry-picked relations.** Mapping only the relations that fit and ignoring disanalogies.
- **Retrieval bias.** Surface-similar items crowd out the structurally similar ones, so the detector never even
  looks at the best match. This is MAC/FAC's lesson, and it applies directly to embedding search.
- **Overextended candidate inferences.** Transferring an isolated predicate, like the Sun's temperature.

**Implementation.**
- **Two-stage detector, as in MAC/FAC.** Stage 1 is a cheap embedding search, deliberately **run on the abstracted
  relation text** (§16 step 2) rather than the raw notes, so surface vocabulary does not dominate. Stage 2 is an
  LLM structure-mapping pass that outputs the relational graphs and mapping as JSON.
- **Scores** (each 0–1):
  - `relational_overlap`: matched relations ÷ min(|R_A|,|R_B|).
  - `systematicity`: depth and size of the largest connected matched subgraph containing at least one
    higher-order relation.
  - `attribute_overlap`, kept as **negative evidence** when relational_overlap is low.
  - `consistency`: 1 if one-to-one and parallel connectivity hold, else penalized.
- **Must-list disanalogies.** The record needs at least one `disanalogy` entry, so it is never one-sided.
- **Comparison-first prompting.** When two or more notes from different domains score high, ask the LLM to *compare
  them and state the common schema* (Gick and Holyoak) rather than mapping one onto the other. Schemas induced from
  two or more instances are more transferable.
- **LLM caveat.** Webb, Holyoak and Lu (2023) reported strong zero-shot analogy performance in GPT-3/4. Lewis and
  Mitchell's counterfactual-task tests showed that performance degrading on unfamiliar variants. Webb et al.'s
  2024–25 reply argues it holds when models can run code. So treat an LLM mapping as a *proposal* and verify it
  with structural checks and a human.

## 4. Peirce: abduction

**Mechanism.** Peirce's schema (CP 5.189): *The surprising fact C is observed; but if A were true, C would be a
matter of course; hence there is reason to suspect that A is true.* Peirce held that abduction is the only logical
operation that introduces a new idea. His method runs abduction, then deduction (derive consequences), then
induction (test them). A known objection (Frankfurt) is that A must already be in mind before the schema can run.
On that reading abduction **filters and ranks** hypotheses more than it **generates** them.

**Deep vs surface signal.** A convergence is *abductively* strong when the shared abstraction makes something
**previously surprising** in one or more domains "a matter of course". Example: "why do my annotation disagreements
cluster in the same places my translation queries do?" If the abstraction explains no surprise, it is filing, not
insight.

**Representation.** Use a `surprise` field (an observation that was anomalous or unexplained in some domain) and an
`explains[]` link from the convergence to those surprises. Pair it with `predicts[]`, the deductive consequences
that would show up if the abstraction holds.

**Failure modes.**
- **Just-so explanations.** The explanation fits every outcome.
- **Premature acceptance.** "Reason to suspect" gets treated as proof.
- **Generation bias.** Only hypotheses the user or model already had are considered.

**Implementation.**
- Let the harness log **surprises** cheaply. Any note tagged `?!`, "weird", "unexpected", "why does", or Korean
  equivalents such as 이상하다, 왜 그런지 becomes an `Anomaly` record. Anomalies are the strongest triggers for
  convergence search.
- Score `explanatory_gain` = the number of distinct-domain anomalies the abstraction makes expected, minus a penalty
  if it would equally have explained the opposite outcome.
- Every accepted convergence needs at least one `predicts` item phrased as a check the user can actually run. This
  is the deduction-then-induction step.

## 5. Whewell's consilience of inductions, and E. O. Wilson's *Consilience* (1998)

**Mechanism.**
- **Colligation:** scattered facts are bound together by a new **conception** supplied by the mind. Whewell held
  that this is not mere guesswork, though guesses often come first.
- **Consilience of inductions:** an induction built from one class of facts unexpectedly also explains facts of a
  *different* class, so the inductions "jump together". Newton's gravitation unified falling bodies and planetary
  orbits. It is one of Whewell's three tests of a hypothesis, alongside predicting untried cases and coherence
  (simplifying over time).
- **Wilson's version:** Wilson borrowed the word for the unity of knowledge across the natural sciences, social
  sciences and humanities. Critics, including an NEJM reviewer, H. Allen Orr in *Boston Review*, and a 2020s
  academic analysis, attack its **reductionism**: squeezing all knowledge into a physics-rooted mould and
  understating historical and social complexity.

**Deep vs surface signal.** This is the strongest signal on the list. An abstraction formed from domain A's
evidence **independently accounts for domain B's evidence that was not used to form it**. The test is
asymmetric and checks for leakage: was B part of building the idea, or did B confirm it afterwards?

**Representation.**
- `formed_from[]`: the evidence used to build the abstraction.
- `consilient_with[]`: evidence from other domains explained afterwards, each with a timestamp later than formation.
- `coherence_history[]`: does the abstraction get *simpler* as domains are added (good), or does it gain clauses
  (bad, see Lakatos in §14)?

**Failure modes.**
- **Leakage.** The B evidence was quietly used to shape the abstraction, so the "independent" fit is circular.
- **Reductionist overreach (Wilson critique).** One domain's vocabulary is forced onto another. For example,
  treating job search as "just an optimization pipeline" and losing its social and identity side (see Weick, §7).

**Implementation.**
- **Hold out one domain.** When a candidate is formed from notes in domains A and B, the harness *freezes* the
  generic-space statement and then searches domains C, D and E for fits. Fits found after freezing count as
  `consilience` evidence. Fits used during formation do not.
- Score `consilience = Σ over held-out domains of fit_strength × independence`. Independence is 1 if the domain was
  never shown during formation.
- Add a `reduction_check` review prompt: "Does this abstraction explain B in B's own terms, or does it rename B's
  terms into A's?"

## 6. Divergent → convergent thinking: Guilford (1950) and the Design Council Double Diamond (2004–05)

**Mechanism.**
- **Guilford.** His Structure of Intellect model separates **divergent production** (many varied answers where none
  is dictated; measured as fluency, flexibility and originality) from **convergent production** (the single best
  answer the information determines). His 1950 APA address is often credited with starting modern creativity
  research. The full SOI model has weak empirical support, but the divergent/convergent split has survived.
- **Double Diamond.** The UK Design Council's model came from case studies at 11 firms; dates vary across secondary
  sources between 2003 and 2005. It runs two diverge–converge cycles:
  - **Discover → Define** in the problem space.
  - **Develop → Deliver** in the solution space.

  It enforces the sequence twice to **prevent premature closure**.

**Deep vs surface signal.** Neither theory sorts deep from surface. They supply the **timing discipline**:
- Converge only after a real diverge phase, i.e. enough varied candidates.
- Converge on the *problem framing* before the *solution*.

A convergence proposed with fewer than N alternatives considered is suspect.

**Representation.**
- `phase` on every candidate: `diverge-problem | converge-problem | diverge-solution | converge-solution`.
- `alternatives_considered[]`: rival abstractions that could also explain the same instances.

**Failure modes.**
- **Premature convergence.** The first plausible abstraction wins.
- **Endless divergence.** Nothing is ever committed.
- **Skipped first diamond.** The harness solves "how to reuse X" before confirming the shared *problem* is real.

**Implementation.**
- **Rival requirement.** Before review, the pipeline must generate at least two alternative generic spaces for the
  same instance set and score them side by side. This is the diverge step, and the user picks one (converge).
- **Two-diamond gate.** First promote to `Convergence(problem)`: "these share the same problem structure". Only
  then allow `Convergence(solution)`: "this one tool or pattern serves all of them".
- **Cadence.** Divergent harvesting runs daily, in the background and cheaply. The converge decision happens only
  in the weekly review, which matches the librarian loop.

## 7. Weick: sensemaking (*Sensemaking in Organizations*, 1995)

**Mechanism.** Seven properties:
1. Grounded in **identity** construction.
2. **Retrospective**: we make sense of what has already happened.
3. **Enactive**: we help create the environment we then interpret.
4. **Social**.
5. **Ongoing**.
6. Focused on and by **extracted cues**.
7. Driven by **plausibility rather than accuracy**.

Sense is made *after the fact*, from cues, as a story that is good enough to act on.

**Deep vs surface signal.** Weick warns more than he discriminates. Because sensemaking favours **plausible
stories**, a convergence can feel deep simply because it makes a satisfying narrative. It may also be *identity-
driven*: "I am a person whose translation skills transfer to UX writing". Strong signal is a convergence that
**changes what the user does next** (enactment). Weak signal is one that only makes a nicer story.

**Representation.**
- `cues[]`: the specific extracted observations.
- `identity_claim`, optional, flagged when the convergence asserts something about who the user is. This is
  common in job search.
- `action_implication`: what would be done differently.

**Failure modes.**
- **Plausibility trap.** Narrative coherence is mistaken for structural truth.
- **Retrospective fabrication.** The convergence is read into old notes after the fact.
- **Identity-protective convergence.** The user accepts the abstraction because it flatters their career story.

**Implementation.**
- Raise the review threshold for any record with `identity_claim` set. Require at least one instance that is *not*
  self-description, e.g. an artifact, an outcome or third-party feedback.
- `action_implication` is required for promotion past `candidate`.
- Keep timestamps on cues so retrospective re-reading is visible. The review shows "noted at the time" versus
  "noticed now".

## 8. Klein, Moon and Hoffman: the data/frame theory (2006)

**Mechanism.** Sensemaking is "fitting data into a frame and fitting a frame around the data". Frames are
explanatory structures that decide what counts as data. There are two cycles:
- **Elaboration cycle:** elaborate the frame, question it against anomalies, preserve it, much like Piaget's
  assimilation.
- **Reframing cycle:** compare alternative frames, seek or construct a new one.

The later list of moves is *elaborating, questioning, comparing, preserving, reframing, seeking*. The 2023
**plausibility-transition** paper by Klein, Jalaeian, Hoffman and Mueller adds that plausibility judgments drive
both elaborating and switching frames.

**Deep vs surface signal.** A frame is deep when it **survives questioning by anomalous data** without ad-hoc
patches, and when it **decides what counts as data** in a new domain. In other words, it tells you where to look.

**Representation.** A `Frame` record (the abstraction as an explanatory structure) has `fits[]`, `anomalies[]`
(data that does not fit), and a `preserved_by[]` log (explanations used to keep the frame despite anomalies). A
growing `preserved_by` list is a red flag; compare Lakatos's degenerating programme in §14.

**Failure modes.**
- **Fixation.** Anomalies are explained away again and again (knowledge shields).
- **Reframing too late.**
- **Reframing too early**, on one data point.

**Implementation.**
- Convergence records are **living frames**. New notes in any domain are checked against active convergences and
  routed to `fits` or `anomalies`.
- Auto-raise a `reframe?` review item when `anomalies ≥ k` or `preserved_by` grows faster than `fits`.
- Run the **comparing** move as a pipeline step: always show the user the strongest rival frame next to the
  favoured one (shared with the §6 rival requirement).

## 9. Pirolli and Card: the sensemaking loop for intelligence analysis (2005)

**Mechanism.** From cognitive task analysis of all-source intelligence analysts, the model has two nested loops:
- **Foraging loop:** external data sources → *search and filter* → **shoebox** (the relevant subset) →
  *read and extract* → **evidence file** (snippets).
- **Sensemaking loop:** evidence file → *schematize* → **schema** (re-represented or organized evidence) →
  *build case* → **hypotheses** (tentative conclusions with supporting arguments) → *tell story* →
  **presentation**.

It runs both **bottom-up** (data to theory) and **top-down** (re-evaluating theory, searching for support or
counter-evidence) at many granularities. The paper's leverage points include the cost of the processing structure,
limited attention span, **confirmation bias**, and difficulty generating and holding alternative hypotheses. The
paper points to **Analysis of Competing Hypotheses (ACH)** as one remedy.

**Deep vs surface signal.** The model is a workflow, not a similarity test. It says that convergence happens at the
**schema** stage, through re-representation, not at the evidence stage. So the detector should compare
*schematized* notes, not raw snippets. Top-down search for **disconfirming** evidence is what separates a hypothesis
from a story.

**Representation.** The model maps onto storage tiers one-to-one:

| Pirolli and Card stage | Harness record |
|---|---|
| External data sources | raw notes, chats, files in `knowledge/raw` per domain |
| Shoebox | `Note` tagged with a domain, after intake filtering |
| Evidence file | `Claim` / `Observation`: atomic snippets with a back-link to the source |
| Schema | `Abstraction`: domain-neutral relational restatement (§16 step 2) |
| Hypothesis | `Convergence(candidate)` with supporting and contrary links |
| Presentation | `Convergence(accepted)` written up as an evergreen wiki page or decision note |

**Failure modes.**
- **Confirmation bias.** Only supporting evidence is collected.
- **No alternatives.** Hypotheses are never set against rivals.
- **Foraging starvation.** Domains with fewer notes, such as job search in a quiet month, never contribute.

**Implementation.**
- A **top-down search step** for every candidate: an explicit query for counter-evidence in each involved domain,
  logged as `contradicts` links.
- An **ACH matrix** in review: rows are evidence, columns are the candidate and its rivals. Score each cell
  consistent, inconsistent or neutral. The candidate with the *fewest inconsistencies* wins, not the one with the
  most support.
- **Domain-balanced foraging.** Sample candidate pairs stratified by domain so sparse domains are not starved.

## 10. Luhmann: the Zettelkasten as a communication partner ("Kommunikation mit Zettelkästen", 1981)

**Mechanism. (secondary sources only: the essay text and the Kuehn translation were not opened)**
- Luhmann treated his slip box as a **communication partner** that can **surprise** its user. Communication, on his
  account, requires partners able to surprise each other.
- Notes have **fixed numbers**, and a new note is filed next to the note it follows (*Folgezettel*, branching IDs
  such as 21/3d7a).
- There is **no topical hierarchy**. A **register** (keyword index) gives a few entry points, and **cross-references**
  between distant notes create the network.
- Surprise comes from following links into regions the user did not have in mind when searching. Some commentators
  argue "interaction" fits better than "communication".

**Deep vs surface signal.** Two notes placed far apart, in different branches, that the user later links on
purpose are the Zettelkasten version of a cross-domain convergence. A link counts for more when it carries an
**explicit reason** ("this is the same problem as…") than when it is bare.

**Representation.** Stable IDs, `follows` links (sequence/branch), `refers` cross-links each with a written
`reason`, and a small register of entry points. Hub notes collect links to a topic's entry points.

**Failure modes.**
- **Link spam.** Many bare links, no reasons.
- **Collector's fallacy.** Notes are filed but never put into conversation with one another.
- **Over-curation.** A neat topical hierarchy rebuilds the silos that cross-domain surprise depends on.

**Implementation.**
- **Surprise channel.** Once a week the harness "talks back": it surfaces 3–5 pairs of distant notes, measured by
  graph distance and domain difference, whose abstractions score high (§16). It asks the user to write a one-line
  link reason or dismiss the pair. Reasoned links become evidence for convergences.
- **Bare-link penalty.** Links with no `reason` add nothing to convergence scores.
- Keep the five domains as *tags*, not folders, so no hierarchy blocks cross-links.

## 11. Matuschak: evergreen notes

**Mechanism.** Evergreen notes are written to **accumulate insight over time** across projects, not to capture
information. His principles include:
- **atomic**;
- **concept-oriented**: organize notes by concept, not by book, project or topic, *specifically so that cross-domain
  connections surface over time*;
- **densely linked**;
- **associative ontologies over hierarchical taxonomies**;
- **write for yourself by default**.

His own notes cite the Zettelkasten as a major influence.

**Deep vs surface signal.** A concept note whose backlinks come from **several different project contexts** is a
living convergence. The concept-oriented title, ideally a complete claim, *is* the generic space.

**Representation.** `Concept` notes with claim-style titles, e.g. "Specifications fail at edge cases, so consistency
needs adjudicated exemplars". Backlinks are typed by the domain they come from.

**Failure modes.**
- **Topic-titled notes** ("Annotation") that hold everything and converge nothing.
- **Notes stuck to their project**, so the abstraction never comes loose from its first domain.
- **Over-atomization.** The relational system that systematicity needs (§3) is split across notes and lost.

**Implementation.**
- Name accepted convergences as **claims**. Lint: a title must contain a verb and must not be a single noun phrase.
- `backlink_domain_entropy` = Shannon entropy over the domains of the backlinks. High entropy plus high
  systematicity marks a mature convergence.
- An accepted Convergence *becomes* an evergreen concept note in the wiki. New domain notes that fit it get
  backlinks automatically, routed through the §8 fits/anomalies check.

## 12. Christopher Alexander: pattern languages (*A Pattern Language*, 1977; *The Timeless Way of Building*, 1979)

**Mechanism.**
- **Size.** 253 patterns, from towns down to construction details. Ranges reported: towns 1–94, buildings about
  95–204, construction about 205–253; sources disagree on the boundary.
- **Pattern anatomy:** name; picture; **context** paragraph linking *up* to the larger patterns it helps complete;
  **problem** statement naming the conflicting **forces**; evidence; **solution**; then links *down* to the smaller
  patterns that complete it.
- **Network structure.** The authors write, "A pattern language has the structure of a network". It is not a tree;
  compare his earlier essay "A City Is Not a Tree".
- **Confidence marks.** Asterisks show confidence, and the authors call all 253 patterns "hypotheses" and
  "tentative".

**Deep vs surface signal.** Two things share a pattern when they share the same **forces in conflict** and the same
**resolution**, not the same look. The pattern is the reusable *problem–forces–solution* triple that works across
contexts. This is close to Hope et al.'s **purpose/mechanism** decomposition, which was built to find analogies at
scale (§13).

**Representation.** `Pattern { name, context(up-links), problem, forces[], solution, instances[], down-links,
confidence(0–2 stars) }`. Patterns at different scales are linked by `completes` (up) and `completed_by` (down).

**Failure modes.**
- **Cargo-cult patterns.** The solution is copied without the forces.
- **Patterns as a tree.** Rigid hierarchy loses cross-scale links.
- **False certainty.** The asterisks are dropped and patterns are treated as laws.

**Implementation.**
- **Forces-first matching.** For every candidate, extract each instance's `forces[]` (e.g. *consistency vs.
  speed*, *fidelity vs. fluency*, *coverage vs. depth*) and its `resolution`. Score `force_overlap` separately from
  relational overlap. Shared forces plus a shared resolution is the strongest pattern signal.
- **Scale tags.** Use `micro` (a sentence, a label, a UI control), `meso` (a document, a dataset, a screen, an
  application) and `macro` (a project, a career, a product). Link convergences across scales with `completes`. A
  micro convergence (e.g. "glossary entries ≈ design tokens") can complete a meso one ("a shared spec layer").
- Carry a 0/1/2-star `confidence` that only the human can raise to 2.

## 13. Methods that put structure-mapping into practice at scale

- **Purpose/mechanism mining** (Hope, Chan, Kittur and Shahaf, KDD 2017). They learned separate *purpose* and
  *mechanism* vectors from product descriptions using crowd annotation and RNNs. They found analogies by matching
  purpose and varying mechanism, or the reverse. Their reported example is a yogurt maker: mechanism ≈ "pump, steel,
  electric", purpose ≈ "food, produce, concentrate". The design lesson is to **factor each note into facets before
  embedding**, so similarity is measured per facet rather than over the whole text, where surface words dominate.
  Follow-ups: PNAS 2019, "Scaling up analogical innovation with crowds and AI"; arXiv 2102.09761, fine-grained
  functional aspects.
- **MAC/FAC** (§3) gives the cheap-filter then structural-match architecture.
- **ACH** (§9) handles rival comparison.

## 14. Kuhn and Lakatos: how theories consolidate

**Mechanism.**
- **Kuhn.** In *normal science* work happens inside a **paradigm**. Anomalies pile up, and a crisis leads to a
  revolution. The 1969 Postscript splits "paradigm" in two:
  - the **disciplinary matrix**: symbolic generalizations, models, values, exemplars;
  - **exemplars**: concrete solved problems. Training on exemplars is what gives the "faculty of seeing a current
    problem as like another".
- **Lakatos.** A **research programme** has a **hard core**, which by methodological decision is not refuted, and a
  **protective belt** of auxiliary hypotheses that absorbs anomalies. It is **progressive** if changes to the belt
  predict novel facts that are later confirmed (Neptune). It is **degenerating** if changes only accommodate known
  anomalies after the fact. Degenerating programmes can come back.

**Deep vs surface signal.** A convergence *consolidates* into a lasting abstraction when (a) **exemplars** from
several domains can be solved the same way, which is Kuhn's "seeing as like", and (b) every revision to its scope
or clauses **pays for itself in a new successful prediction**, which is Lakatos-progressive.

**Representation.**
- `hard_core`: the generic-space claim.
- `protective_belt[]`: scope conditions and clauses added over time, each with `added_because` (an anomaly) and
  `predicted_novel` (yes/no, and whether it was confirmed).
- `exemplars[]`: one worked, concrete case per domain.

**Failure modes.**
- **Degenerating abstraction.** Clauses pile up to rescue it.
- **Paradigm lock-in.** Every new note is forced into the dominant convergence.
- **Abandoning too early.** A good abstraction is dropped before it has had time to work.

**Implementation.**
- `progress_ratio` = confirmed novel predictions ÷ belt revisions. Below 0.5 over the last N revisions → mark
  `degenerating` and schedule a reframing review (§8).
- Each accepted convergence keeps **one exemplar per domain** it claims. A domain without a worked exemplar is not
  covered, whatever the similarity scores say.
- Give each convergence a **quarterly health check**: progressive, stagnant or degenerating, plus any rival
  convergence gaining instances.

---

## 15. Proposed `Convergence` record

The record merges §1–14. Field provenance appears in brackets. YAML front matter sits in a wiki page, so
`kb.py` can index it and humans can read it.

```yaml
id: conv-2026-10-016                 # stable, Luhmann-style; never reused
title: "Shared specs break at edge cases; consistency comes from adjudicated exemplars"  # claim-form [Matuschak]
status: candidate | under_review | accepted | degenerating | retired | rejected
phase: converge-problem | converge-solution          # [Double Diamond]
scale: micro | meso | macro                           # [Alexander]
confidence_stars: 0 | 1 | 2                           # 2 only by human [Alexander]

instances:                     # ≥2 distinct domains; each is an Abstraction of a Note
  - domain: translation
    note: kb://raw/translation/2026-09-12-client-glossary-dispute
    exemplar: true             # worked case in this domain [Kuhn]
    noted_at: 2026-09-12       # vs noticed_at, retrospection visible [Weick]
  - domain: annotation
    note: kb://raw/annotation/2026-10-03-guideline-v4-disagreements
  - domain: design
    note: kb://raw/design/2026-08-20-token-naming-drift

generic_space:                 # domain-neutral; linted against domain vocab [Fauconnier & Turner]
  statement: "Independent producers follow a shared spec; outputs diverge exactly where the spec is silent; divergence shrinks when disputed cases are adjudicated and added back as exemplars."
  roles: [producer, spec, edge_case, adjudicator, exemplar]
  relations:                   # explicit higher-order structure [Gentner]
    - CAUSE(SILENT(spec, edge_case), DIVERGE(outputs))
    - CAUSE(ADD(exemplar, spec), REDUCE(divergence))
  forces: ["consistency vs. speed", "spec completeness vs. spec readability"]   # [Alexander]

mappings:                      # one-to-one per instance pair [Gentner]
  - pair: [translation, annotation]
    map: {glossary: guideline, translator: annotator, reviewer_query: adjudication_ticket, TM_entry: gold_example}
    disanalogies: ["translation clients can overrule; annotation adjudication is internal"]   # required

blend:                         # [Fauconnier & Turner]
  emergent:                    # ≥1 required to leave candidate
    - type: tool
      text: "One 'edge-case ledger' format reused for glossary queries, guideline questions and design-token disputes."
    - type: prediction
      text: "App API contract bugs should also cluster at undocumented edge cases."
  unpacking_check: pass        # LLM reconstructs inputs from blend alone

explains:                      # anomalies made 'a matter of course' [Peirce]
  - anomaly: kb://anomaly/2026-10-01-why-same-annotators-disagree-on-same-items
predicts:                      # runnable checks [Peirce → deduction → induction]
  - check: "Tag last 30 app-dev bugs; ≥50% trace to unspecified edge cases"
    status: open | confirmed | failed
formed_from: [translation, annotation]                 # [Whewell] leakage guard
consilient_with:                                       # held-out domains fit AFTER freeze
  - domain: app_dev
    evidence: kb://raw/appdev/2026-10-10-null-handling-bug
    found_after_freeze: true

rivals:                        # ≥2 before review [Double Diamond, ACH]
  - id: conv-2026-10-016-r1
    statement: "Divergence is caused by fatigue/time pressure, not spec silence."
ach_matrix: kb://review/conv-2026-10-016/ach.csv       # [Pirolli & Card]

frame_tracking:                # [Klein]
  fits: []
  anomalies: []
  preserved_by: []
protective_belt:               # [Lakatos]
  - clause: "Applies only where ≥2 producers work in parallel"
    added_because: kb://anomaly/...
    predicted_novel: false

identity_claim: null           # set → stricter review [Weick]
action_implication: "Start a shared edge-case ledger template; use it in the next annotation batch and translation job."

scores: {see §16 step 6}
review_log:
  - date: 2026-10-16
    reviewer: user
    decision: promote | revise | reject | park
    note: "..."
```

**Supporting record types.**

| Type | Purpose | Theory |
|---|---|---|
| `Note` | raw item in one domain, unchanged | P&C shoebox |
| `Observation` | atomic snippet with source back-link | P&C evidence file |
| `Abstraction` | domain-neutral relational restatement of one Note: roles, relations, forces, purpose/mechanism facets | Gentner, Hope et al., Alexander |
| `Anomaly` | a surprise or unexplained observation | Peirce, Klein |
| `Convergence` | as above | all |
| `Pattern` | an accepted, solution-phase Convergence written as context/problem/forces/solution | Alexander |

**Link types.** Each link is typed, and every link carries a `reason` string; a bare link has no evidential weight
(Luhmann).

| Link | Meaning |
|---|---|
| `abstracts` | Note → Abstraction |
| `instance_of` | Abstraction → Convergence |
| `maps_to` | Abstraction ↔ Abstraction, with an entity map |
| `explains` | Convergence → Anomaly |
| `predicts` | Convergence → check |
| `consilient_with` | Convergence → held-out evidence |
| `contradicts` | evidence → Convergence |
| `rival_of` | Convergence ↔ Convergence |
| `completes` / `completed_by` | across scales |
| `supersedes` | replacement after reframing, with `valid_to` on the old record |
| `follows` | Folgezettel-style sequence |

## 16. Detection pipeline

The pipeline fits the harness's existing intake → KB → weekly librarian loop.

1. **Intake (foraging, daily, cheap).** Tag each new `Note` with a domain (translation / annotation / app_dev /
   design / job_search) and split it into `Observation`s. Detect surprise markers and open an `Anomaly` for each
   (§4). *Hook:* the existing intake skill and `kb.py`.
2. **Abstract (schematize).** For each Note, an LLM writes an `Abstraction` with these fields:
   - (a) a **domain-neutral** one-sentence restatement;
   - (b) roles, plus relations including at least one higher-order relation;
   - (c) `forces[]` and `resolution`;
   - (d) `purpose` and `mechanism` facets.

   A lint step rejects abstractions that still contain domain jargon from a per-domain stop-list, e.g. "TM",
   "IAA", "Figma", "PR", "ATS". This is the most important single step: it is how the harness gets past MAC/FAC's
   surface-retrieval bias.
3. **Retrieve (MAC).** Embed each facet of each Abstraction separately: neutral statement, relations, forces,
   purpose, mechanism. Retrieve cross-domain neighbours only, with pairs drawn stratified by domain (§9). Get
   anomalies first: every open Anomaly searches the other domains.
4. **Map (FAC).** For the top-k pairs, and for triples when available, an LLM runs a structure-mapping pass. It
   outputs `mapping`, `matched_relations`, `disanalogies` and `candidate_inferences` as JSON. A deterministic
   checker verifies one-to-one mapping and parallel connectivity (§3). Where three or more instances exist, use
   **comparison prompting** to induce the schema (Gick and Holyoak).
5. **Blend and rival generation (diverge).** Write the generic space and emergent items, and run the unpacking test
   (§2). Generate **two or more rival generic spaces** for the same instances (§6).
6. **Score.** Each component is 0–1:

   ```
   structural   = 0.35*systematicity + 0.25*relational_overlap + 0.20*force_overlap + 0.20*consistency
   surface_pen  = max(0, attribute_overlap - relational_overlap)          # mere-appearance penalty
   novelty      = domain_distance(instances)                                # Koestler; multiplier only
   explanatory  = min(1, 0.5*|explains| + 0.25*|confirmed predicts|)       # Peirce
   consilience  = Σ fit_strength over held-out domains, capped at 1        # Whewell; post-freeze only
   emergence    = 1 if ≥1 emergent item verified else 0                    # F&T
   rival_margin = score(candidate) - score(best rival)                     # Klein/ACH

   evidence = 0.40*structural + 0.20*explanatory + 0.25*consilience + 0.15*emergence - 0.30*surface_pen
   priority = evidence * (0.6 + 0.4*novelty) * (rival_margin > 0.1 ? 1 : 0.5)
   ```

   Gates, applied before human review:
   - instances span at least 2 domains;
   - at least 1 higher-order relation is matched;
   - at least 1 disanalogy is listed;
   - at least 2 rivals exist;
   - `generic_space` passes the jargon lint.

   The weights are a starting point. Calibrate them with the eval gate against a small hand-labelled set of
   true and false convergences taken from the user's own notes.
7. **Counter-evidence search (top-down).** For each surviving candidate, explicitly query each involved domain
   for contradicting notes. Fill the ACH matrix (§9).
8. **Freeze and hold out (consilience).** Freeze the `generic_space`, then search the domains not used in
   formation. Record fits found after the freeze as `consilient_with` (§5).
9. **Human review (converge, weekly).** Show at most 3–5 candidates, sorted by `priority`. For each, the user
   answers the five-question card:
   1. Name the rule each domain's instance obeys. (Koestler; checks for puns)
   2. Is the generic space true *without* domain words? Edit it. (Fauconnier and Turner)
   3. Strongest disanalogy: does it break the transfer? (Gentner)
   4. Better than the rival? Look at the ACH matrix. (Klein, Pirolli and Card)
   5. What will you do differently, and which prediction will you check? (Weick, Peirce)

   The user then chooses `promote`, `revise`, `reject` or `park`. Records with `identity_claim` need non-self
   evidence before they can be promoted (§7). Only a human can set `confidence_stars` to 2.
10. **Maintain (living frame).** Route new notes through the accepted convergences as `fits` or `anomalies` (§8).
    Track `protective_belt` and `progress_ratio` (§14). Run a quarterly health check. When a convergence is
    replaced, set `supersedes` and `valid_to` and never delete it. Accepted solution-phase convergences are
    published as claim-titled evergreen concept notes or `Pattern`s, with up and down scale links (§11–12).

**Defences against the main failure modes, collected.**

| Failure | Defence in the pipeline |
|---|---|
| False analogy by shared vocabulary | step 2 jargon lint, facet embeddings, `surface_pen`, Koestler card question |
| Cherry-picked mapping | required `disanalogies`, deterministic consistency check |
| Premature convergence | daily diverge / weekly converge cadence, at least 2 rivals, two-diamond gate (problem before solution) |
| Plausible-story trap | `action_implication` and runnable `predicts` required, identity-claim gate |
| Circular confirmation | freeze plus held-out-domain consilience only |
| Fixation / degenerating abstractions | anomalies tracking, `progress_ratio`, reframing review |
| Starved domains | domain-stratified retrieval |
| Over-generation (blending permissiveness) | gates in step 6, max 5 candidates per week |
| Over-trusting the LLM mapper | LLM output is a proposal only; structural checker plus human card |

**Worked seeds for this user.** These are hypotheses to test, not conclusions.
- **Spec–edge-case–exemplar.** Translation glossaries and style guides, annotation guidelines with adjudication,
  design tokens and component specs, and API contracts or type schemas all share one structure (the record in §15).
  Job search may be a held-out domain: does a job description act as a "spec" whose silent edge cases are where
  tailored applications diverge?
- **Mapping between two vocabularies.** Translation (source → target), annotation (raw → label schema), design
  handoff (design → code), and résumé tailoring (experience → JD terms) may all be *structure-mapping tasks
  themselves*. Under that convergence, Gentner's systematicity becomes a *quality criterion inside each domain*:
  for example, a tailored résumé should carry over relational achievements (CAUSE(action, outcome)), not just
  keywords (attributes).

## 17. Sources

Everything was reached through WebSearch extended-mode extracts. **WebFetch could not reach any host tried**
(DNS `ENOTFOUND`), and the egress proxy returned `403` for en.wikipedia.org, so no page was read in full.

- **Gentner 1983:**
  - [PDF, colorado.edu](http://matt.colorado.edu/teaching/highcog/readings/g83.pdf): fetch failed.
  - [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1207/s15516709cog0702_3)
  - [Wikipedia: Structure-mapping theory](https://en.wikipedia.org/wiki/Structure-mapping_theory)
  - [Gentner and Markman, Structure mapping in analogy and similarity](https://home.csulb.edu/~cwallis/382/readings/482/GenterMarkman.pdf)
  - [Falkenhainer, Forbus and Gentner, SME](https://groups.psych.northwestern.edu/gentner/newpdfpapers/FalkenhainerGentner86.pdf)
  - [Gentner and Forbus 2011, Computational models of analogy](https://groups.psych.northwestern.edu/gentner/papers/gentner&Forbus_2011.pdf)
- **Retrieval vs soundness:**
  - [Gentner, Rattermann and Forbus 1993](https://www.semanticscholar.org/paper/The-Roles-of-Similarity-in-Transfer:-Separating-Gentner-Rattermann/8e8de7b9320caffa71cff3db62d68c62bbee49b8)
  - [MAC/FAC (Forbus, Gentner and Law)](https://onlinelibrary.wiley.com/doi/abs/10.1207/s15516709cog1902_1)
  - [QRG PDF](https://www.qrg.northwestern.edu/papers/Files/QRG_Dist_Files/QRG_1994/Forbus_1994_MAC_FAC_Model_Similarity-Based_Retrieval_CogSci.pdf)
- **Gick and Holyoak 1983:**
  - [PDF (gwern)](https://gwern.net/doc/psychology/1983-gick.pdf)
  - [DeepBlue](https://deepblue.lib.umich.edu/items/196ea13e-fb69-4a74-a6f9-864c81aed465)
- **LLM analogy debate:**
  - [Webb, Holyoak and Lu 2023](https://sotaverified.org/papers/emergent-analogical-reasoning-in-large)
  - [Lewis and Mitchell, counterfactual tasks](https://escholarship.org/uc/item/58d9s666)
  - [Webb et al. reply](https://arxiv.org/abs/2404.13070v1)
  - [Hodel and West response](https://arxiv.org/pdf/2308.16118)
- **Fauconnier and Turner:**
  - [Conceptual Blending, Form and Meaning (2003)](https://tecfa.unige.ch/tecfa/maltt/cofor-1/textes/Fauconnier-Turner03.pdf)
  - [Fauconnier 2005, Compression and emergent structure](https://pages.ucsd.edu/~scoulson/spaces/fauconnier05.pdf)
  - [Turner, Conceptual Integration](https://markturner.org/cinLEA.pdf)
  - [Wikipedia](https://en.wikipedia.org/wiki/Conceptual_blending): fetch failed; search extract only.
  - [A Critical View on CBT](https://escholarship.org/content/qt95p302sj/qt95p302sj_noSplash_915227ed37c13210752713ed4e659169.pdf)
  - The optimality-principle list comes from an unofficial Scribd text of *The Way We Think*, ch. 16. Verify it
    against the book.
- **Koestler:**
  - [Wikipedia: The Act of Creation](https://en.wikipedia.org/wiki/The_Act_of_Creation)
  - [The Marginalian](https://www.themarginalian.org/2013/05/20/arthur-koestler-creativity-bisociation/): fetch failed.
  - [JGMF reading notes](http://jgmf.blogspot.com/2016/03/reading-notes-arthur-koestler-act-of.html): the orthogonality tension, secondary.
  - [arXiv 2606.13977](https://arxiv.org/pdf/2606.13977)
- **Peirce:**
  - [SEP: Peirce on Abduction](https://plato.stanford.edu/entries/abduction/peirce.html)
  - [Psillos, Peirce on abduction](http://users.uoa.gr/~psillos/PapersI/11-Peirce-Abduction.pdf)
  - [IEP: Peirce's Logic](https://iep.utm.edu/peir-log/)
- **Whewell:**
  - [SEP: Whewell](https://plato.stanford.edu/entries/whewell/)
  - [SEP Winter 2009 edition](https://plato.stanford.edu/archives/win2009/entries/whewell/)
  - [Whewell–Mill debate](https://www.researchgate.net/publication/237432830_The_Debate_between_Whewell_and_Mill_on_the_Nature_of_Scientific_Induction)
- **Wilson:**
  - [Wikipedia: Consilience (book)](https://en.wikipedia.org/wiki/Consilience_(book))
  - [Orr, Boston Review](https://www.bostonreview.net/articles/h-allen-orr-big-picture/)
  - [American Scientist review](https://www.americanscientist.org/article/e.-o.-wilsons-consilience-a-noble-unifying-vision-grandly-expressed)
  - [Critical analysis (RESF)](https://revistas.ucm.es/index.php/RESF/en/article/view/100581)
- **Guilford:**
  - [InstructionalDesign.org: Structure of Intellect](https://www.instructionaldesign.org/theories/intellect/)
  - [Cogn-IQ: convergent thinking](https://www.cogn-iq.org/learn/theory/convergent-thinking/)
  - [Cogn-IQ: Structure of Intellect](https://www.cogn-iq.org/learn/theory/structure-of-intellect/)
- **Double Diamond:**
  - [Wikipedia](https://en.wikipedia.org/wiki/Double_Diamond_(design_process_model))
  - [Designing Buildings](https://www.designingbuildings.co.uk/wiki/Double%20diamond%20design%20process)
  - [ThinkInsights](https://thinkinsights.net/consulting/double-diamond)
  - The Design Council's original page was not retrieved.
- **Weick:**
  - [Review of the 1995 book](https://www.researchgate.net/publication/257397559_Sensemaking_in_organizations_by_Karl_E_Weick_Thousand_Oaks_CA_Sage_Publications_1995_231_pp)
  - [Louisiana Civil Service handout](https://www.civilservice.louisiana.gov/files/divisions/training/Weick_Sensemaking_With_Disruptions.pdf)
  - [Wikipedia: Sensemaking](https://en.wikipedia.org/wiki/Sensemaking)
- **Klein:**
  - [Klein, Moon and Hoffman 2006](https://perigeantechnologies.com/publications/MakingSenseofSensemaking2-AMacrocognitiveModel.pdf)
  - [Gary Klein: Data-Frame Theory](https://www.gary-klein.com/data-frame)
  - [Frontiers 2023, plausibility transition model](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2023.1160132/full)
- **Pirolli and Card 2005:**
  - [PDF, andymatuschak.org](https://andymatuschak.org/files/papers/Pirolli,%20Card%20-%202005%20-%20The%20sensemaking%20process%20and%20leverage%20points%20for%20analyst%20technology%20as.pdf): fetch failed.
  - [ResearchGate](https://www.researchgate.net/publication/215439203_The_sensemaking_process_and_leverage_points_for_analyst_technology_as_identified_through_cognitive_task_analysis)
  - [Iceberg Sensemaking (arXiv)](https://arxiv.org/html/2204.04758v3)
  - [Redalyc, sensemaking loop in digital history](https://www.redalyc.org/journal/589/58980067002/html/)
- **Luhmann:**
  - [zettelkasten.de translation](https://zettelkasten.de/communications-with-zettelkastens/)
  - [Ernest Chiang, Luhmann's original Zettelkasten](https://www.ernestchiang.com/en/posts/2025/niklas-luhmann-original-zettelkasten-method/)
  - [Zettelkasten forum: Kommunikationspartner](https://forum.zettelkasten.de/discussion/2868/kommunikationspartner)
  - [Dan Allosso: revisiting the 1981 article](https://danallosso.substack.com/p/revisiting-luhmanns-1981-zettelkasten)
  - Primary text not opened.
- **Matuschak:**
  - [Evergreen notes should be concept-oriented](https://notes.andymatuschak.org/Evergreen_notes_should_be_concept-oriented)
  - [Evergreen notes](https://notes.andymatuschak.org/z5E5QawiXCMbtNtupvxeoEX)
  - [Maggie Appleton, Growing the Evergreens](https://maggieappleton.com/evergreens)
- **Alexander:**
  - [Wikipedia: A Pattern Language](https://en.wikipedia.org/wiki/A_Pattern_Language)
  - [Book PDF (knu.edu.tw)](https://ocw.knu.edu.tw/sysdata/doc/1/1b24102d69091f2d/pdf.pdf)
  - [Gaurav Sharma, all 253 patterns](https://gauravsharma.com/design/christopher-alexander/pattern-language/)
- **Kuhn and Lakatos:**
  - [Routledge REP: Kuhn](https://www.rep.routledge.com/dms/Kuhn.pdf)
  - [Kindi, "Paradigm"](https://eclass-b.uoa.gr/modules/document/file.php/PHS269/Kindi_Paradigm_Encyclopedia%20of%20Social%20Theory.pdf)
  - [DBU, Kuhn's Postscript](https://www3.dbu.edu/mitchell/kuhnpostscript.htm)
  - [Methodology of scientific research programmes](https://www.qualityresearchinternational.com/socialresearch/methodologyofscientificresearchprogrammes.htm)
  - [Aeon, Lakatos](https://aeon.co/essays/imre-lakatos-and-the-philosophy-of-bad-science)
  - [Stagnant Lakatosian research programmes (arXiv)](https://arxiv.org/pdf/2404.18307)
  - No SEP Kuhn entry was returned.
- **Analogy mining:**
  - [Hope et al. 2017 (arXiv)](https://arxiv.org/abs/1706.05585)
  - [ACM](https://dl.acm.org/doi/10.1145/3097983.3098038)
  - [PNAS 2019](https://www.pnas.org/doi/abs/10.1073/pnas.1807185116)
  - [arXiv 2102.09761](https://arxiv.org/pdf/2102.09761)
