import yaml, json

def load_constraints(path="config/constraints.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)

def evaluate(telemetry: dict) -> dict:
    c = load_constraints()
    margin = c["borderline_threshold_percent"] / 100

    results = {
        "collisions":  telemetry.get("collisions", 0) <= c["max_collisions"],
        "cpu":         telemetry.get("avg_cpu", 0) <= c["max_cpu_percent"],
        "ram":         telemetry.get("avg_ram_mb", 0) <= c["max_ram_mb"],
        "control_freq":telemetry.get("control_freq_hz", 0) >= c["min_control_frequency_hz"],
        "tf_stable":   telemetry.get("transform_tree_stable", False) == c["transform_tree_stable"],
    }

    # Flag borderline cases for human review
    borderline = []
    if telemetry.get("avg_cpu", 0) >= c["max_cpu_percent"] * (1 - margin):
        borderline.append(f"CPU near limit: {telemetry['avg_cpu']}%")
    if telemetry.get("collisions", 0) > 0:
        borderline.append(f"Collisions detected: {telemetry['collisions']}")

    passed = all(results.values())
    return {"passed": passed, "checks": results, "borderline": borderline}

if __name__ == "__main__":
    # Example telemetry for testing
    sample = {
        "collisions": 0, "avg_cpu": 55.0,
        "avg_ram_mb": 1800, "control_freq_hz": 60,
        "transform_tree_stable": True
    }
    print(json.dumps(evaluate(sample), indent=2))
