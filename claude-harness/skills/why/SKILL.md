---
name: why
description: Record a decision with its intent, justification, evidence, alternatives and a checkable prediction. Use when the user says /why or makes a notable choice.
argument-hint: "<the decision>"
---

# Decision record

Decision: $ARGUMENTS

If anything below is missing, ask for it in **one** short message. Don't invent reasons.

Append to `decisions.md` in the project, and append a `decision` event to the log:

```markdown
## D-<YYYYMMDD>-<n>: <claim>
- **Intent / situation:**
- **Reasons (specific, checkable):**
- **Evidence:** links or proofs
- **Alternatives rejected and why:**
- **Expected outcome (metric + date):**
- **Review on:** <date>
- **Meta:** what kind of decision this is, and whether it should become a rule
```
