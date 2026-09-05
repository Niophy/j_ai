"""J_AI command line — evaluate one answer and print the verdict as JSON.

Usage:
    python cli.py evaluate --case REQ_001 --answer myanswer.txt
    python cli.py evaluate --template requirements_analysis_v1 --scenario scenario.txt --answer myanswer.txt
    python cli.py evaluate --list-templates
    python cli.py evaluate --list-cases

Exit codes: 0 = pass, 1 = fail (including guard-rejected answers),
2 = usage error or runtime/provider error (nothing was actually graded).
"""

import argparse
import json
import sys

from dotenv import load_dotenv

from jai.eval.runner import (
    STATUS_PROVIDER_ERROR,
    load_cases,
    provider_label,
    run_single_case,
    save_run,
)
from jai.eval.templates import TEMPLATES
from src.core.provider_factory import get_provider

load_dotenv()


def read_text(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def find_case(case_id):
    for case in load_cases().get("cases", []):
        if case["id"] == case_id:
            return case
    return None


def adhoc_case(template_name, scenario_text):
    # Type is the template name without its version suffix: requirements_analysis_v1 -> requirements_analysis
    case_type = template_name.rsplit("_v", 1)[0]
    input_key = "question" if "{question}" in TEMPLATES[template_name] else "scenario"
    return {
        "id": "ADHOC",
        "type": case_type,
        "prompt_template": template_name,
        "input": {input_key: scenario_text},
    }


def cmd_evaluate(args):
    if args.list_templates:
        for name in TEMPLATES:
            print(name)
        return 0
    if args.list_cases:
        for case in load_cases().get("cases", []):
            print(f"{case['id']}  ({case['type']})")
        return 0

    if args.case:
        case = find_case(args.case)
        if case is None:
            print(f"Unknown case id: {args.case} (try --list-cases)", file=sys.stderr)
            return 2
    elif args.template and args.scenario:
        if args.template not in TEMPLATES:
            print(f"Unknown template: {args.template} (try --list-templates)", file=sys.stderr)
            return 2
        case = adhoc_case(args.template, read_text(args.scenario))
    else:
        print("Need --case ID, or --template NAME with --scenario FILE (plus --answer FILE).", file=sys.stderr)
        return 2

    if not args.answer:
        print("Need --answer FILE (or '-' to read the answer from stdin).", file=sys.stderr)
        return 2

    answer = read_text(args.answer)
    provider = get_provider()
    outcome = run_single_case(case, provider, answer)
    print(json.dumps(outcome, indent=2, ensure_ascii=False))

    if args.save:
        run_file = save_run(
            [outcome],
            course="cli",
            version="adhoc",
            provider=provider_label(provider),
        )
        print(f"Saved to {run_file}", file=sys.stderr)

    if outcome.get("status") == STATUS_PROVIDER_ERROR:
        return 2
    return 0 if str(outcome["result"].get("verdict", "")).lower() == "pass" else 1


def main():
    parser = argparse.ArgumentParser(prog="jai", description="J_AI evaluation engine")
    sub = parser.add_subparsers(dest="command", required=True)

    ev = sub.add_parser("evaluate", help="grade one answer, print the JSON verdict")
    ev.add_argument("--case", help="grade against a stored case id from cases.json")
    ev.add_argument("--template", help="grade ad-hoc with this template (see --list-templates)")
    ev.add_argument("--scenario", help="file with the scenario/question text (ad-hoc mode)")
    ev.add_argument("--answer", help="file with the student answer, or '-' for stdin")
    ev.add_argument("--save", action="store_true", help="also save a run file usable by the scoreboard")
    ev.add_argument("--list-templates", action="store_true")
    ev.add_argument("--list-cases", action="store_true")
    ev.set_defaults(func=cmd_evaluate)

    args = parser.parse_args()
    try:
        sys.exit(args.func(args))
    except SystemExit:
        raise
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
