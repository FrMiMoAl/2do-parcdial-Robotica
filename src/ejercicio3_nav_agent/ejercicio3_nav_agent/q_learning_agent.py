import rclpy
from rclpy.node import Node

from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_srvs.srv import Empty
from rclpy.qos import qos_profile_sensor_data

import math
import random
import csv
import json
import os


class QLearningNavigationAgent(Node):
    def __init__(self):
        super().__init__('q_learning_navigation_agent')

        # Parámetros ROS
        self.declare_parameter('scan_topic', '/base_scan')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('cmd_topic', '/cmd_vel')
        self.declare_parameter('reset_service', '/reset_positions')

        self.declare_parameter('mode', 'train')  # train o test
        self.declare_parameter('episodes', 30)
        self.declare_parameter('max_steps', 120)
        self.declare_parameter('epsilon', 0.40)

        self.scan_topic = self.get_parameter('scan_topic').value
        self.odom_topic = self.get_parameter('odom_topic').value
        self.cmd_topic = self.get_parameter('cmd_topic').value
        self.reset_service_name = self.get_parameter('reset_service').value

        self.mode = self.get_parameter('mode').value
        self.max_episodes = int(self.get_parameter('episodes').value)
        self.max_steps = int(self.get_parameter('max_steps').value)
        self.epsilon = float(self.get_parameter('epsilon').value)

        self.alpha = 0.20
        self.gamma = 0.90
        self.epsilon_decay = 0.96
        self.min_epsilon = 0.05

        # Archivos
        self.results_dir = os.path.expanduser('~/stage_ws/results')
        os.makedirs(self.results_dir, exist_ok=True)

        self.log_path = os.path.join(self.results_dir, 'training_log.csv')
        self.q_table_path = os.path.join(self.results_dir, 'q_table.json')

        # Datos ROS
        self.scan = None
        self.odom = None

        self.cmd_pub = self.create_publisher(Twist, self.cmd_topic, 10)

        self.create_subscription(
            LaserScan,
            self.scan_topic,
            self.scan_callback,
            qos_profile_sensor_data
        )

        self.create_subscription(
            Odometry,
            self.odom_topic,
            self.odom_callback,
            10
        )

        self.reset_client = self.create_client(Empty, self.reset_service_name)

        # Acciones discretas: linear.x, angular.z
        self.actions = [
            (0.35, 0.00),    # avanzar
            (0.15, 0.70),    # avanzar girando izquierda
            (0.15, -0.70),   # avanzar girando derecha
            (0.00, 0.90),    # girar izquierda
            (0.00, -0.90),   # girar derecha
            (0.15, 0.00),    # avanzar lento
        ]

        # Metas válidas aproximadas del mundo cave
        self.goal_candidates = [
            (-6.0, -5.0),
            (-5.0, -3.5),
            (-4.0, -6.0),
            (-3.5, -4.5),
            (-6.5, -4.0),
        ]

        self.q_table = {}

        if os.path.exists(self.q_table_path):
            try:
                with open(self.q_table_path, 'r') as f:
                    self.q_table = json.load(f)
                self.get_logger().info('Q-table cargada.')
            except Exception:
                self.get_logger().warn('No se pudo cargar q_table.json. Se inicia desde cero.')

        self.prepare_csv()

        self.current_episode = 0
        self.step = 0
        self.episode_reward = 0.0

        self.goal_x = 0.0
        self.goal_y = 0.0

        self.prev_state = None
        self.prev_action = None
        self.prev_distance = None
        self.prev_angular_sign = 0

        self.finished = False

        self.timer = self.create_timer(0.10, self.control_loop)

        self.get_logger().info('Agente Q-learning iniciado.')
        self.get_logger().info(f'Modo: {self.mode}')
        self.get_logger().info(f'Scan: {self.scan_topic}, Odom: {self.odom_topic}, Cmd: {self.cmd_topic}')

    def prepare_csv(self):
        file_exists = os.path.exists(self.log_path)

        self.csv_file = open(self.log_path, 'a', newline='')
        self.csv_writer = csv.writer(self.csv_file)

        if not file_exists or os.path.getsize(self.log_path) == 0:
            self.csv_writer.writerow([
                'mode',
                'episode',
                'reward',
                'steps',
                'success',
                'collision',
                'goal_x',
                'goal_y',
                'epsilon'
            ])
            self.csv_file.flush()

    def scan_callback(self, msg):
        self.scan = msg

    def odom_callback(self, msg):
        self.odom = msg

    def reset_simulation(self):
        if self.reset_client.wait_for_service(timeout_sec=0.5):
            req = Empty.Request()
            self.reset_client.call_async(req)
        else:
            self.get_logger().warn(f'Servicio {self.reset_service_name} no disponible.')

    def start_episode(self):
        self.current_episode += 1
        self.step = 0
        self.episode_reward = 0.0

        self.goal_x, self.goal_y = random.choice(self.goal_candidates)

        self.prev_state = None
        self.prev_action = None
        self.prev_distance = None
        self.prev_angular_sign = 0

        self.stop_robot()
        self.reset_simulation()

        self.get_logger().info(
            f'Episodio {self.current_episode}/{self.max_episodes} | '
            f'Meta: ({self.goal_x:.2f}, {self.goal_y:.2f}) | '
            f'Epsilon: {self.epsilon:.2f}'
        )

    def control_loop(self):
        if self.finished:
            return

        if self.scan is None or self.odom is None:
            return

        if self.current_episode == 0:
            self.start_episode()
            return

        state, distance, angle_error, min_front, min_all = self.get_state()

        reward = 0.0
        success = False
        collision = False
        done = False

        if self.prev_distance is not None:
            progress = self.prev_distance - distance
            reward += 8.0 * progress

            # Penalización por tiempo
            reward -= 0.02

            # Premia si mira hacia la meta
            if abs(angle_error) < 0.40:
                reward += 0.04

            # Penaliza cercanía a obstáculos
            if min_front < 0.50:
                reward -= 0.20

            # Penaliza oscilación de giro
            current_angular_sign = self.get_angular_sign_from_action(self.prev_action)
            if current_angular_sign != 0 and self.prev_angular_sign != 0:
                if current_angular_sign != self.prev_angular_sign:
                    reward -= 0.10
            self.prev_angular_sign = current_angular_sign

        if distance < 0.35:
            reward += 15.0
            success = True
            done = True

        if min_all < 0.18:
            reward -= 15.0
            collision = True
            done = True

        if self.step >= self.max_steps:
            done = True

        self.episode_reward += reward

        if self.prev_state is not None and self.prev_action is not None:
            self.update_q_table(
                self.prev_state,
                self.prev_action,
                reward,
                state,
                done
            )

        if done:
            self.end_episode(success, collision)
            return

        action = self.choose_action(state)
        self.publish_action(action)

        self.prev_state = state
        self.prev_action = action
        self.prev_distance = distance

        self.step += 1

    def end_episode(self, success, collision):
        self.stop_robot()

        self.csv_writer.writerow([
            self.mode,
            self.current_episode,
            round(self.episode_reward, 4),
            self.step,
            int(success),
            int(collision),
            round(self.goal_x, 3),
            round(self.goal_y, 3),
            round(self.epsilon, 4)
        ])
        self.csv_file.flush()

        self.get_logger().info(
            f'Fin episodio {self.current_episode} | '
            f'Reward: {self.episode_reward:.2f} | '
            f'Pasos: {self.step} | '
            f'Éxito: {success} | '
            f'Colisión: {collision}'
        )

        if self.mode == 'train':
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
            self.save_q_table()

        if self.current_episode >= self.max_episodes:
            self.finish_training()
        else:
            self.start_episode()

    def finish_training(self):
        self.stop_robot()
        self.save_q_table()
        self.finished = True
        self.get_logger().info('Entrenamiento/prueba finalizado.')
        self.get_logger().info(f'CSV guardado en: {self.log_path}')
        self.get_logger().info(f'Q-table guardada en: {self.q_table_path}')
        self.get_logger().info('Puedes cerrar con Ctrl+C.')

    def save_q_table(self):
        with open(self.q_table_path, 'w') as f:
            json.dump(self.q_table, f, indent=2)

    def choose_action(self, state):
        key = str(state)

        if key not in self.q_table:
            self.q_table[key] = [0.0 for _ in self.actions]

        if self.mode == 'train' and random.random() < self.epsilon:
            return random.randint(0, len(self.actions) - 1)

        q_values = self.q_table[key]
        return int(max(range(len(q_values)), key=lambda i: q_values[i]))

    def update_q_table(self, state, action, reward, next_state, done):
        if self.mode != 'train':
            return

        state_key = str(state)
        next_key = str(next_state)

        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0 for _ in self.actions]

        if next_key not in self.q_table:
            self.q_table[next_key] = [0.0 for _ in self.actions]

        old_value = self.q_table[state_key][action]

        if done:
            target = reward
        else:
            target = reward + self.gamma * max(self.q_table[next_key])

        new_value = old_value + self.alpha * (target - old_value)
        self.q_table[state_key][action] = new_value

    def publish_action(self, action_index):
        linear_x, angular_z = self.actions[action_index]

        cmd = Twist()
        cmd.linear.x = float(linear_x)
        cmd.angular.z = float(angular_z)

        self.cmd_pub.publish(cmd)

    def stop_robot(self):
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.cmd_pub.publish(cmd)

    def get_state(self):
        ranges = self.clean_scan_ranges()

        n = len(ranges)
        right_sector = ranges[0:n // 3]
        front_sector = ranges[n // 3:2 * n // 3]
        left_sector = ranges[2 * n // 3:n]

        min_right = min(right_sector)
        min_front = min(front_sector)
        min_left = min(left_sector)
        min_all = min(ranges)

        x, y, yaw = self.get_robot_pose()

        dx = self.goal_x - x
        dy = self.goal_y - y

        distance = math.sqrt(dx * dx + dy * dy)
        target_angle = math.atan2(dy, dx)
        angle_error = self.normalize_angle(target_angle - yaw)

        front_bin = self.distance_bin(min_front)
        left_bin = self.distance_bin(min_left)
        right_bin = self.distance_bin(min_right)
        goal_distance_bin = self.goal_distance_bin(distance)
        goal_angle_bin = self.angle_bin(angle_error)

        state = (
            front_bin,
            left_bin,
            right_bin,
            goal_distance_bin,
            goal_angle_bin
        )

        return state, distance, angle_error, min_front, min_all

    def clean_scan_ranges(self):
        max_range = self.scan.range_max
        clean = []

        for r in self.scan.ranges:
            if math.isnan(r) or math.isinf(r):
                clean.append(max_range)
            else:
                clean.append(max(0.0, min(r, max_range)))

        return clean

    def get_robot_pose(self):
        x = self.odom.pose.pose.position.x
        y = self.odom.pose.pose.position.y

        q = self.odom.pose.pose.orientation
        yaw = self.yaw_from_quaternion(q)

        return x, y, yaw

    def yaw_from_quaternion(self, q):
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def normalize_angle(self, angle):
        return (angle + math.pi) % (2.0 * math.pi) - math.pi

    def distance_bin(self, d):
        if d < 0.35:
            return 0
        elif d < 0.70:
            return 1
        else:
            return 2

    def goal_distance_bin(self, d):
        if d < 0.50:
            return 0
        elif d < 1.50:
            return 1
        elif d < 3.00:
            return 2
        else:
            return 3

    def angle_bin(self, angle):
        if angle < -1.20:
            return 0
        elif angle < -0.40:
            return 1
        elif angle < 0.40:
            return 2
        elif angle < 1.20:
            return 3
        else:
            return 4

    def get_angular_sign_from_action(self, action_index):
        if action_index is None:
            return 0

        angular_z = self.actions[action_index][1]

        if angular_z > 0.05:
            return 1
        elif angular_z < -0.05:
            return -1
        else:
            return 0


def main(args=None):
    rclpy.init(args=args)
    node = QLearningNavigationAgent()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.stop_robot()
    node.save_q_table()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
