import time
import RPi.GPIO as GPIO
import board
import adafruit_dht
from threading import Thread, Event
import json
import os

# Configuracion inicial
class SensorController:
    def __init__(self):
        # Configuracion de pines
        self.led_pin = 17
        self.dht_pin = board.D4  # GPIO4
        
        # Configuracion inicial
        self.interval = 5  # segundos (valor por defecto)
        self.led_intensity = 100  # 0-100%
        self.led_state = False
        self.running = True
        
        # Configurar GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.led_pin, GPIO.OUT)
        
        # Configurar PWM para el LED
        self.pwm = GPIO.PWM(self.led_pin, 100)  # Frecuencia 100Hz
        self.pwm.start(0)  # Iniciar con duty cycle 0
        
        # Sensor DHT11
        self.dht_sensor = adafruit_dht.DHT11(self.dht_pin)
        
        # Evento para sincronizacion
        self.stop_event = Event()
        
        # Crear archivo de configuracion si no existe
        self.config_file = 'sensor_config.json'
        if not os.path.exists(self.config_file):
            self.save_config()
        
        # Cargar configuracion
        self.load_config()
        
    def save_config(self):
        config = {
            'interval': self.interval,
            'led_intensity': self.led_intensity,
            'led_state': self.led_state
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
    
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.interval = config.get('interval', self.interval)
                self.led_intensity = config.get('led_intensity', self.led_intensity)
                self.led_state = config.get('led_state', self.led_state)
                self.update_led()
        except:
            pass
    
    def update_led(self):
        if self.led_state:
            self.pwm.ChangeDutyCycle(self.led_intensity)
        else:
            self.pwm.ChangeDutyCycle(0)
    
    def read_sensor(self):
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
        while self.running:
            # Leer sensor y controlar LED segun el intervalo
            data = self.read_sensor()
            if data:
                print(f"Datos: Temp={data['temperature']}°C, Hum={data['humidity']}%")
                with open('sensor_data.log', 'a') as f:
                    f.write(f"{data}\n")
            
            # Encender LED si esta activado
            if self.led_state:
                self.pwm.ChangeDutyCycle(self.led_intensity)
                time.sleep(1)  # LED encendido por 1 segundo
                self.pwm.ChangeDutyCycle(0)
            
            # Esperar el intervalo (menos el tiempo que el LED estuvo encendido)
            self.stop_event.wait(self.interval - 1 if self.led_state else self.interval)
    
    def stop(self):
        self.running = False
        self.stop_event.set()
        self.pwm.stop()
        self.dht_sensor.exit()  # Limpieza del sensor DHT
        GPIO.cleanup()

# Iniciar el servicio
def start_service():
    controller = SensorController()
    
    try:
        # Iniciar hilo para el loop principal
        t = Thread(target=controller.run_loop)
        t.start()
        
        # Loop para recibir comandos
        while controller.running:
            cmd = input("Comando (on/off/intensity/interval/exit): ").strip().lower()
            
            if cmd == 'exit':
                controller.stop()
                t.join()
                break
            elif cmd == 'on':
                controller.led_state = True
                controller.update_led()
                controller.save_config()
                print("LED encendido")
            elif cmd == 'off':
                controller.led_state = False
                controller.update_led()
                controller.save_config()
                print("LED apagado")
            elif cmd.startswith('intensity'):
                try:
                    intensity = int(cmd.split()[1])
                    if 0 <= intensity <= 100:
                        controller.led_intensity = intensity
                        controller.update_led()
                        controller.save_config()
                        print(f"Intensidad del LED ajustada a {intensity}%")
                    else:
                        print("La intensidad debe estar entre 0 y 100")
                except:
                    print("Uso: intensity <0-100>")
            elif cmd.startswith('interval'):
                try:
                    interval = int(cmd.split()[1])
                    if interval >= 1:
                        controller.interval = interval
                        controller.save_config()
                        print(f"Intervalo ajustado a {interval} segundos")
                    else:
                        print("El intervalo debe ser al menos 1 segundo")
                except:
                    print("Uso: interval <segundos>")
                    
    except KeyboardInterrupt:
        controller.stop()
        t.join()

if __name__ == '__main__':
    start_service()
