from google import genai
import json, os

def analyse_with_claude(telemetry: dict, check_results: dict) -> str:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = f"""You are a robotics CI validation agent reviewing a simulation test run.

## Simulation Telemetry
{json.dumps(telemetry, indent=2)}

## Constraint Check Results
{json.dumps(check_results, indent=2)}

## Constraints Reference
- max_collisions: 0 (any collision = unsafe)
- min_control_frequency_hz: 5 (this is good enough for testing perposes, if its lower than this then that is dangerous)
- max_cpu_percent: 80 (above this = system overload risk)
- max_ram_mb: 2048 (above this = memory issue)
- transform_tree_stable: true (false = TF not publishing, navigation broken)

## Your Task
Analyse the simulation results and produce a structured report with:

1. **APPROVED** or **REJECTED** verdict on the first line
2. **Summary** — one sentence explaining the overall result
3. **Constraint Analysis** — for each constraint:
   - Status (PASS/FAIL)
   - The actual value vs the limit
   - What this means for the robot in the real world
4. **Root Cause Analysis** — for any failures, what likely caused them
5. **Recommendations** — specific actionable steps to fix each failure
6. **Borderline Flags** — any values close to limits that need watching

## Rules
- NEVER approve if collisions > 0
- NEVER approve if control_freq_hz == 0.0 (means controller not running)
- NEVER approve if transform_tree_stable == false (means TF broken)
- Flag anything within 10% of a limit for human review
- Be concise and technical — your audience is robotics engineers
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

if __name__ == "__main__":
    import sys
    telemetry_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/telemetry.json"

    with open(telemetry_path) as f:
        telemetry = json.load(f)

    from constraint_checker import evaluate
    results = evaluate(telemetry)
    print(analyse_with_claude(telemetry, results))