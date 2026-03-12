#!/bin/bash
# Usage: ./dev.sh         → enter container
#        ./dev.sh build   → rebuild image

HOST_IP=$(ip route | grep default | awk '{print $3}')

if [ "$1" == "build" ]; then
    echo "Building ci_agent_ros image..."
    docker build -t ci_agent_ros:latest ~/ci-agent/
    exit 0
fi

# Start container if not running
if [ "$(docker inspect -f '{{.State.Running}}' ci_agent_dev 2>/dev/null)" != "true" ]; then
    echo "Starting ci_agent_dev..."
    docker start ci_agent_dev 2>/dev/null || docker run -it \
        --name ci_agent_dev \
        -v ~/ros2_ws:/ros2_ws \
        -v ~/ci-agent:/ci-agent \
        -e DISPLAY=$HOST_IP:0.0 \
        -e LIBGL_ALWAYS_INDIRECT=0 \
        -e QT_X11_NO_MITSHM=1 \
        ci_agent_ros:latest \
        bash
fi

docker exec -it ci_agent_dev bash
