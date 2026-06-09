#!/usr/bin/env python3
"""
Herramientas de diagnóstico para comunicación UDP
Ejecuta este script para probar la conexión
"""

import socket
import json
import time
import sys

# ========= CONFIGURACIÓN =========
PUERTO = 5005

# ========= COLORES PARA TERMINAL =========
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Color.BOLD}{Color.CYAN}{'='*60}{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}{text}{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}{'='*60}{Color.END}\n")

def print_success(text):
    print(f"{Color.GREEN}✅ {text}{Color.END}")

def print_error(text):
    print(f"{Color.RED}❌ {text}{Color.END}")

def print_info(text):
    print(f"{Color.BLUE}ℹ️  {text}{Color.END}")

def print_warning(text):
    print(f"{Color.YELLOW}⚠️  {text}{Color.END}")

# ========= TEST 1: OBTENER IP LOCAL =========
def test_ip_local():
    print_header("TEST 1: Obtener IP Local")
    try:
        # Método 1: Conectar a internet
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print_success(f"IP detectada: {ip}")
        return ip
    except Exception as e:
        print_error(f"No se pudo detectar IP: {e}")
        return None

# ========= TEST 2: VERIFICAR PUERTO =========
def test_puerto_disponible(puerto):
    print_header(f"TEST 2: Verificar Puerto {puerto}")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("0.0.0.0", puerto))
        s.close()
        print_success(f"Puerto {puerto} está disponible")
        return True
    except OSError as e:
        if "Address already in use" in str(e):
            print_error(f"Puerto {puerto} YA ESTÁ EN USO")
            print_info("Cierra el otro programa o usa otro puerto")
        else:
            print_error(f"Error con puerto: {e}")
        return False

# ========= TEST 3: SERVIDOR SIMPLE =========
def test_servidor_simple(puerto, timeout=10):
    print_header(f"TEST 3: Servidor UDP Simple (Timeout: {timeout}s)")
    print_info(f"Esperando paquetes en 0.0.0.0:{puerto}...")
    print_info("Presiona Ctrl+C para cancelar")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", puerto))
        sock.settimeout(timeout)
        
        print_success(f"Servidor escuchando en puerto {puerto}")
        print_warning(f"Envía un paquete UDP desde otra terminal:")
        print(f"   echo 'test' | nc -u localhost {puerto}")
        print(f"   o")
        print(f"   echo 'test' | nc -u <IP_SERVIDOR> {puerto}\n")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                print_success(f"📨 Paquete recibido de {addr[0]}:{addr[1]}")
                print_info(f"   Contenido: {data.decode('utf-8', errors='ignore')}")
                print_info(f"   Tamaño: {len(data)} bytes")
                return True
            except socket.timeout:
                continue
        
        print_warning(f"No se recibieron paquetes en {timeout} segundos")
        return False
        
    except KeyboardInterrupt:
        print_warning("\nTest cancelado por usuario")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False
    finally:
        sock.close()

# ========= TEST 4: CLIENTE SIMPLE (LOOPBACK) =========
def test_cliente_loopback(puerto):
    print_header("TEST 4: Cliente UDP Loopback (localhost)")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        mensaje = json.dumps({"cmd": "test", "timestamp": time.time()})
        
        print_info(f"Enviando a localhost:{puerto}")
        print_info(f"Mensaje: {mensaje}")
        
        sock.sendto(mensaje.encode('utf-8'), ("localhost", puerto))
        print_success("Paquete enviado correctamente")
        sock.close()
        return True
        
    except Exception as e:
        print_error(f"Error enviando: {e}")
        return False

# ========= TEST 5: CLIENTE A IP REMOTA =========
def test_cliente_remoto(ip, puerto):
    print_header(f"TEST 5: Cliente UDP a IP Remota ({ip}:{puerto})")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        
        mensaje = json.dumps({"cmd": "test", "msg": "Hola desde cliente"})
        
        print_info(f"Enviando a {ip}:{puerto}")
        print_info(f"Mensaje: {mensaje}")
        
        sock.sendto(mensaje.encode('utf-8'), (ip, puerto))
        print_success("Paquete enviado")
        
        # Intentar recibir respuesta
        print_info("Esperando respuesta (3s)...")
        try:
            data, addr = sock.recvfrom(1024)
            print_success(f"Respuesta recibida de {addr}")
            print_info(f"   {data.decode('utf-8')}")
        except socket.timeout:
            print_warning("Sin respuesta del servidor (normal si no hay servidor)")
        
        sock.close()
        return True
        
    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ========= TEST 6: FIREWALL =========
def test_firewall_info():
    print_header("TEST 6: Información de Firewall")
    print_info("Verificando configuración del firewall...")
    
    import subprocess
    
    # UFW (Ubuntu/Debian)
    try:
        result = subprocess.run(['sudo', 'ufw', 'status'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            print_info("UFW Status:")
            print(result.stdout)
    except:
        pass
    
    print_warning("Para abrir el puerto en el firewall:")
    print(f"   sudo ufw allow {PUERTO}/udp")
    print(f"   sudo firewall-cmd --add-port={PUERTO}/udp  (para firewalld)")

# ========= MENÚ PRINCIPAL =========
def menu_principal():
    while True:
        print(f"\n{Color.BOLD}🔧 HERRAMIENTAS DE DIAGNÓSTICO UDP{Color.END}")
        print(f"{Color.BOLD}{'='*60}{Color.END}")
        print("1. Test Completo (Recomendado)")
        print("2. Obtener IP Local")
        print("3. Verificar Puerto Disponible")
        print("4. Servidor Simple (Esperar paquetes)")
        print("5. Cliente Loopback (Enviar a localhost)")
        print("6. Cliente Remoto (Enviar a IP)")
        print("7. Info Firewall")
        print("0. Salir")
        print(f"{Color.BOLD}{'='*60}{Color.END}")
        
        opcion = input(f"\n{Color.CYAN}Selecciona opción: {Color.END}").strip()
        
        if opcion == "1":
            # Test completo
            ip = test_ip_local()
            if ip:
                test_puerto_disponible(PUERTO)
                print_info("\nAhora ejecuta el servidor en otra terminal:")
                print(f"   python3 udp.py")
                input(f"\n{Color.YELLOW}Presiona Enter cuando el servidor esté listo...{Color.END}")
                test_cliente_loopback(PUERTO)
                
        elif opcion == "2":
            test_ip_local()
            
        elif opcion == "3":
            test_puerto_disponible(PUERTO)
            
        elif opcion == "4":
            timeout = input("Timeout en segundos (default 30): ").strip()
            timeout = int(timeout) if timeout.isdigit() else 30
            test_servidor_simple(PUERTO, timeout)
            
        elif opcion == "5":
            test_cliente_loopback(PUERTO)
            
        elif opcion == "6":
            ip = input("IP del servidor: ").strip()
            puerto = input(f"Puerto (default {PUERTO}): ").strip()
            puerto = int(puerto) if puerto.isdigit() else PUERTO
            test_cliente_remoto(ip, puerto)
            
        elif opcion == "7":
            test_firewall_info()
            
        elif opcion == "0":
            print(f"\n{Color.GREEN}👋 ¡Hasta luego!{Color.END}\n")
            break
        else:
            print_error("Opción inválida")

# ========= CLIENTE INTERACTIVO SIMPLIFICADO =========
def cliente_interactivo():
    print_header("🎮 CLIENTE UDP INTERACTIVO")
    
    ip = input("IP del servidor: ").strip()
    puerto = input(f"Puerto (default {PUERTO}): ").strip()
    puerto = int(puerto) if puerto.isdigit() else PUERTO
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    
    print_success(f"Cliente listo para enviar a {ip}:{puerto}")
    print_info("Comandos: adelante, atras, izquierda, derecha, detener, status, salir")
    
    try:
        while True:
            cmd = input(f"\n{Color.CYAN}Comando: {Color.END}").strip().lower()
            
            if cmd == "salir":
                break
            
            if cmd in ["adelante", "atras", "izquierda", "derecha"]:
                vel = input("Velocidad (0-100, default 50): ").strip()
                vel = int(vel) if vel.isdigit() else 50
                mensaje = {"cmd": cmd, "vel": vel}
            elif cmd in ["detener", "status"]:
                mensaje = {"cmd": cmd}
            else:
                print_error("Comando no reconocido")
                continue
            
            # Enviar
            sock.sendto(json.dumps(mensaje).encode('utf-8'), (ip, puerto))
            print_success(f"Enviado: {mensaje}")
            
            # Recibir respuesta
            try:
                data, addr = sock.recvfrom(1024)
                respuesta = json.loads(data.decode('utf-8'))
                print_success(f"Respuesta: {respuesta}")
            except socket.timeout:
                print_warning("Sin respuesta del servidor")
            except Exception as e:
                print_error(f"Error: {e}")
    
    except KeyboardInterrupt:
        print_warning("\nCliente cerrado")
    finally:
        sock.close()

# ========= MAIN =========
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cliente":
        cliente_interactivo()
    else:
        try:
            menu_principal()
        except KeyboardInterrupt:
            print(f"\n\n{Color.YELLOW}Programa interrumpido{Color.END}\n")