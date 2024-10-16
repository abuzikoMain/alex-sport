import sys
from typing import Any
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget,
    QPushButton, QLineEdit, QDialog, QFormLayout, QLabel, QHeaderView, QMenu,
    QFileDialog, QListWidget, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import (QAction)
from openpyxl import Workbook
from docx import Document
from test_model_sql import *
from collections import defaultdict

from test_model_sql import *
# Список из 30 имен
names = [
    "Александр", "Мария", "Дмитрий", "Елена", "Сергей",
    "Анна", "Иван", "Ольга", "Максим", "Татьяна",
    "Анастасия", "Николай", "Екатерина", "Павел", "Юлия",
    "Владимир", "Светлана", "Роман", "Дарья", "Артем",
    "Ксения", "Игорь", "Людмила", "Станислав", "Наталья",
    "Григорий", "Виктория", "Алексей", "Евгения", "Константин"
]

class FileSaver:
    """Класс для управления сохранением файлов в разных форматах."""
    
    @staticmethod
    def save_as_xlsx(file_name, content):
        wb = Workbook()
        ws = wb.active
        ws['A1'] = content
        wb.save(file_name)

    @staticmethod
    def save_as_docx(file_name, content):
        doc = Document()
        doc.add_paragraph(content)
        doc.save(file_name)

class TextEditorController:
    """Класс для управления логикой текстового редактора."""
    
    def __init__(self):
        self.content = ""

    def set_content(self, content):
        self.content = content

    def get_content(self):
        return self.content

    def save_file(self, file_name):
        if file_name.endswith('.xlsx'):
            FileSaver.save_as_xlsx(file_name, self.content)
        elif file_name.endswith('.docx'):
            FileSaver.save_as_docx(file_name, self.content)
        else:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(self.content)

class TextEditorUI(QMainWindow):
    """Класс для отображения пользовательского интерфейса текстового редактора."""
    
    def __init__(self, controller):
        super().__init__()

        self.controller = controller

        self.setWindowTitle("Текстовый редактор")
        self.setGeometry(100, 100, 600, 400)

        self.text_edit = QTextEdit(self)
        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.save_file)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.save_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def save_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Text Files (*.txt);;Excel Files (*.xlsx);;Word Files (*.docx)", options=options)
        
        if file_name:
            content = self.text_edit.toPlainText()
            self.controller.set_content(content)  # Устанавливаем контент в контроллер
            self.controller.save_file(file_name)  # Сохраняем файл


class Status:
    __slots__ = ['new', 'changed', 'exist']
    
    """Класс для представления статуса элемента."""
    def __init__(self, new = False, changed = False, exist = False):
        self.new = new
        self.changed = changed
        self.exist = exist

class StatusManager:
    """Менеджер для управления статусами элементов."""
    def __init__(self):
        self._statuses = defaultdict(Status) 

    def get_status(self, key):
        """Получает статус для указанного ключа."""
        return self._statuses[key]  # Теперь не нужно проверять наличие ключа

    def update_status(self, key, new_status):
        """Обновляет статус для указанного ключа."""
        if not isinstance(new_status, Status):
            raise ValueError("new_status должен быть экземпляром класса Status")

        status = self.get_status(key)
        status.new = new_status.new
        status.changed = new_status.changed
        status.exist = new_status.exist

    def update_statuses(self, keys, new_status):
        """Обновляет статусы для списка ключей."""
        for key in keys:
            self.update_status(key, new_status)

    def remove_status(self, key):
        """Удаляет статус для указанного ключа."""
        if key in self._statuses:
            del self._statuses[key]

# Модель данных для QTableView
class UserTableModel(QAbstractTableModel):
    def __init__(self, headers, user_manager: UserManager, attribute_manager: AttributeManager):
        super().__init__()
        self._data: ObservableDict
        self.user_manager = user_manager
        self.attribute_manager = attribute_manager
        # Данные в формате {row_id: {header_name: value}}
        self._headers = headers
        self.copied_data = None  # Для хранения скопированных данных

    def get_new_data(self) -> dict:
        """Возвращает созданные данные."""
        new_data = {}        
        data_cp = self._data.copy()
        for key, val in data_cp.items():
            if self.is_data_new(key):
                new_data[key] = val
        return new_data
    
    def get_data_changed(self) -> dict:
        """Возвращает измененные данные."""
        new_data = {}
        data_cp = self._data.copy()
        for key, val in data_cp.items():
            if self.is_data_changed(key) and not self.is_data_new(key):
                new_data[key] = val
        return new_data

    def is_data_new(self, key) -> bool:
        """Проверяет, изменены ли данные по заданному ключу."""
        status = self._data.status(key)
        return status.new

    def is_data_changed(self, key) -> bool:
        """Проверяет, изменены ли данные по заданному ключу."""
        status = self._data.status(key)
        return status.changed

    def save_action(self) -> tuple:
            """Сохраняет измененные данные и создает атрибуты и пользователей."""
            changed_data = self.get_data_changed()
            del_data = self.get_deletion_data()
            new_data = self.get_new_data()

            error_code = 0  # 0 - успех, 1 - ошибка удаления, 2 - ошибка обновления, 3 - ошибка создания
            
            if del_data or changed_data or new_data:
                self.create_attributes()

            if del_data:
                error_code = self.delete_users(del_data)
                if error_code != 0:
                    return False, error_code

            if changed_data:
                error_code = self.update_users(changed_data)
                if error_code != 0:
                    return False, error_code

            if new_data:
                error_code = self.create_users(new_data)
                if error_code != 0:
                    return False, error_code

            self.create_attributes()  # Создание атрибутов после всех операций
            return True, None  # Успех

    def delete_users(self, del_data) -> int:
        """Удаляет пользователей и возвращает код ошибки."""
        try:
            for data in del_data.values():
                self.user_manager.delete_user(data['user_id'])
            self.clear_delation_data()
            return 0  # Успех
        except Exception as e:
            return 1  # Код ошибки удаления

    def update_users(self, changed_data) -> int:
        """Обновляет пользователей и возвращает код ошибки."""
        try:
            for data in changed_data.values():
                self.user_manager.update_data_user(data)
            self._data.update_statuses(changed_data.keys(), Status(new=False, changed=False, exist=True))
            return 0  # Успех
        except Exception as e:
            return 2  # Код ошибки обновления

    # def create_users(self, new_data) -> int:
        # """Создает пользователей и возвращает код ошибки."""
        # try:
        #     # self.create_attributes()  # Создание атрибутов перед созданием пользователей
        #     self.user_manager.create_users(new_data)
        #     self._data.update_statuses(new_data.keys(), Status(new=False, changed=False, exist=True))
        #     return 0  # Успех
        # except Exception as e:
        #     return 3  # Код ошибки создания

    def create_attributes(self):
        """Создает атрибуты для всех заголовков."""
        for attribute in self._headers:
            self.attribute_manager.create_attribute(attribute)

    def create_users(self, data: dict) -> int:
        """Создает пользователей на основе измененных данных."""
        try:
            status_operations = {}

            for key, val in data.items():
                t_dic = {key: val}
                status_operation = self.user_manager.create_user(t_dic)
                status_operations[key] = status_operation
                if status_operation == True:
                    self._data.update_status(key, Status(False, False, True))
                    
            not_have_false = all(status_operations.values())
            if not_have_false:
                return 0
        except Exception as e:
            return 3

        has_false = not all(status_operations.values())
        return not has_false

    def clear_delation_data(self):
        self._data.clear_delation_data()
        if self._data._delete_data:
            return True
        else:
            return False

    def get_deletion_data(self):
        return self._data.get_deletion_data()
            
    def get_data(self):
        return self._data
    
    def set_data(self, row_id, value):
        if self._data.get(row_id, False):
            self._data[row_id] = value
            self.dataChanged.emit(self.index(row_id, 0), self.index(row_id, len(self._headers) - 1))
        else:
            raise KeyError("Row ID does not exist.")
        
    def del_data(self, row_id):
        if self._data.get(row_id, False):
            del self._data[row_id]

    def get_headers(self):
        return self._headers

    # Метод для копирования данных
    def copyData(self, rows, columns):
        self.copied_data = []
        for row in rows:
            row_data = [self._data[row].get(self._headers[col], "") for col in columns]
            self.copied_data.append(row_data)

    def pasteData(self, row, column):
        if self.copied_data is None:
            return
        # Проверяем, подходит ли вставляемые данные к существующей структуре
        if row < 0 or column < 0:
            return  # Неверные индексы

        for i, row_data in enumerate(self.copied_data):
            target_row = row + i
            if target_row >= len(self._data):
                self.addRow()  # Добавляем новую строку, если необходимо

            # Проверяем, чтобы не выйти за пределы существующих заголовков
            if column + len(row_data) > len(self._headers):
                raise IndexError("Вставляемые данные выходят за пределы существующих заголовков.")

            inputs = dict(zip(self._headers[column:column + len(row_data)], row_data))
            self.set_data(target_row, inputs)

        # Уведомляем об изменении данных
        self.dataChanged.emit(self.index(row, 0), self.index(row + len(self.copied_data) - 1, len(self._headers) - 1))


    def addRow(self):
        new_row_id = len(self._data) # Используем новый ID для строки
        self._data[new_row_id] = {header: "" for header in self._headers}  # Добавляем пустую строку
        self.beginInsertRows(self.index(len(self._data), 0), len(self._data), len(self._data))        
        self.endInsertRows()

    def removeRow(self, row):
        if row not in self._data:
            return  # Проверка на допустимость индекса строки

        self.beginRemoveRows(self.index(row, 0), row, row)
        self.del_data(row_id=row)# Удаляем данные в строке
        self.endRemoveRows()

        # Обновляем row_id только для строк, которые идут после удаленной
        self.reassign_row_ids(row)

        # Уведомляем об изменении данных
        self.layoutChanged.emit()

    def reassign_row_ids(self, ids):
        """Переопределяет row_id для строк, которые идут после удаленной строки."""
        new_data = self.get_data()
        keys = list(new_data.keys())

        for old_row_id in keys:
            if old_row_id > ids:
                new_data[old_row_id - 1] = self._data[old_row_id]
                new_data.pop(old_row_id)
            else:
                new_data[old_row_id] = self._data[old_row_id]
        self._data = new_data


    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            else:
                return section + 1  # Нумерация строк
        return None
    
    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role in [Qt.DisplayRole, Qt.EditRole]:
                if row := self._data.get(index.row(), False):
                    value = row.get(self._headers[index.column()], "")
                    return str(value)

            elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter

    def setData(self, index, value, role):
        if index.isValid() and role == Qt.EditRole:
            temp = self._data[index.row()].copy()
            temp[self._headers[index.column()]] = value
            self._data[index.row()] = temp
            return True
        return False  # Возвращаем False, если роль не соответствует

    
    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        # return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def editData(self, row):
        ...
        # dialog = EditDialog(self._data[row], self._headers)
        # if dialog.exec() == QDialog.Accepted:
        #     new_values = dialog.getValues()
        #     self._data[row] = new_values            
        #     self.dataChanged.emit(self.index(row, 0), self.index(row, len(self._headers) - 1))

    def addColumn(self, header):
        self.beginInsertColumns(self.index(0, len(self._headers)), len(self._headers), len(self._headers))
        self._headers.append(header)
        for row in self._data.values():
            row[header] = ""  # Добавляем пустое значение для новой колонки
        self.endInsertColumns()

    def removeColumn(self, column):
        if column < 0 or column >= len(self._headers):
            return  # Проверка на допустимость индекса колонки
        self.beginRemoveColumns(self.index(0, column), column, column)
        # Удаляем заголовок колонки
        key = self._headers[column]
        del self._headers[column]
        
        # Удаляем данные в каждой строке для этой колонки
        for row in self._data.values():
            del row[key]  # Убедитесь, что вы удаляете правильный ключ

        self.endRemoveColumns()
        self.layoutChanged.emit()  # Уведомляем об изменении данных

        self.attribute_manager.delete_attribute(key)

    def loadDataFromExcel(self, file_path):
        # Считываем данные из Excel, начиная с первой строки и первого столбца
        df = pd.read_excel(file_path, header=0)  # Укажите нужный номер строки для заголовков
        self._headers = df.columns.tolist()
        self._data = df.values.tolist()
        self.layoutChanged.emit()  # Обновляем представление

    def output_data(self):
        return self._data

class ObservableDict(dict):
    """Словарь, который отслеживает изменения и статусы элементов."""
    def __init__(self):
        self._internal_data = {}
        self._delete_data = {}
        self._status_manager = StatusManager()

    @property
    def data(self):
        return self._internal_data if self._internal_data else {}
    
    @data.setter
    def data(self, var: dict | tuple):
        if isinstance(var, dict):
            for row_id, value in var.items():
                self[row_id] = value  # Используем __setitem__ для обновления статусов

        elif isinstance(var, tuple):
            row_id, value = var
            self[row_id] = value  # Используем __setitem__ для обновления статусов
        else:
            raise ValueError            
    def clear_delation_data(self):
        self._delete_data.clear()

    def get_deletion_data(self):
        return self._delete_data

    # Новый метод для загрузки данных из словаря
    def load_from_dict(self, input_dict):
        """Загружает данные из переданного словаря и устанавливает статусы."""
        for key, value in input_dict.items():
            self[key] = value  # Используем __setitem__ для обновления статусов
            status = self._status_manager.get_status(key)
            status.exist = True
            status.new = False
            status.changed = False

    def load_from_db(self, data_from_db):
        """
        Загружает данные из базы данных и устанавливает статусы.
        :param data_from_db: Словарь с данными из базы данных.
        """
        for key, value in data_from_db.items():
            self[key] = value  # Используем __setitem__ для обновления статусов
            # Устанавливаем статусы для существующих данных
            status = self._status_manager.get_status(key)
            status.exist = True
            status.new = False
            status.changed = False

    def update_status(self, key, new_status):
        """Обновляет статус для одного элемента."""
        if not isinstance(new_status, Status):
            raise ValueError("new_status должен быть экземпляром класса Status")

        self._status_manager.update_status(key, new_status)

    def update_statuses(self, keys, new_status):
        """Обновляет статусы для списка ключей."""
        self._status_manager.update_statuses(keys, new_status)

    def status(self, key):
        """Получает статус для указанного ключа."""
        return self._status_manager.get_status(key)

    def pop(self, key, default=None):
        return self._internal_data.pop(key, default)

    def keys(self):
        """D.keys() -> a set-like object providing a view on D's keys"""
        return self._internal_data.keys()

    def copy(self) -> dict:
        return self._internal_data.copy()

    def get(self, key: Any, default:Any=None):
        return self._internal_data.get(key, default)

    def __contains__(self, key):
        # Здесь вы можете определить свою логику
        return key in self._internal_data

    def __getitem__(self, key: Any) -> Any:
        return self._internal_data.__getitem__(key)

    def __setitem__(self, key, value):
        status = self._status_manager.get_status(key)
        if key in self._internal_data:
            if self._internal_data[key] != value:
                status.changed = True
            else:
                status.changed = False
        else:
            status.new = True

        # Устанавливаем exist в True, так как элемент добавляется
        status.exist = True

        self._internal_data[key] = value
        self._status_manager.update_status(key, status)

    def __delitem__(self, key):
        if key in self._internal_data:
            self._delete_data[key] = self._internal_data[key]
            del self._internal_data[key]
            # Удаляем статус элемента
            self._status_manager.remove_status(key)

    def __len__(self) -> int:
        return len(self._internal_data)

    def __repr__(self):
        return f'{self._internal_data}'

class GroupValidator:
    def __init__(self, groups):
        self.groups = groups


    def validate_group_name(self, group_name: str):
        if not group_name:
            raise ValueError("Имя группы не может быть пустым.")
        if any(group_name == list(group.keys())[0] for group in self.groups):
            raise ValueError(f"Группа с именем '{group_name}' уже существует.")

    def validate_conditions(self, conditions: dict):
        if not conditions:
            raise ValueError("Условия не могут быть пустыми.")
        for value in conditions.values():
            if any(attrValue in (None, '',) for attrValue in value.values()):
                raise ValueError("Условия не могут быть пустыми.")
                      
    def validate_group_index(self, index: int):
        if not (0 <= index < len(self.groups)):
            raise IndexError(f"Индекс {index} вне диапазона групп.")

    def validate_conditions_overlap(self, new_conditions: dict):
        for attribute, new_values in new_conditions.items():
            self._check_overlap(attribute, new_values)

    def _check_overlap(self, attribute: str, new_values: dict):
        for group in self.groups:
            for existing_group in group.values():
                if attribute in existing_group:
                    existing_values = existing_group[attribute]
                    if self._is_overlapping(new_values, existing_values):
                        raise ValueError(f"Пересечение значений атрибута '{attribute}' с существующей группой.")

    def _is_overlapping(self, new_values: dict, existing_values: dict) -> bool:
        return new_values['min'] <= existing_values['max'] and new_values['max'] >= existing_values['min']
        
        # for group in self.groups:
        #     for attribute, values in new_conditions.items():
        #         for _, values_existing in group.items():
        #             for attribute_old, exist_values in values_existing.items():
        #                 if attribute == attribute_old:
        #                     existing_values = exist_values
        #                     if (values['min'] <= existing_values['max'] and values['max'] >= existing_values['min']):
        #                         raise ValueError(f"Пересечение значений атрибута '{attribute}' с существующей группой.")                


class ConditionManager:
    def __init__(self):
        self.groups = []
        self.validator = GroupValidator(self.groups)  # Инициализация валидатора        

    def add_group(self, group_name: str, conditions: dict[str: dict[str: str, str: str]]):
            # Проверка на наличие дубликатов с помощью валидатора
            self.validator.validate_group_name(group_name)
            self.validator.validate_conditions(conditions)
            self.validator.validate_conditions_overlap(conditions)

            group_info = Group()
            group_info[group_name] = conditions
            # Добавление новой группы
            self.groups.append(group_info)

    def edit_group(self, index: int, group_name: str, conditions: dict[str: dict[str: str, str: str]]):
        # Conditions: {'Test': {'min': '1', 'max': '1'}}
        self.validator.validate_group_index(index)
        self.validator.validate_conditions(conditions)
        self.validator.validate_conditions_overlap(conditions)
        self.groups[index] = Group({group_name: conditions})

    def delete_group(self, index: int):
        # Удаляем группу по индексу
        self.validator.validate_group_index(index)
        # deleted_group = self.groups[index]
        del self.groups[index]     

    def get_groups(self):
        return self.groups

# Основное окно приложения
class MainWindow(QMainWindow):
    def __init__(self, model):
        super().__init__()

        self.setWindowTitle("Пример QTableView с добавлением колонки")
        self.setGeometry(100, 100, 400, 300)

        self.condition_groups = []
        self.table_view = QTableView()
        self.table_view.setModel(model)
        self.table_view.setSizeAdjustPolicy(QTableView.AdjustToContents)
        
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.setCentralWidget(self.create_central_widget())
        self.create_menus()

    def create_central_widget(self):
        layout = QVBoxLayout()
        layout.addWidget(self.table_view, stretch=1)
        container = QWidget()
        container.setLayout(layout)
        return container

    def create_menus(self):
        self.menu_bar_file = self.menuBar()
        self.file_menu_file = QMenu("Файл", self)
        self.menu_bar_file.addMenu(self.file_menu_file)

        self.file_menu_action = QMenu("Действия", self)
        self.menu_bar_file.addMenu(self.file_menu_action)

        self.group_data = self.create_menu_action("Сгруппировать", self.file_menu_action)
        self.add_column_action = self.create_menu_action("Добавить колонку", self.file_menu_action)
        self.remove_column_action = self.create_menu_action("Удалить колонку", self.file_menu_action)
        self.add_row_action = self.create_menu_action("Добавить строку", self.file_menu_action, shortcut="Ctrl+D")
        self.remove_row_action = self.create_menu_action("Удалить строку", self.file_menu_action, shortcut="Delete")
        self.copy_action = self.create_menu_action("Копировать", self.file_menu_action, shortcut="Ctrl+C")
        self.save_action = self.create_menu_action("Сохранить", self.file_menu_file, shortcut="Ctrl+S")
        self.paste_action = self.create_menu_action("Вставить", self.file_menu_action, shortcut="Ctrl+V")
        self.load_excel_action = self.create_menu_action("Загрузить из Excel", self.file_menu_file)
        self.conditions_action = self.create_menu_action("Условия", self.file_menu_file)
        self.exit_action = self.create_menu_action("Выход", self.file_menu_file)

    def create_menu_action(self, name, parent_menu, shortcut=None):
        action = QAction(name, self)
        if shortcut:
            action.setShortcut(shortcut)
        parent_menu.addAction(action)
        return action

class Group(dict):    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_keys(self):
        """Возвращает список всех ключей в словаре."""
        return list(self.keys())

    def get_values(self):
        """Возвращает список всех значений в словаре."""
        return list(self.values())

    def __repr__(self) -> str:
        return f"{super().__repr__()}"

    def __str__(self):
        """Переопределяем метод str для удобного отображения."""
        if len(self) > 0 and len(self) < 2:
            key = next(reversed(self.keys()))        
            return f"Группа {key}"
        return f"{super().__str__()}"
  

class ConditionGroupDialog(QDialog):
    def __init__(self, headers: list[str, str, Any], condition_manager: ConditionManager):
        super().__init__()
        self.setWindowTitle("Создать группу условий")
        self.setFixedSize(300, 300)

        self.layout = QVBoxLayout(self)
        self.inputs = {}
        self.condition_manager = condition_manager

        # Создаем поля ввода на основе заголовков
        self._create_input_fields(headers)

        # Поле для ввода имени группы
        self.layout.addWidget(QLabel("Имя группы:"))
        self.group_name = QLineEdit(self)
        self.layout.addWidget(self.group_name)

        # Кнопка создания группы
        self.create_button = QPushButton("Создать группу", self)
        self.create_button.clicked.connect(self.create_group)
        self.layout.addWidget(self.create_button)
        
        self.delete_button = QPushButton("Удалить групп", self)
        self.delete_button.clicked.connect(lambda: self.delete_group())
        self.layout.addWidget(self.delete_button)
        self.delete_button.hide()

        # Список созданных групп
        self.groups_list = QListWidget(self)
        self.layout.addWidget(self.groups_list)
        self.load_groups()
        self.groups_list.doubleClicked.connect(lambda: self.editGroup(self.condition_manager.get_groups()))
        self.groups_list.itemClicked.connect(self.show_delete_button)


    def delete_group(self):
        selected_item = self.groups_list.currentItem()
        if selected_item:
            index = self.groups_list.row(selected_item)
            group_name = selected_item.text()  # Получаем имя группы для удаления
            self.condition_manager.delete_group(index)  # Удаляем группу из менеджера условий
            self.load_groups()  # Обновляем список групп
            self.clear_inputs()  # Очищаем поля ввода

    def _create_input_fields(self, headers):
        for header in headers:
            if headers.index(header) == 0:
                continue
            h_layout = QHBoxLayout()
            from_input = QLineEdit(self)
            to_input = QLineEdit(self)
            self.inputs[header] = (from_input, to_input)
            h_layout.addWidget(QLabel(f"{header}: от"))
            h_layout.addWidget(from_input)
            h_layout.addWidget(QLabel("до"))
            h_layout.addWidget(to_input)
            self.layout.addLayout(h_layout)

    def load_groups(self):
        self.groups_list.clear()
        for group in self.condition_manager.get_groups():
            self.groups_list.addItem(str(group))

    def create_group(self):
        group_name = self.group_name.text()
        conditions = {header: {'min':from_input.text(), 'max':to_input.text()} for header, (from_input, to_input) in self.inputs.items()}
        self.condition_manager.add_group(group_name, conditions)
        self.load_groups()
        self.clear_inputs()

    def clear_inputs(self):
        self.group_name.clear()
        for from_input, to_input in self.inputs.values():
            from_input.clear()
            to_input.clear()

    def show_delete_button(self):
        if self.groups_list.currentItem() is not None:
            self.delete_button.show()
        else:
            self.delete_button.hide()
        

    def editGroup(self, groups):
        selected_item = self.groups_list.currentItem()
        if selected_item:
            index = self.groups_list.row(selected_item)
            group = groups[index]
            self.group_name.setText(list(group.keys())[0])  # Установка имени группы
            conditions = group[list(group.keys())[0]]

            # Установка значений в поля ввода
            for header, (from_input, to_input) in self.inputs.items():
                if header in conditions:
                    from_input.setText(conditions[header]['min'])
                    to_input.setText(conditions[header]['max'])

            # Изменение кнопки создания группы на кнопку редактирования
            self.create_button.setText("Редактировать группу")
            self.create_button.clicked.disconnect()  # Отключаем старый обработчик
            self.create_button.clicked.connect(lambda: self.update_group(index))

    def update_group(self, index):
        group_name = self.group_name.text()
        conditions = {header: {'min': from_input.text(), 'max': to_input.text()} for header, (from_input, to_input) in self.inputs.items()}
        self.condition_manager.edit_group(index, group_name, conditions)
        self.load_groups()
        self.clear_inputs()
        self.create_button.setText("Создать группу")  # Возвращаем текст кнопки
        self.create_button.clicked.disconnect()  # Отключаем старый обработчик
        self.create_button.clicked.connect(self.create_group)  # Подключаем обратно
        

class EditDialog(QDialog):
    def __init__(self, data: dict, headers: list):
        super().__init__()
        
        # Установка заголовка и фиксированного размера окна
        self.setWindowTitle("Редактирование данных")
        self.setFixedSize(300, 200)

        # Инициализация компоновки и словаря для ввода
        self.layout = QFormLayout(self)
        self.inputs = {}

        # Копирование заголовков и данных
        self._headers = headers.copy()
        self._data = data.copy()

        # Заполнение полей ввода на основе переданных данных
        self._initialize_inputs(data)

        # Добавление кнопки сохранения
        self._add_save_button()

    def _initialize_inputs(self, data: dict):
        """Инициализация полей ввода на основе данных."""
        for header, value in data.items():
            if header == 'changed':
                continue
            if header:
                self._add_input_field(header, value)

        # Добавление оставшихся заголовков, которые не были в данных
        self._add_remaining_headers()

    def _add_input_field(self, header: str, value: str):
        """Добавление поля ввода для заданного заголовка и значения."""
        line_edit = QLineEdit(self)
        line_edit.setText(str(value))
        self.inputs[header] = line_edit
        self.layout.addRow(QLabel(header), line_edit)

        # Удаление заголовка из списка, если он уже был добавлен
        if header in self._headers:
            self._headers.remove(header)

    def _add_remaining_headers(self):
        """Добавление оставшихся заголовков в качестве полей ввода."""
        for header in self._headers:
            line_edit = QLineEdit(self)
            self.inputs[header] = line_edit
            self.layout.addRow(QLabel(header), line_edit)

    def _add_save_button(self):
        """Добавление кнопки сохранения."""
        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.accept)
        self.layout.addRow(self.save_button)

    def getValues(self):
        """Получение значений из полей ввода."""
        return {key: value.text() for key, value in self.inputs.items()}

# Диалог для ввода имени колонки
class AddColumnDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавить колонку")
        self.setFixedSize(300, 100)

        self.layout = QFormLayout(self)
        self.column_name_input = QLineEdit(self)
        self.layout.addRow(QLabel("Имя колонки:"), self.column_name_input)

        self.add_button = QPushButton("Добавить", self)
        self.add_button.clicked.connect(self.accept)
        self.layout.addRow(self.add_button)

    def getColumnName(self):
        return self.column_name_input.text()

class TableController:
    def __init__(self, model: UserTableModel, window: MainWindow, condition_controller: UserTableModel):
        self.condition_controller = condition_controller
        self.model = model
        self.window = window

        # Подключаем действия интерфейса к методам контроллера
        self.window.add_column_action.triggered.connect(self.add_column)
        self.window.add_row_action.triggered.connect(self.add_row)
        # self.window.add_row_button.triggered.connect(self.add_row)
        self.window.copy_action.triggered.connect(self.copy_data)
        self.window.paste_action.triggered.connect(self.paste_data)
        self.window.remove_column_action.triggered.connect(self.remove_column)
        self.window.remove_row_action.triggered.connect(self.remove_row)
        self.window.table_view.doubleClicked.connect(self.on_cell_double_clicked)
        self.window.group_data.triggered.connect(self.group_data)
        self.window.save_action.triggered.connect(self.save_action)

    def group_data(self) -> dict[str, dict[str, Any]]:
        """
        Метод для группировки данных на основе фильтров из контроллера условий.

        Возвращает словарь, где ключами являются идентификаторы пользователей, 
        а значениями - словари атрибутов пользователей.
        """
        groups = self.get_groups_from_controller()  # Получаем группы из контроллера условий
        filtered_data = self.filter_data(groups)  # Фильтруем данные на основе групп
        a = self.process_filtered_data(filtered_data)
        print(a)
        return a  # Обрабатываем и возвращаем результат

    def get_groups_from_controller(self) -> list[dict[str, dict[str, tuple]]]:
        """Получает группы из контроллера условий."""
        return self.condition_controller.get_groups()  # [{'asd': {'Test': ('1', '4')}}]

    def filter_data(self, groups: list[dict[str, dict[str, tuple]]]) -> dict[str, Any]:
        """Фильтрует данные на основе переданных групп."""
        filtered_data: dict[str, Any] = {}

        for group in groups:
            for filter_key, filter_value in group.items():
                if filter_value is not None:
                    user_data = self.get_user_data(filter_value)
                    if user_data:
                        filtered_data[filter_key] = user_data

        return filtered_data

    def get_user_data(self, filter_value: dict[str, tuple]) -> Any:
        """Получает данные пользователя на основе фильтра."""
        result = self.model.user_manager.select_on_filter(filter_value)
        return result[0] if result else None

    def process_filtered_data(self, filtered_data: dict[str, Any]) -> dict[str, Any]:
        """Обрабатывает отфильтрованные данные."""
        for each in filtered_data:
            filtered_data[each] = self.construct_result(filtered_data[each])
        return filtered_data

    def construct_result(self, filtered_data: list[tuple[str, str, Any]]) -> dict[str, dict[str, Any]]:
        """
        Метод для построения словаря результатов на основе отфильтрованных данных.

        Аргументы:
        filtered_data -- список кортежей, содержащих идентификаторы, имена атрибутов и значения.

        Возвращает словарь, где ключами являются идентификаторы пользователей, 
        а значениями - словари атрибутов пользователей.
        """
        result = {}  # Словарь для хранения результатов
        # Проходим по отфильтрованным данным
        for id_, attribute_name, value in filtered_data:
            if id_ not in result:  # Если идентификатор еще не добавлен в результат
                result[id_] = {}  # Инициализируем новый словарь для атрибутов
            # Добавляем атрибут и его значение в словарь
            result[id_][attribute_name] = value
        return result  # Возвращаем итоговый словарь
       
    def save_action(self):
        status, error_code = self.model.save_action()
        if status == True:
            self.show_message("Успех", "Данные успешно сохранены.")
        elif status == False:
            self.show_message("Ошибка", f"Не удалось сохранить данные.\n Error code {error_code}")

    def show_message(self, title: str, message: str):
        """Отображает сообщение в диалоговом окне."""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    def add_column(self):
        dialog = AddColumnDialog()
        if dialog.exec() == QDialog.Accepted:
            if column_name := dialog.getColumnName():
                self.model.addColumn(column_name)

    def add_row(self):
        self.model.addRow()

    def copy_data(self):
        if selected_indexes := self.window.table_view.selectedIndexes():
            rows = set(index.row() for index in selected_indexes)
            columns = set(index.column() for index in selected_indexes)
            self.model.copyData(rows, columns)

    def paste_data(self):
        selected_index = self.window.table_view.currentIndex()
        if selected_index.isValid():
            self.model.pasteData(selected_index.row(), selected_index.column())
        self.window.table_view.clearSelection()

    def remove_column(self):
        selected_indexes = self.window.table_view.selectedIndexes()
        if not selected_indexes:
            return

        columns_to_remove = sorted(set(index.column() for index in selected_indexes), reverse=True)
        for column in columns_to_remove:
            self.model.removeColumn(column)


    def remove_row(self):
        selected_indexes = self.window.table_view.selectedIndexes()
        if not selected_indexes:
            return

        rows_to_remove = sorted(set(index.row() for index in selected_indexes), reverse=True)
        for row in rows_to_remove:
            self.model.removeRow(row)

    def on_cell_double_clicked(self, index):
        if index.isValid():
            self.model.editData(index.row())

class ConditionController:
    def __init__(self):
        self.condition_manager = ConditionManager()

    def get_groups(self):
        return self.condition_manager.get_groups()

    def open_conditions_dialog(self, headers):
        dialog = ConditionGroupDialog(headers, self.condition_manager)
        dialog.exec()

class AppController:
    def __init__(self, db):
        self.table_manager = TableManager(db)
        self.table_manager.create_tables()
        self.user_manager = UserManager(db)
        self.attribute_manager = AttributeManager(db)

        self.data = ObservableDict()
        data = self.user_manager.select_all()
        self.data.load_from_db(data)

        self.headers = self.attribute_manager.names_all_attributes()

        self.model = UserTableModel(self.headers, self.user_manager, self.attribute_manager)
        self.model._data = self.data

        self.window = MainWindow(self.model)
        self.condition_groups = []
        self.table_controller = TableController(self.model, self.window)
        self.condition_controller = ConditionController()

        self.table_controller = TableController(self.model, self.window, self.condition_controller)

        self.window.load_excel_action.triggered.connect(self.load_data_from_excel)
        self.window.conditions_action.triggered.connect(lambda: self.condition_controller.open_conditions_dialog(self.model.get_headers()))


    def load_data_from_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self.window, "Открыть файл Excel", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.model.loadDataFromExcel(file_path)

    def run(self):
        self.window.show()

def insert_data(user_manager: UserManager, attribute_manager: AttributeManager):    
    count = 9

    name = "Имя"
    weight = "Вес"
    height = "Рост"

    for _ in range(count):
        user_manager.create_user({})

    attribute_manager.create_attribute("Имя")
    attribute_manager.create_attribute("Вес")
    attribute_manager.create_attribute("Рост")            

    for user_id in range(1, count + 1):
        random_name = random.choice(names)
        random_weight = random.randint(50, 95)
        random_height = random.randint(150, 190)

        user_manager.change_attribute_value(user_id, random_name, name)
        user_manager.change_attribute_value(user_id, random_weight, weight)
        user_manager.change_attribute_value(user_id, random_height, height)

def main():
    db = Database('your_database.db')
    app = QApplication(sys.argv)  # Создаем экземпляр QApplication     

    # Получаем список доступных экранов
    screens = app.screens()

    if len(screens) > 1: 

        # Получаем второй экран
        second_screen = screens[0]
        # Получаем геометрию второго экрана
        screen_geometry = second_screen.geometry()
        # Создаем главное окно
        controller = Controller(db)      # Создаем экземпляр контроллера
         
        # Устанавливаем позицию окна на втором мониторе
        controller.window.setGeometry(screen_geometry)
        controller.window.move(screen_geometry.x(), screen_geometry.y())

    else:
        print("Второй монитор не обнаружен.")
        return
    
    controller.run() 
    sys.exit(app.exec())

def new_main():
    db = Database('your_database.db')

    app = QApplication(sys.argv)  # Создаем экземпляр QApplication     

    # Получаем список доступных экранов
    screens = app.screens()
    first_screen = screens[0]
    screen_geometry = first_screen.geometry()
    appController = AppController(db)
    appController.table_manager.create_tables()

    appController.window.setGeometry(screen_geometry)
    appController.window.move(screen_geometry.x(), screen_geometry.y())      

    # if len(screens) > 1: 

    #     # Получаем второй экран
    #     second_screen = screens[0]
    #     # Получаем геометрию второго экрана
    #     screen_geometry = second_screen.geometry()
    #     # Создаем главное окно
    #     appController = AppController(db)     # Создаем экземпляр контроллера
         
    #     # Устанавливаем позицию окна на втором мониторе
    #     appController.window.setGeometry(screen_geometry)
    #     appController.window.move(screen_geometry.x(), screen_geometry.y())

    # else:
    #     print("Второй монитор не обнаружен.")
    #     return
    
    appController.run() 
    sys.exit(app.exec())


# Запуск приложения
if __name__ == "__main__":
    new_main()


