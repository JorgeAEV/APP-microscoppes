from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QSlider, QGroupBox, QDialog, 
                            QFileDialog, QFrame, QSizePolicy, QSpacerItem)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QPixmap, QColor, QFont
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Configurar el backend para evitar problemas
import matplotlib.pyplot as plt
from io import BytesIO
import cv2

class HistogramWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Análisis de Luminosidad")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)
        
        # Configurar matplotlib para mejor calidad
        plt.style.use('seaborn')
        matplotlib.rcParams['figure.dpi'] = 100
        matplotlib.rcParams['savefig.dpi'] = 300
        matplotlib.rcParams['font.size'] = 10
        
        # Crear área de gráficos
        self.create_graph_area()
        
        # Panel de estadísticas
        self.create_stats_panel()
        
        # Panel de controles
        self.create_control_panel()
        
        self.setLayout(self.layout)
    
    def create_graph_area(self):
        """Crea el área de visualización del gráfico"""
        graph_frame = QFrame()
        graph_frame.setFrameShape(QFrame.Shape.Box)
        graph_frame.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            border: 2px solid #dee2e6;
        """)
        graph_layout = QVBoxLayout(graph_frame)
        graph_layout.setContentsMargins(10, 10, 10, 10)
        
        self.figure = plt.figure(figsize=(8, 5), facecolor='#f8f9fa')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        
        # Configurar tamaño mínimo y política de expansión
        self.canvas.setMinimumSize(600, 400)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        graph_layout.addWidget(self.canvas)
        self.layout.addWidget(graph_frame, stretch=1)
        
        # Barra de herramientas de navegación
        self.toolbar = NavigationToolbar(self.canvas, self)
        graph_layout.addWidget(self.toolbar)
    
    def create_stats_panel(self):
        """Crea el panel de estadísticas"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            background-color: #e9ecef;
            border-radius: 6px;
            padding: 12px;
        """)
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setHorizontalSpacing(20)
        stats_layout.setVerticalSpacing(8)
        
        # Etiquetas de estadísticas
        titles = ["Mínimo:", "Máximo:", "Media:", "Mediana:", "Desviación:", "Moda:"]
        self.stats_labels = []
        
        for i, title in enumerate(titles):
            # Etiqueta del título
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: bold; color: #495057;")
            stats_layout.addWidget(title_label, i//3, (i%3)*2)
            
            # Etiqueta del valor
            value_label = QLabel("--")
            value_label.setStyleSheet("color: #212529; min-width: 80px;")
            stats_layout.addWidget(value_label, i//3, (i%3)*2+1)
            self.stats_labels.append(value_label)
        
        self.layout.addWidget(stats_frame)
    
    def create_control_panel(self):
        """Crea el panel de controles"""
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            background-color: #e9ecef;
            border-radius: 6px;
            padding: 10px;
        """)
        control_layout = QHBoxLayout(control_frame)
        control_layout.setSpacing(15)
        
        # Botón para guardar
        save_btn = QPushButton("💾 Guardar Imagen")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        save_btn.clicked.connect(self.save_histogram)
        
        # Botón para exportar datos
        export_btn = QPushButton("📊 Exportar Datos")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        export_btn.clicked.connect(self.export_data)
        
        # Botón para cerrar
        close_btn = QPushButton("✕ Cerrar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        close_btn.clicked.connect(self.close)
        
        control_layout.addWidget(save_btn)
        control_layout.addWidget(export_btn)
        control_layout.addStretch()
        control_layout.addWidget(close_btn)
        
        self.layout.addWidget(control_frame)
    
    def display_histogram(self, image_data):
        """Muestra el histograma con los datos de la imagen"""
        try:
            # Convertir a escala de grises si es necesario
            if len(image_data.shape) == 3:
                self.image_data = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
            else:
                self.image_data = image_data
            
            # Calcular estadísticas
            self.calculate_stats()
            
            # Generar el histograma
            self.generate_histogram()
            
            # Mostrar la ventana
            self.show()
            
        except Exception as e:
            print(f"Error al mostrar histograma: {str(e)}")
            QMessageBox.critical(self, "Error", f"No se pudo generar el histograma:\n{str(e)}")
    
    def calculate_stats(self):
        """Calcula las estadísticas de la imagen"""
        self.min_val = np.min(self.image_data)
        self.max_val = np.max(self.image_data)
        self.mean_val = np.mean(self.image_data)
        self.median_val = np.median(self.image_data)
        self.std_val = np.std(self.image_data)
        
        # Calcular moda (puede haber múltiples valores)
        vals, counts = np.unique(self.image_data, return_counts=True)
        self.mode_val = vals[np.argmax(counts)]
        
        # Actualizar la interfaz
        stats = [self.min_val, self.max_val, self.mean_val, 
                self.median_val, self.std_val, self.mode_val]
        
        for label, value in zip(self.stats_labels, stats):
            if isinstance(value, float):
                label.setText(f"{value:.2f}")
            else:
                label.setText(f"{value}")
    
    def generate_histogram(self):
        """Genera el gráfico del histograma"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Datos del histograma
        hist, bins = np.histogram(self.image_data, bins=256, range=(0, 256))
        
        # Gráfico de barras con estilo mejorado
        bars = ax.bar(bins[:-1], hist, width=1, 
                     color='#4285F4', edgecolor='#3367D6', 
                     alpha=0.8, linewidth=0.5)
        
        # Líneas de referencia
        ax.axvline(self.mean_val, color='#EA4335', linestyle='--', 
                  linewidth=1.5, label=f'Media: {self.mean_val:.1f}')
        ax.axvline(self.median_val, color='#34A853', linestyle='--', 
                  linewidth=1.5, label=f'Mediana: {self.median_val:.1f}')
        ax.axvline(self.mode_val, color='#FBBC05', linestyle='--', 
                  linewidth=1.5, label=f'Moda: {self.mode_val}')
        
        # Ajustes estéticos
        ax.set_title('Distribución de Luminosidad', pad=20, fontsize=12)
        ax.set_xlabel('Nivel de Intensidad (0-255)', fontsize=10)
        ax.set_ylabel('Frecuencia de Píxeles', fontsize=10)
        
        # Cuadrícula sutil
        ax.grid(True, linestyle=':', alpha=0.3)
        
        # Leyenda mejorada
        ax.legend(framealpha=1, facecolor='white', edgecolor='#f1f1f1')
        
        # Ajustar márgenes
        self.figure.tight_layout()
        
        # Redibujar el canvas
        self.canvas.draw()
    
    def save_histogram(self):
        """Guarda el histograma como imagen"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Histograma",
            "histograma_luminosidad.png",
            "Imágenes PNG (*.png);;Imágenes JPEG (*.jpg);;Todos los archivos (*)",
            options=options
        )
        
        if file_path:
            try:
                # Determinar formato basado en extensión
                if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                    format = 'jpg'
                    dpi = 300
                else:
                    format = 'png'
                    dpi = 300
                    if not file_path.lower().endswith('.png'):
                        file_path += '.png'
                
                # Guardar con alta calidad
                self.figure.savefig(file_path, format=format, dpi=dpi, 
                                  bbox_inches='tight', facecolor=self.figure.get_facecolor())
                
                QMessageBox.information(self, "Éxito", "Histograma guardado correctamente")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{str(e)}")
    
    def export_data(self):
        """Exporta los datos del histograma a CSV"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Datos del Histograma",
            "datos_histograma.csv",
            "Archivos CSV (*.csv);;Todos los archivos (*)",
            options=options
        )
        
        if file_path:
            try:
                hist, bins = np.histogram(self.image_data, bins=256, range=(0, 256))
                
                if not file_path.lower().endswith('.csv'):
                    file_path += '.csv'
                
                with open(file_path, 'w') as f:
                    f.write("Bin,Count\n")
                    for b, h in zip(bins[:-1], hist):
                        f.write(f"{b},{h}\n")
                
                QMessageBox.information(self, "Éxito", "Datos exportados correctamente")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo exportar los datos:\n{str(e)}")
class CalibrationScreen(QWidget):
    back_signal = pyqtSignal()
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.current_microscope = None
        self.init_ui()
        self.setup_sensor_timer()
    
    def init_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.layout.setSpacing(20)
        
        # Encabezado
        header_layout = QHBoxLayout()
        
        # Título con icono
        title_label = QLabel("🔬 Calibración del Microscopio")
        title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold;
            color: #2c3e50;
        """)
        
        # ID del microscopio con estilo
        self.microscope_id_label = QLabel("Dispositivo: --")
        self.microscope_id_label.setStyleSheet("""
            font-size: 16px;
            color: #7f8c8d;
            font-style: italic;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.microscope_id_label)
        self.layout.addLayout(header_layout)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("border: 1px solid #bdc3c7;")
        self.layout.addWidget(separator)
        
        # Área principal (video + controles)
        main_content = QHBoxLayout()
        main_content.setSpacing(25)
        
        # Panel de video (70% del espacio)
        video_frame = QFrame()
        video_frame.setFrameShape(QFrame.Shape.Box)
        video_frame.setStyleSheet("""
            background-color: black;
            border-radius: 8px;
            border: 2px solid #3498db;
        """)
        video_layout = QVBoxLayout(video_frame)
        video_layout.setContentsMargins(5, 5, 5, 5)
        
        self.video_label = QLabel("Transmisión en vivo")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            padding: 10px;
        """)
        video_layout.addWidget(self.video_label)
        
        main_content.addWidget(video_frame, stretch=7)
        
        # Panel de controles (30% del espacio) con mejor espaciado
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            background-color: #ecf0f1; 
            border-radius: 8px;
            padding: 15px;
        """)
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setSpacing(20)
        
        # Grupo de control LED con mejor espaciado
        led_group = QGroupBox("💡 Control de Iluminación")
        led_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        led_layout = QVBoxLayout(led_group)
        led_layout.setSpacing(15)
        led_layout.setContentsMargins(15, 20, 15, 15)
        
        # Botón de encendido/apagado
        self.led_toggle = QPushButton("🔴 Apagar LED")
        self.led_toggle.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-size: 14px;
                min-height: 40px;
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
        """)
        self.led_toggle.clicked.connect(self.toggle_led)
        led_layout.addWidget(self.led_toggle)
        
        # Control de intensidad con mejor espaciado
        intensity_group = QGroupBox("Intensidad")
        intensity_layout = QVBoxLayout(intensity_group)
        intensity_layout.setSpacing(10)
        
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(50)
        self.intensity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 10px;
                background: #bdc3c7;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                width: 20px;
                margin: -5px 0;
                background: #3498db;
                border-radius: 10px;
            }
            QSlider::sub-page:horizontal {
                background: #3498db;
                border-radius: 5px;
            }
        """)
        self.intensity_slider.valueChanged.connect(self.update_led_intensity)
        
        intensity_layout.addWidget(self.intensity_slider)
        led_layout.addWidget(intensity_group)
        controls_layout.addWidget(led_group)
        
        # Grupo de información con mejor espaciado
        info_group = QGroupBox("📊 Información del Sistema")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(15, 20, 15, 15)
        
        # Estilo para las etiquetas de información
        info_style = """
            QLabel {
                font-size: 14px;
                padding: 8px 0;
                min-height: 25px;
            }
        """
        
        self.resolution_label = QLabel("🖥️ Resolución: --")
        self.resolution_label.setStyleSheet(info_style)
        
        self.timestamp_label = QLabel("⏱️ Última captura: --")
        self.timestamp_label.setStyleSheet(info_style)
        
        self.temperature_label = QLabel("🌡️ Temperatura: --°C")
        self.temperature_label.setStyleSheet(info_style)
        
        self.humidity_label = QLabel("💧 Humedad: --%")
        self.humidity_label.setStyleSheet(info_style)
        
        info_layout.addWidget(self.resolution_label)
        info_layout.addWidget(self.timestamp_label)
        info_layout.addWidget(self.temperature_label)
        info_layout.addWidget(self.humidity_label)
        controls_layout.addWidget(info_group)
        
        # Espaciador flexible para empujar el botón hacia arriba
        controls_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botón de histograma con mejor espaciado
        self.histogram_button = QPushButton("📈 Generar Histograma")
        self.histogram_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 14px;
                border-radius: 5px;
                font-size: 15px;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.histogram_button.clicked.connect(self.generate_histogram)
        controls_layout.addWidget(self.histogram_button)
        
        main_content.addWidget(controls_frame, stretch=3)
        self.layout.addLayout(main_content)
        
        # Botón de regreso
        self.back_button = QPushButton("← Volver a Microscopios")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.back_button.clicked.connect(self.back_signal.emit)
        self.layout.addWidget(self.back_button)
        
        self.setLayout(self.layout)
    
    def setup_sensor_timer(self):
        """Configura el temporizador para actualizar los datos del sensor"""
        self.sensor_timer = QTimer(self)
        self.sensor_timer.timeout.connect(self.update_sensor_data)
        self.sensor_timer.start(5000)  # Actualizar cada 5 segundos
    
    def update_sensor_data(self):
        """Actualiza los datos del sensor con colores condicionales"""
        if not self.current_microscope:
            return
            
        sensor_data = self.parent.api_client.get_data()
        if sensor_data:
            # Temperatura con color condicional
            temp = sensor_data.get('temperature', '--')
            temp_color = "#e74c3c" if isinstance(temp, (int, float)) and temp > 30 else "#3498db"
            self.temperature_label.setText(f"🌡️ Temperatura: {temp}°C")
            self.temperature_label.setStyleSheet(f"font-size: 14px; color: {temp_color};")
            
            # Humedad
            humidity = sensor_data.get('humidity', '--')
            self.humidity_label.setText(f"💧 Humedad: {humidity}%")
            
            # Timestamp
            if 'timestamp' in sensor_data:
                self.timestamp_label.setText(f"⏱️ Última captura: {sensor_data['timestamp']}")
    
    def set_microscope(self, microscope_id):
        self.current_microscope = microscope_id
        self.microscope_id_label.setText(f"Dispositivo: {microscope_id}")
        
        config = self.parent.api_client.get_microscope_config(microscope_id)
        if config:
            self.intensity_slider.setValue(config.get('led_intensity', 50))
            
            # Actualizar estado LED con color
            led_on = config.get('led_on', False)
            self.led_toggle.setText("🟢 Encender LED" if not led_on else "🔴 Apagar LED")
            self.led_toggle.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#2ecc71' if led_on else '#e74c3c'};
                    color: white;
                    padding: 12px;
                    border-radius: 5px;
                    font-size: 14px;
                    min-height: 40px;
                }}
            """)
            
            self.resolution_label.setText(f"🖥️ Resolución: {config.get('resolution', '--')}")
        
        self.update_sensor_data()
    
    def toggle_led(self):
        if not self.current_microscope:
            return
            
        current_text = self.led_toggle.text()
        new_state = "🔴 Apagar LED" not in current_text
        
        success = self.parent.api_client.set_led_state(
            self.current_microscope, 
            new_state
        )
        
        if success:
            self.led_toggle.setText("🔴 Apagar LED" if new_state else "🟢 Encender LED")
            self.led_toggle.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#e74c3c' if new_state else '#2ecc71'};
                    color: white;
                    padding: 12px;
                    border-radius: 5px;
                    font-size: 14px;
                    min-height: 40px;
                }}
            """)
    
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
            
        # Obtener imagen real del microscopio (reemplazar esta parte con tu implementación)
        try:
            # Esto es solo un ejemplo - reemplazar con tu código real de captura
            image_data = self.parent.api_client.capture_image(self.current_microscope)
            if image_data is None:
                print("Error: No se pudo obtener imagen del microscopio")
                return
                
            # Convertir a numpy array (asegúrate que esta parte coincida con tu implementación)
            if isinstance(image_data, np.ndarray):
                img_array = image_data
            else:
                # Ejemplo de conversión para datos binarios
                img_array = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
                if img_array is None:
                    print("Error: No se pudo decodificar la imagen")
                    return
            
            # Crear y mostrar la ventana del histograma
            histogram_window = HistogramWindow(self)
            histogram_window.display_histogram(img_array)
            histogram_window.exec()
            
        except Exception as e:
            print(f"Error al generar histograma: {str(e)}")