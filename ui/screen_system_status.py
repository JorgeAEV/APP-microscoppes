from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                            QProgressBar, QFileDialog, QHBoxLayout, QGroupBox)
from PyQt6.QtCore import pyqtSignal, QTimer

class SystemStatusScreen(QWidget):
    next_screen_signal = pyqtSignal()
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(2000)  # Actualizar cada 2 segundos
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        self.title_label = QLabel("Estado del Sistema")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # Panel de estado del sistema
        system_group = QGroupBox("Estado del Servidor")
        system_layout = QVBoxLayout()
        
        # Recursos del sistema
        self.cpu_label = QLabel("Uso de CPU: --%")
        self.memory_label = QLabel("Uso de Memoria: --%")
        self.storage_label = QLabel("Uso de Almacenamiento: --%")
        self.temp_label = QLabel("Temperatura CPU: --°C")
        
        # Barras de progreso
        self.cpu_bar = QProgressBar()
        self.memory_bar = QProgressBar()
        self.storage_bar = QProgressBar()
        
        system_layout.addWidget(self.cpu_label)
        system_layout.addWidget(self.cpu_bar)
        system_layout.addWidget(self.memory_label)
        system_layout.addWidget(self.memory_bar)
        system_layout.addWidget(self.storage_label)
        system_layout.addWidget(self.storage_bar)
        system_layout.addWidget(self.temp_label)
        
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)
        
        # Panel de microscopios
        microscope_group = QGroupBox("Microscopios Disponibles")
        microscope_layout = QVBoxLayout()
        
        self.microscope_count_label = QLabel("Microscopios conectados: --")
        self.microscope_list_label = QLabel()
        self.microscope_list_label.setWordWrap(True)
        
        microscope_layout.addWidget(self.microscope_count_label)
        microscope_layout.addWidget(self.microscope_list_label)
        microscope_group.setLayout(microscope_layout)
        layout.addWidget(microscope_group)
        
        # Botón siguiente
        self.next_button = QPushButton("Continuar a Microscopios")
        self.next_button.clicked.connect(self.next_screen_signal.emit)
        layout.addWidget(self.next_button)
        
        self.setLayout(layout)
    
    def update_status(self):
        status = self.parent.api_client.get_system_status()
        if status:
            # Convertir valores float a int para las barras de progreso
            cpu_usage = int(status.get('cpu_usage', 0))
            memory_usage = int(status.get('memory_usage', 0))
            storage_usage = int(status.get('storage_usage', 0))
            
            self.cpu_label.setText(f"Uso de CPU: {cpu_usage}%")
            self.memory_label.setText(f"Uso de Memoria: {memory_usage}%")
            self.storage_label.setText(f"Uso de Almacenamiento: {storage_usage}%")
            self.temp_label.setText(f"Temperatura CPU: {status.get('cpu_temp', 0)}°C")
            
            self.cpu_bar.setValue(cpu_usage)
            self.memory_bar.setValue(memory_usage)
            self.storage_bar.setValue(storage_usage)
            
            # Actualizar información de microscopios
            microscopes = self.parent.api_client.get_microscopes()
            count = len(microscopes)
            self.microscope_count_label.setText(f"Microscopios conectados: {count}")
            self.microscope_list_label.setText(", ".join(microscopes) if microscopes else "No se detectaron microscopios")