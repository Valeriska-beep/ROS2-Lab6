#!/usr/bin/env bash
# Запуск трьох нод із записом логів у ../logs. Зупинка: Ctrl+C.
source /opt/ros/${ROS_DISTRO:-humble}/setup.bash
cd "$(dirname "$0")"
mkdir -p ../logs
python3 sensor_node.py    2>&1 | tee ../logs/sensor.log    &
python3 heartbeat_node.py 2>&1 | tee ../logs/heartbeat.log &
python3 monitor_node.py   2>&1 | tee ../logs/monitor.log   &
trap 'kill $(jobs -p)' INT TERM
wait
