# Resultados de Entrenamiento y Evaluación

Este directorio contiene los resultados generados por los scripts de simulación en modo mock.

Archivos generados:
- `training_log.csv`: Registro episodio por episodio del entrenamiento mock.
- `reward_curve.png`: Gráfica de la recompensa acumulada.
- `success_rate_curve.png`: Gráfica de la tasa de éxito (media móvil).
- `collision_curve.png`: Gráfica de la tasa de colisión (media móvil).

**Nota importante**: Los datos actuales son mock (simulados) y sirven exclusivamente para validar el pipeline (guardado de logs, lectura, graficación y evaluación base) sin depender de Gazebo en tiempo real.
