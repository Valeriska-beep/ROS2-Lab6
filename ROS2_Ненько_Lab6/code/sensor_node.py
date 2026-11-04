#!/usr/bin/env python3
"""Sensor Node: імітує датчик температури та демонструє логування INFO / WARN / ERROR."""
import random

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

SENSOR_TOPIC = '/sensor_data'
PUBLISH_PERIOD = 0.5          # с
VALUE_MIN, VALUE_MAX = 18.0, 32.0
CONNECTION_LOSS_EVERY = 30    # кожен 30-й цикл імітуємо втрату зв'язку


class SensorNode(Node):
    def __init__(self):
        super().__init__('sensor_node')
        self.publisher = self.create_publisher(Float32, SENSOR_TOPIC, 10)
        self.timer = self.create_timer(PUBLISH_PERIOD, self.tick)
        self.count = 0
        self.get_logger().info('Sensor node started')            # запуск ноди

    def tick(self):
        self.count += 1

        if self.count % CONNECTION_LOSS_EVERY == 0:              # помилка
            self.get_logger().error('Connection lost: sensor is not responding')
            return

        value = random.gauss(25.0, 3.0)
        if value < VALUE_MIN or value > VALUE_MAX:               # попередження
            self.get_logger().warn(
                f'Sensor unstable: value={value:.2f} is out of range '
                f'[{VALUE_MIN}, {VALUE_MAX}]')

        msg = Float32()
        msg.data = float(value)
        self.publisher.publish(msg)
        self.get_logger().info(f'Published {SENSOR_TOPIC}: {value:.2f}')  # дані


def main(args=None):
    rclpy.init(args=args)
    node = SensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Sensor node stopped by user')
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
