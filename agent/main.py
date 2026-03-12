import json, sys, os
from constraint_checker import evaluate
from reason_act import analyse_with_claude
from github_reporter import post_comment

def run(telemetry_path: str, pr_number: int):
    with open(telemetry_path) as f:
        telemetry = json.load(f)

    check_results = evaluate(telemetry)
    report = analyse_with_claude(telemetry, check_results)
    approved = check_results["passed"] and len(check_results["borderline"]) == 0

    print(report)
    post_comment(pr_number, report, approved)

    sys.exit(0 if approved else 1)  # Exit code used by GitHub Actions

if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2]))
