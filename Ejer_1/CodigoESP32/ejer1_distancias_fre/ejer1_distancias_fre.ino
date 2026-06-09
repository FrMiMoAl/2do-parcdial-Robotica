#include <Arduino.h>
#include <Wire.h>
#include <micro_ros_arduino.h>

#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include <std_msgs/msg/int32.h>
#include <std_msgs/msg/float32.h>
#include <geometry_msgs/msg/vector3.h>
#include <geometry_msgs/msg/twist.h>

// =====================================================
// CONFIGURACIÓN DE TU ENCODER
// =====================================================
#define ENCODER_RESOLUTION 330.0

// =====================================================
// PINES SEGUN TU ESQUEMATICO
// =====================================================
#define PWMA_PIN 25
#define AIN2_PIN 27
#define AIN1_PIN 26

#define PWMB_PIN 18
#define BIN2_PIN 17
#define BIN1_PIN 16

#define STBY_PIN 14

#define SDA_PIN 21
#define SCL_PIN 22
#define MPU6050_ADDR 0x68

#define ENCODER_A_PIN 32
#define END1_POS_PIN 33
#define ENCODER_B_PIN 34
#define END2_POS_PIN 35

#define LED_PIN 2

// =====================================================
// CONFIGURACION PWM Y RANGOS
// =====================================================
#define PWM_FREQ 20000
#define PWM_RESOLUTION 8
#define PWM_CHANNEL_A 0
#define PWM_CHANNEL_B 1

#define USE_LIMIT_SAFETY false
#define LIMIT_ACTIVE_LOW true

const int PWM_MIN_MOV = 80;
const int PWM_MAX_MOV = 255;
const int PWM_DEADBAND = 25;

// =====================================================
// PARÁMETROS SMOOTH MODE
// =====================================================
const float MAX_RPM_CHANGE_PER_CYCLE = 3.0;
const float input_filter_alpha = 0.6;

// =====================================================
// FILTRO DE VELOCIDAD
// =====================================================
const float velocity_filter_alpha = 0.6;

// =====================================================
// COMPENSACIÓN DE ASIMETRÍA MOTOR
// =====================================================
const float motor_b_balance_factor = 1.02;  

// =====================================================
// PARÁMETROS IMU
// =====================================================
float gyro_filter_alpha = 0.8;
const float GYRO_DEADBAND = 0.1;
const unsigned long GYRO_RECAL_INTERVAL = 10000;
float gyro_recal_old_weight = 0.9;
float gyro_recal_new_weight = 0.1;

// =====================================================
// CONSTANTES MECÁNICAS (RANGO AMPLIADO A 6.5 CM)
// =====================================================
const float WHEEL_DIAMETER_CM = 4.0;      
const float POSITION_TOLERANCE_CM = 7;  // <- Ampliado para absorber inercia de frenado

// Conversión cinemática: Centímetros a Ticks absolutos
const float CM_TO_TICKS = (ENCODER_RESOLUTION / (3.14159265 * WHEEL_DIAMETER_CM));
const float TICK_TOLERANCE = POSITION_TOLERANCE_CM * CM_TO_TICKS;

// =====================================================
// CLASE PID
// =====================================================
class PIDController {
  public:
    float kp, ki, kd, dt, output_min, output_max, integral_limit;
    float _integral, _prev_error;

    PIDController(float kp = 0.6, float ki = 0.10, float kd = 0.15, float dt = 0.02,  
                  float output_min = -1.0, float output_max = 1.0, float integral_limit = 25.0) {
        this->kp = kp;
        this->ki = ki;
        this->kd = kd;
        this->dt = dt;
        this->output_min = output_min;
        this->output_max = output_max;
        this->integral_limit = integral_limit;
        reset();
    }

    float compute(float setpoint, float measurement) {
        float error = setpoint - measurement;
        float p_term = kp * error;

        _integral += error * dt;
        _integral = max(-integral_limit, min(integral_limit, _integral));
        float i_term = ki * _integral;

        float derivative = (error - _prev_error) / dt;
        float d_term = kd * derivative;
        _prev_error = error;

        float output = p_term + i_term + d_term;
        output = max(output_min, min(output_max, output));

        if (output >= output_max || output <= output_min) {
            _integral -= error * dt;  
        }

        return output;
    }

    void reset() {
        _integral = 0.0;
        _prev_error = 0.0;
    }
};

PIDController pid_motor_a(0.6, 0.10, 0.15, 0.02); 
PIDController pid_motor_b(0.6, 0.10, 0.15, 0.02); 

// =====================================================
// MICRO-ROS OBJETOS
// =====================================================
rcl_node_t node;
rclc_support_t support;
rclc_executor_t executor;
rcl_allocator_t allocator;

rcl_subscription_t cmd_vel_sub;
geometry_msgs__msg__Twist cmd_vel_msg;

rcl_publisher_t rpm_left_pub;
std_msgs__msg__Float32 rpm_left_msg;

rcl_publisher_t rpm_right_pub;
std_msgs__msg__Float32 rpm_right_msg;

rcl_publisher_t imu_yaw_pub;
std_msgs__msg__Float32 imu_yaw_msg;

// =====================================================
// VARIABLES DE ESTADO Y CONTROL
// =====================================================
int motor_a_cmd = 0;
int motor_b_cmd = 0;

volatile long encoder_a_total_ticks = 0;
volatile long encoder_b_total_ticks = 0;

volatile long absolute_ticks_a = 0;
volatile long absolute_ticks_b = 0;

unsigned long last_control_time = 0;
unsigned long last_gyro_recal_time = 0;

float target_rpm_a = 0.0;
float target_rpm_b = 0.0;

float _prev_rpm_a = 0.0;
float _prev_rpm_b = 0.0;
float _prev_linear = 0.0;
float _prev_angular = 0.0;

float gyro_x_offset = 0;
float current_yaw = 0;
float target_yaw = 0;
bool is_going_straight = false;
unsigned long last_mpu_time = 0;

float Kp_gyro = 0.5;
float gyro_deadband_deg = 3.0;
float _prev_gyro_x_filtered = 0.0;

// Variables de lazo de posición
float target_position_ticks = 0.0;
float Kp_position = 0.6;  
float max_velocity_rpm = 80.0; 

bool emergency_stop = true; 

// =====================================================
// RUTINAS DE INTERRUPCIÓN (ISRs)
// =====================================================
void IRAM_ATTR ISR_encoder_a() {
  encoder_a_total_ticks++;
  absolute_ticks_a++;
}

void IRAM_ATTR ISR_encoder_b() {
  encoder_b_total_ticks++;
  absolute_ticks_b++;
}

// =====================================================
// PROTOTIPOS
// =====================================================
void motor_a_write(int pwm);
void motor_b_write(int pwm);
void motors_init();
void mpu6050_init_improved();
void mpu6050_init() { mpu6050_init_improved(); }
void recalibrate_gyro_offset_dynamic();
void update_yaw_improved();
void update_yaw() { update_yaw_improved(); }
void control_loop_pid();
float constrain_change(float current, float previous, float max_change);
float apply_lowpass_filter(float current, float previous, float alpha);

// =====================================================
// ERROR
// =====================================================
#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if ((temp_rc != RCL_RET_OK)) error_loop(); }
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; (void)temp_rc; }

void error_loop() {
  while (1) {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    delay(100);
  }
}

float apply_lowpass_filter(float current, float previous, float alpha) {
  return alpha * current + (1.0 - alpha) * previous;
}

float constrain_change(float current, float previous, float max_change) {
  float delta = current - previous;
  if (delta > max_change) return previous + max_change;
  else if (delta < -max_change) return previous - max_change;
  return current;
}

// =====================================================
// LÓGICA /cmd_vel - CON REINICIO INTEGRAL DE ENCODERS Y MPU
// =====================================================
void cmd_vel_callback(const void * msgin) {
  const geometry_msgs__msg__Twist * msg = (const geometry_msgs__msg__Twist *)msgin;

  float linear = msg->linear.x; 
  float angular = msg->angular.z;

  if (linear == 0.0 && angular == 0.0) {
    emergency_stop = true;
    target_rpm_a = 0.0;
    target_rpm_b = 0.0;
    target_position_ticks = 0.0;
    pid_motor_a.reset();
    pid_motor_b.reset();
    motor_a_write(0);
    motor_b_write(0);
    Serial.println("🚨 PARADA DE EMERGENCIA EN SECO ACTIVADA");
    return; 
  }

  emergency_stop = false;

  linear = apply_lowpass_filter(linear, _prev_linear, input_filter_alpha);
  angular = apply_lowpass_filter(angular, _prev_angular, input_filter_alpha);
  _prev_linear = linear;
  _prev_angular = angular;

  // 1. REINICIAR RUMBO MPU: Establecemos el cero relativo del giroscopio
  current_yaw = 0.0;
  target_yaw = 0.0;
  is_going_straight = false;

  // 2. REINICIAR ODOMETRÍA: Ponemos a 0 las ruedas para arrancar desde cero el test
  noInterrupts();
  absolute_ticks_a = 0;
  absolute_ticks_b = 0;
  interrupts();

  target_position_ticks = linear * CM_TO_TICKS;
  Serial.println("🔄 Lazo e IMU reseteados. Iniciando nueva prueba de posición...");
}

// =====================================================
// LAZO PID PRINCIPAL CON APAGADO ELECTRÓNICO EN META
// =====================================================
void control_loop_pid() {
  unsigned long now = millis();
  float dt = (now - last_control_time) / 1000.0;

  if (dt < 0.02) return; 
  last_control_time = now;

  noInterrupts();
  long ticks_a = encoder_a_total_ticks;
  long ticks_b = encoder_b_total_ticks;
  long current_abs_ticks_a = absolute_ticks_a;
  long current_abs_ticks_b = absolute_ticks_b;
  encoder_a_total_ticks = 0; 
  encoder_b_total_ticks = 0;
  interrupts();

  if (emergency_stop) {
    motor_a_write(0);
    motor_b_write(0);
    return;
  }

  float average_current_ticks = (float)(current_abs_ticks_a + current_abs_ticks_b) / 2.0;
  float position_error = target_position_ticks - average_current_ticks;

  float base_rpm = 0.0;

  // -----------------------------------------------------------------
  // CONDICIÓN DE DETENCIÓN DE MOTORES AL LLEGAR A LA META REAL 
  // -----------------------------------------------------------------
  if (fabs(position_error) > TICK_TOLERANCE) {
    base_rpm = position_error * Kp_position;
    base_rpm = constrain(base_rpm, -max_velocity_rpm, max_velocity_rpm);
  } else {
    // ¡META ALCANZADA!: Forzamos apagado total instantáneo y reseteamos el acumulado de corriente
    target_rpm_a = 0.0;
    target_rpm_b = 0.0;
    pid_motor_a.reset();
    pid_motor_b.reset();
    motor_a_write(0);
    motor_b_write(0);
    return; 
  }

  float dt_minutes = dt / 60.0;
  float current_rpm_a = ((float)ticks_a / ENCODER_RESOLUTION) / dt_minutes;
  float current_rpm_b = ((float)ticks_b / ENCODER_RESOLUTION) / dt_minutes;

  current_rpm_a = apply_lowpass_filter(current_rpm_a, _prev_rpm_a, velocity_filter_alpha);
  current_rpm_b = apply_lowpass_filter(current_rpm_b, _prev_rpm_b, velocity_filter_alpha);
  _prev_rpm_a = current_rpm_a;
  _prev_rpm_b = current_rpm_b;

  float rpm_left = base_rpm;
  float rpm_right = base_rpm;

  if (base_rpm != 0.0) {
    if (!is_going_straight) {
      target_yaw = current_yaw; 
      is_going_straight = true;
    }
    float error_yaw = target_yaw - current_yaw;
    if (fabs(error_yaw) > gyro_deadband_deg) {
      float gyro_correction = error_yaw * Kp_gyro;
      if (base_rpm < 0) {
        rpm_left -= gyro_correction; rpm_right += gyro_correction;
      } else {
        rpm_left += gyro_correction; rpm_right -= gyro_correction;
      }
    }
  } else {
    is_going_straight = false;
  }

  target_rpm_a = constrain_change(rpm_left, target_rpm_a, MAX_RPM_CHANGE_PER_CYCLE);
  float rpm_right_balanced = rpm_right / motor_b_balance_factor;
  target_rpm_b = constrain_change(rpm_right_balanced, target_rpm_b, MAX_RPM_CHANGE_PER_CYCLE);

  if (target_rpm_a < 0) current_rpm_a = -current_rpm_a;
  if (target_rpm_b < 0) current_rpm_b = -current_rpm_b;

  float pid_out_a = pid_motor_a.compute(target_rpm_a, current_rpm_a);
  float pid_out_b = pid_motor_b.compute(target_rpm_b, current_rpm_b);

  int pwm_output_a = 0; int pwm_output_b = 0;
  
  if (target_rpm_a > 0.1) {
    pwm_output_a = map(pid_out_a * 1000, 0, 1000, PWM_MIN_MOV, PWM_MAX_MOV);
    if (abs(pwm_output_a) < PWM_DEADBAND) { pwm_output_a = 0; pid_motor_a.reset(); }
  } else if (target_rpm_a < -0.1) {
    pwm_output_a = map(pid_out_a * 1000, -1000, 0, -PWM_MAX_MOV, -PWM_MIN_MOV);
    if (abs(pwm_output_a) < PWM_DEADBAND) { pwm_output_a = 0; pid_motor_a.reset(); }
  }

  if (target_rpm_b > 0.1) {
    pwm_output_b = map(pid_out_b * 1000, 0, 1000, PWM_MIN_MOV, PWM_MAX_MOV);
    if (abs(pwm_output_b) < PWM_DEADBAND) { pwm_output_b = 0; pid_motor_b.reset(); }
  } else if (target_rpm_b < -0.1) {
    pwm_output_b = map(pid_out_b * 1000, -1000, 0, -PWM_MAX_MOV, -PWM_MIN_MOV);
    if (abs(pwm_output_b) < PWM_DEADBAND) { pwm_output_b = 0; pid_motor_b.reset(); }
  }

  motor_a_write(pwm_output_a);
  motor_b_write(pwm_output_b);

  rpm_left_msg.data = current_rpm_a;
  RCSOFTCHECK(rcl_publish(&rpm_left_pub, &rpm_left_msg, NULL));
  rpm_right_msg.data = current_rpm_b;
  RCSOFTCHECK(rcl_publish(&rpm_right_pub, &rpm_right_msg, NULL));
  imu_yaw_msg.data = current_yaw;
  RCSOFTCHECK(rcl_publish(&imu_yaw_pub, &imu_yaw_msg, NULL));
}

// =====================================================
// ESCRITURA FÍSICA EN PUENTES H
// =====================================================
void motor_a_write(int pwm) {
  pwm = constrain(pwm, -255, 255);
  if (pwm > 0) { digitalWrite(AIN1_PIN, HIGH); digitalWrite(AIN2_PIN, LOW); ledcWrite(PWM_CHANNEL_A, pwm); } 
  else if (pwm < 0) { digitalWrite(AIN1_PIN, LOW); digitalWrite(AIN2_PIN, HIGH); ledcWrite(PWM_CHANNEL_A, -pwm); } 
  else { digitalWrite(AIN1_PIN, LOW); digitalWrite(AIN2_PIN, LOW); ledcWrite(PWM_CHANNEL_A, 0); }
}

void motor_b_write(int pwm) {
  pwm = constrain(pwm, -255, 255);
  if (pwm > 0) { digitalWrite(BIN1_PIN, HIGH); digitalWrite(BIN2_PIN, LOW); ledcWrite(PWM_CHANNEL_B, pwm); } 
  else if (pwm < 0) { digitalWrite(BIN1_PIN, LOW); digitalWrite(BIN2_PIN, HIGH); ledcWrite(PWM_CHANNEL_B, -pwm); } 
  else { digitalWrite(BIN1_PIN, LOW); digitalWrite(BIN2_PIN, LOW); ledcWrite(PWM_CHANNEL_B, 0); }
}

// =====================================================
// MANEJO MPU6050
// =====================================================
void mpu6050_init_improved() {
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x6B); Wire.write(0); Wire.endTransmission(true);
  delay(100);
  long sum = 0; int samples = 500;
  for (int i = 0; i < samples; i++) {
    Wire.beginTransmission(MPU6050_ADDR); Wire.write(0x43); Wire.endTransmission(false);
    Wire.requestFrom((uint8_t)MPU6050_ADDR, (size_t)2, true);
    int16_t raw_x = (Wire.read() << 8) | Wire.read();
    sum += raw_x; delay(2);
  }
  gyro_x_offset = (float)sum / samples;
  last_mpu_time = millis();
  last_gyro_recal_time = millis();
}

void update_yaw_improved() {
  unsigned long current_time = millis();
  float dt = (current_time - last_mpu_time) / 1000.0; 
  last_mpu_time = current_time;
  if (dt <= 0.0) return;

  Wire.beginTransmission(MPU6050_ADDR); Wire.write(0x43); Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)MPU6050_ADDR, (size_t)2, true);
  int16_t raw_x = (Wire.read() << 8) | Wire.read();
  float gyro_x = ((float)raw_x - gyro_x_offset) / 131.0;
  if (abs(gyro_x) < GYRO_DEADBAND) gyro_x = 0.0;

  float filtered_gyro_x = gyro_filter_alpha * gyro_x + (1.0 - gyro_filter_alpha) * _prev_gyro_x_filtered;
  _prev_gyro_x_filtered = filtered_gyro_x;
  current_yaw += filtered_gyro_x * dt;

  if (millis() - last_gyro_recal_time > GYRO_RECAL_INTERVAL) {
    recalibrate_gyro_offset_dynamic();
    last_gyro_recal_time = millis();
  }
}

void recalibrate_gyro_offset_dynamic() {
  if (abs(target_rpm_a) < 5.0 && abs(target_rpm_b) < 5.0) {
    long sum = 0; int samples = 100;
    for (int i = 0; i < samples; i++) {
      Wire.beginTransmission(MPU6050_ADDR); Wire.write(0x43); Wire.endTransmission(false);
      Wire.requestFrom((uint8_t)MPU6050_ADDR, (size_t)2, true);
      int16_t raw_x = (Wire.read() << 8) | Wire.read();
      sum += raw_x; delay(1);
    }
    float new_offset = (float)sum / samples;
    gyro_x_offset = gyro_recal_old_weight * gyro_x_offset + gyro_recal_new_weight * new_offset;
  }
}

void motors_init() {
  pinMode(PWMA_PIN, OUTPUT); pinMode(AIN1_PIN, OUTPUT); pinMode(AIN2_PIN, OUTPUT);
  pinMode(PWMB_PIN, OUTPUT); pinMode(BIN1_PIN, OUTPUT); pinMode(BIN2_PIN, OUTPUT);
  pinMode(STBY_PIN, OUTPUT); digitalWrite(STBY_PIN, HIGH);
  ledcSetup(PWM_CHANNEL_A, PWM_FREQ, PWM_RESOLUTION); ledcAttachPin(PWMA_PIN, PWM_CHANNEL_A);
  ledcSetup(PWM_CHANNEL_B, PWM_FREQ, PWM_RESOLUTION); ledcAttachPin(PWMB_PIN, PWM_CHANNEL_B);
  pinMode(ENCODER_A_PIN, INPUT_PULLUP); pinMode(ENCODER_B_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A_PIN), ISR_encoder_a, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_B_PIN), ISR_encoder_b, RISING);
  motor_a_write(0); motor_b_write(0);
}

void setup() {
  Serial.begin(115200); 
  delay(500);
  pinMode(LED_PIN, OUTPUT);
  mpu6050_init();

  char ssid[] = "ZTE_2.4G_WRgugR";
  char psk[]  = "aWV6fWY6";
  char agent_ip[] = "192.168.1.102";
  set_microros_wifi_transports(ssid, psk, agent_ip, 8888);
  delay(2000);
  
  motors_init();

  allocator = rcl_get_default_allocator();
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));
  RCCHECK(rclc_node_init_default(&node, "esp32_robot_node", "", &support));

  RCCHECK(rclc_subscription_init_default(&cmd_vel_sub, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist), "/cmd_vel"));
  RCCHECK(rclc_publisher_init_default(&rpm_left_pub, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float32), "/real_rpm_left"));
  RCCHECK(rclc_publisher_init_default(&rpm_right_pub, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float32), "/real_rpm_right"));
  RCCHECK(rclc_publisher_init_default(&imu_yaw_pub, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float32), "/imu_yaw"));

  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator));
  RCCHECK(rclc_executor_add_subscription(&executor, &cmd_vel_sub, &cmd_vel_msg, &cmd_vel_callback, ON_NEW_DATA));
  
  last_control_time = millis();
  Serial.println("✅ Sistema de Posición con Auto-Reset IMU Listo\n");
}

void loop() {
  update_yaw();
  control_loop_pid();
  RCSOFTCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10)));
  delay(1);
}