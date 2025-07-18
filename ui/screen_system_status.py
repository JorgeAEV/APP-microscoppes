from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                            QProgressBar, QHBoxLayout, QGroupBox, QFrame)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont, QPixmap, QIcon

class SystemStatusScreen(QWidget):
    next_screen_signal = pyqtSignal()
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        self.setup_update_timer()
    
    def init_ui(self):
        # Layout principal con márgenes y espaciado
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Encabezado con logo y título
        header_layout = QHBoxLayout()
        
        # Logo (puedes reemplazar con tu propio logo)
        logo_label = QLabel()
        logo_pixmap = QPixmap(":/icons/microscope_icon.png").scaled(80, 80, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        header_layout.addWidget(logo_label)
        
        # Título del proyecto
        title_container = QVBoxLayout()
        title_label = QLabel("MicroscopioVision Pro")
        title_label.setStyleSheet("""
            font-size: 32px; 
            font-weight: bold; 
            color: #2c3e50;
        """)
        
        subtitle_label = QLabel("Sistema de Control de Microscopios USB")
        subtitle_label.setStyleSheet("font-size: 16px; color: #7f8c8d;")
        
        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)
        title_container.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # Separador decorativo
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #3498db;")
        main_layout.addWidget(separator)
        
        # Panel de estado del sistema
        system_group = QGroupBox("📊 Estado del Servidor (Raspberry Pi 3B)")
        system_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        system_layout = QVBoxLayout()
        system_layout.setSpacing(12)
        
        # Widgets de monitoreo
        self.create_resource_widget(system_layout, "CPU", "cpu_usage", "⚙️")
        self.create_resource_widget(system_layout, "Memoria", "memory_usage", "🧠")
        self.create_resource_widget(system_layout, "Almacenamiento", "storage_usage", "💾")
        
        # Temperatura
        temp_layout = QHBoxLayout()
        temp_icon = QLabel("🌡️")
        temp_icon.setStyleSheet("font-size: 24px;")
        temp_layout.addWidget(temp_icon)
        
        self.temp_label = QLabel("Temperatura CPU: --°C")
        self.temp_label.setStyleSheet("font-size: 14px;")
        temp_layout.addWidget(self.temp_label)
        temp_layout.addStretch()
        
        system_layout.addLayout(temp_layout)
        system_group.setLayout(system_layout)
        main_layout.addWidget(system_group)
        
        # Panel de dispositivos
        device_group = QGroupBox("🔬 Microscopios Conectados")
        device_group.setStyleSheet(system_group.styleSheet())
        
        device_layout = QVBoxLayout()
        device_layout.setSpacing(10)
        
        self.microscope_count_label = QLabel()
        self.microscope_count_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.microscope_list_label = QLabel()
        self.microscope_list_label.setStyleSheet("font-size: 14px;")
        self.microscope_list_label.setWordWrap(True)
        
        device_layout.addWidget(self.microscope_count_label)
        device_layout.addWidget(self.microscope_list_label)
        device_group.setLayout(device_layout)
        main_layout.addWidget(device_group)
        
        # Botón de acción
        self.next_button = QPushButton("Iniciar Sistema")
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                border-radius: 6px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.next_button.setIcon(QIcon(":/icons/start_icon.png"))
        self.next_button.clicked.connect(self.next_screen_signal.emit)
        
        button_container = QHBoxLayout()
        button_container.addStretch()
        button_container.addWidget(self.next_button)
        button_container.addStretch()
        main_layout.addLayout(button_container)
        
        self.setLayout(main_layout)
    
    def create_resource_widget(self, layout, name, key, icon):
        """Crea un widget de recurso con barra de progreso"""
        resource_layout = QHBoxLayout()
        
        # Icono
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        resource_layout.addWidget(icon_label)
        
        # Texto y barra de progreso
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        label = QLabel(f"{name}: --%")
        label.setStyleSheet("font-size: 14px;")
        
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setStyleSheet("""
            QProgressBar {
                height: 20px;
                border-radius: 4px;
                background-color: #ecf0f1;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        
        # Guardar referencias para actualización
        setattr(self, f"{key}_label", label)
        setattr(self, f"{key}_bar", bar)
        
        text_layout.addWidget(label)
        text_layout.addWidget(bar)
        resource_layout.addLayout(text_layout)
        resource_layout.addStretch()
        
        layout.addLayout(resource_layout)
    
    def setup_update_timer(self):
        """Configura el temporizador para actualizaciones automáticas"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(2000)  # Actualizar cada 2 segundos
        self.update_status()  # Llamada inicial
    
    def update_status(self):
        """Actualiza los datos del sistema"""
        status = self.parent.api_client.get_system_status()
        if status:
            # Actualizar recursos del sistema
            for resource in ['cpu_usage', 'memory_usage', 'storage_usage']:
                value = int(status.get(resource, 0))
                getattr(self, f"{resource}_label").setText(
                    f"{resource.replace('_', ' ').title()}: {value}%"
                )
                getattr(self, f"{resource}_bar").setValue(value)
            
            # Actualizar temperatura
            cpu_temp = status.get('cpu_temp', '--')
            self.temp_label.setText(f"Temperatura CPU: {cpu_temp}°C")
            
            # Cambiar color de temperatura si es alta
            if isinstance(cpu_temp, (int, float)):
                color = "#e74c3c" if cpu_temp > 70 else "#2ecc71" if cpu_temp > 50 else "#3498db"
                self.temp_label.setStyleSheet(f"font-size: 14px; color: {color};")
            
            # Actualizar información de microscopios
            microscopes = self.parent.api_client.get_microscopes()
            count = len(microscopes)
            
            if count > 0:
                self.microscope_count_label.setText(f"🟢 {count} microscopio(s) detectado(s)")
                self.microscope_list_label.setText(
                    "Dispositivos conectados:\n" + "\n".join(
                        f"• {microscope_id}" for microscope_id in microscopes
                    )
                )
                self.next_button.setEnabled(True)
            else:
                self.microscope_count_label.setText("🔴 No se detectaron microscopios")
                self.microscope_list_label.setText("Conecte al menos un microscopio USB")
                self.next_button.setEnabled(False)