"""Core pipeline tests with a fake judge. No model, no network.

Covers the parts the agent tests do not: the input guard, provider errors,
the runner's marking-scheme check, the scoreboard maths, and the fresh-install
promise that the default path never needs the optional openai package.

Run from the project root:  python -m unittest discover -s tests -v
"""

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from jai.eval import runner  # noqa: E402
from jai.eval.scorers import summarize  # noqa: E402

CASE = {
    "id": "T_001",
    "type": "requirements_analysis",
    "prompt_template": "requirements_analysis_v1",
    "input": {"scenario": "A test scenario."},
    "expected": {"must_include": ["a", "b", "c", "d", "e"], "min_points": 4},  # 1 missing allowed
}

ANSWER = "A properly long test answer that clears the twenty character input guard."


class FakeJudge:
    model = "fake-judge"
    think = None

    def __init__(self, reply):
        self.reply = reply if isinstance(reply, str) else json.dumps(reply)
        self.calls = 0

    def generate_structured(self, prompt, schema):
        self.calls += 1
        return self.reply


def grade(reply, answer=ANSWER, case=CASE):
    judge = FakeJudge(reply)
    return runner.run_single_case(case, judge, answer), judge


class GuardAndErrors(unittest.TestCase):

    def test_short_answer_is_guard_rejected_and_judge_never_called(self):
        out, judge = grade({"score": 9, "verdict": "pass"}, answer="idk")
        self.assertEqual(out["status"], runner.STATUS_GUARD_REJECTED)
        self.assertEqual(out["result"]["score"], 0)
        self.assertEqual(judge.calls, 0)

    def test_unparseable_reply_is_provider_error(self):
        out, _ = grade("the model rambled and returned no json")
        self.assertEqual(out["status"], runner.STATUS_PROVIDER_ERROR)
        self.assertEqual(out["result"]["verdict"], "fail")

    def test_json_wrapped_in_prose_is_rescued(self):
        out, _ = grade('Here you go: {"score": 7, "verdict": "pass", "missing_points": []} thanks')
        self.assertEqual(out["status"], runner.STATUS_GRADED)
        self.assertEqual(out["result"]["score"], 7)


class RubricCheck(unittest.TestCase):

    def setUp(self):
        os.environ.pop("JAI_RUBRIC_CHECK", None)

    def tearDown(self):
        os.environ.pop("JAI_RUBRIC_CHECK", None)

    def test_pass_with_too_many_missing_becomes_fail(self):
        out, _ = grade({"score": 8, "verdict": "pass", "missing_points": ["a", "b"]})
        check = out["result"]["rubric_check"]
        self.assertEqual(out["result"]["verdict"], "fail")
        self.assertTrue(check["overridden"])
        self.assertEqual(check["judge_verdict"], "pass")
        self.assertEqual((check["missing_listed"], check["allowed_missing"]), (2, 1))

    def test_pass_within_allowance_stays_pass(self):
        out, _ = grade({"score": 8, "verdict": "pass", "missing_points": ["a"]})
        self.assertEqual(out["result"]["verdict"], "pass")
        self.assertFalse(out["result"]["rubric_check"]["overridden"])

    def test_check_never_turns_fail_into_pass(self):
        out, _ = grade({"score": 3, "verdict": "fail", "missing_points": []})
        self.assertEqual(out["result"]["verdict"], "fail")
        self.assertFalse(out["result"]["rubric_check"]["overridden"])

    def test_all_missing_lists_count(self):
        out, _ = grade({"score": 8, "verdict": "pass", "missing_reasoning": ["x"], "missing_controls": ["y"]})
        self.assertEqual(out["result"]["rubric_check"]["missing_listed"], 2)
        self.assertEqual(out["result"]["verdict"], "fail")

    def test_case_without_scheme_is_untouched(self):
        adhoc = {k: v for k, v in CASE.items() if k != "expected"}
        out, _ = grade({"score": 8, "verdict": "pass", "missing_points": ["a", "b", "c"]}, case=adhoc)
        self.assertEqual(out["result"]["verdict"], "pass")
        self.assertNotIn("rubric_check", out["result"])

    def test_switch_off(self):
        os.environ["JAI_RUBRIC_CHECK"] = "0"
        out, _ = grade({"score": 8, "verdict": "pass", "missing_points": ["a", "b"]})
        self.assertEqual(out["result"]["verdict"], "pass")
        self.assertNotIn("rubric_check", out["result"])


class Scoreboard(unittest.TestCase):

    def test_guard_counts_as_zero_and_provider_errors_are_excluded(self):
        run = {"results": [
            {"status": "graded", "type": "t", "latency_seconds": 2.0, "result": {"score": 8, "verdict": "pass"}},
            {"status": "graded", "type": "t", "latency_seconds": 4.0, "result": {"score": 4, "verdict": "fail"}},
            {"status": "guard_rejected", "type": "t", "latency_seconds": 0.0, "result": {"score": 0, "verdict": "fail"}},
            {"status": "provider_error", "type": "t", "latency_seconds": 9.0, "result": {"score": 0, "verdict": "fail"}},
        ]}
        s = summarize(run)
        self.assertEqual(s["cases_total"], 4)
        self.assertEqual(s["average_score"], 4.0)          # (8 + 4 + 0) / 3
        self.assertEqual(s["pass_rate"], 0.33)             # 1 of 3 scorable
        self.assertEqual(s["cases_provider_error"], 1)
        self.assertEqual(s["avg_model_latency_seconds"], 3.0)  # graded rows only

    def test_non_numeric_score_is_counted_not_averaged(self):
        run = {"results": [
            {"status": "graded", "type": "t", "result": {"score": "high", "verdict": "pass"}},
            {"status": "graded", "type": "t", "result": {"score": 6, "verdict": "pass"}},
        ]}
        s = summarize(run)
        self.assertEqual(s["cases_bad_score_value"], 1)
        self.assertEqual(s["average_score"], 6.0)


class FreshInstall(unittest.TestCase):

    def test_default_provider_path_never_imports_openai(self):
        # A fresh subprocess, so no other test can have imported it first.
        code = ("import sys; import src.core.provider_factory as f; "
                "f.get_provider(); print('src.providers.gpt_provider' in sys.modules, 'openai' in sys.modules)")
        env = dict(os.environ, JAI_PROVIDER="ollama")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env,
                             capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(out, ["False", "False"])


if __name__ == "__main__":
    unittest.main()
