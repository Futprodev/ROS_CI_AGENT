import anthropic, json, os

def analyse_with_claude(telemetry: dict, check_results: dict) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""You are a robotics CI validation agent.

Simulation telemetry:
{json.dumps(telemetry, indent=2)}

Constraint check results:
{json.dumps(check_results, indent=2)}

Rules:
- NEVER approve if collisions > 0
- Flag borderline cases for human review
- Be concise and technical — your audience is robotics engineers

Respond with:
1. APPROVED or REJECTED
2. A bullet-point summary of what passed/failed and why
3. Any edge cases requiring human review
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

if __name__ == "__main__":
    telemetry = {
        "collisions": 0, "avg_cpu": 55.0,
        "avg_ram_mb": 1800, "control_freq_hz": 60,
        "transform_tree_stable": True
    }
    from constraint_checker import evaluate
    results = evaluate(telemetry)
    print(analyse_with_claude(telemetry, results))
