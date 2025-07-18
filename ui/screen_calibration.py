from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QSlider, QGroupBox, QDialog)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

class HistogramWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histograma de Intensidad")
        self.setGeometry(100, 100, 600, 400)
        self.layout = QVBoxLayout()
        
        self.histogram_label = QLabel()
        self.histogram_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.histogram_label)
        
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.close)
        self.layout.addWidget(self.close_button)
        
        self.setLayout(self.layout)

class CalibrationScreen(QWidget):
    back_signal = pyqtSignal()
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.current_microscope = None
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout()
        
        # Título
        self.title_label = QLabel("Calibración del Microscopio")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.title_label)
        
        # ID del microscopio
        self.microscope_id_label = QLabel("Microscopio: --")
        self.layout.addWidget(self.microscope_id_label)
        
        # Video del microscopio (ahora ocupa toda la parte superior)
        self.video_label = QLabel("Vista previa")
        self.video_label.setStyleSheet("background-color: black; min-height: 400px;")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.video_label)
        
        # Controles e información en la parte inferior
        bottom_layout = QHBoxLayout()
        
        # Controles LED
        led_group = QGroupBox("Control LED")
        led_layout = QVBoxLayout()
        
        self.led_toggle = QPushButton("Apagar LED")
        self.led_toggle.clicked.connect(self.toggle_led)
        led_layout.addWidget(self.led_toggle)
        
        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(QLabel("Intensidad:"))
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.valueChanged.connect(self.update_led_intensity)
        intensity_layout.addWidget(self.intensity_slider)
        led_layout.addLayout(intensity_layout)
        
        led_group.setLayout(led_layout)
        bottom_layout.addWidget(led_group)
        
        # Información del microscopio
        info_group = QGroupBox("Información")
        info_layout = QVBoxLayout()
        
        self.resolution_label = QLabel("Resolución: --")
        self.timestamp_label = QLabel("Última captura: --")
        self.temperature_label = QLabel("Temperatura: --°C")
        self.humidity_label = QLabel("Humedad: --%")
        
        info_layout.addWidget(self.resolution_label)
        info_layout.addWidget(self.timestamp_label)
        info_layout.addWidget(self.temperature_label)
        info_layout.addWidget(self.humidity_label)
        
        # Botón de histograma (ahora en la sección de información)
        self.histogram_button = QPushButton("Generar Histograma")
        self.histogram_button.clicked.connect(self.generate_histogram)
        info_layout.addWidget(self.histogram_button)
        
        info_group.setLayout(info_layout)
        bottom_layout.addWidget(info_group)
        
        self.layout.addLayout(bottom_layout)
        
        # Botón de regreso
        self.back_button = QPushButton("Volver a Microscopios")
        self.back_button.clicked.connect(self.back_signal.emit)
        self.layout.addWidget(self.back_button)
        
        self.setLayout(self.layout)
    
    def set_microscope(self, microscope_id):
        self.current_microscope = microscope_id
        self.microscope_id_label.setText(f"Microscopio: {microscope_id}")
        
        config = self.parent.api_client.get_microscope_config(microscope_id)
        if config:
            self.intensity_slider.setValue(config.get('led_intensity', 50))
            self.led_toggle.setText("Apagar LED" if config.get('led_on', False) else "Encender LED")
            
            self.resolution_label.setText(f"Resolución: {config.get('resolution', '--')}")
            self.temperature_label.setText(f"Temperatura: {config.get('temperature', '--')}°C")
            self.humidity_label.setText(f"Humedad: {config.get('humidity', '--')}%")
    
    def toggle_led(self):
        if not self.current_microscope:
            return
            
        current_text = self.led_toggle.text()
        new_state = current_text == "Encender LED"
        
        success = self.parent.api_client.set_led_state(
            self.current_microscope, 
            new_state
        )
        
        if success:
            self.led_toggle.setText("Apagar LED" if new_state else "Encender LED")
    
    def update_led_intensity(self, value):
        if not self.current_microscope:
            return
            
        self.parent.api_client.set_led_intensity(
            self.current_microscope,
            value
        )
    
    def generate_histogram(self):
        if not self.current_microscope:
            return
            
        image_data = self.parent.api_client.capture_image(self.current_microscope)
        if not image_data:
            return
            
        img_array = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        
        # Crear ventana emergente para el histograma
        histogram_window = HistogramWindow(self)
        
        plt.figure(figsize=(6, 4))
        plt.hist(img_array.ravel(), bins=256, range=(0, 256), color='gray')
        plt.title('Histograma de Intensidad')
        plt.xlabel('Nivel de intensidad')
        plt.ylabel('Frecuencia')
        plt.grid(True)
        
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        histogram_window.histogram_label.setPixmap(pixmap.scaled(
            histogram_window.histogram_label.width(),
            histogram_window.histogram_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        ))
        
        histogram_window.exec()