import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
import math


class SimpleAgent(Node):
    def __init__(self):
        super().__init__('simple_agent')

        self.scan = None
        self.odom = None

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.create_subscription(
            LaserScan,
            '/base_scan',
            self.scan_callback,
            10
        )

        self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info('Simple navigation agent started.')

    def scan_callback(self, msg):
        self.scan = msg

    def odom_callback(self, msg):
        self.odom = msg

    def control_loop(self):
        if self.scan is None:
            return

        ranges = list(self.scan.ranges)
        valid_ranges = [
            r for r in ranges
            if not math.isinf(r) and not math.isnan(r)
        ]

        if len(valid_ranges) == 0:
            return

        front = min(valid_ranges[len(valid_ranges)//3: 2*len(valid_ranges)//3])

        cmd = Twist()

        if front < 0.7:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.6
        else:
            cmd.linear.x = 0.3
            cmd.angular.z = 0.0

        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = SimpleAgent()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
