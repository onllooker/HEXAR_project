import sqlite3
from datetime import datetime, timedelta
import random


def generate_data(start_time, num_points, base_temp):
    data = []
    current_time = datetime.strptime(start_time, "%H:%M:%S")
    for i in range(num_points):
        # Генерация данных с небольшими случайными колебаниями
        reactor_temp = base_temp + random.uniform(-2.5, 2.5)
        vapor_temp = reactor_temp * 0.5 + random.uniform(-1.0, 1.0)

        # Добавление аномалий в 5% случаев
        if random.random() < 0.05:
            reactor_temp += random.uniform(5.0, 15.0)
            comment = "Аномальное значение"
        elif random.random() < 0.1:
            reactor_temp -= random.uniform(5.0, 10.0)
            comment = "Понижение температуры"
        else:
            comment = "Нормальный режим"

        data.append((
            current_time.strftime("%H:%M:%S"),
            round(reactor_temp, 2),
            round(vapor_temp, 2),
            comment
        ))
        current_time += timedelta(seconds=15)
    return data


# Создаем базу данных
conn = sqlite3.connect('TEST_data.db')
cursor = conn.cursor()

# Создаем таблицы
cursor.execute('''
CREATE TABLE H1 (
    time TEXT PRIMARY KEY,
    reactor REAL NOT NULL,
    vapor REAL NOT NULL,
    comment TEXT
)
''')

cursor.execute('''
CREATE TABLE H2 (
    time TEXT PRIMARY KEY,
    reactor REAL NOT NULL,
    vapor REAL NOT NULL,
    comment TEXT
)
''')

# Генерируем данные для H1 (дневная смена, более высокая температура)
h1_data = generate_data("08:00:00", 800, 245.0)

# Генерируем данные для H2 (ночная смена, немного ниже температура)
h2_data = generate_data("09:00:00", 800, 235.0)

# Вставляем данные
cursor.executemany('INSERT INTO H1 VALUES (?, ?, ?, ?)', h1_data)
cursor.executemany('INSERT INTO H2 VALUES (?, ?, ?, ?)', h2_data)

# Сохраняем изменения и закрываем соединение
conn.commit()
conn.close()

print("База данных reactor_data.db успешно создана с 800 записями в каждой таблице.")