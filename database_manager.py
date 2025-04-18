from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from PyQt5.QtWidgets import QMessageBox
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DatabaseManager:
    def __init__(self, db_name='HEXAR_data.db'):
        self.db_name=db_name
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(db_name)
        if not self.db.open():
            error_message = "Не удалось подключиться к базе данных!"
            logging.error(error_message)
            QMessageBox.critical(None, "Ошибка", error_message)
            raise Exception(error_message)
        logging.info("Подключение к базе данных успешно установлено.")

    def create_table(self, table_name):
        """Создает таблицу с указанным именем, если она не существует."""
        query = QSqlQuery()
        if not query.exec(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,
                reactor REAL NOT NULL,
                vapor REAL NOT NULL,
                comment TEXT
            )
        """):
            error_message = f"Не удалось создать таблицу {table_name}: {query.lastError().text()}"
            logging.error(error_message)
            QMessageBox.critical(None, "Ошибка", error_message)
        else:
            logging.info(f"Таблица {table_name} успешно создана или уже существует.")

    def get_model(self, table_name):
        """Возвращает модель для работы с указанной таблицей."""
        model = QSqlTableModel()
        model.setTable(table_name)
        model.setEditStrategy(QSqlTableModel.OnFieldChange)  # Автосохранение изменений
        model.select()
        return model

    def insert_data(self, table_name, time, reactor, vapor, comment=""):
        """Вставляет новую строку в указанную таблицу."""
        query = QSqlQuery()
        query.prepare(f"""
            INSERT INTO {table_name} (time, reactor, vapor, comment)
            VALUES (:time, :reactor, :vapor, :comment)
        """)
        query.bindValue(":time", time)
        query.bindValue(":reactor", reactor)
        query.bindValue(":vapor", vapor)
        query.bindValue(":comment", comment)

        if not query.exec():
            error_message = f"Не удалось вставить данные в таблицу {table_name}: {query.lastError().text()}"
            logging.error(error_message)
            QMessageBox.critical(None, "Ошибка", error_message)
        else:
            logging.info(f"Данные успешно вставлены в таблицу {table_name}.")

    def close(self):
        """Закрывает соединение с базой данных."""
        self.db.close()
        logging.info("Соединение с базой данных закрыто.")

    def __del__(self):
        """Автоматически закрывает соединение при удалении объекта."""
        self.close()

