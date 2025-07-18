from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                            QProgressBar, QFileDialog)
from PyQt6.QtCore import pyqtSignal, QTimer

class SystemStatusScreen(QWidget):
    next_screen_signal = pyqtSignal()
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_system_status)
        self.update_timer.start(2000)  # Actualizar cada 2 segundos
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        self.title_label = QLabel("Estado del Sistema")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # Recursos del sistema
        self.cpu_label = QLabel("CPU: --%")
        self.ram_label = QLabel("RAM: --%")
        self.storage_label = QLabel("Almacenamiento: --%")
        self.temp_label = QLabel("Temperatura CPU: --°C")
        
        # Barras de progreso
        self.cpu_bar = QProgressBar()
        self.ram_bar = QProgressBar()
        self.storage_bar = QProgressBar()
        
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.cpu_bar)
        layout.addWidget(self.ram_label)
        layout.addWidget(self.ram_bar)
        layout.addWidget(self.storage_label)
        layout.addWidget(self.storage_bar)
        layout.addWidget(self.temp_label)
        
        # Selección de carpeta
        self.folder_button = QPushButton("Seleccionar Carpeta para Imágenes")
        self.folder_button.clicked.connect(self.select_folder)
        self.folder_label = QLabel("Carpeta seleccionada: Ninguna")
        layout.addWidget(self.folder_button)
        layout.addWidget(self.folder_label)
        
        # Botón siguiente
        self.next_button = QPushButton("Siguiente")
        self.next_button.clicked.connect(self.next_screen_signal.emit)
        layout.addWidget(self.next_button)
        
        self.setLayout(layout)
    
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if folder:
            self.folder_label.setText(f"Carpeta seleccionada: {folder}")
            # Guardar en configuración
            self.parent.api_client.save_setting("image_folder", folder)
    
    def update_system_status(self):
        # Obtener datos de la Raspberry Pi
        status = self.parent.api_client.get_system_status()
        
        if status:
            self.cpu_label.setText(f"CPU: {status['cpu']}%")
            self.ram_label.setText(f"RAM: {status['ram']}%")
            self.storage_label.setText(f"Almacenamiento: {status['storage']}%")
            self.temp_label.setText(f"Temperatura CPU: {status['temp']}°C")
            
            self.cpu_bar.setValue(status['cpu'])
            self.ram_bar.setValue(status['ram'])
            self.storage_bar.setValue(status['storage'])