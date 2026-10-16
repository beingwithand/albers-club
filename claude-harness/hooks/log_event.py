"""Append a raw event to $HARNESS_DATA/log/YYYY-MM.jsonl from a Claude Code hook.

Raw capture plus one cheap tag. Prompts get `correction_candidate` and
`correction_confidence` from a regex table (English and Korean). The tag is only a
hint for the weekly labeling pass, which still decides `is_correction` with a cheap
model. The hook stays fast, append-only, and never blocks (always exits 0).

Pattern-table shape (regex, name, confidence) follows BayramAnnakov/claude-reflect
`scripts/lib/reflect_utils.py` (MIT, (c) 2025 Bayram Annakov); the patterns here are
rewritten, and the Korean ones are new.
Field names follow the hooks reference; verify against
https://code.claude.com/docs/en/hooks if a field comes back empty.
"""
import datetime
import json
import os
import pathlib
import re
import sys
import uuid

CANDIDATE_THRESHOLD = 0.5
LONG_PROMPT = 400  # long prompts are usually task specs; "don't" there is an instruction

# (regex, name, confidence). Matched case-insensitively against the stripped prompt.
CORRECTION_PATTERNS = [
    # English
    (r"^no[,.!:;—–-]+\s*\S", "no,", 0.80),
    (r"^no\s+\S", "no-bare", 0.60),
    (r"that'?s (?:wrong|incorrect|not right)|that is (?:wrong|incorrect|not right)", "that's-wrong", 0.90),
    (r"\bnot what I (?:asked|wanted|meant|said)\b|^not what I\b", "not-what-I", 0.90),
    (r"^I (?:said|meant)\b|\bI (?:already )?told you\b", "I-said", 0.85),
    (r"^(?:don'?t|do not)\b", "don't-start", 0.75),
    (r"\b(?:don'?t|do not)\b", "don't", 0.45),
    (r"^(?:stop|never)\b", "stop/never", 0.75),
    (r"\binstead\b", "instead", 0.50),
    (r"^actually[,. ]", "actually", 0.50),
    (r"\buse .{1,30}? not\b", "use-X-not-Y", 0.70),
    (r"\b(?:wrong|incorrect)\b", "wrong", 0.55),
    (r"\bwhy did you\b", "why-did-you", 0.70),
    (r"\b(?:revert|undo) (?:that|this|it)\b", "revert", 0.70),
    # Korean
    (r"^아니(?!면|라면)", "아니-start", 0.80),
    (r"아니야|아니잖아|아니에요|아닌데", "아니야", 0.80),
    (r"그게\s*아니(?:라|고)|그거\s*아니(?:라|고)|이게\s*아니(?:라|고)", "그게-아니라", 0.90),
    (r"말고", "말고", 0.60),
    (r"틀렸|틀린\s*거|틀려", "틀렸", 0.85),
    (r"잘못", "잘못", 0.70),
    (r"하지\s*(?:마|말라|말고|말아)", "하지-마", 0.80),
    (r"왜\s*.{0,30}?했(?:어|냐|니|지|어요|나요)", "왜-했어", 0.80),
    (r"(?:내가|제가)\s*(?:말했|말한|얘기했|분명히)", "내가-말했", 0.85),
    (r"다시", "다시", 0.40),
    (r"대신", "대신", 0.50),
]

# Benign shapes that look like correction openers (subset of claude-reflect's list).
NON_CORRECTION = [
    r"^no\s+(?:problem|worries|need|way|idea|rush|hurry|pressure|thanks?)\b",
    r"^don'?t\s+(?:worry|mind|bother)\b",
    r"^never\s*mind\b",
    r"^stop\s+worrying\b",
    r"^no\s+(?:it|that|this)\s+(?:'?s|is|was|works?|looks?)\s+(?:fine|good|ok|okay|right|correct)?",
    r"^아니(?:요|에요)?[,.\s]*(?:괜찮|됐어|좋아)",
]
# Questions and task openers are usually new requests, not corrections.
QUESTIONISH = [
    r"[?？]\s*$",
    r"^(?:please|can you|could you|would you|help me)\b",
    r"(?:까|나요|니)\s*[?？]?\s*$",
]
QUESTION_EXEMPT = {"why-did-you", "왜-했어", "that's-wrong", "not-what-I", "그게-아니라"}

_COMPILED = [(re.compile(p, re.IGNORECASE), n, c) for p, n, c in CORRECTION_PATTERNS]
_NON = [re.compile(p, re.IGNORECASE) for p in NON_CORRECTION]
_QUEST = [re.compile(p, re.IGNORECASE) for p in QUESTIONISH]


def detect_correction(text):
    """Return (is_candidate, confidence, pattern_names). Never raises."""
    try:
        if not isinstance(text, str):
            return False, 0.0, []
        t = text.strip()
        if not t:
            return False, 0.0, []
        if any(rx.search(t) for rx in _NON):
            return False, 0.0, []
        hits = [(n, c) for rx, n, c in _COMPILED if rx.search(t)]
        if not hits:
            return False, 0.0, []
        name, conf = max(hits, key=lambda h: h[1])
        if len(hits) > 1:  # several independent signals: small bump
            conf = min(0.95, conf + 0.05 * (len(hits) - 1))
        if any(rx.search(t) for rx in _QUEST) and name not in QUESTION_EXEMPT:
            conf *= 0.5
        if len(t) > LONG_PROMPT:
            conf *= 0.6
        conf = round(conf, 2)
        return conf >= CANDIDATE_THRESHOLD, conf, [n for n, _ in hits]
    except Exception:
        return False, 0.0, []


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    data_dir = pathlib.Path(os.environ.get("HARNESS_DATA", pathlib.Path.home() / "harness-data"))
    now = datetime.datetime.now(datetime.timezone.utc)
    log_dir = data_dir / "log"
    log_dir.mkdir(parents=True, exist_ok=True)

    cwd = payload.get("cwd", os.getcwd())
    content = payload.get("prompt") if kind == "prompt" else None
    event = {
        "id": f"evt_{now:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:4]}",
        "ts": now.isoformat(),
        "actor": "me" if kind == "prompt" else "harness",
        "type": kind,
        "scope_hint": cwd,
        "session_id": payload.get("session_id"),
        "content": content,
        "transcript_path": payload.get("transcript_path"),
        "end_reason": payload.get("reason") if kind == "session_end" else None,
        "labels": [],
        "intent": None,     # filled by weekly labeling pass
        "meta": None,       # filled by weekly labeling pass
    }
    if kind == "prompt":
        cand, conf, names = detect_correction(content)
        event["correction_candidate"] = cand
        event["correction_confidence"] = conf
        if names:
            event["correction_patterns"] = names

    with open(log_dir / f"{now:%Y-%m}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
