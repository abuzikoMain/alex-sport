import sqlite3
import random
from datetime import datetime, timedelta

# Список из 30 имен
names = [
    "Александр", "Мария", "Дмитрий", "Елена", "Сергей",
    "Анна", "Иван", "Ольга", "Максим", "Татьяна",
    "Анастасия", "Николай", "Екатерина", "Павел", "Юлия",
    "Владимир", "Светлана", "Роман", "Дарья", "Артем",
    "Ксения", "Игорь", "Людмила", "Станислав", "Наталья",
    "Григорий", "Виктория", "Алексей", "Евгения", "Константин"
]

def generate_random_date(start_date: str, end_date: str) -> str:
    """Генерирует случайную дату между двумя датами."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_date = start + timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%d")

def insert_random_birth_dates():
    """Заполняет таблицу UserDateBirth случайными датами рождения."""
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    # Укажите диапазон дат для генерации
    start_date = "1950-01-01"
    end_date = "2000-12-31"

    query = "SELECT MAX(id) FROM Users;"
    cursor.execute(query)
    user_ids = cursor.fetchone()[0]

    for user_id in range(1, user_ids + 1):
        random_date = generate_random_date(start_date, end_date)
        cursor.execute("INSERT INTO UserDateBirth (user_id, date_of_birth) VALUES (?, ?);", (user_id, random_date))

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()

def insert_data():
    count = 10
    query = ""

    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor() 

    # Вставка пользователей
    # Вставка пользователей
    for _ in range(count):
        cursor.execute("INSERT INTO Users DEFAULT VALUES;")

    # Получение последних добавленных идентификаторов
    user_ids = cursor.lastrowid - count + 1

    # Вставка атрибутов для каждого пользователя
    for user_id in range(user_ids, user_ids + count):
        random_name = random.choice(names)
        random_weight = random.randint(50, 95)
        random_height = random.randint(150, 190)

        attributes = [
            (user_id, 'Имя', random_name),
            (user_id, 'Вес', random_weight),
            (user_id, 'Рост', random_height)
        ]

        cursor.executemany("INSERT INTO UserAttributes (user_id, attribute_key, attribute_value) VALUES (?, ?, ?);", attributes)

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()

def insert_attribute(attribute_key, attribute_value=None):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()  

    # Запрос для получения последнего id
    query = "SELECT MAX(id) FROM Users;"
    cursor.execute(query)
    user_ids = cursor.fetchone()[0] + 1

    # Вставка атрибутов для каждого пользователя
    for user_id in range(1, user_ids):
        attributes = [
            (user_id, attribute_key, attribute_value)
        ]
        cursor.executemany("INSERT INTO UserAttributes (user_id, attribute_key, attribute_value) VALUES (?, ?, ?);", attributes)

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()

def delete_attribute(attribute_key):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor() 

    query = """
    DELETE FROM UserAttributes
    WHERE attribute_key = ?;""" 

    cursor.execute(query, (attribute_key,))
    conn.commit()  # Сохранение изменений

def rename_attribute(attribute_key, new_attribute_key):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor() 

    cursor.execute("UPDATE UserAttributes SET attribute_key = ? WHERE attribute_key = ?", (new_attribute_key, attribute_key))
    conn.commit()  # Сохранение изменений

def change_attribute_value(user_id, new_value):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor() 

    cursor.execute("UPDATE UserAttributes SET attribute_value = ? WHERE user_id = ?", (new_value, user_id))
    conn.commit()  # Сохранение изменений

def change_date_value(user_id, new_value):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor() 

    cursor.execute("UPDATE UserDateBirth SET date_of_birth = ? WHERE user_id = ?", (new_value, user_id))
    conn.commit()  # Сохранение изменений

def insert_user(attributes: dict):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor() 

    # Вставка нового пользователя
    cursor.execute("INSERT INTO Users DEFAULT VALUES;")
    user_id = cursor.lastrowid  # Получаем id нового пользователя

    # Вставка атрибутов
    for key, value in attributes.items():
        if key != 'date_of_birth':
            cursor.execute("INSERT INTO UserAttributes (user_id, attribute_key, attribute_value) VALUES (?, ?, ?);",
                            (user_id, key, value))

    # Вставка даты рождения
    cursor.execute("INSERT INTO UserDateBirth (user_id, date_of_birth) VALUES (?, ?);",
                    (user_id, attributes['date_of_birth']))

    conn.commit()  # Сохранение изменений

def delete_user(user_id):
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()     
    
    # Удаление атрибутов пользователя
    cursor.execute("DELETE FROM UserAttributes WHERE user_id = ?;", (user_id,))
    
    # Удаление даты рождения пользователя
    cursor.execute("DELETE FROM UserDateBirth WHERE user_id = ?;", (user_id,))
    
    # Удаление пользователя
    cursor.execute("DELETE FROM Users WHERE id = ?;", (user_id,))
    
    conn.commit()  # Сохранение изменений

def creating_tables():
    # Подключение к базе данных
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()  

    query = """
    CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT
    );"""
    cursor.execute(query)

    query = """
    CREATE TABLE IF NOT EXISTS UserAttributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    attribute_key TEXT NOT NULL,
    attribute_value TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(id)
    );"""
    cursor.execute(query)

    query = """
    CREATE TABLE IF NOT EXISTS UserDateBirth (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
	date_of_birth DATE,
	FOREIGN KEY (user_id) REFERENCES Users(id)
    );"""
    cursor.execute(query)

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()

def drop_tables():
    # Сброс всех таблиц
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()         

    cursor.execute("DROP TABLE IF EXISTS UserAttributes;")
    cursor.execute("DROP TABLE IF EXISTS UserDateBirth;")
    cursor.execute("DROP TABLE IF EXISTS Users;")
    
    conn.commit()  # Сохранение изменений
    print("Все таблицы успешно сброшены.")
    
def count_attributes():
    # Подключение к базе данных
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()    

    query = """
    SELECT COUNT(DISTINCT attribute_key) AS unique_attribute_key_count
    FROM UserAttributes;"""
    cursor.execute(query)
    count_attributes = cursor.fetchall()
    if len(count_attributes) > 0:
        count_attributes = count_attributes[0][0]
    else:
        count_attributes = 0  # Если нет атрибутов, возвращаем 0

    return count_attributes

def attributes() -> dict:
    start_date = '1970-01-01'
    end_date = '1990-12-31'

    # attributes = {
    #     "date": {"min": start_date, "max": end_date}
    # }

    attributes = {
        "Вес": {"min": 50, "max": 80},
        "Рост": {"min": 150, "max": 180},
        "date": {"min": start_date, "max": end_date}
    }
    return attributes

def build_query() -> tuple[str, list]:
    """
    Return tuple[str, list]
    str: sql_query
    list: params of sql_query
    """
     # Начало построения запроса
    sub_query = """
    (SELECT u.id
    FROM Users u
    JOIN UserAttributes ua ON u.id = ua.user_id
    WHERE {})
    """

    date_sub_query = """
    (SELECT u.id
    FROM Users u 
    JOIN UserDateBirth ud ON u.id = ud.user_id
    WHERE {})
    """

    base_query = """
    SELECT u.id
    FROM Users u
    WHERE u.id IN {}
    """

    condition_date = "date_of_birth BETWEEN ? AND ?"
    condition = "(ua.attribute_key = ? AND CAST(ua.attribute_value AS INTEGER) >= ? AND CAST(ua.attribute_value AS INTEGER) <= ?)"

    # Список условий для запроса
    params = []
    temp_query = []

    for attribute, limits in attributes().items():
        if attribute == "date":
            temp_query.append(date_sub_query.format(condition_date))
            params.extend([limits["min"], limits["max"]])    
        else:
            temp_query.append(sub_query.format(condition))
            params.extend([attribute, limits["min"], limits["max"]])
    
    where_clause = "AND u.id IN".join(temp_query)
    final_query = base_query.format(where_clause)
    print(final_query)
    print(params)

    return final_query, params

def build_query_users_attributes(users: list[tuple[int]]) -> tuple[str, list]:
    # Получаем список идентификаторов пользователей
    user_ids = [user[0] for user in users]
    placeholders = ', '.join('?' for _ in user_ids)
    query = f"""
    SELECT 
        u.id AS user_id,
        ua.attribute_key,
        ua.attribute_value
    FROM 
        Users u
    LEFT JOIN 
        UserAttributes ua ON u.id = ua.user_id
    WHERE u.id IN ({placeholders})
    ORDER BY 
        u.id;"""
    return query, user_ids

def distribute_users(data, n):
    groups = []
    for i in range(0, len(data), n):
        group = data[i:i + n]
        groups.append(group)
    return groups

def output(result):
    for idx, group in enumerate(result):
        print(f"Группа {idx + 1}:")
        for user in group:
            for attribute in user:
                print(f"{attribute[1]}: {attribute[2]}")
            print("\n")
        print(f"------------\n")

def grouping():
    # Подключение к базе данных
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    query, params = build_query()
    cursor.execute(query, params)
    users = cursor.fetchall()
    if not users:
        return

    query, user_ids = build_query_users_attributes(users)
    cursor.execute(query, user_ids)
    user_attributes = cursor.fetchall()
    if not user_attributes:
        return

    count_atributes = count_attributes()
    if not count_atributes:
        return
    
    # Разделение на группы
    groups = [user_attributes[i:i + count_atributes] for i in range(0, len(user_attributes), count_atributes)]
    random.shuffle(groups)

    # Задайте количество человек в группе
    N = 3
    result = distribute_users(groups, N)

    output(result=result)

    # Закрытие соединения
    conn.close()

if __name__ == "__main__":
    # creating_tables()
    # insert_data()
    # grouping()
    # insert_attribute("Test")
    # insert_random_birth_dates()
    # delete_attribute("Test")
    drop_tables()
    creating_tables()

