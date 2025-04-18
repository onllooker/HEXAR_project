import sys
import seaborn as sns
import matplotlib.pyplot as plt
import mplcursors
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Пример данных
np.random.seed(0)
data = pd.DataFrame({
    'x': np.linspace(0, 10, 100),
    'y': np.sin(np.linspace(0, 10, 100)) + np.random.normal(scale=0.2, size=100),
    'label': ['Point ' + str(i) for i in range(100)]
})

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Seaborn with Hover Labels and Controls")
        self.setGeometry(100, 100, 800, 600)

        # Центральный виджет для отображения графика
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Создаем график с помощью matplotlib и Seaborn
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        sns.scatterplot(data=data, x='x', y='y', ax=self.ax)

        # Встраиваем график в PyQt
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # Добавляем кнопки управления
        control_layout = QHBoxLayout()
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        control_layout.addWidget(self.zoom_in_button)

        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        control_layout.addWidget(self.zoom_out_button)

        self.reset_button = QPushButton("Reset View")
        self.reset_button.clicked.connect(self.reset_view)
        control_layout.addWidget(self.reset_button)

        layout.addLayout(control_layout)

        # Добавляем центральный виджет
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Добавляем интерактивность (всплывающие подсказки)
        self.add_interactivity()

        # Настроим начальные параметры масштаба
        self.initial_range = {'x': (0, 10), 'y': (-2, 2)}
        self.ax.set_xlim(self.initial_range['x'])
        self.ax.set_ylim(self.initial_range['y'])

    def add_interactivity(self):
        """Добавляем всплывающие подсказки с использованием mplcursors"""
        mplcursors.cursor(self.ax, hover=True).connect("add",
            lambda sel: sel.annotation.set_text(f"Label: {data['label'][sel.index]}"))

    def zoom_in(self):
        """Масштабирование графика (увеличение)"""
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()

        # Уменьшаем диапазоны для увеличения графика
        self.ax.set_xlim(current_xlim[0] + 0.5, current_xlim[1] - 0.5)
        self.ax.set_ylim(current_ylim[0] + 0.2, current_ylim[1] - 0.2)

        self.canvas.draw()

    def zoom_out(self):
        """Масштабирование графика (уменьшение)"""
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()

        # Увеличиваем диапазоны для уменьшения графика
        self.ax.set_xlim(current_xlim[0] - 0.5, current_xlim[1] + 0.5)
        self.ax.set_ylim(current_ylim[0] - 0.2, current_ylim[1] + 0.2)

        self.canvas.draw()

    def reset_view(self):
        """Возвращаем график в исходное положение"""
        self.ax.set_xlim(self.initial_range['x'])
        self.ax.set_ylim(self.initial_range['y'])
        self.canvas.draw()

# Основной цикл приложения
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
