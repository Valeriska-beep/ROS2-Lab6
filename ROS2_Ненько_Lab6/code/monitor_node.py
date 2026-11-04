#!/usr/bin/env python3
"""Monitor Node: стежить за /heartbeat та /sensor_data і оцінює стабільність системи."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String

HEARTBEAT_TOPIC = '/heartbeat'
SENSOR_TOPIC = '/sensor_data'
CHECK_PERIOD = 1.0            # с
WARN_TIMEOUT = 2.5            # с без heartbeat -> WARN
ERROR_TIMEOUT = 5.0           # с без heartbeat -> ERROR


class MonitorNode(Node):
    def __init__(self):
        super().__init__('monitor_node')
        self.create_subscription(String, HEARTBEAT_TOPIC, self.on_heartbeat, 10)
        self.create_subscription(Float32, SENSOR_TOPIC, self.on_sensor, 10)
        self.create_timer(CHECK_PERIOD, self.check)
        now = self.get_clock().now()
        self.last_heartbeat = now
        self.last_sensor = now
        self.get_logger().info('Monitor node started')

    def on_heartbeat(self, msg):
        self.last_heartbeat = self.get_clock().now()
        self.get_logger().debug(f'Heartbeat received: {msg.data}')

    def on_sensor(self, msg):
        self.last_sensor = self.get_clock().now()
        self.get_logger().info(f'Sensor data received: {msg.data:.2f}')

    def age(self, stamp):
        return (self.get_clock().now() - stamp).nanoseconds / 1e9

    def check(self):
        hb_age = self.age(self.last_heartbeat)
        sensor_age = self.age(self.last_sensor)

        if hb_age > ERROR_TIMEOUT:
            self.get_logger().error(
                f'Heartbeat lost for {hb_age:.1f}s: node is not working')
        elif hb_age > WARN_TIMEOUT:
            self.get_logger().warn(f'Heartbeat delayed: {hb_age:.1f}s')
        elif sensor_age > WARN_TIMEOUT:
            self.get_logger().warn(f'No sensor data for {sensor_age:.1f}s')
        else:
            self.get_logger().info('System status: STABLE')


def main(args=None):
    rclpy.init(args=args)
    node = MonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Monitor node stopped by user')
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
