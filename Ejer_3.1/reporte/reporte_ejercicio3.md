# Metodología para Entrenamiento y Test de un Agente de Navegación en ROS 2

## 1. Configuración del Entorno

El laboratorio se plantea sobre ROS 2 Jazzy, usando un robot móvil diferencial simulado. El entorno de simulación recomendado es Gazebo, con visualización en RViz2. El robot utiliza un LiDAR 2D publicado en `/scan` mediante `sensor_msgs/msg/LaserScan` y odometría publicada en `/odom` mediante `nav_msgs/msg/Odometry`. La actuación se realiza con comandos de velocidad publicados en `/cmd_vel` usando `geometry_msgs/msg/Twist`.

Las herramientas empleadas son ROS 2 Jazzy, Python 3, `rclpy`, Gazebo, RViz2, `numpy`, `pandas`, `matplotlib`, `gymnasium` y `stable-baselines3`. La simulación permite ejecutar episodios repetibles sin riesgo físico.

## 2. Definición del Agente

El agente recibe como observación lecturas LiDAR reducidas y normalizadas, pose/velocidad odométrica, distancia a la meta, ángulo relativo a la meta y distancia mínima a obstáculos.

`obs = [lidar_1, ..., lidar_24, distancia_meta, angulo_meta, velocidad_lineal, velocidad_angular, distancia_obstaculo_minima]`

Las acciones corresponden a comandos continuos publicados en `/cmd_vel`: `linear.x ∈ [0.0, 0.35] m/s` y `angular.z ∈ [-1.0, 1.0] rad/s`. El algoritmo recomendado es PPO porque permite acciones continuas.

La recompensa propuesta es:

`r_t = 2.0(d_{t-1} - d_t) + 0.5cos(theta_goal) + 0.1v_x - 0.05|w_z| - 0.01 - P_colision + R_meta`

Donde `P_colision = 100` si existe colisión y `R_meta = 100` si el robot alcanza la meta.

## 3. Entrenamiento en Simulación

El entrenamiento se realiza exclusivamente en simulación mediante episodios. Al inicio de cada episodio se reinicia el robot y se genera una meta aleatoria dentro de zonas válidas. Cada transición registra estado, acción, recompensa y condición terminal.

Se utiliza semilla fija `42`, máximo `1000` episodios y `500` pasos por episodio. Se realiza evaluación intermedia cada `25` episodios y parada temprana si no existe mejora durante `10` evaluaciones consecutivas.

Las condiciones terminales son: éxito si la distancia a la meta es menor a `0.30 m`, colisión si la distancia mínima LiDAR es menor a `0.18 m` y timeout al superar el máximo de pasos.

## 4. Evaluación y Pruebas

La evaluación se realiza con el agente entrenado y política determinista. Se proponen entre 20 y 30 episodios de prueba con metas fijas y aleatorias. En cada prueba se registra recompensa acumulada, éxito, colisión, pasos, distancia final y tiempo de ejecución.

## 5. Métricas de Validación

| Métrica | Descripción | Criterio esperado |
|---|---|---|
| Recompensa acumulada | Suma de recompensas por episodio | Tendencia creciente |
| Recompensa media móvil | Promedio suavizado | Estabilidad |
| Tasa de éxito | Porcentaje de metas alcanzadas | ≥ 80% |
| Tasa de colisión | Episodios con choque | ≤ 10% |
| Tiempo promedio | Duración media del episodio | Disminución progresiva |
| Distancia final | Error respecto a la meta | Menor a 0.30 m |
| Pasos por episodio | Acciones ejecutadas | Tendencia decreciente |

## Conclusión

La metodología permite entrenar y evaluar un agente de navegación en ROS 2 Jazzy usando LiDAR, odometría y comandos `/cmd_vel`. La recompensa integra avance, orientación, seguridad y eficiencia, permitiendo validar el desempeño mediante métricas cuantitativas.
