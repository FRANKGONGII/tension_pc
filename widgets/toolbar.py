from enum import auto

from PyQt5.QtWidgets import QToolBar, QPushButton, QMenu, QAction, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QButtonGroup, QWidget, QSizePolicy, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator
from component.buttons import MenuButton,ChartButton1,ChartButton2


class ToolBarWidget(QToolBar):

    from enum import Enum, auto
    class TestStatus(Enum):
        no_test= auto()  # 自动分配值(从1开始)
        on_retest = auto()

    switch_chart_1 = pyqtSignal()  # 切换信号（供主界面使用）
    switch_chart_2 = pyqtSignal()
    history_visible = pyqtSignal()
    clear_panel_clicked = pyqtSignal()
    edit_visible = pyqtSignal()
    x_range_changed = pyqtSignal(int, int)
    y_range_changed = pyqtSignal(int, int)
    # 用于打印的信号量
    print_doc_signal = pyqtSignal(int) 

    status = TestStatus.no_test



    def __init__(self):
        super().__init__()
        self.setMovable(False)
        self.init_ui()

    def init_ui(self):
        # 创建坐标轴范围设置按钮，点击弹出对话框
        self.axis_range_button = QPushButton("坐标轴范围")
        self.axis_range_button.setCursor(Qt.PointingHandCursor)
        self.axis_range_button.clicked.connect(self.show_axis_range_dialog)

        self.menu_btn = MenuButton()
        self.addWidget(self.menu_btn)

        self.chart_btn1 = ChartButton1()
        self.chart_btn1.clicked.connect(self.switch_chart_1.emit)
        self.addWidget(self.chart_btn1)

        self.chart_btn2 = ChartButton2()
        self.chart_btn2.setEnabled(False)  # 暂时禁用
        self.chart_btn2.clicked.connect(self.switch_chart_2.emit)
        self.addWidget(self.chart_btn2)

        self.save_btn = QPushButton("测试入库")
        self.addWidget(self.save_btn)

        self.print_btn = QPushButton("打印")
        self.addWidget(self.print_btn)

        # 添加坐标轴范围设置按钮
        self.addWidget(self.axis_range_button)

        # 查询历史
        history_btn = QPushButton("查询历史")
        history_btn.setCursor(Qt.PointingHandCursor)
        history_btn.clicked.connect(self.on_get_history)
        self.addWidget(history_btn)

        # 清空面板
        self.clear_import_btn = QPushButton("清空面板")
        self.clear_import_btn.setCursor(Qt.PointingHandCursor)
        self.clear_import_btn.clicked.connect(self.clear_panel_clicked.emit)
        self.addWidget(self.clear_import_btn)

        # 数据编辑：放在帮助左边，左右各增加间距
        spacer_left = QWidget()
        spacer_left.setFixedWidth(24)
        spacer_left.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.addWidget(spacer_left)
        self.edit_btn = QPushButton("数据编辑")
        self.addWidget(self.edit_btn)
        spacer_right = QWidget()
        spacer_right.setFixedWidth(24)
        spacer_right.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.addWidget(spacer_right)

        # 帮助
        help_btn = QPushButton("帮助")
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.clicked.connect(self.on_help)
        self.addWidget(help_btn)

        # 互斥选中：仅算法1、算法2两个按钮，点击后高亮，点击另一按钮时原选中自动恢复原色
        self._chart_button_group = QButtonGroup(self)
        self._chart_button_group.setExclusive(True)
        for btn in (self.chart_btn1, self.chart_btn2):
            btn.setCheckable(True)
            self._chart_button_group.addButton(btn)

        # 仅选中态样式，不修改默认样式
        self.setStyleSheet("""
            QToolBar QPushButton:checked {
                background-color: #2196F3;
                color: white;
            }
        """)

    def on_edit(self):
        # print("编辑按钮点击")
        self.edit_visible.emit()
        
    def on_print(self):
        # 发射打印信号量
        self.print_doc_signal.emit(self._now_handle_data_id) 


    def on_get_history(self):
        # print("查询历史按钮点击")
        self.history_visible.emit()

    def on_help(self):
        from widgets.dialog.HelpDialog import HelpDialog
        dialog = HelpDialog(self)
        dialog.exec_()
    
    def show_axis_range_dialog(self):
        """显示坐标轴范围设置对话框"""
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("设置坐标轴范围")
        dialog.resize(300, 200)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # X轴（载荷）范围设置
        x_layout = QHBoxLayout()
        x_label = QLabel("X轴范围 (载荷):")
        self.x_min_input = QLineEdit()
        self.x_min_input.setValidator(QIntValidator(0, 99999))
        self.x_min_input.setPlaceholderText("最小值")
        self.x_min_input.setText("2500")  # 默认值
        
        x_separator = QLabel("-")
        
        self.x_max_input = QLineEdit()
        self.x_max_input.setValidator(QIntValidator(0, 99999))
        self.x_max_input.setPlaceholderText("最大值")
        self.x_max_input.setText("10000")  # 默认值
        
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.x_min_input)
        x_layout.addWidget(x_separator)
        x_layout.addWidget(self.x_max_input)
        
        # Y轴（位移）范围设置
        y_layout = QHBoxLayout()
        y_label = QLabel("Y轴范围 (位移):")
        self.y_min_input = QLineEdit()
        self.y_min_input.setValidator(QIntValidator(0, 99999))
        self.y_min_input.setPlaceholderText("最小值")
        self.y_min_input.setText("0")  # 默认值
        
        y_separator = QLabel("-")
        
        self.y_max_input = QLineEdit()
        self.y_max_input.setValidator(QIntValidator(0, 99999))
        self.y_max_input.setPlaceholderText("最大值")
        self.y_max_input.setText("200")  # 默认值
        
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_min_input)
        y_layout.addWidget(y_separator)
        y_layout.addWidget(self.y_max_input)
        
        # 添加预设选项
        preset_layout = QHBoxLayout()
        preset_label = QLabel("快速预设:")
        preset_layout.addWidget(preset_label)
        
        default_btn = QPushButton("默认")
        default_btn.clicked.connect(lambda: self.set_preset_range(2500, 10000, 0, 200))
        
        small_btn = QPushButton("0-200")
        small_btn.clicked.connect(lambda: self.set_preset_range(0, 2000, 0, 200))
        
        medium_btn = QPushButton("200-500")
        medium_btn.clicked.connect(lambda: self.set_preset_range(0, 5000, 0, 200))
        
        large_btn = QPushButton("500-1000")
        large_btn.clicked.connect(lambda: self.set_preset_range(0, 10000, 0, 200))
        
        preset_layout.addWidget(default_btn)
        preset_layout.addWidget(small_btn)
        preset_layout.addWidget(medium_btn)
        preset_layout.addWidget(large_btn)
        
        # 添加按钮框
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.apply_axis_ranges(dialog))
        button_box.rejected.connect(dialog.reject)
        
        # 添加到主布局
        layout.addLayout(x_layout)
        layout.addLayout(y_layout)
        layout.addLayout(preset_layout)
        layout.addWidget(button_box)
        
        # 显示对话框
        dialog.exec_()
    
    def set_preset_range(self, x_min, x_max, y_min, y_max):
        """设置预设范围"""
        self.x_min_input.setText(str(x_min))
        self.x_max_input.setText(str(x_max))
        self.y_min_input.setText(str(y_min))
        self.y_max_input.setText(str(y_max))
    
    def apply_axis_ranges(self, dialog):
        """应用用户设置的坐标轴范围"""
        try:
            # 获取用户输入的范围值
            x_min = int(self.x_min_input.text())
            x_max = int(self.x_max_input.text())
            y_min = int(self.y_min_input.text())
            y_max = int(self.y_max_input.text())
            
            # 验证范围有效性
            if x_min >= x_max or y_min >= y_max:
                raise ValueError("最小值必须小于最大值")
            
            # 发送信号更新图表范围
            self.x_range_changed.emit(x_min, x_max)
            self.y_range_changed.emit(y_min, y_max)
            
            # 更新按钮文本以显示当前范围
            self.axis_range_button.setText(f"坐标轴: X({x_min}-{x_max}), Y({y_min}-{y_max})")
            
            # print(f"坐标轴范围已更改为: X({x_min}-{x_max}), Y({y_min}-{y_max})")
            
            # 关闭对话框
            dialog.accept()
        except ValueError as e:
            # 显示错误消息
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "输入错误", str(e))

    def get_show_buttons(self):
        return self._show_buttons