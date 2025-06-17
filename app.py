from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedLayout, QLabel, QDockWidget, QTextEdit, \
    QApplication, QDialog
from PyQt5.QtCore import Qt
from boto import connect_sns

from widgets.dialog.ScaleAdjustDialog import ScaleAdjustDialog
from widgets.header import HeaderWidget
from widgets.data_display import DataDisplayWidget
from widgets.footer import FooterWidget
from widgets.sub_widgets.test_widget_1 import TestViewWidget_1
from widgets.sub_widgets.test_widget_2 import TestViewWidget_2
from widgets.sub_widgets.search_history_widget import SearchHistoryWidget
from widgets.toolbar import ToolBarWidget
from utils.data_manager import DataManager

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("恒力吊架性能测试系统")
        self.resize(2000,1000)
        self.init_ui()
        self.load_styles()

    def init_ui(self):
        """初始化主界面布局"""
        screen =  QApplication.primaryScreen()
        screen_width = screen.size().width()
        dock_width = screen_width // 5  # 1/5 屏幕宽度

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
        # 中部页面3：图表计算2
        self.chart_widget2 = TestViewWidget_2()
        self.stack.addWidget(self.chart_widget2)
        self.current_index = 0

        # 添加各个组件
        self.header = HeaderWidget()
        self.data_display = DataDisplayWidget()

        # 绑定图表变化信号到数据显示
        self.chart_widget1.mouse_data_changed.connect(self.data_display.update_data)
        self.chart_widget2.mouse_data_changed.connect(self.data_display.update_data)
        self.chart_widget1.received_data_changed.connect(self.data_display.update_data)
        # TODO: 更新widget2
        # self.chart_widget2.received_data_changed.connect(self.data_display.update_data)

        # self.footer = FooterWidget()
        self.toolbar = ToolBarWidget()
        self.toolbar.switch_chart_1.connect(self.switch_chart_1)
        self.toolbar.switch_chart_2.connect(self.switch_chart_2)
        self.toolbar.change_visible.connect(self.change_visible)
        self.toolbar.history_visible.connect(self.history_visible)
        self.toolbar.save_btn.clicked.connect(self.save_data)
        self.toolbar.edit_btn.clicked.connect(self.edit_data)

        main_layout.addWidget(self.toolbar, alignment=Qt.AlignTop)
        main_layout.addLayout(self.stack)
        main_layout.addWidget(self.data_display, alignment=Qt.AlignBottom)

        self.setCentralWidget(central_widget)

        # 创建查询侧边栏
        self.dock = QDockWidget("查询栏", self)
        self.dock.setWidget(SearchHistoryWidget())
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.setMinimumWidth(dock_width)
        self.dock.setMaximumWidth(dock_width)
        self.dock.setVisible(False)

        # 最大化启动
        self.showMaximized()

    def load_styles(self):
        """加载样式表"""
        try:
            with open('resources/styles.qss', 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("未找到样式表文件")

    def create_chart(self):
        fig = Figure(figsize=(4, 3))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.plot([0, 1, 2, 3], [10, 1, 20, 3])
        ax.set_title("简单折线图")
        return canvas

    def switch_chart_1(self):
        self.stack.setCurrentIndex(1)

    def switch_chart_2(self):
        self.stack.setCurrentIndex(2)

    def change_visible(self):
        self.chart_widget1.change_retest_visible()
        self.chart_widget2.change_retest_visible()

    def history_visible(self):
        self.dock.setVisible(not self.dock.isVisible())

    def save_data(self):
        data = self.chart_widget1.get_all_data()
        print("get data", data)
        last_id = DataManager.save_detail(data[0])
        DataManager.save_test_data(last_id, data[1], data[2])

    def edit_data(self):
        x = self.chart_widget1._record_dot_x
        self.on_adjust_scale_clicked(points=x)

    def on_adjust_scale_clicked(self, points: []):
        # 示例数据（你应从实际数据获取）
        min_val = min(points)
        max_val = max(points)
        constancy = self.calculate_constancy(points)  # 自定义的恒定度计算

        # 弹出对话框
        dialog = ScaleAdjustDialog(self)
        dialog.set_data_stats(min_val, max_val, constancy)

        self.try_scaling(points, constancy)

        if dialog.exec_() == QDialog.Accepted:
            ratio = dialog.get_scale_ratio()
            if ratio:
                scaled_points = self.apply_scaling(points, ratio, constancy)
                print("缩放后数据：", scaled_points)

    def try_scaling(self, points, constancy):
        maxP = max(points)
        minP = min(points)
        mid = (maxP + minP) / 2
        for i in range(0, len(points)):
            if (points[i] < mid):
                points[i] *= 1 + (constancy - 5) / 100
            else:
                points[i] *= 1 - (constancy - 5) / 100
        print("scaling", points, self.calculate_constancy(points))


    def calculate_constancy(self, points):
        maxP = max(points)
        minP = min(points)
        return (maxP - minP) * 100 / (maxP + minP)




