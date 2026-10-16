# Glossary — <project or client>

Copy to `knowledge/glossary.md` in the project. The `translate` skill reads it before every job.
One row per term. Keep the table sorted by source term. Add rows only after the user approves them.

**Columns**
- **Source** / **Target**: the term exactly as it appears; for en→ko jobs, the source is English.
- **Dir**: `ko-en`, `en-ko`, or `both`.
- **Domain**: legal, tech, medical, business, marketing, game, general, ...
- **Client**: client id, or `any` if it's the user's own default.
- **DNT**: `Y` = do not translate (keep byte-identical: brand names, product names, UI strings, code, tags). Target column then repeats the source.
- **Status**: `approved` (client- or user-confirmed), `preferred` (user default, can change), `proposed` (from a translation, awaiting approval), `forbidden` (never use this target; put the reason in Notes).
- **Notes**: context, part of speech, casing, plural form, alternatives rejected and why, source of the decision (email date, style sheet).

| Source | Target | Dir | Domain | Client | DNT | Status | Notes |
|---|---|---|---|---|---|---|---|
| 계약서 | agreement | ko-en | legal | any | N | preferred | "contract" only when the client's style sheet says so |
| 담당자 | point of contact | ko-en | business | any | N | preferred | "person in charge" sounds translated; avoid |
| 수고하셨습니다 | — | ko-en | business | any | N | preferred | No fixed equivalent; render by situation ("Thanks for your work on this") |
| Acme Cloud | Acme Cloud | both | tech | acme | Y | approved | Product name; never 아크미 클라우드 |
| {{user_name}} | {{user_name}} | both | tech | any | Y | approved | Placeholder; keep braces exactly |
| stakeholder | 이해관계자 | en-ko | business | any | N | proposed | Check: client may prefer 관계자 |

## Client style-sheet notes
- <client>: <rules from their style guide that aren't single terms, e.g. "use 합니다체 in UI, no exclamation marks">

## Changelog
- YYYY-MM-DD: <added/changed terms, who approved>
