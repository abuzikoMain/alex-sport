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
        if self.attributes:
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

    def select_all(self, return_type: str = None):
        users_attributes = self.fetch_users_attributes()
        return self.aggregate_user_attributes(users_attributes)

    def fetch_users_attributes(self):
        query = """
        SELECT 
            u.id AS user_id,
            ua.attribute_key,
            ua.attribute_value
        FROM 
            Users u
        LEFT JOIN 
            UserAttributes ua ON u.id = ua.user_id   
        """
        self.db.cursor.execute(query)
        return self.db.cursor.fetchall()

    def aggregate_user_attributes(self, users_attributes):
        users = {}
        for user_id, attribute_key, attribute_value in users_attributes:
            # Используем user_id напрямую, так как он уже соответствует id пользователя
            if user_id not in users:
                users[user_id] = {}
            users[user_id][attribute_key] = attribute_value
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
        return self.db.cursor.fetchall()

    def create_user(self, attributes: dict):
        user = User(attributes)
        user.insert(self.db)
        self.db.commit()

    def delete_user(self, user_id):
        self.delete_user_attributes(user_id)
        self.delete_user_date_of_birth(user_id)
        self.delete_user_record(user_id)
        self.db.commit()

    def delete_user_attributes(self, user_id):
        self.db.cursor.execute("DELETE FROM UserAttributes WHERE user_id = ?;", (user_id,))

    def delete_user_date_of_birth(self, user_id):
        self.db.cursor.execute("DELETE FROM UserDateBirth WHERE user_id = ?;", (user_id,))

    def delete_user_record(self, user_id):
        self.db.cursor.execute("DELETE FROM Users WHERE id = ?;", (user_id,))

    def insert_random_birth_dates(self, start_date: str, end_date: str):
        user_ids = self.fetch_all_user_ids()
        for user_id in user_ids:
            random_date = self.generate_random_date(start_date, end_date)
            self.insert_birth_date(user_id, random_date)
        self.db.commit()

    def fetch_all_user_ids(self):
        query = "SELECT MAX(id) FROM Users;"
        self.db.cursor.execute(query)
        return range(1, self.db.cursor.fetchone()[0] + 1)

    def insert_birth_date(self, user_id, random_date):
        self.db.cursor.execute("INSERT INTO UserDateBirth (user_id, date_of_birth) VALUES (?, ?);", 
                               (user_id, random_date))

    def change_attribute_value(self, user_id, new_value, attribute_key):
        self.db.cursor.execute("UPDATE UserAttributes SET attribute_value = ? WHERE user_id = ? AND attribute_key = ?", 
                               (new_value, user_id, attribute_key))
        self.db.commit()

    def change_date_value(self, user_id, new_value):
        self.db.cursor.execute("UPDATE UserDateBirth SET date_of_birth = ? WHERE user_id = ?", 
                               (new_value, user_id))
        self.db.commit()

    def select_on_filter(self, attributes: dict):
        query, params = self.build_query(attributes)
        self.db.cursor.execute(query, params)
        users = self.db.cursor.fetchall()
        if not users:
            return

        user_attributes = self.fetch_user_attributes(users)
        if count_attributes := self.count_unique_attributes():
            return user_attributes, count_attributes
        else:
            return

    def fetch_user_attributes(self, users):
        query, user_ids = self.build_query_users_attributes(users)
        self.db.cursor.execute(query, user_ids)
        return self.db.cursor.fetchall()

    def count_unique_attributes(self):
        return AttributeManager.count_attributes(self.db)

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
        if not self.validate_attribute(attribute_key):
            raise ValueError(f"Attribute '{attribute_key}' already exists.")  # Генерация исключения

        user_ids = self.fetch_all_user_ids()
        self.insert_attributes_for_users(user_ids, attribute_key, attribute_value)
        self.insert_attribute_name(attribute_key)

    def fetch_all_user_ids(self):
        query = "SELECT id FROM Users;"
        self.db.cursor.execute(query)
        return [user[0] for user in self.db.cursor.fetchall()]

    def insert_attributes_for_users(self, user_ids, attribute_key, attribute_value):
        attributes = [(user_id, attribute_key, attribute_value) for user_id in user_ids]
        self.db.cursor.executemany(
            "INSERT INTO UserAttributes (user_id, attribute_key, attribute_value) VALUES (?, ?, ?);",
            attributes
        )

    def insert_attribute_name(self, attribute_key):
        query = "INSERT INTO Attributes (attribute_name) VALUES (?);"
        self.db.cursor.execute(query, (attribute_key,))
        self.db.commit()

    def validate_attribute(self, attribute_key: str) -> bool:
        query = "SELECT 1 FROM Attributes WHERE attribute_name = ? LIMIT 1;"
        self.db.cursor.execute(query, (attribute_key,))
        exists = self.db.cursor.fetchone() is not None
        return not exists

    def delete_attribute(self, attribute_key):
        if not self.validate_attribute(attribute_key):
            # Если атрибут существует, удаляем его
            query = "DELETE FROM UserAttributes WHERE attribute_key = ?;"
            self.db.cursor.execute(query, (attribute_key,))
            query = "DELETE FROM Attributes WHERE attribute_name = ?;"
            self.db.cursor.execute(query, (attribute_key,))
            self.db.commit()
        else:
            print(f"Attribute '{attribute_key}' does not exist and cannot be deleted.")

    def rename_attribute(self, attribute_key, new_attribute_key):
        if not self.validate_attribute(attribute_key):
            # Если атрибут существует, переименовываем его
            self.db.cursor.execute("UPDATE UserAttributes SET attribute_key = ? WHERE attribute_key = ?", 
                                    (new_attribute_key, attribute_key))
            self.db.cursor.execute("UPDATE Attributes SET attribute_name = ? WHERE attribute_name = ?", 
                                    (new_attribute_key, attribute_key))
            self.db.commit()
        else:
            print(f"Attribute '{attribute_key}' does not exist and cannot be renamed.")

    def names_all_attributes(self):
        query = "SELECT attribute_name AS unique_attribute_key_count FROM Attributes ORDER BY id ASC;"
        self.db.cursor.execute(query)
        names_attributes = self.db.cursor.fetchall()
        return [item[0] for item in names_attributes]

    @staticmethod
    def count_attributes(db: Database):
        query = "SELECT COUNT(DISTINCT attribute_name) AS unique_attribute_key_count FROM Attributes;"
        db.cursor.execute(query)
        count_attributes = db.cursor.fetchone()[0]  # Получаем результат только один раз
        return count_attributes if count_attributes is not None else 0
   
class TableManager:
    def __init__(self, db: Database):
        self.db = db

    def create_tables(self):
        self._extracted_from_drop_tables_2(
            """
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT
        );""",
            """
        CREATE TABLE IF NOT EXISTS UserAttributes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            attribute_key TEXT NOT NULL,
            attribute_value TEXT,
            FOREIGN KEY (user_id) REFERENCES Users(id)
        );""",
            """
        CREATE TABLE IF NOT EXISTS UserDateBirth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date_of_birth DATE,
            FOREIGN KEY (user_id) REFERENCES Users(id)
        );""",
            """
        CREATE TABLE IF NOT EXISTS Attributes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attribute_name TEXT
        );""",
        )

    def drop_tables(self):
        self._extracted_from_drop_tables_2(
            "DROP TABLE IF EXISTS UserAttributes;",
            "DROP TABLE IF EXISTS Attributes;",
            "DROP TABLE IF EXISTS UserDateBirth;",
            "DROP TABLE IF EXISTS Users;",
        )
        print("Все таблицы успешно сброшены.")

    # TODO Rename this here and in `create_tables` and `drop_tables`
    def _extracted_from_drop_tables_2(self, arg0, arg1, arg2, arg3):
        self.db.cursor.execute(arg0)
        self.db.cursor.execute(arg1)
        self.db.cursor.execute(arg2)
        self.db.cursor.execute(arg3)
        self.db.commit()


if __name__ == "__main__":
    db = Database('your_database.db')
    table_manager = TableManager(db)
    table_manager.create_tables()
    user_manager = UserManager(db)
    user_manager.create_user({})
    attribute_manager = AttributeManager(db)
    attribute_manager.create_attribute("ФИО")
    attribute_manager.create_attribute("Вес")
    attribute_manager.create_attribute("Рост")
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
    
