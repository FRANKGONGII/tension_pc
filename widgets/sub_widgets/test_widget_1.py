import ast
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QHBoxLayout, QVBoxLayout,
    QGridLayout, QPushButton, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph as pg
from pyqtgraph import TextItem

from utils.serial_reader import SerialReader
from utils.data_manager import DataManager
from PO.input_data import inputManager
from pyqtgraph import InfiniteLine
from utils.calculate import *


class TestViewWidget_1(QWidget):
    mouse_data_changed = pyqtSignal(object)
    received_data_changed = pyqtSignal(object)

    show_buttons = False
    _show_dot_duration = 10
    _cnt_receive_dot = 0
    _record_dot_x = []
    _record_dot_y = []
    # 记录表单控件
    inputs = {}
    input_manager = inputManager()
    # 数据库
    DataManager = DataManager()
    # 调整系数
    adjust_number = 1
    # 调整中心值
    adjust_center = -1
    # y轴起始点，用于去0逻辑
    _y_start = None
    # 标记是否已经记录了起始点
    _has_recorded_start = False
    # x轴初始值，用于x轴去0逻辑
    _x_initial = None
    # 拔销值
    _pin_pull_value = None
    # 最新的x值，独立于_record_dot_x结构，时刻记录最新的x值
    _latest_x_value = None
    def __init__(self):
        super().__init__()
        # 图表组件
        # 下面两个是控制开始测试和结束的显示
        show_buttons = True
        self.if_start = True
        self.restart = False
        self.plot_widget = pg.PlotWidget()
        # x轴范围变量
        self.current_x_min = 2500
        self.current_x_max = 10000

        # 整体布局：上方左右 + 下方表格
        main_layout = QHBoxLayout()
        left_panel = self.create_left_form()
        # 创建图表
        self.create_chart([], [])
        right_panel = self.plot_widget

        main_layout.addLayout(left_panel, 2)
        main_layout.addWidget(right_panel, 5)

        bottom_panel = self.create_bottom_grid()

        layout = QVBoxLayout()
        layout.addLayout(main_layout)
        layout.addLayout(bottom_panel)

        self.setLayout(layout)
        
        # TODO:补充设计位移的获取逻辑
        self.design_displacement = 10  # 设计位移，单位mm




    def create_left_form(self):
        form_layout = QVBoxLayout()
        font = QFont()
        font.setPointSize(12)


        # 添加两个按钮
        button_layout = QHBoxLayout()
        self.btn1 = QPushButton("开始")
        self.btn2 = QPushButton("结束")
        self.btn1.setFont(font)
        self.btn2.setFont(font)
        self.btn1.setFixedHeight(32)
        self.btn2.setFixedHeight(32)
        self.btn1.setMinimumSize(120, 50)
        self.btn2.setMinimumSize(120, 50)
        button_layout.addWidget(self.btn1)
        button_layout.addWidget(self.btn2)
        self.btn1.setEnabled(self.if_start)
        self.btn2.setEnabled(not self.if_start)

        # 绑定槽函数
        self.btn1.clicked.connect(self.on_start_clicked)
        self.btn2.clicked.connect(self.on_end_clicked)

        # 设置初始可见性
        self.btn1.setVisible(False)
        self.btn2.setVisible(False)
        form_layout.addLayout(button_layout)
        
        # 添加两个新按钮：去0按钮和记录拔销值按钮
        new_button_layout = QHBoxLayout()
        self.btn_zero = QPushButton("记录初始值(去0)")
        self.btn_pin_pull = QPushButton("记录拔销值")
        self.btn_zero.setFont(font)
        self.btn_pin_pull.setFont(font)
        self.btn_zero.setFixedHeight(32)
        self.btn_pin_pull.setFixedHeight(32)
        self.btn_zero.setMinimumSize(150, 50)
        self.btn_pin_pull.setMinimumSize(150, 50)
        new_button_layout.addWidget(self.btn_zero)
        new_button_layout.addWidget(self.btn_pin_pull)
        
        # 设置初始可见性（与开始/结束按钮逻辑一致）
        self.btn_zero.setVisible(False)
        self.btn_pin_pull.setVisible(False)
        form_layout.addLayout(new_button_layout)
        
        # 绑定槽函数
        self.btn_zero.clicked.connect(self.on_zero_clicked)
        self.btn_pin_pull.clicked.connect(self.on_pin_pull_clicked)

        # 初始化串口监听
        self.listening = True  # 状态变量：是否正在监听串口
        self.serial_reader = SerialReader(port='COM7', baudrate=9600)
        self.serial_reader.data_received.connect(self.handle_data)


        def add_label_input(label_text, input_widget=None):
            layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setFont(font)
            label.setFixedWidth(200)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            if input_widget is None:
                input_widget = QLineEdit()
            input_widget.setFont(font)
            input_widget.setFixedHeight(28)

            layout.addWidget(label)
            layout.addWidget(input_widget)
            form_layout.addLayout(layout)
            self.inputs[label_text.strip("").strip('：').split('(')[0]] = input_widget
            return input_widget

        # 分组添加内容
        self.time_input = add_label_input("试验时间：")

        user = add_label_input("用户：", QComboBox())
        # TODO:这些都要改成从配置文件读取
        user.addItems(["管理员1", "管理员2"])
        user.setCurrentIndex(0)
        user.setEditable(True)
        inputManager.set_value(self.input_manager, "用户", "管理员1")

        lang_points = add_label_input("吊点代号：", QComboBox())
        lang_points.addItems([f"{i:02d}" for i in range(1, 21)])
        lang_points.setCurrentIndex(0)
        inputManager.set_value(self.input_manager, "吊点代号", "01")
        
        add_label_input("出厂编号：")
        add_label_input("型号规格：")
        add_label_input("工作载荷(N): ")

        direction = add_label_input("位移方向：", QComboBox())
        direction.addItems(["上", "下", "左", "右"])
        direction.setCurrentIndex(0)
        inputManager.set_value(self.input_manager, "位移方向", "上")

        add_label_input("总位移(mm): ")
        add_label_input("工作位移：")

        operator = add_label_input("操作员：", QComboBox())
        operator.addItems(["刘云佳", "张三", "李四"])
        operator.setCurrentIndex(0)
        operator.setEditable(True)
        inputManager.set_value(self.input_manager, "操作员", "刘云佳")
        checker = add_label_input("检验员：", QComboBox())
        checker.addItems(["陈广春", "王五", "赵六"])
        checker.setCurrentIndex(0)
        checker.setEditable(True)
        inputManager.set_value(self.input_manager, "检验员", "陈广春")

        # 状态项
        for label in [
            "位移起始点值", "位移终止点值", "实测位移值",
            "超载试验值(N)", "起始 - 终止时间", "超载试验保持时间",
            "恒定度", "锁定位置", "载荷偏差度", "测试结果", "拔销值"
        ]:
            add_label_input(label)
        self.bind_signals()

        return form_layout

    # 记录表单内容
    def bind_signals(self):
        for key, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda val, k=key: self.on_input_changed(k, val))
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(lambda val, k=key: self.on_input_changed(k, val))

    def on_input_changed(self, key, value):
        print(f"{key} changed: {value}")
        self.input_manager.set_value(key.split("(")[0], value)

    def get_all_data(self):
        return self.input_manager, self._record_dot_x, self._record_dot_y

    def change_retest_visible(self):
        if self.show_buttons:
            self.btn1.setVisible(False)
            self.btn2.setVisible(False)
            self.btn_zero.setVisible(False)
            self.btn_pin_pull.setVisible(False)
        else:
            self.btn1.setVisible(True)
            self.btn2.setVisible(True)
            self.btn_zero.setVisible(True)
            self.btn_pin_pull.setVisible(True)
            self.show_buttons = False

    def on_start_clicked(self):
        if self.btn1.isEnabled():
            # 检查是否已输入工作载荷
            try:
                base_value = self.input_manager.get_value("工作载荷")
                # 确保工作载荷不为空且是有效的数字，并且大于0
                if not base_value or float(base_value) <= 0:
                    QMessageBox.warning(self, "警告", "请先输入有效的工作载荷值")
                    return
            except (ValueError, TypeError):
                QMessageBox.warning(self, "警告", "请先输入有效的工作载荷值")
                return
            
            # 检查是否已输入工作位移
            try:
                displacement_value = self.input_manager.get_value("工作位移")
                # 确保工作位移不为空且是有效的数字，并且大于0
                if not displacement_value or float(displacement_value) <= 0:
                    QMessageBox.warning(self, "警告", "请先输入有效的工作位移值")
                    return
            except (ValueError, TypeError):
                QMessageBox.warning(self, "警告", "请先输入有效的工作位移值")
                return
            
            # 逻辑处理
            print("开始按钮被点击")
            self.btn1.setEnabled(False)
            self.btn2.setEnabled(True)
            now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_input.setText(now_time)
            inputManager.set_value(self.input_manager, "试验时间", now_time)
            # 清空原先数据
            self._cnt_receive_dot = 0
            self._record_dot_x = []
            self._record_dot_y = []
            # 重置去0逻辑相关变量
            self._y_start = None
            self._has_recorded_start = False
            # 不清空表单中的拔销值显示
            # if "拔销值" in self.inputs:
            #     self.inputs["拔销值"].setText("")
            if self.restart == True:
                self.plot_widget.clear()
                self.curve = self.plot_widget.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush='b')
                self.restart = False
            # 插入边界线
            base = int(self.input_manager.get_value("工作载荷"))
            print("载荷", base)
            line1 = InfiniteLine(pos=base * 1.05, angle=90, pen='r')
            line2 = InfiniteLine(pos=base * 0.95, angle=90, pen='g')
            self.inputs["恒定度"].setText("")
            self.inputs["总位移"].setText("")
            self.inputs["位移终止点值"].setText("")
            self.inputs["位移起始点值"].setText("")
            self.inputs["实测位移值"].setText("")
            self.inputs["载荷偏差度"].setText("")
            self.plot_widget.addItem(line1)
            self.plot_widget.addItem(line2)
            # 开始生成数据
            self.serial_reader.start()
            


    # 点击结束要计算一些项目，并忽略后续数据
    def on_zero_clicked(self):
        """记录x初始值，用于后续去0"""
        if self._latest_x_value is not None:
            # 记录最新的x值作为初始值
            # DEBUG：初始值先给个100
            # self._x_initial = self._latest_x_value
            self._x_initial = 100
            print(f"记录x初始值: {self._x_initial}")
            QMessageBox.information(self, "提示", f"已记录x初始值: {self._x_initial}")
        else:
            QMessageBox.warning(self, "警告", "暂无数据可记录初始值")

    def on_pin_pull_clicked(self):
        """记录当前x值作为拔销值"""
        if self._latest_x_value is not None:
            # 记录最新的x值作为拔销值
            # DEBUG：拔销值先给个100
            # self._pin_pull_value = self._latest_x_value
            self._pin_pull_value = 100
            # 在左侧表单中显示拔销值
            if "拔销值" in self.inputs:
                self.inputs["拔销值"].setText(f"{self._pin_pull_value:.3f}")
            print(f"记录拔销值: {self._pin_pull_value}")
            QMessageBox.information(self, "提示", f"已记录拔销值: {self._pin_pull_value:.3f}")
        else:
            QMessageBox.warning(self, "警告", "暂无数据可记录拔销值")

    def on_end_clicked(self):
        if self.btn2.isEnabled():
            self.restart = True
            # 逻辑处理
            print("结束按钮被点击")
            self.btn2.setEnabled(False)
            self.btn1.setEnabled(True)
            # 后续如需重新开始，也可以再启用 start
            self.serial_reader.stop()
            # 清空x轴初始值和拔销值
            self._x_initial = None
            self._pin_pull_value = None
            # 计算一些值
            # 写入恒定度
            constancy = calculate_constancy(self._record_dot_x)
            self.inputs["恒定度"].setText(f"{constancy:.4f}%")
            # TODO:
            # 确认工作位移如何计算？
            # 计算方法是1.2倍工作位移和设计位移+25mm的较大值，注意目前的逻辑是反的
            # 正确应该是从工作位移的值出发
            total_displacement = max(1.2 * float(self.inputs["工作位移"].text()), float(self.design_displacement) + 25)
            self.inputs["总位移"].setText(f"{total_displacement:.2f}")
            # 写入位移终止点值
            end_value = self._record_dot_y[-1]
            self.inputs["位移终止点值"].setText(f"{end_value:.2f}" if self._record_dot_y else "0.00")
            # 写入位移起始点值
            start_value = self._record_dot_y[0]
            self.inputs["位移起始点值"].setText(f"{start_value:.2f}" if self._record_dot_y else "0.00")
            # 写入实测位移值
            real_value = end_value - start_value
            self.inputs["实测位移值"].setText(f"{real_value:.2f}")
            # 写入载荷偏差度
            base = self.input_manager.get_value("工作载荷")
            if base != 0:
                load_values = calculate_load_deviation(float(base), self._record_dot_x)
                self.inputs["载荷偏差度"].setText(f"{load_values:.2f}%")

    def create_chart(self, x: list, y: list, x_center=5000, y_center=5000):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("载荷-位移特性曲线图\nLoad-Travel Performance Curve", color='purple', size='14pt')
        self.plot_widget.setLabel('left', '位移Travel(mm)', **{'color': '#000', 'font-size': '12pt'})
        self.plot_widget.setLabel('top', '载荷Load(N)', **{'color': '#000', 'font-size': '12pt'})
        self.plot_widget.showGrid(x=True, y=True)

        # 把 curve 存起来，以便后续更新
        self.curve = self.plot_widget.plot(
            x, y,
            pen=None,
            symbol='o',
            symbolSize=5,
            symbolBrush='b'
        )
        # 设置移动获取坐标
        self.plot_widget.getViewBox().invertY(True)
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_moved)
        self.plot_widget.setXRange(x_center / 2, x_center * 2)
        # 将y轴范围设置为0-200
        self.plot_widget.setYRange(0, 200)


    def update_chart(self, x: list, y: list):
        if hasattr(self, 'curve'):
            self.curve.setData(x, y)


    def rewrite_chart(self, x: [], y: []):
        self.plot_widget.clear()
        self.curve = self.plot_widget.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush='b')
        self._record_dot_y = y
        self._record_dot_x = x
        self._cnt_receive_dot = 0

        # 应用当前的x轴范围设置
        self.plot_widget.setXRange(self.current_x_min, self.current_x_max)
        
        # 插入边界线
        base = int(self.input_manager.get_value("工作载荷"))
        print("载荷", base)
        line1 = InfiniteLine(pos=base * 1.05, angle=90, pen='r')
        line2 = InfiniteLine(pos=base * 0.95, angle=90, pen='g')
        self.plot_widget.addItem(line1)
        self.plot_widget.addItem(line2)

        self.update_chart(self._record_dot_x, self._record_dot_y)
        for i in range(0, len(x)):
            self._cnt_receive_dot += 1
            if self._cnt_receive_dot % self._show_dot_duration == 0:
                self.highlight_plot(x[i], y[i])
                # 保存图片
                pixmap = self.plot_widget.grab()
                pixmap.save("./resources/png.png")


    def highlight_plot(self, x: float, y: float):
        # 加一个红色的大点覆盖在原曲线上，曲线不变
        highlight = pg.ScatterPlotItem(
            [x], [y],
            symbol='o',
            size=14,
            brush='r',
            pen='k'
        )
        self.plot_widget.addItem(highlight)

        # 添加坐标标签（偏移一点避免遮挡）
        def find_non_overlapping_pos(x, y):
            if y < self._record_dot_y[-1]:
                return x - 2.0, y - 2.0
            else:
                return x + 2.0, y - 2.0


        label = TextItem(f"{x:.3f}", anchor=(0.5, 0), color='black')
        new_x, new_y = find_non_overlapping_pos(x, y)
        label.setPos(new_x, new_y)
        self.plot_widget.addItem(label)
        
    def set_x_range(self, x_min, x_max):
        """设置图表的x轴范围"""
        self.current_x_min = x_min
        self.current_x_max = x_max
        if hasattr(self, 'plot_widget'):
            self.plot_widget.setXRange(x_min, x_max)
            print(f"已设置x轴范围: {x_min}-{x_max}")


    def on_mouse_moved(self, evt):
        pos = evt
        mouse_point = self.plot_widget.getPlotItem().vb.mapSceneToView(pos)
        x = mouse_point.x()
        y = mouse_point.y()
        if self.btn1.isEnabled():
            self.mouse_data_changed.emit([x, y])  # 发射信号


    def create_bottom_grid(self):
        grid_layout = QGridLayout()
        font = QFont()
        font.setPointSize(11)

        labels = ["力(N)"] + [str(i) for i in range(1, 13)] + ["Pmax", "Pmin"]
        for col, text in enumerate(labels):
            label = QLabel(text)
            label.setFont(font)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("background-color: lightgray; border: 1px solid gray;")
            grid_layout.addWidget(label, 0, col)

        return grid_layout


    def handle_data(self, data):
        x, y = ast.literal_eval(data)
        # 时刻记录最新的x值，独立于_record_dot_x结构
        self._latest_x_value = x
        
        print(self.adjust_center, self.adjust_number)
        if self.adjust_center != -1:
            print("will adjust number")
            if x < self.adjust_center:
                x = x * (1 + self.adjust_number)
            else:
                x = x * (1 - self.adjust_number)
        
        # 实现x轴去0逻辑：如果已经记录了初始值，则减去该值
        print("init", self._latest_x_value)
        if self._x_initial is not None:
            x = x - self._x_initial
            # 确保x值不为负
            if x < 0:
                x = 0
        
        # 实现固定起始点逻辑：让第一个点显示在100的位置（0-200范围的中间）
        if not self._has_recorded_start and not self.btn1.isEnabled() and self.btn2.isEnabled():
            # 当开始按钮被禁用且结束按钮被启用时，表示正在测试过程中
            # 计算偏移量，使第一个点显示在100的位置
            self._y_start = y - 100
            self._has_recorded_start = True
            print(f"设置偏移量: {self._y_start}，使第一个点显示在100的位置")
            # 第一个点直接设置为100
            y = 100
        elif self._has_recorded_start:
            # 减去偏移量，保持相对变化
            y = y - self._y_start
            
        # 发射处理后的数据到data_display
        self.received_data_changed.emit([x, y])
        
        if self.serial_reader._sending_data == False:
            return
        
        print("get data:", x, y)
        self._cnt_receive_dot += 1
        # 更新图表
        self.update_chart(self._record_dot_x, self._record_dot_y)
        # TODO：按照位移y坐标间隔一定标记一个点
        if self._cnt_receive_dot % self._show_dot_duration == 0:
            self.highlight_plot(x, y)
            # 保存图片
            pixmap = self.plot_widget.grab()
            pixmap.save("./resources/png.png")
        
        # 添加到记录列表
        self._record_dot_x.append(x)
        self._record_dot_y.append(y)





