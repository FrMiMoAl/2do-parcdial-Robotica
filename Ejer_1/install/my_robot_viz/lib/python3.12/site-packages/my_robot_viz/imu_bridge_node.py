"""
imu_bridge_node.py
──────────────────
Convierte el yaw del IMU publicado por la ESP32 como Float32 (grados)
en un mensaje estándar sensor_msgs/Imu para que RViz pueda visualizarlo.

Tópicos:
  Suscribe : /imu_yaw      (std_msgs/Float32) — yaw en GRADOS desde ESP32
  Publica  : /imu/data     (sensor_msgs/Imu)  — orientación completa
"""

import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from sensor_msgs.msg import Imu


class ImuBridgeNode(Node):
    def __init__(self):
        super().__init__('imu_bridge_node')

        # Suscribirse al yaw en grados publicado por la ESP32
        self.yaw_sub = self.create_subscription(
            Float32,
            '/imu_yaw',
            self.imu_yaw_callback,
            10
        )

        # Publicar un Imu estándar para RViz
        self.imu_pub = self.create_publisher(Imu, '/imu/data', 10)

        self.get_logger().info('✅ IMU Bridge Node iniciado')
        self.get_logger().info('   /imu_yaw (Float32°) → /imu/data (sensor_msgs/Imu)')

    def imu_yaw_callback(self, msg: Float32):
        """Convierte yaw en grados a quaternión y publica sensor_msgs/Imu."""
        yaw_deg = msg.data
        yaw_rad = math.radians(yaw_deg)

        # Quaternión solo con rotación en Z (yaw)
        q_z = math.sin(yaw_rad / 2.0)
        q_w = math.cos(yaw_rad / 2.0)

        imu_msg = Imu()
        imu_msg.header.stamp    = self.get_clock().now().to_msg()
        imu_msg.header.frame_id = 'base_link'

        # Orientación calculada desde el yaw del gyro
        imu_msg.orientation.x = 0.0
        imu_msg.orientation.y = 0.0
        imu_msg.orientation.z = q_z
        imu_msg.orientation.w = q_w

        # Covarianza: -1 → campo no disponible; 0 en diagonal → confianza perfecta
        # Usamos covarianza diagonal pequeña para la orientación (solo yaw es bueno)
        cov = [0.0] * 9
        cov[0] = 1e6   # roll  — no disponible (valor alto = poca confianza)
        cov[4] = 1e6   # pitch — no disponible
        cov[8] = 0.01  # yaw   — dato confiable del gyro
        imu_msg.orientation_covariance = cov

        # Velocidad angular y aceleración no disponibles → covarianza -1
        imu_msg.angular_velocity_covariance[0]    = -1.0
        imu_msg.linear_acceleration_covariance[0] = -1.0

        self.imu_pub.publish(imu_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ImuBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
