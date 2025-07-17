import sys
import time
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                               QPushButton, QTextEdit, QGroupBox, QMessageBox, 
                               QFileDialog, QFrame, QSizePolicy)
from PySide6.QtCore import QTimer, Qt, QThread, Signal
from PySide6.QtGui import QFont, QPalette, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class OpenFieldApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teste de Campo Aberto - Marcação de Áreas")
        self.setGeometry(100, 100, 1400, 700)
        
        # Variáveis de controle do teste
        self.test_running = False
        self.start_time = None
        self.remaining_time = 0
        self.test_duration = 300  # Duração padrão em segundos
        self.animal_id = ""
        
        # Variáveis para armazenar o tempo acumulado em cada área
        self.corner_time = 0.0
        self.lateral_time = 0.0
        self.center_time = 0.0
        
        # Variáveis para controlar se um botão de área está atualmente pressionado
        self.corner_button_pressed = False
        self.lateral_button_pressed = False
        self.center_button_pressed = False
        
        # Variáveis para registrar o tempo de início da pressão do botão
        self.corner_press_time = None
        self.lateral_press_time = None
        self.center_press_time = None
        
        self.test_data = {}  # Para armazenar os resultados do teste atual
        
        # Timer para atualizar a interface
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        self.init_ui()
        
    def init_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal horizontal (duas colunas)
        main_layout = QHBoxLayout(central_widget)
        
        # Coluna da esquerda - Aplicação de Teste
        left_frame = QFrame()
        left_frame.setFrameStyle(QFrame.Box)
        left_frame.setLineWidth(2)
        left_layout = QVBoxLayout(left_frame)
        
        # Frame de Configuração
        config_group = QGroupBox("Configurações do Teste")
        config_layout = QGridLayout(config_group)
        
        # ID do Animal
        config_layout.addWidget(QLabel("ID do Animal:"), 0, 0)
        self.animal_id_entry = QLineEdit()
        self.animal_id_entry.setMinimumWidth(200)
        config_layout.addWidget(self.animal_id_entry, 0, 1)
        
        # Duração do Teste
        config_layout.addWidget(QLabel("Duração do Teste (segundos):"), 1, 0)
        self.duration_entry = QLineEdit()
        self.duration_entry.setText("300")
        self.duration_entry.setMinimumWidth(200)
        config_layout.addWidget(self.duration_entry, 1, 1)
        
        left_layout.addWidget(config_group)
        
        # Frame de Controle do Teste
        control_group = QGroupBox("Controle do Teste")
        control_layout = QVBoxLayout(control_group)
        
        # Timer
        self.timer_label = QLabel("Tempo Restante: 00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(24)
        self.timer_label.setFont(font)
        control_layout.addWidget(self.timer_label)
        
        # Botões de controle
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Iniciar Teste")
        self.start_button.setMinimumHeight(50)
        self.start_button.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        self.start_button.clicked.connect(self.start_test)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Parar Teste")
        self.stop_button.setMinimumHeight(50)
        self.stop_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_test)
        button_layout.addWidget(self.stop_button)
        
        control_layout.addLayout(button_layout)
        left_layout.addWidget(control_group)
        
        # Frame de Marcação de Áreas
        area_group = QGroupBox("Marcação de Áreas (Pressione e Segure)")
        area_layout = QVBoxLayout(area_group)
        
        # Botões das áreas
        buttons_layout = QGridLayout()
        
        self.corner_btn = QPushButton("Canto")
        self.corner_btn.setMinimumHeight(80)
        self.corner_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.corner_btn.setEnabled(False)
        self.corner_btn.pressed.connect(lambda: self.on_button_press("corner"))
        self.corner_btn.released.connect(lambda: self.on_button_release("corner"))
        buttons_layout.addWidget(self.corner_btn, 0, 0)
        
        self.lateral_btn = QPushButton("Lateral")
        self.lateral_btn.setMinimumHeight(80)
        self.lateral_btn.setStyleSheet("background-color: skyblue; color: black; font-weight: bold;")
        self.lateral_btn.setEnabled(False)
        self.lateral_btn.pressed.connect(lambda: self.on_button_press("lateral"))
        self.lateral_btn.released.connect(lambda: self.on_button_release("lateral"))
        buttons_layout.addWidget(self.lateral_btn, 0, 1)
        
        self.center_btn = QPushButton("Centro")
        self.center_btn.setMinimumHeight(80)
        self.center_btn.setStyleSheet("background-color: forestgreen; color: white; font-weight: bold;")
        self.center_btn.setEnabled(False)
        self.center_btn.pressed.connect(lambda: self.on_button_press("center"))
        self.center_btn.released.connect(lambda: self.on_button_release("center"))
        buttons_layout.addWidget(self.center_btn, 1, 0, 1, 2)
        
        area_layout.addLayout(buttons_layout)
        
        # Labels para exibir os tempos acumulados
        self.corner_time_label = QLabel("Tempo no Canto: 0.00 s")
        self.lateral_time_label = QLabel("Tempo na Lateral: 0.00 s")
        self.center_time_label = QLabel("Tempo no Centro: 0.00 s")
        
        area_layout.addWidget(self.corner_time_label)
        area_layout.addWidget(self.lateral_time_label)
        area_layout.addWidget(self.center_time_label)
        
        left_layout.addWidget(area_group)
        
        # Coluna da direita - Relatório e Gráfico
        right_frame = QFrame()
        right_frame.setFrameStyle(QFrame.Box)
        right_frame.setLineWidth(2)
        right_layout = QVBoxLayout(right_frame)
        
        # Frame de Relatórios
        report_group = QGroupBox("Relatório do Teste")
        report_layout = QVBoxLayout(report_group)
        
        self.report_text = QTextEdit()
        self.report_text.setMinimumHeight(200)
        self.report_text.setReadOnly(True)
        report_layout.addWidget(self.report_text)
        
        # Botões de relatório
        report_buttons_layout = QHBoxLayout()
        
        generate_button = QPushButton("Gerar/Atualizar Relatório")
        generate_button.setMinimumHeight(50)
        generate_button.clicked.connect(self.generate_report)
        report_buttons_layout.addWidget(generate_button)
        
        export_button = QPushButton("Exportar Relatório (TXT)")
        export_button.setMinimumHeight(50)
        export_button.clicked.connect(self.export_report)
        report_buttons_layout.addWidget(export_button)
        
        report_layout.addLayout(report_buttons_layout)
        right_layout.addWidget(report_group)
        
        # Frame para o gráfico
        self.chart_group = QGroupBox("Distribuição de Tempo por Área")
        self.chart_layout = QVBoxLayout(self.chart_group)
        right_layout.addWidget(self.chart_group)
        
        # Configurar proporções das colunas
        main_layout.addWidget(left_frame, 1)
        main_layout.addWidget(right_frame, 1)
        
    def start_test(self):
        if self.test_running:
            return
            
        animal_id = self.animal_id_entry.text().strip()
        if not animal_id:
            QMessageBox.warning(self, "Erro", "Por favor, insira o ID do Animal.")
            return
            
        try:
            duration = int(self.duration_entry.text())
            if duration <= 0:
                raise ValueError
            self.test_duration = duration
        except ValueError:
            QMessageBox.warning(self, "Erro", "Por favor, insira uma duração de teste válida (número inteiro positivo).")
            return
            
        self.animal_id = animal_id
        self.test_running = True
        self.start_time = time.time()
        self.remaining_time = duration
        
        # Resetar todos os tempos e estados dos botões
        self.corner_time = 0.0
        self.lateral_time = 0.0
        self.center_time = 0.0
        self.corner_button_pressed = False
        self.lateral_button_pressed = False
        self.center_button_pressed = False
        self.corner_press_time = None
        self.lateral_press_time = None
        self.center_press_time = None
        self.test_data = {}
        
        self.update_area_time_labels()
        
        # Atualizar estado dos botões
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.corner_btn.setEnabled(True)
        self.lateral_btn.setEnabled(True)
        self.center_btn.setEnabled(True)
        
        # Limpar gráfico anterior
        self.clear_chart()
        
        # Iniciar timer
        self.timer.start(200)  # Atualiza a cada 200ms
        
    def stop_test(self, manual_stop=True):
        if not self.test_running:
            return
            
        self.test_running = False
        self.timer.stop()
        
        # Atualizar estado dos botões
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.corner_btn.setEnabled(False)
        self.lateral_btn.setEnabled(False)
        self.center_btn.setEnabled(False)
        
        # Garantir que qualquer tempo ativo seja contabilizado
        if self.corner_button_pressed:
            self.on_button_release("corner")
        if self.lateral_button_pressed:
            self.on_button_release("lateral")
        if self.center_button_pressed:
            self.on_button_release("center")
            
        self.update_area_time_labels()
        self.generate_report()
        
        if manual_stop:
            QMessageBox.information(self, "Teste Finalizado", f"Teste para {self.animal_id} finalizado!")
            
    def update_timer(self):
        if self.test_running:
            elapsed_total_time = time.time() - self.start_time
            self.remaining_time = self.test_duration - elapsed_total_time
            
            # Atualizar tempos em tempo real
            if self.corner_button_pressed and self.corner_press_time:
                current_press_duration = time.time() - self.corner_press_time
                self.corner_time_label.setText(f"Tempo no Canto: {self.corner_time + current_press_duration:.2f} s")
            if self.lateral_button_pressed and self.lateral_press_time:
                current_press_duration = time.time() - self.lateral_press_time
                self.lateral_time_label.setText(f"Tempo na Lateral: {self.lateral_time + current_press_duration:.2f} s")
            if self.center_button_pressed and self.center_press_time:
                current_press_duration = time.time() - self.center_press_time
                self.center_time_label.setText(f"Tempo no Centro: {self.center_time + current_press_duration:.2f} s")
                
            if self.remaining_time <= 0:
                self.remaining_time = 0
                self.timer_label.setText("Tempo Restante: 00:00")
                self.stop_test(manual_stop=False)
                return
                
            mins = int(self.remaining_time // 60)
            secs = int(self.remaining_time % 60)
            self.timer_label.setText(f"Tempo Restante: {mins:02d}:{secs:02d}")
            
    def on_button_press(self, button_name):
        if not self.test_running:
            return
            
        # Parar outros botões ativos
        if button_name != "corner" and self.corner_button_pressed:
            self.on_button_release("corner")
        if button_name != "lateral" and self.lateral_button_pressed:
            self.on_button_release("lateral")
        if button_name != "center" and self.center_button_pressed:
            self.on_button_release("center")
            
        # Iniciar contagem do botão pressionado
        current_time = time.time()
        if button_name == "corner" and not self.corner_button_pressed:
            self.corner_button_pressed = True
            self.corner_press_time = current_time
            self.highlight_button(self.corner_btn, True)
        elif button_name == "lateral" and not self.lateral_button_pressed:
            self.lateral_button_pressed = True
            self.lateral_press_time = current_time
            self.highlight_button(self.lateral_btn, True)
        elif button_name == "center" and not self.center_button_pressed:
            self.center_button_pressed = True
            self.center_press_time = current_time
            self.highlight_button(self.center_btn, True)
            
    def on_button_release(self, button_name):
        if not self.test_running:
            return
            
        current_time = time.time()
        
        if button_name == "corner" and self.corner_button_pressed:
            elapsed = current_time - self.corner_press_time
            self.corner_time += elapsed
            self.corner_button_pressed = False
            self.corner_press_time = None
            self.highlight_button(self.corner_btn, False)
        elif button_name == "lateral" and self.lateral_button_pressed:
            elapsed = current_time - self.lateral_press_time
            self.lateral_time += elapsed
            self.lateral_button_pressed = False
            self.lateral_press_time = None
            self.highlight_button(self.lateral_btn, False)
        elif button_name == "center" and self.center_button_pressed:
            elapsed = current_time - self.center_press_time
            self.center_time += elapsed
            self.center_button_pressed = False
            self.center_press_time = None
            self.highlight_button(self.center_btn, False)
            
        self.update_area_time_labels()
        
    def highlight_button(self, button, is_pressed):
        if button == self.corner_btn:
            if is_pressed:
                button.setStyleSheet("background-color: darkgray; color: white; font-weight: bold;")
            else:
                button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        elif button == self.lateral_btn:
            if is_pressed:
                button.setStyleSheet("background-color: darkgray; color: white; font-weight: bold;")
            else:
                button.setStyleSheet("background-color: skyblue; color: black; font-weight: bold;")
        elif button == self.center_btn:
            if is_pressed:
                button.setStyleSheet("background-color: darkgray; color: white; font-weight: bold;")
            else:
                button.setStyleSheet("background-color: forestgreen; color: white; font-weight: bold;")
                
    def update_area_time_labels(self):
        self.corner_time_label.setText(f"Tempo no Canto: {self.corner_time:.2f} s")
        self.lateral_time_label.setText(f"Tempo na Lateral: {self.lateral_time:.2f} s")
        self.center_time_label.setText(f"Tempo no Centro: {self.center_time:.2f} s")
        
    def generate_report(self):
        if not self.start_time:
            QMessageBox.information(self, "Aviso", "Inicie um teste primeiro para gerar o relatório.")
            return
            
        total_duration = self.test_duration
        
        # Calcular duração efetiva
        if self.test_running:
            effective_duration = time.time() - self.start_time
        else:
            effective_duration = total_duration - self.remaining_time
            
        if effective_duration <= 0:
            effective_duration = 0.001
            
        # Calcular porcentagens
        corner_percent = (self.corner_time / effective_duration) * 100
        lateral_percent = (self.lateral_time / effective_duration) * 100
        center_percent = (self.center_time / effective_duration) * 100
        
        # Formatear relatório
        report = f"--- Relatório do Teste Open Field ---\n\n"
        report += f"ID do Animal: {self.animal_id}\n"
        report += f"Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Duração Programada do Teste: {total_duration} segundos\n"
        report += f"Duração Efetiva do Teste: {effective_duration:.2f} segundos\n\n"
        report += f"Tempo Acumulado nas Áreas:\n"
        report += f"  Canto: {self.corner_time:.2f} segundos ({corner_percent:.2f}%)\n"
        report += f"  Lateral: {self.lateral_time:.2f} segundos ({lateral_percent:.2f}%)\n"
        report += f"  Centro: {self.center_time:.2f} segundos ({center_percent:.2f}%)\n\n"
        
        self.report_text.setPlainText(report)
        
        # Armazenar dados
        self.test_data = {
            "ID do Animal": self.animal_id,
            "Data/Hora": time.strftime("%Y-%m-%d %H:%M:%S"),
            "Duração Programada (s)": total_duration,
            "Duração Efetiva (s)": effective_duration,
            "Tempo no Canto (s)": self.corner_time,
            "Porcentagem no Canto (%)": corner_percent,
            "Tempo na Lateral (s)": self.lateral_time,
            "Porcentagem na Lateral (%)": lateral_percent,
            "Tempo no Centro (s)": self.center_time,
            "Porcentagem no Centro (%)": center_percent,
        }
        
        # Gerar gráfico
        self.show_pie_chart(self.corner_time, self.lateral_time, self.center_time)
        
    def clear_chart(self):
        # Limpar widgets do gráfico
        for i in reversed(range(self.chart_layout.count())):
            child = self.chart_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
                
    def show_pie_chart(self, corner_time, lateral_time, center_time):
        self.clear_chart()
        
        labels = ['Canto', 'Lateral', 'Centro']
        sizes = [corner_time, lateral_time, center_time]
        colors = ['red', 'skyblue', 'forestgreen']
        
        # Filtrar áreas com tempo zero
        filtered_labels = []
        filtered_sizes = []
        filtered_colors = []
        for i, size in enumerate(sizes):
            if size > 0:
                filtered_sizes.append(size)
                filtered_labels.append(labels[i])
                filtered_colors.append(colors[i])
                
        if not filtered_sizes:
            label = QLabel("Nenhum tempo registrado para exibir o gráfico.")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: gray;")
            self.chart_layout.addWidget(label)
            return
            
        # Criar figura matplotlib
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        wedges, texts, autotexts = ax.pie(filtered_sizes, labels=filtered_labels, 
                                         colors=filtered_colors, autopct='%1.1f%%', 
                                         startangle=90, pctdistance=0.85)
        
        # Ajustar texto
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(10)
        for text in texts:
            text.set_fontsize(10)
            
        ax.axis('equal')
        ax.set_title("Distribuição de Tempo por Área")
        
        # Adicionar canvas ao layout
        canvas = FigureCanvas(fig)
        self.chart_layout.addWidget(canvas)
        
        # Adicionar toolbar
        toolbar = NavigationToolbar(canvas, self)
        self.chart_layout.addWidget(toolbar)
        
    def export_report(self):
        if not self.test_data:
            QMessageBox.information(self, "Nenhum Dado", "Nenhum relatório foi gerado para exportar.")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, 
            "Salvar Relatório do Teste Open Field",
            "",
            "Arquivos de Texto (*.txt);;Todos os Arquivos (*)"
        )
        
        if not filepath:
            return
            
        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(self.report_text.toPlainText())
            QMessageBox.information(self, "Exportação Concluída", 
                                  f"Relatório exportado com sucesso para:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", 
                               f"Ocorreu um erro ao exportar o relatório: {e}")

def main():
    app = QApplication(sys.argv)
    window = OpenFieldApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()