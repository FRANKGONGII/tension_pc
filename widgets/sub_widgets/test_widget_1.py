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

    def __init__(self):
        super().__init__()
        # 图表组件
        # 下面两个是控制开始测试和结束的显示
        show_buttons = True
        self.if_start = True
        self.restart = False
        self.plot_widget = pg.PlotWidget()

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

        # 初始化串口监听
        self.listening = True  # 状态变量：是否正在监听串口
        self.serial_reader = SerialReader(port='COM1', baudrate=9600)
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
            "恒定度", "锁定位置", "载荷偏差度", "测试结果"
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
        else:
            self.btn1.setVisible(True)
            self.btn2.setVisible(True)
            self.show_buttons = False

    def on_start_clicked(self):
        if self.btn1.isEnabled():
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
            if self.restart == True:
                self.plot_widget.clear()
                self.curve = self.plot_widget.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush='b')
                self.restart = False
            # 插入边界线
            base = int(self.input_manager.get_value("工作载荷"))
            print("载荷", base)
            line1 = InfiniteLine(pos=base * 1.05, angle=90, pen='r')
            line2 = InfiniteLine(pos=base * 0.95, angle=90, pen='g')
            self.plot_widget.addItem(line1)
            self.plot_widget.addItem(line2)
            # 开始生成数据
            self.serial_reader.start()
            


    # 点击结束要计算一些项目，并忽略后续数据
    def on_end_clicked(self):
        if self.btn2.isEnabled():
            self.restart = True
            # 逻辑处理
            print("结束按钮被点击")
            self.btn2.setEnabled(False)
            self.btn1.setEnabled(True)
            # 后续如需重新开始，也可以再启用 start
            self.serial_reader.stop()
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
            end_value = max(self._record_dot_y)
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

    def create_chart(self, x: list, y: list):
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
        self.plot_widget.setXRange(40, 80)
        self.plot_widget.setYRange(100, 250)


    def update_chart(self, x: list, y: list):
        if hasattr(self, 'curve'):
            self.curve.setData(x, y)


    def rewrite_chart(self, x: [], y: []):
        self.plot_widget.clear()
        self.curve = self.plot_widget.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush='b')
        self._record_dot_y = y
        self._record_dot_x = x
        self._cnt_receive_dot = 0

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
        print(self.adjust_center, self.adjust_number)
        if self.adjust_center != -1:
            print("will adjust number")
            if x < self.adjust_center:
                x = x * (1 + self.adjust_number)
            else:
                x = x * (1 - self.adjust_number)

        print("get data:", x, y, self._record_dot_x, self._record_dot_y)
        self._cnt_receive_dot += 1
        self.received_data_changed.emit([x, y])
        self.update_chart(self._record_dot_x, self._record_dot_y)
        # TODO：按照位移y坐标间隔一定标记一个点
        if self._cnt_receive_dot % self._show_dot_duration == 0:
            self.highlight_plot(x, y)
            # 保存图片
            pixmap = self.plot_widget.grab()
            pixmap.save("./resources/png.png")

        self._record_dot_x.append(x)
        self._record_dot_y.append(y)





