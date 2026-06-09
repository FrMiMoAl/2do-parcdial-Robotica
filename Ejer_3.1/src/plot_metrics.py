"""
Script para visualizar las métricas del entrenamiento.
Lee el archivo CSV generado y crea gráficas de recompensa,
tasa de éxito y tasa de colisiones utilizando promedios móviles.
"""
import os
import pandas as pd
import matplotlib.pyplot as plt


def main():
    """Genera y guarda las gráficas de entrenamiento en la carpeta results/."""
    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    results_dir = os.path.join(base_dir, "results")
    csv_path = os.path.join(results_dir, "training_log.csv")

    if not os.path.exists(csv_path):
        raise FileNotFoundError("No existe results/training_log.csv. Ejecuta: python3 src/train_agent.py --mock")

    df = pd.read_csv(csv_path)
    df["reward_ma"] = df["total_reward"].rolling(window=10, min_periods=1).mean()
    df["success_ma"] = df["success"].rolling(window=10, min_periods=1).mean()
    df["collision_ma"] = df["collision"].rolling(window=10, min_periods=1).mean()

    plt.figure()
    plt.plot(df["episode"], df["total_reward"], label="Recompensa")
    plt.plot(df["episode"], df["reward_ma"], label="Media movil")
    plt.xlabel("Episodio")
    plt.ylabel("Recompensa acumulada")
    plt.title("Curva de aprendizaje")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(results_dir, "reward_curve.png"), dpi=300)

    plt.figure()
    plt.plot(df["episode"], df["success_ma"])
    plt.xlabel("Episodio")
    plt.ylabel("Tasa de exito")
    plt.title("Tasa de exito")
    plt.grid(True)
    plt.savefig(os.path.join(results_dir, "success_rate_curve.png"), dpi=300)

    plt.figure()
    plt.plot(df["episode"], df["collision_ma"])
    plt.xlabel("Episodio")
    plt.ylabel("Tasa de colision")
    plt.title("Tasa de colision")
    plt.grid(True)
    plt.savefig(os.path.join(results_dir, "collision_curve.png"), dpi=300)

    print("Graficas generadas en results/")


if __name__ == "__main__":
    main()
