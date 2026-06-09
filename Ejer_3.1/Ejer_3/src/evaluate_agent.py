"""
Script de evaluación para el Agente RL (Modo Mock).
Permite validar el rendimiento del agente una vez entrenado, ejecutando
múltiples episodios y calculando métricas como tasa de éxito y colisión.
"""
import os
import yaml
import numpy as np
from rl_navigation_env import RLNavigationEnv


def load_config(path):
    """Carga los parámetros de configuración desde un archivo YAML."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    """Ejecuta la evaluación del agente y muestra las métricas por consola."""
    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config = load_config(os.path.join(base_dir, "config", "rl_params.yaml"))
    env = RLNavigationEnv(config)

    episodes = 30
    rewards = []
    successes = 0
    collisions = 0
    steps_list = []

    for ep in range(episodes):
        env.reset(seed=int(config.get("seed", 42)) + ep)
        total_reward = 0.0
        info = {"success": False, "collision": False}

        for step in range(int(config.get("max_steps_per_episode", 500))):
            action = np.array([0.18, np.random.uniform(-0.25, 0.25)])
            _, reward, done, info = env.step(action)
            total_reward += reward
            if done:
                break

        rewards.append(total_reward)
        steps_list.append(step + 1)
        successes += int(info["success"])
        collisions += int(info["collision"])

    print("Evaluacion mock de referencia")
    print(f"Episodios: {episodes}")
    print(f"Recompensa promedio: {np.mean(rewards):.2f}")
    print(f"Tasa de exito: {(successes / episodes) * 100:.2f}%")
    print(f"Tasa de colision: {(collisions / episodes) * 100:.2f}%")
    print(f"Pasos promedio: {np.mean(steps_list):.2f}")
    print("Nota: esto valida el pipeline, no es entrenamiento real en Gazebo.")


if __name__ == "__main__":
    main()
