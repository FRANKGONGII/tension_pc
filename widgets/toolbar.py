from PyQt5.QtWidgets import QToolBar, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from component.buttons import MenuButton,ChartButton1,ChartButton2


class ToolBarWidget(QToolBar):
    switch_chart_1 = pyqtSignal()  # 切换信号（供主界面使用）
    switch_chart_2 = pyqtSignal()
    visibility_changed = pyqtSignal(bool) # 发出显示/隐藏信号（True 显示，False 隐藏）
    _show_buttons = False


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
            ("帮助", self.on_help),
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
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(callback)
            self.addWidget(btn)

    def on_retest(value:bool, self):
        print("重新测试按钮点击")
        # if self._show_buttons != value:
        #     self._show_buttons = value
        #     self.visibility_changed.emit(value)  # 通知界面刷新


    def on_edit(self):
        print("编辑按钮点击")

    def on_save(self):
        print("入库按钮点击")

    def on_help(self):
        print("帮助按钮点击")

    def on_about(self):
        print("关于按钮点击")

    def get_show_buttons(self):
        return self._show_buttons