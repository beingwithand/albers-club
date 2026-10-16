# Registers / 문체 구분

> **DRAFT for user review (2026-10-16).** Claude wrote these as generic starting points. They are not yet your style. Replace each `<<fill: ...>>` with your own rules and examples, delete anything that doesn't match how you write, then remove this banner. Over time, approved rules from `$HARNESS_DATA/style/guide.md` (built by the `style-guide` skill from your edits) should replace the generic text here.

The register ids below are the ones in `schema/ontology.yaml` (`registers:`). `scripts/style_pairs.py` rejects anything else, so add a register there first (by reviewed PR) if you need a new one.

For each register: when it applies, Korean cues, English cues, and your own rules.

---

## `formal-email` — 격식 이메일 / Formal email
**When / 언제:** First contact, new clients, agencies, institutions, people senior to you, anything with money or deadlines in writing. 첫 연락, 신규 클라이언트, 기관, 윗사람, 견적·마감 등 기록이 남는 메일.

**Korean cues:** 하십시오체 as the base (～합니다, ～드립니다, ～하시겠습니까); 해요체 only in softening lines if at all. Set openers/closers: 안녕하십니까/안녕하세요, ○○○ 님 / 감사합니다, ○○○ 드림. Avoid 반말, emoticons, ㅎㅎ.

**English cues:** Full sentences, few contractions, "Dear X," or "Hi X," depending on the client, clear ask in the first paragraph, "Best regards," closing. Avoid over-literal Korean politeness ("I humbly request").

**My rules / 내 규칙:**
- Opener I use: <<fill: e.g. 안녕하세요, ○○○ 님. / Hi Ms. Kim,>>
- Closer and signature: <<fill>>
- 하십시오체 vs 해요체 mix I'm comfortable with: <<fill>>
- Phrases I never use: <<fill>>
- Example (draft → my final): <<fill>>

---

## `office` — 사내·업무 / Office and business
**When / 언제:** Colleagues, project managers, regular clients you already work with; Slack/Teams/메신저 work threads, status updates, meeting notes.

**Korean cues:** 해요체 base (～해요, ～할게요, ～드릴게요), 하십시오체 for announcements or reports up the chain. Common set phrases: 확인 부탁드립니다, 공유드립니다, 수고하셨습니다. Short, scannable.

**English cues:** Direct and concise, contractions fine, bullets for status, explicit owners and dates. "Thanks!" acceptable.

**My rules / 내 규칙:**
- When I switch from 해요체 to 하십시오체 at work: <<fill>>
- How I render 수고하셨습니다 / 확인 부탁드립니다 in English: <<fill>>
- Example: <<fill>>

---

## `friendly` — 친근한 존댓말 / Friendly but polite
**When / 언제:** Acquaintances, friendly clients after rapport, community posts, thank-you notes; warm but not intimate.

**Korean cues:** 해요체, softeners (～네요, ～거든요, ～더라고요), occasional ^^ or ㅎㅎ if the other side uses them; no 반말.

**English cues:** Casual-polite, contractions, exclamation marks in moderation, first names.

**My rules / 내 규칙:**
- Emoticons / ㅎㅎ / ^^ policy: <<fill>>
- Example: <<fill>>

---

## `chat` — 채팅·반말 / Casual chat
**When / 언제:** Close friends, family, peers who've agreed to 말 놓기; KakaoTalk, DMs.

**Korean cues:** 반말 (～해, ～했어, ～하자, ～야/～아), dropped subjects and particles, ㅋㅋ/ㅎㅎ/ㅠㅠ, abbreviations (ㅇㅇ, ㄱㄱ, ㄹㅇ), short lines sent as separate messages. Only use 반말 where the relationship already has it.

**English cues:** Lowercase is fine, fragments, abbreviations (lol, tbh), emoji; don't translate ㅋㅋ literally (lol / haha / nothing, by tone).

**My rules / 내 규칙:**
- Who gets 반말 vs 해요체 in chat: <<fill>>
- Laugh markers I actually use (ㅋㅋ vs ㅎㅎ, lol vs haha): <<fill>>
- Example: <<fill>>

---

## `client-deliverable` — 납품 번역물 / Client deliverable
**When / 언제:** The translated document, subtitles, UI strings or copy you hand to a client. The register is set by the **client's** brief and style sheet, not your voice.

**Korean cues:** Usually 합니다체/하십시오체 for documents and UI, 해요체 for consumer-facing apps if the client asks; consistent terminology from the glossary; no translator's notes in the body (send them separately).

**English cues:** Client's spelling standard (US/UK), house style (serial comma, title case), consistent terminology; natural target-language flow over literal structure unless the client wants literal.

**My rules / 내 규칙:**
- Default when the client gives no style sheet: <<fill>>
- How I deliver translator's notes / queries: <<fill>>
- Quality checklist I always run: <<fill>>

---

## `annotation-response` — 데이터 어노테이션 응답 / Data-annotation response
**When / 언제:** Writing model responses, rationales, ratings or rewrites for annotation/RLHF projects.

**Korean cues:** Follow the project guideline's 문체 (often 해요체 for assistant responses, 합니다체 for rationales); neutral, no slang; natural Korean, not translationese.

**English cues:** Guideline-defined tone (often neutral-helpful), justified ratings that cite the specific span, no filler or hedging beyond what accuracy needs.

**My rules / 내 규칙:**
- Projects and their guideline tone: <<fill: project → tone>>
- How I structure a rationale: <<fill>>
- Words or patterns reviewers flagged: <<fill>>
- Example: <<fill>>

---

## Cross-register notes / 공통
- Signs I've picked the wrong register: <<fill>>
- Mixed-language habits (when I keep English terms in Korean text): <<fill>>
