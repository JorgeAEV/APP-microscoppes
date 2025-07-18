from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTabWidget, QGroupBox, QGridLayout,
                            QFrame)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt  # Asegúrate de tener Qt aquí
from PyQt6.QtGui import QFont
from controllers.microscope_thread import MicroscopeThread

class MicroscopesScreen(QWidget):
    calibration_signal = pyqtSignal(str)  # Emite ID del microscopio
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.microscopes = {}  # Diccionario para almacenar los controles de cada microscopio
        self.init_ui()
        self.setup_system_monitor()
    
    def init_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
        
        # Título con estilo mejorado
        self.title_label = QLabel("Sistema de Microscopios USB")
        self.title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #2c3e50;
            padding: 10px;
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_label)
        
        # Controles superiores
        top_layout = QHBoxLayout()
        
        # Contador de microscopios con estilo
        self.microscope_count_label = QLabel("0 dispositivos conectados")
        self.microscope_count_label.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        
        # Botones con estilo consistente
        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """
        
        self.refresh_button = QPushButton("🔄 Actualizar")
        self.refresh_button.setStyleSheet(button_style)
        self.refresh_button.clicked.connect(self.refresh_data)
        
        self.add_button = QPushButton("➕ Agregar Microscopio")
        self.add_button.setStyleSheet(button_style)
        self.add_button.clicked.connect(self.add_microscope)
        
        top_layout.addWidget(self.microscope_count_label)
        top_layout.addStretch()
        top_layout.addWidget(self.refresh_button)
        top_layout.addWidget(self.add_button)
        self.layout.addLayout(top_layout)
        
        # Separador visual
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(separator)
        
        # Área principal dividida en pestañas y sistema
        main_layout = QHBoxLayout()
        
        # Área de pestañas (80% ancho)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 12px;
                background: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
        """)
        main_layout.addWidget(self.tab_widget, stretch=4)
        
        # Panel lateral del sistema (20% ancho)
        self.system_group = QGroupBox("Estado del Sistema (RPi 3B)")
        self.system_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        
        self.system_layout = QGridLayout()
        self.system_layout.setSpacing(10)
        
        # Crear etiquetas del sistema
        self.cpu_label = self.create_system_label("CPU:")
        self.mem_label = self.create_system_label("Memoria:")
        self.temp_label = self.create_system_label("Temp CPU:")
        self.disk_label = self.create_system_label("Disco:")
        self.uptime_label = self.create_system_label("Tiempo activo:")
        
        # Añadir al layout
        self.system_layout.addWidget(self.cpu_label, 0, 0)
        self.system_layout.addWidget(self.mem_label, 1, 0)
        self.system_layout.addWidget(self.temp_label, 2, 0)
        self.system_layout.addWidget(self.disk_label, 3, 0)
        self.system_layout.addWidget(self.uptime_label, 4, 0)
        
        self.system_group.setLayout(self.system_layout)
        main_layout.addWidget(self.system_group, stretch=1)
        
        self.layout.addLayout(main_layout)
        self.setLayout(self.layout)
    
    def create_system_label(self, text):
        """Crea una etiqueta estilizada para el sistema"""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #2c3e50;
            }
        """)
        return label
    
    def setup_system_monitor(self):
        """Configura el temporizador para monitorear el sistema"""
        self.system_timer = QTimer(self)
        self.system_timer.timeout.connect(self.update_system_status)
        self.system_timer.start(3000)  # Actualizar cada 3 segundos
        self.update_system_status()  # Primera actualización
    
    def update_system_status(self):
        """Actualiza los datos del sistema Raspberry Pi"""
        status = self.parent.api_client.get_system_status()
        if status:
            self.cpu_label.setText(f"CPU: {status.get('cpu_usage', '--')}%")
            self.mem_label.setText(f"Memoria: {status.get('memory_usage', '--')}%")
            self.temp_label.setText(f"Temp CPU: {status.get('cpu_temp', '--')}°C")
            self.disk_label.setText(f"Disco: {status.get('disk_usage', '--')}%")
            self.uptime_label.setText(f"Tiempo activo: {status.get('uptime', '--')}")
    
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
        layout.setSpacing(10)
        
        # Video del microscopio con borde
        video_frame = QFrame()
        video_frame.setFrameShape(QFrame.Shape.Box)
        video_frame.setStyleSheet("background-color: black;")
        video_layout = QVBoxLayout()
        video_frame.setLayout(video_layout)
        
        video_label = QLabel("Transmisión en vivo")
        video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        video_label.setStyleSheet("color: white; font-size: 16px;")
        video_layout.addWidget(video_label)
        
        layout.addWidget(video_frame, stretch=4)
        
        # Controles del microscopio
        controls_group = QGroupBox("Controles")
        controls_layout = QHBoxLayout()
        
        # LED control con estilo
        led_button = QPushButton("🔴 LED: OFF")
        led_button.setStyleSheet("""
            QPushButton {
                padding: 8px;
                border-radius: 4px;
                background-color: #e74c3c;
                color: white;
            }
            QPushButton:checked {
                background-color: #2ecc71;
            }
        """)
        
        # Etiqueta de temperatura
        temp_label = QLabel("🌡️ Temperatura: --°C")
        temp_label.setStyleSheet("font-size: 14px;")
        
        # Botón de calibración
        cal_button = QPushButton("⚙️ Calibración")
        cal_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        cal_button.clicked.connect(lambda: self.calibration_signal.emit(microscope_id))
        
        controls_layout.addWidget(led_button)
        controls_layout.addWidget(temp_label)
        controls_layout.addStretch()
        controls_layout.addWidget(cal_button)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group, stretch=1)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, microscope_id)
        
        # Almacenar referencias a los controles
        self.microscopes[microscope_id] = {
            'tab': tab,
            'led_button': led_button,
            'temp_label': temp_label,
            'video_label': video_label,
            'video_frame': video_frame
        }
        
        # Crear y guardar hilo para este microscopio
        thread = MicroscopeThread(microscope_id, self.parent.api_client)
        thread.status_updated.connect(lambda s: self.update_microscope_status(microscope_id, s))
        thread.start()
        
        # Guardar el hilo en el diccionario
        self.microscopes[microscope_id]['thread'] = thread
        
        self.update_microscope_count()
    
    def update_microscope_status(self, microscope_id, status):
        """Actualiza la UI con el estado del microscopio"""
        if microscope_id in self.microscopes:
            controls = self.microscopes[microscope_id]
            
            # Actualizar LED
            if 'led_button' in controls:
                led_on = status.get('led_on', False)
                controls['led_button'].setText("🟢 LED: ON" if led_on else "🔴 LED: OFF")
                controls['led_button'].setStyleSheet(f"""
                    QPushButton {{
                        padding: 8px;
                        border-radius: 4px;
                        background-color: {'#2ecc71' if led_on else '#e74c3c'};
                        color: white;
                    }}
                """)
            
            # Actualizar temperatura
            if 'temp_label' in controls:
                temp = status.get('temperature', '--')
                controls['temp_label'].setText(f"🌡️ Temperatura: {temp}°C")
    
    def update_microscope_count(self):
        """Actualiza el contador de microscopios con estilo"""
        count = self.tab_widget.count()
        self.microscope_count_label.setText(f"🔬 {count} dispositivo(s) conectado(s)")
        self.microscope_count_label.setStyleSheet(f"""
            font-size: 14px; 
            color: {'#2ecc71' if count > 0 else '#e74c3c'};
            font-weight: {'bold' if count > 0 else 'normal'};
        """)