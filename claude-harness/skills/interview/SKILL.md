---
name: interview
description: Short scope interview before any non-trivial task. Asks only questions whose answers change the plan, proposes defaults from stored preferences, and records the answers. Use at the start of research, translation, applications, code features, art work, or anything with unclear scope.
argument-hint: "<task description>"
---

# Scope interview

Task: $ARGUMENTS

## 1. Recall
- Classify the task: area (`schema/ontology.yaml`) and task type (e.g. research report, translation, job application).
- Read `$HARNESS_DATA/preferences.jsonl` and pull entries whose `scope` matches this task type, then this area, then `global`. Newer entries win over older ones.
- Read the project's `CLAUDE.md` and `PROGRESS.md` if they exist. Don't ask what they already answer.

## 2. Ask (one message)
Only the questions that change the plan, each with a proposed default from step 1:
- **Goal and "done":** what outcome, and how we'll know it's met.
- **Audience and register:** who reads it; register from `schema/ontology.yaml`.
- **Depth:** quick, standard or exhaustive.
- **Sources:** trusted and banned.
- **Budget:** time, money, number of agents.
- **Deadline.**

Format: a numbered list, `Q — proposed: <default> (from <pref id or "no history">)`. Tell the user they can reply "ok" to accept all defaults. Never ask more than 6 questions.

## 3. Record
- Write the agreed scope and acceptance criteria to `SPEC.md` (or the task entry in `PROGRESS.md`). These become the verifier's criteria.
- Append each **new or changed** answer to `$HARNESS_DATA/preferences.jsonl` as a `Preference`: `{id, statement, scope, task_type, source_event, ts}`. Don't duplicate unchanged ones.
- Append a `prompt`-linked `task` event with `intent` (the real goal behind the ask), `situation` (constraints, deadline) and `meta` (`kind_of_thing: scope interview`, which defaults were accepted vs. overridden).

## 4. Hand back
Return the scope block. Don't start the work.
