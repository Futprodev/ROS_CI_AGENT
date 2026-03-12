# CI Agent — Automated ROS 2 CI/CD Validation Pipeline

An AI-powered agent that automatically validates ROS 2 code changes by running headless Gazebo simulations and using Claude to approve or reject GitHub Pull Requests.

---

## Project Structure

```
~/
├── ci-agent/                        ← the agent
│   ├── .github/workflows/
│   │   └── ci_agent.yml             ← GitHub Actions entry point
│   ├── sim/
│   │   ├── run_headless_sim.sh      ← launches Gazebo headless + telemetry recorder
│   │   └── telemetry_recorder.py    ← ROS 2 node that writes /tmp/telemetry.json
│   ├── agent/
│   │   ├── constraint_checker.py    ← scores telemetry vs thresholds
│   │   ├── reason_act.py            ← Claude API reasoning layer
│   │   ├── github_reporter.py       ← posts verdict as GitHub PR comment
│   │   └── main.py                  ← orchestrates all steps
│   ├── config/
│   │   └── constraints.yaml         ← robot performance thresholds
│   ├── Dockerfile                   ← project Docker image definition
│   └── dev.sh                       ← helper script to enter container
│
└── ros_ws/                          ← ROS 2 workspace (note: ros_ws not ros2_ws)
    └── src/
        └── ci_agent_robot/          ← robot package
            ├── urdf/
            │   ├── robot.urdf.xacro ← robot description
            │   └── robot.sdf        ← converted SDF (generated via gz sdf -p)
            ├── worlds/
            │   └── test_world.sdf   ← walled arena world
            ├── launch/
            │   └── sim.launch.py    ← full simulation launch
            ├── config/
            │   └── gz_bridge.yaml   ← Gazebo <-> ROS 2 topic bridge config
            ├── ci_agent_robot/
            │   ├── patrol_node.py         ← drives robot at 50Hz
            │   ├── telemetry_recorder.py  ← records sim metrics
            │   └── collision_monitor.py   ← watches /bumper/contact
            ├── package.xml
            └── setup.py
```

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
              ├── reason_act.py          → sends results to Claude API
              └── github_reporter.py     → posts APPROVED/REJECTED comment on PR
```

---

## Docker Setup

The entire dev environment runs in Docker to avoid WSL package conflicts
(WSL has a mysql/mariadb conflict caused by Frappe installation — see Troubleshooting).

### First Time Setup

```bash
# Build the image (only needed once)
docker build -t ci_agent_ros:latest ~/ci-agent/

# Create the persistent container (only needed once)
docker run -it \
  --name ci_agent_dev \
  -v ~/ros_ws:/ros2_ws \
  -v ~/ci-agent:/ci-agent \
  -e DISPLAY=$(ip route | grep default | awk '{print $3}'):0.0 \
  -e LIBGL_ALWAYS_INDIRECT=0 \
  -e QT_X11_NO_MITSHM=1 \
  ci_agent_ros:latest \
  bash
```

### Every Session After That

```bash
# Option 1 — use the helper script (recommended)
~/ci-agent/dev.sh

# Option 2 — manually
docker start -ai ci_agent_dev

# Option 3 — open extra terminal into running container
docker exec -it ci_agent_dev bash
```

### Rebuild Image (if Dockerfile changes)

```bash
~/ci-agent/dev.sh build
```

---

## Gazebo GUI (Visual Inspection)

To observe the simulation visually you need VcXsrv running on Windows.

### One-time Windows Setup

1. Download and install VcXsrv: https://sourceforge.net/projects/vcxsrv/
2. Launch XLaunch with these settings:
   - Multiple windows
   - Display number: 0
   - Start no client
   - ✅ Disable access control
3. Allow VcXsrv through Windows Firewall (both Private and Public)

```powershell
# PowerShell as Administrator
New-NetFirewallRule -DisplayName "VcXsrv" -Direction Inbound -Program "C:\Program Files\VcXsrv\vcxsrv.exe" -Action Allow -Profile Any
```

### Launch GUI Container

```bash
HOST_IP=$(ip route | grep default | awk '{print $3}')

docker run -it --rm \
  --name ros_gui \
  -v ~/ros_ws:/ros2_ws \
  -v ~/ci-agent:/ci-agent \
  -e DISPLAY=$HOST_IP:0.0 \
  -e LIBGL_ALWAYS_INDIRECT=0 \
  -e QT_X11_NO_MITSHM=1 \
  ci_agent_ros:latest \
  bash
```

Then inside:

```bash
source /opt/ros/jazzy/setup.bash
source /ros2_ws/install/setup.bash
gz sim /ros2_ws/src/ci_agent_robot/worlds/test_world.sdf
```

---

## Building the Robot Package

Run these inside the container:

```bash
source /opt/ros/jazzy/setup.bash
cd /ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select ci_agent_robot
source install/setup.bash
```

---

## Running the Simulation

### Headless (CI mode)

```bash
gz sim -s -r /ros2_ws/src/ci_agent_robot/worlds/test_world.sdf
```

### Headless with verbose logging

```bash
gz sim -s -r -v 4 /ros2_ws/src/ci_agent_robot/worlds/test_world.sdf
```

### Via launch file (starts everything together)

```bash
ros2 launch ci_agent_robot sim.launch.py
```

---

## Monitoring a Running Simulation

Open extra terminals into the container with `docker exec -it ci_agent_dev bash`, then:

```bash
# See all active topics
ros2 topic list

# Watch control commands
ros2 topic echo /cmd_vel

# Monitor control frequency
ros2 topic hz /cmd_vel

# Watch odometry
ros2 topic echo /odom

# Check TF tree
ros2 run tf2_tools view_frames

# Watch telemetry file update live
watch -n 1 cat /tmp/telemetry.json

# Watch raw Gazebo bumper sensor directly
gz topic -e -t /world/ci_test_world/model/ci_agent_robot/link/base_link/sensor/bumper/contact

# Watch collision monitor node
ros2 run ci_agent_robot collision_monitor
```

---

## Regenerating the SDF from URDF

Whenever you change `robot.urdf.xacro` regenerate the SDF:

```bash
xacro /ros2_ws/src/ci_agent_robot/urdf/robot.urdf.xacro > /tmp/robot.urdf
gz sdf -p /tmp/robot.urdf > /ros2_ws/src/ci_agent_robot/urdf/robot.sdf
colcon build --packages-select ci_agent_robot
source install/setup.bash
```

---

## Testing the Agent Locally

```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Create a sample telemetry file
echo '{
  "collisions": 0,
  "avg_cpu": 55.0,
  "avg_ram_mb": 1800,
  "control_freq_hz": 60,
  "transform_tree_stable": true
}' > /tmp/telemetry.json

# Test constraint checker only
cd /ci-agent/agent
python3 constraint_checker.py

# Test full agent (constraint check + Claude reasoning)
python3 reason_act.py

# Test full pipeline including GitHub comment
python3 main.py /tmp/telemetry.json <PR_NUMBER>
```

---

## GitHub Secrets Required

Go to your repo → Settings → Secrets and variables → Actions:

| Secret | Value | Notes |
|--------|-------|-------|
| `ANTHROPIC_API_KEY` | Your key from console.anthropic.com | Required |
| `GITHUB_TOKEN` | Auto-provided | Do nothing, GitHub handles this |

---

## Things to Customize

| File | What to change |
|------|---------------|
| `sim/run_headless_sim.sh` | Replace `ci_agent_robot` and `sim.launch.py` with your actual package/launch file |
| `config/constraints.yaml` | Tune CPU, RAM, frequency and collision thresholds to your robot's specs |
| `.github/workflows/ci_agent.yml` | Change `branches: [main]` if your production branch has a different name |
| `.github/workflows/ci_agent.yml` | Change `runs-on: ubuntu-latest` to `ubuntu-24.04` for Jazzy compatibility |
| `ci_agent_robot/telemetry_recorder.py` | Replace topic names if your robot uses different ones |

---

## Constraints Config Reference

```yaml
# config/constraints.yaml
max_collisions: 0               # any collision = fail
min_control_frequency_hz: 50    # robot must publish cmd_vel at >=50Hz
max_cpu_percent: 80             # must stay under 80% CPU usage
max_ram_mb: 2048                # must stay under 2GB RAM
transform_tree_stable: true     # ROS TF tree must be publishing
borderline_threshold_percent: 10 # within 10% of any limit = flag for human review
```

---

## Telemetry JSON Format

The simulation must write this file to `/tmp/telemetry.json`:

```json
{
  "collisions": 0,
  "avg_cpu": 55.0,
  "avg_ram_mb": 1800,
  "control_freq_hz": 60.0,
  "transform_tree_stable": true
}
```

---

## Progress Log

### Session 1 — Architecture & Agent Code
- ✅ Designed agent architecture and CI pipeline
- ✅ Created ci-agent project structure
- ✅ Written all agent Python files (constraint_checker, reason_act, github_reporter, main)
- ✅ Created GitHub Actions workflow
- ✅ Set up constraints.yaml

### Session 2 — Environment Setup
- ✅ Decided on Docker over native WSL due to Frappe/mysql conflict
- ✅ Built ci_agent_ros Docker image with ROS 2 Jazzy + Gazebo Harmonic
- ✅ Created persistent ci_agent_dev container with volume mounts
- ✅ Created dev.sh helper script for one-command container entry
- ✅ Set up VS Code → WSL → Docker workflow for editing files
- ✅ Fixed file permission issues (chown ros_ws and ci-agent)
- ❌ WSL native ROS 2 broken due to libmysqlclient-dev conflict from Frappe install
- ℹ️ Root cause: Frappe installed directly in WSL pulled in libmysqlclient-dev which conflicts with libmariadb-dev required by Gazebo
- ℹ️ Resolution: all ROS 2 work happens inside Docker, Frappe stays in WSL untouched

### Session 3 — Robot Package & Simulation
- ✅ Created ci_agent_robot ROS 2 package via ros2 pkg create
- ✅ Written URDF with diff drive robot, wheels, caster, named collisions
- ✅ Written test_world.sdf with walled arena and required plugins
- ✅ Written gz_bridge.yaml for topic bridging
- ✅ Written patrol_node.py (drives robot at 50Hz forward/turn pattern)
- ✅ Written telemetry_recorder.py
- ✅ Written collision_monitor.py
- ✅ Gazebo world spawns correctly with headless server mode
- ✅ Fixed robot spawn issue — added UserCommands plugin to world SDF
- ✅ Fixed Gazebo GUI mode issue — switched to ExecuteProcess with -s -r flags
- ✅ ROS 2 bridge connects correctly (cmd_vel, odom, tf, clock)
- ✅ Converted URDF to SDF via gz sdf -p for reliable sensor loading
- ✅ Bumper sensor topic exists in Gazebo topic list
- ✅ Bridge subscribes to bumper contact topic correctly
- ❌ Bumper contact sensor has no publishers — topic exists but sensor not publishing
- ⏳ IN PROGRESS: Contact sensor publisher issue under investigation

### Known Issues

**Contact sensor not publishing**
The bumper sensor topic `/world/ci_test_world/model/ci_agent_robot/link/base_link/sensor/bumper/contact` exists and has bridge subscribers but has no publishers. The sensor was confirmed to receive data briefly (background gz echo processes exited with Done after collisions) but does not publish continuously. Likely a Gazebo Harmonic contact sensor configuration issue with the converted SDF format.

**GUI not tested**
VcXsrv display forwarding configured but Gazebo GUI not yet verified working through Docker + VcXsrv.

### Next Steps
- [ ] Fix contact sensor publisher issue
- [ ] Test full telemetry recording (90s run + JSON output)
- [ ] Test constraint checker with real telemetry data
- [ ] Test Claude API reasoning layer locally
- [ ] Uncomment patrol_node and telemetry_recorder in launch file
- [ ] Push both repos to GitHub
- [ ] Test full CI pipeline on a real PR

---

## Troubleshooting

**`gz: command not found` inside container**
```bash
apt-get update && apt-get install -y ros-jazzy-ros-gz
```

**Robot not spawning — waiting for /world/.../create service**
Make sure `gz-sim-user-commands-system` plugin is in your world SDF:
```xml
<plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
```

**Gazebo launches in GUI mode instead of headless**
Use `ExecuteProcess` instead of `IncludeLaunchDescription` for Gazebo:
```python
from launch.actions import ExecuteProcess
gazebo_launch = ExecuteProcess(
    cmd=['gz', 'sim', '-s', '-r', '-v4', world_path],
    output='screen'
)
```

**Contact sensor has no publishers**
Convert URDF to SDF and spawn from SDF file directly:
```bash
xacro robot.urdf.xacro > /tmp/robot.urdf
gz sdf -p /tmp/robot.urdf > robot.sdf
```
Then spawn using `-file robot.sdf` instead of `-topic /robot_description`.

**apt mysql/mariadb conflict in Docker build**
The Dockerfile already handles this with `/etc/apt/preferences.d/block-mysql`.
This conflict originated from Frappe being installed directly in WSL.
Long term fix: run Frappe in Docker too using https://github.com/frappe/frappe_docker

**Docker permission denied**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**VS Code cannot save files**
```bash
sudo chown -R $USER:$USER ~/ros_ws
sudo chown -R $USER:$USER ~/ci-agent
```

**colcon build fails**
```bash
source /opt/ros/jazzy/setup.bash
cd /ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select ci_agent_robot
```

**OCI runtime exec failed / container working directory error**
Container working directory no longer exists after deleting a folder. Recreate:
```bash
docker rm ci_agent_dev
~/ci-agent/dev.sh
``` 