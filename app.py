import logging
from datetime import datetime

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QIODevice
from PyQt5.QtSerialPort import QSerialPort

from database_manager import DatabaseManager
from ports import serial_ports, baudrate
from plot_manager import PlotHandler
from limited_table_model import LimitedTableModel  # Новый класс для таблицы


class HEXARApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("design.ui")
        self.setWindowTitle("HEXAR_synthesis")

        self.serial = QSerialPort()
        self.plot_handler = PlotHandler(self.ui)
        self.db_manager = DatabaseManager()
        self.is_logging = False

        self.ui.tableView.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)
        self.setup_ports_and_baudrates()

        # Подключение сигналов
        self.ui.connect_btn.clicked.connect(self.connect)
        self.ui.log_btn.clicked.connect(self.toggle_logging)
        self.ui.zoom_btn.clicked.connect(self.plot_handler.toggle_scale)
        self.serial.readyRead.connect(self.reading)

        logging.basicConfig(filename="app.log", level=logging.DEBUG)

    def setup_ports_and_baudrates(self):
        self.ui.SetPort.addItems(serial_ports())
        self.ui.SetBaud.addItems(baudrate())

    def reading(self):
        if self.serial.canReadLine():
            try:
                line = str(self.serial.readLine(), "utf-8").strip()
                values = line.split(";")
                if len(values) == 2:
                    timestamp = datetime.now()
                    temp1 = float(values[0])
                    temp2 = float(values[1])

                    if self.is_logging and hasattr(self, "table_name"):
                        self.auto_insert_data(self.table_name, timestamp.strftime("%H:%M:%S"), temp1, temp2)

                    # Обновляем график
                    self.plot_handler.update_plot(timestamp, temp1, temp2)

                    # Обновляем интерфейс
                    self.ui.reactor_temp.setText(f"{temp1}°C")
                    self.ui.vapor_temp.setText(f"{temp2}°C")

            except Exception as e:
                logging.error(f"Ошибка в reading: {e}")
                self.ui.statusbar.showMessage(f"Ошибка обработки данных: {e}")

    def auto_insert_data(self, table_name, time, reactor, vapor, comment=""):
        """Добавляет данные в базу и обновляет таблицу"""
        if not self.is_logging or not table_name:
            return

        self.db_manager.insert_data(table_name, time, reactor, vapor, comment)

        if hasattr(self, "model"):
            self.model.load_data()  # Загружаем только последние 200 строк
            self.ui.tableView.scrollToBottom()  # Прокручиваем вниз

    def connect(self):
        try:
            self.serial.setBaudRate(int(self.ui.SetBaud.currentText()))
            self.serial.setPortName(self.ui.SetPort.currentText())
            if self.serial.open(QIODevice.ReadWrite):
                self.ui.connect_indicator.setStyleSheet("QRadioButton::indicator { background-color : lightgreen }")
                self.ui.statusbar.showMessage("Успешное подключение")
            else:
                self.ui.statusbar.showMessage("Ошибка подключения!")
        except Exception as e:
            logging.error(f"Ошибка в connect: {e}")
            self.ui.statusbar.showMessage(f"Ошибка: {e}")

    def toggle_logging(self):
        if not self.is_logging:
            table_name = self.ui.file_name_input.toPlainText().strip()
            if not table_name:
                self.ui.statusbar.showMessage("Введите имя таблицы!")
                return

            self.table_name = "".join(e for e in table_name if e.isalnum() or e == "_")
            self.db_manager.create_table(self.table_name)

            # Используем новый класс таблицы
            db_path = self.db_manager.db_name
            self.model = LimitedTableModel(db_path, self.table_name, limit=200)
            self.ui.tableView.setModel(self.model)

            self.ui.tableView.verticalHeader().setVisible(False)

            self.is_logging = True
            self.ui.logging_indicator.setStyleSheet("QRadioButton::indicator { background-color : lightgreen }")
            self.ui.statusbar.showMessage(f"Логирование начато в таблицу {self.table_name}.")
        else:
            self.is_logging = False
            self.ui.logging_indicator.setStyleSheet("QRadioButton::indicator { background-color : red }")
            self.ui.statusbar.showMessage("Логирование остановлено.")
