import sqlite3
import random
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_name='your_database.db'):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()

class User:
    def __init__(self, attributes):
        self.attributes = attributes

    def insert(self, db: Database):
        # Вставка нового пользователя
        db.cursor.execute("INSERT INTO Users DEFAULT VALUES;")
        user_id = db.cursor.lastrowid  # Получаем id нового пользователя

        # Вставка атрибутов
        for key, value in self.attributes.items():
            if key != 'date_of_birth':
                db.cursor.execute("INSERT INTO UserAttributes (user_id, attribute_key, attribute_value) VALUES (?, ?, ?);",
                                (user_id, key, value))

        # Вставка даты рождения
        db.cursor.execute("INSERT INTO UserDateBirth (user_id, date_of_birth) VALUES (?, ?);",
                        (user_id, self.attributes['date_of_birth']))

class UserManager:
    def __init__(self, db: Database):
        self.db = db

    def select_all(self):
        query = """
        SELECT 
            u.id AS user_id,
            udb.date_of_birth,
            GROUP_CONCAT(ua.attribute_key || ': ' || ua.attribute_value, ', ') AS attributes
        FROM 
            Users u
        LEFT JOIN 
            UserAttributes ua ON u.id = ua.user_id
        LEFT JOIN 
            UserDateBirth udb ON u.id = udb.user_id
        GROUP BY 
            u.id, udb.date_of_birth;
        """
        self.db.cursor.execute(query)
        users = self.db.cursor.fetchall()
        return users

    def select_user(self, user_id):
        query = """
        SELECT 
            u.id AS user_id,
            udb.date_of_birth,
            GROUP_CONCAT(ua.attribute_key || ': ' || ua.attribute_value, ', ') AS attributes
        FROM 
            Users u
        LEFT JOIN 
            UserAttributes ua ON u.id = ua.user_id
        LEFT JOIN 
            UserDateBirth udb ON u.id = udb.user_id
        WHERE u.id = ?
        GROUP BY 
            u.id, udb.date_of_birth;
        """
        self.db.cursor.execute(query, (user_id,))
        user = self.db.cursor.fetchall()
        return user

    def create_user(self, attributes: dict):
        user = User(None, attributes)
        user.insert(self.db)
        self.db.commit()

    def delete_user(self, user_id):
        self.db.cursor.execute("DELETE FROM UserAttributes WHERE user_id = ?;", (user_id,))
        self.db.cursor.execute("DELETE FROM UserDateBirth WHERE user_id = ?;", (user_id,))
        self.db.cursor.execute("DELETE FROM Users WHERE id = ?;", (user_id,))
        self.db.commit()

    def insert_random_birth_dates(self, start_date: str, end_date: str):
        query = "SELECT MAX(id) FROM Users;"
        self.db.cursor.execute(query)
        user_ids = self.db.cursor.fetchone()[0]

        for user_id in range(1, user_ids + 1):
            random_date = self.generate_random_date(start_date, end_date)
            self.db.cursor.execute("INSERT INTO UserDateBirth (user_id, date_of_birth) VALUES (?, ?);", 
                                   (user_id, random_date))
        self.db.commit()

    def change_attribute_value(self, user_id, new_value, attribute_key):
        self.db.cursor.execute("UPDATE UserAttributes SET attribute_value = ? WHERE user_id = ? AND attribute_key = ?", (new_value, user_id, attribute_key))
        self.db.commit()  # Сохранение изменений

    def change_date_value(self, user_id, new_value):
        self.db.cursor.execute("UPDATE UserDateBirth SET date_of_birth = ? WHERE user_id = ?", (new_value, user_id))
        self.db.commit()   # Сохранение изменений

    def select_on_filter(self, attributes: dict):
        query, params = self.build_query(attributes)
        self.db.cursor.execute(query, params)
        users = self.db.cursor.fetchall()
        if not users:
            return

        query, user_ids = self.build_query_users_attributes(users)
        self.db.cursor.execute(query, user_ids)
        user_attributes = self.db.cursor.fetchall()
        if not user_attributes:
            return
        
        count_atributes = AttributeManager.count_attributes(self.db)
        if not count_atributes:
            return
        
        return user_attributes, count_atributes
    
    def build_query(self, attributes: dict) -> tuple[str, list]:
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

        for attribute, limits in attributes.items():
            if attribute == "date":
                temp_query.append(date_sub_query.format(condition_date))
                params.extend([limits["min"], limits["max"]])    
            else:
                temp_query.append(sub_query.format(condition))
                params.extend([attribute, limits["min"], limits["max"]])
        
        where_clause = "AND u.id IN".join(temp_query)
        final_query = base_query.format(where_clause)

        return final_query, params

    def build_query_users_attributes(self, users: list[tuple[int]]) -> tuple[str, list]:
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
    
    @staticmethod
    def generate_random_date(start_date: str, end_date: str) -> str:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        delta = end - start
        random_days = random.randint(0, delta.days)
        random_date = start + timedelta(days=random_days)
        return random_date.strftime("%Y-%m-%d")

class AttributeManager:
    def __init__(self, db: Database) -> None:
        self.db = db
    
    def create_attribute(self, attribute_key, attribute_value=None):
        # Запрос для получения последнего id
        query = "SELECT MAX(id) FROM Users;"
        self.db.cursor.execute(query)
        user_ids = self.db.cursor.fetchone()[0] + 1

        # Вставка атрибутов для каждого пользователя
        for user_id in range(1, user_ids):
            attributes = [
                (user_id, attribute_key, attribute_value)
            ]
            self.db.cursor.executemany("INSERT INTO UserAttributes (user_id, attribute_key, attribute_value) VALUES (?, ?, ?);", attributes)

        # Сохранение изменений и закрытие соединения
        self.db.conn.commit()
        self.db.conn.close()

    def delete_attribute(self, attribute_key):
        query = """
        DELETE FROM UserAttributes
        WHERE attribute_key = ?;""" 

        self.db.cursor.execute(query, (attribute_key,))
        self.db.conn.commit()  # Сохранение изменений

    def rename_attribute(self, attribute_key, new_attribute_key):
        self.db.cursor.execute("UPDATE UserAttributes SET attribute_key = ? WHERE attribute_key = ?", (new_attribute_key, attribute_key))
        self.db.conn.commit()  # Сохранение изменений
    
    @staticmethod
    def count_attributes(db: Database):
        query = """
        SELECT COUNT(DISTINCT attribute_key) AS unique_attribute_key_count
        FROM UserAttributes;"""
        db.cursor.execute(query)
        count_attributes = db.cursor.fetchall()
        if len(count_attributes) > 0:
            count_attributes = count_attributes[0][0]
        else:
            count_attributes = 0  # Если нет атрибутов, возвращаем 0

        return count_attributes
    
class TableManager:
    def __init__(self, db: Database):
        self.db = db

    def create_tables(self):
        self.db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT
        );""")
        self.db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS UserAttributes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            attribute_key TEXT NOT NULL,
            attribute_value TEXT,
            FOREIGN KEY (user_id) REFERENCES Users(id)
        );""")
        self.db.cursor.execute("""
        CREATE TABLE IF NOT EXISTS UserDateBirth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date_of_birth DATE,
            FOREIGN KEY (user_id) REFERENCES Users(id)
        );""")
        self.db.commit()

    def drop_tables(self):
        self.db.cursor.execute("DROP TABLE IF EXISTS UserAttributes;")
        self.db.cursor.execute("DROP TABLE IF EXISTS UserDateBirth;")
        self.db.cursor.execute("DROP TABLE IF EXISTS Users;")
        self.db.commit()
        print("Все таблицы успешно сброшены.")




if __name__ == "__main__":
    db = Database('your_database.db')
    table_manager = TableManager(db)
    table_manager.create_tables()
    user_manager = UserManager(db)
    attributes = {
        "Вес": {"min": 50, "max": 80},
        "Рост": {"min": 150, "max": 180}
        # "date": {"min": start_date, "max": end_date}
    }
    users = user_manager.select_on_filter(attributes)
    print(users)
    # all_users = user_manager.select_all()
    # user_manager.change_attribute_value(1, "test", "Test")
    # user = user_manager.select_user(1)
    # print(all_users)
    # print(user)
    
