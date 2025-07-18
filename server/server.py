from flask import Flask, request, jsonify, send_file
import json
import os
import cv2
from datetime import datetime
import threading
import time
from flask_cors import CORS
import glob
import psutil
from SensorController import SensorController

app = Flask(__name__)
CORS(app)

# Declaración global al inicio del archivo
global IMAGE_FOLDER
IMAGE_FOLDER = 'microscope_captures'

# Inicialización de componentes
controller = SensorController()
cameras = {}  # Diccionario para múltiples cámaras
camera_lock = threading.Lock()

# Crear carpeta para imágenes si no existe
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def detect_microscopes():
    """Detecta todos los dispositivos de video conectados"""
    devices = glob.glob('/dev/video*')
    return sorted(devices)  # Ordenar para consistencia

def init_camera(camera_index=0):
    """Inicializa una cámara específica"""
    try:
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 15)
        
        time.sleep(1)  # Pausa para inicialización
        
        if not cap.isOpened():
            print(f"Error: No se pudo abrir la cámara {camera_index}")
            return None
        
        print(f"Cámara {camera_index} inicializada correctamente")
        return cap
    except Exception as e:
        print(f"Error al inicializar cámara {camera_index}: {str(e)}")
        return None

def get_system_stats():
    """Obtiene estadísticas del sistema"""
    return {
        'cpu': psutil.cpu_percent(),
        'ram': psutil.virtual_memory().percent,
        'storage': psutil.disk_usage('/').percent,
        'temp': get_cpu_temp()
    }

def get_cpu_temp():
    """Obtiene la temperatura de la CPU"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            return int(f.read()) / 1000.0
    except:
        return 0.0

# Inicializar todas las cámaras al iniciar el servidor
def initialize_all_cameras():
    global cameras
    devices = detect_microscopes()
    for i, device in enumerate(devices):
        cap = init_camera(i)
        if cap:
            cameras[f"microscope_{i+1}"] = {
                'device': device,
                'capture': cap,
                'config': {
                    'led_on': False,
                    'led_intensity': 50,
                    'resolution': '1280x720'
                }
            }

initialize_all_cameras()

# Endpoints del sistema
@app.route('/get_config', methods=['GET'])
def get_config():
    stats = get_system_stats()
    return jsonify({
        'interval': controller.interval,
        'led_intensity': controller.led_intensity,
        'led_state': controller.led_state,
        'camera_connected': len(cameras) > 0,
        'cpu_usage': stats['cpu'],
        'memory_usage': stats['ram'],
        'storage_usage': stats['storage'],
        'cpu_temp': stats['temp']
    })

@app.route('/list_microscopes', methods=['GET'])
def list_microscopes():
    microscope_list = [
        {
            'id': mid,
            'connected': True,
            'resolution': data['config']['resolution']
        } 
        for mid, data in cameras.items()
    ]
    return jsonify({
        'success': True,
        'microscopes': microscope_list,
        'count': len(cameras)
    })

@app.route('/microscope_config/<microscope_id>', methods=['GET'])
def microscope_config(microscope_id):
    if microscope_id not in cameras:
        return jsonify({'success': False, 'error': 'Microscopio no encontrado'}), 404
    
    return jsonify({
        'success': True,
        'config': cameras[microscope_id]['config']
    })

@app.route('/capture_image/<microscope_id>', methods=['GET'])
def capture_image(microscope_id):
    global IMAGE_FOLDER  # Declaración global dentro de la función
    
    if microscope_id not in cameras:
        return jsonify({'success': False, 'error': 'Microscopio no encontrado'}), 404
    
    try:
        with camera_lock:
            cap = cameras[microscope_id]['capture']
            ret, frame = cap.read()
            if not ret:
                return jsonify({'success': False, 'error': 'Error al capturar imagen'})
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{microscope_id}_{timestamp}.jpg"
            filepath = os.path.join(IMAGE_FOLDER, filename)
            
            cv2.imwrite(filepath, frame)
            return send_file(filepath, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/set_led', methods=['POST'])
def set_led():
    data = request.json
    microscope_id = data.get('microscope_id')
    state = data.get('state')
    
    if microscope_id not in cameras:
        return jsonify({'success': False, 'error': 'Microscopio no encontrado'})
    
    cameras[microscope_id]['config']['led_on'] = state
    controller.led_state = state  # Para compatibilidad con el controlador original
    controller.update_led()
    return jsonify({'success': True})

@app.route('/set_intensity', methods=['POST'])
def set_intensity():
    data = request.json
    microscope_id = data.get('microscope_id')
    intensity = data.get('intensity')
    
    if microscope_id not in cameras:
        return jsonify({'success': False, 'error': 'Microscopio no encontrado'})
    
    cameras[microscope_id]['config']['led_intensity'] = intensity
    controller.led_intensity = intensity  # Para compatibilidad con el controlador original
    controller.update_led()
    return jsonify({'success': True})

@app.route('/set_interval', methods=['POST'])
def set_interval():
    data = request.json
    controller.interval = data['interval']
    controller.save_config()
    return jsonify({'success': True})

@app.route('/get_data', methods=['GET'])
def get_data():
    sensor_data = controller.read_sensor()
    if sensor_data:
        return jsonify({
            'success': True,
            'temperature': sensor_data['temperature'],
            'humidity': sensor_data['humidity'],
            'timestamp': sensor_data['timestamp']
        })
    return jsonify({'success': False})

@app.route('/set_image_folder', methods=['POST'])
def set_image_folder():
    global IMAGE_FOLDER  # Declaración global dentro de la función
    
    try:
        data = request.json
        folder = data.get('folder', IMAGE_FOLDER)
        
        IMAGE_FOLDER = folder
        os.makedirs(folder, exist_ok=True)
        
        return jsonify({'success': True, 'message': f'Carpeta actualizada a {folder}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_camera_status', methods=['GET'])
def get_camera_status():
    status = {
        'connected': len(cameras) > 0,
        'count': len(cameras),
        'microscopes': list(cameras.keys())
    }
    return jsonify({'success': True, 'status': status})

if __name__ == '__main__':
    print(f"Microscopios detectados: {len(cameras)}")
    for mid, data in cameras.items():
        print(f"- {mid}: {data['device']}")
    
    app.run(host='0.0.0.0', port=5000, threaded=True)