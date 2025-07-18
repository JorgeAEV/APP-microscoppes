from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTabWidget, QGroupBox)
from PyQt6.QtCore import pyqtSignal
from controllers.microscope_thread import MicroscopeThread

class MicroscopesScreen(QWidget):
    calibration_signal = pyqtSignal(str)  # Emite ID del microscopio
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.microscopes = {}
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout()
        
        # Título
        self.title_label = QLabel("Microscopios y Sensores")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.title_label)
        
        # Controles superiores
        top_layout = QHBoxLayout()
        self.microscope_count_label = QLabel("Microscopios conectados: 0")
        self.add_button = QPushButton("Agregar Microscopio")
        self.add_button.clicked.connect(self.add_microscope)
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.clicked.connect(self.refresh_data)
        
        top_layout.addWidget(self.microscope_count_label)
        top_layout.addStretch()
        top_layout.addWidget(self.refresh_button)
        top_layout.addWidget(self.add_button)
        self.layout.addLayout(top_layout)
        
        # Área de pestañas
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        # Panel lateral de sensores
        self.sensor_group = QGroupBox("Resumen de Sensores")
        self.sensor_layout = QVBoxLayout()
        self.sensor_group.setLayout(self.sensor_layout)
        self.layout.addWidget(self.sensor_group)
        
        self.setLayout(self.layout)
    
    def load_data(self, microscopes):
        """Carga los microscopios disponibles"""
        for microscope_id in microscopes:
            self.add_microscope_tab(microscope_id)
    
    def refresh_data(self):
        """Actualiza la lista de microscopios"""
        microscopes = self.parent.api_client.get_microscopes()
        current_ids = [self.tab_widget.tabText(i) for i in range(self.tab_widget.count())]
        
        # Añadir nuevos microscopios
        for microscope_id in microscopes:
            if microscope_id not in current_ids:
                self.add_microscope_tab(microscope_id)
        
        # Actualizar contador
        self.update_microscope_count()
    
    def add_microscope(self):
        """Intenta agregar un nuevo microscopio"""
        microscopes = self.parent.api_client.get_microscopes()
        new_id = f"microscope_{len(microscopes)+1}"
        self.add_microscope_tab(new_id)
    
    def add_microscope_tab(self, microscope_id):
        """Añade una pestaña para un microscopio específico"""
        if microscope_id in self.microscopes:
            return
            
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Video del microscopio
        video_label = QLabel("Transmisión en vivo")
        video_label.setStyleSheet("background-color: black; min-height: 300px;")
        layout.addWidget(video_label)
        
        # Controles del microscopio
        controls_layout = QHBoxLayout()
        
        self.led_button = QPushButton("LED: OFF")
        self.temp_label = QLabel("Temperatura: --°C")
        cal_button = QPushButton("Calibración")
        cal_button.clicked.connect(lambda: self.calibration_signal.emit(microscope_id))
        
        controls_layout.addWidget(self.led_button)
        controls_layout.addWidget(self.temp_label)
        controls_layout.addStretch()
        controls_layout.addWidget(cal_button)
        layout.addLayout(controls_layout)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, microscope_id)
        
        # Crear y guardar hilo para este microscopio
        thread = MicroscopeThread(microscope_id, self.parent.api_client)
        thread.status_updated.connect(lambda s: self.update_microscope_status(microscope_id, s))
        thread.start()
        
        self.microscopes[microscope_id] = {
            'tab': tab,
            'thread': thread,
            'video_label': video_label
        }
        
        self.update_microscope_count()
    
    def update_microscope_status(self, microscope_id, status):
        """Actualiza la UI con el estado del microscopio"""
        if microscope_id in self.microscopes:
            controls = self.microscopes[microscope_id]
            controls['led_button'].setText(f"LED: {'ON' if status['led_on'] else 'OFF'}")
            controls['temp_label'].setText(f"Temperatura: {status['temperature']}°C")
    
    def update_microscope_count(self):
        """Actualiza el contador de microscopios"""
        count = self.tab_widget.count()
        self.microscope_count_label.setText(f"Microscopios conectados: {count}")