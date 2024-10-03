import sqlite3
import random

# Список из 30 имен
names = [
    "Александр", "Мария", "Дмитрий", "Елена", "Сергей",
    "Анна", "Иван", "Ольга", "Максим", "Татьяна",
    "Анастасия", "Николай", "Екатерина", "Павел", "Юлия",
    "Владимир", "Светлана", "Роман", "Дарья", "Артем",
    "Ксения", "Игорь", "Людмила", "Станислав", "Наталья",
    "Григорий", "Виктория", "Алексей", "Евгения", "Константин"
]

def creating_tables():
    # Подключение к базе данных
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()  

    query = """CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT
    );"""
    cursor.execute(query)

    query = """CREATE TABLE UserAttributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    attribute_key TEXT NOT NULL,
    attribute_value TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(id)
    );"""
    cursor.execute(query)

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

def count_attributes():
    # Подключение к базе данных
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()    

    query = """
    SELECT COUNT(DISTINCT attribute_key) AS unique_attribute_key_count
    FROM UserAttributes;"""
    cursor.execute(query)
    count_atributes = cursor.fetchall()
    if len(count_atributes) > 0:
        count_atributes = count_atributes[0][0]

    return count_atributes

def attributes() -> dict:
    attributes = {
        "Вес": {"min": 50, "max": 60},
        "Рост": {"min": 160, "max": 175}
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

    base_query = """
    SELECT u.id
    FROM Users u
    WHERE u.id IN {}
    """

    condition = "(ua.attribute_key = ? AND CAST(ua.attribute_value AS INTEGER) > ? AND CAST(ua.attribute_value AS INTEGER) < ?)"

    # Список условий для запроса
    params = []
    temp_query = []

    for attribute, limits in attributes().items():
        temp_query.append(sub_query.format(condition))
        params.extend([attribute, limits["min"], limits["max"]])
    
    where_clause = " AND ".join(temp_query)
    final_query = base_query.format(where_clause)

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

    query, user_ids = build_query_users_attributes(users)
    cursor.execute(query, user_ids)
    user_attributes = cursor.fetchall()

    count_atributes = count_attributes()
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
    grouping()

