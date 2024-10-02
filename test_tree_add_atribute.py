import sys
import json
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    QPushButton, QLineEdit, QDialog, QFormLayout, QDialogButtonBox, QFileDialog,
    QMessageBox, QComboBox
)

class GroupingDialog(QDialog):
    def __init__(self, users, columns):
        super().__init__()
        self.setWindowTitle("Grouping Users")
        self.layout = QVBoxLayout(self)

        self.group_size_input = QLineEdit(self)
        self.group_size_input.setPlaceholderText("Enter Group Size (N)")
        self.layout.addWidget(self.group_size_input)

        self.age_difference_input = QLineEdit(self)
        self.age_difference_input.setPlaceholderText("Enter Max Age Difference")
        self.layout.addWidget(self.age_difference_input)

        self.attribute_combo = QComboBox(self)
        self.attribute_combo.addItems(columns)  # Добавляем доступные атрибуты для группировки
        self.layout.addWidget(self.attribute_combo)

        self.group_button = QPushButton("Group Users", self)
        self.group_button.clicked.connect(self.group_users)
        self.layout.addWidget(self.group_button)

        self.result_tree_widget = QTreeWidget()
        self.result_tree_widget.setHeaderLabels(["Group", "Users"])
        self.layout.addWidget(self.result_tree_widget)

        self.users = users  # Сохраняем список пользователей

    def group_users(self):
        group_size = self.group_size_input.text()
        age_difference = self.age_difference_input.text()
        selected_attribute = self.attribute_combo.currentText()

        if not group_size.isdigit() or not age_difference.isdigit():
            QMessageBox.warning(self, "Input Error", "Please enter valid numbers for group size and age difference.")
            return

        group_size = int(group_size)
        age_difference = int(age_difference)

        # Сортируем пользователей по возрасту
        sorted_users = sorted(self.users, key=lambda item: int(item.text(2)))  # Предполагаем, что возраст находится в третьем столбце (индекс 2)

        groups = []
        current_group = []

        for user in sorted_users:
            if len(current_group) == 0:
                current_group.append(user)
            else:
                # Проверяем разницу в возрасте
                age_diff = int(user.text(2)) - int(current_group[0].text(2))
                if age_diff <= age_difference and len(current_group) < group_size:
                    current_group.append(user)
                else:
                    # Сохраняем текущую группу и начинаем новую
                    groups.append(current_group)
                    current_group = [user]

        # Не забываем добавить последнюю группу, если она не пустая
        if current_group:
            groups.append(current_group)

        self.display_groups(groups)

    def display_groups(self, groups):
        self.result_tree_widget.clear()
        for index, group in enumerate(groups):
            group_item = QTreeWidgetItem([f"Group {index + 1}"])
            self.result_tree_widget.addTopLevelItem(group_item)
            for item in group:
                user_item = QTreeWidgetItem([item.text(0)])  # Копируем только имя пользователя
                group_item.addChild(user_item)

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
        self.init_ui()

        self.columns = ["Name", "Email", "Age"]

    def init_ui(self):
        self.setWindowTitle("User Tree View")
        self.setGeometry(100, 100, 600, 400)

        self.layout = QVBoxLayout(self)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Name", "Email", "Age"])
        self.layout.addWidget(self.tree_widget)

        self.add_button = QPushButton("Add User", self)
        self.add_button.clicked.connect(self.open_user_dialog)
        self.layout.addWidget(self.add_button)

        self.load_button = QPushButton("Load from Excel", self)
        self.load_button.clicked.connect(self.load_from_excel)
        self.layout.addWidget(self.load_button)

        self.save_layout_button = QPushButton("Save Layout", self)
        self.save_layout_button.clicked.connect(self.save_layout)
        self.layout.addWidget(self.save_layout_button)

        self.load_layout_button = QPushButton("Load Layout", self)
        self.load_layout_button.clicked.connect(self.load_layout)
        self.layout.addWidget(self.load_layout_button)

        # Добавляем кнопку для группировки
        self.group_button = QPushButton("Group Users", self)
        self.group_button.clicked.connect(self.open_grouping_dialog)
        self.layout.addWidget(self.group_button)

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
        user_item = QTreeWidgetItem([user_data.get("Name"), user_data.get("Email"), user_data.get("Age")])
        self.tree_widget.addTopLevelItem(user_item)

        for i in range(3, len(self.columns)):
            user_item.setText(i, user_data.get(self.columns[i], ""))

    def load_from_excel(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file_name:
            try:
                df = pd.read_excel(file_name)
                for _, row in df.iterrows():
                    user_data = {col: str(row[col]) for col in self.columns if col in row}
                    self.add_user(user_data)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load data from Excel: {str(e)}")

    def add_column(self):
        new_column_name = self.new_column_input.text()
        if new_column_name:
            self.columns.append(new_column_name)
            current_headers = [self.tree_widget.headerItem().text(i) for i in range(self.tree_widget.headerItem().columnCount())]
            current_headers.append(new_column_name)
            self.tree_widget.setHeaderLabels(current_headers)

            self.new_column_input.clear()

    def save_layout(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Layout", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                data = {
                    "headers": self.columns,
                    "users": []
                }
                for i in range(self.tree_widget.topLevelItemCount()):
                    item = self.tree_widget.topLevelItem(i)
                    user_data = {self.columns[j]: item.text(j) for j in range(len(self.columns))}
                    data["users"].append(user_data)
                
                with open(file_name, 'w') as f:
                    json.dump(data, f, indent=4)
                QMessageBox.information(self, "Success", "Layout saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save layout: {str(e)}")

    def load_layout(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Layout", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    data = json.load(f)
                    self.tree_widget.clear()  # Очищаем текущее дерево
                    self.tree_widget.setHeaderLabels([None])
                    self.columns = data.get("headers", ["Name", "Email", "Age"])  # Загружаем заголовки
                    self.tree_widget.setHeaderLabels(self.columns)  # Устанавливаем заголовки в виджет дерева
                QMessageBox.information(self, "Success", "Layout loaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load layout: {str(e)}")

    def open_grouping_dialog(self):
        users = [self.tree_widget.topLevelItem(i) for i in range(self.tree_widget.topLevelItemCount())]
        dialog = GroupingDialog(users, self.columns[2:])
        dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserTreeView()
    window.show()
    sys.exit(app.exec())
