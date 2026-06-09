import csv
import os
import matplotlib.pyplot as plt

log_path = os.path.expanduser('~/stage_ws/results/training_log.csv')
output_path = os.path.expanduser('~/stage_ws/results/reward_curve.png')

episodes = []
rewards = []
successes = []
collisions = []

with open(log_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['mode'] == 'train':
            episodes.append(int(row['episode']))
            rewards.append(float(row['reward']))
            successes.append(int(row['success']))
            collisions.append(int(row['collision']))

plt.figure()
plt.plot(episodes, rewards, marker='o')
plt.xlabel('Episodio')
plt.ylabel('Recompensa acumulada')
plt.title('Curva de aprendizaje del agente')
plt.grid(True)
plt.savefig(output_path, dpi=300)

print(f'Gráfica guardada en: {output_path}')

if len(successes) > 0:
    print(f'Tasa de éxito: {sum(successes)/len(successes)*100:.2f}%')
    print(f'Tasa de colisión: {sum(collisions)/len(collisions)*100:.2f}%')

