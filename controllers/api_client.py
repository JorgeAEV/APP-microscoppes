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
                return response.json()
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
                return response.json()
            return None
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