# Multi-account Google Drive + email attachments → one findable, logged index (research notes, 2026-10-16)

Goal: every file across several personal Gmail accounts + the Workspace account `hello@albers.club`
(own files, client-shared files, email attachments) is findable, logged and organized for the harness,
**without** handing NDA client files to third-party aggregators and **without** touching client sharing.

Harness context read first: `docs/MESSAGING.md` (rule zero: raw client content → `~/msg-vault`, never git;
only derived records → `~/harness-data`), `skills/intake/SKILL.md` (sha256 fingerprint, provenance,
verify-before-archive), `docs/LOCAL_ONLY.md` (no cloud converters for client text), `docs/BACKUP.md`
(3-2-1; Drive for desktop Mirror; never sync git repos), `schema/ontology.yaml` v0.2 (`Account`,
`Document`, `Attachment`, `Organization`, `Client`, `SyncCursor`; enum `account_connection:
[claude-connector, takeout, imap, api, forwarding]`).

Legend: **[V]** verified in an official doc / project source I could read; **[S]** from search-result
snippets of official pages or from third-party pages (verify before relying); **[?]** my inference.

**Reachability:** `support.google.com`, `developers.google.com`, `knowledge.workspace.google.com` and
`rclone.org` were NOT fetchable from this sandbox (DNS failure / proxy 403). rclone facts come from the
upstream doc source `github.com/rclone/rclone/docs/content/drive.md` (read in full) and the `gws` facts from
`github.com/googleworkspace/cli` README (read). Google Help facts are from search snippets of the official
pages → marked [S]. Re-check them in a browser on the Mac.

---

## 0. TL;DR — recommended architecture

```
                 ┌───────── secondary Gmail accounts (acct_gmail_a, _b, _c …) ─────────┐
                 │  own files: shared (Editor) to hub, ownership stays                   │
                 │  client "Shared with me": left where it is; clients asked to also     │
                 │  share with hello@albers.club going forward                           │
                 │  mail: auto-forward → hub  (+ one-time Takeout mbox backfill)         │
                 └───────────────────────────────────────────────────────────────────────┘
                                      │ share / forward
                                      ▼
  HUB = hello@albers.club (Workspace)  ← the ONE account the Claude Drive/Gmail connector uses
                                      │
     ┌────────────────────────────────┼─────────────────────────────────────────────┐
     ▼                                ▼                                             ▼
 Drive for desktop (Mac)        rclone (read-only, own OAuth client,          gws CLI (read-only,
 hub + up to 3 more accounts,   one remote per account) → nightly             per-account config dir)
 hub = Mirror, others = Stream  backup + export of Google-native docs          → metadata the
 ~/Library/CloudStorage/…       into ~/drive-vault/<acct>/ (local only)        index needs (owner,
                                                                               sharingUser, perms)
     └────────────────────────────────┬─────────────────────────────────────────────┘
                                      ▼
            ~/drive-vault/index/files.sqlite  (+ files.jsonl)  ← unified manifest, LOCAL ONLY
            one row per (account, fileId) + one row per mail attachment; sha256 dedupe;
            client / project / sensitivity columns
                                      │ derived, non-sensitive only
                                      ▼
            ~/harness-data: accounts.jsonl, organizations.jsonl, drive_sync events (counts, ids)
```

Rules in one line each:
1. **Hub = `hello@albers.club`.** Workspace gives shared drives, admin-side migration tools, an "Internal"
   OAuth app option, pooled storage, and is the business identity clients should share to. The Claude
   connector stays on the hub permanently; no connector switching.
2. **Never move or re-share client files.** Only *you* stop collecting new client files on secondary
   accounts (ask clients to share with the hub). Old client shares are read where they are, via that
   account's read-only rclone/gws credentials.
3. **Everything that reads Drive programmatically is read-only** (`drive.readonly`) and uses **your own**
   OAuth client. No aggregator holds a token.
4. **Bytes stay local** (`~/drive-vault`, `~/msg-vault`: FileVault, mode 700, never git, never re-uploaded
   to another cloud). Only counts/ids/derived records go to `~/harness-data`.
5. **Index, don't consolidate.** A sha256-keyed manifest across all accounts beats physically moving files
   (which changes file IDs, breaks client links, and can violate NDAs).

---

## 1. Consolidating Drives across accounts — what Google actually allows

### 1.1 Ownership transfer
| Case | Allowed? | Notes |
|---|---|---|
| personal Gmail → personal Gmail | **Yes, with acceptance** [S] | Share → set role "Transfer ownership" → recipient gets an email and must accept; until then you stay owner ("pending owner"). Google developer docs: ownership can be transferred "from one consumer account to another" and Drive "doesn't transfer ownership … until the prospective owner explicitly consents" [S, developers.google.com/workspace/drive/api/guides/transfer-file snippet]. Old owner becomes Editor. Third-party guides say the invitation expires (7 days) [S, unconfirmed]. |
| personal Gmail → Workspace (`hello@albers.club`) | **No** [S] | "You cannot transfer from a personal account to a work or school account." Also: a transfer to a personal account that later becomes a managed account can't be accepted [S, Drive Help 2494892 snippet]. |
| Workspace → Workspace, same org | Yes (instant; admin can also bulk-transfer a user's files) | Not useful here: you are one person in the org. |
| Workspace → outside domain | **No** [S] ("You can only transfer ownership of files to people within your work or school"; rclone doc: "you can't transfer ownership to someone outside your organization" [V]) | |
| Files you don't own (client "Shared with me") | **Never yours to transfer.** | Leave them. |

**Consequence:** to get your *own* personal files "into" the Workspace account you must **copy** (new file
IDs, new owner = hub) or **share** (owner unchanged). Prefer **share the top-level folder to the hub with
Editor** for active material (zero copy, keeps IDs/links, quota stays on the secondary account). Copy only
archival material you want to own in Workspace (`rclone copy` between remotes, §3.5).

### 1.2 Google's own migration tools
- **Workspace transfer tool for unmanaged accounts** [S, knowledge.workspace.google.com/admin/users/use-the-transfer-tool-to-migrate-unmanaged-personal-accounts]: only for *consumer accounts whose address is already in your domain* (e.g. a consumer Google Account created on `x@albers.club`). Not for `@gmail.com`. Blocked if the account is in a family group. Probably irrelevant unless you once made a consumer account with an `@albers.club` address [?].
- **Admin console Data Migration service (New)** [S]: officially supports *personal Gmail → Workspace mailbox* (email, and per Google guidance calendar/contacts). For **Drive** the evidence is mixed: Google's marketing page says Drive migration "from personal accounts" is supported; 2026 third-party guides say the data migration service doesn't touch Drive. **Verify in Admin console → Data → Data import & export → Data migration (New)** before relying on it. Mail import into the hub is the useful part (backfill of secondary mailboxes, §5).
- **"Copy data between Google Workspace accounts" / Education "Transfer your content"**: Workspace→Workspace or school→personal only; not applicable [S].
- **Google Takeout** (per account): exports only **files you own**; **"Shared with me" items are not included** [S, several university IT guides + third parties]. Docs/Sheets/Slides are converted (choose docx/xlsx/pptx or pdf/odt…), formatting/formulas can change [S]. Scheduled option: **every 2 months for 1 year** (6 archives), not available for Advanced Protection accounts [S, support.google.com/accounts/answer/3024190 snippet]. Delivery: download link or add to Drive/Dropbox/OneDrive/Box (adding to Drive eats that account's quota). Good as an **independent, Google-made cold copy**, not as the sync mechanism.

### 1.3 Shared drives
- Shared drives need Workspace (the hub has them if the edition includes them; verify Business Starter's shared-drive entitlement in Admin console [?]). Files in a shared drive are owned by the org, not a person; you can add your own Gmail accounts as external members (Contributor/Content manager) if external sharing is allowed [S, support.google.com/a/answer/60781 snippet].
- **Use:** one shared drive per *your own* domain of work (e.g. `Albers — Translation`, `Albers — Art`) as the target for files you copy into Workspace ownership. **Do not** put client files there unless the client created/shared it that way; moving a file into a shared drive requires being its owner (or manager) and changes who controls it [?].

### 1.4 "Shared with me"
- Not synced by Drive for desktop and not in Takeout. To make a client folder appear on disk: in the web UI of the account it was shared with, **Organize → Add shortcut** to My Drive [S, Drive Help 2375057 snippet]. Shortcuts change nothing on the client's file (no permission change) [?, consistent with Drive's shortcut model].
- rclone reads them directly with `--drive-shared-with-me` [V] and dereferences shortcuts [V].

---

## 2. Drive for desktop on the Mac (multiple accounts)

Facts:
- **Up to 4 accounts at once** in Drive for desktop [S, Google Help "Customize Drive for desktop settings" 13470231 snippet]. With more than 4 accounts, the rest are reached only via rclone/gws (that's fine; the index doesn't depend on Drive for desktop).
- On current macOS it uses Apple's **File Provider**; location is **`~/Library/CloudStorage/GoogleDrive-<email>/`** (subfolders `My Drive/`, `Shared drives/`, `Other computers/`), shown in Finder under Locations; Google says this location can't be changed [S, Drive Help 12178485 snippet; Macktez]. Per-account folder name contains the email [S].
- **Stream vs Mirror** is per account, for My Drive [S]. Mirror keeps a full local copy (needed for real offline/ripgrep); Stream keeps placeholders and downloads on open. Workspace admins can disallow mirroring [S] (you are the admin of albers.club: allow it).
- **Google-native Docs/Sheets/Slides are `.gdoc/.gsheet/.gslides` link files (~1 KB JSON with URL + doc id), never the content**, in both modes [S, fileinfo.com + forum reports]. ripgrep/Spotlight therefore see only the title/id, not the text. → native docs must be **exported** (rclone, §3) to be searchable/readable offline.

Recommended settings:
| Account | Mode | Why |
|---|---|---|
| `hello@albers.club` (hub) | **Mirror** | full offline copy of all binary files; Claude Code can `rg` it; matches BACKUP.md |
| 2–3 most-used personal accounts | **Stream** | visible in Finder for drag/drop; don't fill the disk |
| remaining accounts | not added | rclone/gws only |

Making it agent-readable without accidents:
- **Do not run recursive `rg`/`find -exec cat` over a Stream folder**: reading placeholders hydrates (downloads) every file [?, File Provider behaviour]. Search the **index** (§6) or the rclone vault instead; use the Mirror folder for direct `rg`.
- macOS will ask the terminal / Claude Code for permission to access `CloudStorage` (Files & Folders / File Provider prompt) [?]. Grant to the terminal app only.
- Drive for desktop is **read-write**: a `rm` or an over-eager edit by an agent propagates to Drive, including to client files where you are Editor. Add deny rules to `~/.claude/settings.json` (merge via `config/settings.json`):
  ```json
  "permissions": { "deny": [
    "Edit(~/Library/CloudStorage/**)", "Write(~/Library/CloudStorage/**)",
    "Bash(rm:*~/Library/CloudStorage*)", "Edit(~/drive-vault/**)", "Write(~/drive-vault/**)"
  ]}
  ```
  (exact rule grammar: check against the official permissions doc when merging [?]). Agents write to project `work/`, never into a sync folder.
- Mark individual folders "Available offline" (Finder right-click) in Stream accounts only where needed.
- Never put git repos inside a Drive folder (BACKUP.md rule).

---

## 3. rclone: one read-only remote per account → local vault + exports

### 3.1 Facts [V, rclone drive.md]
- Scopes: `drive` (default), **`drive.readonly`** ("Files may be listed and downloaded but not uploaded, renamed or deleted"), `drive.file`, `drive.appfolder`, `drive.metadata.readonly` (names only, no content).
- **"The shared client_id is being retired and will stop working during 2026, so creating your own is now strongly recommended."** rclone config now asks "Continue using the shared client_id anyway? n (default)".
- Own client: GCP project → OAuth consent screen (Audience **External** so personal Gmail accounts can sign in; "Internal" only works for users of the Workspace org) → client type **Desktop app**. In **Testing**, "grants will expire after a week"; **publish** the app (needs homepage + privacy-policy URL in Branding; a GitHub Pages page is fine) and stay **unverified** — personal-use apps (<100 users) are exempt from verification; you click through the "unverified app" screen once per account.
- `--drive-shared-with-me` operates on "Shared with me" for list and copy commands.
- `--drive-export-formats` default `docx,xlsx,pptx,svg`; first matching format wins; e.g. `pdf` for archive copies, `md` is a listed export (text/markdown) for Docs. Can also export link files (`url`, `webloc`, `link.html`).
- Hashes: **MD5, SHA1 and SHA256** supported (some pre-2018 uploads lack SHA1/SHA256). Google-native docs have **no** hash (they are exports).
- Shortcuts are dereferenced; `--drive-skip-shortcuts`, `--drive-skip-dangling-shortcuts`.
- Metadata (`-M` / `lsjson -M`): `owner` (with `--drive-metadata-owner read`), `permissions` (`--drive-metadata-permissions read`), `labels`, `copy-requires-writer-permission`, `starred`, `viewed-by-me`, `btime`, `mtime`, `description`.
- `--drive-acknowledge-abuse` downloads files flagged as malware — **don't set it** for client folders.
- Upload limit ~750 GiB/day (undocumented); `--fast-list` speeds big listings a lot; HTTP/2 disabled by default.
- `--server-side-across-configs` allows server-side copy between two Drive remotes (when it works).
- Latest tag seen: `v1.75.2` (via `git ls-remote`) → pin `rclone >= 1.75` (Homebrew).

### 3.2 One OAuth client for everything
Create **one** GCP project (owned by the hub, e.g. `albers-harness-readers`), enable Drive API + Gmail API,
consent screen External + published, scopes `drive.readonly` (+ `gmail.readonly` later for gws if wanted).
One Desktop client id/secret serves all accounts; each account gets its own token. Store the secret in
1Password (`op://Private/google-oauth-harness/client_secret`), never in git.

### 3.3 Config (per account)
```bash
brew install rclone
rclone config            # n) new remote, repeat per account
#   name>          g_hub | g_a | g_b | g_c        (short, no email in the name)
#   Storage>       drive
#   client_id>     <your id>.apps.googleusercontent.com
#   client_secret> <secret>
#   scope>         drive.readonly
#   (sign in in the browser AS THAT ACCOUNT — use a separate Chrome profile per account)
#   Shared Drive?  n   (make an extra remote g_hub_sd with team_drive=<id> per shared drive)
# then encrypt the config file that now holds 4+ refresh tokens:
rclone config encryption set      # store the password in 1Password
export RCLONE_PASSWORD_COMMAND='op read op://Private/rclone-config/password'
```
"Shared with me" needs no extra remote: pass `--drive-shared-with-me` to the same remote and write into a
separate local tree (§3.4).

### 3.4 Nightly backup + export into the local vault
```bash
VAULT=~/drive-vault ; ACCT=g_a
COMMON=(--fast-list --tpslimit 5 --transfers 4 --checkers 8
        --drive-export-formats docx,xlsx,pptx,pdf --drive-skip-dangling-shortcuts
        --drive-metadata-owner read --drive-metadata-permissions read -M
        --log-file "$VAULT/logs/$ACCT.$(date +%F).log" --log-level INFO)
# own files (My Drive)
rclone sync  "$ACCT:"  "$VAULT/$ACCT/my-drive"   "${COMMON[@]}" \
      --backup-dir "$VAULT/$ACCT/.versions/$(date +%F)"
# client files shared with this account (read-only copy; never re-uploaded anywhere)
rclone copy  "$ACCT:"  "$VAULT/$ACCT/shared-with-me" "${COMMON[@]}" --drive-shared-with-me
# machine-readable listing for the index (hashes + owner + permissions)
rclone lsjson -R --hash --metadata --fast-list "$ACCT:" > "$VAULT/index/raw/$ACCT.mydrive.json"
rclone lsjson -R --hash --metadata --fast-list --drive-shared-with-me "$ACCT:" > "$VAULT/index/raw/$ACCT.swm.json"
```
- `sync` + `--backup-dir` keeps deleted/changed files instead of losing them (a deletion on Drive does not
  destroy the local copy). Use `copy` (never `sync`) for shared-with-me so a client revoking access doesn't
  silently delete your record — **but** see §8 (NDA retention): when a project ends, delete per contract.
- Export Google-native docs **twice if you want text search**: `docx,xlsx,pptx` for fidelity, plus a cheap
  text pass for the index: `rclone copy … --drive-export-formats md,csv,txt --include "*.{md,csv,txt}"`
  into `$VAULT/$ACCT/text/` [?: test that `md` export works for your docs; fallback `txt`].
- Respect **`copy-requires-writer-permission=true`** (client disabled download for viewers): rclone will get
  an error; **do not work around it** (no screenshots/print-to-PDF). Log it as `download_blocked` in the index.
- Schedule with launchd (`mac/launchd/com.harness.drivesync.plist`, StartCalendarInterval 02:30, same pattern
  as `com.harness.autocommit.plist`). Run accounts sequentially; `--tpslimit 5` keeps well below API quotas.
- Takeout (§1.2) every 2 months per account = second, Google-produced copy for disaster recovery.

### 3.5 Copying your own archive into Workspace ownership (optional)
```bash
rclone copy g_a:"Archive/2019-2024" g_hub_rw:"Imported/g_a/2019-2024" \
  --server-side-across-configs --drive-metadata-owner off -P
```
Needs a separate **write** remote for the hub (`g_hub_rw`, scope `drive`), used only for this one-off and
then deleted (`rclone config delete g_hub_rw`). New file IDs; old links still point at the originals. Never
do this for client files.

---

## 4. Programmatic multi-account access for agents

| Option | Multi-account? | Verdict for NDA files |
|---|---|---|
| **Claude Drive/Gmail connector** | One Google account per Claude account; connecting another replaces it [S, third-party guides]; open feature request anthropics/claude-code#100407 "allow more than one Google account" [S] | Keep it on the **hub only**. Content read by Claude goes to Anthropic either way (that is the harness's baseline; check each NDA allows AI processing, see §8). |
| **rclone** (local, own client, `drive.readonly`) | Yes, a remote per account | **Recommended** for bulk/backup/listing. Tokens local, encrypted config. |
| **`gws` — googleworkspace/cli** [V README] | Not built-in multi-profile, but `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` overrides the config dir → one dir per account. Credentials AES-256-GCM encrypted with key in OS keyring. JSON output, `--page-all` NDJSON, ships agent skills + an MCP mode. **README disclaimer: not an officially supported Google product.** Latest tag v0.9.1. Unverified (testing) apps are limited to ~25 scopes → `gws auth login --scopes drive` (pick read-only scopes in the picker [?]). | **Recommended** for metadata the index needs that rclone lacks (`sharingUser`, `owners`, `lastModifyingUser`, `sha256Checksum`, `capabilities.canDownload`). Caveat: it loads a `.env` from the current dir (dotenvy) → always run it from a fixed dir, never inside a downloaded/client folder. |
| **Google's official Drive / Gmail remote MCP servers** (`https://drivemcp.googleapis.com/mcp/v1`, `https://gmailmcp.googleapis.com/mcp/v1`) | Per-OAuth-token; in Claude Code you can register one MCP entry per account [?, untested] | **Developer Preview** (needs program enrollment; rollout from May 2026 [S]). Tools include permission management and upload → write-capable. Interesting later; not now. |
| **Self-built MCP** (Python, per-account token files, read-only scope, stdio, local) | Yes | Only if rclone+gws+index are not enough. Security rules: `drive.readonly` only; tokens in Keychain/1Password, not files in the repo; expose `search_index` / `read_vault_file` over the **local index**, not live Drive; no tool that changes permissions or sends mail. |
| **Google Picker + `drive.file`** | Per user pick | Best least-privilege pattern for a future web tool: the app only sees files you explicitly pick. Overkill for a personal harness. |
| **GAM / GAMADV-XTD3** | Workspace admin tool | Useful only for admin tasks on albers.club (e.g. audit sharing); not for personal accounts. |
| **Composio, Carly, Drag and similar aggregators** | Yes (that's their selling point) | **Do not use for any account holding client/NDA files.** They hold your OAuth refresh tokens and proxy content through their servers. Composio disclosed a security incident on 21 May 2026 (API keys and GitHub OAuth tokens exfiltrated per a third-party write-up; Composio's own bulletin confirms unauthorized access to internal systems) [S]. Carly runs as a paid custom connector service [S]; Drag is a SaaS inbox layer [?]. Even with SOC 2, adding a fourth party to an NDA chain is usually a breach of "no disclosure to third parties". Acceptable at most for a throwaway account with no client data. |

---

## 5. Email attachments across accounts

### 5.1 Forwarding hub (from the messaging plan)
- **Gmail POP "Check mail from other accounts" and Gmailify are being discontinued in 2026** [S, The Register 2026-01-05, Thurrott, ITdaily] → the hub can't *pull* from the secondaries. Use **push**:
  in each secondary Gmail: Settings → Forwarding and POP/IMAP → Add forwarding address `hello@albers.club` →
  confirm code in hub → "Forward a copy… and **keep** Gmail's copy" (keep, so the source account remains the
  record and Takeout still works). Optionally forward only via a filter (e.g. `has:attachment OR from:(client domains)`).
- In the hub, label by source: filter `deliveredto:secondary@gmail.com` → label `src/acct_gmail_a` [?, `deliveredto:` works for forwarded mail because the original To/Delivered-To header is preserved — test].
- Forwarding only covers **new** mail. Backfill = Takeout mbox per account (below) or Admin-console Data
  Migration of each personal Gmail into the hub mailbox [S] (convenient, but duplicates every client email
  into Workspace — fine, it's your own mail, but count the storage).
- Record each Account in `accounts.jsonl`: `{id: acct_gmail_a, provider: gmail, forwards_to: acct_ws_hello, connected_via: forwarding, privacy: harness-data, is_hub: false}`.

### 5.2 Takeout mbox → attachments into the vault (local, stdlib only)
Takeout → Mail (choose labels or all) → `.mbox` (attachments are inside the MIME parts). Extract:
```python
# scripts/mbox_attachments.py  (proposal; run with python3 -I; stdlib only; input = untrusted)
import mailbox, hashlib, json, os, sys, email.policy
from email import message_from_bytes
mbox, acct, vault = sys.argv[1], sys.argv[2], os.path.expanduser("~/msg-vault/gmail")
out = open(f"{vault}/{acct}/attachments.jsonl", "a")
for key, raw in mailbox.mbox(mbox).iteritems():
    msg = message_from_bytes(raw.as_bytes(), policy=email.policy.default)
    gmid = msg.get("X-GM-THRID", "") ; mid = msg.get("Message-ID", "")
    for part in msg.iter_attachments():
        data = part.get_payload(decode=True) or b""
        h = hashlib.sha256(data).hexdigest()
        dst = f"{vault}/blobs/{h[:2]}/{h}"           # content-addressed: dedupe across ALL accounts
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), mode=0o700, exist_ok=True)
            with open(dst, "wb") as f: f.write(data)
        out.write(json.dumps({"id": f"att_{h[:12]}_{abs(hash(mid))%10**6}", "message": f"msg_{acct}_{mid}",
            "filename": part.get_filename(), "mime": part.get_content_type(), "sha256": h,
            "size": len(data), "account": acct, "thread": gmid, "date": msg.get("Date")}) + "\n")
```
(Sketch: make ids deterministic with a proper hash, not Python's `hash()`, before using.) Content-addressed
`blobs/` means the same contract PDF mailed to three accounts is stored once.

### 5.3 Linking attachments ↔ Drive copies
- Drive binary files expose `sha256Checksum` (rclone `--hash`, gws `fields=files(id,name,sha256Checksum,…)`).
  Join `attachments.sha256 = drive_files.sha256` → `copy_of` link, no download needed.
- Gmail "Save to Drive" / Docs conversions change bytes (converted to Google format) → fall back to
  `(normalized filename, size ±1%, date ±2 days)` fuzzy match, flagged `match: fuzzy`.

---

## 6. The unified index (manifest)

Location: `~/drive-vault/index/files.sqlite` (+ a `files.jsonl` append-only export). **Local only**: file names
of client documents are themselves confidential (project names, people). `~/harness-data` gets only counts
and ids (a `drive_sync` event per run: `{account, files_seen, new, changed, blocked, errors}`).

Proposed record (new ontology type **`DriveFile`**, store `root: drive-vault` (new root, privacy `vault`)):
| field | source | notes |
|---|---|---|
| `id` | `gd_<acct>_<fileId>` | stable; one row per account×file (the same file seen by two accounts = two rows, same `file_id`) |
| `account` | remote name → `acct_…` | ref Account |
| `file_id`, `name`, `path`, `mime`, `size` | rclone lsjson / gws | |
| `owner` | rclone `owner` metadata / gws `owners[].emailAddress` | |
| `shared_by` | gws `sharingUser.emailAddress` | only present for shared-with-me |
| `origin` | `my-drive` / `shared-with-me` / `shared-drive:<name>` / `attachment` | |
| `organization`, `client`, `project` | rules: owner/sharer domain → `organizations.jsonl` (`org-…`); folder path → project | ref Organization/Client/Project |
| `sensitivity` | `public` / `own` / `client` / `nda` | **default `nda` for anything owned or shared by a non-own address** until a human downgrades it |
| `sha256`, `md5` | Drive API / local hash of export | native docs: none → use `(file_id, modifiedTime)` as identity |
| `modified`, `created`, `last_modifier` | metadata | |
| `is_native` | mime `application/vnd.google-apps.*` | |
| `export_path`, `text_path` | vault paths | |
| `download_blocked` | `copy-requires-writer-permission` / 403 | never circumvent |
| `dup_of` | earliest row with same sha256 | |
| `seen_at`, `gone_at` | sync run | soft-delete when it disappears from Drive |

Builder: `scripts/drive_index.py` (proposal, stdlib + sqlite3): reads `index/raw/*.json` (rclone lsjson) +
gws NDJSON (`gws drive files list --params '{"q":"trashed=false","fields":"nextPageToken,files(id,name,mimeType,owners(emailAddress),sharingUser(emailAddress),sha256Checksum,md5Checksum,modifiedTime,size,parents,capabilities(canDownload))","pageSize":1000}' --page-all` with `GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws/<acct>`), the attachment jsonl files, and
upserts. Agent-facing query: `drive_index.py find "<term>" [--client X] [--account Y]` → paths in the vault.
Full-text: SQLite FTS5 over `text_path` contents (local; converters per `LOCAL_ONLY.md`/kb.py).

Ontology changes to propose (reviewed PR, per ontology header):
- enum `account_connection` += `drive-desktop`, `rclone`, `gws`.
- new type `DriveFile` (above), relation `copy_of: Attachment ↔ DriveFile (via sha256)`, `received_via` gains DriveFile.
- `Document` (project `knowledge/manifest.json`) gets `drive_file: gd_…` and `account` so intake records which account the source came from; `archive` link must be in the **hub** (intake step 7 uploads to the project's hub folder).
- `Organization.domains: [..]` to map owner/sharer email domains → client.
- enum `sensitivity: [public, own, client, nda]`.

Naming conventions (for files **you** create/own; never rename client files):
- Folders in hub: `<area>/<YYYY>_<client-slug>_<project-slug>/{source,work,deliverables,admin}` mirroring the harness `templates/project` layout.
- Files: `YYYY-MM-DD_<client>_<project>_<doc-type>_v<NN>[_<lang>].<ext>` (e.g. `2026-10-16_acme_s2-subs_deliverable_v02_en.docx`).
- Client-shared items: don't rename; put a **shortcut** with your name convention in the project folder.

---

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| **Breaking client permissions** | Never re-share client files to your other accounts yourself (it adds a principal visible in the client's ACL and may breach NDA); ask the client to add the hub. Shortcuts only. All programmatic access read-only; the only write remote is temporary (§3.5). Drive-for-desktop folders denied to agents' Edit/Write/rm. |
| **NDA leakage to third parties** | No aggregators (§4). Vault never synced to another cloud, never git. Backblaze only with private encryption key (BACKUP.md). Converters local (LOCAL_ONLY.md). Index local. Per-client flag `ai_allowed` in `clients.jsonl`; if false, the file is indexed by name only and never opened by an agent. |
| **Retention after a project ends** | NDAs often require return/destruction. Index has `client` + `project` → `drive_index.py purge --client X` deletes vault copies and logs a `drive_purge` event (Time Machine/Backblaze copies age out — note this in the NDA response). |
| **OAuth token theft** | Encrypted rclone config, gws keyring, 1Password for client secret; read-only scopes; review "Third-party apps with account access" quarterly; revoke on device loss (SECURITY.md step list gets "revoke `albers-harness-readers` grants for every account"). |
| **Tokens expire / revoked** | Testing-mode apps expire grants after 7 days → publish the app [V]. Google revokes OAuth tokens that include Gmail scopes when the password changes [?, known Google behaviour; verify] → re-run `rclone config reconnect g_x:` / `gws auth login`. Monitor via the sync log (exit code 2 for gws auth errors [V]). |
| **Account suspension / abuse flags** | Throttle (`--tpslimit 5`), sequential accounts, never `--drive-acknowledge-abuse`, no scraping of shared links you weren't given. Big initial syncs: spread over several nights. |
| **Quotas** | Free Gmail 15 GB shared with Gmail+Photos; copies count against the new owner, shares don't. Takeout delivered "to Drive" uses quota. Upload ~750 GiB/day irrelevant here. Check with `rclone about g_x:`. |
| **Inactive-account deletion** | Personal Google Accounts unused for 2 years may be deleted with their Drive/Gmail [S, support.google.com/accounts/answer/12418290]. API access by your own app probably doesn't count as "use" [?] → calendar a twice-yearly sign-in per secondary account (log it as a `drill` event); a running Takeout schedule is also activity [?]. |
| **2FA / lockout** | Each account: passkey + authenticator + recovery codes in 1Password; recovery email = the hub (but hub's recovery must NOT be one of the secondaries → avoid circular recovery). Advanced Protection blocks scheduled Takeout and may block unverified apps [S/?]. |
| **Stream-folder hydration fills disk** | Don't `rg` stream folders; search the index. |
| **Duplicate truths** | sha256 dedupe, `dup_of`; one canonical location per own file (hub). |
| **Takeout misses shared-with-me** | rclone `--drive-shared-with-me` is the only bulk path for those [V]. |
| **Prompt injection via file content** | Content is data (intake rule). Index stores no instructions; agents read vault files read-only. |

---

## 8. Step list for the new Mac

Prereqs: SECURITY.md part 1 done; 1Password unlocked; FileVault on.

1. **Inventory accounts** → `~/harness-data/accounts.jsonl`: one line per Gmail + `hello@albers.club` (`is_hub: true`). Note which clients use which address (rough list → `organizations.jsonl` with `domains`).
2. **Secure each Google account**: passkey/2FA, recovery codes in 1Password, review third-party app access; remove any old aggregator grants (Composio/Carly/etc.).
3. **Hub decisions in Admin console (albers.club)**: allow Drive for desktop mirroring; confirm shared-drive availability; restrict external sharing defaults to "allowed, with warning"; (optional) Data migration (New) → import the personal Gmail mailboxes.
4. **Forwarding**: each secondary → forward a copy to the hub, keep original; hub filters label `src/<acct>`.
5. **Ask clients** (template email, reviewed by you): "please add hello@albers.club to shared folders; existing access can stay". Track replies in the project CLAUDE.md.
6. **Share your own folders** from each secondary to the hub (Editor). In each secondary web UI, add **shortcuts** for active client folders in "Shared with me".
7. **Drive for desktop**: install; sign in hub (Mirror) + up to 3 personal (Stream). Grant terminal access to CloudStorage when macOS asks. Merge the deny rules (§2) into `~/.claude/settings.json`.
8. **Claude connector**: connect Google Drive + Gmail with the **hub** account only.
9. **GCP project** `albers-harness-readers` (owned by hub): enable Drive API (+ Gmail API), consent screen External, add Branding URLs, **publish**, create Desktop OAuth client; secret → 1Password.
10. **rclone**: `brew install rclone`; `rclone config` one `drive.readonly` remote per account (separate Chrome profile per account for the browser sign-in); `rclone config encryption set`; test `rclone lsd g_a:` and `rclone lsd g_a: --drive-shared-with-me`.
11. **gws** (optional, for sharer/owner metadata): `brew install googleworkspace-cli`; per account `GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws/g_a gws auth login --scopes drive` (choose read-only); test a files.list.
12. **Vault**: `mkdir -p ~/drive-vault/{index/raw,logs} && chmod 700 ~/drive-vault`; exclude from Drive/iCloud; confirm Time Machine (encrypted) + Backblaze (private key) include it.
13. **First sync**, one account per night (§3.4); check logs; then load `com.harness.drivesync.plist` (02:30 nightly).
14. **Takeout**: per account, Drive + Mail, "export every 2 months for 1 year", zip, download link; when each arrives, move to `~/drive-vault/takeout/<acct>/<date>/` and run the mbox extractor (§5.2).
15. **Index**: build `drive_index.py` (proposal), run it after each sync; spot-check 10 random rows against Drive web (owner, sharer, hash) and log a `verification` event.
16. **Ontology PR**: `account_connection` values, `DriveFile`, `sensitivity`, `Organization.domains`, `Document.drive_file`.
17. **Add to the monthly drill** (BACKUP.md): restore one vault file; check last drivesync log < 24 h; `rclone about` per account; sign-in check for any account idle > 18 months.

---

## 9. Open questions / to verify on the Mac
- Exact current Drive Help wording for the 4-account limit and the CloudStorage folder name (pages unreachable here).
- Whether Data migration (New) moves Drive from personal Gmail into Workspace in your edition.
- Business Starter shared-drive entitlement and external-member rules.
- Does `--drive-export-formats md` export Docs faithfully enough for search (else `txt`)?
- `deliveredto:` filter behaviour on forwarded mail.
- Whether Google's Drive MCP (Developer Preview) can be registered per account in Claude Code, and whether it supports a read-only scope.
- Each client NDA: is processing with Claude (Anthropic) permitted? Record as `ai_allowed` per client.

## Sources
- rclone Google Drive backend doc source (read in full): https://github.com/rclone/rclone/blob/master/docs/content/drive.md (mirror of https://rclone.org/drive/, unreachable here)
- googleworkspace/cli README (read): https://github.com/googleworkspace/cli
- Drive Help, make someone else the owner [S]: https://support.google.com/drive/answer/2494892
- Drive API, transfer file ownership [S]: https://developers.google.com/workspace/drive/api/guides/transfer-file
- Drive Help, Use Drive for desktop on macOS [S]: https://support.google.com/drive/answer/12178485
- Drive Help, Customize Drive for desktop settings (4 accounts) [S]: https://support.google.com/drive/answer/13470231
- Drive Help, Find files shared with you [S]: https://support.google.com/drive/answer/2375057
- Google Account Help, download your data / scheduled exports [S]: https://support.google.com/accounts/answer/3024190
- Inactive Google Account Policy [S]: https://support.google.com/accounts/answer/12418290
- Workspace transfer tool for unmanaged accounts [S]: https://knowledge.workspace.google.com/admin/users/use-the-transfer-tool-to-migrate-unmanaged-personal-accounts
- Workspace migration product matrix [S]: https://support.google.com/a/answer/9413033
- Drive migration (Workspace) [S]: https://workspace.google.com/solutions/migration/drive-migration/
- External sharing / shared drives admin help [S]: https://support.google.com/a/answer/60781
- Google Workspace MCP servers (Developer Preview) [S]: https://developers.google.com/workspace/guides/configure-mcp-servers , https://docs.cloud.google.com/mcp/supported-products , https://workspaceupdates.googleblog.com/2026/05/agent-tools-and-security-updates-for-workspace-developers.html
- Gmail POP/Gmailify discontinuation [S]: https://www.theregister.com/2026/01/05/gmail_dropping_pop3/ , https://www.thurrott.com/cloud/331409/gmail-is-discontinuing-pop3-import-and-gmailify-features-for-other-accounts
- Takeout excludes shared-with-me [S]: https://services.udel.edu/TDClient/32/Portal/KB/ArticleDet?ID=1055 , https://cuit.columbia.edu/sites/default/files/content/How%20to%20Use%20Google%20Data%20as%20of%201.31.24.pdf
- .gdoc link files [S]: https://fileinfo.com/help/google_drive_file_types
- Claude connector single account / feature request [S]: https://github.com/anthropics/claude-code/issues/100407 , https://www.usecarly.com/blog/claude-multiple-accounts/
- Composio incident [S]: https://composio.dev/blog/composio-may-2026-security-incident , https://material.security/resources/the-composio-breach-one-token-10242-doors
- Macktez on CloudStorage path [S]: https://www.macktez.com/2023/google-drive-changes-in-macos/
