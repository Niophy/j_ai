TEMPLATES = {

    "requirements_analysis_v1": """
You are marking a network design answer.

Be strict. Think like an examiner.

Scenario:
{scenario}

Student Response:
{student_answer}

Check:
- Did they clearly separate business goals and technical goals?
- Did they identify constraints?
- Did they consider scalability?
- Did they address security?
- Did they avoid making assumptions?

Return ONLY valid JSON:

{{
  "score": 0 to 10,
  "verdict": "pass" or "fail",
  "missing_points": [],
  "technical_errors": [],
  "strengths": []
}}

Do not explain outside JSON.
""",

    "logical_design_v1": """
You are reviewing a logical network design explanation.

Scenario:
{scenario}

Student Response:
{student_answer}

Evaluate:
- Is there clear hierarchy?
- Is segmentation justified?
- Is addressing structured?
- Is routing choice logical?
- Is redundancy considered?

Be critical. Weak answers should score low.

Return ONLY valid JSON:

{{
  "score": 0 to 10,
  "verdict": "pass" or "fail",
  "missing_points": [],
  "design_flaws": [],
  "strengths": []
}}
""",

    "protocol_selection_v1": """
You are evaluating protocol justification quality.

Question:
{question}

Student Response:
{student_answer}

Check:
- Is the protocol suitable for the scenario?
- Is scalability addressed?
- Is convergence or performance mentioned?
- Are incorrect claims made?

Return ONLY valid JSON:

{{
  "score": 0 to 10,
  "verdict": "pass" or "fail",
  "incorrect_claims": [],
  "missing_reasoning": [],
  "strengths": []
}}
""",

    "security_strategy_v1": """
You are evaluating a proposed security strategy.

Scenario:
{scenario}

Student Response:
{student_answer}

Check:
- Is there layered security?
- Is segmentation mentioned?
- Is remote access protected?
- Is monitoring included?
- Are internal and perimeter security separated?

Return ONLY valid JSON:

{{
  "score": 0 to 10,
  "verdict": "pass" or "fail",
  "missing_controls": [],
  "risk_gaps": [],
  "strengths": []
}}
"""
}
