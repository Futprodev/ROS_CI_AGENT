# CI Agent — Automated ROS 2 CI/CD Validation Pipeline

An AI-powered agent that automatically validates ROS 2 code changes by running headless Gazebo simulations and using Gemini AI to approve or reject GitHub Pull Requests.

---

## How It Works

```
Developer opens PR
  └── GitHub Actions triggers ci_agent.yml
        ├── run_headless_sim.sh
        │     ├── sources ROS 2 workspace
        │     ├── launches Gazebo headless (gz sim -s -r)
        │     ├── patrol_node.py drives robot around arena at 50Hz
        │     └── telemetry_recorder.py writes /tmp/telemetry.json after 90s
        └── main.py
              ├── constraint_checker.py  → scores CPU, RAM, collisions, TF, freq
              ├── reason_act.py          → sends results to Gemini API
              └── github_reporter.py     → posts APPROVED/REJECTED comment on PR
```

---

## Project Structure

```
ci-agent/
├── .github/workflows/
│   └── ci_agent.yml             ← GitHub Actions entry point (triggers on PR to main)
├── sim/
│   └── run_headless_sim.sh      ← sources ROS 2, launches Gazebo headless, runs 90s sim
├── agent/
│   ├── constraint_checker.py    ← scores telemetry vs config/constraints.yaml
│   ├── reason_act.py            ← Gemini API reasoning and report generation
│   ├── github_reporter.py       ← posts APPROVED/REJECTED verdict as PR comment
│   └── main.py                  ← orchestrator: telemetry → check → reason → report
└── config/
    └── constraints.yaml         ← robot performance thresholds
```

---

## Constraints

```yaml
max_collisions: 0                 # any collision = fail
min_control_frequency_hz: 50      # robot must publish cmd_vel at >=50Hz
max_cpu_percent: 80               # must stay under 80% CPU
max_ram_mb: 2048                  # must stay under 2GB RAM
transform_tree_stable: true       # ROS TF tree must be publishing
borderline_threshold_percent: 10  # within 10% of any limit = flag for human review
```

---

## Telemetry JSON Format

Written to `/tmp/telemetry.json` after each 90s simulation run:

```json
{
  "collisions": 0,
  "avg_cpu": 22.17,
  "avg_ram_mb": 1800.0,
  "control_freq_hz": 50.3,
  "transform_tree_stable": true
}
```

---

## AI Validation Report

The agent uses Gemini (`gemini-2.0-flash`) to produce a structured report posted as a PR comment:

- **APPROVED / REJECTED** verdict
- Constraint analysis with actual vs limit values
- Real-world impact explanation for each failure
- Root cause analysis
- Actionable recommendations
- Borderline flags for human review

---

## Docker Setup

The dev environment runs in Docker to avoid WSL package conflicts.

### First Time Setup

```bash
# Build the image
docker build -t ci_agent_ros:latest ~/ci-agent/

# Create persistent container
docker run -it \
  --name ci_agent_dev \
  -v ~/ros_ws:/ros2_ws \
  -v ~/ci-agent:/ci-agent \
  -e DISPLAY=$(ip route | grep default | awk '{print $3}'):0.0 \
  ci_agent_ros:latest bash
```

### Every Session

```bash
~/ci-agent/dev.sh
```

### Extra Terminals

```bash
docker exec -it ci_agent_dev bash
```

---

## Testing the Agent Locally

Inside the container:

```bash
# Set API key
export GEMINI_API_KEY="your-key-here"

# Run a simulation first (or use existing telemetry)
ros2 launch ci_agent_robot sim.launch.py

# Test constraint checker only
cd /ci-agent/agent
python3 constraint_checker.py

# Test full AI reasoning against real telemetry
python3 reason_act.py /tmp/telemetry.json

# Test full pipeline (without posting GitHub comment)
python3 main.py /tmp/telemetry.json <PR_NUMBER>
```

---

## One-Command Test Cycle

```bash
/ci-agent/sim/run_and_validate.sh
```

This rebuilds the ROS package, runs the simulation, and runs the AI agent automatically.

---

## GitHub Secrets Required

Go to your repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|--------|-------|
| `GEMINI_API_KEY` | From aistudio.google.com |
| `GITHUB_TOKEN` | Auto-provided by GitHub Actions |

---

## Constraints Config Reference

Edit `config/constraints.yaml` to tune thresholds for your robot:

| Field | Default | Meaning |
|-------|---------|---------|
| `max_collisions` | 0 | Zero tolerance for wall hits |
| `min_control_frequency_hz` | 50 | Minimum cmd_vel publish rate |
| `max_cpu_percent` | 80 | CPU usage ceiling |
| `max_ram_mb` | 2048 | RAM usage ceiling |
| `transform_tree_stable` | true | TF must be publishing |
| `borderline_threshold_percent` | 10 | Flag if within 10% of any limit |

---

## Troubleshooting

**`config/constraints.yaml` not found**
Run the agent from `/ci-agent/agent/` or the path is resolved relative to the script automatically.

**Gemini quota exceeded**
Free tier allows 15 requests/minute and 1500/day on `gemini-2.0-flash`. If you hit the limit wait 60 seconds and retry.

**`gz: command not found` inside container**
```bash
apt-get update && apt-get install -y ros-jazzy-ros-gz
```

**Robot not spawning**
Make sure `gz-sim-user-commands-system` plugin is in `test_world.sdf`.

**Contact sensor not publishing**
Sensor and TouchPlugin must be on the wall models in the world SDF, not on the robot URDF.

**colcon build fails**
```bash
source /opt/ros/jazzy/setup.bash
cd /ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select ci_agent_robot
```

---

## Author

Maulana Mu'ammar 

## License

MIT License
