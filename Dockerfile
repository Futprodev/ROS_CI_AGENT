FROM osrf/ros:jazzy-desktop

# Block mysql dev packages that conflict with mariadb
RUN echo "Package: libmysqlclient-dev" >> /etc/apt/preferences.d/block-mysql && \
    echo "Pin: release *" >> /etc/apt/preferences.d/block-mysql && \
    echo "Pin-Priority: -1" >> /etc/apt/preferences.d/block-mysql && \
    echo "" >> /etc/apt/preferences.d/block-mysql && \
    echo "Package: default-libmysqlclient-dev" >> /etc/apt/preferences.d/block-mysql && \
    echo "Pin: release *" >> /etc/apt/preferences.d/block-mysql && \
    echo "Pin-Priority: -1" >> /etc/apt/preferences.d/block-mysql && \
    echo "" >> /etc/apt/preferences.d/block-mysql && \
    echo "Package: libgdal-dev" >> /etc/apt/preferences.d/block-mysql && \
    echo "Pin: release *" >> /etc/apt/preferences.d/block-mysql && \
    echo "Pin-Priority: -1" >> /etc/apt/preferences.d/block-mysql && \
    echo "" >> /etc/apt/preferences.d/block-mysql && \
    echo "Package: libgz-common5-geospatial-dev" >> /etc/apt/preferences.d/block-mysql && \
    echo "Pin: release *" >> /etc/apt/preferences.d/block-mysql && \
    echo "Pin-Priority: -1" >> /etc/apt/preferences.d/block-mysql

# Install everything needed for the project
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-interfaces \
    ros-jazzy-ros-gz-sim \
    python3-pip \
    xvfb \
    x11-utils \
    mesa-utils \
    libgl1-mesa-dri \
    xdg-utils \
    && pip3 install psutil anthropic requests pyyaml --break-system-packages \
    && rm -rf /var/lib/apt/lists/*

# Auto source ROS every time container starts
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
RUN echo "source /ros2_ws/install/setup.bash 2>/dev/null || true" >> ~/.bashrc

WORKDIR /ros2_ws
