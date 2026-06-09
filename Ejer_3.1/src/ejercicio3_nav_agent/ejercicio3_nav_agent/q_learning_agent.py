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
        self.declare_parameter('episodes', 300)
        self.declare_parameter('max_steps', 500)
        self.declare_parameter('epsilon', 1.0)

        # Semilla aleatoria fija para reproducibilidad
        self.declare_parameter('random_seed', 42)
        # Evaluaciones intermedias cada N episodios de entrenamiento
        self.declare_parameter('eval_interval', 20)
        # Número de episodios por ronda de evaluación
        self.declare_parameter('eval_episodes', 5)
        # Parada temprana: si no mejora en 'patience' rondas de eval, detener
        self.declare_parameter('patience', 5)

        self.scan_topic = self.get_parameter('scan_topic').value
        self.odom_topic = self.get_parameter('odom_topic').value
        self.cmd_topic = self.get_parameter('cmd_topic').value
        self.reset_service_name = self.get_parameter('reset_service').value

        self.mode = self.get_parameter('mode').value
        self.max_episodes = int(self.get_parameter('episodes').value)
        self.max_steps = int(self.get_parameter('max_steps').value)
        self.epsilon = float(self.get_parameter('epsilon').value)

        self.random_seed = int(self.get_parameter('random_seed').value)
        self.eval_interval = int(self.get_parameter('eval_interval').value)
        self.eval_episodes_count = int(self.get_parameter('eval_episodes').value)
        self.patience = int(self.get_parameter('patience').value)

        # Fijar semilla para reproducibilidad de entrenamiento
        random.seed(self.random_seed)

        self.alpha = 0.20
        self.gamma = 0.95
        self.epsilon_decay = 0.995
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
            (0.30, 0.00),    # avanzar rápido
            (0.20, 0.50),    # avanzar girando izquierda
            (0.20, -0.50),   # avanzar girando derecha
            (0.00, 0.80),    # girar izquierda en sitio
            (0.00, -0.80),   # girar derecha en sitio
            (0.15, 0.00),    # avanzar lento
            (0.10, 1.20),    # giro cerrado izquierda
            (0.10, -1.20),   # giro cerrado derecha
        ]

        # Metas aleatorias en zonas válidas (espacios abiertos) del mundo cave
        # Verificadas contra el mapa cave.png (16×16m centrado en origen)
        self.goal_candidates = [
            (5.0, 4.0),      # posición del bloque verde (esquina superior derecha)
            (0.0, 1.0),      # corredor central
            (-3.0, 3.5),     # zona abierta superior izquierda
            (3.0, -1.0),     # corredor derecho central
            (-5.0, -3.0),    # zona abierta izquierda
            (6.0, -6.0),     # esquina inferior derecha
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
        self.train_episode_count = 0
        self.step = 0
        self.episode_reward = 0.0

        self.goal_x = 0.0
        self.goal_y = 0.0

        self.prev_state = None
        self.prev_action = None
        self.prev_distance = None
        self.prev_angular_sign = 0

        self.finished = False

        # --- Evaluación intermedia y parada temprana ---
        self.in_eval_phase = False
        self.eval_phase_count = 0
        self.eval_phase_rewards = []
        self.best_eval_reward = -float('inf')
        self.no_improve_count = 0
        self.saved_epsilon = 0.0

        self.timer = self.create_timer(0.10, self.control_loop)

        self.get_logger().info('Agente Q-learning iniciado.')
        self.get_logger().info(f'Modo: {self.mode} | Semilla: {self.random_seed}')
        self.get_logger().info(f'Scan: {self.scan_topic}, Odom: {self.odom_topic}, Cmd: {self.cmd_topic}')
        self.get_logger().info(f'Eval cada {self.eval_interval} ep, {self.eval_episodes_count} ep/eval, patience={self.patience}')

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

        # Meta aleatoria dentro de las zonas válidas
        self.goal_x, self.goal_y = random.choice(self.goal_candidates)

        self.prev_state = None
        self.prev_action = None
        self.prev_distance = None
        self.prev_angular_sign = 0

        self.stop_robot()
        self.reset_simulation()

        phase_label = '[EVAL]' if self.in_eval_phase else '[TRAIN]'
        self.get_logger().info(
            f'{phase_label} Episodio {self.current_episode} '
            f'(train #{self.train_episode_count}) | '
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
            reward += 10.0 * progress  # más peso al progreso hacia la meta

            # Penalización por tiempo (incentiva rapidez)
            reward -= 0.05

            # Premia si mira hacia la meta
            if abs(angle_error) < 0.30:
                reward += 0.10
            elif abs(angle_error) < 0.60:
                reward += 0.03

            # Penaliza cercanía a obstáculos (gradual)
            if min_front < 0.35:
                reward -= 0.50
            elif min_front < 0.55:
                reward -= 0.20

            # Penalización por oscilación de giro:
            # Si el signo de angular.z cambia de un paso al siguiente
            # (ej: girar izquierda → girar derecha), se penaliza.
            # Esto castiga el comportamiento "zigzag" que no progresa.
            current_angular_sign = self.get_angular_sign_from_action(self.prev_action)
            if current_angular_sign != 0 and self.prev_angular_sign != 0:
                if current_angular_sign != self.prev_angular_sign:
                    reward -= 0.10  # penalización por oscilación
            self.prev_angular_sign = current_angular_sign

        if distance < 0.60 and self.step > 10:
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

        # Solo actualizar la Q-table durante entrenamiento (no en eval ni test)
        if not self.in_eval_phase and self.prev_state is not None and self.prev_action is not None:
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

        # SIN capa de seguridad: el agente debe aprender a evitar
        # paredes por sí mismo mediante la penalización de colisión (-15.0).
        # Esto permite un aprendizaje por refuerzo auténtico.

        self.publish_action(action)

        self.prev_state = state
        self.prev_action = action
        self.prev_distance = distance

        self.step += 1

    def end_episode(self, success, collision):
        self.stop_robot()

        # Determinar el modo actual para el CSV
        if self.in_eval_phase:
            csv_mode = 'eval'
        else:
            csv_mode = self.mode

        self.csv_writer.writerow([
            csv_mode,
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

        # --- Lógica de fase de evaluación intermedia ---
        if self.in_eval_phase:
            self.eval_phase_rewards.append(self.episode_reward)
            self.eval_phase_count += 1

            if self.eval_phase_count >= self.eval_episodes_count:
                self.end_eval_phase()
            else:
                self.start_episode()
            return

        # --- Lógica normal de entrenamiento ---
        if self.mode == 'train':
            self.train_episode_count += 1
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
            self.save_q_table()

            # Verificar si toca evaluación intermedia
            if self.train_episode_count % self.eval_interval == 0:
                self.start_eval_phase()
                return

        if self.train_episode_count >= self.max_episodes:
            self.finish_training()
        else:
            self.start_episode()

    # --- Evaluación intermedia ---

    def start_eval_phase(self):
        """Inicia una ronda de evaluación intermedia (N episodios con ε=0, sin actualizar Q-table)."""
        self.in_eval_phase = True
        self.eval_phase_count = 0
        self.eval_phase_rewards = []
        self.saved_epsilon = self.epsilon
        self.epsilon = 0.0  # política greedy pura durante evaluación

        eval_round = self.train_episode_count // self.eval_interval
        self.get_logger().info(
            f'=== INICIO EVALUACIÓN INTERMEDIA (ronda {eval_round}) ==='
        )
        self.start_episode()

    def end_eval_phase(self):
        """Finaliza la ronda de evaluación intermedia y verifica early stopping."""
        self.in_eval_phase = False
        self.epsilon = self.saved_epsilon  # restaurar epsilon de entrenamiento

        avg_eval_reward = sum(self.eval_phase_rewards) / len(self.eval_phase_rewards)
        eval_round = self.train_episode_count // self.eval_interval

        self.get_logger().info(
            f'=== FIN EVALUACIÓN (ronda {eval_round}) | '
            f'Reward promedio: {avg_eval_reward:.2f} | '
            f'Mejor: {self.best_eval_reward:.2f} ==='
        )

        # Verificar mejora para early stopping
        if avg_eval_reward > self.best_eval_reward:
            self.best_eval_reward = avg_eval_reward
            self.no_improve_count = 0
            self.save_q_table()
            self.get_logger().info('Nuevo mejor resultado de evaluación. Q-table guardada.')
        else:
            self.no_improve_count += 1
            self.get_logger().info(
                f'Sin mejora ({self.no_improve_count}/{self.patience})'
            )

        # Parada temprana
        if self.no_improve_count >= self.patience:
            self.get_logger().warn(
                f'PARADA TEMPRANA: sin mejora en {self.patience} rondas de evaluación consecutivas.'
            )
            self.finish_training()
            return

        if self.train_episode_count >= self.max_episodes:
            self.finish_training()
        else:
            self.start_episode()

    def finish_training(self):
        self.stop_robot()
        self.save_q_table()
        self.finished = True
        self.get_logger().info('Entrenamiento/prueba finalizado.')
        self.get_logger().info(f'Episodios de entrenamiento completados: {self.train_episode_count}')
        self.get_logger().info(f'CSV guardado en: {self.log_path}')
        self.get_logger().info(f'Q-table guardada en: {self.q_table_path}')
        self.get_logger().info('Puedes cerrar con Ctrl+C.')

    def save_q_table(self):
        with open(self.q_table_path, 'w') as f:
            json.dump(self.q_table, f, indent=2)

    def choose_action(self, state):
        key = str(state)

        # Si no existe o tiene tamaño incorrecto (q_table de versión anterior), reiniciar
        if key not in self.q_table or len(self.q_table[key]) != len(self.actions):
            self.q_table[key] = [0.0 for _ in self.actions]

        # Exploración ε-greedy (solo en entrenamiento, no en eval)
        if self.mode == 'train' and not self.in_eval_phase and random.random() < self.epsilon:
            return random.randint(0, len(self.actions) - 1)

        q_values = self.q_table[key]
        return int(max(range(len(q_values)), key=lambda i: q_values[i]))

    def update_q_table(self, state, action, reward, next_state, done):
        if self.mode != 'train':
            return

        state_key = str(state)
        next_key = str(next_state)

        # Validar tamaño (compatibilidad con q_tables de versiones anteriores)
        if state_key not in self.q_table or len(self.q_table[state_key]) != len(self.actions):
            self.q_table[state_key] = [0.0 for _ in self.actions]

        if next_key not in self.q_table or len(self.q_table[next_key]) != len(self.actions):
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
        # Stage lidar: 0° = frente, sentido antihorario
        # Dividimos en 5 sectores: frente-izq, izq, frente, der, frente-der
        front_idx = n // 2  # índice del frente (180°)
        # Sector frontal: ±30° alrededor del frente
        front_span = max(1, n // 12)
        left_span = n // 4

        front_indices = list(range(front_idx - front_span, front_idx + front_span))
        left_indices  = list(range(front_idx, front_idx + left_span))
        right_indices = list(range(front_idx - left_span, front_idx))

        # Clamping seguro
        front_sector = [ranges[i % n] for i in front_indices]
        left_sector  = [ranges[i % n] for i in left_indices]
        right_sector = [ranges[i % n] for i in right_indices]

        min_right = min(right_sector)
        min_front = min(front_sector)
        min_left  = min(left_sector)
        min_all   = min(ranges)

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
