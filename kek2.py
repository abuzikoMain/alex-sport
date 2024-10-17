import sys
import pickle
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QInputDialog, QMessageBox, QLabel, QComboBox, QHBoxLayout,
    QFileDialog
)
from PySide6.QtGui import QClipboard, QAction

class GroupDataWindow(QWidget):
    def __init__(self, table_widget):
        super().__init__()
        self.table_widget = table_widget

        self.setWindowTitle("Группировка данных")
        self.setGeometry(200, 200, 400, 300)

        self.group_conditions = []

        self.group_column_combo = QComboBox()
        self.group_column_combo.setPlaceholderText("Выберите столбец для группировки")
        self.group_column_combo.currentIndexChanged.connect(self.update_unique_values)

        self.condition_layout = QVBoxLayout()
        self.condition_layout.addWidget(QLabel("Условия группировки:"))

        self.add_condition_button = QPushButton("Добавить условие")
        self.add_condition_button.clicked.connect(self.add_condition)

        self.group_button = QPushButton("Группировка")
        self.group_button.clicked.connect(self.group_data)

        layout = QVBoxLayout()
        layout.addLayout(self.condition_layout)
        layout.addWidget(self.add_condition_button)
        layout.addWidget(self.group_button)

        self.setLayout(layout)

        # Заполнение комбобокса столбцами из таблицы
        self.populate_columns()

    def add_condition(self):
        condition_widget = QWidget()
        condition_layout = QHBoxLayout()

        column_combo = QComboBox()
        column_combo.setPlaceholderText("Выберите столбец")
        column_combo.addItems([self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())])

        value_selection_combo = QComboBox()
        value_selection_combo.setPlaceholderText("Выберите значение или диапазон")
        value_selection_combo.setEnabled(False)

        min_value_input = QLineEdit()
        min_value_input.setPlaceholderText("Минимальное значение")
        max_value_input = QLineEdit()
        max_value_input.setPlaceholderText("Максимальное значение")

        # Обработчик изменения выбора столбца
        column_combo.currentIndexChanged.connect(lambda: self.update_value_selection(column_combo, value_selection_combo, min_value_input, max_value_input))

        condition_layout.addWidget(column_combo)
        condition_layout.addWidget(min_value_input)
        condition_layout.addWidget(max_value_input)
        condition_layout.addWidget(value_selection_combo)

        condition_widget.setLayout(condition_layout)
        self.condition_layout.addWidget(condition_widget)

        self.group_conditions.append((column_combo, min_value_input, max_value_input, value_selection_combo))

    def update_value_selection(self, column_combo, value_selection_combo, min_value_input, max_value_input):
        column_name = column_combo.currentText()
        column_index = self.get_column_index(column_name)
        column_index = 0
        if column_index is not None:
            is_numeric = True
            unique_values = set()

            for row in range(self.table_widget.rowCount()):
                item = self.table_widget.item(row, column_index)
                if item:
                    try:
                        float(item.text())  # Проверка на числовое значение
                    except ValueError:
                        is_numeric = False
                        unique_values.add(item.text())

            value_selection_combo.clear()
            if is_numeric:
                min_value_input.setEnabled(True)
                max_value_input.setEnabled(True)
                value_selection_combo.setEnabled(False)
            else:
                min_value_input.clear()
                max_value_input.clear()
                min_value_input.setEnabled(False)
                max_value_input.setEnabled(False)
                value_selection_combo.addItems(unique_values)
                value_selection_combo.setEnabled(True)

    def update_unique_values(self):
        # Этот метод будет вызываться при изменении выбранного столбца для группировки
        column_name = self.group_column_combo.currentText()
        column_index = self.get_column_index(column_name)

        if column_index is not None:
            is_numeric = True
            unique_values = set()

            for row in range(self.table_widget.rowCount()):
                item = self.table_widget.item(row, column_index)
                if item:
                    try:
                        float(item.text())  # Проверка на числовое значение
                    except ValueError:
                        is_numeric = False
                        unique_values.add(item.text())

            # Обновление комбобокса значений в зависимости от типа данных
            if is_numeric:
                self.min_value_input.setEnabled(True)
                self.max_value_input.setEnabled(True)
            else:
                self.min_value_input.clear()
                self.max_value_input.clear()
                self.min_value_input.setEnabled(False)
                self.max_value_input.setEnabled(False)
                self.value_selection_combo.clear()
                self.value_selection_combo.addItems(unique_values)
                self.value_selection_combo.setEnabled(True)

    def populate_columns(self):
        self.group_column_combo.clear()
        for index in range(self.table_widget.columnCount()):
            column_name = self.table_widget.horizontalHeaderItem(index).text()
            self.group_column_combo.addItem(column_name)

    def group_data(self):
        column_name = self.group_column_combo.currentText()
        if not column_name:
            QMessageBox.warning(self, "Ошибка", "Выберите столбец для группировки.")
            return

        column_index = self.get_column_index(column_name)
        if column_index is None:
            QMessageBox.warning(self, "Ошибка", "Столбец не найден.")
            return

        grouped_data = []
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, column_index)
            if item:
                match = True
                for column_combo, min_value_input, max_value_input, value_selection_combo in self.group_conditions:
                    condition_column_index = self.get_column_index(column_combo.currentText())
                    if condition_column_index is not None:
                        # Проверка на наличие значения в списке
                        if value_selection_combo.isEnabled() and value_selection_combo.currentText():
                            selected_value = value_selection_combo.currentText()
                            if self.table_widget.item(row, condition_column_index).text() != selected_value:
                                match = False
                                break
                        else:
                            try:
                                value = float(self.table_widget.item(row, condition_column_index).text())
                                min_value = float(min_value_input.text()) if min_value_input.text() else float('-inf')
                                max_value = float(max_value_input.text()) if max_value_input.text() else float('inf')

                                if not (min_value <= value <= max_value):
                                    match = False
                                    break
                            except ValueError:
                                match = False
                                break

                if match:
                    grouped_data.append([self.table_widget.item(row, col).text() if self.table_widget.item(row, col) else "" for col in range(self.table_widget.columnCount())])

        self.show_grouped_data(grouped_data)

    def get_column_index(self, column_name):
        for index in range(self.table_widget.columnCount()):
            if self.table_widget.horizontalHeaderItem(index).text() == column_name:
                return index
        return None

    def show_grouped_data(self, grouped_data):
        if grouped_data:
            msg = QMessageBox()
            msg.setWindowTitle("Группированные данные")
            msg.setText("Группированные данные:\n" + "\n".join([str(row) for row in grouped_data]))
            msg.exec()
        else:
            QMessageBox.information(self, "Группировка", "Нет данных, соответствующих условиям.")

class TableWidget(QTableWidget):
    def __init__(self):
        super().__init__()

    def setItem(self, row, column, item: QTableWidgetItem):
        super().setItem(row, column, item)


class TableStateManager:
    def __init__(self, table_widget: QTableWidget):
        self.table_widget = table_widget
        self.undo_stack = []


    def save_table_state(self):
        current_state = {
            "columns": [self.table_widget.horizontalHeaderItem(col).text() for col in range(self.table_widget.columnCount())],
            "data": []
        }

        for row in range(self.table_widget.rowCount()):
            row_data = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                row_data.append(item.text() if item else "")
            current_state["data"].append(row_data)

        self.undo_stack.append(current_state)

        # Ограничиваем размер стека
        if len(self.undo_stack) > 10:
            self.undo_stack.pop(0)

    def load_table_state(self, filename="table_state.pkl"):
        try:
            with open(filename, "rb") as f:
                table_state = pickle.load(f)

            self.table_widget.setColumnCount(len(table_state["columns"]))
            self.table_widget.setHorizontalHeaderLabels(table_state["columns"])
            self.table_widget.setRowCount(len(table_state["data"]))

            for row in range(len(table_state["data"])):
                for col in range(len(table_state["columns"])):
                    self.table_widget.setItem(row, col, QTableWidgetItem(table_state["data"][row][col]))

        except FileNotFoundError:
            QMessageBox.warning(self.table_widget, "Ошибка", "Состояние таблицы не найдено.")

    def undo(self):
        if not self.undo_stack:
            QMessageBox.information(self.table_widget, "Отмена", "Нет доступных действий для отмены.")
            return

        last_state = self.undo_stack.pop()

        self.table_widget.setColumnCount(len(last_state["columns"]))
        self.table_widget.setHorizontalHeaderLabels(last_state["columns"])
        self.table_widget.setRowCount(len(last_state["data"]))

        for row in range(len(last_state["data"])):
            for col in range(len(last_state["columns"])):
                self.table_widget.setItem(row, col, QTableWidgetItem(last_state["data"][row][col]))
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.undo_stack = []
        self.first_start_app = True

        self.setWindowTitle("Таблица данных")
        self.setGeometry(100, 100, 800, 600)

        self.table_widget = TableWidget()
        self.table_widget.setColumnCount(0)
        self.table_widget.setRowCount(0)
        self.table_widget.itemChanged.connect(self.item_changed)

        self.state_manager = TableStateManager(self.table_widget)

        # Создаем действия
        self.add_column_action = QAction("Добавить столбец", self)
        self.add_column_action.triggered.connect(self.add_column)
        self.add_column_action.setShortcut("Ctrl+C")  # Горячая клавиша для добавления столбца

        self.add_row_action = QAction("Добавить строку", self)
        self.add_row_action.triggered.connect(self.add_row)
        self.add_row_action.setShortcut("Ctrl+R")  # Горячая клавиша для добавления строки

        self.group_action = QAction("Группировка", self)
        self.group_action.triggered.connect(self.open_group_data_window)
        self.group_action.setShortcut("Ctrl+G")  # Горячая клавиша для группировки

        self.export_action = QAction("Экспорт в Excel", self)
        self.export_action.triggered.connect(self.export_to_excel)
        self.export_action.setShortcut("Ctrl+E")  # Горячая клавиша для экспорта

        self.import_action = QAction("Импорт из Excel", self)
        self.import_action.triggered.connect(self.import_from_excel)
        self.import_action.setShortcut("Ctrl+I")  # Горячая клавиша для импорта

        self.save_template_action = QAction("Сохранить шаблон", self)
        self.save_template_action.triggered.connect(self.save_template)
        self.save_template_action.setShortcut("Ctrl+S")  # Горячая клавиша для сохранения шаблона

        self.load_template_action = QAction("Загрузить шаблон", self)
        self.load_template_action.triggered.connect(self.load_template)
        self.load_template_action.setShortcut("Ctrl+L")  # Горячая клавиша для загрузки шаблона

        self.save_table_state_action = QAction("Сохранить состояние таблицы", self)
        self.save_table_state_action.triggered.connect(self.state_manager.save_table_state)
        self.save_table_state_action.setShortcut("Ctrl+T")  # Горячая клавиша для сохранения состояния таблицы

        self.load_table_state_action = QAction("Загрузить состояние таблицы", self)
        self.load_table_state_action.triggered.connect(self.state_manager.load_table_state)
        self.load_table_state_action.setShortcut("Ctrl+Shift+T")  # Горячая клавиша для загрузки состояния таблицы

        self.copy_action = QAction("Копировать", self)
        self.copy_action.triggered.connect(self.copy_to_clipboard)
        self.copy_action.setShortcut("Ctrl+C")  # Горячая клавиша для копирования

        self.paste_action = QAction("Вставить", self)
        self.paste_action.triggered.connect(self.paste_from_clipboard)
        self.paste_action.setShortcut("Ctrl+V")  # Горячая клавиша для вставки

        self.undo_action = QAction("Отмена", self)
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setShortcut("Ctrl+Z")  # Горячая клавиша для отмены

        # Создаем меню
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Файл")
        file_menu.addAction(self.import_action)
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_template_action)
        file_menu.addAction(self.load_template_action)

        edit_menu = menu_bar.addMenu("Правка")
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addAction(self.undo_action)

        table_menu = menu_bar.addMenu("Таблица")
        table_menu.addAction(self.add_column_action)
        table_menu.addAction(self.add_row_action)
        table_menu.addAction(self.group_action)
        table_menu.addSeparator()
        table_menu.addAction(self.save_table_state_action)
        table_menu.addAction(self.load_table_state_action)

        self.state_manager.load_table_state()
        # Загружаем шаблон при запуске
        self.load_template()

        # Устанавливаем центральный виджет
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        container.setLayout(layout)
        self.setCentralWidget(container)

    def item_changed(self, item: QTableWidgetItem):
        if self.first_start_app:
           self.save_table_state()
        elif self.undo_stack and len(self.undo_stack) > 1:            
            row = item.row()
            col = item.column()
            past = self.undo_stack[len(self.undo_stack) - 1]['data'][row][col]
            new = self.table_widget.item(row, col).text()
            if past != new:
                self.save_table_state()



    # Не забудьте сохранить состояние при редактировании ячеек
    def save_table_state(self):
        # Сохраняем текущее состояние таблицы в стек
        current_state = {
            "columns": [self.table_widget.horizontalHeaderItem(col).text() for col in range(self.table_widget.columnCount())],
            "data": []
        }

        for row in range(self.table_widget.rowCount()):
            row_data = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                row_data.append(item.text() if item else "")
            current_state["data"].append(row_data)

        self.undo_stack.append(current_state)  # Добавляем текущее состояние в стек

        # Ограничиваем размер стека, чтобы не занимать слишком много памяти
        if len(self.undo_stack) > 10:  # Например, храним только последние 10 состояний
            self.undo_stack.pop(0)


    def load_table_state(self):
        try:
            with open("table_state.pkl", "rb") as f:
                table_state = pickle.load(f)

            self.table_widget.setColumnCount(len(table_state["columns"]))
            self.table_widget.setHorizontalHeaderLabels(table_state["columns"])
            self.table_widget.setRowCount(len(table_state["data"]))

            for row in range(len(table_state["data"])):
                for col in range(len(table_state["columns"])):
                    self.table_widget.setItem(row, col, QTableWidgetItem(table_state["data"][row][col]))

        except FileNotFoundError:
            QMessageBox.warning(self, "Ошибка", "Состояние таблицы не найдено.")


    def closeEvent(self, event):
        self.save_template()  # Сохраняем шаблон перед выходом
        self.state_manager.save_table_state()  # Сохраняем состояние таблицы перед выходом
        event.accept()  # Позволяем закрыть окно


    def add_column(self):
        self.save_table_state()  # Сохраняем текущее состояние перед добавлением столбца
        column_name, ok = QInputDialog.getText(self, "Добавить столбец", "Введите имя столбца:")
        if ok and column_name:
            # Проверка на уникальность имени столбца
            for index in range(self.table_widget.columnCount()):
                if self.table_widget.horizontalHeaderItem(index).text() == column_name:
                    QMessageBox.warning(self, "Ошибка", "Столбец с таким именем уже существует.")
                    return

            current_column_count = self.table_widget.columnCount()
            self.table_widget.insertColumn(current_column_count)
            self.table_widget.setHorizontalHeaderItem(current_column_count, QTableWidgetItem(column_name))

    def add_row(self):
        self.save_table_state()  # Сохраняем текущее состояние перед добавлением строки
        current_row_count = self.table_widget.rowCount()
        self.table_widget.insertRow(current_row_count)

    def open_group_data_window(self):
        self.group_data_window = GroupDataWindow(self.table_widget)
        self.group_data_window.show()

    def copy_to_clipboard(self):
        clipboard = QClipboard()
        selected_items = self.table_widget.selectedItems()
        
        if not selected_items:
            return

        # Создаем строку для копирования
        rows = {}
        for item in selected_items:
            if item.row() not in rows:
                rows[item.row()] = []
            rows[item.row()].append(item.text())

        clipboard.setText("\n".join(["\t".join(rows[row]) for row in sorted(rows.keys())]))

    def paste_from_clipboard(self):
        self.save_table_state()  # Сохраняем текущее состояние перед вставкой
        clipboard = QClipboard()
        text = clipboard.text()
        
        if not text:
            return

        rows = text.split("\n")
        current_row = self.table_widget.currentRow()
        current_col = self.table_widget.currentColumn()

        for row_index, row in enumerate(rows):
            columns = row.split("\t")
            for col_index, value in enumerate(columns):
                if current_row + row_index < self.table_widget.rowCount() and current_col + col_index < self.table_widget.columnCount():
                    self.table_widget.setItem(current_row + row_index, current_col + col_index, QTableWidgetItem(value))

    def undo(self):
        if not self.undo_stack:
            QMessageBox.information(self, "Отмена", "Нет доступных действий для отмены.")
            return

        last_state = self.undo_stack.pop()  # Извлекаем последнее состояние из стека
        last_state = self.undo_stack.pop()

        # Восстанавливаем состояние таблицы
        self.table_widget.setColumnCount(len(last_state["columns"]))
        self.table_widget.setHorizontalHeaderLabels(last_state["columns"])
        self.table_widget.setRowCount(len(last_state["data"]))

        for row in range(len(last_state["data"])):
            for col in range(len(last_state["columns"])):
                self.table_widget.setItem(row, col, QTableWidgetItem(last_state["data"][row][col]))


    def save_template(self):
        template = {
            "columns": [self.table_widget.horizontalHeaderItem(col).text() for col in range(self.table_widget.columnCount())],
            "data": []
        }

        for row in range(self.table_widget.rowCount()):
            row_data = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                row_data.append(item.text() if item else "")
            template["data"].append(row_data)

        with open("template.pkl", "wb") as f:
            pickle.dump(template, f)

    def load_template(self):
        try:
            with open("template.pkl", "rb") as f:
                template = pickle.load(f)

            self.table_widget.setColumnCount(len(template["columns"]))
            self.table_widget.setHorizontalHeaderLabels(template["columns"])
            self.table_widget.setRowCount(len(template["data"]))

            for row in range(len(template["data"])):
                for col in range(len(template["columns"])):
                    self.table_widget.setItem(row, col, QTableWidgetItem(template["data"][row][col]))

        except FileNotFoundError:
            QMessageBox.warning(self, "Ошибка", "Шаблон не найден.")
        
        self.first_start_app = False           


    # Новый метод для импорта данных из Excel
    def import_from_excel(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите файл Excel", "", "Excel Files (*.xlsx *.xls)")
        if file_name:
            df = pd.read_excel(file_name)
            self.table_widget.setRowCount(df.shape[0])
            self.table_widget.setColumnCount(df.shape[1])
            self.table_widget.setHorizontalHeaderLabels(df.columns.tolist())

            for row in range(df.shape[0]):
                for col in range(df.shape[1]):
                    self.table_widget.setItem(row, col, QTableWidgetItem(str(df.iat[row, col])))

    def export_to_excel(self):
        data = []
        for row in range(self.table_widget.rowCount()):
            row_data = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)

        df = pd.DataFrame(data, columns=[self.table_widget.horizontalHeaderItem(col).text() for col in range(self.table_widget.columnCount())])
        df.to_excel("output.xlsx", index=False)
        QMessageBox.information(self, "Экспорт", "Данные успешно экспортированы в output.xlsx")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


