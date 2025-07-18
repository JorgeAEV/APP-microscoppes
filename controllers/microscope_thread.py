from PyQt6.QtCore import QThread, pyqtSignal
import time
from datetime import datetime

class MicroscopeThread(QThread):
    status_updated = pyqtSignal(dict)
    
    def __init__(self, microscope_id, api_client):
        super().__init__()
        self.microscope_id = microscope_id
        self.api_client = api_client
    
    def run(self):
        while True:
            # Obtener estado actual del microscopio
            config = self.api_client.get_microscope_config(self.microscope_id)
            if config:
                self.status_updated.emit({
                    'led_on': config.get('led_on', False),
                    'temperature': config.get('temperature', 0.0)
                })
            self.msleep(2000)  # Actualizar cada 2 segundos
    
    def capture_image(self):
        image_path = self.api_client.capture_image(self.microscope_id)
        if image_path:
            self.image_captured.emit(image_path)
    
    def stop(self):
        self.running = False
        self.wait()