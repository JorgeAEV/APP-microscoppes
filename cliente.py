import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget
from ui.screen_system_status import SystemStatusScreen
from ui.screen_microscopes import MicroscopesScreen
from ui.screen_calibration import CalibrationScreen
from controllers.api_client import APIClient

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Microscopios y Sensores")
        self.setGeometry(100, 100, 1024, 768)
        
        # Cliente API para comunicación con Raspberry Pi
        self.api_client = APIClient("http://192.168.123.233:5000")
        
        # Configuración de pantallas
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Crear pantallas
        self.system_status_screen = SystemStatusScreen(self)
        self.microscopes_screen = MicroscopesScreen(self)
        self.calibration_screen = CalibrationScreen(self)
        
        # Agregar pantallas al stacked widget
        self.stacked_widget.addWidget(self.system_status_screen)
        self.stacked_widget.addWidget(self.microscopes_screen)
        self.stacked_widget.addWidget(self.calibration_screen)
        
        # Conectar señales de navegación
        self.system_status_screen.next_screen_signal.connect(self.show_microscopes)
        self.microscopes_screen.calibration_signal.connect(self.show_calibration)
        self.calibration_screen.back_signal.connect(self.show_microscopes)
        
        # Mostrar pantalla inicial
        self.stacked_widget.setCurrentIndex(0)
    
    def show_microscopes(self):
        self.microscopes_screen.load_data()
        self.stacked_widget.setCurrentIndex(1)
    
    def show_calibration(self, microscope_id):
        self.calibration_screen.set_microscope(microscope_id)
        self.stacked_widget.setCurrentIndex(2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())