"""
robot_full.launch.py
Lanza en un solo comando:
  1. micro-ROS Agent (contenedor Docker) — escucha UDP en el puerto 8888
  2. robot_state_publisher   — publica el modelo URDF
  3. odom_node               — odometría desde encoders + IMU
  4. imu_bridge_node         — puente de datos IMU
  5. RViz2                   — visualización con la config robot.rviz

Uso (no requiere source del workspace local):
  source /opt/ros/jazzy/setup.bash
  source ~/Roboticaclase/robotica2parcial/2do-parcdial-Robotica/Ejer_1/install/setup.bash
  export ROS_DOMAIN_ID=69
  ros2 launch ~/Roboticaclase/robotica2parcial/2do-parcdial-Robotica/Ejer_1/launch/robot_full.launch.py
"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node

# Ruta base absoluta del paquete my_robot_viz dentro del proyecto
_EJER1_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PKG_DIR   = os.path.join(_EJER1_DIR, 'my_robot_viz')

URDF_FILE = os.path.join(_PKG_DIR, 'urdf', 'autitorobotica.urdf')
RVIZ_FILE = os.path.join(_PKG_DIR, 'rviz', 'robot.rviz')


def generate_launch_description():
    with open(URDF_FILE, 'r') as f:
        robot_description = f.read()

    # ── 1. micro-ROS Agent via Docker ──────────────────────────────────────
    micro_ros_agent = ExecuteProcess(
        cmd=[
            'docker', 'run', '--rm',
            '--network', 'host',
            '-e', 'ROS_DOMAIN_ID=69',
            'microros/micro-ros-agent:jazzy',
            'udp4', '--port', '8888'
        ],
        name='micro_ros_agent_docker',
        output='screen',
    )

    # ── 2. robot_state_publisher ────────────────────────────────────────────
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen',
    )

    # ── 3. odom_node ────────────────────────────────────────────────────────
    odom_node = Node(
        package='my_robot_viz',
        executable='odom_node',
        name='odom_node',
        output='screen',
    )

    # ── 4. imu_bridge_node ──────────────────────────────────────────────────
    imu_bridge_node = Node(
        package='my_robot_viz',
        executable='imu_bridge_node',
        name='imu_bridge_node',
        output='screen',
    )

    # ── 5. RViz2 (delay de 3s para que los nodos arranquen primero) ─────────
    rviz = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                arguments=['-d', RVIZ_FILE],
                output='screen',
            )
        ]
    )

    return LaunchDescription([
        micro_ros_agent,
        robot_state_publisher,
        odom_node,
        imu_bridge_node,
        rviz,
    ])
