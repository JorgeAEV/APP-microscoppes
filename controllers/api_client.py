import requests
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime
import os

class APIClient(QObject):
    connection_changed = pyqtSignal(bool)
    
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 5
        
    def get_system_status(self):
        try:
            response = self.session.get(f"{self.base_url}/get_config", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return {
                    'cpu_usage': data.get('cpu_usage', 0.0),  # Puede ser float
                    'memory_usage': data.get('memory_usage', 0.0),
                    'storage_usage': data.get('storage_usage', 0.0),
                    'cpu_temp': data.get('cpu_temp', 0.0),
                    'microscopes_count': len(data.get('microscopes', []))
                }
        except requests.exceptions.RequestException:
            return None
    
    def get_microscopes(self):
        """Obtiene la lista de microscopios disponibles"""
        try:
            response = self.session.get(f"{self.base_url}/list_microscopes", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return [microscope['id'] for microscope in data.get('microscopes', [])]
            return []
        except requests.exceptions.RequestException:
            return []
    
    def get_microscope_config(self, microscope_id):
        try:
            response = self.session.get(
                f"{self.base_url}/microscope_config/{microscope_id}",
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json().get('config', {})
            return {
                'led_on': False,
                'temperature': 0.0
            }
        except requests.exceptions.RequestException:
            return None
    
    def capture_image(self, microscope_id):
        try:
            response = self.session.get(
                f"{self.base_url}/capture_image/{microscope_id}",
                timeout=self.timeout
            )
            if response.status_code == 200:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"capture_{microscope_id}_{timestamp}.jpg"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return filename
        except requests.exceptions.RequestException:
            return None
    
    def set_led_state(self, microscope_id, state):
        try:
            response = self.session.post(
                f"{self.base_url}/set_led",
                json={
                    'microscope_id': microscope_id,
                    'state': state
                },
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def set_led_intensity(self, microscope_id, intensity):
        try:
            response = self.session.post(
                f"{self.base_url}/set_intensity",
                json={
                    'microscope_id': microscope_id,
                    'intensity': intensity
                },
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
        
    def get_data(self):
        """Obtiene los datos del sensor DHT11"""
        try:
            response = requests.get(f"{self.base_url}/get_data")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {
                        'temperature': data.get('temperature'),
                        'humidity': data.get('humidity'),
                        'timestamp': data.get('timestamp')
                    }
            return None
        except Exception as e:
            print(f"Error al obtener datos del sensor: {e}")
            return None