"""
plot_results.py — Genera curvas de aprendizaje del agente Q-learning.

Lee el archivo training_log.csv y genera 6 gráficas:
  1. Recompensa acumulada por episodio (entrenamiento + puntos de eval)
  2. Tasa de éxito acumulada (%)
  3. Recompensa promedio por ronda de evaluación intermedia
  4. Pasos por episodio
  5. Decaimiento de epsilon
  6. Tasa de colisión acumulada (%)

Uso:
  ros2 run ejercicio3_nav_agent plot_results
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


def compute_eval_rounds(df_eval, eval_episodes_count=5):
    """
    Agrupa los episodios de evaluación intermedia en rondas.
    Retorna un DataFrame con columnas: round, mean_reward, mean_success, episode_ref
    donde episode_ref es el número de episodio máximo de cada ronda (para graficarlo
    en el mismo eje x que el entrenamiento).
    """
    if df_eval.empty:
        return pd.DataFrame(columns=['round', 'mean_reward', 'mean_success', 'episode_ref'])

    rounds = []
    n = len(df_eval)
    chunk = max(1, eval_episodes_count)
    round_idx = 1

    for start in range(0, n, chunk):
        group = df_eval.iloc[start:start + chunk]
        rounds.append({
            'round': round_idx,
            'mean_reward': group['reward'].mean(),
            'mean_success': group['success'].mean() * 100,
            'episode_ref': group['episode'].max(),
        })
        round_idx += 1

    return pd.DataFrame(rounds)


def main():
    results_dir = os.path.expanduser('~/stage_ws/results')
    log_path = os.path.join(results_dir, 'training_log.csv')

    if not os.path.exists(log_path):
        print(f'Error: no se encontró {log_path}')
        print('Ejecuta primero el entrenamiento con q_learning_agent.')
        sys.exit(1)

    df = pd.read_csv(log_path)

    if df.empty:
        print('Error: el archivo CSV está vacío.')
        sys.exit(1)

    # Separar datos de entrenamiento y evaluación
    df_train = df[df['mode'] == 'train'].reset_index(drop=True)
    df_eval  = df[df['mode'] == 'eval'].reset_index(drop=True)
    df_test  = df[df['mode'] == 'test'].reset_index(drop=True)

    if df_train.empty:
        print('Error: no hay datos de entrenamiento en el CSV.')
        sys.exit(1)

    # --- Calcular métricas derivadas para entrenamiento ---
    window = min(10, len(df_train))
    df_train['reward_smooth']    = df_train['reward'].rolling(window=window, min_periods=1).mean()
    df_train['success_rate']     = df_train['success'].expanding().mean() * 100
    df_train['collision_rate']   = df_train['collision'].expanding().mean() * 100
    df_train['steps_smooth']     = df_train['steps'].rolling(window=window, min_periods=1).mean()

    # Agrupar evaluaciones intermedias en rondas
    df_eval_rounds = compute_eval_rounds(df_eval, eval_episodes_count=5)

    # Detectar si hubo early stopping (entrenamiento terminó antes del máximo declarado)
    max_train_ep = df_train['episode'].max()
    early_stop_ep = None
    if not df_eval_rounds.empty and len(df_eval_rounds) >= 2:
        # Heurística: si los últimos episodios de entrenamiento muestran un salto
        # grande sin llegar al máximo parametrizado, asumimos early stopping.
        # No podemos saber el parámetro max_episodes directamente desde el CSV,
        # así que solo marcamos el último episodio de entrenamiento.
        early_stop_ep = max_train_ep

    # =====================================================================
    # Figura principal — layout 2×3
    # =====================================================================
    fig, axs = plt.subplots(2, 3, figsize=(17, 10))
    fig.suptitle(
        'Curvas de Aprendizaje — Agente Q-Learning (Navegación con Metas Aleatorias)',
        fontsize=14, fontweight='bold'
    )

    ep = df_train['episode']

    # ─────────────────────────────────────────────────────────────────────
    # 1. Recompensa por episodio (entrenamiento + evaluaciones como puntos)
    # ─────────────────────────────────────────────────────────────────────
    ax1 = axs[0, 0]
    ax1.plot(ep, df_train['reward'],
             alpha=0.25, color='steelblue', linewidth=0.8, label='Por episodio')
    ax1.plot(ep, df_train['reward_smooth'],
             color='darkblue', linewidth=2,
             label=f'Media móvil ({window} ep)')

    if not df_eval.empty:
        ax1.scatter(df_eval['episode'], df_eval['reward'],
                    color='red', marker='x', s=50, linewidths=1.5,
                    label='Eval intermedia', zorder=5)

    ax1.set_title('Recompensa por Episodio')
    ax1.set_xlabel('Episodio')
    ax1.set_ylabel('Recompensa acumulada')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    # ─────────────────────────────────────────────────────────────────────
    # 2. Tasa de éxito acumulada
    # ─────────────────────────────────────────────────────────────────────
    ax2 = axs[0, 1]
    ax2.plot(ep, df_train['success_rate'],
             color='green', linewidth=2, label='Entrenamiento')

    if not df_eval_rounds.empty:
        ax2.scatter(df_eval_rounds['episode_ref'], df_eval_rounds['mean_success'],
                    color='darkgreen', marker='^', s=60,
                    label='Éxito eval (ronda)', zorder=5)

    ax2.set_title('Tasa de Éxito Acumulada')
    ax2.set_xlabel('Episodio')
    ax2.set_ylabel('Tasa de éxito (%)')
    ax2.set_ylim(-5, 105)
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    # ─────────────────────────────────────────────────────────────────────
    # 3. Recompensa promedio por ronda de evaluación intermedia
    # ─────────────────────────────────────────────────────────────────────
    ax3 = axs[0, 2]
    if not df_eval_rounds.empty:
        ax3.plot(df_eval_rounds['round'], df_eval_rounds['mean_reward'],
                 color='crimson', linewidth=2, marker='o', markersize=6,
                 label='Reward promedio / ronda')

        # Marcar la mejor ronda
        best_idx = df_eval_rounds['mean_reward'].idxmax()
        best_round = df_eval_rounds.loc[best_idx]
        ax3.axhline(best_round['mean_reward'], color='crimson',
                    linestyle='--', alpha=0.5, linewidth=1,
                    label=f'Mejor: {best_round["mean_reward"]:.2f} (ronda {int(best_round["round"])})')
        ax3.scatter([best_round['round']], [best_round['mean_reward']],
                    color='gold', s=120, zorder=6, edgecolors='crimson', linewidths=1.5)

        ax3.set_xlabel('Ronda de evaluación')
    else:
        ax3.text(0.5, 0.5, 'Sin datos de\nevaluación intermedia',
                 ha='center', va='center', transform=ax3.transAxes,
                 fontsize=11, color='gray')

    ax3.set_title('Recompensa Promedio — Evaluaciones Intermedias')
    ax3.set_ylabel('Recompensa promedio')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)

    # ─────────────────────────────────────────────────────────────────────
    # 4. Pasos por episodio
    # ─────────────────────────────────────────────────────────────────────
    ax4 = axs[1, 0]
    ax4.plot(ep, df_train['steps'],
             color='orange', alpha=0.25, linewidth=0.8, label='Por episodio')
    ax4.plot(ep, df_train['steps_smooth'],
             color='darkorange', linewidth=2,
             label=f'Media móvil ({window} ep)')
    ax4.set_title('Pasos por Episodio')
    ax4.set_xlabel('Episodio')
    ax4.set_ylabel('Pasos')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)

    # ─────────────────────────────────────────────────────────────────────
    # 5. Decaimiento de epsilon
    # ─────────────────────────────────────────────────────────────────────
    ax5 = axs[1, 1]
    ax5.plot(ep, df_train['epsilon'],
             color='red', linewidth=2, label='ε (exploración)')
    ax5.fill_between(ep, df_train['epsilon'], alpha=0.15, color='red')

    # Marcar cuando epsilon llega al mínimo
    min_eps = df_train['epsilon'].min()
    min_ep_idx = df_train[df_train['epsilon'] <= min_eps + 0.001]['episode'].min()
    ax5.axvline(min_ep_idx, color='darkred', linestyle=':', alpha=0.6,
                label=f'ε_min={min_eps:.3f} alcanzado (ep {min_ep_idx})')

    ax5.set_title('Decaimiento de Epsilon (Exploración → Explotación)')
    ax5.set_xlabel('Episodio')
    ax5.set_ylabel('Epsilon (ε)')
    ax5.set_ylim(-0.05, 1.05)
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.3)

    # ─────────────────────────────────────────────────────────────────────
    # 6. Tasa de colisión acumulada
    # ─────────────────────────────────────────────────────────────────────
    ax6 = axs[1, 2]
    ax6.plot(ep, df_train['collision_rate'],
             color='purple', linewidth=2, label='Colisiones acumuladas (%)')
    ax6.fill_between(ep, df_train['collision_rate'], alpha=0.12, color='purple')

    # Añadir tasa de éxito como referencia (eje Y secundario implícito con misma escala)
    ax6.plot(ep, df_train['success_rate'],
             color='green', linewidth=1.5, linestyle='--', alpha=0.7,
             label='Éxito acumulado (%)')

    ax6.set_title('Tasa de Colisión vs. Éxito Acumulados')
    ax6.set_xlabel('Episodio')
    ax6.set_ylabel('Porcentaje (%)')
    ax6.set_ylim(-5, 105)
    ax6.legend(fontsize=8)
    ax6.grid(True, alpha=0.3)

    # ─────────────────────────────────────────────────────────────────────
    # Ajustar y guardar
    # ─────────────────────────────────────────────────────────────────────
    plt.tight_layout()

    plot_path = os.path.join(results_dir, 'curvas_aprendizaje.png')
    fig.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f'\nGráficas guardadas en: {plot_path}')

    # ─────────────────────────────────────────────────────────────────────
    # Resumen de métricas en consola
    # ─────────────────────────────────────────────────────────────────────
    last_20 = df_train.tail(20)
    successful = df_train[df_train['success'] == 1]

    print('\n' + '=' * 55)
    print('   RESUMEN DE MÉTRICAS — ENTRENAMIENTO Q-LEARNING')
    print('=' * 55)
    print(f'  Episodios de entrenamiento  : {len(df_train)}')
    print(f'  Episodios de evaluación     : {len(df_eval)}')
    print(f'  Rondas de evaluación        : {len(df_eval_rounds)}')
    if not df_test.empty:
        print(f'  Episodios de test           : {len(df_test)}')
    print()
    print(f'  Recompensa promedio (total) : {df_train["reward"].mean():.2f}')
    print(f'  Recompensa promedio (últ.20): {last_20["reward"].mean():.2f}')
    print()
    print(f'  Tasa de éxito total         : {df_train["success"].mean() * 100:.1f}%')
    print(f'  Tasa de éxito (últ. 20 ep) : {last_20["success"].mean() * 100:.1f}%')
    print(f'  Tasa de colisión total      : {df_train["collision"].mean() * 100:.1f}%')
    print()
    print(f'  Pasos promedio (todos)      : {df_train["steps"].mean():.1f}')
    if not successful.empty:
        print(f'  Pasos promedio (éxitos)     : {successful["steps"].mean():.1f}')
    print()
    print(f'  Epsilon inicial             : {df_train["epsilon"].iloc[0]:.4f}')
    print(f'  Epsilon final               : {df_train["epsilon"].iloc[-1]:.4f}')

    if not df_eval_rounds.empty:
        print()
        print(f'  Mejor reward eval (ronda)   : '
              f'{df_eval_rounds["mean_reward"].max():.2f} '
              f'(ronda {int(df_eval_rounds.loc[df_eval_rounds["mean_reward"].idxmax(), "round"])})')
        print(f'  Mejor éxito eval (ronda)    : '
              f'{df_eval_rounds["mean_success"].max():.1f}%')

    if not df_test.empty:
        print()
        print(f'  [TEST] Reward promedio      : {df_test["reward"].mean():.2f}')
        print(f'  [TEST] Tasa de éxito        : {df_test["success"].mean() * 100:.1f}%')

    print('=' * 55)

    plt.show()


if __name__ == '__main__':
    main()
