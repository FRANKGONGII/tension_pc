from enum import auto

from PyQt5.QtWidgets import QToolBar, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from component.buttons import MenuButton,ChartButton1,ChartButton2


class ToolBarWidget(QToolBar):

    from enum import Enum, auto
    class TestStatus(Enum):
        no_test= auto()  # 自动分配值(从1开始)
        on_retest = auto()

    switch_chart_1 = pyqtSignal()  # 切换信号（供主界面使用）
    switch_chart_2 = pyqtSignal()
    change_visible = pyqtSignal()
    history_visible = pyqtSignal()
    status = TestStatus.no_test



    def __init__(self):
        super().__init__()
        self.setMovable(False)
        self.init_ui()

    def init_ui(self):
        # 创建功能按钮
        buttons = [
            ("重新测试", self.on_retest),
            ("编辑", self.on_edit),
            ("测试入库", self.on_save),
            ("查询历史", self.on_get_history),
            ("关于", self.on_about)
        ]

        self.menu_btn = MenuButton()
        self.addWidget(self.menu_btn)

        self.chart_btn1 = ChartButton1()
        self.chart_btn1.clicked.connect(self.switch_chart_1.emit)
        self.addWidget(self.chart_btn1)

        self.chart_btn2 = ChartButton2()
        self.chart_btn2.clicked.connect(self.switch_chart_2.emit)
        self.addWidget(self.chart_btn2)


        for text, callback in buttons:
            btn = QPushButton(text)
            if text == "测试入库" or text == "编辑":
                btn.setEnabled(False)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(callback)
            self.addWidget(btn)

    def on_retest(self):
        print("重新测试按钮点击")
        self.change_visible.emit()


    def on_edit(self):
        print("编辑按钮点击")

    def on_save(self):
        print("入库按钮点击")

    def on_get_history(self):
        print("查询历史按钮点击")
        self.history_visible.emit()

    def on_about(self):
        print("关于按钮点击")

    def get_show_buttons(self):
        return self._show_buttons