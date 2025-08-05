import time
import RPi.GPIO as GPIO
import board
import adafruit_dht
from threading import Thread, Event
import json
import os

class CameraSystemController:
    def __init__(self):
        # Configuración de pines para cada cámara (ID: pin_GPIO)
        self.cameras = {
            'cam1': {'led_pin': 17, 'led_intensity': 100, 'led_state': False},
            'cam2': {'led_pin': 22, 'led_intensity': 100, 'led_state': False},
        }
        #     'cam3': {'led_pin': 22, 'led_intensity': 100, 'led_state': False},
        #     'cam4': {'led_pin': 23, 'led_intensity': 100, 'led_state': False}
        # }
        
        # Configuración general
        self.interval = 5  # segundos (valor por defecto)
        self.led_auto_on_duration = 1  # segundos que permanecen encendidos los LEDs en modo automático
        self.running = True
        
        # Configurar GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Configurar PWM para cada LED
        self.pwms = {}
        for cam_id, config in self.cameras.items():
            GPIO.setup(config['led_pin'], GPIO.OUT)
            self.pwms[cam_id] = GPIO.PWM(config['led_pin'], 100)  # Frecuencia 100Hz
            self.pwms[cam_id].start(0)  # Iniciar con duty cycle 0
        
        # Sensor DHT11 (único para todo el sistema)
        self.dht_pin = board.D4  # GPIO4
        self.dht_sensor = adafruit_dht.DHT11(self.dht_pin)
        
        # Evento para sincronización
        self.stop_event = Event()
        
        # Archivo de configuración
        self.config_file = 'camera_system_config.json'
        if not os.path.exists(self.config_file):
            self.save_config()
        
        # Cargar configuración
        self.load_config()
        
    def save_config(self):
        config = {
            'interval': self.interval,
            'led_auto_on_duration': self.led_auto_on_duration,
            'cameras': self.cameras
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.interval = config.get('interval', self.interval)
                self.led_auto_on_duration = config.get('led_auto_on_duration', self.led_auto_on_duration)
                
                # Actualizar configuración de cada cámara
                for cam_id in self.cameras.keys():
                    if cam_id in config.get('cameras', {}):
                        self.cameras[cam_id].update(config['cameras'][cam_id])
                        self.update_led(cam_id)
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def update_led(self, cam_id):
        """Actualiza el estado del LED de una cámara específica"""
        if cam_id in self.pwms and cam_id in self.cameras:
            config = self.cameras[cam_id]
            if config['led_state']:
                self.pwms[cam_id].ChangeDutyCycle(config['led_intensity'])
            else:
                self.pwms[cam_id].ChangeDutyCycle(0)
    
    def update_all_leds(self):
        """Actualiza todos los LEDs según su configuración"""
        for cam_id in self.cameras.keys():
            self.update_led(cam_id)
    
    def auto_on_leds(self):
        """Enciende todos los LEDs según su intensidad configurada por un tiempo determinado"""
        for cam_id, pwm in self.pwms.items():
            intensity = self.cameras[cam_id]['led_intensity']
            pwm.ChangeDutyCycle(intensity)
        
        time.sleep(self.led_auto_on_duration)
        
        for pwm in self.pwms.values():
            pwm.ChangeDutyCycle(0)
    
    def read_sensor(self):
        """Lee el sensor DHT11 compartido"""
        try:
            temperature = self.dht_sensor.temperature
            humidity = self.dht_sensor.humidity
            if humidity is not None and temperature is not None:
                return {
                    'temperature': temperature,
                    'humidity': humidity,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                }
        except RuntimeError as e:
            print(f"Error reading sensor: {e}")
        return None
    
    def run_loop(self):
        """Bucle principal del sistema"""
        while self.running:
            # Leer sensor
            data = self.read_sensor()
            if data:
                print(f"Datos ambientales: Temp={data['temperature']}°C, Hum={data['humidity']}%")
                with open('sensor_data.log', 'a') as f:
                    f.write(f"{data}\n")
            
            # Encender LEDs en modo automático
            self.auto_on_leds()
            
            # Esperar el intervalo (menos el tiempo que los LEDs estuvieron encendidos)
            self.stop_event.wait(self.interval - self.led_auto_on_duration)
    
    def stop(self):
        """Detener el sistema y limpiar recursos"""
        self.running = False
        self.stop_event.set()
        
        # Detener todos los PWMs
        for pwm in self.pwms.values():
            pwm.stop()
        
        # Limpiar sensor DHT
        self.dht_sensor.exit()
        GPIO.cleanup()

def start_service():
    controller = CameraSystemController()
    
    try:
        # Iniciar hilo para el loop principal
        t = Thread(target=controller.run_loop)
        t.start()
        
        # Loop para recibir comandos
        while controller.running:
            print("\nSistema de control de cámaras")
            print("Comandos disponibles:")
            print("  list - Listar cámaras y estados")
            print("  on <cam_id> - Encender LED de cámara")
            print("  off <cam_id> - Apagar LED de cámara")
            print("  intensity <cam_id> <0-100> - Ajustar intensidad")
            print("  interval <segundos> - Cambiar intervalo automático")
            print("  duration <segundos> - Cambiar duración encendido automático")
            print("  exit - Salir del programa")
            
            cmd = input("Comando: ").strip().lower().split()
            
            if not cmd:
                continue
                
            if cmd[0] == 'exit':
                controller.stop()
                t.join()
                break
                
            elif cmd[0] == 'list':
                print("\nEstado de las cámaras:")
                for cam_id, config in controller.cameras.items():
                    state = "ENCENDIDO" if config['led_state'] else "APAGADO"
                    print(f"{cam_id}: LED {state} (Intensidad: {config['led_intensity']}%)")
                print(f"\nIntervalo automático: {controller.interval}s")
                print(f"Duración encendido automático: {controller.led_auto_on_duration}s")
                
            elif cmd[0] in ['on', 'off'] and len(cmd) > 1:
                cam_id = cmd[1]
                if cam_id in controller.cameras:
                    controller.cameras[cam_id]['led_state'] = (cmd[0] == 'on')
                    controller.update_led(cam_id)
                    controller.save_config()
                    state = "encendido" if cmd[0] == 'on' else "apagado"
                    print(f"LED de {cam_id} {state}")
                else:
                    print(f"Cámara {cam_id} no encontrada")
                    
            elif cmd[0] == 'intensity' and len(cmd) > 2:
                cam_id = cmd[1]
                try:
                    intensity = int(cmd[2])
                    if 0 <= intensity <= 100 and cam_id in controller.cameras:
                        controller.cameras[cam_id]['led_intensity'] = intensity
                        controller.update_led(cam_id)
                        controller.save_config()
                        print(f"Intensidad del LED en {cam_id} ajustada a {intensity}%")
                    else:
                        print("La intensidad debe estar entre 0 y 100 o la cámara no existe")
                except ValueError:
                    print("Uso: intensity <cam_id> <0-100>")
                    
            elif cmd[0] == 'interval' and len(cmd) > 1:
                try:
                    interval = int(cmd[1])
                    if interval >= 1:
                        controller.interval = interval
                        controller.save_config()
                        print(f"Intervalo automático ajustado a {interval} segundos")
                    else:
                        print("El intervalo debe ser al menos 1 segundo")
                except ValueError:
                    print("Uso: interval <segundos>")
                    
            elif cmd[0] == 'duration' and len(cmd) > 1:
                try:
                    duration = int(cmd[1])
                    if duration >= 0:
                        controller.led_auto_on_duration = duration
                        controller.save_config()
                        print(f"Duración de encendido automático ajustada a {duration} segundos")
                    else:
                        print("La duración no puede ser negativa")
                except ValueError:
                    print("Uso: duration <segundos>")
                    
            else:
                print("Comando no reconocido")
                    
    except KeyboardInterrupt:
        controller.stop()
        t.join()

if __name__ == '__main__':
    start_service()