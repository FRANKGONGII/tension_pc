import os
import sys

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedLayout, QLabel, QDockWidget, QTextEdit, \
    QApplication, QDialog, QMessageBox
from PyQt5.QtCore import Qt, QTimer
#from boto import connect_sns


from utils.paths import resource_path

from widgets.dialog.ScaleAdjustDialog import ScaleAdjustDialog
from widgets.dialog.ConfigDialog import ConfigDialog
from widgets.header import HeaderWidget
from widgets.data_display import DataDisplayWidget
from widgets.footer import FooterWidget
from widgets.sub_widgets.test_widget_1 import TestViewWidget_1
# from widgets.sub_widgets.test_widget_2 import TestViewWidget_2  # 算法2已注释
from widgets.sub_widgets.search_history_widget import SearchHistoryWidget
from widgets.toolbar import ToolBarWidget
from utils.data_manager import DataManager
from utils.system_logger import get_logger

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from utils.print_doc import print_doc, PrintCancelled
from utils.calculate import calculate_constancy, robust_min_max_means, solve_constancy_pull_params

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("恒力吊架性能测试系统")
        self.init_ui()
        self.load_styles()
        # 正在处理的表单数据id，默认-1，打印用
        self.now_handle_data_id = -1

    def init_ui(self):
        """初始化主界面布局"""
        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None
        dock_width = (avail.width() // 5) if avail else 400  # 1/5 可用宽度

        central_widget = QWidget()

        # 主垂直布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # 中部：使用 QStackedLayout
        self.stack = QStackedLayout()
        # 中部页面1：背景文字
        self.text_label = QLabel("恒力吊架性能测试系统")
        self.stack.addWidget(self.text_label)
        # 中部页面2：图表计算1
        self.chart_widget1 = TestViewWidget_1()
        self.stack.addWidget(self.chart_widget1)
        # 中部页面3：图表计算2（已注释）
        # self.chart_widget2 = TestViewWidget_2()
        # self.stack.addWidget(self.chart_widget2)
        self.current_index = 0

        # 添加各个组件
        self.header = HeaderWidget()
        self.data_display = DataDisplayWidget()

        # 绑定图表变化信号到数据显示
        # self.chart_widget1.mouse_data_changed.connect(self.data_display.update_data)
        # self.chart_widget2.mouse_data_changed.connect(self.data_display.update_data)
        self.chart_widget1.received_data_changed.connect(self.data_display.update_data)
        # TODO: 更新widget2
        # self.chart_widget2.received_data_changed.connect(self.data_display.update_data)

        # self.footer = FooterWidget()
        self.toolbar = ToolBarWidget()
        self.toolbar.switch_chart_1.connect(self.switch_chart_1)
        # self.toolbar.switch_chart_2.connect(self.switch_chart_2)  # 算法2已注释
        self.toolbar.history_visible.connect(self.history_visible)
        self.toolbar.clear_panel_clicked.connect(self.on_clear_panel)
        self.toolbar.save_btn.clicked.connect(self.save_data)
        self.toolbar.edit_btn.clicked.connect(self.edit_data)
        self.toolbar.print_btn.clicked.connect(self.handle_print_doc)
        self.toolbar.menu_btn.print_doc_signal.connect(lambda _: self.handle_print_doc())  # 菜单打印与工具栏打印同功能
        self.toolbar.menu_btn.config_clicked.connect(self.show_config_dialog)

        # 测试入库：启动时禁用；仅结束流程全部成功后启用；入库成功后再次禁用
        self.toolbar.save_btn.setEnabled(False)
        self.chart_widget1.test_started.connect(lambda: self.toolbar.save_btn.setEnabled(False))
        self.chart_widget1.test_ended.connect(lambda: self.toolbar.save_btn.setEnabled(True))

        main_layout.addWidget(self.toolbar, alignment=Qt.AlignTop)
        main_layout.addLayout(self.stack)
        main_layout.addWidget(self.data_display, alignment=Qt.AlignBottom)

        self.setCentralWidget(central_widget)

        # 创建查询侧边栏
        self.dock = QDockWidget("查询栏", self)
        self.search_history_widget = SearchHistoryWidget()
        self.search_history_widget.set_main_window(self)
        self.dock.setWidget(self.search_history_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.setMinimumWidth(dock_width)
        self.dock.setMaximumWidth(dock_width)
        self.dock.setVisible(False)

        # 默认展示算法1界面
        self.stack.setCurrentIndex(1)
        self.current_index = 1
        self.toolbar.chart_btn1.setChecked(True)
        self.chart_widget1.change_retest_visible()

        self.showMaximized()

    def handle_print_doc(self):
        # 1. 无效记录检查
        if self.now_handle_data_id <= 0:
            QMessageBox.warning(self, "提示", "无法打印：请先入库后再打印。")
            return
        # 2. 测试数据（x、y）非空检查
        x_list, y_list, highlight, side_right = DataManager.queryTestDataByFormId(self.now_handle_data_id)
        if not x_list or not y_list:
            QMessageBox.warning(self, "提示", "无法打印：该记录没有测试数据（x、y 坐标点为空），无法生成报表。")
            return
        try:
            print_doc(self.now_handle_data_id, self.chart_widget1._existing_file_path)
            # 3. 打印成功提示
            QMessageBox.information(self, "提示", "打印成功！")
        except PrintCancelled:
            pass  # 用户取消，不提示
        except Exception as e:
            QMessageBox.warning(self, "提示", f"打印失败：{e}")

    def load_styles(self):
        """加载样式表"""
        try:
            qss_path = resource_path(os.path.join("resources", "styles.qss"))
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            # print("未找到样式表文件")
            # pass
            get_logger().warning("未找到样式表文件")

    def create_chart(self):
        fig = Figure(figsize=(4, 3))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.plot([0, 1, 2, 3], [10, 1, 20, 3])
        ax.set_title("简单折线图")
        return canvas

    def switch_chart_1(self):
        self.stack.setCurrentIndex(1)
        self.chart_widget1.change_retest_visible()

    # def switch_chart_2(self):  # 算法2已注释
    #     self.stack.setCurrentIndex(2)
    #
    def history_visible(self):
        self.search_history_widget.handle_search()
        self.dock.setVisible(not self.dock.isVisible())

    def on_clear_panel(self):
        """处理清空面板按钮点击"""
        chart_widget1 = self.chart_widget1
        self.now_handle_data_id = -1
        # 清空原先数据
        chart_widget1._cnt_receive_dot = 0
        chart_widget1._record_dot_x = []
        chart_widget1._record_dot_y = []
        chart_widget1._record_dot_highlight = []
        chart_widget1._record_dot_side = []
        chart_widget1._has_saved = False  # 新测试开始，重置入库标记
            # 重置去0逻辑相关变量
        chart_widget1._y_start = None
        chart_widget1._has_recorded_start = False
        # 重置U型曲线标签方向控制变量
        chart_widget1._label_direction = "right"  # 初始设为右侧
        chart_widget1._previous_x_for_direction = None
        chart_widget1._direction_switched = False  # 重置切换标记
        chart_widget1._existing_file_path = None
        # 初始化基于工作位移的高亮点控制变量
        try:
            chart_widget1._highlight_step = 15
            chart_widget1._y_start_value = None  # 将在第一个数据点记录
            chart_widget1._y_max_value = None  # 将在测试过程中更新
            chart_widget1._highlighted_displacements = set()  # 已打点的位移值集合
            chart_widget1._is_increasing_phase = True  # 初始为增加阶段（压的过程）
            chart_widget1._previous_y = None  # 上一个y值
            chart_widget1.stack_cnt = []  # 用于记录拉过程中打点位置
        except (ValueError, TypeError):
            chart_widget1._highlight_step = None
            chart_widget1._working_displacement = None
            chart_widget1._max_highlight_count = 10
            chart_widget1.stack_cnt = []
            
        chart_widget1.plot_widget.clear()
        chart_widget1.curve = chart_widget1.plot_widget.plot([], [], pen='b', symbol='o', symbolSize=5, symbolBrush='b')
        chart_widget1.restart = False
        chart_widget1.adjust_center = -1
        chart_widget1.adjust_number = 0.0
        chart_widget1.adjust_constancy_m_ref = None
        chart_widget1.adjust_constancy_M_ref = None
        chart_widget1.adjust_constancy_phi = 0.0
        chart_widget1.adjust_constancy_gamma = 2.0
        chart_widget1._scale_replay_x = []

        chart_widget1.time_input.setText("")
        chart_widget1.input_manager.set_value("试验时间", "")
        for key in ["工作位移", "出厂编号", "工作载荷", "恒定度", "总位移", "位移终止点值", "位移起始点值", "实测位移值", "载荷偏差度", "超载试验值", "起始-终止时间", "超载试验保持时间", "锁定位置", "测试结果"]:
            chart_widget1.inputs[key].setText("")
            chart_widget1.input_manager.set_value(key, "")
        # 清空面板后恢复为「仅可记录初始值」
        chart_widget1._set_test_buttons_pre_record()
        self.toolbar.save_btn.setEnabled(False)

    def show_config_dialog(self):
        dialog = ConfigDialog(self)
        dialog.exec_()

    def save_data(self):
        # 1. 重复入库检查
        if self.chart_widget1.is_data_saved():
            QMessageBox.warning(self, "提示", "当前测试数据已入库，请勿重复入库。\n如需保存新数据，请先点击「开始」进行新一轮测试。")
            return

        data = self.chart_widget1.get_all_data()
        x_list, y_list, highlight, side_right = data[1], data[2], data[3], data[4]

        # 2. 数据检查：x、y 坐标点不能为空
        if not x_list or not y_list:
            QMessageBox.warning(self, "提示", "无法入库：测试数据为空。\n请先进行测试（点击「开始」并完成数据采集）后再入库。")
            return
        if len(x_list) != len(y_list) or len(x_list) == 0:
            QMessageBox.warning(self, "提示", "无法入库：x、y 坐标点数据异常，请检查测试数据。")
            return
        # 检查是否存在空值或无效值
        if any(v is None for v in x_list) or any(v is None for v in y_list):
            QMessageBox.warning(self, "提示", "无法入库：x、y 坐标点不能为空或包含无效值。")
            return

        # print("get data", data)
        last_id = DataManager.save_detail(data[0])
        self.now_handle_data_id = last_id
        DataManager.save_test_data(last_id, x_list, y_list, highlight, side_right)
        self.chart_widget1.mark_as_saved()
        self.toolbar.save_btn.setEnabled(False)

        # 3. 入库成功提示
        QMessageBox.information(self, "提示", "入库成功！")

    def edit_data(self):
        w = self.chart_widget1
        x = w._record_dot_x or []
        y = w._record_dot_y or []
        ys = y if len(y) == len(x) else None
        self.on_adjust_scale_clicked(points=x, ys=ys)

    def on_adjust_scale_clicked(self, points, ys=None):
        if points:
            m, M = robust_min_max_means(points)
            min_val, max_val = m, M
            constancy = calculate_constancy(points)
        else:
            min_val = max_val = constancy = None
        dialog = ScaleAdjustDialog(self)
        dialog.set_data_stats(min_val, max_val, constancy)

        if dialog.exec_() == QDialog.Accepted and points:
            self.try_scaling(points, ys, dialog.get_target_constancy_fraction())

    def try_scaling(self, points, ys, target_fraction):
        m, M = robust_min_max_means(points)
        if m is None or M is None or M + m <= 0:
            QMessageBox.warning(self, "提示", "无法计算缩放：力值数据无效。")
            return
        target_percent = float(target_fraction) * 100.0
        params = solve_constancy_pull_params(points, ys, target_percent, window_n=5)
        if params is None:
            QMessageBox.warning(self, "提示", "无法计算缩放：力值数据无效。")
            return
        try:
            wg_raw = self.chart_widget1.input_manager.get_value("工作载荷")
            Wg = float(wg_raw) / 1000.0
        except (TypeError, ValueError):
            QMessageBox.warning(self, "提示", "请先填写有效的工作载荷。")
            return
        if Wg <= 0:
            QMessageBox.warning(self, "提示", "工作载荷须为大于 0 的数值。")
            return
        cw = self.chart_widget1
        cw.adjust_constancy_m_ref = params["m_ref"]
        cw.adjust_constancy_M_ref = params["M_ref"]
        cw.adjust_constancy_phi = params["phi"]
        cw.adjust_constancy_gamma = params["gamma"]
        cw.adjust_number = params["phi"]
        cw.adjust_center = Wg