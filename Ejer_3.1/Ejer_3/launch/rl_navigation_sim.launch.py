import os
from launch import LaunchDescription
from launch.actions import LogInfo


def generate_launch_description():
    '''
    Launch placeholder para ROS 2 Jazzy - Ejercicio 3 RL Navigation.

    Para convertir esto de un mock a un entrenamiento real en Gazebo, falta:
    1. Incluir el launch de Gazebo Sim (gz_sim) o Classic (gazebo_ros).
    2. Integrar robot_state_publisher con el URDF/Xacro del robot.
    3. Integrar spawn_entity para instanciar el robot en Gazebo.
    4. Integrar RViz2 para visualización.
    5. Lanzar el nodo de ROS 2 que contiene el agente RL que publica en /cmd_vel y se suscribe a /scan y /odom.

    NOTA: No se usan nodos talker/listener ni py_pubsub genéricos.
    Este archivo está reservado para la integración completa del entorno.
    '''
    return LaunchDescription([
        LogInfo(msg="Launch placeholder para Ejercicio 3. Falta integrar Gazebo, robot_state_publisher, spawn_entity, RViz2 y el nodo RL.")
    ])
