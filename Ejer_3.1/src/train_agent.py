"""
Script principal para el entrenamiento del Agente de Navegación RL.
Actualmente soporta el modo '--mock' para generar datos de referencia
y validar el pipeline de guardado y métricas.
"""
import os
import csv
import yaml
import argparse
import numpy as np
from rl_navigation_env import RLNavigationEnv


def load_config(path):
    """Carga los parámetros de configuración desde un archivo YAML."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def train_mock(env, config, output_csv):
    """
    Ejecuta un entrenamiento simulado (mock) generando datos falsos pero con 
    la estructura correcta para validar todo el flujo de trabajo (pipeline).
    """
    episodes = min(int(config.get("total_episodes", 1000)), 200)
    max_steps = int(config.get("max_steps_per_episode", 500))

    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["episode", "total_reward", "success", "collision", "steps", "distance_final", "elapsed_time", "note"])

        for ep in range(1, episodes + 1):
            env.reset(seed=int(config.get("seed", 42)) + ep)
            total_reward = 0.0
            success = False
            collision = False
            distance_final = 999.0

            for step in range(max_steps):
                action = np.array([
                    np.random.uniform(0.05, 0.25),
                    np.random.uniform(-0.35, 0.35)
                ])
                _, reward, done, info = env.step(action)
                total_reward += reward
                success = info["success"]
                collision = info["collision"]
                distance_final = info["distance_to_goal"]
                if done:
                    break

            total_reward += ep * 0.15
            writer.writerow([
                ep,
                round(total_reward, 4),
                int(success),
                int(collision),
                step + 1,
                round(distance_final, 4),
                round((step + 1) * 0.1, 2),
                "datos_simulados_de_referencia"
            ])

    print(f"Archivo generado: {output_csv}")


def main():
    """Función principal para parsear argumentos y lanzar el entrenamiento."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Generar datos mock sin usar Gazebo")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config = load_config(os.path.join(base_dir, "config", "rl_params.yaml"))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    env = RLNavigationEnv(config)

    if args.mock:
        train_mock(env, config, os.path.join(results_dir, "training_log.csv"))
    else:
        print("Entrenamiento real pendiente. Para conectar con Gazebo falta:")
        print("1. Integrar rclpy y crear un nodo de ROS 2 en este script.")
        print("2. Suscribirse a /scan (sensor_msgs/LaserScan) para el estado.")
        print("3. Suscribirse a /odom (nav_msgs/Odometry) para posición y progreso.")
        print("4. Publicar acciones en /cmd_vel (geometry_msgs/Twist).")
        print("5. Sincronizar el entorno de Gymnasium con los callbacks de ROS 2.")


if __name__ == "__main__":
    main()
