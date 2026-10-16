---
name: prior-art
description: Before implementing any technical feature, research how others have built it (apps, repos, papers), compare state-of-the-art approaches including adjacent ideas, assess deployability, and propose options plus experiments. Use whenever the user asks for a technical feature, integration or architecture choice.
argument-hint: "<feature or problem>"
---

# Prior art: study how it's done before building

Feature or problem: $ARGUMENTS

## 1. Scope interview (short)
- **Intent:** what the feature should achieve for users, and the real goal behind the request.
- **Constraints:** the stack (read the repo first), budget, performance, platforms (e.g. iOS Safari), and the deadline.
- **Depth:**
  - quick: about 3 references
  - standard: 3 parallel researchers
  - exhaustive: 5 or more
- **Appetite for the new:** proven only, proven plus one experiment, or exploratory.

## 2. Fan out
Use `web-researcher` agents, one track each:
1. **Who already does this well.** Real apps and sites: how they appear to implement it. Use public code, network behavior, bundles, docs, engineering blogs and talks, reading only what's publicly available, legitimately. Record what the user experiences and how it works under the hood.
   - **Tool: REA (Reverse Engineer Anything)**, from github.com/morluto/rea, the MCP version `npx rea-agents setup`. Install only from the official repo, rea.tools or the `rea-agents` npm package, because there are trojanized copies. REA inspects websites (browser observation), JS/Electron apps, native binaries (via Ghidra, Hopper or IDA), .NET and Android, and its results carry evidence. Use it to understand *how* a feature works, then build our own version.
   - **Ethics:** REA is for understanding and interoperability only. Never copy proprietary code or assets, bypass DRM, license checks or auth, or analyze anything we aren't allowed to. Follow REA's DISCLAIMER.md and the target's terms.
2. **Open-source implementations.** GitHub repos and libraries ranked by recent activity, issue health, license and adoption (stars are inflated, so don't rely on them). Read the actual code paths, not just the README.
3. **State of the art.** Recent papers, standards, browser and platform capabilities, and what changed in the last 6–12 months.
4. **Adjacent ideas.** Techniques from neighboring fields or other products that aren't obvious matches but could combine into something better. Mark these clearly as speculative.

## 3. Compare
Present a table of the options with these columns:
- approach
- examples (with links)
- fit with our stack
- deployability (maturity, license, bundle size or performance, browser support, maintenance)
- risks
- effort
- what makes it distinctive

## 4. Recommend and plan
- A recommended approach, justified with evidence.
- Optionally, **one experiment** to try (a spike with a success metric and a timebox).
- Concrete reference snippets or patterns to imitate. AI implements best from examples.
- A `SPEC.md` with acceptance criteria, which the verifier will use.

## 5. Log
- Save the research to `research/<date>_<feature>.md`.
- Record the chosen option with `/why`, including the alternatives that were rejected.
- Extract any reusable principle (see `distill-principles`).
