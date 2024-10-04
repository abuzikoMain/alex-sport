import sys
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                               QVBoxLayout, QPushButton, QFileDialog, QWidget, QFormLayout,
                               QCheckBox, QLineEdit, QMessageBox)

class ExcelViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Excel Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.table_widget = QTableWidget()
        self.setCentralWidget(self.table_widget)

        self.load_button = QPushButton("Load Excel File")
        self.load_button.clicked.connect(self.load_excel)

        layout = QVBoxLayout()
        layout.addWidget(self.load_button)
        layout.addWidget(self.table_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.grouping_conditions = []

    def load_excel(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file_name:
            self.display_data(file_name)

    def display_data(self, file_name):
        # Считываем данные из Excel, включая заголовки
        df = pd.read_excel(file_name)

        # Устанавливаем количество строк и столбцов в таблице
        self.table_widget.setRowCount(df.shape[0])
        self.table_widget.setColumnCount(df.shape[1])

        # Устанавливаем заголовки столбцов
        self.table_widget.setHorizontalHeaderLabels(df.columns)

        # Заполняем таблицу данными
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                self.table_widget.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

        # Создаем окно для условий группировки
        self.create_grouping_window(df)

    def create_grouping_window(self, df):
        self.grouping_window = QWidget()
        self.grouping_window.setWindowTitle("Grouping Conditions")
        layout = QFormLayout()

        # Условия для Age
        self.age_checkbox = QCheckBox("Age RAZNICA")
        self.age_input = QLineEdit()
        layout.addRow(self.age_checkbox, self.age_input)

        # Условия для остальных атрибутов
        for column in df.columns[2:]:  # Пропускаем Name и Email
            checkbox = QCheckBox(f"{column} RAZNICA")
            input_field = QLineEdit()
            layout.addRow(checkbox, input_field)
            self.grouping_conditions.append((checkbox, input_field))

        # Кнопка для группировки
        self.group_button = QPushButton("Сгруппировать")
        self.group_button.clicked.connect(lambda: self.group_data(df))
        layout.addRow(self.group_button)

        self.grouping_window.setLayout(layout)
        self.grouping_window.show()

    def group_data(self, df):
        conditions = []
        if self.age_checkbox.isChecked():
            age_value = self.age_input.text()
            if age_value.isdigit():
                conditions.append((df['Age'] > int(age_value), "Age"))

        for checkbox, input_field in self.grouping_conditions:
            if checkbox.isChecked():
                test_value = input_field.text()
                if test_value.isdigit():
                    conditions.append((df[checkbox.text().split()[0]] > int(test_value), checkbox.text().split()[0]))

        if not conditions:
            QMessageBox.warning(self, "Ошибка", "Не выбраны условия для группировки.")
            return

        # Применяем условия
        filtered_df = df
        for condition, column in conditions:
            filtered_df = filtered_df[condition]

        # Группируем по Name
        groups = filtered_df.groupby('Name').agg(list)

        # Выводим результат группировки
        result = "Группы:\n"
        for name, group in groups.iterrows():
            result += f"Группа {name}:\n"
            for col in group.index:
                result += "\t- " + f"{col}: " + ", ".join(map(str, group[col])) + "\n"

        QMessageBox.information(self, "Результат группировки", result)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ExcelViewer()
    viewer.show()
    sys.exit(app.exec())
