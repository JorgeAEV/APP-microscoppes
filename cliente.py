import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from ui.screen_system_status import SystemStatusScreen
from ui.screen_microscopes import MicroscopesScreen
from ui.screen_calibration import CalibrationScreen
from controllers.api_client import APIClient

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Microscopios y Sensores")
        self.setGeometry(100, 100, 1024, 768)
        
        # Configurar cliente API
        self.api_client = APIClient("http://192.168.123.233:5000")  # Cambiar por IP de tu Raspberry
        
        # Verificar conexión al iniciar
        if not self.check_connection():
            QMessageBox.critical(self, "Error", "No se pudo conectar al servidor")
            sys.exit(1)
        
        # Configurar pantallas
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.system_status_screen = SystemStatusScreen(self)
        self.microscopes_screen = MicroscopesScreen(self)
        self.calibration_screen = CalibrationScreen(self)
        
        self.stacked_widget.addWidget(self.system_status_screen)
        self.stacked_widget.addWidget(self.microscopes_screen)
        self.stacked_widget.addWidget(self.calibration_screen)
        
        # Conectar señales
        self.system_status_screen.next_screen_signal.connect(self.show_microscopes)
        self.microscopes_screen.calibration_signal.connect(self.show_calibration)
        self.calibration_screen.back_signal.connect(self.show_microscopes)
        
        # Cargar datos iniciales
        self.load_initial_data()
        self.stacked_widget.setCurrentIndex(0)
    
    def check_connection(self):
        """Verifica la conexión con el servidor"""
        try:
            status = self.api_client.get_system_status()
            return status is not None
        except Exception:
            return False
    
    def load_initial_data(self):
        """Carga los datos iniciales del sistema"""
        # Actualizar estado del sistema
        self.system_status_screen.update_status()
        
        # Cargar microscopios (si hay pantalla de microscopios)
        if hasattr(self, 'microscopes_screen'):
            microscopes = self.api_client.get_microscopes()
            if microscopes:
                self.microscopes_screen.load_data(microscopes)
    
    def show_microscopes(self):
        """Muestra la pantalla de microscopios y actualiza datos"""
        self.microscopes_screen.refresh_data()
        self.stacked_widget.setCurrentIndex(1)
    
    def show_calibration(self, microscope_id):
        """Muestra la pantalla de calibración para un microscopio específico"""
        try:
            # Obtener configuración actualizada del microscopio
            config = self.api_client.get_microscope_config(microscope_id)
            if config:
                # Verificar que exista la clave 'led_intensity'
                if 'led_intensity' not in config:
                    config['led_intensity'] = 50  # Valor por defecto
                
                # Pasar solo los parámetros necesarios
                self.calibration_screen.set_microscope(microscope_id)
                self.stacked_widget.setCurrentIndex(2)
            else:
                QMessageBox.warning(self, "Error", "No se pudo cargar la configuración del microscopio")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al mostrar calibración: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())