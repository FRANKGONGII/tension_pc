from enum import auto

from PyQt5.QtWidgets import QToolBar, QPushButton, QComboBox
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
    edit_visible = pyqtSignal()
    x_range_changed = pyqtSignal(int, int)

    status = TestStatus.no_test



    def __init__(self):
        super().__init__()
        self.setMovable(False)
        self.init_ui()

    def init_ui(self):
        # 创建功能按钮
        buttons = [
            ("重新测试", self.on_retest),
            ("查询历史", self.on_get_history),
            ("关于", self.on_about)
        ]
        
        # 创建x轴范围选择下拉按钮
        self.x_range_combo = QComboBox()
        self.x_range_combo.addItem("X轴范围: 默认")
        self.x_range_combo.addItem("X轴范围: 0-2000")
        self.x_range_combo.addItem("X轴范围: 0-5000")
        self.x_range_combo.addItem("X轴范围: 0-10000")
        self.x_range_combo.setCursor(Qt.PointingHandCursor)
        self.x_range_combo.currentIndexChanged.connect(self.on_x_range_changed)
        # 设置与其他工具栏按钮一致的样式
        self.x_range_combo.setStyleSheet("""
            QComboBox {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                font-size: 14px;
                padding: 4px 8px;
                min-width: 150px;
            }
            QComboBox:hover {
                background-color: #e8e8e8;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #f0f0f0;
            }
            QComboBox::down-arrow {
                image: url(:/icons/arrow-down.png);
                width: 16px;
                height: 16px;
            }
        """)

        self.menu_btn = MenuButton()
        self.addWidget(self.menu_btn)

        self.chart_btn1 = ChartButton1()
        self.chart_btn1.clicked.connect(self.switch_chart_1.emit)
        self.addWidget(self.chart_btn1)

        self.chart_btn2 = ChartButton2()
        self.chart_btn2.clicked.connect(self.switch_chart_2.emit)
        self.addWidget(self.chart_btn2)

        self.save_btn = QPushButton("测试入库")
        self.addWidget(self.save_btn)

        self.edit_btn = QPushButton("数据编辑")
        self.addWidget(self.edit_btn)


        # 首先添加重新测试按钮
        btn_retest = QPushButton(buttons[0][0])
        btn_retest.setCursor(Qt.PointingHandCursor)
        btn_retest.clicked.connect(buttons[0][1])
        self.addWidget(btn_retest)
        
        # 添加x轴范围选择下拉按钮
        self.addWidget(self.x_range_combo)
        
        # 添加剩余的按钮
        for text, callback in buttons[1:]:
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(callback)
            self.addWidget(btn)

    def on_retest(self):
        print("重新测试按钮点击")
        self.change_visible.emit()


    def on_edit(self):
        print("编辑按钮点击")
        self.edit_visible.emit()


    def on_save(self):
        print("入库按钮点击")


    def on_get_history(self):
        print("查询历史按钮点击")
        self.history_visible.emit()

    def on_about(self):
        print("关于按钮点击")
    
    def on_x_range_changed(self, index):
        """处理x轴范围变化事件"""
        # 根据选择的索引设置不同的x轴范围
        if index == 1:  # 选项1: 0-2000
            self.x_range_changed.emit(0, 2000)
        elif index == 2:  # 选项2: 0-5000
            self.x_range_changed.emit(0, 5000)
        elif index == 3:  # 选项3: 0-10000
            self.x_range_changed.emit(0, 10000)
        else:  # 默认: 2500-10000
            self.x_range_changed.emit(2500, 10000)
        print(f"x轴范围已更改为: {self.x_range_combo.currentText()}")

    def get_show_buttons(self):
        return self._show_buttons