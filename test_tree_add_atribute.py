import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    QPushButton, QLineEdit, QDialog, QFormLayout, QDialogButtonBox
)


class UserDialog(QDialog):
    def __init__(self, columns, add_user_callback):
        super().__init__()
        self.setWindowTitle("Add User")
        self.layout = QFormLayout(self)

        self.inputs = {}
        for column in columns:
            input_field = QLineEdit(self)
            input_field.setPlaceholderText(f"Enter {column}")
            self.inputs[column] = input_field
            self.layout.addRow(column, input_field)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.add_user)  # Изменяем здесь
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.add_user_callback = add_user_callback  # Сохраняем коллбек для добавления пользователя

    def add_user(self):
        user_data = self.get_user_data()
        self.add_user_callback(user_data)  # Вызываем коллбек для добавления пользователя
        # Очищаем поля ввода, но не закрываем диалог
        for input_field in self.inputs.values():
            input_field.clear()

    def get_user_data(self):
        return {column: input_field.text() for column, input_field in self.inputs.items()}

class UserTreeView(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("User Tree View")
        self.setGeometry(100, 100, 600, 400)

        self.layout = QVBoxLayout(self)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Name", "Email", "Age"])  # Начальные столбцы
        self.layout.addWidget(self.tree_widget)

        self.add_button = QPushButton("Add User", self)
        self.add_button.clicked.connect(self.open_user_dialog)
        self.layout.addWidget(self.add_button)

        self.new_column_input = QLineEdit(self)
        self.new_column_input.setPlaceholderText("Enter New Attribute")
        self.layout.addWidget(self.new_column_input)

        self.add_column_button = QPushButton("Add Column", self)
        self.add_column_button.clicked.connect(self.add_column)
        self.layout.addWidget(self.add_column_button)

        self.columns = ["Name", "Email", "Age"]  # Список столбцов

    def open_user_dialog(self):
        dialog = UserDialog(self.columns, self.add_user)  # Передаем метод добавления пользователя
        dialog.exec()  # Открываем диалог

    def add_user(self, user_data):
        # Создаем элемент с данными пользователя
        user_item = QTreeWidgetItem([user_data.get("Name"), user_data.get("Email"), user_data.get("Age")])
        
        # Добавляем элемент в дерево
        self.tree_widget.addTopLevelItem(user_item)

        # Обновляем значения для новых столбцов
        for i in range(3, len(self.columns)):
            user_item.setText(i, user_data.get(self.columns[i], ""))  # Устанавливаем текст для новых столбцов

    def add_column(self):
        new_column_name = self.new_column_input.text()
        if new_column_name:
            # Добавляем новый заголовок
            self.columns.append(new_column_name)
            current_headers = [self.tree_widget.headerItem().text(i) for i in range(self.tree_widget.headerItem().columnCount())]
            current_headers.append(new_column_name)
            self.tree_widget.setHeaderLabels(current_headers)

            # Добавляем пустые ячейки для нового столбца в каждом элементе
            for i in range(self.tree_widget.topLevelItemCount()):
                item = self.tree_widget.topLevelItem(i)
                item.addChild(QTreeWidgetItem([None]))  # Убираем это, чтобы не добавлять дочерние элементы

            self.new_column_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserTreeView()
    window.show()
    sys.exit(app.exec())
