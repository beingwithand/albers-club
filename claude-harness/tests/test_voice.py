"""Tests for scripts/voice.py (email voice). Synthetic emails only, no real data. Run from the harness root:
    python3 -I -m unittest discover -s tests -t . -p test_voice.py
"""
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vo = _load("voice")
sc = _load("schema_check")

KO_FORMAL = [
    "김{n} 님,\n안녕하세요.\n\n공고를 보고 번역 포지션에 지원합니다. 이력서와 포트폴리오를 첨부했습니다.\n검토 부탁드립니다.\n\n감사합니다.\n홍길동 드림",
    "{n} 담당자님께\n안녕하십니까.\n\n지난주 제출한 지원서 관련하여 연락드립니다. 추가로 필요한 서류가 있으시면 말씀해 주십시오.\n\n감사합니다.\n홍길동 드림",
    "이{n} 님,\n안녕하세요.\n\n면접 일정 제안 주셔서 감사합니다. 목요일 오후 2시에 참석 가능합니다.\n확인 부탁드립니다.\n\n감사합니다.\n홍길동 드림",
    "박{n} 님,\n안녕하세요.\n\n채용 절차를 안내해 주셔서 감사합니다. 과제는 금요일까지 제출하겠습니다.\n\n감사합니다.\n홍길동 드림",
    "최{n} 님,\n안녕하세요.\n\n요청하신 경력 증명서를 첨부했습니다. 확인해 주시면 감사하겠습니다.\n\n감사합니다.\n홍길동 드림",
    "정{n} 님,\n안녕하세요.\n\n지원 결과를 기다리고 있습니다. 혹시 진행 상황을 알려 주실 수 있으신지 여쭙니다.\n\n감사합니다.\n홍길동 드림",
]
KO_CHAT = [
    "{n}아 오늘 저녁 먹을래? ㅎㅎ\n7시 어때",
    "어제 고마웠어 ㅋㅋ 다음엔 내가 살게",
    "{n}야 사진 보내줘 ㅎㅎ",
    "주말에 시간 돼? 같이 전시 보러 가자",
    "도착했어! 조심히 들어가 ㅎㅎ",
]
EN_FORMAL = [
    "Dear Ms. Client{n},\n\nThank you for your message. I would like to confirm that the translation will be delivered on Friday. Please find attached the glossary.\n\nBest regards,\nAlex",
    "Dear Mr. Agency{n},\n\nI am writing to follow up on the invoice sent last month. I would appreciate an update on the payment date.\n\nBest regards,\nAlex",
    "Dear Client{n} team,\n\nThank you for your feedback on the draft. I have revised the second section as requested.\n\nBest regards,\nAlex",
    "Dear Ms. Lee{n},\n\nI would like to propose a rate of 0.12 USD per word for this project. I look forward to your reply.\n\nBest regards,\nAlex",
    "Dear Project{n} manager,\n\nPlease find attached the final files. Thank you for your patience during the review.\n\nBest regards,\nAlex",
    "Dear Mr. Kim{n},\n\nThank you for your inquiry. I am available to start the localization project next week.\n\nBest regards,\nAlex",
]
EN_OFFICE = [
    "Hi Sam{n},\n\nI'm sending the updated file now. Let me know if anything's off!\n\nThanks!\nAlex",
    "Hi Jo{n},\n\nCan't make the 3pm sync, can we move it to 4? I'll bring the notes.\n\nThanks!\nAlex",
    "Hi Pat{n},\n\nI've pushed the fixes. It's ready for review whenever you're free.\n\nThanks!\nAlex",
    "Hi Lee{n},\n\nQuick one: I don't have access to the shared folder yet. Could you add me?\n\nThanks!\nAlex",
    "Hi Ari{n},\n\nThat's done. I'll start on the next batch tomorrow.\n\nThanks!\nAlex",
]


def make_records(account="acct_test"):
    recs = []
    sets = [(KO_FORMAL, "ko", "formal-email", "recruiter", "apply", "new"),
            (KO_CHAT, "ko", "chat", "friend", "chat", "close"),
            (EN_FORMAL, "en", "formal-email", "client", "inform", "ongoing"),
            (EN_OFFICE, "en", "office", "colleague", "request", "ongoing")]
    i = 0
    for texts, lang, reg, aud, purpose, rel in sets:
        for t in texts:
            i += 1
            recs.append({"message": f"m{i:04x}", "thread": f"t{i:04x}", "account": account,
                         "ts": f"2026-03-{(i % 27) + 1:02d}T10:00:00+00:00", "text": t.format(n=i),
                         "language": lang, "register": reg, "audience_kind": aud, "purpose": purpose,
                         "relationship": rel, "subject": f"Subject line {i}", "to": f"person{i}@example.com",
                         "context_summary": f"synthetic context {i}"})
    return recs


def cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = vo.main(argv)
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.tmp.name)
        self.vault = base / "msg-vault"
        self.data = base / "harness-data"
        self.pairs = self.data / "style" / "pairs.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def ingest_all(self, recs=None):
        return vo.ingest(recs or make_records(), self.vault, pairs_file=self.pairs, data=self.data)

    def samples(self, include_mixed=False):
        return vo.load_samples(self.vault, include_mixed)


class TestFeatures(unittest.TestCase):
    def test_korean_speech_levels(self):
        self.assertEqual(vo.ko_level("확인 부탁드립니다."), "hasipsio")
        self.assertEqual(vo.ko_level("제출하겠습니다"), "hasipsio")
        self.assertEqual(vo.ko_level("말씀해 주십시오."), "hasipsio")
        self.assertEqual(vo.ko_level("보내 드릴게요!"), "haeyo")
        self.assertEqual(vo.ko_level("괜찮으시죠?"), "haeyo")
        self.assertEqual(vo.ko_level("저녁 먹을래? ㅎㅎ"), "banmal")
        self.assertEqual(vo.ko_level("다음엔 내가 살게"), "banmal")
        self.assertEqual(vo.ko_level("오늘 끝냈다."), "plain")
        self.assertEqual(vo.ko_level("검토 완료함"), "nominal")
        self.assertIsNone(vo.ko_level("Thanks"))

    def test_korean_formal_email(self):
        f = vo.features(KO_FORMAL[0].format(n=1) + "\n010-1234-5678")
        self.assertEqual(f["language"], "ko")
        self.assertEqual(f["greeting"], "ko-haseyo")
        self.assertTrue(f["addressed_by_name"])
        self.assertEqual(f["closing"], "ko-gamsahamnida")
        self.assertEqual(f["ko_signoff"], "deurim")
        self.assertEqual(f["ko_speech_level"], "hasipsio")
        self.assertTrue(f["signature"])
        self.assertGreaterEqual(f["honorific_nim"], 1)

    def test_korean_chat(self):
        f = vo.features(KO_CHAT[0].format(n=1))
        self.assertEqual(f["ko_speech_level"], "banmal")
        self.assertGreaterEqual(f["emoticons"], 1)
        self.assertEqual(f["closing"], "none")
        self.assertFalse(f["signature"])
        self.assertEqual(vo.infer_register(f), "chat")

    def test_haeyo_and_honorific(self):
        f = vo.features("선생님, 자료 보내 주셔서 고마워요. 내일 확인하실 수 있으세요?")
        self.assertEqual(f["ko_speech_level"], "haeyo")
        self.assertGreaterEqual(f["honorific_si"], 1)
        self.assertGreaterEqual(f["questions"], 1)

    def test_english_cues(self):
        formal = vo.features(EN_FORMAL[0].format(n=1))
        self.assertEqual(formal["greeting"], "en-dear")
        self.assertEqual(formal["closing"], "en-best-regards")
        self.assertEqual(formal["en_contractions"], 0)
        self.assertGreaterEqual(formal["en_formal"], 2)
        self.assertEqual(vo.infer_register(formal), "formal-email")
        office = vo.features(EN_OFFICE[0].format(n=1))
        self.assertEqual(office["greeting"], "en-hi")
        self.assertEqual(office["closing"], "en-thanks")
        self.assertGreaterEqual(office["en_contractions"], 1)
        self.assertEqual(vo.features("John's file is here.")["en_contractions"], 0)  # possessive is not a contraction

    def test_bullets_emoji_hedges_mixed(self):
        f = vo.features("혹시 아래 확인 가능하실까요?\n- 파일 A\n- 파일 B\n1) deadline Friday 🙏\nmaybe next week works for the review meeting")
        self.assertEqual(f["bullets"], 3)
        self.assertEqual(f["emoji"], 1)
        self.assertGreaterEqual(f["hedges"], 2)
        self.assertEqual(f["language"], "mixed")
        self.assertEqual(f["length_bucket"], "xs")

    def test_length_buckets_by_language(self):
        self.assertEqual(vo.features("가" * 70)["length_bucket"], "s")
        self.assertEqual(vo.features("a" * 70)["length_bucket"], "xs")
        self.assertEqual(vo.features("")["length_bucket"], "xs")

    def test_own_text_strips_quotes(self):
        en = "Sounds good.\n\nOn Mon, Oct 12, 2026 at 3:00 PM Someone <a@b.com>\nwrote:\n> Can we meet?\n> ok"
        self.assertEqual(vo.own_text(en), "Sounds good.")
        ko = "네, 확인했습니다.\n\n2026년 10월 12일 (월) 오후 3:00, 김철수 <a@b.com>님이 작성:\n> 확인 부탁드립니다"
        self.assertEqual(vo.own_text(ko), "네, 확인했습니다.")
        fw = "FYI below.\n---------- Forwarded message ---------\nFrom: X"
        self.assertEqual(vo.own_text(fw), "FYI below.")
        self.assertEqual(vo.own_text("> only quoted\nmine"), "mine")

    def test_redact(self):
        t = vo.redact("mail a.b+c@ex-ample.co.kr or call 010-1234-5678 / +82 10 1234 5678, id 900101-1234567, acct 1234567890, https://x.y/z?q=1")
        for raw in ("a.b+c@", "1234-5678", "900101", "1234567890", "https://"):
            self.assertNotIn(raw, t)
        for tag in ("[EMAIL]", "[PHONE]", "[ID]", "[NUM]", "[URL]"):
            self.assertIn(tag, t)
        self.assertIn("2026-10-16", vo.redact("due 2026-10-16"))  # dates survive

    def test_classify(self):
        c = vo.classify("Thank you for the offer. Unfortunately I won't be able to take this project.",
                        context="reply to agency PM")
        self.assertEqual(c["purpose"], "decline")
        self.assertEqual(c["audience_kind"], "client")
        c = vo.classify("이력서를 첨부하여 지원합니다.", to_domain="greenhouse.io")
        self.assertEqual(c["purpose"], "apply")
        self.assertEqual(c["audience_kind"], "recruiter")
        self.assertEqual(vo.classify("ok")["purpose"], "unknown")


class TestPrivacy(Base):
    def test_guard(self):
        vo.privacy_guard({"segments": {"ko|*|*|*": {"n": 3, "samples": ["vs_0123456789ab"]}}, "ts": "2026-10-16T00:00:00+00:00"})
        for bad in ({"lessons": ["ask x@y.com"]}, {"note": "call 010-1234-5678"}, {"subject": "hi"},
                    {"rules": [{"context_summary": "x"}]}, {"n": "12345678901"}):
            with self.assertRaises(vo.VoiceError, msg=bad):
                vo.privacy_guard(bad)

    def test_vault_refused_inside_git_or_harness_data(self):
        repo = pathlib.Path(self.tmp.name) / "repo"
        (repo / ".git").mkdir(parents=True)
        with self.assertRaises(vo.VoiceError):
            vo.ingest(make_records()[:1], repo / "vault", pairs_file=False, data=self.data)
        with self.assertRaises(vo.VoiceError):
            vo.ingest(make_records()[:1], self.data / "vault", pairs_file=False, data=self.data)

    def test_harness_data_outputs_hold_no_raw_text(self):
        self.ingest_all()
        s = self.samples()
        vo.write_stats(vo.segment_stats(s), self.data)
        res = vo.propose_rules(s, existing={})
        vo.write_rules(res["rules"], self.data)
        vo.build_profile(s, self.data)
        blob = "".join(p.read_text(encoding="utf-8") for p in self.data.rglob("*") if p.is_file())
        for needle in ("Subject line", "synthetic context", "example.com", "홍길동", "Dear Ms", "person1@"):
            self.assertNotIn(needle, blob)


class TestIngest(Base):
    def test_ingest_idempotent_and_redacted(self):
        recs = make_records()
        recs[0]["text"] += "\n연락처 010-9999-8888 / hong@example.com"
        res = self.ingest_all(recs)
        self.assertEqual(len(res["added"]), len(recs))
        self.assertEqual(res["errors"], [])
        again = self.ingest_all(recs)
        self.assertEqual(again["added"], [])
        self.assertEqual(len(again["skipped_dup"]), len(recs))
        s = {x["message"]: x for x in self.samples()}
        first = s["msg_m0001"]
        self.assertEqual(first["id"], vo.sample_id("gmail", "msg_m0001"))
        self.assertEqual(first["thread"], "thr_t0001")
        self.assertEqual(first["direction"], "sent")
        self.assertEqual(first["authorship"], "user")
        self.assertEqual(first["to_domain"], "example.com")
        self.assertNotIn("to", first)
        txt = (self.vault / first["text_ref"]).read_text(encoding="utf-8")
        self.assertNotIn("010-9999-8888", txt)
        self.assertNotIn("hong@example.com", txt)
        self.assertIn("[PHONE]", txt)
        rep = sc.Report()
        n = sc.check_file(vo.samples_file(self.vault), "VoiceSample", sc.Ontology.load(), rep)
        self.assertEqual(n, len(recs))
        self.assertEqual(rep.errors, [])

    def test_bad_records_reported(self):
        bad = [{"message": "x1", "account": "me", "text": "hi"},
               {"message": "x2", "account": "acct_a", "text": "> quoted only"},
               {"message": "x3", "account": "acct_a", "text": "hello", "purpose": "gossip"},
               {"message": "x4", "account": "acct_a", "text": "hello", "register": "poetry"}]
        res = vo.ingest(bad, self.vault, pairs_file=False, data=self.data)
        self.assertEqual(res["added"], [])
        self.assertEqual(len(res["errors"]), 4)

    def test_from_backfill(self):
        bf = pathlib.Path(self.tmp.name) / "style_samples.jsonl"
        rows = [{"message_id": "18f0a1b2c3d4e5f6", "thread_id": "18f0a1b2c3d4e5f0", "date": "2026-02-03",
                 "to_domain": "greenhouse.io", "subject": "Application", "register": "formal-email", "language": "en",
                 "context": "application to recruiter", "excerpt": "Dear Hiring Team,\n\nI am applying for the translator role. Please find attached my resume.\n\nBest regards,\nAlex",
                 "excerpt_source": "snippet"},
                {"message_id": "18f0a1b2c3d4e5f7", "thread_id": "18f0a1b2c3d4e5f1", "date": "2026-02-04",
                 "to_domain": "gmail.com", "subject": "re", "register": "chat", "language": "ko",
                 "context": "friend", "excerpt": "고마워 ㅋㅋ 내일 보자", "excerpt_source": "body"}]
        bf.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        code, out, err = cli(["--vault", str(self.vault), "--data", str(self.data), "ingest", "--from-backfill", str(bf)])
        self.assertEqual(code, 2)
        self.assertIn("--account", err)
        code, out, err = cli(["--vault", str(self.vault), "--data", str(self.data), "ingest", "--from-backfill", str(bf),
                              "--account", "acct_main", "--no-link"])
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["added"], 2)
        s = {x["message"]: x for x in self.samples()}
        a = s["msg_18f0a1b2c3d4e5f6"]
        self.assertEqual((a["origin"], a["text_source"], a["purpose"], a["audience_kind"]), ("backfill", "snippet", "apply", "recruiter"))
        self.assertTrue(a["features"]["partial"])
        self.assertEqual(a["ts"], "2026-02-03T00:00:00+00:00")
        b = s["msg_18f0a1b2c3d4e5f7"]
        self.assertEqual((b["purpose"], b["features"]["ko_speech_level"]), ("chat", "banmal"))

    def test_update_outcome_and_link(self):
        self.ingest_all()
        vo.update(self.vault, "m0001", {"outcome": "positive", "outcome_after_days": 2}, data=self.data)
        vo.update(self.vault, "msg_m0002", {"purpose": "follow-up"}, data=self.data)
        s = {x["message"]: x for x in self.samples(include_mixed=True)}
        self.assertEqual((s["msg_m0001"]["outcome"], s["msg_m0001"]["outcome_after_days"]), ("positive", 2))
        self.assertEqual((s["msg_m0002"]["purpose"], s["msg_m0002"]["classified_by"]), ("follow-up", "user"))
        vo.update(self.vault, "m0003", {"draft_pair": "sp_20261016_120000_abcd"}, data=self.data)
        self.assertNotIn("msg_m0003", {x["message"] for x in self.samples()})          # mixed excluded by default
        self.assertIn("msg_m0003", {x["message"] for x in self.samples(include_mixed=True)})
        with self.assertRaises(vo.VoiceError):
            vo.update(self.vault, "nope", {"outcome": "replied"}, data=self.data)

    def test_auto_link_email_draft_pair(self):
        sp = vo.style_pairs()
        rec = make_records()[12]  # an English formal mail
        line = sp.add({"draft": "draft v0", "final": rec["text"], "language": "en", "direction": "none",
                       "register": "formal-email", "derived_from": "thr_" + rec["thread"], "origin": "email-draft"},
                      self.pairs)
        vo.ingest([rec], self.vault, pairs_file=self.pairs, data=self.data)
        [s] = self.samples(include_mixed=True)
        self.assertEqual((s["draft_pair"], s["authorship"]), (line["id"], "mixed"))

    def test_cursor_roundtrip_keeps_others(self):
        (self.vault).mkdir(parents=True)
        (self.vault / "cursors.json").write_text(json.dumps({"cursors": {"cur_other": {"id": "cur_other", "source": "lark",
                                                  "account": "acct_x", "last_ts": "2026-01-01T00:00:00+00:00"}}}))
        self.assertIsNone(vo.cursor(self.vault, "acct_main", data=self.data)["last_ts"])
        vo.cursor(self.vault, "acct_main", set_ts="2026-10-01T09:00:00Z", last_id="abc", data=self.data)
        c = vo.cursor(self.vault, "acct_main", data=self.data)
        self.assertEqual((c["id"], c["last_ts"], c["last_id"]), ("cur_gmail_sent_main", "2026-10-01T09:00:00+00:00", "abc"))
        doc = json.loads((self.vault / "cursors.json").read_text())
        self.assertIn("cur_other", doc["cursors"])
        rep = sc.Report()
        sc.check_file(self.vault / "cursors.json", "SyncCursor", sc.Ontology.load(), rep)
        self.assertEqual(rep.errors, [])


class TestLearning(Base):
    def setUp(self):
        super().setUp()
        self.ingest_all()

    def test_segment_stats(self):
        st = vo.segment_stats(self.samples())
        seg = st["segments"]["ko|formal-email|recruiter|apply"]
        self.assertEqual(seg["n"], 6)
        self.assertEqual(next(iter(seg["features"]["ko_speech_level"])), "hasipsio")
        self.assertNotIn("ko|*|*|*", st["segments"])  # language-only is not a segment (nothing to contrast)
        self.assertIn("en|formal-email|*|*", st["segments"])
        self.assertEqual(st["n_samples"], 22)

    def test_propose_rules_contrast(self):
        res = vo.propose_rules(self.samples(), existing={})
        rules = res["rules"]
        by = {(r["feature"], json.dumps(r["value"]), vo.seg_key(r["scope"])): r for r in rules}
        hs = [r for r in rules if r["feature"] == "ko_speech_level" and r["value"] == "hasipsio"]
        self.assertEqual(len(hs), 1, rules)
        r = hs[0]
        self.assertEqual(r["scope"]["language"], "ko")
        self.assertEqual(len(r["evidence"]), 6)
        self.assertTrue(all(e.startswith("vs_") for e in r["evidence"]))
        self.assertIn("하십시오체", r["statement"])
        # most general scope wins: the rule is not repeated for the narrower ko|formal-email|recruiter|apply segment
        self.assertEqual(sum(1 for k in by if k[0] == "ko_speech_level" and k[1] == '"hasipsio"'), 1)
        self.assertTrue(any(r["feature"] == "uses_contractions" and r["value"] is False and r["scope"]["language"] == "en"
                            for r in rules), rules)
        for r in rules:
            self.assertGreaterEqual(r["support"], 0.8)
            self.assertGreaterEqual(r["contrast"], 0.25)
        self.assertEqual(vo.propose_rules(self.samples(), min_n=50, existing={})["rules"], [])

    def test_write_approve_profile_compare_cycle(self):
        res = vo.propose_rules(self.samples(), existing={})
        vo.write_rules(res["rules"], self.data, harvest="hr_20261016_120000_abcd")
        events = [json.loads(l) for p in (self.data / "log").glob("*.jsonl") for l in p.read_text().splitlines()]
        self.assertEqual([e["type"] for e in events], ["voice_rule_proposed"])
        rules = vo.load_rules(self.data)
        rid = next(r["id"] for r in rules.values() if r["feature"] == "ko_speech_level" and r["value"] == "hasipsio")
        approved = vo.set_rule(self.data, rid, "approved")
        self.assertEqual((approved["status"], approved["version"]), ("approved", 2))
        # re-mining with no new data proposes nothing new
        self.assertEqual(vo.propose_rules(self.samples(), existing=vo.load_rules(self.data))["rules"], [])
        p1 = vo.build_profile(self.samples(), self.data)
        self.assertEqual((p1["id"], p1["version"]), ("vp_0001", 1))
        self.assertEqual(p1["rules"], [rid])
        self.assertIn("하십시오체", p1["rule_details"][0]["statement"])
        # drift: the user starts writing 해요체 to recruiters
        drift = []
        for i in range(8):
            drift.append({"message": f"d{i}", "account": "acct_test", "ts": "2026-09-01T10:00:00+00:00",
                          "text": f"강{i} 님, 안녕하세요.\n\n지원서 보내 드려요. 확인해 주시면 좋겠어요.\n\n감사해요!",
                          "language": "ko", "register": "formal-email", "audience_kind": "recruiter", "purpose": "apply"})
        self.ingest_all(drift)
        res2 = vo.propose_rules(self.samples(), existing=vo.load_rules(self.data))
        self.assertIn(rid, [w["id"] for w in res2["weakened"]])
        self.assertEqual(vo.load_rules(self.data)[rid]["status"], "approved")  # never auto-retired
        p2 = vo.build_profile(self.samples(), self.data)
        self.assertEqual((p2["version"], p2["previous"]), (2, "vp_0001"))
        d = p2["diff_from_previous"]["segments"]["ko|formal-email|recruiter|apply"]
        self.assertEqual(d["dominant_changed"]["ko_speech_level"], ["hasipsio", "haeyo"])
        c = vo.compare(vo.resolve_profile("previous", self.data), vo.resolve_profile("latest", self.data))
        self.assertEqual((c["from_profile"], c["to_profile"]), ("vp_0001", "vp_0002"))
        self.assertTrue(any("ko_speech_level hasipsio->haeyo" in s for s in c["summary"]))
        cur = vo.compare(vo.resolve_profile("latest", self.data), vo.resolve_profile("current", self.data, self.samples()))
        self.assertEqual(cur["summary"], ["no drift above thresholds"])
        onto = sc.Ontology.load()
        for f, t in (("voice/rules.jsonl", "VoiceRule"), ("voice/profiles.jsonl", "VoiceProfile")):
            rep = sc.Report()
            sc.check_file(self.data / f, t, onto, rep)
            self.assertEqual(rep.errors, [], f)

    def test_rule_status_validation(self):
        with self.assertRaises(vo.VoiceError):
            vo.set_rule(self.data, "vr_0000000000", "approved")


class TestDrafting(Base):
    def setUp(self):
        super().setUp()
        self.ingest_all()

    def test_nearest_same_segment_first(self):
        ctx = {"language": "ko", "register": "formal-email", "audience_kind": "recruiter", "purpose": "apply"}
        out = vo.nearest(self.samples(), ctx, text="면접 일정 제안 감사합니다. 목요일 오후 참석", k=4, vault=self.vault)
        self.assertEqual(len(out), 4)
        self.assertTrue(all(o["segment"] == "ko|formal-email|recruiter|apply" for o in out))
        self.assertIn("면접", out[0]["text"])  # bigram similarity breaks the tie
        out = vo.nearest(self.samples(), {"language": "en", "register": "office"}, k=30, vault=self.vault, with_text=False)
        self.assertTrue(all(o["segment"].startswith("en|") for o in out))
        self.assertTrue(out[0]["segment"].startswith("en|office"))
        self.assertNotIn("text", out[0])

    def test_check_flags_rule_violation(self):
        vo.write_rules(vo.propose_rules(self.samples(), existing={})["rules"], self.data)
        for r in vo.load_rules(self.data).values():
            vo.set_rule(self.data, r["id"], "approved")
        prof = vo.build_profile(self.samples(), self.data)
        ctx = {"language": "ko", "register": "formal-email", "audience_kind": "recruiter", "purpose": "apply"}
        bad = vo.check("김민수 님, 지원서 보내 드려요. 확인해 주세요 ㅎㅎ", ctx, self.data, profile=prof)
        self.assertTrue(any(v["expected"] == "hasipsio" and v["got"] == "haeyo" for v in bad["violations"]), bad["violations"])
        self.assertTrue(bad["profile_deviations"])
        good = vo.check(KO_FORMAL[2].format(n=99), ctx, self.data, profile=prof)
        self.assertFalse([v for v in good["violations"] if v["got"] != v["expected"] and v["expected"] == "hasipsio"])
        self.assertGreater(len(good["passed"]), 0)


class TestHarvestLogAndCli(Base):
    def test_harvest_log(self):
        rec = {"account": "acct_test", "mode": "incremental", "cursor_from": "2026-10-01T00:00:00Z",
               "cursor_to": "2026-10-08T00:00:00Z", "counts": {"threads_seen": 9, "ingested": 4, "skipped_dup": 1},
               "new_samples": [vo.sample_id("gmail", "msg_a")], "new_rules_proposed": [],
               "lessons": ["Korean recruiter mail is always 하십시오체 so far"], "cost": {"usd": 0.04}}
        out = vo.harvest_log(rec, self.data)
        self.assertTrue(out["id"].startswith("hr_"))
        [ev] = [json.loads(l) for p in (self.data / "log").glob("*.jsonl") for l in p.read_text().splitlines()]
        self.assertEqual((ev["type"], ev["items"], ev["cost_usd"]), ("harvest_run", [out["id"]], 0.04))
        with self.assertRaises(vo.VoiceError):
            vo.harvest_log(dict(rec, lessons=["reply to kim@corp.com faster"]), self.data)
        with self.assertRaises(vo.VoiceError):
            vo.harvest_log(dict(rec, mode="weekly"), self.data)
        onto = sc.Ontology.load()
        for path, t in ((self.data / "voice" / "harvests.jsonl", "HarvestRun"), (next((self.data / "log").glob("*.jsonl")), "Event")):
            rep = sc.Report()
            sc.check_file(path, t, onto, rep)
            self.assertEqual(rep.errors, [], t)

    def test_cli_pipeline(self):
        src = pathlib.Path(self.tmp.name) / "batch.jsonl"
        src.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in make_records()), encoding="utf-8")
        base = ["--vault", str(self.vault), "--data", str(self.data)]
        code, out, err = cli(base + ["ingest", "--json", str(src), "--pairs", str(self.pairs)])
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["added"], 22)
        code, out, err = cli(base + ["segment-stats"])
        self.assertEqual(code, 0, err)
        self.assertTrue((self.data / "voice" / "segment_stats.json").exists())
        code, out, err = cli(base + ["propose-rules", "--write"])
        self.assertEqual(code, 0, err)
        rid = json.loads(out)["rules"][0]["id"]
        code, out, err = cli(base + ["rule", "--id", rid, "--status", "approved"])
        self.assertEqual(code, 0, err)
        code, out, err = cli(base + ["profile"])
        self.assertEqual((code, json.loads(out)["id"]), (0, "vp_0001"))
        code, out, err = cli(base + ["compare", "--from", "latest", "--to", "current"])
        self.assertEqual(code, 0, err)
        code, out, err = cli(base + ["nearest", "--language", "en", "--register", "office", "-k", "2", "--no-text"])
        self.assertEqual((code, len(out.strip().splitlines())), (0, 2))
        draft = pathlib.Path(self.tmp.name) / "draft.txt"
        draft.write_text("Hey, gonna send it tmrw lol", encoding="utf-8")
        code, out, err = cli(base + ["check", "--text", f"@{draft}", "--language", "en", "--register", "formal-email",
                                     "--audience-kind", "client", "--purpose", "inform"])
        self.assertEqual(code, 0, err)
        self.assertIn("violations", json.loads(out))
        code, out, err = cli(base + ["rules", "--status", "approved"])
        self.assertEqual((code, len(out.strip().splitlines())), (0, 1))
        code, out, err = cli(base + ["features", "--text", "안녕하세요. 확인했습니다."])
        self.assertEqual(json.loads(out)["ko_speech_level"], "hasipsio")


if __name__ == "__main__":
    unittest.main()
