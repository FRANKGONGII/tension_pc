from PyQt5.QtWidgets import (
    QWidget, QLabel, QComboBox, QCheckBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QHBoxLayout, QPushButton, QDockWidget,
    QHeaderView
)
from PyQt5.QtCore import Qt

class SearchHistoryWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        # 查询方式
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("查询方式："))
        self.query_mode = QComboBox()
        self.query_mode.addItems(["试验日期", "用户编号", "出厂编号"])
        row1.addWidget(self.query_mode)
        layout.addLayout(row1)

        # 查询年份
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("查询年份："))
        self.year_box = QComboBox()
        self.year_box.addItems([str(y) for y in range(2020, 2031)])
        row2.addWidget(self.year_box)
        layout.addLayout(row2)

        # 复选框：全部数据 / 自动隐藏
        row3 = QHBoxLayout()
        self.checkbox_all = QCheckBox("全部数据")
        self.checkbox_auto_hide = QCheckBox("自动隐藏")
        row3.addWidget(self.checkbox_all)
        row3.addWidget(self.checkbox_auto_hide)
        layout.addLayout(row3)

        # 查询框（例如筛选框）
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("试验日期")
        layout.addWidget(self.search_box)

        # 表格控件
        self.table = QTableWidget(5, 3)  # 示例：5 行 3 列
        self.table.setHorizontalHeaderLabels(["测试日期", "出厂编号", "用户编号"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(self.table)

        # 删除按钮 + 输出标记复选框
        row4 = QHBoxLayout()
        self.delete_button = QPushButton("删除")
        self.delete_button.setEnabled(False)
        self.mark_checkbox = QCheckBox("输出标记")
        row4.addWidget(self.delete_button)
        row4.addWidget(self.mark_checkbox)
        layout.addLayout(row4)
