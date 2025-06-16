from PyQt5.QtWidgets import (
    QWidget, QLabel, QComboBox, QCheckBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QHBoxLayout, QPushButton, QDockWidget,
    QHeaderView
)
from PyQt5.QtCore import Qt
from sympy.strategies.core import switch
from utils import data_manager
from utils.data_manager import DataManager


class SearchHistoryWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        # 查询方式
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("查询方式："))
        self.query_mode = QComboBox()
        self.query_mode.addItems(["试验日期", "用户", "出厂编号"])
        row1.addWidget(self.query_mode)
        layout.addLayout(row1)

        # 查询年份
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("查询年份："))
        self.year_box = QComboBox()
        self.year_box.addItems([str(y) for y in range(2025, 2031)])
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
        self.search_box.setPlaceholderText("试验日期或者其他")
        layout.addWidget(self.search_box)

        # 表格控件
        self.table = QTableWidget(5, 3)  # 示例：5 行 3 列
        self.table.setHorizontalHeaderLabels(["试验日期", "用户", "出场编号"])
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

        # 搜索框回车触发搜索
        self.search_box.returnPressed.connect(self.handle_search)
        self.year_box.currentIndexChanged.connect(self.handle_search)
        self.handle_search()


    def handle_search(self):
        """执行搜索并刷新表格"""
        mode = self.query_mode.currentText()
        year = self.year_box.currentText()
        keyword = self.search_box.text().strip()

        results = self.query_records(mode, year, keyword)  # 返回 list[tuple]

        self.table.setRowCount(0)

        for row_data in results:
            row_index = self.table.rowCount()
            self.table.insertRow(row_index)
            for col_index, value in enumerate(row_data):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(value)))

    def query_records(self, mode, year, keyword):
        if mode == "试验日期":
            result = DataManager.queryByYear(year)
        elif mode == "用户" and len(keyword) != 0:
            result = DataManager.queryByYearAndUser(year, keyword)
        elif mode == "出厂编号" and len(keyword) != 0:
            result = DataManager.queryByYearAndFactoryNum(year, keyword)
        else:
            result = DataManager.queryByYear(year)

        print(result, year, keyword)
        return [ [row[1], row[2], row[4]] for row in result ]






