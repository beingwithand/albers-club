---
name: new-project
description: Start a new project from the standard template. Copies templates/project into <area>/<project>, fills in its CLAUDE.md, creates the Drive folder and records the pointer, and logs the event. Use when the user starts any new project, client job or application campaign.
argument-hint: "<area>/<project> [one-line goal]"
---

# New project

Target: $ARGUMENTS

## 1. Check inputs
- `area` must be one of the areas in `schema/ontology.yaml` (translation, annotation, job-search, art, code, research, personal). If it isn't, ask; don't add a new area without approval.
- `project` is lowercase kebab-case. If `<area>/<project>/` already exists, stop and ask.
- If the goal, client or deadline is missing, run `interview` (quick depth).

## 2. Copy the template
Copy the harness `templates/project/` (at `${CLAUDE_PLUGIN_ROOT}/templates/project`, else `~/code/claude-harness/templates/project`) to `<area>/<project>/`, keeping the `.gitkeep` files. Don't overwrite anything.

## 3. Fill `CLAUDE.md`
Replace the placeholders: project name, area, client/owner, goal (intent, in the user's words), Drive folder link. Leave "Project-specific rules" empty unless the user gave one. Keep it short; nothing Claude can infer.

Also fill `PROGRESS.md` → **Goal**, and add `## Next: run /intake on inbox/` if inputs exist.

## 4. Drive folder
- With the Google Drive connector, create the folder `Projects/<area>/<project>/` (folders `inbox`, `deliverables`, `archive` inside it). Search first so you don't duplicate one.
- Write the folder link into `CLAUDE.md` and `knowledge/manifest.json` (`"drive_folder"`).
- If the connector isn't available, write `Drive folder: TODO` and tell the user plainly.

## 5. Finish
1. Run `verify` with these criteria: the folder tree matches the template, no placeholder `<...>` remains in `CLAUDE.md` except unknown fields marked `TODO`, and the Drive link resolves.
2. Append a `task` event to `$HARNESS_DATA/log/YYYY-MM.jsonl` (`schema/event.md`) with `scope: <area>/<project>`, plus `intent` (why the project exists), `situation` (client, deadline, inputs received) and `meta` (`kind_of_thing: project setup`). Also record a `Project` entry (id, area, client, status: active, started, drive_folder).
3. Tell the user the path and the next step (usually `/intake`).
