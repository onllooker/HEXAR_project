from PyQt5.QtCore import Qt, QAbstractTableModel
import sqlite3


class LimitedTableModel(QAbstractTableModel):
    def __init__(self, db_path, table_name, limit=200):
        super().__init__()
        self.db_path = db_path
        self.table_name = table_name
        self.limit = limit
        self.data_cache = []
        self.load_data()

    def load_data(self):
        """Загружает последние `limit` строк из базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT rowid, time, reactor, vapor, comment FROM {self.table_name} ORDER BY rowid DESC LIMIT {self.limit}"
        )
        self.data_cache = cursor.fetchall()[::-1]  # Разворачиваем список, чтобы новые записи шли вниз
        conn.close()
        self.layoutChanged.emit()  # Обновляем таблицу в интерфейсе

    def rowCount(self, parent=None):
        return len(self.data_cache)

    def columnCount(self, parent=None):
        return 4  # Количество колонок (time, reactor, vapor, comment)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        return str(self.data_cache[index.row()][index.column() + 1])  # +1 из-за rowid

    def setData(self, index, value, role=Qt.EditRole):
        """Сохраняет изменения комментариев в базе"""
        if index.isValid() and role == Qt.EditRole:
            rowid = self.data_cache[index.row()][0]  # ID записи в БД
            new_value = value.strip()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"UPDATE {self.table_name} SET comment = ? WHERE rowid = ?", (new_value, rowid))
            conn.commit()
            conn.close()

            # Обновляем кеш и таблицу
            self.data_cache[index.row()] = (*self.data_cache[index.row()][:-1], new_value)
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        return False

    def flags(self, index):
        """Разрешаем редактирование только колонки 'Комментарий'"""
        if index.column() == 3:  # 3-я колонка — комментарий
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return ["Время", "Реактор", "Пар", "Комментарий"][section]
        return None
