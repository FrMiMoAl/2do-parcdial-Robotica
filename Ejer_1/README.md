# 🤖 Ejercicio 1 - Robot Diferencial Físico con micro-ROS y ROS 2

## Integrantes

* Franco Morales
* Joel Sejas
* Samuel Barrios
* Samuel Guzman

---

## Descripción del Proyecto

Se implementó un robot diferencial físico utilizando una ESP32 y micro-ROS para la comunicación con ROS 2 Jazzy mediante WiFi.

El robot recibe comandos de velocidad desde el tópico `/cmd_vel`, controla cada motor mediante un controlador PID basado en encoders y utiliza una IMU MPU6050 para corregir desviaciones durante el movimiento recto.

Además, el sistema publica información de odometría básica y velocidad para su visualización en RViz2.

---

## Hardware Utilizado

* ESP32 DevKit
* Puente H TB6612FNG
* 2 Motores DC con encoders
* MPU6050
* Batería de alimentación
* Chasis diferencial

---

## Software Utilizado

* Ubuntu 24.04
* ROS 2 Jazzy Jalisco
* micro-ROS Agent
* Arduino IDE 2.x
* RViz2

---

## Estructura del Repositorio

```text
.
├── firmware/
│   └── codigoesp32.ino
├── ros2/
│   ├── launch/
│   ├── rviz/
│   └── config/
├── README.md
└── video/
```

---

## Control PID

Se implementó un controlador PID independiente para cada rueda utilizando la información de los encoders para regular la velocidad de los motores.

### Parámetros Finales

```text
Kp = 0.6
Ki = 0.10
Kd = 0.15
```

### Justificación de los Parámetros

Los parámetros fueron ajustados experimentalmente sobre la plataforma física real hasta obtener una respuesta estable y un seguimiento adecuado de la velocidad de referencia enviada desde ROS 2.

* **Kp = 0.6:** Corrige rápidamente el error entre la velocidad deseada y la velocidad medida.
* **Ki = 0.10:** Elimina errores permanentes causados por fricción, diferencias mecánicas y variaciones de carga.
* **Kd = 0.15:** Reduce oscilaciones y mejora la estabilidad del movimiento.

Además, se implementó una estrategia Anti-Windup para evitar saturaciones del término integral.

### Resultado

La combinación de parámetros seleccionada permitió obtener una respuesta rápida, estable y con bajo error estacionario durante las pruebas realizadas sobre el robot físico.

---

# Carga del Firmware en la ESP32

1. Abrir:

```text
firmware/codigoesp32.ino
```

2. Configurar la red WiFi y la IP del agente:

```cpp
char ssid[] = "NOMBRE_DE_TU_RED";
char psk[]  = "CONTRASEÑA_WIFI";
char agent_ip[] = "192.168.1.XXX";
```

3. Seleccionar la placa:

```text
ESP32 Dev Module
```

4. Compilar y cargar el firmware.

5. Abrir el monitor serial a:

```text
115200 baud
```

---

# Compilación del Workspace ROS 2

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
```

---

# Ejecución del Sistema

⚠️ En cada terminal ejecutar previamente:

```bash
source /opt/ros/jazzy/setup.bash
source ~/Roboticaclase/RvizRobot/install/setup.bash
export ROS_DOMAIN_ID=69
```

---

## Terminal 1 - micro-ROS Agent

```bash
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```

---

## Terminal 2 - Lanzar Nodos y RViz

```bash
ros2 launch my_robot_viz visualize.launch.py
```

RViz se abrirá automáticamente mostrando el robot y la información publicada por ROS 2.

---

## Terminal 3 - Control del Robot

### Avanzar

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.3}, angular: {z: 0.0}}"
```

### Girar

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0}, angular: {z: 0.5}}"
```

### Detener

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0}, angular: {z: 0.0}}"
```

---

# Abrir RViz Manualmente

Si RViz no inicia automáticamente:

```bash
rviz2 -d ~/Roboticaclase/RvizRobot/my_robot_viz/rviz/robot.rviz
```

---

# Diagnóstico

Ver tópicos activos:

```bash
ros2 topic list
```

RPM rueda izquierda:

```bash
ros2 topic echo /real_rpm_left
```

RPM rueda derecha:

```bash
ros2 topic echo /real_rpm_right
```

Yaw de la IMU:

```bash
ros2 topic echo /imu_yaw
```

Ver nodos activos:

```bash
ros2 node list
```

---

# Resultados

Se logró implementar un robot diferencial físico integrado con ROS 2 mediante micro-ROS. El sistema permite:

* Control de velocidad mediante PID.
* Comunicación inalámbrica ESP32 ↔ ROS 2.
* Corrección de trayectoria mediante IMU.
* Monitoreo de RPM y orientación.
* Visualización del robot en RViz2.

Las pruebas realizadas demostraron una respuesta estable, bajo error estacionario y un seguimiento adecuado de los comandos enviados desde `/cmd_vel`.



