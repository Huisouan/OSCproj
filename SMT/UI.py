#file:c:\Codes\OSCproj\SMT\UI.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QStackedWidget, QListWidget, QListWidgetItem

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PySide6 多界面示例")
        self.setGeometry(100, 100, 600, 400)

        # 创建一个 QStackedWidget 来管理多个界面
        self.stacked_widget = QStackedWidget()

        # 创建一个 QListWidget 作为目录
        self.directory_list = QListWidget()
        self.directory_list.currentRowChanged.connect(self.display_page)

        # 创建各个界面
        self.page1 = self.create_page1()
        self.page2 = self.create_page2()
        self.page3 = self.create_page3()

        # 将界面添加到 QStackedWidget
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)
        self.stacked_widget.addWidget(self.page3)

        # 将目录项添加到 QListWidget
        self.directory_list.addItem(QListWidgetItem("界面1"))
        self.directory_list.addItem(QListWidgetItem("界面2"))
        self.directory_list.addItem(QListWidgetItem("界面3"))

        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.directory_list)
        main_layout.addWidget(self.stacked_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def create_page1(self):
        page = QWidget()
        layout = QVBoxLayout()

        label = QLabel("这是界面1", page)
        button = QPushButton("按钮1", page)
        button.clicked.connect(lambda: self.label.setText("按钮1已点击"))

        layout.addWidget(label)
        layout.addWidget(button)
        page.setLayout(layout)
        return page

    def create_page2(self):
        page = QWidget()
        layout = QVBoxLayout()

        label = QLabel("这是界面2", page)
        button = QPushButton("按钮2", page)
        button.clicked.connect(lambda: self.label.setText("按钮2已点击"))

        layout.addWidget(label)
        layout.addWidget(button)
        page.setLayout(layout)
        return page

    def create_page3(self):
        page = QWidget()
        layout = QVBoxLayout()

        label = QLabel("这是界面3", page)
        button = QPushButton("按钮3", page)
        button.clicked.connect(lambda: self.label.setText("按钮3已点击"))

        layout.addWidget(label)
        layout.addWidget(button)
        page.setLayout(layout)
        return page

    def display_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())