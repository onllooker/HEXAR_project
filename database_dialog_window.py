from PyQt5.QtWidgets import QDialog, QListWidgetItem, QMessageBox, QVBoxLayout, QWidget
from PyQt5 import uic
import sqlite3
import pyqtgraph as pg
import pandas as pd
from pyqtgraph import AxisItem
from pyqtgraph import ScatterPlotItem


class TimeAxis(AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [f"{int(val)} мин" for val in values]


class TableDialog(QDialog):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi("select_table_dialog.ui", self)

        self.db_path = db_path
        self._load_table_names()
        self._setup_plots()

        self.ui.view_btn.clicked.connect(self._plot_selected_tables)
        self.ui.delete_btn.clicked.connect(self._delete_tables)
        self.ui.cancel_btn.clicked.connect(self.close)


    def _setup_plots(self) -> None:
        self.all_widget = self._add_plot_to_tab('all_data')
        self.reactor_widget = self._add_plot_to_tab('reactor_data')
        self.vapor_widget = self._add_plot_to_tab('vapor_data')


    def _plot_comment_points(self, widget: pg.PlotWidget, df: pd.DataFrame):
        comments = df[df['comment'].notnull() & (df['comment'] != '')]
        if comments.empty:
            return

        spots = []
        for i, row in comments.iterrows():
            spots.append({
                'pos': (row['delta_time'], row['reactor']),  # или row['vapor']
                'data': row['comment'],
                'brush': pg.mkBrush(255, 0, 0, 150),
                'symbol': 'o',
                'size': 10
            })

        scatter = ScatterPlotItem(spots=spots)
        widget.addItem(scatter)

    # def _lock_view_to_data(self, widget: pg.PlotWidget, df: pd.DataFrame):
    #     x_min = df['delta_time'].min()
    #     x_max = df['delta_time'].max()
    #     y_min = min(df['reactor'].min(), df['vapor'].min())
    #     y_max = max(df['reactor'].max(), df['vapor'].max())
    #
    #     vb = widget.getViewBox()
    #
    #     # Устанавливаем границы (пользователь не сможет выйти за них)
    #     vb.setLimits(xMin=x_min, xMax=x_max, yMin=y_min, yMax=y_max)
    #
    #     # Устанавливаем видимую область графика
    #     vb.setRange(xRange=(x_min, x_max), yRange=(y_min, y_max), padding=0.9)

    def _add_plot_to_tab(self, tab_name: str) -> pg.PlotWidget:
        container = self.ui.findChild(QWidget, tab_name)

        # Используем кастомную ось X
        plot_widget = pg.PlotWidget(axisItems={'bottom': TimeAxis(orientation='bottom')})
        plot_widget.setBackground('w')
        plot_widget.addLegend()
        plot_widget.showGrid(x=True, y=True)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)
        layout.addWidget(plot_widget)
        return plot_widget

    def _filter_outliers(self, series: pd.Series, window: int = 5, min_val: float = 19,
                         max_val: float = 200) -> pd.Series:
        filtered = series.copy()
        rolling_avg = series.rolling(window=window, center=True, min_periods=1).mean()

        outliers = (series < min_val) | (series > max_val)
        filtered[outliers] = rolling_avg[outliers]

        return filtered

    def _load_table_names(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = sorted(cursor.fetchall())
            conn.close()

            self.ui.tables.clear()
            for table in tables:
                item = QListWidgetItem(table[0])
                item.setCheckState(0)
                self.ui.tables.addItem(item)

        except Exception as e:
            self.ui.tables.addItem(f"Ошибка загрузки таблиц: {e}")

    def _get_checked_tables(self)->list[str]:
        checked = []
        for i in range(self.ui.tables.count()):
            item = self.ui.tables.item(i)
            if item.checkState():
                checked.append(item.text())
        return checked

    def _load_table_data(self, table_name: str) -> pd.DataFrame:
        try:
            query = f"SELECT time, reactor, vapor, comment FROM '{table_name}'"
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn)

            # Преобразование времени с защитой (пункт 7)
            df['time'] = pd.to_datetime(df['time'], format="%H:%M:%S", errors='coerce')
            df.dropna(subset=['time'], inplace=True)
            return df

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных из таблицы {table_name}:\n{e}")
            return pd.DataFrame()

    def _plot_selected_tables(self):
        selected_tables = self._get_checked_tables()
        if not selected_tables:
            self.all_widget.clear()
            self.reactor_widget.clear()
            self.vapor_widget.clear()
            print("Не выбраны таблицы.")
            return

        self.all_widget.clear()
        self.reactor_widget.clear()
        self.vapor_widget.clear()

        colors = ['blue', 'green', 'red', 'orange', 'purple', 'brown', 'cyan', 'magenta']

        with sqlite3.connect(self.db_path) as conn:
            for idx, table in enumerate(selected_tables):
                try:
                    df = pd.read_sql_query(
                        f"SELECT time, reactor, vapor, comment FROM '{table}'", conn
                    )
                    df['time'] = pd.to_datetime(df['time'], format="%H:%M:%S", errors='coerce')
                    df.dropna(subset=['time'], inplace=True)

                    if df.empty:
                        continue

                    # Расчёт дельта-времени от первой точки (в минутах)
                    start_time = df['time'].iloc[0]
                    df['delta_time'] = (df['time'] - start_time).dt.total_seconds() / 60

                    color = colors[idx % len(colors)]
                    self._plot_data(df, table, color)

                except Exception as e:
                    print(f"Ошибка при обработке таблицы {table}: {e}")

    def _plot_data(self, df: pd.DataFrame, table: str, color: str):
        x = df['delta_time']  # Минуты с начала
        if self.ui.filter_checkbox.isChecked():
            reactor = self._filter_outliers(df['reactor'])
            vapor = self._filter_outliers(df['vapor'])
        else:
            reactor = df['reactor']
            vapor = df['vapor']

        self.all_widget.plot(x, reactor, pen=pg.mkPen(color, width=2), name=f'{table} R')
        self.all_widget.plot(x, vapor, pen=pg.mkPen(color, style=pg.QtCore.Qt.DashLine, width=2), name=f'{table} V')
        self.reactor_widget.plot(x, reactor, pen=pg.mkPen(color,width=2), name=table)
        self.vapor_widget.plot(x, vapor, pen=pg.mkPen(color,width=2), name=table)

        self._plot_comment_points(self.all_widget, df)

        # self._lock_view_to_data(self.all_widget, df)
        # self._lock_view_to_data(self.reactor_widget, df)
        # self._lock_view_to_data(self.vapor_widget, df)

    def _delete_tables(self):
        selected_tables = self._get_checked_tables()
        if not selected_tables:
            return

        reply = QMessageBox.question(self, "Удаление", f"Удалить {len(selected_tables)} таблиц(ы)?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                for table in selected_tables:
                    cursor.execute(f"DROP TABLE IF EXISTS '{table}'")
                conn.commit()
                conn.close()
                self._load_table_names()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении таблиц:\n{e}")
