import sys
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

# Список из 30 имен
names = [
    "Александр", "Мария", "Дмитрий", "Елена", "Сергей",
    "Анна", "Иван", "Ольга", "Максим", "Татьяна",
    "Анастасия", "Николай", "Екатерина", "Павел", "Юлия",
    "Владимир", "Светлана", "Роман", "Дарья", "Артем",
    "Ксения", "Игорь", "Людмила", "Станислав", "Наталья",
    "Григорий", "Виктория", "Алексей", "Евгения", "Константин"
]


class ConditionGroupDialog(QDialog):
    def __init__(self, headers, groups):
        super().__init__()
        self.setWindowTitle("Создать группу условий")
        self.setFixedSize(300, 300)

        self.layout = QVBoxLayout(self)

        self.inputs = {}
        
        # Создаем поля ввода на основе заголовков
        for header in headers:
            if headers.index(header) == 0:
                continue
            h_layout = QHBoxLayout()  # Горизонтальный макет для полей "от" и "до"
            from_input = QLineEdit(self)
            to_input = QLineEdit(self)
            self.inputs[header] = (from_input, to_input)
            h_layout.addWidget(QLabel(f"{header}: от"))
            h_layout.addWidget(from_input)
            h_layout.addWidget(QLabel("до"))
            h_layout.addWidget(to_input)
            self.layout.addLayout(h_layout)  # Добавляем горизонтальный макет в основной

        # Поле для ввода имени группы
        self.layout.addWidget(QLabel("Имя группы:"))
        self.group_name = QLineEdit(self)
        self.layout.addWidget(self.group_name)

        # Кнопка создания группы
        self.create_button = QPushButton("Создать группу", self)
        self.create_button.clicked.connect(lambda: self.createGroup(groups))
        self.layout.addWidget(self.create_button)

        # Список созданных групп
        self.groups_list = QListWidget(self)
        self.layout.addWidget(self.groups_list)
        self.groups_list.doubleClicked.connect(lambda: self.editGroup(groups))

        # Отображаем существующие группы
        self.loadGroups(groups)

    def loadGroups(self, groups):
        self.groups_list.clear()
        for group in groups:
            self.groups_list.addItem(group)

    def createGroup(self, groups):
        group_name = self.group_name.text()
        if group_name:
            conditions = {header: (from_input.text(), to_input.text()) for header, (from_input, to_input) in self.inputs.items()}
            group_info = f"{group_name}: {conditions}"
            self.groups_list.addItem(group_info)
            groups.append(group_info)  # Сохраняем группу в памяти
            self.group_name.clear()
            for from_input, to_input in self.inputs.values():
                from_input.clear()
                to_input.clear()

    def editGroup(self, groups):
        selected_item = self.groups_list.currentItem()
        if selected_item:
            selected_index = self.groups_list.currentRow()
            group_info = groups[selected_index]
            group_name, conditions = group_info.split(": ", 1)
            self.group_name.setText(group_name)

            # Извлекаем условия и заполняем поля ввода
            conditions_dict = eval(conditions)  # Преобразуем строку обратно в словарь
            for header, (from_value, to_value) in conditions_dict.items():
                from_input, to_input = self.inputs[header]
                from_input.setText(from_value)
                to_input.setText(to_value)

            # Обновляем кнопку создания на редактирование
            self.create_button.setText("Сохранить изменения")
            self.create_button.clicked.disconnect()  # Отключаем старый обработчик
            self.create_button.clicked.connect(lambda: self.saveChanges(groups, selected_index))

    def saveChanges(self, groups, index):
        group_name = self.group_name.text()
        if group_name:
            conditions = {header: (from_input.text(), to_input.text()) for header, (from_input, to_input) in self.inputs.items()}
            group_info = f"{group_name}: {conditions}"
            groups[index] = group_info  # Обновляем группу в памяти
            self.loadGroups(groups)  # Обновляем список
            self.group_name.clear()
            for from_input, to_input in self.inputs.values():
                from_input.clear()
                to_input.clear()

            self.create_button.setText("Создать группу")  # Возвращаем текст кнопки
            self.create_button.clicked.disconnect()  # Отключаем старый обработчик
            self.create_button.clicked.connect(lambda: self.createGroup(groups))  # Подключаем обратно

class EditDialog(QDialog):
    def __init__(self, data: dict, headers: list):
        super().__init__()
        self.setWindowTitle("Редактирование данных")
        self.setFixedSize(300, 200)

        self.layout = QFormLayout(self)
        self.inputs = {}
        
        self._headers = headers.copy()
        # for header, value in zip(headers, data):
        #     line_edit = QLineEdit(self)
        #     line_edit.setText(str(value))
        #     self.inputs.append(line_edit)
        #     self.layout.addRow(QLabel(header), line_edit)
        if data:
            for header, value in data.items():
                if header:
                    line_edit = QLineEdit(self)
                    line_edit.setText(str(value))
                    self.inputs[header] = line_edit
                    self.layout.addRow(QLabel(header), line_edit)
                    if header in self._headers:
                        index = self._headers.index(header)
                        self._headers.pop(index)

        if self._headers:
            for header in self._headers:
                line_edit = QLineEdit(self)
                self.inputs[header] = line_edit
                self.layout.addRow(QLabel(header), line_edit)


        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.accept)
        self.layout.addRow(self.save_button)

    def getValues(self):
        return {key:value.text() for key, value in self.inputs.items()}

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

# Модель данных для QTableView
# Модель данных для QTableView
class UserTableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data  # Данные в формате {row_id: {header_name: value}}
        self._headers = headers
        self.copied_data = None  # Для хранения скопированных данных

    # Метод для копирования данных
    def copyData(self, rows, columns):
        self.copied_data = []
        for row in rows:
            row_data = [self._data[row].get(self._headers[col], "") for col in columns]
            self.copied_data.append(row_data)

    def pasteData(self, row, column):
        if self.copied_data is not None:
            for i, row_data in enumerate(self.copied_data):
                # Если текущая строка + i превышает количество строк в данных, добавляем новую строку
                if row + i + 1 not in self._data:
                    self.addRow()  # Используем метод addRow для добавления новой строки

                # Вставляем данные в соответствующие ячейки
                for j, value in enumerate(row_data):
                    if column + j < len(self._headers):
                        self._data[row + i + 1][self._headers[column + j]] = value

            # Уведомляем об изменении данных
            self.dataChanged.emit(self.index(row, 0), self.index(row + len(self.copied_data) - 1, len(self._headers) - 1))

    def addRow(self):
        new_row_id = len(self._data)  # Используем новый ID для строки
        self.beginInsertRows(self.index(len(self._data), 0), len(self._data), len(self._data))
        self._data[new_row_id] = {header: "" for header in self._headers}  # Добавляем пустую строку
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
            if role == Qt.DisplayRole or role == Qt.EditRole:
                row = self._data.get(index.row() + 1, False)
                if row:
                    value = row.get(self._headers[index.column()], "") 
                    return str(value)
                
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            self._data[index.row() + 1][self._headers[index.column()]] = value
            return True
        return False
    
    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def editData(self, row):
        row = row + 1
        dialog = EditDialog(self._data[row], self._headers)
        if dialog.exec() == QDialog.Accepted:
            new_values = dialog.getValues()
            self._data[row] = new_values
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

    def loadDataFromExcel(self, file_path):
        # Считываем данные из Excel, начиная с первой строки и первого столбца
        df = pd.read_excel(file_path, header=0)  # Укажите нужный номер строки для заголовков
        self._headers = df.columns.tolist()
        self._data = df.values.tolist()
        self.layoutChanged.emit()  # Обновляем представление

# Основное окно приложения
class MainWindow(QMainWindow):
    def __init__(self, model):
        super().__init__()

        self.setWindowTitle("Пример QTableView с добавлением колонки")
        self.setGeometry(100, 100, 400, 300)
        
        # Список для хранения групп условий
        self.condition_groups = []

        # Данные для таблицы
        self.data = [
            ["Алексей", 25, "Москва"],
            ["Мария", 30, "Санкт-Петербург"],
            ["Иван", 22, "Екатеринбург"],
            ["Ольга", 28, "Казань"]
        ]

        # Создаем меню
        self.menu_bar = self.menuBar()
        self.file_menu = QMenu("Файл", self)
        self.menu_bar.addMenu(self.file_menu)

        # Добавляем действия в меню
        self.add_column_action = QAction("Добавить колонку", self)
        self.file_menu.addAction(self.add_column_action)

        self.remove_column_action = QAction("Удалить колонку", self)
        self.file_menu.addAction(self.remove_column_action)

        # В конструкторе MainWindow
        self.add_row_action = QAction("Добавить строку", self)
        self.add_row_action.setShortcut("Ctrl+D") 
        self.file_menu.addAction(self.add_row_action)

        self.remove_row_action = QAction("Удалить строку", self)
        self.remove_row_action.setShortcut("Delete") 
        self.file_menu.addAction(self.remove_row_action)

        self.copy_action = QAction("Копировать", self)
        self.copy_action.setShortcut("Ctrl+C") 
        self.file_menu.addAction(self.copy_action)

        self.paste_action = QAction("Вставить", self)
        self.paste_action.setShortcut("Ctrl+V") 
        self.file_menu.addAction(self.paste_action)

        # # Также добавьте кнопку на интерфейс
        self.add_row_button = QAction("Добавить строку", self)
        self.menu_bar.addAction(self.add_row_button)  # Добавьте кнопку в layout

        self.load_excel_action = QAction("Загрузить из Excel", self)
        # self.load_excel_action.triggered.connect(self.loadDataFromExcel)
        self.file_menu.addAction(self.load_excel_action)

        self.conditions_action = QAction("Условия", self)
        self.file_menu.addAction(self.conditions_action)

        self.exit_action = QAction("Выход", self)
        self.file_menu.addAction(self.exit_action)

        # Создаем модель и таблицу
        self.table_view = QTableView()
        self.table_view.setModel(model)
        self.table_view.setSizeAdjustPolicy(QTableView.AdjustToContents)
        # Растягиваем колонки
        self.table_view.horizontalHeader().setStretchLastSection(True)  # Растягиваем последнюю колонку
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Растягиваем все колонки
     
        # Устанавливаем макет
        layout = QVBoxLayout()
        layout.addWidget(self.table_view, stretch=1)  # Изменено: добавлен stretch

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

class Controller:
    def __init__(self, db):
        
        self.table_manager = TableManager(db)
        self.table_manager.create_tables()
        self.user_manager = UserManager(db)

        self.attribute_manager = AttributeManager(db)

        # insert_data(self.user_manager, self.attribute_manager)
    
        # self.data = [
        #     ["Алексей", 25, "Москва"],
        #     ["Мария", 30, "Санкт-Петербург"],
        #     ["Иван", 22, "Екатеринбург"],
        #     ["Ольга", 28, "Казань"]
        # ]

        self.data = self.user_manager.select_all()
        self.headers = self.attribute_manager.names_all_attributes()
        self.condition_groups = []
        
        # Инициализация модели с данными
        self.model = UserTableModel(self.data, self.headers)
        self.window = MainWindow(self.model)
        # self.window.model = self.model  # Передаем модель в окно
        self.dialog = AddColumnDialog()

        # Подключаем действия интерфейса к методам контроллера
        self.window.add_column_action.triggered.connect(self.add_column)
        self.window.add_row_action.triggered.connect(self.add_row)
        self.window.copy_action.triggered.connect(self.copy_data)
        self.window.paste_action.triggered.connect(self.paste_data)
        self.window.conditions_action.triggered.connect(self.open_conditions_dialog)
        self.window.load_excel_action.triggered.connect(self.load_data_from_excel)
        self.window.table_view.doubleClicked.connect(self.onCellDoubleClicked)
        self.window.remove_column_action.triggered.connect(self.removeColumn)
        self.window.remove_row_action.triggered.connect(self.removeRow)

    def select_all_from_table(self):
        test = self.user_manager.select_all()
        headers = self.attribute_manager.names_all_attributes()
        a = 0

    def add_column(self):
        if self.dialog.exec() == QDialog.Accepted:
            column_name = self.dialog.getColumnName()
            if column_name:
                self.model.addColumn(column_name)
                # self.window.updateTableView()

    def removeColumn(self):
        # Получаем индексы выделенных колонок
        selected_indexes = self.table_view.selectedIndexes()
        if not selected_indexes:
            return  # Если ничего не выделено, выходим

        # Получаем уникальные индексы колонок
        columns_to_remove = sorted(set(index.column() for index in selected_indexes), reverse=True)

        # Удаляем колонки из модели, начиная с конца, чтобы не нарушить индексы
        for column in columns_to_remove:
            self.model.removeColumn(column)


    def onCellDoubleClicked(self, index):
        if index.isValid():
            self.model.editData(index.row())   

    def add_row(self):
        self.model.addRow()

    def copy_data(self):
        selected_indexes = self.window.table_view.selectedIndexes()
        if selected_indexes:
            rows = set(index.row() + 1 for index in selected_indexes)
            columns = set(index.column() for index in selected_indexes)
            self.model.copyData(rows, columns)

    def paste_data(self):
        selected_index = self.window.table_view.currentIndex()
        if selected_index.isValid():
            self.model.pasteData(selected_index.row(), selected_index.column())

    def open_conditions_dialog(self):
        headers = self.model._headers  # Получаем заголовки из модели
        dialog = ConditionGroupDialog(headers, self.condition_groups)
        dialog.exec()

    def load_data_from_excel(self):
        # Открываем диалог для выбора файла
        file_path, _ = QFileDialog.getOpenFileName(self.window, "Открыть файл Excel", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.model.loadDataFromExcel(file_path)

    def removeRow(self):
        # Получаем индексы выделенных строк
        selected_indexes = self.window.table_view.selectedIndexes()
        if not selected_indexes:
            return  # Если ничего не выделено, выходим

        # Получаем уникальные индексы строк
        rows_to_remove = sorted(set(index.row() for index in selected_indexes), reverse=True)

        # Удаляем строки из модели, начиная с конца, чтобы не нарушить индексы
        for row in rows_to_remove:
            self.model.removeRow(row)


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
    app = QApplication(sys.argv)

    # db = Database('your_database.db')
    # table_manager = TableManager(db)
    # table_manager.create_tables()
    # user_manager = UserManager(db)
    # user_manager.create_user({})
    # attribute_manager = AttributeManager(db)

    # Получаем список доступных экранов
    screens = app.screens()

    if len(screens) > 1:

        # Получаем второй экран
        second_screen = screens[1]
        # Получаем геометрию второго экрана
        screen_geometry = second_screen.geometry()
        # Создаем главное окно
        window = MainWindow()
        # Устанавливаем позицию окна на втором мониторе
        window.setGeometry(screen_geometry)
        window.move(screen_geometry.x(), screen_geometry.y())
    else:
        print("Второй монитор не обнаружен.")
        return

    window.show()
    sys.exit(app.exec())

# Запуск приложения
if __name__ == "__main__":
    db = Database('your_database.db')
    app = QApplication(sys.argv)  # Создаем экземпляр QApplication
    controller = Controller(db)      # Создаем экземпляр контроллера
    controller.run()               # Запускаем приложение
    sys.exit(app.exec())

