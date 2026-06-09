"""
Entorno de navegación para Reinforcement Learning (Modo Mock).
Simula la interfaz de Gymnasium para entrenar agentes usando comandos de velocidad
continua y observaciones simuladas (LiDAR, odometría, etc.).
"""
import math
import numpy as np


class RLNavigationEnv:
    """
    Entorno simulado para navegación de robot diferencial.
    Calcula observaciones falsas y actualiza cinemática simple para pruebas.
    """
    def __init__(self, config):
        """Inicializa el entorno cargando los parámetros desde config."""
        self.config = config
        self.seed = int(config.get("seed", 42))
        np.random.seed(self.seed)
        self.lidar_num_beams = int(config.get("lidar_num_beams", 24))
        self.max_steps = int(config.get("max_steps_per_episode", 500))
        self.goal_tolerance = float(config.get("goal_tolerance", 0.30))
        self.collision_distance = float(config.get("collision_distance", 0.18))
        self.linear_min = float(config.get("linear_velocity_min", 0.0))
        self.linear_max = float(config.get("linear_velocity_max", 0.35))
        self.angular_min = float(config.get("angular_velocity_min", -1.0))
        self.angular_max = float(config.get("angular_velocity_max", 1.0))
        self.current_step = 0
        self.robot_pose = np.array([0.0, 0.0, 0.0])
        self.goal = np.array([2.0, 0.0])
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.lidar = np.ones(self.lidar_num_beams) * 3.5
        self.previous_distance = self._distance_to_goal()

    def reset(self, seed=None):
        """Reinicia el entorno al inicio de cada episodio."""
        if seed is not None:
            np.random.seed(seed)
        self.current_step = 0
        self.robot_pose = np.array([0.0, 0.0, 0.0])
        self.goal = np.random.uniform(low=[1.0, -1.5], high=[3.0, 1.5])
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.lidar = np.ones(self.lidar_num_beams) * 3.5
        self.previous_distance = self._distance_to_goal()
        return self._get_observation(), {}

    def step(self, action):
        """Aplica la acción del agente, simula un paso temporal y devuelve obs, reward, done, info."""
        vx = float(np.clip(action[0], self.linear_min, self.linear_max))
        wz = float(np.clip(action[1], self.angular_min, self.angular_max))
        self.linear_velocity = vx
        self.angular_velocity = wz
        self._mock_robot_motion(vx, wz)

        distance = self._distance_to_goal()
        min_obstacle = float(np.min(self.lidar))
        collision = min_obstacle < self.collision_distance
        success = distance < self.goal_tolerance
        timeout = self.current_step >= self.max_steps

        reward = self._compute_reward(distance, vx, wz, collision, success)
        self.previous_distance = distance
        self.current_step += 1

        info = {
            "distance_to_goal": distance,
            "collision": collision,
            "success": success,
            "timeout": timeout,
            "step": self.current_step
        }

        done = success or collision or timeout
        return self._get_observation(), reward, done, info

    def _mock_robot_motion(self, vx, wz):
        """Simula movimiento diferencial básico sin Gazebo."""
        dt = 0.1
        x, y, theta = self.robot_pose
        theta += wz * dt
        x += vx * math.cos(theta) * dt
        y += vx * math.sin(theta) * dt
        self.robot_pose = np.array([x, y, theta])
        self.lidar = np.ones(self.lidar_num_beams) * 3.5

    def _distance_to_goal(self):
        """Calcula la distancia euclidiana hacia la meta."""
        return float(np.linalg.norm(self.goal - self.robot_pose[:2]))

    def _angle_to_goal(self):
        """Calcula el ángulo relativo hacia la meta considerando la orientación del robot."""
        dx = self.goal[0] - self.robot_pose[0]
        dy = self.goal[1] - self.robot_pose[1]
        desired_angle = math.atan2(dy, dx)
        error = desired_angle - self.robot_pose[2]
        return math.atan2(math.sin(error), math.cos(error))

    def _get_observation(self):
        """Construye y normaliza el vector de observaciones."""
        lidar_normalized = np.clip(self.lidar / 3.5, 0.0, 1.0)
        obs = np.concatenate([
            lidar_normalized,
            np.array([
                self._distance_to_goal(),
                self._angle_to_goal(),
                self.linear_velocity,
                self.angular_velocity,
                float(np.min(self.lidar))
            ])
        ])
        return obs.astype(np.float32)

    def _compute_reward(self, distance, vx, wz, collision, success):
        """Calcula la función de recompensa basada en el progreso, penalizaciones y logros."""
        r = self.config.get("reward", {})
        progress = self.previous_distance - distance
        heading = math.cos(self._angle_to_goal())

        reward = 0.0
        reward += float(r.get("progress_weight", 2.0)) * progress
        reward += float(r.get("heading_weight", 0.5)) * heading
        reward += float(r.get("linear_velocity_weight", 0.1)) * vx
        reward -= float(r.get("angular_penalty_weight", 0.05)) * abs(wz)
        reward -= float(r.get("time_penalty", 0.01))

        if collision:
            reward -= float(r.get("collision_penalty", 100.0))
        if success:
            reward += float(r.get("goal_reward", 100.0))

        return float(reward)
