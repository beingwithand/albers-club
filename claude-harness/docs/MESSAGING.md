# Messaging and email: ingest and triggers

Full research, with commands and sources: `research_notes/Claude harness/message_extraction.md`.

## Rule zero: where data lives
- **Raw messages and attachments** go in `~/msg-vault/` (mode 700, protected by FileVault). This folder is **never a git remote and never synced**, because it holds other people's personal data and client content that may be under NDA.
- **`~/harness-data`**, which is auto-pushed to a private GitHub repo, gets only the small derived records: JobLead, Application, Platform and Contact. Each one points back to the vault with an ID, never a copy of the message.

## How each source gets in
| Source | Backfill | Keeping it up to date | Trigger for new items |
|---|---|---|---|
| Gmail | Takeout mbox of a `kb/...` label (bulk, includes attachments), plus the Gmail connector as a second pass | `email-scan`, run hourly (Routine) | Apps Script polls every 10 min and sends a *pointer* to the Routine `/fire` URL for urgent mail (interview, offer). The `kb/fired` label stops duplicates. |
| Viber | `viber-export-macos` (decrypts locally; needs your approval, since re-signing the app may breach Viber's terms) | Re-export as needed | Forward the message to yourself on iMessage or Telegram, which Channels picks up |
| Lark | `lark-cli im +chat-messages-list --as user ... --format ndjson` | Scheduled poll | `lark-cli event consume im.message.receive_v1` (only for chats the bot can see) |
| Slack | `slackdump archive` (no admin needed; **ask the client first**) | `slackdump resume` | Slack's email notifications, routed through Gmail |
| ProZ | Job-alert emails, plus the official API (OAuth) if needed | Same | Gmail trigger |
| LinkedIn / Glassdoor | Saved-search alert emails only (**no scraping**: it breaks their terms) | Same | Gmail trigger, then parsed into JobLead records with dedupe on `platform:external_id` plus a fingerprint, and the sender checked against spoofing |

## Trigger safety
- Routine `/fire` payloads are untrusted text, and there is no deduplication key, so the caller must avoid sending the same thing twice.
- Routines can use every tool of the connectors they include, so a triggered routine should have **read-only connectors only**.
- Actions with outside effects (sending, applying, paying) always wait for your OK.
