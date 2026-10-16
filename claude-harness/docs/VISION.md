# Vision: why this harness exists

The owner's words, distilled (2026-10-16). Every design choice in this repo serves these goals. When two goals conflict, raise it; don't settle it silently (principle 17).

1. **Data good enough to train on.** Everything logged (prompts, intent, agent traces, corrections, draft→final edits, verifier verdicts, rubric scores, decisions) should be labeled, structured and documented so that it is useful for future fine-tuning, reward models, RL environments and evals, not just for looking things up. Logging quality is a product in itself.
   - Every record carries its provenance, its rights and consent, a PII status, whether it is human or synthetic, and how its label was made (`docs/` training-readiness spec, in progress).
   - Client, NDA and third-party content is never exported for training.
2. **Albers is AI-native.** The company runs through this harness. The founder relies heavily on AI, and future hires will be fully AI-native. RL-style continuous improvement is the core skill, using every deployable AI technique and the state of the art as it is today.
3. **It keeps updating.** New models, Claude Code features, papers and techniques are taken in continuously, but adopted only when they beat the current setup on our own evals (SOTA intake, in progress).
4. **People and agents work together.** When people join, they plug into the same harness: shared skills, ontology, decision records and review rituals. Communication between humans and their agents is explicit: handoffs, decision records, and "ask the human" rules. Everyone's progress becomes part of what the system learns from.
5. **No compromise.** World-class, verified, with nothing left half-done (principle 17).

Related: `global/PRINCIPLES.md`, `BLUEPRINT.md` §0.5, `docs/FANOUT.md`, `docs/PATTERNS.md`, `schema/`.
