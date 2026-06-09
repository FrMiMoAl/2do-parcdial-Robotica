# Ejercicio 3.1 - Agente de Navegación Q-Learning

Este repositorio contiene la implementación de un agente de aprendizaje por refuerzo (Q-Learning) para la navegación de un robot en el simulador Stage usando ROS 2.

## Requisitos Previos

- ROS 2 Jazzy
- Simulador `stage_ros2` instalado
- Librerías de Python: `pandas`, `matplotlib`

## Limpiar Entrenamientos Anteriores

Si deseas reiniciar el aprendizaje del agente desde cero, debes eliminar la tabla Q y los logs generados en ejecuciones anteriores. Los scripts de este proyecto guardan los resultados en el directorio `~/stage_ws/results/` por defecto.

```bash
rm -f ~/stage_ws/results/q_table.json
rm -f ~/stage_ws/results/training_log.csv
rm -f ~/stage_ws/results/curvas_aprendizaje.png
```
> **Nota:** El archivo de la gráfica se llama `curvas_aprendizaje.png`, no `reward_curve.png`.

## Compilación del Espacio de Trabajo

El código del paquete ROS 2 (`ejercicio3_nav_agent`) se encuentra en el subdirectorio `Ejer_3`. Por lo tanto, debes situarte en ese directorio para compilar:

```bash
cd ~/stage_ws/Ejer_3
colcon build --symlink-install --packages-select ejercicio3_nav_agent
```

## Ejecución del Entrenamiento

Necesitarás abrir **dos terminales**.

### Terminal 1: Iniciar el Simulador (Stage)
Carga el entorno y lanza el simulador con el mundo "cave":

```bash
cd ~/stage_ws/Ejer_3
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 launch stage_ros2 demo.launch.py world:=cave use_stamped_velocity:=false
```

### Terminal 2: Iniciar el Agente Q-Learning
En otra terminal, carga el entorno nuevamente y ejecuta el nodo principal del agente:

```bash
cd ~/stage_ws/Ejer_3
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run ejercicio3_nav_agent q_learning_agent
```

## Visualización de Resultados

Una vez que el entrenamiento haya terminado (o incluso durante el mismo si lo detienes), puedes generar y visualizar las curvas de aprendizaje y otras métricas. Este script lee el CSV y muestra las gráficas.

**En cualquier terminal (o una tercera):**
```bash
cd ~/stage_ws/Ejer_3
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run ejercicio3_nav_agent plot_results
```
Este comando:
1. Abrirá una ventana interactiva con 6 gráficas (recompensa, tasa de éxito, decaimiento de epsilon, colisiones, etc.).
2. Guardará automáticamente la imagen final en `~/stage_ws/results/curvas_aprendizaje.png`.
3. Imprimirá un resumen estadístico del entrenamiento en la consola.
