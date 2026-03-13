#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source /home/runner/work/ROS_CI_AGENT/ROS_CI_AGENT/ros_ws/install/setup.bash

export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
sleep 2

echo "Launching headless simulation..."
timeout 100 ros2 launch ci_agent_robot sim.launch.py \
  2>&1 | tee /tmp/sim_output.log || true

echo "Simulation complete."

# Verify telemetry
if [ ! -f /tmp/telemetry.json ]; then
  echo "ERROR: telemetry.json was not written"
  cat /tmp/sim_output.log
  exit 1
fi

echo "Telemetry written:"
cat /tmp/telemetry.json