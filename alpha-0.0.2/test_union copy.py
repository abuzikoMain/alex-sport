import sys
from typing import Any
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget,
    QPushButton, QLineEdit, QDialog, QFormLayout, QLabel, QHeaderView, QMenu,
    QFileDialog, QListWidget, QHBoxLayout
)
from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import (QAction, QStandardItem, QStandardItemModel,
                           QIcon)
from test_model_sql import *
from collections import defaultdict

# Список из 30 имен
names = [
    "Александр", "Мария", "Дмитрий", "Елена", "Сергей",
    "Анна", "Иван", "Ольга", "Максим", "Татьяна",
    "Анастасия", "Николай", "Екатерина", "Павел", "Юлия",
    "Владимир", "Светлана", "Роман", "Дарья", "Артем",
    "Ксения", "Игорь", "Людмила", "Станислав", "Наталья",
    "Григорий", "Виктория", "Алексей", "Евгения", "Константин"
]

class Status:
    __slots__ = ['new', 'changed', 'exist']
    
    """Класс для представления статуса элемента."""
    def __init__(self):
        self.new = False
        self.changed = False
        self.exist = False

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
    def __init__(self, headers):
        super().__init__()
        self._data = {}
        # Данные в формате {row_id: {header_name: value}}
        self._headers = headers
        self.copied_data = None  # Для хранения скопированных данных

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
            self._data.data = (target_row, inputs)

        # Уведомляем об изменении данных
        self.dataChanged.emit(self.index(row, 0), self.index(row + len(self.copied_data) - 1, len(self._headers) - 1))


    def addRow(self):
        new_row_id = len(self._data) # Используем новый ID для строки
        self.beginInsertRows(self.index(len(self._data), 0), len(self._data), len(self._data))
        self._data.data = (new_row_id, {header: "" for header in self._headers})  # Добавляем пустую строку
        # self.change_status_changed(self._data[new_row_id])
        self.endInsertRows()

    def removeRow(self, row):
        if row not in self._data:
            return  # Проверка на допустимость индекса строки

        self.beginRemoveRows(self.index(row, 0), row, row)
        del self._data[row]  # Удаляем данные в строке
        self.endRemoveRows()

        # Уведомляем об изменении данных
        self.layoutChanged.emit()

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
                if row := self._data.data.get(index.row(), False):
                    value = row.get(self._headers[index.column()], "")
                    return str(value)

            elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter

    def setData(self, index, value, role):
        if index.isValid():
            if role == Qt.EditRole:
                self._data[index.row()][self._headers[index.column()]] = value
                return True
            return False
        return False  # Возвращаем False, если роль не соответствует

    
    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        # return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def editData(self, row):
        dialog = EditDialog(self._data[row], self._headers)
        if dialog.exec() == QDialog.Accepted:
            new_values = dialog.getValues()
            self._data.data = (row, new_values)
            self.dataChanged.emit(self.index(row, 0), self.index(row, len(self._headers) - 1))

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

    def __getitem__(self, key: Any) -> Any:
        return self._internal_data[key]

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
            del self._internal_data[key]
            # Удаляем статус элемента
            self._status_manager.remove_status(key)

    def __len__(self) -> int:
        return len(self._internal_data)

    def __repr__(self):
        return f'{self._internal_data}'

class ConditionManager:
    def __init__(self):
        self.groups = []

    def add_group(self, group_name, conditions):
        group_info = f"{group_name}: {conditions}"
        self.groups.append(group_info)

    def edit_group(self, index, group_name, conditions):
        if 0 <= index < len(self.groups):
            self.groups[index] = f"{group_name}: {conditions}"

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

        self.add_column_action = self.create_menu_action("Добавить колонку", self.file_menu_action)
        self.remove_column_action = self.create_menu_action("Удалить колонку", self.file_menu_action)
        self.add_row_action = self.create_menu_action("Добавить строку", self.file_menu_action, shortcut="Ctrl+D")
        self.remove_row_action = self.create_menu_action("Удалить строку", self.file_menu_action, shortcut="Delete")
        self.copy_action = self.create_menu_action("Копировать", self.file_menu_action, shortcut="Ctrl+C")
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

class ConditionGroupDialog(QDialog):
    def __init__(self, headers, condition_manager):
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

        # Список созданных групп
        self.groups_list = QListWidget(self)
        self.layout.addWidget(self.groups_list)
        self.load_groups()

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
            self.groups_list.addItem(group)

    def create_group(self):
        group_name = self.group_name.text()
        conditions = {header: (from_input.text(), to_input.text()) for header, (from_input, to_input) in self.inputs.items()}
        self.condition_manager.add_group(group_name, conditions)
        self.load_groups()
        self.clear_inputs()

    def clear_inputs(self):
        self.group_name.clear()
        for from_input, to_input in self.inputs.values():
            from_input.clear()
            to_input.clear()

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
    def __init__(self, model, window):
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

        self.model = UserTableModel(self.headers)
        self.model._data = self.data

        self.window = MainWindow(self.model)
        self.condition_groups = []
        self.table_controller = TableController(self.model, self.window)
        self.condition_controller = ConditionController()

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


