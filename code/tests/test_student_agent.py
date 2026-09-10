"""Student agent loop tests with a scripted fake provider. No model, no network.

Covers the branches the live runs never reached (2026-09-10): unknown-tool
refusal, provider_error inside the loop, empty reply, max_steps, the nudge
cap, and the rule that only a graded submission becomes the final answer.

Run from the project root:  python -m unittest tests.test_student_agent -v
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jai.agent import student as agent  # noqa: E402
from jai.eval import runner  # noqa: E402

CASE = {
    "id": "T_001",
    "type": "requirements_analysis",
    "prompt_template": "requirements_analysis_v1",
    "input": {"scenario": "A test scenario."},
    "expected": {"must_include": ["a", "b", "c"], "min_points": 3},
}

GOOD_ANSWER = "A properly long test answer that clears the twenty character input guard."


def tool_call(name, answer=GOOD_ANSWER):
    return {"function": {"name": name, "arguments": {"answer": answer}}}


class FakeStudent:
    """Replays a scripted list of assistant replies, one per chat() call."""

    model = "fake-student"
    think = None

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def chat(self, messages, tools=None, options=None, think=None, format=None):
        self.calls += 1
        if not self.replies:
            return {"role": "assistant", "content": "", "thinking": "", "tool_calls": []}
        r = self.replies.pop(0)
        return {"role": "assistant", "content": r.get("content", ""), "thinking": "",
                "tool_calls": r.get("tool_calls", [])}


class FakeJudge:
    """Returns scripted verdict JSON strings, one per grading."""

    model = "fake-judge"
    think = None

    def __init__(self, verdicts):
        self.verdicts = list(verdicts)

    def generate_structured(self, prompt, schema):
        v = self.verdicts.pop(0)
        return v if isinstance(v, str) else json.dumps(v)


PASS = {"score": 9, "verdict": "pass", "missing_points": []}
FAIL = {"score": 4, "verdict": "fail", "missing_points": ["a", "b"]}


def run(student, judge, **kw):
    kw.setdefault("log", lambda *_: None)
    return agent.run_student(CASE, student, judge, **kw)


class StudentAgentTests(unittest.TestCase):

    def test_pass_then_final_text(self):
        s = FakeStudent([{"tool_calls": [tool_call(agent.TOOL_NAME)]}, {"content": "final words"}])
        r = run(s, FakeJudge([PASS]))
        self.assertTrue(r["passed"])
        self.assertEqual(r["stop_reason"], "final_answer")
        self.assertEqual(r["submissions"], 1)
        # graded submission is the final answer; the closing text is kept separately
        self.assertEqual(r["final_answer"], GOOD_ANSWER)
        self.assertEqual(r["closing_text"], "final words")

    def test_revise_until_pass(self):
        s = FakeStudent([
            {"tool_calls": [tool_call(agent.TOOL_NAME, GOOD_ANSWER + " v1")]},
            {"tool_calls": [tool_call(agent.TOOL_NAME, GOOD_ANSWER + " v2")]},
            {"content": "done"},
        ])
        r = run(s, FakeJudge([FAIL, PASS]))
        self.assertTrue(r["passed"])
        self.assertEqual([a["score"] for a in r["attempts"]], [4, 9])
        self.assertTrue(r["final_answer"].endswith("v2"))

    def test_unknown_tool_is_refused_and_loop_continues(self):
        s = FakeStudent([
            {"tool_calls": [tool_call("read_answer_key")]},
            {"tool_calls": [tool_call(agent.TOOL_NAME)]},
            {"content": "done"},
        ])
        r = run(s, FakeJudge([PASS]))
        self.assertTrue(r["passed"])
        tool_msgs = [m for m in r["transcript"] if m["role"] == "tool"]
        self.assertIn("unknown tool", tool_msgs[0]["content"])
        self.assertEqual(tool_msgs[0]["tool_name"], "read_answer_key")
        self.assertEqual(r["submissions"], 1)

    def test_provider_error_counts_as_attempt_and_is_visible(self):
        s = FakeStudent([
            {"tool_calls": [tool_call(agent.TOOL_NAME)]},
            {"tool_calls": [tool_call(agent.TOOL_NAME)]},
            {"content": "done"},
        ])
        r = run(s, FakeJudge(["this is not json at all", PASS]))
        self.assertEqual(r["attempts"][0]["status"], runner.STATUS_PROVIDER_ERROR)
        self.assertIn("could not grade", r["attempts"][0]["verdict_shown"]["note"])
        self.assertEqual(r["submissions"], 2)
        self.assertTrue(r["passed"])

    def test_nudge_cap_then_gave_up(self):
        s = FakeStudent([{"content": "answer without submitting"}] * 5)
        r = run(s, FakeJudge([]))
        self.assertEqual(r["stop_reason"], "gave_up")
        self.assertEqual(r["nudges"], agent.MAX_NUDGES)
        self.assertEqual(r["submissions"], 0)
        self.assertIsNone(r["final_answer"])
        self.assertEqual(r["closing_text"], "answer without submitting")

    def test_empty_reply_after_nudges(self):
        s = FakeStudent([{"content": "text"}, {"content": "text"}, {"content": ""}])
        r = run(s, FakeJudge([]))
        self.assertEqual(r["stop_reason"], "empty_reply")

    def test_max_steps_terminates(self):
        # never submits, never stops: only the step cap ends it
        s = FakeStudent([{"tool_calls": [tool_call("nope")]}] * 50)
        r = run(s, FakeJudge([]), max_steps=6)
        self.assertEqual(r["stop_reason"], "max_steps")
        self.assertEqual(r["steps"], 6)

    def test_submission_budget_forces_final(self):
        s = FakeStudent([{"tool_calls": [tool_call(agent.TOOL_NAME)]}] * 3 + [{"content": "best I can do"}])
        r = run(s, FakeJudge([FAIL, FAIL, FAIL]), max_submissions=2)
        self.assertEqual(r["submissions"], 2)
        self.assertFalse(r["passed"])
        self.assertEqual(r["stop_reason"], "final_answer")
        self.assertEqual(r["final_answer"], GOOD_ANSWER)  # best graded attempt, not the closing text

    def test_strict_overrides_lenient_pass(self):
        lenient = {"score": 8, "verdict": "pass", "missing_points": ["a", "b"]}  # 2 missing, 0 allowed
        s = FakeStudent([{"tool_calls": [tool_call(agent.TOOL_NAME)]}, {"content": "x"}, {"content": "x"}, {"content": "x"}])
        r = run(s, FakeJudge([lenient]), strict=True)
        self.assertEqual(r["attempts"][0]["judge_verdict"], "pass")
        self.assertEqual(r["attempts"][0]["verdict"], "fail")
        self.assertFalse(r["passed"])

    def test_student_never_sees_expected_block(self):
        s = FakeStudent([{"tool_calls": [tool_call(agent.TOOL_NAME)]}, {"content": "done"}])
        r = run(s, FakeJudge([PASS]))
        for m in r["transcript"]:
            if m["role"] in ("system", "user"):
                self.assertNotIn("must_include", m["content"])
                self.assertNotIn("min_points", m["content"])


if __name__ == "__main__":
    unittest.main()
