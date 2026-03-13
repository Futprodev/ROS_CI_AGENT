#!/bin/bash
# Requires ROS 2 sourced before running
source /opt/ros/jazzy/setup.bash
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &

# don't forget the name for the pkg and launch file
echo "Launching headless simulation..."
timeout 120 ros2 launch ci_agent_robot sim.launch.py \ 
  --ros-args -p headless:=true \
  2>&1 | tee /tmp/sim_output.log

echo "Simulation complete."
