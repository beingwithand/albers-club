#!/usr/bin/env python3
"""Email voice: harvest how the user writes sent mail, learn rules, compare over time, pick exemplars.

Run with `python3 -I scripts/voice.py <command>` (stdlib only). Skills: voice-harvest, email-draft.

Privacy split (hard rule):
  vault  ($MSG_VAULT, default ~/msg-vault; never git, never synced)
         voice/samples.jsonl   VoiceSample lines (context, subject, recipient domain, features)
         voice/text/<id>.txt   the user's OWN text (quoted replies stripped), phones/emails/ids redacted
         cursors.json          SyncCursor per source/account
  harness-data ($HARNESS_DATA, default ~/harness-data; private git)
         voice/segment_stats.json, voice/rules.jsonl, voice/profiles.jsonl, voice/harvests.jsonl
         -> features, counts, shares and vs_ ids only. Writes are refused if they carry an address, a phone
            number, a long digit run or a raw-text field (privacy_guard).

Commands
  features       features of one text (JSON): language, greeting/closing, sentences, Korean speech level, ...
  classify       rule-based guess of purpose / audience_kind / register for one text (+ optional context)
  ingest         append VoiceSamples to the vault (idempotent by message id); --from-backfill imports a
                 style_samples.jsonl backfill (message_id, thread_id, date, to_domain, subject, register,
                 language, context, excerpt, excerpt_source)
  update         append a new line for an existing sample: outcome, relabel, draft_pair link
  cursor         read or set the SyncCursor for <source> sent mail of an account
  segment-stats  aggregate features per segment language x register x audience_kind x purpose (+ roll-ups)
  propose-rules  contrast-mine candidate VoiceRules (consistent inside a segment, different outside it)
  rule           change one rule's status (approve / retire) or wording; appends a new version
  profile        build the next VoiceProfile from approved rules + current stats, with a diff vs the previous
  compare        diff two profiles (or a profile vs `current` stats): drift per segment
  nearest        k exemplar samples for a drafting context (same segment first, then features + bigrams)
  check          features of a draft vs the approved rules (and the segment profile) -> deviations
  harvest-log    validate and append one HarvestRun (+ a harvest_run event)
"""
import argparse
import collections
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import statistics
import sys
import uuid

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
HARNESS_ROOT = HERE.parent

AUDIENCE_KINDS = ("client", "recruiter", "employer", "platform-support", "colleague", "friend", "family", "other")
RELATIONSHIPS = ("new", "ongoing", "close", "formal-authority", "unknown")
PURPOSES = ("apply", "follow-up", "inquire", "decline", "accept", "negotiate", "thank", "apologize", "inform",
            "request", "schedule", "complain", "chat", "unknown")
OUTCOMES = ("replied", "positive", "negative", "no-reply", "unknown")
RULE_STATUSES = ("candidate", "proposed", "approved", "retired")
LANGUAGES = ("ko", "en", "mixed")
DIMS = ("language", "register", "audience_kind", "purpose")
# segment levels, most specific first; a missing dim means "any"
LEVELS = (DIMS, ("language", "register", "audience_kind"), ("language", "register", "purpose"),
          ("language", "audience_kind", "purpose"), ("language", "register"), ("language", "audience_kind"),
          ("language", "purpose"))


def _load_module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_style_pairs = None


def style_pairs():
    global _style_pairs
    if _style_pairs is None:
        _style_pairs = _load_module("style_pairs")
    return _style_pairs


def now_utc():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso(t):
    return t.isoformat()


class VoiceError(ValueError):
    pass


# ---------------------------------------------------------------------------------------------- paths / safety
def vault_dir(path=None):
    return pathlib.Path(path or os.environ.get("MSG_VAULT") or pathlib.Path.home() / "msg-vault").expanduser()


def data_dir(path=None):
    return pathlib.Path(path or os.environ.get("HARNESS_DATA") or pathlib.Path.home() / "harness-data").expanduser()


def _inside_git(p):
    p = p.resolve()
    for d in [p, *p.parents]:
        if (d / ".git").exists():
            return d
    return None


def assert_vault_safe(vault, data=None, allow_unsafe=False):
    """The vault must never be inside a git work tree or inside harness-data (which is git-synced)."""
    if allow_unsafe or os.environ.get("VOICE_ALLOW_UNSAFE_VAULT") == "1":
        return
    v = vault.resolve() if vault.exists() else vault.absolute()
    g = _inside_git(v if v.exists() else v.parent if v.parent.exists() else pathlib.Path("/"))
    if g is not None:
        raise VoiceError(f"vault {vault} is inside a git work tree ({g}); raw email must never be committed")
    d = data_dir(data).absolute()
    if v == d or d in v.parents:
        raise VoiceError(f"vault {vault} is inside harness-data ({d}), which is git-synced")


def _mkdir_private(p):
    p.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(p, 0o700)
    except OSError:
        pass


def append_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n")


def read_jsonl(path):
    path = pathlib.Path(path)
    if not path.exists():
        return []
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"warning: skipping malformed line {n} in {path}", file=sys.stderr)
    return out


def latest_by_id(records):
    """Event-sourced stores: the newest line per id wins (file order)."""
    out = {}
    for r in records:
        if isinstance(r, dict) and r.get("id"):
            out[r["id"]] = r
    return out


# ---------------------------------------------------------------------------------------------- privacy
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_RRN_RE = re.compile(r"\b\d{6}-?[1-4]\d{6}\b")
_PHONE_RE = re.compile(r"(?<![\w-])(?:\+\d{1,3}[\s.-]?)?(?:\(?0?\d{1,4}\)?[\s.-])?\d{3,4}[\s.-]\d{4}(?![\w-])")
_LONGNUM_RE = re.compile(r"\b\d{8,}\b")
RAW_TEXT_KEYS = {"text", "excerpt", "body", "subject", "context", "context_summary", "to", "to_domain", "from",
                 "sender", "recipients", "audience_party", "draft", "final", "quote"}


def redact(text):
    t = _EMAIL_RE.sub("[EMAIL]", text or "")
    t = _URL_RE.sub("[URL]", t)
    t = _RRN_RE.sub("[ID]", t)
    t = _PHONE_RE.sub("[PHONE]", t)
    t = _LONGNUM_RE.sub("[NUM]", t)
    return t


def privacy_guard(obj, where="record"):
    """Raise if obj (bound for harness-data) carries raw text fields or identifying strings."""
    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in RAW_TEXT_KEYS and v not in (None, "", [], {}):
                    raise VoiceError(f"{where}: field {path}{k} would put raw/identifying text in harness-data")
                walk(v, f"{path}{k}.")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}{i}.")
        elif isinstance(o, str):
            for rx, what in ((_EMAIL_RE, "an email address"), (_PHONE_RE, "a phone number"),
                             (_LONGNUM_RE, "a long digit run"), (_RRN_RE, "an id number")):
                if rx.search(o):
                    raise VoiceError(f"{where}: {path.rstrip('.') or 'value'} contains {what}")
    walk(obj, "")
    return obj


# ---------------------------------------------------------------------------------------------- own text
_QUOTE_HEADERS = [
    re.compile(r"\n[ \t]*On [^\n]{0,300}(?:\n[^\n]{0,300})?wrote:[ \t]*(?:\n|$)"),
    re.compile(r"\n[ \t]*-{2,}[ \t]*(?:Original Message|Forwarded message|원본 메시지|전달된 메시지)", re.I),
    re.compile(r"\n[ \t]*(?:From|보낸 사람|보낸사람)[ \t]*:[ \t][^\n]*\n[ \t]*(?:Sent|Date|To|보낸 날짜|날짜|받는 사람)[ \t]*:", re.I),
    re.compile(r"\n[^\n]{0,200}님이 작성:[ \t]*(?:\n|$)"),
    re.compile(r"\n_{5,}[ \t]*\n"),
]


def own_text(text):
    """The part the user wrote: cut at the first quoted-reply header, drop '>' lines, trim."""
    t = "\n" + (text or "").replace("\r\n", "\n").replace("\r", "\n")
    cut = len(t)
    for rx in _QUOTE_HEADERS:
        m = rx.search(t)
        if m and m.start() < cut:
            cut = m.start()
    t = t[:cut]
    lines = [ln for ln in t.split("\n") if not ln.lstrip().startswith(">")]
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------------------------- features
_HANGUL_SYL = re.compile(r"[가-힣]")
_LATIN = re.compile(r"[A-Za-z]")
_SENT_SPLIT = re.compile(r"(?<=[.!?。？！])\s+")
_TRAIL = re.compile(r"[\s.!?~…^ㅋㅎㅠㅜ:;)(\-*·•\"'”’“‘,。？！\U0001F300-\U0001FAFF☀-➿]+$")
_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")
_EMOTICON_RE = re.compile(r"\^\^|ㅎㅎ+|ㅋㅋ+|ㅠㅠ+|ㅜㅜ+|:-?\)|:D\b|;-?\)")
_BULLET_RE = re.compile(r"^\s*(?:[-*•·▪◦]|\d+[.)]|[①-⑳]|[가-하][.)])\s+")
_EN_CONTRACTION = re.compile(r"\b(?:[A-Za-z]+n['’]t|[A-Za-z]+['’](?:re|ve|ll|m|d)|(?:it|that|there|here|what|let|he|she|who)['’]s)\b", re.I)
_EN_FORMAL = re.compile(r"\b(?:dear|best regards|kind regards|warm regards|sincerely|yours (?:truly|faithfully)|"
                        r"i am writing|please find attached|i would like to|thank you for your|i look forward to|"
                        r"at your earliest convenience|please do not hesitate)\b", re.I)
_EN_INFORMAL = re.compile(r"\b(?:hey|lol|haha+|btw|gonna|wanna|thx|cheers|yeah|yep|ok so)\b|!!+", re.I)
_HEDGES = re.compile(r"\b(?:i think|i guess|maybe|perhaps|possibly|probably|might|just wanted|i was wondering|"
                     r"if possible|a bit|kind of|sort of|hopefully|i believe)\b|혹시|아마|것 같|듯합니다|듯해요|"
                     r"조금|좀|가능하시다면|괜찮으시다면|괜찮으시면|실례지만", re.I)
_APOLOGY = re.compile(r"\bsorry\b|apolog|\bexcuse me\b|\bmy bad\b|\bforgive\b|죄송|미안|송구|양해|불편을 드려", re.I)
_THANKS = re.compile(r"\bthank|\bthanks\b|\bthx\b|\bappreciate|\bgrateful\b|감사|고맙|고마워", re.I)
_HON_SI = re.compile(r"[가-힣](?:으)?(?:시[는면고며겠었던지길어]|세요|셨|십니|십시|실\b|셔)")
_KO_Q_END = re.compile(r"(?:까요|나요|습니까|ㅂ니까|을까|가요|ㄹ까|는지요|신가요)$")

GREETINGS = [  # (id, regex) checked on the first 3 non-empty lines, first hit wins
    ("ko-hasimnikka", re.compile(r"안녕하십니까")),
    ("ko-haseyo", re.compile(r"안녕하세요")),
    ("ko-sugo", re.compile(r"수고\s?(?:많으십니다|하십니다|많으세요|하세요)")),
    ("ko-annyeong", re.compile(r"^안녕[!~.\s]*$|^하이\b")),
    ("en-dear", re.compile(r"^\s*dear\b", re.I)),
    ("en-hello", re.compile(r"^\s*hello\b", re.I)),
    ("en-hey", re.compile(r"^\s*hey\b", re.I)),
    ("en-hi", re.compile(r"^\s*hi\b", re.I)),
    ("en-good-time", re.compile(r"^\s*good (?:morning|afternoon|evening)\b", re.I)),
]
CLOSINGS = [  # checked on the last 6 non-empty lines, bottom-up; most specific first
    ("ko-gamsadeurimnida", re.compile(r"감사드립니다")),
    ("ko-gamsahamnida", re.compile(r"감사합니다")),
    ("ko-gomapseumnida", re.compile(r"고맙습니다")),
    ("ko-gamsahaeyo", re.compile(r"감사해요|고마워요")),
    ("ko-gomawo", re.compile(r"고마워(?!요)")),
    ("ko-sugohaseyo", re.compile(r"수고하세요|수고하십시오")),
    ("ko-joeun-haru", re.compile(r"좋은 (?:하루|주말|저녁|한 주)")),
    ("en-best-regards", re.compile(r"^\s*best regards\b", re.I)),
    ("en-kind-regards", re.compile(r"^\s*(?:kind|warm|warmest) regards\b", re.I)),
    ("en-regards", re.compile(r"^\s*regards\b", re.I)),
    ("en-sincerely", re.compile(r"^\s*(?:sincerely|yours sincerely|yours truly|yours faithfully)\b", re.I)),
    ("en-best", re.compile(r"^\s*best(?: wishes)?[,!.]?\s*$", re.I)),
    ("en-many-thanks", re.compile(r"^\s*many thanks\b", re.I)),
    ("en-thank-you", re.compile(r"^\s*thank you[,!.]?\s*$", re.I)),
    ("en-thanks", re.compile(r"^\s*(?:thanks|thx)(?: again| so much| a lot)?[,!.]*\s*$", re.I)),
    ("en-cheers", re.compile(r"^\s*cheers\b", re.I)),
    ("en-talk-soon", re.compile(r"^\s*(?:talk soon|speak soon|ttyl|see you)\b", re.I)),
]
_FORMULA_RE = re.compile(r"^(?:\S+\s?님[,.]?\s*)?(?:안녕하세요|안녕하십니까|감사합니다|감사드립니다|고맙습니다|수고하세요|"
                         r"수고하십시오|수고\s?많으십니다|수고\s?많으세요|좋은 (?:하루|주말|저녁|한 주)\s?(?:되세요|보내세요))$")
_KO_SIGNOFF = re.compile(r"(드림|올림)\s*[.!]?\s*$")


def _has_b_batchim(ch):
    o = ord(ch) - 0xAC00
    return 0 <= o < 11172 and o % 28 == 17


def ko_level(sentence):
    """Speech level of one Korean sentence from its final ending, or None."""
    core = _TRAIL.sub("", sentence.strip())
    if not core or not _HANGUL_SYL.match(core[-1]):
        return None
    m = re.search(r"([가-힣]+)$", core)
    w = m.group(1)
    if len(w) < 2:
        return None
    if w.endswith(("습니다", "습니까", "십시오", "십시요", "읍시다", "옵니다")):
        return "hasipsio"
    if w.endswith(("니다", "니까")) and len(w) >= 3 and _has_b_batchim(w[-3]):
        return "hasipsio"
    if w.endswith(("요", "죠")):
        return "haeyo"
    if w.endswith(("음", "함", "임", "됨", "바람", "요망", "필요")):
        return "nominal"
    if w.endswith(("다", "라")):
        return "plain"
    if w.endswith(("어", "아", "야", "해", "지", "자", "냐", "니", "래", "게", "네", "까", "걸", "데", "돼",
                   "봐", "줘", "워", "와", "거든", "잖아", "나", "고마워")):
        return "banmal"
    return None


def _sentences(lines):
    out = []
    for ln in lines:
        for part in _SENT_SPLIT.split(ln.strip()):
            if part.strip():
                out.append(part.strip())
    return out


def detect_language(text):
    h = len(_HANGUL_SYL.findall(text or ""))
    l = len(_LATIN.findall(text or ""))
    if h + l == 0:
        return "en"
    share = h / (h + l * 0.5)
    if share >= 0.75:
        return "ko"
    if share <= 0.15:
        return "en"
    return "mixed"


# non-space characters; Korean packs about 2x the content per character, so it gets its own cuts
LEN_CUTS = {False: (120, 400, 1000), True: (60, 200, 500)}
SENT_CUTS = {False: (30, 60), True: (15, 30)}


def _bucket(v, cuts, names):
    for c, n in zip(cuts, names):
        if v < c:
            return n
    return names[-1]


def features(text, partial=False):
    """VoiceFeatures for one text (counts and enum values only; never text)."""
    text = (text or "").replace("\r\n", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]
    nonempty = [ln.strip() for ln in lines if ln.strip()]
    lang = detect_language(text)

    greeting, greet_idx = "none", set()
    for i, ln in enumerate(nonempty[:3]):
        for gid, rx in GREETINGS:
            if rx.search(ln):
                greeting = gid
                greet_idx.add(i)
                break
        if greeting != "none":
            break
    addressed = False
    for i, ln in enumerate(nonempty[:2]):
        if re.search(r"\S\s?님\s?[,.!께]?\s*$|님께\b", ln) or re.match(r"^\s*(?:dear|hi|hello|hey)\s+\S+", ln, re.I) \
                or re.match(r"^[A-Z][a-z]+(?: [A-Z][a-z]+)?,\s*$", ln):
            addressed = True
            greet_idx.add(i)
            if greeting == "none" and re.match(r"^[A-Z][a-z]+(?: [A-Z][a-z]+)?,\s*$", ln):
                greeting = "en-name-only"
            elif greeting == "none" and "님" in ln:
                greeting = "ko-name-nim"

    closing, close_idx = "none", set()
    tail_start = max(0, len(nonempty) - 6)
    for i in range(len(nonempty) - 1, tail_start - 1, -1) if len(nonempty) >= 2 else ():
        if i in greet_idx:
            continue
        hit = None
        for cid, rx in CLOSINGS:
            m = rx.search(nonempty[i])
            # the line must be (almost) only the closing formula, not a sentence that contains it
            if m and len(nonempty[i].strip()) - len(m.group(0)) <= 6:
                hit = cid
                break
        if hit:
            closing = hit
            close_idx.add(i)
            break
    ko_signoff = "none"
    for i in range(len(nonempty) - 1, tail_start - 1, -1):
        m = _KO_SIGNOFF.search(nonempty[i])
        if m and len(nonempty[i]) <= 30:
            ko_signoff = "deurim" if m.group(1) == "드림" else "ollim"
            close_idx.add(i)
            break

    # signature: 드림/올림, a '--' line, contact info in the tail, or a short line after the closing
    signature = ko_signoff != "none" or any(ln.strip() in ("--", "-- ") for ln in lines)
    tail = "\n".join(nonempty[tail_start:])
    if _PHONE_RE.search(tail) or _EMAIL_RE.search(tail) or "[PHONE]" in tail or "[EMAIL]" in tail:
        signature = True
    if close_idx:
        after = [ln for j, ln in enumerate(nonempty) if j > max(close_idx) and len(ln) <= 40]
        if after:
            signature = True
            close_idx.update(range(max(close_idx) + 1, len(nonempty)))

    # speech level: every sentence except set formulas (안녕하세요 / 감사합니다 are fixed in any register)
    sents = [s for s in _sentences(nonempty) if not _FORMULA_RE.match(_TRAIL.sub("", s))]
    levels = collections.Counter()
    q_ko = 0
    for s in sents:
        lv = ko_level(s)
        if lv:
            levels[lv] += 1
        core = _TRAIL.sub("", s)
        if not s.rstrip().endswith(("?", "？")) and _KO_Q_END.search(core):
            q_ko += 1
    total = sum(levels.values())
    if total == 0:
        ko_speech = "none"
    else:
        top, cnt = levels.most_common(1)[0]
        ko_speech = top if cnt / total >= 0.7 else "mixed"

    chars = len(re.sub(r"\s", "", text))
    body_chars = [len(re.sub(r"\s", "", s)) for s in sents]
    avg = round(sum(body_chars) / len(body_chars), 1) if body_chars else 0.0
    paragraphs = len([b for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]) if text.strip() else 0
    return {
        "language": lang,
        "greeting": greeting,
        "addressed_by_name": addressed,
        "closing": closing,
        "ko_signoff": ko_signoff,
        "chars": chars,
        "words": len(text.split()),
        "sentences": len(sents),
        "paragraphs": paragraphs,
        "avg_sentence_chars": avg,
        "sentence_len_bucket": _bucket(avg, SENT_CUTS[lang == "ko"], ("short", "medium", "long")),
        "length_bucket": _bucket(chars, LEN_CUTS[lang == "ko"], ("xs", "s", "m", "l")),
        "ko_levels": {k: levels.get(k, 0) for k in ("hasipsio", "haeyo", "banmal", "plain", "nominal")},
        "ko_speech_level": ko_speech,
        "honorific_si": len(_HON_SI.findall(text)),
        "honorific_nim": text.count("님"),
        "hedges": len(_HEDGES.findall(text)),
        "apologies": len(_APOLOGY.findall(text)),
        "thanks": len(_THANKS.findall(text)),
        "questions": text.count("?") + text.count("？") + q_ko,
        "exclamations": text.count("!") + text.count("！"),
        "bullets": sum(1 for ln in lines if _BULLET_RE.match(ln)),
        "signature": signature,
        "emoji": len(_EMOJI_RE.findall(text)),
        "emoticons": len(_EMOTICON_RE.findall(text)),
        "en_contractions": len(_EN_CONTRACTION.findall(text)),
        "en_formal": len(_EN_FORMAL.findall(text)),
        "en_informal": len(_EN_INFORMAL.findall(text)),
        "partial": bool(partial),
    }


# Mined (categorical) view of features: what rules and contrasts are computed over.
def mined(f):
    lang = f.get("language")
    out = {
        "greeting": f.get("greeting", "none"),
        "closing": f.get("closing", "none"),
        "addressed_by_name": bool(f.get("addressed_by_name")),
        "length_bucket": f.get("length_bucket"),
        "sentence_len_bucket": f.get("sentence_len_bucket"),
        "has_signature": bool(f.get("signature")),
        "has_hedges": (f.get("hedges") or 0) > 0,
        "has_apology": (f.get("apologies") or 0) > 0,
        "has_thanks": (f.get("thanks") or 0) > 0,
        "has_questions": (f.get("questions") or 0) > 0,
        "has_bullets": (f.get("bullets") or 0) > 0,
        "has_emoji": (f.get("emoji") or 0) + (f.get("emoticons") or 0) > 0,
        "has_exclamations": (f.get("exclamations") or 0) > 0,
    }
    if lang in ("ko", "mixed"):
        out["ko_speech_level"] = f.get("ko_speech_level", "none")
        out["ko_signoff"] = f.get("ko_signoff", "none")
        out["uses_honorific_si"] = (f.get("honorific_si") or 0) > 0
        out["uses_nim"] = (f.get("honorific_nim") or 0) > 0
    if lang in ("en", "mixed"):
        out["uses_contractions"] = (f.get("en_contractions") or 0) > 0
        out["en_formal_markers"] = (f.get("en_formal") or 0) > 0
    if f.get("partial"):  # a truncated snippet: its tail (closing, signature) and length are unknown
        for k in TAIL_FEATURES:
            out.pop(k, None)
    return out


TAIL_FEATURES = ("closing", "has_signature", "ko_signoff", "length_bucket")
# features the rule classifier itself keys on for a purpose: a rule between them would be circular
CIRCULAR = {"thank": {"has_thanks"}, "apologize": {"has_apology"}, "inquire": {"has_questions"}}


NUMERIC = ("chars", "sentences", "avg_sentence_chars", "hedges", "questions", "honorific_si", "en_contractions",
           "bullets", "thanks", "apologies")

_FEATURE_PHRASES = {
    "ko_speech_level": {"hasipsio": "use 하십시오체 endings (-습니다/-십시오)", "haeyo": "use 해요체 endings (-요)",
                        "banmal": "use 반말", "plain": "use plain 해라체 (-다)", "nominal": "use 개조식 nominal endings (-음/-함)",
                        "mixed": "mix speech levels", "none": "use no Korean predicate endings"},
    "ko_signoff": {"deurim": "sign off with '<name> 드림'", "ollim": "sign off with '<name> 올림'", "none": "skip a 드림/올림 sign-off"},
    "greeting": {"none": "open without a greeting line"},
    "closing": {"none": "end without a closing formula"},
}
_BOOL_PHRASES = {
    "addressed_by_name": ("address the reader by name in the first line", "don't open with the reader's name"),
    "has_signature": ("end with a signature block", "send without a signature block"),
    "has_hedges": ("soften with hedges (혹시/maybe/I was wondering)", "write without hedges"),
    "has_apology": ("include an apology marker", "don't apologize"),
    "has_thanks": ("include a thanks", "don't add a thanks line"),
    "has_questions": ("ask at least one explicit question", "make no explicit questions"),
    "has_bullets": ("use bullets or numbered points", "write in prose, no bullets"),
    "has_emoji": ("use emoji/emoticons (^^, ㅎㅎ, :))", "use no emoji or emoticons"),
    "has_exclamations": ("use exclamation marks", "use no exclamation marks"),
    "uses_honorific_si": ("use subject honorific -시-", "don't use -시- honorifics"),
    "uses_nim": ("use 님", "don't use 님"),
    "uses_contractions": ("use contractions (I'm, don't)", "avoid contractions"),
    "en_formal_markers": ("use formal set phrases (Dear, Best regards, I would like to)", "avoid formal set phrases"),
}


def rule_phrase(feature, value):
    if feature in _BOOL_PHRASES:
        return _BOOL_PHRASES[feature][0 if value else 1]
    special = _FEATURE_PHRASES.get(feature, {}).get(value)
    if special:
        return special
    if feature == "greeting":
        return f"open with the '{value}' greeting"
    if feature == "closing":
        return f"close with the '{value}' formula"
    if feature == "length_bucket":
        return f"keep the length in the '{value}' bucket"
    if feature == "sentence_len_bucket":
        return f"keep sentences {value} on average"
    return f"{feature} = {value}"


_LANG_NAMES = {"ko": "Korean", "en": "English", "mixed": "mixed-language"}


def scope_label(scope):
    if not any(scope.get(d) for d in DIMS):
        return "all"
    out = _LANG_NAMES.get(scope.get("language"), scope.get("language") or "any-language") + " email"
    quals = [f"{label} {scope[d]}" for d, label in (("register", "register"), ("audience_kind", "to"),
                                                   ("purpose", "purpose")) if scope.get(d)]
    return out + (f" [{', '.join(quals)}]" if quals else "")


# ---------------------------------------------------------------------------------------------- classify
_PURPOSE_CUES = {
    "apply": r"\bapply|application|applying|\bresume\b|\bcv\b|cover letter|portfolio|지원(?:합니다|드립니다|서|하고)|이력서|포트폴리오",
    "follow-up": r"follow(?:ing)?[- ]up|checking in|any update|just wanted to check|circle back|후속|진행 상황|회신 부탁|확인차|혹시 검토",
    "schedule": r"\bavailab|\bschedule|\bmeeting\b|\bcall\b|time slot|calendar|일정|미팅|통화|가능한 시간|시간 괜찮|날짜",
    "negotiate": r"\brates?\b|per word|\bbudget\b|\bprice\b|\bquote\b|\bfee\b|\bcounter\b|단가|견적|요율|금액|비용",
    "decline": r"unfortunately|\bdecline|unable to|not be able|pass on this|won't be able|어렵습니다|어려울 것 같|정중히|고사|사양",
    "accept": r"happy to accept|i accept|accept the|glad to take|i'?d be happy to|수락|기꺼이|함께하겠습니다",
    "apologize": r"\bsorry\b|apolog|죄송|사과드|양해",
    "thank": r"thank you for|thanks for|감사드립니다|감사합니다|고맙습니다",
    "complain": r"\bcomplain|disappointed|issue with|not (?:yet )?received|still haven'?t|불만|항의|아직 (?:받지|입금)|미지급",
    "inquire": r"i was wondering|could you (?:let me know|tell me)|\binquir|\bquestion\b|문의|궁금|여쭤",
    "request": r"could you|would you|please send|please (?:review|confirm|check)|부탁드립니다|요청드|해 주시",
    "inform": r"\bfyi\b|please find attached|\battached\b|sharing|let you know|공유드|첨부|알려드|안내드",
    "chat": r"ㅋㅋ|ㅎㅎ|\blol\b|haha|how are you|잘 지내",
}
_PURPOSE_WEIGHT = {"apply": 3, "follow-up": 3, "decline": 3, "accept": 3, "negotiate": 2.5, "schedule": 2,
                   "complain": 2.5, "inquire": 1.5, "request": 1.2, "inform": 1.2, "apologize": 1, "thank": 0.6,
                   "chat": 1.5}
_AUDIENCE_CUES = {
    "recruiter": r"recruit|talent|\bhr\b|hiring|greenhouse|lever\.co|workday|ashby|채용|인사담당|헤드헌",
    "platform-support": r"support|helpdesk|help center|zendesk|freshdesk|ticket|고객센터|고객지원|문의센터|noreply|no-reply",
    "client": r"\bclient|\bproject\b|translation|localization|\bagency\b|\bpm\b|deliver|납품|번역|의뢰|클라이언트|프로젝트",
    "employer": r"\bemployer|\bmanager\b|\bboss\b|\bteam lead|onboarding|contract(?:or)? agreement|상사|팀장|대표님",
    "colleague": r"colleague|coworker|teammate|동료|같은 팀",
    "family": r"\bmom\b|\bdad\b|family|엄마|아빠|가족|언니|오빠|누나|형\b",
    "friend": r"\bfriend|친구|buddy",
}


def classify(text="", context="", subject="", to_domain=""):
    hay = " ".join(filter(None, [subject, context, text])).lower()
    scores = {}
    for p, rx in _PURPOSE_CUES.items():
        hits = len(re.findall(rx, hay, re.I))
        if hits:
            scores[p] = hits * _PURPOSE_WEIGHT[p]
    f = features(text)
    if f["questions"] and "inquire" not in scores and not scores:
        scores["inquire"] = 1
    purpose = max(scores, key=lambda k: (scores[k], -PURPOSES.index(k))) if scores else "unknown"
    ranked = sorted(scores.values(), reverse=True)
    pconf = "medium" if ranked and (len(ranked) == 1 or ranked[0] >= 2 * ranked[1]) else "low"
    ahay = " ".join(filter(None, [to_domain, context, subject])).lower()
    aud = "other"
    for k, rx in _AUDIENCE_CUES.items():
        if re.search(rx, ahay, re.I):
            aud = k
            break
    if aud == "other" and f["emoticons"] and not to_domain:
        aud = "friend"
    return {"purpose": purpose, "purpose_scores": scores, "purpose_confidence": pconf if purpose != "unknown" else "low",
            "audience_kind": aud, "audience_confidence": "low" if aud == "other" else "medium",
            "register": infer_register(f), "language": f["language"]}


def infer_register(f):
    lv = f.get("ko_speech_level")
    if f.get("language") in ("ko", "mixed") and lv not in (None, "none", "mixed"):
        if lv == "hasipsio":
            return "formal-email"
        if lv == "banmal":
            return "chat"
        if lv == "haeyo":
            return "friendly" if (f.get("emoticons") or f.get("emoji")) else "office"
        return "office"
    if (f.get("emoji") or 0) + (f.get("en_informal") or 0) >= 2:
        return "chat"
    if f.get("en_formal") and not f.get("en_contractions"):
        return "formal-email"
    if f.get("greeting") in ("en-hey",) or f.get("emoticons"):
        return "friendly"
    return "office"


# ---------------------------------------------------------------------------------------------- samples
def _registers():
    return style_pairs().load_registers()


def sample_id(source, message):
    return "vs_" + hashlib.sha256(f"{source}:{message}".encode()).hexdigest()[:12]


def _prefixed(value, prefix):
    if value in (None, ""):
        return None
    v = str(value).strip()
    return v if v.startswith(prefix) else prefix + v


def _norm_ts(value):
    if not value:
        return iso(now_utc())
    s = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s + "T00:00:00+00:00"
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        raise VoiceError(f"ts {value!r} is not ISO 8601")
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return iso(t)


def _enum(rec, field, allowed, default=None):
    v = rec.get(field)
    if v in (None, ""):
        return default
    v = str(v).strip().lower()
    if v not in allowed:
        raise VoiceError(f"{field} {rec.get(field)!r} not one of {', '.join(allowed)}")
    return v


def samples_file(vault):
    return vault / "voice" / "samples.jsonl"


def load_samples(vault=None, include_mixed=True):
    recs = latest_by_id(read_jsonl(samples_file(vault_dir(vault))))
    out = list(recs.values())
    if not include_mixed:
        out = [r for r in out if r.get("authorship") == "user"]
    return out


def _link_pair(sample_text, thread, pairs):
    """A StylePair from email-draft whose derived_from is this thread and whose final matches the sent text."""
    if not thread:
        return None
    sp = style_pairs()
    best, best_sim = None, 0.0
    for p in pairs:
        df = p.get("derived_from")
        dfs = df if isinstance(df, list) else [df]
        if thread not in dfs:
            continue
        sim = sp.similarity(sample_text, p.get("final", ""))
        if sim > best_sim:
            best, best_sim = p, sim
    return best["id"] if best and best_sim >= 0.4 else None  # thread match + similar text (names may be <name>)


def build_sample(rec, registers, origin="harvest", pairs=None):
    """Validate one input record and return (VoiceSample, own_text_redacted)."""
    source = _enum(rec, "source", ("gmail", "viber", "lark", "slack", "proz", "linkedin", "glassdoor", "imessage",
                                   "telegram", "other"), "gmail")
    raw_msg = rec.get("message") or rec.get("message_id")
    if not raw_msg:
        raise VoiceError("'message' (the provider message id) is required")
    message = _prefixed(raw_msg, "msg_")
    account = rec.get("account")
    if not account or not str(account).startswith("acct_"):
        raise VoiceError(f"account {account!r} must be an Account id (acct_...)")
    text = own_text(rec.get("text") or rec.get("excerpt") or "")
    if not text:
        raise VoiceError(f"{message}: empty text after stripping quoted replies")
    partial = (rec.get("text_source") or rec.get("excerpt_source")) == "snippet"
    feats = features(text, partial=partial)
    hint = classify(text, rec.get("context_summary") or rec.get("context") or "", rec.get("subject") or "",
                    rec.get("to_domain") or "")
    language = _enum(rec, "language", LANGUAGES, feats["language"])
    register = style_pairs().norm_register(rec.get("register") or hint["register"])
    if register not in registers:
        raise VoiceError(f"register {rec.get('register')!r} not in ontology list: {', '.join(registers)}")
    classified_by = rec.get("classified_by") or ("model" if rec.get("purpose") and origin == "harvest" else "rule")
    out = {
        "id": sample_id(source, message),
        "ts": _norm_ts(rec.get("ts") or rec.get("date")),
        "ingested_at": iso(now_utc()),
        "source": source,
        "account": account,
        "thread": _prefixed(rec.get("thread") or rec.get("thread_id"), "thr_"),
        "message": message,
        "direction": "sent",
        "language": language,
        "register": register,
        "audience_kind": _enum(rec, "audience_kind", AUDIENCE_KINDS, hint["audience_kind"]),
        "relationship": _enum(rec, "relationship", RELATIONSHIPS, "unknown"),
        "purpose": _enum(rec, "purpose", PURPOSES, hint["purpose"]),
        "features": feats,
        "outcome": _enum(rec, "outcome", OUTCOMES, "unknown"),
        "authorship": "user",
        "text_source": "snippet" if partial else "body",
        "origin": origin,
        "classified_by": classified_by if classified_by in ("rule", "model", "user") else "rule",
        "confidence": _enum(rec, "confidence", ("high", "medium", "low"),
                            "medium" if classified_by != "rule" else hint["purpose_confidence"]),
    }
    for f in ("audience_party", "context_summary", "subject", "to_domain", "notes", "harvest"):
        if rec.get(f) not in (None, ""):
            out[f] = rec[f]
    if rec.get("to") and not out.get("to_domain"):
        m = re.search(r"@([\w.-]+)", str(rec["to"]))
        if m:
            out["to_domain"] = m.group(1).lower()
    if rec.get("outcome_after_days") not in (None, ""):
        out["outcome_after_days"] = int(rec["outcome_after_days"])
    dp = rec.get("draft_pair") or (_link_pair(text, out["thread"], pairs) if pairs else None)
    if dp:
        out["draft_pair"] = dp
        out["authorship"] = "mixed"
    out["text_ref"] = f"voice/text/{out['id']}.txt"
    return out, redact(text)


def ingest(records, vault=None, origin="harvest", pairs_file=None, data=None, allow_unsafe=False, harvest=None):
    v = vault_dir(vault)
    assert_vault_safe(v, data, allow_unsafe)
    _mkdir_private(v)
    _mkdir_private(v / "voice")
    _mkdir_private(v / "voice" / "text")
    existing = latest_by_id(read_jsonl(samples_file(v)))
    regs = _registers()
    pairs = style_pairs().load(pairs_file) if pairs_file is not False else []
    added, skipped, errors = [], [], []
    for i, rec in enumerate(records, 1):
        try:
            if harvest and not rec.get("harvest"):
                rec = dict(rec, harvest=harvest)
            s, txt = build_sample(rec, regs, origin, pairs)
        except VoiceError as e:
            errors.append(f"record {i}: {e}")
            continue
        if s["id"] in existing or any(a["id"] == s["id"] for a in added):
            skipped.append(s["id"])
            continue
        tp = v / s["text_ref"]
        tp.write_text(txt, encoding="utf-8")
        try:
            os.chmod(tp, 0o600)
        except OSError:
            pass
        added.append(s)
    append_jsonl(samples_file(v), added)
    return {"added": [a["id"] for a in added], "skipped_dup": skipped, "errors": errors}


BACKFILL_CAP = 500  # backfill excerpts were cut near 600 chars: treat long ones as truncated (partial)


def from_backfill(path, account):
    """Map a style_samples.jsonl backfill (StyleSample shape) to ingest records (best effort).
    message_id/thread_id -> message/thread, date -> ts, context -> context_summary, excerpt -> text,
    excerpt_source snippet (or an excerpt >= BACKFILL_CAP chars) -> text_source snippet (features partial)."""
    out = []
    for r in read_jsonl(path):
        src = r.get("excerpt_source") or "body"
        if len(r.get("excerpt") or "") >= BACKFILL_CAP:
            src = "snippet"
        out.append({
            "source": "gmail", "account": account,
            "message": r.get("message_id"), "thread": r.get("thread_id"),
            "ts": r.get("date"), "to_domain": r.get("to_domain"), "subject": r.get("subject"),
            "register": r.get("register"), "language": r.get("language"),
            "context_summary": r.get("context"), "text": r.get("excerpt"),
            "text_source": src,
            "classified_by": "rule", "notes": "imported from style_samples backfill",
        })
    return out


def update(vault, message, changes, source="gmail", allow_unsafe=False, data=None):
    v = vault_dir(vault)
    assert_vault_safe(v, data, allow_unsafe)
    sid = message if str(message).startswith("vs_") else sample_id(source, _prefixed(message, "msg_"))
    cur = latest_by_id(read_jsonl(samples_file(v))).get(sid)
    if cur is None:
        raise VoiceError(f"no sample for {message} ({sid})")
    new = dict(cur)
    if "outcome" in changes:
        new["outcome"] = _enum(changes, "outcome", OUTCOMES)
    if changes.get("outcome_after_days") is not None:
        new["outcome_after_days"] = int(changes["outcome_after_days"])
    for f, allowed in (("purpose", PURPOSES), ("audience_kind", AUDIENCE_KINDS), ("relationship", RELATIONSHIPS)):
        if changes.get(f):
            new[f] = _enum(changes, f, allowed)
            new["classified_by"] = "user"
            new["confidence"] = "high"
    if changes.get("register"):
        reg = style_pairs().norm_register(changes["register"])
        if reg not in _registers():
            raise VoiceError(f"register {changes['register']!r} not in ontology list")
        new["register"], new["classified_by"], new["confidence"] = reg, "user", "high"
    if changes.get("draft_pair"):
        if not str(changes["draft_pair"]).startswith("sp_"):
            raise VoiceError("draft_pair must be a StylePair id (sp_...)")
        new["draft_pair"], new["authorship"] = changes["draft_pair"], "mixed"
    if changes.get("audience_party"):
        new["audience_party"] = changes["audience_party"]
    new["ingested_at"] = iso(now_utc())
    append_jsonl(samples_file(v), [new])
    return new


# ---------------------------------------------------------------------------------------------- cursor
def cursor(vault, account, source="gmail", set_ts=None, last_id=None, allow_unsafe=False, data=None):
    v = vault_dir(vault)
    assert_vault_safe(v, data, allow_unsafe)
    p = v / "cursors.json"
    doc = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    curs = doc.setdefault("cursors", {})
    cid = f"cur_{source}_sent_{str(account).removeprefix('acct_')}"
    if set_ts:
        _mkdir_private(v)
        curs[cid] = {"id": cid, "source": source, "account": account, "last_ts": _norm_ts(set_ts),
                     "last_id": last_id, "updated": iso(now_utc())}
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, p)
    return curs.get(cid) or {"id": cid, "source": source, "account": account, "last_ts": None}


# ---------------------------------------------------------------------------------------------- stats
def seg_key(scope):
    return "|".join(scope.get(d) or "*" for d in DIMS)


def key_scope(key):
    return {d: (None if v == "*" else v) for d, v in zip(DIMS, key.split("|"))}


def _share(counter, n):
    return {str(k): round(v / n, 3) for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))}


def _jsonable(v):
    return "true" if v is True else "false" if v is False else str(v)


def segment_stats(samples, min_n=1):
    groups = collections.defaultdict(list)
    for s in samples:
        for level in LEVELS:
            scope = {d: s.get(d) for d in level}
            groups[seg_key(scope)].append(s)
    segs = {}
    for key, members in sorted(groups.items()):
        if len(members) < min_n:
            continue
        n = len(members)
        cats = collections.defaultdict(collections.Counter)
        for s in members:
            for f, val in mined(s.get("features") or {}).items():
                cats[f][_jsonable(val)] += 1
        nums = {}
        for f in NUMERIC:
            vals = [float((s.get("features") or {}).get(f) or 0) for s in members]
            nums[f] = {"mean": round(statistics.fmean(vals), 2), "median": round(statistics.median(vals), 2)}
        outc = collections.Counter(s.get("outcome") or "unknown" for s in members)
        known = n - outc.get("unknown", 0)
        replied = outc.get("replied", 0) + outc.get("positive", 0) + outc.get("negative", 0)
        segs[key] = {
            "scope": key_scope(key), "n": n,
            "samples": sorted(s["id"] for s in members),
            "features": {f: _share(c, n) for f, c in sorted(cats.items())},
            "numeric": nums,
            "outcomes": dict(outc),
            "reply_rate": round(replied / known, 3) if known else None,
            "positive_rate": round(outc.get("positive", 0) / known, 3) if known else None,
        }
    return {"generated": iso(now_utc()), "n_samples": len(samples), "segments": segs}


def write_stats(stats, data=None):
    privacy_guard(stats, "segment_stats")
    p = data_dir(data) / "voice" / "segment_stats.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(stats, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------------------------- rules
def rules_file(data=None):
    return data_dir(data) / "voice" / "rules.jsonl"


def load_rules(data=None):
    return latest_by_id(read_jsonl(rules_file(data)))


def rule_id(scope, feature, value):
    key = json.dumps([seg_key(scope), feature, _jsonable(value)], ensure_ascii=False)
    return "vr_" + hashlib.sha256(key.encode()).hexdigest()[:10]


def _parse_val(s):
    return True if s == "true" else False if s == "false" else s


def propose_rules(samples, min_n=5, min_share=0.8, min_contrast=0.25, min_pool=3, existing=None):
    """Contrast mining: a feature value shared by >= min_share of a segment (n >= min_n) whose share among
    the other samples of the same language is at least min_contrast lower."""
    existing = existing or {}
    stats = segment_stats(samples)["segments"]
    by_lang = collections.defaultdict(list)
    feats_of = {s["id"]: mined(s.get("features") or {}) for s in samples}
    for s in samples:
        by_lang[s.get("language")].append(s)
    cands = []
    for key, seg in stats.items():
        scope = seg["scope"]
        if all(scope.get(d) is None for d in DIMS[1:]) or seg["n"] < min_n:
            continue  # language-only segments have nothing of the same language to contrast with
        if scope.get("purpose") == "unknown" or scope.get("audience_kind") == "other":
            continue  # a rule for "unclassified mail" is not actionable; classify those samples instead
        members = set(seg["samples"])
        pool = [s for s in by_lang[scope["language"]] if s["id"] not in members]
        if len(pool) < min_pool:
            continue
        for feat, dist in seg["features"].items():
            if feat in CIRCULAR.get(scope.get("purpose"), ()):
                continue
            has = [m for m in members if feat in feats_of[m]]  # partial snippets lack tail features
            if len(has) < min_n:
                continue
            top_val = next(iter(dist))
            ev = sorted(m for m in has if _jsonable(feats_of[m][feat]) == top_val)
            share = round(len(ev) / len(has), 3)
            if share < min_share:
                continue
            val = _parse_val(top_val)
            pool_has = [x for x in pool if feat in feats_of[x["id"]]]
            if len(pool_has) < min_pool:
                continue
            other = sum(1 for x in pool_has if _jsonable(feats_of[x["id"]][feat]) == top_val) / len(pool_has)
            contrast = round(share - other, 3)
            if contrast < min_contrast:
                continue
            counter = sorted(set(has) - set(ev))
            n = len(has)
            if n >= 10 and share >= 0.9 and contrast >= 0.4:
                conf = "high"
            elif n >= max(min_n, 5) and contrast >= 0.35:
                conf = "medium"
            else:
                conf = "low"
            cands.append({"scope": scope, "feature": feat, "value": val, "n": n, "support": share,
                          "contrast": contrast, "evidence": ev, "counterexamples": counter, "confidence": conf})
    # One rule per (feature, value) and population: drop a candidate when a kept one with the same feature/value
    # has a more general scope that covers it, or (nearly) the same evidence (register/audience/purpose often
    # coincide). Fewer dims first; at equal dims the LEVELS order prefers register, then audience, then purpose.
    def level_rank(c):
        dims = tuple(d for d in DIMS if c["scope"].get(d))
        return LEVELS.index(dims) if dims in LEVELS else len(LEVELS)

    cands.sort(key=lambda c: (sum(1 for d in DIMS if c["scope"].get(d)), level_rank(c), -c["support"]))
    kept = []
    for c in cands:
        ev = set(c["evidence"])
        covered = False
        for k in kept:
            if k["feature"] != c["feature"] or k["value"] != c["value"]:
                continue
            general = all(c["scope"].get(d) == k["scope"].get(d) for d in DIMS if k["scope"].get(d))
            kev = set(k["evidence"])
            if general or len(ev & kev) / max(len(ev | kev), 1) >= 0.9:
                covered = True
                break
        if not covered:
            kept.append(c)
    now = iso(now_utc())
    out, weakened = [], []
    for c in kept:
        rid = rule_id(c["scope"], c["feature"], c["value"])
        prev = existing.get(rid)
        stmt = f"In {scope_label(c['scope'])}: {rule_phrase(c['feature'], c['value'])}"
        rec = {"id": rid, "ts": now, "statement": stmt, "feature": c["feature"], "value": c["value"],
               "scope": {d: c["scope"].get(d) for d in DIMS}, "evidence": c["evidence"][:50],
               "counterexamples": c["counterexamples"][:50], "n": c["n"], "support": c["support"],
               "contrast": c["contrast"], "confidence": c["confidence"],
               "status": "proposed" if c["confidence"] != "low" else "candidate", "version": 1}
        if prev:
            if prev.get("n") == rec["n"] and prev.get("support") == rec["support"]:
                continue  # nothing new
            rec["version"] = int(prev.get("version") or 1) + 1
            if prev.get("status") not in ("candidate", None):
                rec["status"] = prev["status"]  # proposed stays proposed; approved/retired are my decisions
            if prev.get("statement") and prev.get("status") == "approved":
                rec["statement"] = prev["statement"]  # keep the wording I approved
            for f in ("approved_on", "notes"):
                if prev.get(f):
                    rec[f] = prev[f]
        out.append(rec)
    # approved rules whose segment no longer supports them -> shown to me, never auto-retired
    for rid, r in existing.items():
        if r.get("status") != "approved":
            continue
        seg = stats.get(seg_key(r.get("scope") or {}))
        if not seg:
            continue
        share = seg["features"].get(r["feature"], {}).get(_jsonable(r.get("value")), 0.0)
        if share < 0.6:
            weakened.append({"id": rid, "statement": r.get("statement"), "support_now": share, "n_now": seg["n"]})
    return {"rules": out, "weakened": weakened}


def _schema_validate(type_name, recs):
    sc = _load_module("schema_check")
    onto = sc.Ontology.load()
    rep = sc.Report()
    sc.validate_records(type_name, [(f"[{i}]", r) for i, r in enumerate(recs)], onto, rep, where="")
    if rep.errors:
        raise VoiceError("; ".join(rep.errors))


def append_event(data, etype, items, pointers, content="", extra=None):
    now = now_utc()
    ev = {"id": f"evt_{now:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}", "ts": iso(now), "actor": "agent:voice",
          "type": etype, "scope": "global", "intent": None, "meta": None, "items": items, "pointers": pointers,
          "content": content}
    ev.update(extra or {})
    privacy_guard(ev, f"{etype} event")
    append_jsonl(data_dir(data) / "log" / f"{now:%Y-%m}.jsonl", [ev])
    return ev


def write_rules(rules, data=None, harvest=None):
    for r in rules:
        if harvest:
            r["harvest"] = harvest
        if r.get("confidence") == "low" and r.get("status") == "proposed":
            r["status"] = "candidate"
    privacy_guard(rules, "VoiceRule")
    _schema_validate("VoiceRule", rules)
    append_jsonl(rules_file(data), rules)
    shown = [r for r in rules if r["status"] == "proposed"]
    if shown:
        append_event(data, "voice_rule_proposed", [r["id"] for r in shown], ["voice/rules.jsonl"],
                     "\n".join(r["statement"] for r in shown))
    return rules


def set_rule(data, rid, status=None, statement=None, note=None):
    cur = load_rules(data).get(rid)
    if cur is None:
        raise VoiceError(f"no rule {rid}")
    new = dict(cur, ts=iso(now_utc()), version=int(cur.get("version") or 1) + 1)
    if status:
        if status not in RULE_STATUSES:
            raise VoiceError(f"status {status!r} not one of {', '.join(RULE_STATUSES)}")
        new["status"] = status
        if status == "approved":
            new["approved_on"] = dt.date.today().isoformat()
    if statement:
        new["statement"] = statement
    if note:
        new["notes"] = note
    privacy_guard(new, "VoiceRule")
    _schema_validate("VoiceRule", [new])
    append_jsonl(rules_file(data), [new])
    return new


# ---------------------------------------------------------------------------------------------- profiles
def profiles_file(data=None):
    return data_dir(data) / "voice" / "profiles.jsonl"


def load_profiles(data=None):
    return read_jsonl(profiles_file(data))


def _slim_segments(stats):
    return {k: {"n": v["n"], "features": v["features"], "numeric": v["numeric"], "reply_rate": v["reply_rate"],
                "positive_rate": v["positive_rate"]} for k, v in stats["segments"].items()}


def compare(a, b, share_delta=0.2, numeric_delta=0.25):
    """Drift from profile-like a to b ({segments, rules})."""
    sa, sb = a.get("segments") or {}, b.get("segments") or {}
    segs, summary = {}, []
    for key in sorted(set(sa) | set(sb)):
        if key not in sa:
            segs[key] = {"added": True, "n": sb[key]["n"]}
            continue
        if key not in sb:
            segs[key] = {"removed": True, "n": sa[key]["n"]}
            continue
        x, y = sa[key], sb[key]
        d = {"n": [x["n"], y["n"]], "dominant_changed": {}, "share_shifts": {}, "numeric_shifts": {}}
        for f in sorted(set(x["features"]) | set(y["features"])):
            fx, fy = x["features"].get(f, {}), y["features"].get(f, {})
            dx = next(iter(fx), None)
            dy = next(iter(fy), None)
            if dx and dy and dx != dy:
                d["dominant_changed"][f] = [dx, dy]
            for val in set(fx) | set(fy):
                delta = round(fy.get(val, 0) - fx.get(val, 0), 3)
                if abs(delta) >= share_delta:
                    d["share_shifts"][f"{f}={val}"] = delta
        for f in NUMERIC:
            mx = (x.get("numeric") or {}).get(f, {}).get("mean")
            my = (y.get("numeric") or {}).get(f, {}).get("mean")
            if mx is None or my is None:
                continue
            base = max(abs(mx), 1.0)
            if abs(my - mx) / base >= numeric_delta:
                d["numeric_shifts"][f] = [mx, my]
        if d["dominant_changed"] or d["share_shifts"] or d["numeric_shifts"]:
            segs[key] = d
            if d["dominant_changed"]:
                summary.append(f"{key}: " + ", ".join(f"{f} {v[0]}->{v[1]}" for f, v in d["dominant_changed"].items()))
    ra = {r["id"] if isinstance(r, dict) else r for r in a.get("rules") or []}
    rb = {r["id"] if isinstance(r, dict) else r for r in b.get("rules") or []}
    added_segs = sum(1 for v in segs.values() if v.get("added"))
    if added_segs:
        summary.append(f"{added_segs} new segment(s)")
    if rb - ra or ra - rb:
        summary.append(f"rules +{len(rb - ra)} -{len(ra - rb)}")
    return {"from_profile": a.get("id", "current"), "to_profile": b.get("id", "current"), "segments": segs,
            "rules_added": sorted(rb - ra), "rules_removed": sorted(ra - rb),
            "summary": summary or ["no drift above thresholds"]}


def build_profile(samples, data=None, harvest=None, notes=None):
    profs = load_profiles(data)
    prev = profs[-1] if profs else None
    stats = segment_stats(samples)
    approved = [r for r in load_rules(data).values() if r.get("status") == "approved"]
    version = int(prev["version"]) + 1 if prev else 1
    prof = {"id": f"vp_{version:04d}", "ts": iso(now_utc()), "version": version, "n_samples": len(samples),
            "segments": _slim_segments(stats),
            "rules": sorted(r["id"] for r in approved),
            "rule_details": [{"id": r["id"], "statement": r["statement"], "feature": r["feature"], "value": r.get("value"),
                              "scope": r["scope"], "support": r["support"]} for r in sorted(approved, key=lambda r: r["id"])]}
    if harvest:
        prof["generated_from"] = harvest
    if prev:
        prof["previous"] = prev["id"]
        prof["diff_from_previous"] = compare(prev, prof)
    if notes:
        prof["notes"] = notes
    privacy_guard(prof, "VoiceProfile")
    _schema_validate("VoiceProfile", [prof])
    append_jsonl(profiles_file(data), [prof])
    return prof


def resolve_profile(ref, data=None, samples=None):
    if ref == "current":
        st = segment_stats(samples or [])
        approved = [r["id"] for r in load_rules(data).values() if r.get("status") == "approved"]
        return {"id": "current", "segments": _slim_segments(st), "rules": approved}
    profs = load_profiles(data)
    if not profs:
        raise VoiceError("no profiles yet (run `voice.py profile`)")
    if ref in (None, "latest"):
        return profs[-1]
    if ref == "previous":
        if len(profs) < 2:
            raise VoiceError("only one profile exists")
        return profs[-2]
    for p in profs:
        if p["id"] == ref:
            return p
    raise VoiceError(f"no profile {ref}")


# ---------------------------------------------------------------------------------------------- nearest / check
def _segment_score(s, ctx):
    w = {"language": 4, "register": 3, "audience_kind": 2, "purpose": 2, "relationship": 1}
    return sum(wt for d, wt in w.items() if ctx.get(d) and s.get(d) == ctx[d])


def _feat_sim(fa, fb):
    ma, mb = mined(fa), mined(fb)
    keys = set(ma) & set(mb)
    return sum(1 for k in keys if ma[k] == mb[k]) / len(keys) if keys else 0.0


def nearest(samples, ctx, text=None, k=5, vault=None, with_text=True):
    v = vault_dir(vault)
    sp = style_pairs()
    qf = features(text) if text else None
    outcome_bonus = {"positive": 1.0, "replied": 0.8, "unknown": 0.5, "no-reply": 0.2, "negative": 0.1}

    def text_of(s):
        p = v / (s.get("text_ref") or "")
        return p.read_text(encoding="utf-8") if s.get("text_ref") and p.exists() else ""

    scored = []
    for s in samples:
        if ctx.get("language") and s.get("language") != ctx["language"] and ctx["language"] != "mixed":
            continue  # never use an exemplar in the other language
        body = text_of(s) if (text or with_text) else ""
        fs = _feat_sim(qf, s.get("features") or {}) if qf else 0.0
        ts = sp.similarity(text, body) if text else 0.0
        combined = round(0.5 * fs + 0.5 * ts + 0.1 * outcome_bonus.get(s.get("outcome") or "unknown", 0.5), 4)
        key = (_segment_score(s, ctx), int(s.get("authorship") == "user"), combined, s.get("ts", ""))
        scored.append((key, s, body))
    scored.sort(key=lambda t: t[0], reverse=True)
    out = []
    for key, s, body in scored[:max(k, 0)]:
        r = {"id": s["id"], "segment": seg_key(s), "relationship": s.get("relationship"), "outcome": s.get("outcome"),
             "authorship": s.get("authorship"), "_score": list(key[:3])}
        if with_text:
            r["text"] = body
        out.append(r)
    return out


def rules_for(ctx, data=None, include_proposed=False):
    ok = ("approved", "proposed") if include_proposed else ("approved",)
    out = []
    for r in load_rules(data).values():
        if r.get("status") not in ok:
            continue
        sc = r.get("scope") or {}
        if all(not sc.get(d) or sc.get(d) == ctx.get(d) for d in DIMS):
            out.append(r)
    return sorted(out, key=lambda r: (r.get("status") != "approved", r["id"]))


def check(text, ctx, data=None, include_proposed=False, profile=None):
    f = features(text)
    m = mined(f)
    viol, ok = [], []
    for r in rules_for(ctx, data, include_proposed):
        got = m.get(r["feature"])
        if got is None:
            continue
        item = {"rule": r["id"], "status": r["status"], "statement": r["statement"], "expected": r.get("value"), "got": got}
        (ok if got == r.get("value") else viol).append(item)
    soft = []
    if profile:
        seg = (profile.get("segments") or {}).get(seg_key(ctx))
        if seg and seg["n"] >= 3:
            for feat, dist in seg["features"].items():
                top, share = next(iter(dist.items()))
                if share >= 0.7 and feat in m and _jsonable(m[feat]) != top:
                    soft.append({"feature": feat, "profile_value": top, "profile_share": share, "got": _jsonable(m[feat]),
                                 "segment_n": seg["n"]})
    return {"features": f, "segment": seg_key(ctx), "rules_checked": len(viol) + len(ok), "violations": viol,
            "passed": ok, "profile_deviations": soft}


# ---------------------------------------------------------------------------------------------- harvest log
def harvest_log(rec, data=None):
    now = now_utc()
    rec = dict(rec)
    rec.setdefault("id", f"hr_{now:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}")
    rec.setdefault("ts", iso(now))
    rec.setdefault("source", "gmail")
    for f in ("cursor_from", "cursor_to"):
        if rec.get(f):
            rec[f] = _norm_ts(rec[f])
    privacy_guard(rec, "HarvestRun")
    _schema_validate("HarvestRun", [rec])
    append_jsonl(data_dir(data) / "voice" / "harvests.jsonl", [rec])
    counts = rec.get("counts") or {}
    cost = rec.get("cost") or {}
    append_event(data, "harvest_run", [rec["id"]], ["voice/harvests.jsonl"],
                 ", ".join(f"{k}={v}" for k, v in counts.items()),
                 {"cost_usd": cost.get("usd")} if isinstance(cost, dict) and cost.get("usd") is not None else None)
    return rec


# ---------------------------------------------------------------------------------------------- CLI
def _read_arg(value):
    if value and value.startswith("@"):
        return pathlib.Path(value[1:]).expanduser().read_text(encoding="utf-8")
    if value == "-":
        return sys.stdin.read()
    return value


def _read_records(src):
    raw = sys.stdin.read() if src == "-" else pathlib.Path(src).expanduser().read_text(encoding="utf-8")
    raw = raw.strip()
    if not raw:
        return []
    if raw.startswith("["):
        return json.loads(raw)
    try:
        one = json.loads(raw)
        return [one] if isinstance(one, dict) else list(one)
    except json.JSONDecodeError:
        return [json.loads(ln) for ln in raw.splitlines() if ln.strip()]


def _ctx(args):
    ctx = {d: getattr(args, d.replace("-", "_"), None) for d in DIMS}
    ctx["relationship"] = getattr(args, "relationship", None)
    if ctx.get("register"):
        ctx["register"] = style_pairs().norm_register(ctx["register"])
    return ctx


def _add_ctx(p):
    p.add_argument("--language", choices=LANGUAGES)
    p.add_argument("--register")
    p.add_argument("--audience-kind", dest="audience_kind", choices=AUDIENCE_KINDS)
    p.add_argument("--purpose", choices=PURPOSES)
    p.add_argument("--relationship", choices=RELATIONSHIPS)


def _print(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--vault", help="msg-vault root (default $MSG_VAULT or ~/msg-vault)")
    ap.add_argument("--data", help="harness-data root (default $HARNESS_DATA or ~/harness-data)")
    ap.add_argument("--allow-unsafe-vault", action="store_true", help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("features", help="features of a text (@file, - for stdin, or literal)")
    p.add_argument("--text", required=True)
    p.add_argument("--own", action="store_true", help="strip quoted replies first")

    p = sub.add_parser("classify", help="rule-based purpose / audience_kind / register guess")
    p.add_argument("--text", required=True)
    p.add_argument("--context", default="")
    p.add_argument("--subject", default="")
    p.add_argument("--to-domain", dest="to_domain", default="")

    p = sub.add_parser("ingest", help="append VoiceSamples to the vault (idempotent by message id)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--json", help="JSON object, array or JSON lines ('-' = stdin)")
    g.add_argument("--from-backfill", dest="from_backfill", help="style_samples.jsonl from a Gmail backfill")
    p.add_argument("--account", help="acct_ id (required for --from-backfill unless the records carry one)")
    p.add_argument("--harvest", help="hr_ id of the run doing the ingest")
    p.add_argument("--pairs", help="StylePair file for auto-linking drafts (default $HARNESS_DATA/style/pairs.jsonl)")
    p.add_argument("--no-link", action="store_true", help="don't auto-link email-draft StylePairs")

    p = sub.add_parser("update", help="append a changed line for one sample (outcome, relabel, draft link)")
    p.add_argument("--message", required=True, help="provider message id, msg_ id or vs_ id")
    p.add_argument("--source", default="gmail")
    p.add_argument("--outcome", choices=OUTCOMES)
    p.add_argument("--after-days", dest="outcome_after_days", type=int)
    p.add_argument("--draft-pair", dest="draft_pair")
    p.add_argument("--audience-party", dest="audience_party")
    p.add_argument("--purpose", choices=PURPOSES)
    p.add_argument("--audience-kind", dest="audience_kind", choices=AUDIENCE_KINDS)
    p.add_argument("--relationship", choices=RELATIONSHIPS)
    p.add_argument("--register")

    p = sub.add_parser("cursor", help="get or set the sent-mail SyncCursor")
    p.add_argument("--account", required=True)
    p.add_argument("--source", default="gmail")
    p.add_argument("--set-ts", dest="set_ts")
    p.add_argument("--last-id", dest="last_id")

    p = sub.add_parser("segment-stats", help="per-segment aggregates -> $HARNESS_DATA/voice/segment_stats.json")
    p.add_argument("--min-n", type=int, default=1)
    p.add_argument("--include-mixed", action="store_true", help="also count Claude-drafted (mixed) samples")
    p.add_argument("--stdout", action="store_true", help="print instead of writing")

    p = sub.add_parser("propose-rules", help="contrast-mine candidate rules")
    p.add_argument("--min-n", type=int, default=5)
    p.add_argument("--min-share", type=float, default=0.8)
    p.add_argument("--min-contrast", type=float, default=0.25)
    p.add_argument("--include-mixed", action="store_true")
    p.add_argument("--write", action="store_true", help="append to voice/rules.jsonl (+ voice_rule_proposed event)")
    p.add_argument("--harvest")

    p = sub.add_parser("rule", help="approve / retire / reword one rule (appends a new version)")
    p.add_argument("--id", required=True)
    p.add_argument("--status", choices=RULE_STATUSES)
    p.add_argument("--statement")
    p.add_argument("--note")

    p = sub.add_parser("rules", help="list rules (latest version), optionally for a context")
    _add_ctx(p)
    p.add_argument("--status", choices=RULE_STATUSES)

    p = sub.add_parser("profile", help="build the next VoiceProfile")
    p.add_argument("--harvest")
    p.add_argument("--include-mixed", action="store_true")
    p.add_argument("--notes")

    p = sub.add_parser("compare", help="diff two profiles (ids, latest, previous or current)")
    p.add_argument("--from", dest="a", default="previous")
    p.add_argument("--to", dest="b", default="latest")

    p = sub.add_parser("nearest", help="k exemplar samples for a drafting context")
    _add_ctx(p)
    p.add_argument("--text", help="draft, notes or the message being answered (@file)")
    p.add_argument("-k", type=int, default=5)
    p.add_argument("--no-text", action="store_true")
    p.add_argument("--include-mixed", action="store_true")

    p = sub.add_parser("check", help="draft features vs approved rules and the segment profile")
    _add_ctx(p)
    p.add_argument("--text", required=True)
    p.add_argument("--include-proposed", action="store_true")
    p.add_argument("--profile", default="latest", help="profile id, latest, or none")
    p.add_argument("--strict", action="store_true", help="exit 1 when an approved rule is violated")

    p = sub.add_parser("harvest-log", help="append one HarvestRun (JSON) + harvest_run event")
    p.add_argument("--json", required=True)

    args = ap.parse_args(argv)
    try:
        if args.cmd == "features":
            t = _read_arg(args.text)
            _print(features(own_text(t) if args.own else t))
        elif args.cmd == "classify":
            _print(classify(_read_arg(args.text), args.context, args.subject, args.to_domain))
        elif args.cmd == "ingest":
            if args.from_backfill:
                if not args.account:
                    raise VoiceError("--from-backfill needs --account acct_...")
                recs, origin = from_backfill(args.from_backfill, args.account), "backfill"
            else:
                recs, origin = _read_records(args.json), "harvest"
                if args.account:
                    recs = [dict(r, account=r.get("account") or args.account) for r in recs]
            res = ingest(recs, args.vault, origin, False if args.no_link else args.pairs, args.data,
                         args.allow_unsafe_vault, args.harvest)
            _print({"added": len(res["added"]), "skipped_dup": len(res["skipped_dup"]), "errors": res["errors"],
                    "new_samples": res["added"]})
            return 1 if res["errors"] and not res["added"] else 0
        elif args.cmd == "update":
            ch = {k: getattr(args, k) for k in ("outcome", "outcome_after_days", "draft_pair", "audience_party",
                                                 "purpose", "audience_kind", "relationship", "register")
                  if getattr(args, k) is not None}
            new = update(args.vault, args.message, ch, args.source, args.allow_unsafe_vault, args.data)
            _print({"id": new["id"], "outcome": new.get("outcome"), "purpose": new.get("purpose"),
                    "authorship": new.get("authorship")})
        elif args.cmd == "cursor":
            _print(cursor(args.vault, args.account, args.source, args.set_ts, args.last_id, args.allow_unsafe_vault, args.data))
        elif args.cmd == "segment-stats":
            st = segment_stats(load_samples(args.vault, args.include_mixed), args.min_n)
            if args.stdout:
                _print(privacy_guard(st, "segment_stats"))
            else:
                p = write_stats(st, args.data)
                _print({"written": str(p), "n_samples": st["n_samples"], "segments": len(st["segments"])})
        elif args.cmd == "propose-rules":
            samples = load_samples(args.vault, args.include_mixed)
            res = propose_rules(samples, args.min_n, args.min_share, args.min_contrast, existing=load_rules(args.data))
            if args.write and res["rules"]:
                write_rules(res["rules"], args.data, args.harvest)
            _print(privacy_guard(res, "propose-rules"))
        elif args.cmd == "rule":
            _print(set_rule(args.data, args.id, args.status, args.statement, args.note))
        elif args.cmd == "rules":
            ctx = _ctx(args)
            rs = load_rules(args.data).values()
            if any(ctx.values()):
                rs = rules_for(ctx, args.data, include_proposed=True)
            for r in rs:
                if not args.status or r.get("status") == args.status:
                    print(json.dumps({k: r.get(k) for k in ("id", "status", "statement", "scope", "support", "n",
                                                             "confidence", "version")}, ensure_ascii=False))
        elif args.cmd == "profile":
            prof = build_profile(load_samples(args.vault, args.include_mixed), args.data, args.harvest, args.notes)
            _print({"id": prof["id"], "version": prof["version"], "segments": len(prof["segments"]),
                    "rules": len(prof["rules"]), "diff_summary": (prof.get("diff_from_previous") or {}).get("summary")})
        elif args.cmd == "compare":
            samples = load_samples(args.vault) if "current" in (args.a, args.b) else None
            _print(compare(resolve_profile(args.a, args.data, samples), resolve_profile(args.b, args.data, samples)))
        elif args.cmd == "nearest":
            for r in nearest(load_samples(args.vault, args.include_mixed), _ctx(args), _read_arg(args.text), args.k,
                             args.vault, not args.no_text):
                print(json.dumps(r, ensure_ascii=False))
        elif args.cmd == "check":
            prof = None
            if args.profile != "none":
                try:
                    prof = resolve_profile(args.profile, args.data)
                except VoiceError:
                    prof = None
            res = check(_read_arg(args.text), _ctx(args), args.data, args.include_proposed, prof)
            _print(res)
            if args.strict and any(v["status"] == "approved" for v in res["violations"]):
                return 1
        elif args.cmd == "harvest-log":
            recs = _read_records(args.json)
            if len(recs) != 1:
                raise VoiceError("harvest-log takes exactly one JSON object")
            _print(harvest_log(recs[0], args.data))
    except (VoiceError, json.JSONDecodeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
