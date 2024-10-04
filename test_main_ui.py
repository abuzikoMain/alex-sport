
import sys
import json
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    QPushButton, QLineEdit, QDialog, QFormLayout, QDialogButtonBox, QFileDialog,
    QMessageBox, QComboBox, QCheckBox, QLabel, QHBoxLayout
)
from alpha.test_model_sql import *

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

    def add_user_callback(self, user_callback, data):
        user_callback(data)        


    def add_user(self):
        user_data = self.get_user_data()
        self.add_user_callback(user_data)  # Вызываем коллбек для добавления пользователя
        # Очищаем поля ввода, но не закрываем диалог
        for input_field in self.inputs.values():
            input_field.clear()

    def get_user_data(self):
        return {column: (input_field.text() if input_field.text() != '' else None) for column, input_field in self.inputs.items()}

class UserTreeView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db

        table_manager = TableManager(self.db)
        table_manager.create_tables()
        user_manager = UserManager(self.db)
        attribute_manager = AttributeManager(self.db)

        self.columns = attribute_manager.names_all_attributes()
        self.columns = [item[0] for item in self.columns]
        self.init_ui()
        

    def init_ui(self):
        self.setWindowTitle("User Tree View")
        self.setGeometry(100, 100, 600, 400)

        self.layout = QVBoxLayout(self)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(self.columns)
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

    def open_user_dialog(self):
        dialog = UserDialog(self.columns, self.add_user)
        dialog.exec()

    def add_user(self, user_data):
        params = []
        for _, value in user_data.items():
            if value:
                params.append(value)
        if params:
            user_item = QTreeWidgetItem(params)
            self.tree_widget.addTopLevelItem(user_item)

    def add_column(self):
        new_column_name = self.new_column_input.text()
        if new_column_name:
            self.columns.append(new_column_name)
            current_headers = [self.tree_widget.headerItem().text(i) for i in range(self.tree_widget.headerItem().columnCount())]
            current_headers.append(new_column_name)
            self.tree_widget.setHeaderLabels(current_headers)

            self.new_column_input.clear()


if __name__ == "__main__":
    db = Database('your_database.db')
    app = QApplication(sys.argv)
    window = UserTreeView(db)
    window.show()
    sys.exit(app.exec())