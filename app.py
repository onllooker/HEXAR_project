import logging
from datetime import datetime, timedelta
from database_dialog_window import TableDialog
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QIODevice, QTimer
from PyQt5.QtSerialPort import QSerialPort

from database_manager import DatabaseManager
from ports import baudrate
from plot_manager import PlotHandler
from limited_table_model import LimitedTableModel
from ports import PortMonitor
import os
from PyQt5.QtMultimedia import QSound


class HEXARApp(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = uic.loadUi("design.ui")
        self.setWindowTitle("HEXAR_synthesis")

        self.serial = QSerialPort()
        self.plot_handler = PlotHandler(self.ui)
        self.db_manager = DatabaseManager()
        self.is_logging = False

        self.port_monitor = PortMonitor()
        self.port_timer = QTimer()
        self.port_timer.timeout.connect(self.update_ports)
        self.port_timer.start(1000)  # Проверка портов каждую секунду

        self.connection_check_timer = QTimer()
        self.connection_check_timer.timeout.connect(self.check_connection_status)
        self.connection_check_timer.start(1000)  # Проверка связи каждую секунду
        self.last_data_received_time = datetime.now()

        self.ui.tableView.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)
        self.setup_baudrates()
        self.update_ports()

        # Подключение сигналов
        self.ui.connect_btn.clicked.connect(self.connect)
        self.ui.log_btn.clicked.connect(self.toggle_logging)
        self.ui.zoom_btn.clicked.connect(self.plot_handler.toggle_scale)
        self.serial.readyRead.connect(self.reading)
        self.ui.show_tables_btn.clicked.connect(self.show_select_table_dialog)
        self.alarm_triggered = False

        # Загрузить звук
        sound_path = os.path.join(os.path.dirname(__file__), "resources", "sounds", "warning_sound.wav")
        self.warning_sound = QSound(sound_path)

        logging.basicConfig(filename="app.log", level=logging.DEBUG)

    def setup_baudrates(self) -> None:
        self.ui.SetBaud.addItems(baudrate())

    def update_ports(self) -> None:
        added, removed = self.port_monitor.check_changes()
        current_ports = self.port_monitor.get_current_ports()

        if added or removed:
            self.ui.SetPort.clear()
            self.ui.SetPort.addItems(sorted(current_ports))

            if added:
                logging.info(f"Добавлены порты: {added}")
            if removed:
                logging.info(f"Удалены порты: {removed}")

        # Проверка: если текущий порт отключен — закрываем соединение
        current_port = self.serial.portName()
        if self.serial.isOpen() and current_port and current_port not in current_ports:
            logging.warning(f"Порт {current_port} отключён!")
            self.serial.close()
            self.ui.connect_indicator.setStyleSheet("QRadioButton::indicator { background-color : red }")
            self.ui.statusbar.showMessage(f"Порт {current_port} отключён!")

    def show_select_table_dialog(self)->None:
        dialog = TableDialog("HEXAR_data.db",self)
        dialog.exec_()
    def reading(self) -> None:
        if self.serial.canReadLine():
            self.last_data_received_time = datetime.now()  # обновляем время получения данных
            try:
                line = str(self.serial.readLine(), "utf-8").strip()
                values = line.split(";")
                if len(values) == 2:
                    timestamp = datetime.now()
                    temp1 = float(values[0])
                    temp2 = float(values[1])

                    if self.is_logging and hasattr(self, "table_name"):
                        self.auto_insert_data(self.table_name, timestamp.strftime("%H:%M:%S"), temp1, temp2)

                    self.plot_handler.update_plot(timestamp, temp1, temp2)

                    self.ui.reactor_temp.setText(f"{temp1}°C")
                    self.ui.vapor_temp.setText(f"{temp2}°C")
                    self.check_temperature_alerts(temp1, temp2)

            except Exception as e:
                logging.error(f"Ошибка в reading: {e}")
                self.ui.statusbar.showMessage(f"Ошибка обработки данных: {e}")

    def check_temperature_alerts(self, temp_reactor: float, temp_vapor: float) -> None:
        reactor_alert = temp_reactor > 250
        vapor_alert = temp_vapor > 30

        # Обновляем индикаторы
        self.ui.reactor_alarm.setStyleSheet(
            "QRadioButton::indicator { background-color : red }" if reactor_alert else "QRadioButton::indicator { background-color : lightgreen }"
        )
        self.ui.vapor_alarm.setStyleSheet(
            "QRadioButton::indicator { background-color : red }" if vapor_alert else "QRadioButton::indicator { background-color : lightgreen }"
        )

        # Воспроизводим звук один раз
        if (reactor_alert or vapor_alert) and not self.alarm_triggered:
            self.warning_sound.play()
            self.alarm_triggered = True
        elif not reactor_alert and not vapor_alert:
            self.alarm_triggered = False

    def check_connection_status(self) -> None:
        """Проверяет, не потеряна ли связь с COM-портом."""
        if self.serial.isOpen():
            elapsed = datetime.now() - self.last_data_received_time
            if elapsed > timedelta(seconds=30):
                self.serial.close()
                self.ui.connect_indicator.setStyleSheet(
                    "QRadioButton::indicator { background-color : red }"
                )
                self.ui.statusbar.showMessage("Связь с устройством потеряна!")

    def auto_insert_data(self, table_name: str, time: str, reactor: float, vapor: float, comment: str = "") -> None:
        if not self.is_logging or not table_name:
            return

        self.db_manager.insert_data(table_name, time, reactor, vapor, comment)

        if hasattr(self, "model"):
            self.model.load_data()
            self.ui.tableView.scrollToBottom()

    def connect(self) -> None:
        try:
            self.serial.setBaudRate(int(self.ui.SetBaud.currentText()))
            self.serial.setPortName(self.ui.SetPort.currentText())
            if self.serial.open(QIODevice.ReadWrite):
                self.last_data_received_time = datetime.now()
                self.ui.connect_indicator.setStyleSheet("QRadioButton::indicator { background-color : lightgreen }")
                self.ui.statusbar.showMessage("Успешное подключение")
            else:
                self.ui.statusbar.showMessage("Ошибка подключения!")
        except Exception as e:
            logging.error(f"Ошибка в connect: {e}")
            self.ui.statusbar.showMessage(f"Ошибка: {e}")

    def toggle_logging(self) -> None:
        if not self.is_logging:
            table_name = self.ui.file_name_input.toPlainText().strip()
            if not table_name:
                self.ui.statusbar.showMessage("Введите имя таблицы!")
                return

            self.table_name = "".join(e for e in table_name if e.isalnum() or e == "_")
            self.db_manager.create_table(self.table_name)

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
