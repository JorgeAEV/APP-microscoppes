from PyQt6.QtCore import QThread, pyqtSignal, QObject
import time
import random

class MicroscopeThread(QThread):
    video_frame = pyqtSignal(object)  # QPixmap
    status_update = pyqtSignal(dict)  # {'led_on': bool, 'temperature': float}
    
    def __init__(self, microscope_id: str, api_client):
        super().__init__()
        self.microscope_id = microscope_id
        self.api_client = api_client
        self.running = True
    
    def run(self):
        while self.running:
            # Simular actualización de estado (en implementación real, esto vendría de la API)
            status = {
                'led_on': random.random() > 0.5,
                'temperature': round(25 + random.random() * 10, 1)
            }
            self.status_update.emit(status)
            
            # Simular frame de video (en implementación real, esto procesaría el stream real)
            # self.video_frame.emit(frame_real)
            
            time.sleep(1)  # Actualizar cada segundo
    
    def stop(self):
        self.running = False
        self.wait()