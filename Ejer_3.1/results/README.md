# Resultados de Entrenamiento y Evaluación

Este directorio contiene los resultados generados por los scripts de simulación en modo mock.

Archivos generados:
- `training_log.csv`: Registro episodio por episodio del entrenamiento mock.
- `reward_curve.png`: Gráfica de la recompensa acumulada.
- `success_rate_curve.png`: Gráfica de la tasa de éxito (media móvil).
- `collision_curve.png`: Gráfica de la tasa de colisión (media móvil).

**Nota importante**: Los datos actuales son mock (simulados) y sirven exclusivamente para validar el pipeline (guardado de logs, lectura, graficación y evaluación base) sin depender de Gazebo en tiempo real.

## Instrucciones de Ejecución

Para probar el pipeline y ejecutar los scripts de este ejercicio en modo mock, sitúate en la carpeta `Ejer_3.1` y ejecuta los siguientes comandos:

### 1. Entrenamiento Mock
Genera los datos simulados de referencia y crea el archivo `results/training_log.csv`:
python3 src/train_agent.py --mock


### 2. Generación de Gráficas
Una vez generado el log de entrenamiento, crea las gráficas (curvas de recompensa, éxito y colisión) ejecutando:
```bash
python3 src/plot_metrics.py
```
Las gráficas se guardarán automáticamente en esta misma carpeta `results/`.

### 3. Evaluación del Agente
Para correr una evaluación del agente simulado y ver las métricas (tasa de éxito, colisión, recompensas, etc.) directamente en consola:
```bash
python3 src/evaluate_agent.py
```
