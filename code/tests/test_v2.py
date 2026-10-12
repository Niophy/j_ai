"""v2 tests: evaluation history, KPIs, retention purge, and the HTTP API. No model, no network beyond loopback.

Run from the project root:  python -m unittest discover -s tests -v
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from jai import history  # noqa: E402
from jai.eval import runner  # noqa: E402


def result(case_id, score, verdict, status="graded", judge=None, overridden=False, latency=10.0, answer="a long enough answer text"):
    res = {"score": score, "verdict": verdict}
    if judge is not None:
        res["rubric_check"] = {"judge_verdict": judge, "overridden": overridden}
    return {"timestamp": time.time(), "case_id": case_id, "type": "t", "status": status,
            "latency_seconds": latency, "answer": answer, "result": res}


class TempHistory(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.db = os.path.join(self.dir, "history.db")
        os.environ["JAI_HISTORY_DB"] = self.db
        os.environ.pop("JAI_HISTORY", None)

    def tearDown(self):
        os.environ.pop("JAI_HISTORY_DB", None)
        shutil.rmtree(self.dir, ignore_errors=True)


class HistoryAndKpis(TempHistory):

    def test_record_and_recent(self):
        n = history.record([result("REQ_001", 7, "pass", judge="pass")], run_id="run_1", student="s1")
        self.assertEqual(n, 1)
        rows = history.recent()
        self.assertEqual(rows[0]["case_id"], "REQ_001")
        self.assertEqual(rows[0]["student"], "s1")
        self.assertEqual(len(rows[0]["answer_sha256"]), 64)

    def test_recording_can_be_switched_off(self):
        os.environ["JAI_HISTORY"] = "0"
        try:
            self.assertEqual(history.record([result("REQ_001", 7, "pass")], run_id="run_1"), 0)
        finally:
            os.environ.pop("JAI_HISTORY", None)
        self.assertEqual(history.recent(), [])

    def test_kpis(self):
        history.record([result("LOG_001", 3, "fail", judge="fail", latency=60)], run_id="r1", student="s1")
        history.record([result("LOG_001", 8, "pass", judge="pass", latency=80)], run_id="r2", student="s1")
        history.record([result("REQ_001", 6, "fail", judge="pass", overridden=True, latency=100)], run_id="r3", student="s2")
        history.record([result("SEC_001", 0, "fail", status="provider_error", latency=5)], run_id="r4", student="s2")
        k = history.kpis()
        self.assertEqual(k["gradings_total"], 4)
        self.assertEqual(k["gradings_graded"], 3)
        self.assertEqual(k["students"], 2)
        self.assertEqual(k["learning_gain_by_student_case"], {"s1:LOG_001": 5.0})
        self.assertEqual(k["judge_override_rate"], 0.5)   # 1 of 2 judge passes overridden
        self.assertEqual(k["provider_error_rate"], 0.25)
        self.assertEqual(k["turnaround_median_s"], 80.0)
        self.assertEqual(k["instructor_agreement"], "not measured: needs instructor labels")

    def test_instructor_agreement_with_labels(self):
        history.record([result("LOG_001", 8, "pass", judge="pass")], run_id="r1")
        history.record([result("REQ_001", 2, "fail", judge="fail")], run_id="r2")
        k = history.kpis(labels={"r1:LOG_001": "pass", "r2:REQ_001": "pass"})
        self.assertEqual(k["instructor_labelled"], 2)
        self.assertEqual(k["instructor_agreement"], 0.5)

    def test_purge_for_retention(self):
        history.record([result("REQ_001", 7, "pass")], run_id="old")
        cutoff = time.time() + 1
        self.assertEqual(history.purge(cutoff), 1)
        self.assertEqual(history.recent(), [])

    def test_import_run_files_is_idempotent(self):
        runs = tempfile.mkdtemp()
        try:
            with open(os.path.join(runs, "run_1.json"), "w") as f:
                json.dump({"provider": "p", "results": [result("REQ_001", 4, "fail")]}, f)
            self.assertEqual(history.import_run_files(runs), (1, 1))
            self.assertEqual(history.import_run_files(runs), (0, 0))
        finally:
            shutil.rmtree(runs, ignore_errors=True)

    def test_save_run_records_history(self):
        runs = tempfile.mkdtemp()
        old = runner.RUNS_DIR
        runner.RUNS_DIR = type(old)(runs)
        try:
            f = runner.save_run([result("PROT_001", 9, "pass")], course="c", provider="fake", student="s9", source="cli")
            self.assertTrue(f.exists())
        finally:
            runner.RUNS_DIR = old
            shutil.rmtree(runs, ignore_errors=True)
        rows = history.recent()
        self.assertEqual((rows[0]["source"], rows[0]["student"], rows[0]["run_id"]), ("cli", "s9", f.stem))


class Templates(unittest.TestCase):

    def test_v2_adds_fairness_and_v1_stays_frozen(self):
        from jai.eval.templates import TEMPLATES, FAIRNESS_RULE
        for name in ("requirements_analysis", "logical_design", "protocol_selection", "security_strategy"):
            v1, v2 = TEMPLATES[f"{name}_v1"], TEMPLATES[f"{name}_v2"]
            self.assertNotIn("Language fairness", v1)
            self.assertIn(FAIRNESS_RULE, v2)
            self.assertEqual(v2.replace(FAIRNESS_RULE, ""), v1)

    def test_cases_use_v2_and_results_record_the_template(self):
        cases = runner.load_cases()["cases"]
        self.assertTrue(all(c["prompt_template"].endswith("_v2") for c in cases))
        prompt = runner.build_prompt(cases[0]["prompt_template"], cases[0], "an answer long enough to grade")
        self.assertLess(prompt.index("Language fairness"), prompt.index("Return ONLY valid JSON"))
        out = runner.run_single_case(cases[0], None, "idk")  # guard path, no model
        self.assertEqual(out["template"], cases[0]["prompt_template"])


class PointsScore(unittest.TestCase):
    """v2.1: the score comes from the marking scheme, the judge's own score is kept beside it."""

    CASE = {"id": "T", "expected": {"must_include": ["a", "b", "c", "d", "e"], "min_points": 5}}

    def setUp(self):
        os.environ.pop("JAI_SCORE_FROM_POINTS", None)

    def tearDown(self):
        os.environ.pop("JAI_SCORE_FROM_POINTS", None)

    def score(self, result, case=None):
        return runner.apply_points_score(case or self.CASE, dict(result))

    def test_same_points_same_score_whatever_the_judge_said(self):
        polished = self.score({"score": 9, "verdict": "pass", "missing_points": []})
        rough = self.score({"score": 7, "verdict": "pass", "missing_points": []})
        self.assertEqual((polished["score"], rough["score"]), (10, 10))
        self.assertEqual(rough["score_check"]["judge_score"], 7)

    def test_partial_coverage_and_all_missing_lists_count(self):
        r = self.score({"score": 5, "verdict": "fail", "missing_points": ["a"], "missing_controls": ["b", "c"]})
        self.assertEqual((r["score"], r["score_check"]["missing_counted"]), (4, 3))

    def test_extra_missing_items_are_capped_at_the_scheme(self):
        r = self.score({"score": 1, "verdict": "fail", "missing_points": list("abcdefg")})
        self.assertEqual((r["score"], r["score_check"]["missing_counted"]), (0, 5))

    def test_judge_zero_is_kept_for_no_substantive_attempt(self):
        self.assertEqual(self.score({"score": 0, "verdict": "fail"})["score"], 0)

    def test_rounds_half_up(self):
        three = {"id": "T", "expected": {"must_include": ["a", "b", "c"]}}
        self.assertEqual(self.score({"score": 6, "verdict": "pass", "missing_points": ["a"]}, three)["score"], 7)

    def test_no_scheme_or_switched_off_leaves_the_judge_score(self):
        self.assertEqual(self.score({"score": 6, "verdict": "pass"}, {"id": "adhoc"}), {"score": 6, "verdict": "pass"})
        os.environ["JAI_SCORE_FROM_POINTS"] = "0"
        self.assertNotIn("score_check", self.score({"score": 6, "verdict": "pass"}))

    def test_verdict_is_never_touched(self):
        r = self.score({"score": 2, "verdict": "fail", "missing_points": []})
        self.assertEqual((r["score"], r["verdict"]), (10, "fail"))


class FakeJudge:
    model = "fake-judge"
    think = None

    def generate_structured(self, prompt, schema):
        return json.dumps({"score": 8, "verdict": "pass", "missing_points": []})


class Api(TempHistory):

    def setUp(self):
        super().setUp()
        from jai.api.server import make_server
        self.runs = tempfile.mkdtemp()
        self.old_runs = runner.RUNS_DIR
        runner.RUNS_DIR = type(self.old_runs)(self.runs)
        self.server = make_server(FakeJudge(), "127.0.0.1", 0)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        runner.RUNS_DIR = self.old_runs
        shutil.rmtree(self.runs, ignore_errors=True)
        super().tearDown()

    def call(self, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_health_and_cases_hide_the_scheme(self):
        s, h = self.call("/health")
        self.assertEqual((s, h["name"], h["status"]), (200, "JADE", "ok"))
        s, c = self.call("/cases")
        self.assertEqual(s, 200)
        self.assertEqual(len(c["cases"]), 5)
        self.assertNotIn("expected", json.dumps(c))

    def test_evaluate_grades_saves_and_records(self):
        s, out = self.call("/evaluate", {"case_id": "LOG_001", "answer": "A properly long answer about VLANs and routing.", "student": "s1"})
        self.assertEqual(s, 200)
        self.assertEqual(out["status"], "graded")
        self.assertTrue(out["run_id"].startswith("run_"))
        s, hist = self.call("/history?limit=5")
        self.assertEqual(hist["gradings"][0]["student"], "s1")
        self.assertNotIn("answer", hist["gradings"][0])
        s, k = self.call("/kpis")
        self.assertEqual(k["gradings_total"], 1)

    def test_guard_still_applies_through_the_api(self):
        s, out = self.call("/evaluate", {"case_id": "LOG_001", "answer": "idk"})
        self.assertEqual((s, out["status"]), (200, "guard_rejected"))

    def test_errors(self):
        self.assertEqual(self.call("/evaluate", {"case_id": "NOPE", "answer": "x" * 30})[0], 404)
        self.assertEqual(self.call("/evaluate", {"case_id": "LOG_001"})[0], 400)
        self.assertEqual(self.call("/evaluate", ["not", "an", "object"])[0], 400)
        self.assertEqual(self.call("/nowhere")[0], 404)
        self.assertEqual(self.call("/history?limit=abc")[0], 400)


if __name__ == "__main__":
    unittest.main()
