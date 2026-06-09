# launch/visualize.launch.py
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg = get_package_share_directory('my_robot_viz')

    urdf_file = os.path.join(pkg, 'urdf', 'autitorobotica.urdf')

    rviz_file = os.path.join(pkg, 'rviz', 'robot.rviz')

    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    return LaunchDescription([

        # Publica el modelo URDF
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),



        # Odometría desde cmd_vel
        Node(
            package='my_robot_viz',
            executable='odom_node',
            output='screen',
        ),

        # Puente IMU
        Node(
            package='my_robot_viz',
            executable='imu_bridge_node',
            output='screen',
        ),

        # RViz2
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_file],
            output='screen',
        ),
    ])