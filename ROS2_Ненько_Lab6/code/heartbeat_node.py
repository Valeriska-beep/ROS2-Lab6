#!/usr/bin/env python3
"""Heartbeat Node: щосекунди публікує сигнал активності в /heartbeat (std_msgs/String)."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

HEARTBEAT_TOPIC = '/heartbeat'
HEARTBEAT_PERIOD = 1.0        # с


class HeartbeatNode(Node):
    def __init__(self):
        super().__init__('heartbeat_node')
        self.publisher = self.create_publisher(String, HEARTBEAT_TOPIC, 10)
        self.timer = self.create_timer(HEARTBEAT_PERIOD, self.beat)
        self.seq = 0
        self.get_logger().info(
            f'Heartbeat node started: topic={HEARTBEAT_TOPIC}, period={HEARTBEAT_PERIOD}s')

    def beat(self):
        self.seq += 1
        msg = String()
        msg.data = f'alive #{self.seq}'
        self.publisher.publish(msg)
        self.get_logger().info(f'Heartbeat sent: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = HeartbeatNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Heartbeat node stopped by user')
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
