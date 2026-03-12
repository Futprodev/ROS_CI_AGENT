import requests, os

def post_comment(pr_number: int, report: str, approved: bool):
    token = os.environ["GITHUB_TOKEN"]
    repo  = os.environ["GITHUB_REPOSITORY"]  # don't forget to set this maul
    verdict = "APPROVED" if approved else "REJECTED"

    body = f"## CI Validation Agent — {verdict}\n\n{report}"
    if not approved:
        body += "\n\n> Human review required before merging."

    resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
        json={"body": body},
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    )
    resp.raise_for_status()
    print(f"Comment posted to PR #{pr_number}")
