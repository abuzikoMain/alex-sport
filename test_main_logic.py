import sys
# import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QDialog, QLabel, QLineEdit, QListWidget, QMessageBox
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Управление Пользователями")
        self.setGeometry(100, 100, 400, 300)

        self.user_list = QListWidget()
        self.load_users()

        self.add_button = QPushButton("Добавить Пользователя")
        self.add_button.clicked.connect(self.add_user)

        self.delete_button = QPushButton("Удалить Пользователя")
        self.delete_button.clicked.connect(self.delete_user)

        layout = QVBoxLayout()
        layout.addWidget(self.user_list)
        layout.addWidget(self.add_button)
        layout.addWidget(self.delete_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_users(self):
        # Здесь должна быть логика загрузки пользователей из базы данных
        self.user_list.addItems(["Иванов И.И.", "Петров П.П."])  # Пример данных

    def add_user(self):
        dialog = UserDialog(self)
        dialog.exec()

    def delete_user(self):
        selected_items = self.user_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для удаления.")
            return

        user_name = selected_items[0].text()
        reply = QMessageBox.question(self, "Подтверждение", f"Вы уверены, что хотите удалить {user_name}?",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Здесь должна быть логика удаления пользователя из базы данных
            self.user_list.takeItem(self.user_list.row(selected_items[0]))

class UserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Добавить Пользователя")
        self.setGeometry(150, 150, 300, 200)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("ФИО")
        self.weight_input = QLineEdit(self)
        self.weight_input.setPlaceholderText("Вес")
        self.height_input = QLineEdit(self)
        self.height_input.setPlaceholderText("Рост")

        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.save_user)

        layout = QVBoxLayout()
        layout.addWidget(self.name_input)
        layout.addWidget(self.weight_input)
        layout.addWidget(self.height_input)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_user(self):
        # Здесь должна быть логика сохранения пользователя в базу данных
        user_name = self.name_input.text()
        weight = self.weight_input.text()
        height = self.height_input.text()
        print(f"Сохранен пользователь: {user_name}, Вес: {weight}, Рост: {height}")
        self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
