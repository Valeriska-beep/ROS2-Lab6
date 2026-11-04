"""Запуск усієї системи: ros2 launch launch/system.launch.py (з каталогу code/)."""
import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_launch_description():
    nodes = ['sensor_node.py', 'heartbeat_node.py', 'monitor_node.py']
    return LaunchDescription([
        ExecuteProcess(cmd=['python3', os.path.join(BASE, n)], output='screen')
        for n in nodes
    ])
