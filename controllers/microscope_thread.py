from PyQt6.QtCore import QThread, pyqtSignal
import time
from datetime import datetime

class MicroscopeThread(QThread):
    status_updated = pyqtSignal(dict)
    image_captured = pyqtSignal(str)  # Path de la imagen
    
    def __init__(self, microscope_id, api_client):
        super().__init__()
        self.microscope_id = microscope_id
        self.api_client = api_client
        self.running = True
        self.update_interval = 2  # segundos
    
    def run(self):
        while self.running:
            # Obtener estado del microscopio
            status = {
                'led_on': False,
                'temperature': 25.0,
                'last_update': datetime.now().strftime("%H:%M:%S")
            }
            self.status_updated.emit(status)
            
            time.sleep(self.update_interval)
    
    def capture_image(self):
        image_path = self.api_client.capture_image(self.microscope_id)
        if image_path:
            self.image_captured.emit(image_path)
    
    def stop(self):
        self.running = False
        self.wait()