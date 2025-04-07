import pyqtgraph as pg
from PyQt5 import QtWidgets
from collections import deque
from datetime import timedelta

class PlotHandler:
    def __init__(self, ui):
        self.ui = ui
        self.setup_plot()
        self.is_full_range = False  # Флаг для переключения масштаба
        self.time_window = timedelta(minutes=30)  # Окно 30 минут
        self.data = deque(maxlen=120)  # Храним последние 30 минут (120 точек по 15 сек)
        self.full_data = []  # Храним все данные

    def setup_plot(self):
        plot_container1 = self.ui.findChild(QtWidgets.QWidget, 'Plot_1')
        self.plot_widget1 = pg.PlotWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        plot_container1.setLayout(layout)
        layout.addWidget(self.plot_widget1)

        # Отключаем масштабирование по Y
        self.plot_widget1.setMouseEnabled(x=True, y=False)
        self.plot_widget1.enableAutoRange(axis=pg.ViewBox.XAxis, enable=True)

        self.plot_widget1.setBackground('w')
        self.plot_widget1.setLabel("left", "Temperature Reactor", color="b", size="12pt")
        self.plot_widget1.setLabel("bottom", "Time", color="r", size="12pt")
        self.plot_widget1.addLegend()
        self.plot_widget1.showGrid(x=True, y=True)

        # Правая ось (Температура паров)
        self.plot_widget1.setLabel("right", "Temperature Vapor", color="g", size="12pt")
        self.plot_widget1.getAxis("right").setTextPen("g")
        self.plot_widget1.showAxis("right")

        # Графики
        self.line1 = self.plot_widget1.plot(pen=pg.mkPen(color='b', width=2), name="Reactor")
        self.line2 = self.plot_widget1.plot(pen=pg.mkPen(color='g', width=2), name="Vapor")

    def update_plot(self, timestamp, temp_reactor, temp_vapor):
        """Обновляет график новыми данными."""
        self.data.append((timestamp, temp_reactor, temp_vapor))
        self.full_data.append((timestamp, temp_reactor, temp_vapor))

        self.redraw()

    def redraw(self):
        """Перерисовывает график в зависимости от масштаба."""
        if self.is_full_range:
            x_data, y1_data, y2_data = zip(*self.full_data) if self.full_data else ([], [], [])
        else:
            x_data, y1_data, y2_data = zip(*self.data) if self.data else ([], [], [])

        if x_data:
            self.line1.setData([t.timestamp() for t in x_data], y1_data)
            self.line2.setData([t.timestamp() for t in x_data], y2_data)
            self.plot_widget1.setXRange(x_data[0].timestamp(), x_data[-1].timestamp(), padding=0)

            # Настроить подписи оси X
            # Рассчитаем интервал меток в зависимости от масштаба
            window_duration = (x_data[-1] - x_data[0]).total_seconds()
            print(window_duration)
            if window_duration > 3600:  # Если окно больше часа, показывать метки реже
                tick_interval = 600  # Каждые 10 минут
            elif window_duration > 1800:  # Если окно больше 30 минут, показывать каждую минуту
                tick_interval = 60
            else:  # Для окна меньше 30 минут показывать каждую секунду
                tick_interval = 1
            # Вычисление меток для оси X
            ticks = []
            for t in x_data:
                if int(t.timestamp()) % tick_interval == 0:  # Показываем метку, если время кратно интервалу
                    ticks.append((t.timestamp(), t.strftime('%H:%M:%S')))

            # Устанавливаем метки для оси X
            self.plot_widget1.getAxis("bottom").setTicks([ticks])

    def toggle_scale(self):
        """Переключает между 30 минутами и полным масштабом."""
        self.is_full_range = not self.is_full_range
        self.redraw()
