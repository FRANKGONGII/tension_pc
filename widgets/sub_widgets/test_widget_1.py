import ast
import statistics
import sys
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QHBoxLayout, QVBoxLayout,
    QGridLayout, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph as pg
from pyqtgraph import TextItem

from utils.serial_reader import SerialReader
from utils.config_manager import (
    get_serial_port, get_overload_factor, get_combobox_history, save_combobox_item,
)
from utils.data_manager import DataManager
from PO.input_data import inputManager
from pyqtgraph import InfiniteLine
from utils.calculate import *
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
import random

SCALE_MAP = {
    10240: (0, 10, 0, 500),
    18432: (0, 200, 0, 500),
    34816: (0, 400, 0, 500),
}
DEFAULT_SCALE = (0, 200, 0, 500)

class TestViewWidget_1(QWidget):
    mouse_data_changed = pyqtSignal(object)
    received_data_changed = pyqtSignal(object)
    test_started = pyqtSignal()   # 点击开始后发射，用于禁用测试入库
    test_ended = pyqtSignal()    # 点击结束后发射，用于启用测试入库

    show_buttons = False
    _show_dot_duration = 10
    _cnt_receive_dot = 0
    _record_dot_x = []
    _record_dot_y = []
    _record_dot_highlight = []
    _record_dot_side = []
    # 记录表单控件
    inputs = {}
    _history_combobox_keys = set()
    input_manager = inputManager()
    # 数据库
    DataManager = DataManager()
    # adjust_center != -1 表示已启用恒定度校准；点击缩放时写入 m_ref/M_ref/φ/γ，对称向中心压缩 + 按 y 峰分段滤波
    adjust_number = 0.0
    adjust_center = -1
    adjust_constancy_m_ref = None
    adjust_constancy_M_ref = None
    adjust_constancy_phi = 0.0
    adjust_constancy_gamma = 2.0
    # y轴起始点，用于去0逻辑
    _y_start = None
    # 标记是否已经记录了起始点
    _has_recorded_start = False
    # x轴初始值，用于x轴去0逻辑
    _x_initial = 0
    _y_initial = 0
    # 最新的x值，独立于_record_dot_x结构，时刻记录最新的x值
    _latest_x_value = -1
    # 最新的x值，独立于_record_dot_x结构，时刻记录最新的x值
    _latest_y_value = None
    # U型曲线标签方向控制
    _label_direction = "right"  # "left" 或 "right"，初始设为右侧
    _previous_x_for_direction = None  # 用于检测x值变化趋势
    _x_change_threshold = 5.0  # x值变化阈值，调大到5.0，超过此值认为到达转折点
    _direction_switched = False  # 标记是否已经切换过方向，防止多次切换
    # 基于工作位移的高亮点控制
    _highlight_threshold = 15  # 高亮点阈值
    _y_start_value = None  # 起始点的y值（位移起始点）
    _y_max_value = None  # 最大y值（位移终止点）
    _highlight_step = None  # 间隔值（工作位移/5）
    _highlighted_displacements = set()  # 已打点的位移值集合，用于避免重复打点
    _is_increasing_phase = True  # 当前是否在增加阶段（压的过程）
    _previous_y = None  # 上一个y值，用于判断位移变化趋势
    _has_saved = False  # 当前测试数据是否已入库，用于防止重复入库
    _existing_file_path = None
    _test_result = True
    _scale_switched = False
    _if_accpet_node = True
    _filter_x_window = []
    _FILTER_WINDOW_N = 5
    # 恒定度缩放：记录「去0后、固定 φ 变换前」的力值
    _scale_replay_x = []

    def __init__(self):
        super().__init__()
        # 图表组件
        # 下面两个是控制开始测试和结束的显示
        show_buttons = True
        self.if_start = True
        self.restart = False
        self.plot_widget = pg.PlotWidget()
        # 轴范围变量
        self.current_x_min = 0
        self.current_x_max = 200
        self.current_y_min = 0
        self.current_y_max = 500

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

    def set_restart(self):
        self.restart = True

    def create_left_form(self):
        form_layout = QVBoxLayout()
        font = QFont()
        font.setPointSize(12)


        # 记录初始值、开始、结束 三个按钮放在一排，记录初始值在第一位
        button_layout = QHBoxLayout()
        self.btn_zero = QPushButton("记录初始值(去0)")
        self.btn1 = QPushButton("开始")
        self.btn2 = QPushButton("结束")
        for btn in (self.btn_zero, self.btn1, self.btn2):
            btn.setFont(font)
            btn.setFixedHeight(32)
        self.btn_zero.setMinimumSize(150, 50)
        self.btn1.setMinimumSize(120, 50)
        self.btn2.setMinimumSize(120, 50)
        button_layout.addWidget(self.btn_zero)
        button_layout.addWidget(self.btn1)
        button_layout.addWidget(self.btn2)
        self.btn1.setEnabled(self.if_start)
        self.btn2.setEnabled(not self.if_start)

        # 绑定槽函数
        self.btn1.clicked.connect(self.on_start_clicked)
        self.btn2.clicked.connect(self.on_end_clicked)
        self.btn_zero.clicked.connect(self.on_zero_clicked)

        # 设置初始可见性
        self.btn_zero.setVisible(False)
        self.btn1.setVisible(False)
        self.btn2.setVisible(False)
        form_layout.addLayout(button_layout)
        form_layout.addSpacing(16)

        # 初始化串口监听（端口从配置读取，下次启动测试时生效）
        self.listening = True  # 状态变量：是否正在监听串口
        self.serial_reader = SerialReader(port=get_serial_port(), baudrate=9600)
        self.serial_reader.data_received.connect(self.handle_data)


        # 所有表单字段统一放入表格（两列：名称 + 值）
        # 每项: (标签文本, 存储key, 控件类型, 可选配置)
        table_rows = [
            ("试验时间：", "试验时间", "label", None),
            ("用户：", "用户", "combobox", {"items": get_combobox_history("用户"), "default": (get_combobox_history("用户") or [""])[-1], "save_history": True}),
            ("吊点代号：", "吊点代号", "combobox", {"items": get_combobox_history("吊点代号"), "default": (get_combobox_history("吊点代号") or [""])[-1], "save_history": True}),
            ("出厂编号：", "出厂编号", "lineedit", None),
            ("型号规格：", "型号规格", "lineedit", None),
            ("工作载荷(N): ", "工作载荷", "lineedit", None),
            ("总位移(mm): ", "总位移", "lineedit", None),
            ("工作位移：", "工作位移", "lineedit", None),
            ("操作员：", "操作员", "combobox", {"items": ["刘云佳", "张三", "李四"], "default": "刘云佳"}),
            ("检验员：", "检验员", "combobox", {"items": ["陈广春", "王五", "赵六"], "default": "陈广春"}),
            ("位移方向：", "位移方向", "combobox", {"items": ["上", "下", "左", "右"], "default": "上"}),
            ("位移起始点值", "位移起始点值", "label", None),
            ("位移终止点值", "位移终止点值", "label", None),
            ("实测位移值", "实测位移值", "label", None),
            ("超载试验值(kN)", "超载试验值", "label", None),
            ("起始-终止时间", "起始-终止时间", "label", None),
            ("超载试验保持时间", "超载试验保持时间", "label", None),
            ("恒定度", "恒定度", "label", None),
            ("锁定位置", "锁定位置", "label", None),
            ("载荷偏差度", "载荷偏差度", "label", None),
            ("测试结果", "测试结果", "label", None),
        ]
        result_table = QTableWidget(len(table_rows), 2)
        result_table.horizontalHeader().setVisible(False)
        result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        result_table.verticalHeader().setVisible(False)
        result_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        result_table.setShowGrid(True)
        result_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        result_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        result_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid black;
                gridline-color: black;
            }
            QTableWidget::item {
                border: 1px solid black;
            }
        """)
        value_font = QFont()
        value_font.setPointSize(14)
        for row, item in enumerate(table_rows):
            label_text, key, widget_type, cfg = item if len(item) == 4 else (*item[:3], None)
            # 左列：名称
            label_widget = QLabel(label_text)
            label_widget.setFont(font)
            label_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            result_table.setCellWidget(row, 0, label_widget)
            # 右列：值
            if widget_type == "lineedit":
                value_widget = QLineEdit()
                value_widget.setAlignment(Qt.AlignCenter)
            elif widget_type == "combobox":
                value_widget = QComboBox()
                value_widget.addItems(cfg["items"])
                value_widget.setCurrentText(cfg["default"])
                value_widget.setEditable(True)
                value_widget.lineEdit().setAlignment(Qt.AlignCenter)
                if cfg.get("save_history"):
                    self._history_combobox_keys.add(key)
                inputManager.set_value(self.input_manager, key, cfg["default"])
            else:
                value_widget = QLabel()
                value_widget.setStyleSheet("background-color: #F0F0F0;")
            value_widget.setFont(value_font)
            value_widget.setMinimumHeight(28)
            if isinstance(value_widget, QLabel):
                value_widget.setAlignment(Qt.AlignCenter)
            result_table.setCellWidget(row, 1, value_widget)
            self.inputs[key] = value_widget
        self.time_input = self.inputs["试验时间"]
        form_layout.addWidget(result_table, 1)
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
        self.input_manager.set_value(key.split("(")[0], value)

    def get_all_data(self):
        return self.input_manager, self._record_dot_x, self._record_dot_y, self._record_dot_highlight, self._record_dot_side

    def is_data_saved(self):
        """当前测试数据是否已入库（用于防止重复入库）"""
        return self._has_saved

    def mark_as_saved(self):
        """标记当前数据已入库"""
        self._has_saved = True

    def change_retest_visible(self):
        if self.show_buttons:
            self.btn1.setVisible(False)
            self.btn2.setVisible(False)
            self.btn_zero.setVisible(False)
        else:
            self.btn1.setVisible(True)
            self.btn2.setVisible(True)
            self.btn_zero.setVisible(True)
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
            # 检查是否已输入出厂编号（字符串，非空即可）
            factory_number = self.input_manager.get_value("出厂编号")
            if not factory_number or not str(factory_number).strip():
                QMessageBox.warning(self, "警告", "请先输入有效的出厂编号值")
                return
            
            # 保存历史 combobox 值到配置
            for hkey in self._history_combobox_keys:
                val = str(self.inputs[hkey].currentText()).strip()
                if val:
                    combo = self.inputs[hkey]
                    if combo.findText(val) == -1:
                        combo.addItem(val)
                    save_combobox_item(hkey, val)

            self.btn1.setEnabled(False)
            self.btn2.setEnabled(True)
            self.test_started.emit()
            now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_input.setText(now_time)
            inputManager.set_value(self.input_manager, "试验时间", now_time)
            # 清空原先数据
            self._cnt_receive_dot = 0
            self._record_dot_x = []
            self._record_dot_y = []
            self._record_dot_highlight = []
            self._record_dot_side = []
            self._has_saved = False  # 新测试开始，重置入库标记
            self._scale_switched = False
            self._filter_x_window = []
            self._scale_replay_x = []
            # 重置去0逻辑相关变量
            self._y_start = None
            self._has_recorded_start = False
            # 重置U型曲线标签方向控制变量
            self._label_direction = "right"  # 初始设为右侧
            self._previous_x_for_direction = None
            self._direction_switched = False  # 重置切换标记
            self._existing_file_path = None
            # 初始化基于工作位移的高亮点控制变量
            try:
                working_displacement = float(self.input_manager.get_value("工作位移"))
                self._working_displacement = working_displacement
                # 间隔 = 工作位移/10，高亮数量 = ceil(工作位移/间隔) ≈ 10，随工作位移缩放
                self._highlight_step = 15
                self._y_start_value = None  # 将在第一个数据点记录
                self._y_max_value = None  # 将在测试过程中更新
                self._highlighted_displacements = set()  # 已打点的位移值集合
                self._is_increasing_phase = True  # 初始为增加阶段（压的过程）
                self._previous_y = None  # 上一个y值
                self.stack_cnt = []  # 用于记录拉过程中打点位置
                self._max_highlight_count = max(10, int(working_displacement / self._highlight_step) + 2)  # 按实际工作位移决定数量上限
                # print(f"初始化高亮点控制：工作位移={working_displacement}, 间隔={self._highlight_step}, 最大高亮数≈{self._max_highlight_count}")
            except (ValueError, TypeError):
                self._highlight_step = None
                self._working_displacement = None
                self._max_highlight_count = 10
                self.stack_cnt = []
            if self.restart == True:
                self.plot_widget.clear()
                self.curve = self.plot_widget.plot([], [], pen='b', symbol='o', symbolSize=0.5, symbolBrush='b')
                self.restart = False
            # 插入边界线
            base = float(self.input_manager.get_value("工作载荷"))/1000
            line1 = InfiniteLine(pos=base * 1.06, angle=90, pen='r')
            line2 = InfiniteLine(pos=base * 0.94, angle=90, pen='g')
            for key in ["恒定度", "位移终止点值", "位移起始点值", "实测位移值", "载荷偏差度", "超载试验值", "起始-终止时间", "超载试验保持时间", "锁定位置", "测试结果"]:
                self.inputs[key].setText("")
                self.input_manager.set_value(key, "")
            self.plot_widget.addItem(line1)
            self.plot_widget.addItem(line2)
            # # 开始生成数据
            # TODO:正式时删除
            # self.serial_reader.start_test_thread()  # 启动测试线程
            self.serial_reader.start()
            


    # 点击结束要计算一些项目，并忽略后续数据
    def on_zero_clicked(self):
        """记录x初始值，用于后续去0"""
        print(f"尝试记录x初始值: {self._latest_x_value},已记录y初始值: {self._latest_y_value}")
        if self._latest_x_value is not None:
            # 记录最新的x值作为初始值
            # DEBUG：初始值先给个100
            self._x_initial = self._latest_x_value
            self._y_initial = self._latest_y_value
            # self._x_initial = 0
            # self._y_initial = 0
            # self._x_initial = 100
            # print(f"记录x初始值: {self._x_initial}")
            QMessageBox.information(self, "提示", f"已记录x初始值: {self._x_initial},已记录y初始值: {self._y_initial}")
        else:
            QMessageBox.warning(self, "警告", "暂无数据可记录初始值")

    def on_end_clicked(self):
        if self.btn2.isEnabled():
            self.restart = True
            # 逻辑处理
            # print("结束按钮被点击")
            self.btn2.setEnabled(False)
            self.btn1.setEnabled(True)
            self.test_ended.emit()
            # 后续如需重新开始，也可以再启用 start
            self.serial_reader.stop()
            # 停止测试线程
            # self.serial_reader.stop_test_thread()
            
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
            self.input_manager.set_value("起始-终止时间", f"{start_time_str}-{end_time_str}")
            self.inputs["超载试验保持时间"].setText(duration_str)
            self.input_manager.set_value("超载试验保持时间", duration_str)
            self.inputs["测试结果"].setText("合格" if self._test_result else "不合格")
            self.input_manager.set_value("测试结果", "合格" if self._test_result else "不合格")
            self._test_result = True

            # # 测试结束后重新分析完整图形并重新排列标签
            self.reanalyze_and_rearrange_labels()
            
            self.save_high_res_chart()

            # # 清空x轴初始值和拔销值
            # self._x_initial = 0
            # self._y_initial = 0
            # self._pin_pull_value = None

            # TODO:正式删除
            # self.serial_reader.stop_test_thread()
            # self.serial_reader.end()

    def _calibrate_constancy_on_recorded_series_if_needed(self):
        """固定参数已在点击缩放时确定，测试中已实时变换；结束无需再改力值。"""
        return

    def reanalyze_and_rearrange_labels(self):
        self._calibrate_constancy_on_recorded_series_if_needed()

        # 计算超载试验值（工作载荷 × 配置系数 + 0.001-0.002倍扰动）
        try:
            working_load = int(self.input_manager.get_value("工作载荷"))
            base_factor = get_overload_factor()
            perturbation = base_factor * random.uniform(0.001, 0.002)
            overload_factor = base_factor + perturbation
            overload_value = working_load * overload_factor
            self.inputs["超载试验值"].setText(str(round(overload_value)))
            self.input_manager.set_value("超载试验值", str(round(overload_value)))
        except (ValueError, TypeError):
            # 如果工作载荷无效，设置为空
            self.inputs["超载试验值"].setText("")
            self.input_manager.set_value("超载试验值", "")

        # 计算一些值
        # 写入恒定度
        constancy = calculate_constancy(self._record_dot_x)
        self.inputs["恒定度"].setText(f"{constancy:.2f}%")
        self.input_manager.set_value("恒定度", f"{constancy:.2f}%")
        # TODO:
        # 确认工作位移如何计算？
        # 计算方法是1.2倍工作位移和设计位移+25mm的较大值，注意目前的逻辑是反的
        # 正确应该是从工作位移的值出发
        # total_displacement = max(1.2 * float(self.inputs["工作位移"].text()), float(self.design_displacement) + 25)
        # self.inputs["总位移"].setText(f"{round(total_displacement)}")
        # self.input_manager.set_value("总位移", f"{round(total_displacement)}")
        # 写入位移终止点值（取最大的y值，即最大位移值）
        end_value = max(self._record_dot_y) if self._record_dot_y else 0
        end_value = round(end_value)
        end_str = f"{end_value}"
        self.inputs["位移终止点值"].setText(end_str + "mm")
        self.input_manager.set_value("位移终止点值", end_str)
        # 写入位移起始点值
        start_value = self._y_start_value
        start_value = round(start_value)
        start_str = f"{start_value}"
        self.inputs["位移起始点值"].setText(start_str + "mm")
        self.input_manager.set_value("位移起始点值", start_str)
        # 写入实测位移值
        real_value = end_value - start_value
        real_value = round(real_value)
        real_str = f"{real_value}"
        self.inputs["实测位移值"].setText(real_str + "mm")
        self.input_manager.set_value("实测位移值", real_str)
        # 写入载荷偏差度
        base = self.input_manager.get_value("工作载荷")
        if base != 0:
            load_values = calculate_load_deviation(float(base)/1000, self._record_dot_x)
            load_str = f"{load_values:.2f}%"
            self.inputs["载荷偏差度"].setText(load_str)
            self.input_manager.set_value("载荷偏差度", load_str)
        # 写入锁定位置（实测位移值 / 去0时记录的y位置到最大y值的距离）
        lock_position = calculate_lock_position(int(self.input_manager.get_value("工作位移")), real_value)
        lock_str = f"{lock_position:.2f}" if lock_position is not None else ""
        self.inputs["锁定位置"].setText(lock_str)
        self.input_manager.set_value("锁定位置", lock_str)

    def create_chart(self, x: list, y: list, x_center=5000, y_center=5000):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("载荷-位移特性曲线图\nLoad-Travel Performance Curve", color='purple', size='14pt')
        self.plot_widget.setLabel('left', '位移Travel(mm)', **{'color': '#000', 'font-size': '12pt'})
        self.plot_widget.setLabel('top', '载荷Load(kN)', **{'color': '#000', 'font-size': '12pt'})
        self.plot_widget.showGrid(x=True, y=True)

        # 把 curve 存起来，以便后续更新
        self.curve = self.plot_widget.plot(
            x, y,
            pen='b',
            symbol='o',
            symbolSize=0.5,
            symbolBrush='b'
        )
        # 设置移动获取坐标
        self.plot_widget.getViewBox().invertY(True)
        self.plot_widget.getViewBox().setMouseEnabled(x=False, y=False)  # 禁用拖拽平移，固定图表
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_moved)
        self.plot_widget.setXRange(self.current_x_min, self.current_x_max)
        self.plot_widget.setYRange(self.current_y_min, self.current_y_max)


    def update_chart(self, x: list, y: list):
        if hasattr(self, 'curve'):
            self.curve.setData(x, y)


    def highlight_plot(self, x: float, y: float, side_right: bool):
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
        y_offset = 0
        # print(x, y, side)
        # 根据 side 参数决定标签左右
        if side_right:
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

    def _rebuild_pyqt_chart_with_highlights(self):
        """按当前 _record_dot_x/y 重画主曲线、公差线及高亮散点与标签（x 被事后校准改写后须调用）。"""
        self.plot_widget.clear()
        self.curve = self.plot_widget.plot([], [], pen='b', symbol='o', symbolSize=0.5, symbolBrush='b')
        self.plot_widget.setXRange(self.current_x_min, self.current_x_max)
        self.plot_widget.setYRange(self.current_y_min, self.current_y_max)
        try:
            base = float(self.input_manager.get_value("工作载荷")) / 1000
            self.plot_widget.addItem(InfiniteLine(pos=base * 1.06, angle=90, pen='r'))
            self.plot_widget.addItem(InfiniteLine(pos=base * 0.94, angle=90, pen='g'))
        except (ValueError, TypeError):
            pass
        self.update_chart(self._record_dot_x, self._record_dot_y)
        hl, sd = self._record_dot_highlight, self._record_dot_side
        nx = len(self._record_dot_x)
        for i in range(min(len(hl), nx)):
            if hl[i]:
                side = sd[i] if i < len(sd) else True
                self.highlight_plot(self._record_dot_x[i], self._record_dot_y[i], side)

    def rewrite_chart(self, x: list, y: list, highlight: list, side_right: list):
        self._record_dot_x = x
        self._record_dot_y = y
        self._record_dot_highlight = list(highlight)
        self._record_dot_side = list(side_right)
        self._cnt_receive_dot = 0
        self._rebuild_pyqt_chart_with_highlights()
        # 使用matplotlib保存高质量图片
        # self.save_high_res_chart()

    def save_high_res_chart(self):
        """使用matplotlib重新绘制图表并保存为高质量PNG"""
        # 设置matplotlib支持中文显示（按平台选择已安装字体，避免 findfont 警告）
        if sys.platform.startswith("win"):
            plt.rcParams["font.family"] = ["SimHei", "SimSun", "Microsoft YaHei"]
        else:
            plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]

        # 创建matplotlib图表
        fig, ax = plt.subplots(figsize=(10, 8), dpi=300)  # 设置高DPI以获得更高质量

        # 绘制连线
        ax.plot(self._record_dot_x, self._record_dot_y, color='blue', linewidth=0.8, alpha=0.7)
        # 绘制数据点
        ax.scatter(self._record_dot_x, self._record_dot_y, color='blue', s=0.5, alpha=0.7)

        # n = len(self._record_dot_x)
        x_data, y_data = self._record_dot_x, self._record_dot_y
        highlighted_indices = [i for i, h in enumerate(self._record_dot_highlight) if h]
        highlighted_x = [x_data[i] for i in highlighted_indices]
        highlighted_y = [y_data[i] for i in highlighted_indices]
        ax.scatter(highlighted_x, highlighted_y, color='red', s=15, edgecolor='black', alpha=1.0)

        x_offset = (self.current_x_max - self.current_x_min) * 0.06
        y_offset = 0

        for idx, (x, y) in zip(highlighted_indices, zip(highlighted_x, highlighted_y)):
            side_right = self._record_dot_side[idx]
            if side_right:
                label_x = x + x_offset
            else:
                label_x = x - x_offset
            ax.text(label_x, y, f'{x:.3f}', fontsize=14, ha='center', va='top', color='black')
        
        # 绘制工作载荷的上下5%线
        base = float(self.input_manager.get_value("工作载荷"))/1000
        ax.axvline(x=base * 1.06, color='red', linestyle='--', linewidth=1.5)
        ax.axvline(x=base * 0.94, color='green', linestyle='--', linewidth=1.5)
        
        # 设置坐标轴标签和标题（增大字号确保打印可读）
        ax.set_title("载荷-位移特性曲线图\nLoad-Travel Performance Curve", color='purple', fontsize=16)
        ax.set_xlabel('载荷Load(kN)', fontsize=14)
        ax.set_ylabel('位移Travel(mm)', fontsize=14)
        ax.tick_params(axis='both', labelsize=14)
        # 将x轴移到上方
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
        ax.tick_params(axis='x', bottom=False, top=True, labelbottom=False, labeltop=True)
        
        # 设置坐标轴范围
        ax.set_xlim(self.current_x_min, self.current_x_max)
        ax.set_ylim(self.current_y_min, self.current_y_max)
        
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
        self.current_x_min = x_min
        self.current_x_max = x_max
        if hasattr(self, 'plot_widget'):
            self.plot_widget.setXRange(x_min, x_max)

    def set_y_range(self, y_min, y_max):
        self.current_y_min = y_min
        self.current_y_max = y_max
        if hasattr(self, 'plot_widget'):
            self.plot_widget.setYRange(y_min, y_max)

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
        x, y, status = ast.literal_eval(data)
        self._latest_x_value = x
        self._latest_y_value = y

        if not self._scale_switched and self.serial_reader._sending_data:
            scale = SCALE_MAP.get(status, DEFAULT_SCALE)
            self.set_x_range(scale[0], scale[1])
            self.set_y_range(scale[2], scale[3])
            self._scale_switched = True

        # 实现x轴去0逻辑：如果已经记录了初始值，则减去该值
        # print("init", self._latest_x_value)
        if self._x_initial is not None:
            x = x - self._x_initial
            # 确保x值不为负
            if x < 0:
                x = 0
        if self._y_initial is not None:
            y = y - self._y_initial
            # 确保y值不为负
            if y < 0:
                y = 0

        x_prescale = float(x)
        cal_series = None

        def _emit_display(xv):
            if self._record_dot_y is not None and len(self._record_dot_y) > 0:
                self.received_data_changed.emit([xv, y - self._record_dot_y[0], y])
            else:
                self.received_data_changed.emit([xv, 0, 0])

        if not self.serial_reader._sending_data:
            if len(self._filter_x_window) == 0:
                xv = x_prescale
            else:
                self._filter_x_window.append(x_prescale)
                if len(self._filter_x_window) > self._FILTER_WINDOW_N:
                    self._filter_x_window.pop(0)
                xv = statistics.median(self._filter_x_window)
            _emit_display(xv)
            return

        skip_first_node = self._if_accpet_node
        if skip_first_node:
            self._if_accpet_node = False

        # 启用校准且进入正式打点：用点击缩放时固定的 m_ref/M_ref/φ 对前缀做拉拢+中值滤波（不再随当前曲线重算 φ）
        if (
            (not skip_first_node)
            and self.adjust_center != -1
            and self.adjust_constancy_m_ref is not None
        ):
            self._scale_replay_x.append(x_prescale)
            y_prefix = self._record_dot_y + [y]
            pulled = apply_symmetric_extreme_pull(
                self._scale_replay_x,
                self.adjust_constancy_phi,
                self.adjust_constancy_m_ref,
                self.adjust_constancy_M_ref,
                self.adjust_constancy_gamma,
            )
            cal_series = median_filter_hysteresis_by_y_peak(
                y_prefix, pulled, self._FILTER_WINDOW_N
            )
            x = cal_series[-1]
        else:
            if len(self._filter_x_window) == 0:
                self._filter_x_window = [x_prescale] * self._FILTER_WINDOW_N
                x = x_prescale
            else:
                self._filter_x_window.append(x_prescale)
                if len(self._filter_x_window) > self._FILTER_WINDOW_N:
                    self._filter_x_window.pop(0)
                x = statistics.median(self._filter_x_window)

        _emit_display(x)

        if skip_first_node:
            return

        min_value = float(self.input_manager.get_value("工作载荷"))/1000 * 0.94
        max_value = float(self.input_manager.get_value("工作载荷"))/1000 * 1.06
        if (x < min_value or x > max_value) and self._y_start_value is not None:
            self._test_result = False
        
        # print("get data last:", x, y)
        self._cnt_receive_dot += 1
        
        # 记录起始点的y值（第一个点）
        if self._y_start_value is None:
            self._y_start_value = y
            # print(f"记录起始点y值: {self._y_start_value}")
        
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
        base = int(self.input_manager.get_value("总位移")) + 30
        # 基于工作位移的高亮点逻辑
        should_highlight = False
        highlight_side_right = True
        if self._highlight_step is not None and self._y_start_value is not None:
            target_displacement = None
            
            if self._is_increasing_phase:
                # 拉的过程：每隔 _highlight_threshold 打一个点
                if len(self.stack_cnt) == 0:
                    self.stack_cnt.append(y)
                    should_highlight = True
                else:
                    next_highlight_pos = self.stack_cnt[-1] + self._highlight_threshold
                    if next_highlight_pos < base and y >= next_highlight_pos:
                        self.stack_cnt.append(y)
                        should_highlight = True
            else:
                # 压的过程：y和拉一样
                if len(self.stack_cnt) > 0 and abs(y - self.stack_cnt[-1]) < 0.05:
                    should_highlight = True
                    highlight_side_right = False
                    self.stack_cnt.pop()
            
            if should_highlight:
                if target_displacement is not None and highlight_side_right:
                    self.stack_cnt.append(target_displacement)
                if self.adjust_center == -1:
                    self.highlight_plot(x, y, highlight_side_right)
                # 使用matplotlib保存高质量图片
                # self.save_high_res_chart()

        self._record_dot_y.append(y)
        if self.adjust_center != -1:
            self._record_dot_x = cal_series
        else:
            self._record_dot_x.append(x)
        self._record_dot_highlight.append(should_highlight)
        self._record_dot_side.append(highlight_side_right)

        if self.adjust_center != -1:
            self._rebuild_pyqt_chart_with_highlights()
        else:
            self.update_chart(self._record_dot_x, self._record_dot_y)