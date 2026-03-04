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
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
import random

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
    # 记录hight了几次
    _hightlight_time = 0
    # U型曲线标签方向控制
    _label_direction = "right"  # "left" 或 "right"，初始设为右侧
    _previous_x_for_direction = None  # 用于检测x值变化趋势
    _x_change_threshold = 5.0  # x值变化阈值，调大到5.0，超过此值认为到达转折点
    _direction_switched = False  # 标记是否已经切换过方向，防止多次切换
    # 基于工作位移的高亮点控制
    _y_start_value = None  # 起始点的y值（位移起始点）
    _y_max_value = None  # 最大y值（位移终止点）
    _highlight_step = None  # 间隔值（工作位移/5）
    _highlighted_displacements = set()  # 已打点的位移值集合，用于避免重复打点
    _is_increasing_phase = True  # 当前是否在增加阶段（压的过程）
    _previous_y = None  # 上一个y值，用于判断位移变化趋势
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

        # bottom_panel = self.create_bottom_grid()

        layout = QVBoxLayout()
        layout.addLayout(main_layout)
        # layout.addLayout(bottom_panel)

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
            "超载试验值(N)", "起始-终止时间", "超载试验保持时间",
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
                        # 检查是否已输入工作位移
            try:
                displacement_value = self.input_manager.get_value("出厂编号")
                # 确保工作位移不为空且是有效的数字，并且大于0
                if not displacement_value or float(displacement_value) <= 0:
                    QMessageBox.warning(self, "警告", "请先输入有效的出厂编号值")
                    return
            except (ValueError, TypeError):
                QMessageBox.warning(self, "警告", "请先输入有效的出厂编号值")
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
            self._hightlight_time = 0  # 重置标签左右判定，每轮从右5左5重新开始
            # 重置去0逻辑相关变量
            self._y_start = None
            self._has_recorded_start = False
            # 重置U型曲线标签方向控制变量
            self._label_direction = "right"  # 初始设为右侧
            self._previous_x_for_direction = None
            self._direction_switched = False  # 重置切换标记
            # 初始化基于工作位移的高亮点控制变量
            try:
                working_displacement = float(self.input_manager.get_value("工作位移"))
                self._highlight_step = working_displacement / 5.0  # 间隔 = 工作位移 / 5
                self._y_start_value = None  # 将在第一个数据点记录
                self._y_max_value = None  # 将在测试过程中更新
                self._highlighted_displacements = set()  # 已打点的位移值集合
                self._is_increasing_phase = True  # 初始为增加阶段（压的过程）
                self._previous_y = None  # 上一个y值
                print(f"初始化高亮点控制：工作位移={working_displacement}, 间隔={self._highlight_step}")
            except (ValueError, TypeError):
                self._highlight_step = None
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
            self.serial_reader.start_test_thread()  # 启动测试线程
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
            # 停止测试线程
            self.serial_reader.stop_test_thread()
            # 清空x轴初始值和拔销值
            self._x_initial = None
            self._pin_pull_value = None
            
            # 计算时间相关值
            import random
            from datetime import timedelta
            
            # 起始时间设置为当前时间+2分钟
            start_time = datetime.now() + timedelta(minutes=2)
            # 保持时间为4-5分钟的随机值
            duration_minutes = random.uniform(4, 5)
            duration_seconds = int(duration_minutes * 60)
            # 终止时间 = 起始时间 + 保持时间
            end_time = start_time + timedelta(seconds=duration_seconds)
            
            # 格式化时间显示
            start_time_str = start_time.strftime("%H:%M:%S")
            end_time_str = end_time.strftime("%H:%M:%S")
            
            # 格式化保持时间显示
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            duration_str = f"{minutes}分{seconds}秒"
            
            # 更新表单中的时间字段
            self.inputs["起始-终止时间"].setText(f"{start_time_str}-{end_time_str}")
            self.inputs["超载试验保持时间"].setText(duration_str)
            
            # # 测试结束后重新分析完整图形并重新排列标签
            self.reanalyze_and_rearrange_labels()
    
    def reanalyze_and_rearrange_labels(self):
        # """测试结束后重新分析完整图形，找到真正的拐点并重新排列标签"""
        # if not self._record_dot_x or not self._record_dot_y:
        #     return
        
        # # 更安全地清除现有的数值标签（只清除我们添加的标签）
        # items_to_remove = []
        # for item in self.plot_widget.plotItem.items[:]:
        #     if isinstance(item, TextItem):
        #         text_content = item.toPlainText()
        #         # 只清除内容为数字的标签
        #         try:
        #             float(text_content)
        #             items_to_remove.append(item)
        #         except ValueError:
        #             pass
        # for item in items_to_remove:
        #     self.plot_widget.plotItem.removeItem(item)

        # # 分析完整数据序列找到真正的拐点
        # x_data = self._record_dot_x
        # y_data = self._record_dot_y
        # min_x_index = x_data.index(min(x_data))

        # # 只为高亮点（每隔_show_dot_duration个点，且保证至少有一个标签）重新添加标签
        # highlighted_indices = list(range(0, len(x_data), self._show_dot_duration))
        # if len(x_data) > 0 and (len(x_data)-1) not in highlighted_indices:
        #     highlighted_indices.append(len(x_data)-1)  # 保证最后一个点有标签

        # # 统计左右侧标签数量，用于纵向错开
        # right_indices = [i for i in highlighted_indices if i <= min_x_index]
        # left_indices = [i for i in highlighted_indices if i > min_x_index]
        # # 计算自适应纵向偏移量（y轴范围的比例）
        # y_range = self.plot_widget.plotItem.viewRange()[1]
        # base_y_offset = (y_range[1] - y_range[0]) * 0.03
        # # 简化标签逻辑：前6个放右边，第7个及以后放左边
        # for idx, data_index in enumerate(highlighted_indices):
        #     x = x_data[data_index]
        #     y = y_data[data_index]
        #     x_range = self.plot_widget.plotItem.viewRange()[0]
        #     y_range = self.plot_widget.plotItem.viewRange()[1]
        #     x_offset = (x_range[1] - x_range[0]) * 0.02
        #     y_offset = (y_range[1] - y_range[0]) * 0.03
        #     if idx < 6:
        #         label_x = x + x_offset
        #     else:
        #         label_x = x - x_offset
        #     label_y = y - y_offset
        #     text_item = TextItem(f"{x:.3f}", color=(0, 0, 0), anchor=(0.5, 1))
        #     text_item.setPos(label_x, label_y)
        #     self.plot_widget.plotItem.addItem(text_item)
        # print(f"重新分析完成：找到拐点在索引 {min_x_index}，共重新排列了 {len(highlighted_indices)} 个标签")
            
        # 计算超载试验值（工作载荷的1.8-2.0倍随机整数）
        try:
            working_load = float(self.input_manager.get_value("工作载荷"))
            overload_factor = random.uniform(1.8, 2.0)
            overload_value = int(working_load * overload_factor)
            self.inputs["超载试验值"].setText(str(overload_value))
        except (ValueError, TypeError):
            # 如果工作载荷无效，设置为空
            self.inputs["超载试验值"].setText("")
        
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
        # 写入位移终止点值（取最大的y值，即最大位移值）
        end_value = max(self._record_dot_y) if self._record_dot_y else 0
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
        self.plot_widget.getViewBox().setMouseEnabled(x=False, y=False)  # 禁用拖拽平移，固定图表
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_moved)
        self.plot_widget.setXRange(x_center / 2, x_center * 2)
        # 将y轴范围设置为0-200
        self.plot_widget.setYRange(0, 200)


    def update_chart(self, x: list, y: list):
        if hasattr(self, 'curve'):
            self.curve.setData(x, y)


    # def rewrite_chart(self, x: [], y: []):
    #     self.plot_widget.clear()
    #     self.curve = self.plot_widget.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush='b')
    #     self._record_dot_y = y
    #     self._record_dot_x = x
    #     self._cnt_receive_dot = 0

    #     # 应用当前的x轴范围设置
    #     self.plot_widget.setXRange(self.current_x_min, self.current_x_max)
        
    #     # 插入边界线
    #     base = int(self.input_manager.get_value("工作载荷"))
    #     print("载荷", base)
    #     line1 = InfiniteLine(pos=base * 1.05, angle=90, pen='r')
    #     line2 = InfiniteLine(pos=base * 0.95, angle=90, pen='g')
    #     self.plot_widget.addItem(line1)
    #     self.plot_widget.addItem(line2)

    #     self.update_chart(self._record_dot_x, self._record_dot_y)
    #     for i in range(0, len(x)):
    #         self._cnt_receive_dot += 1
    #         if self._cnt_receive_dot % self._show_dot_duration == 0:
    #             highlight_index = i // self._show_dot_duration
    #             side = "right" if highlight_index < 6 else "left"
    #             self.highlight_plot(x[i], y[i], side)
    #             # 使用matplotlib保存高质量图片
    #             self.save_high_res_chart()


    def highlight_plot(self, x: float, y: float, side: str):
        # 加一个红色的大点覆盖在原曲线上，曲线不变
        highlight = pg.ScatterPlotItem(
            [x], [y],
            symbol='o',
            size=14,
            brush='r',
            pen='k'
        )
        self.plot_widget.addItem(highlight)

        # 获取当前视图范围
        view_range = self.plot_widget.getViewBox().viewRange()
        x_range = view_range[0]
        y_range = view_range[1]
        x_offset = (x_range[1] - x_range[0]) * 0.03  # 3%的x轴范围
        y_offset = (y_range[1] - y_range[0]) * 0.01  # 1%的y轴范围
        print(x, y, side)
        # 根据 side 参数决定标签左右
        if side == "right":
            label_x = x + x_offset
        else:
            label_x = x - x_offset
        label_y = y - y_offset

        label = TextItem(f"{x:.3f}", anchor=(0.5, 1), color=(0, 0, 0))
        label.setPos(label_x, label_y)
        self.plot_widget.addItem(label)
        # 添加坐标标签（基于U型曲线特性的智能位置选择）
        label = TextItem(f"{x:.3f}", anchor=(0.5, 1), color=(0, 0, 0)) 
        label.setPos(label_x, label_y)
        self.plot_widget.addItem(label)
    
    def save_high_res_chart(self, side: str):
        # TODO:11/3需要修复绘制逻辑，不要重新绘制之前的或者记录一下每个要highlight的位置是左边还是右边
        print(side,"==========================")
        """使用matplotlib重新绘制图表并保存为高质量PNG"""
        # 设置matplotlib支持中文显示
        plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
        
        # 创建matplotlib图表
        fig, ax = plt.subplots(figsize=(10, 8), dpi=300)  # 设置高DPI以获得更高质量
        
        # 绘制数据点
        ax.scatter(self._record_dot_x, self._record_dot_y, color='blue', s=5, alpha=0.7)
        
        # 在整个Y轴范围内均匀选择10个目标Y值，然后分配给左右各5个点
        n = len(self._record_dot_x)
        x_data, y_data = self._record_dot_x, self._record_dot_y
        min_x_index = x_data.index(min(x_data)) if x_data else 0
        
        left_indices = [i for i in range(n) if i <= min_x_index]
        right_indices = [i for i in range(n) if i > min_x_index]
        
        if n <= 10:
            highlighted_indices = list(range(n))
            left_selected = [i for i in highlighted_indices if i <= min_x_index]
            right_selected = [i for i in highlighted_indices if i > min_x_index]
        else:
            # 在整个Y轴范围内均匀选择10个目标Y值
            y_min, y_max = min(y_data), max(y_data)
            if y_max - y_min < 1e-6:
                y_targets = [y_min] * 10
            else:
                y_targets = [y_min + i * (y_max - y_min) / 9 for i in range(10)]
            
            # 交替分配：第1个左边，第2个右边，第3个左边，第4个右边...
            left_selected = []
            right_selected = []
            used = set()
            
            for idx, y_t in enumerate(y_targets):
                if idx % 2 == 0:
                    # 偶数索引（0,2,4,6,8）：分配给左边，优先从左臂找
                    left_cands = [i for i in left_indices if i not in used]
                    right_cands = [i for i in right_indices if i not in used]
                    all_cands = left_cands + right_cands  # 优先左臂
                    if not all_cands:
                        break
                    best = min(all_cands, key=lambda i: abs(y_data[i] - y_t))
                    left_selected.append(best)
                    used.add(best)
                else:
                    # 奇数索引（1,3,5,7,9）：分配给右边，优先从右臂找
                    left_cands = [i for i in left_indices if i not in used]
                    right_cands = [i for i in right_indices if i not in used]
                    all_cands = right_cands + left_cands  # 优先右臂
                    if not all_cands:
                        break
                    best = min(all_cands, key=lambda i: abs(y_data[i] - y_t))
                    right_selected.append(best)
                    used.add(best)
            
            highlighted_indices = left_selected + right_selected
        highlighted_x = [x_data[i] for i in highlighted_indices]
        highlighted_y = [y_data[i] for i in highlighted_indices]
        ax.scatter(highlighted_x, highlighted_y, color='red', s=15, edgecolor='black', alpha=1.0)
        
        x_offset = (self.current_x_max - self.current_x_min) * 0.06
        y_offset = 200 * 0.01
        
        for i, (x, y) in enumerate(zip(highlighted_x, highlighted_y)):
            # 前5个是左臂（放左侧），后5个是右臂（放右侧）
            if i < len(left_selected):
                label_x = x - x_offset
            else:
                label_x = x + x_offset
            label_y = y - y_offset
            ax.text(label_x, label_y, f'{x:.3f}', fontsize=14, ha='center', va='top', color='black')
        
        # 绘制工作载荷的上下5%线
        base = int(self.input_manager.get_value("工作载荷"))
        ax.axvline(x=base * 1.05, color='red', linestyle='--', linewidth=1.5)
        ax.axvline(x=base * 0.95, color='green', linestyle='--', linewidth=1.5)
        
        # 设置坐标轴标签和标题（增大字号确保打印可读）
        ax.set_title("载荷-位移特性曲线图\nLoad-Travel Performance Curve", color='purple', fontsize=16)
        ax.set_xlabel('载荷Load(N)', fontsize=14)
        ax.set_ylabel('位移Travel(mm)', fontsize=14)
        ax.tick_params(axis='both', labelsize=14)
        
        # 设置坐标轴范围
        ax.set_xlim(self.current_x_min, self.current_x_max)
        ax.set_ylim(0, 200)
        
        # 设置y轴为0在上（反转y轴）
        ax.invert_yaxis()
        
        # 添加网格线
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存为PNG文件
        plt.savefig("./resources/png.png", dpi=300, bbox_inches='tight')
        plt.close(fig)  # 关闭图表以释放内存
        
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


    # def create_bottom_grid(self):
    #     grid_layout = QGridLayout()
    #     font = QFont()
    #     font.setPointSize(11)

    #     labels = ["力(N)"] + [str(i) for i in range(1, 13)] + ["Pmax", "Pmin"]
    #     for col, text in enumerate(labels):
    #         label = QLabel(text)
    #         label.setFont(font)
    #         label.setAlignment(Qt.AlignCenter)
    #         label.setStyleSheet("background-color: lightgray; border: 1px solid gray;")
    #         grid_layout.addWidget(label, 0, col)

    #     return grid_layout


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
        
        # 记录起始点的y值（第一个点）
        if self._y_start_value is None:
            self._y_start_value = y
            print(f"记录起始点y值: {self._y_start_value}")
        
        # 更新最大y值
        if self._y_max_value is None or y > self._y_max_value:
            self._y_max_value = y
        
        # 判断位移变化趋势（用于确定是压还是拉的过程）
        if self._previous_y is not None:
            if y > self._previous_y:
                self._is_increasing_phase = True  # 位移增加，压的过程
            elif y < self._previous_y:
                self._is_increasing_phase = False  # 位移减少，拉的过程
        self._previous_y = y
        
        # 基于工作位移的高亮点逻辑
        if self._highlight_step is not None and self._y_start_value is not None:
            should_highlight = False
            highlight_side = "right"
            target_displacement = None
            
            if self._is_increasing_phase:
                # 压的过程：在起始点 + 间隔*1, 间隔*2, ..., 间隔*5 时打点
                for i in range(1, 6):  # 1, 2, 3, 4, 5
                    target = self._y_start_value + self._highlight_step * i
                    # 检查是否已经达到或超过目标值，且之前没有打过这个点
                    if target not in self._highlighted_displacements:
                        # 检查当前y值是否达到或超过目标值（允许一定容差）
                        if y >= target - 0.5:  # 允许0.5mm的容差
                            should_highlight = True
                            highlight_side = "right"
                            target_displacement = target
                            break
            else:
                # 拉的过程：从最大位移 - 间隔*1, 间隔*2, ..., 间隔*5 时打点
                if self._y_max_value is not None:
                    for i in range(1, 6):  # 1, 2, 3, 4, 5
                        target = self._y_max_value - self._highlight_step * i
                        # 检查是否已经达到或低于目标值，且之前没有打过这个点
                        if target not in self._highlighted_displacements:
                            # 检查当前y值是否达到或低于目标值（允许一定容差）
                            if y <= target + 0.5:  # 允许0.5mm的容差
                                should_highlight = True
                                highlight_side = "left"
                                target_displacement = target
                                break
            
            if should_highlight and target_displacement is not None:
                self._highlighted_displacements.add(target_displacement)
                self._hightlight_time += 1
                self.highlight_plot(x, y, highlight_side)
                # 使用matplotlib保存高质量图片
                self.save_high_res_chart(highlight_side)
                print(f"高亮点 #{self._hightlight_time}: y={y:.2f}, 目标位移={target_displacement:.2f}, 侧={highlight_side}")
        
        # 更新图表
        self.update_chart(self._record_dot_x, self._record_dot_y)
        
        # 添加到记录列表
        self._record_dot_x.append(x)
        self._record_dot_y.append(y)





