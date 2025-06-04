from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QHBoxLayout, QVBoxLayout,
    QGridLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph as pg

from widgets.data_display import DataDisplayWidget


class TestViewWidget_2(QWidget):
    mouse_data_changed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        # 图表组件
        self.plot_widget = pg.PlotWidget()

        # 整体布局：上方左右 + 下方表格
        main_layout = QHBoxLayout()
        left_panel = self.create_left_form()
        # 创建图表
        self.create_chart()
        right_panel = self.plot_widget

        main_layout.addLayout(left_panel, 2)
        main_layout.addWidget(right_panel, 5)

        bottom_panel = self.create_bottom_grid()

        layout = QVBoxLayout()
        layout.addLayout(main_layout)
        layout.addLayout(bottom_panel)

        self.setLayout(layout)

    def create_left_form(self):
        form_layout = QVBoxLayout()
        font = QFont()
        font.setPointSize(12)

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

        # 分组添加内容
        add_label_input("试验时间：")
        add_label_input("用户：", QComboBox())
        add_label_input("吊点代号：", QComboBox())

        add_label_input("出厂编号：")
        add_label_input("型号规格：")
        add_label_input("工作荷载(N)：")
        add_label_input("位移方向：", QComboBox())
        add_label_input("总位移(mm)：")
        add_label_input("拔销值(N)：")

        add_label_input("操作员：", QComboBox())
        add_label_input("检验员：", QComboBox())

        # 状态项
        for label in [
            "位移起始点值", "位移终止点值", "实测位移值",
            "超载试验值(N)", "起始 - 终止时间", "超载试验保持时间",
            "恒定度", "载荷偏差度", "测试结果"
        ]:
            add_label_input(label)

        return form_layout


    def create_chart(self):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("载荷-位移性能曲线", color='purple', size='14pt')
        self.plot_widget.setLabel('left', '载荷 (N)', **{'color': '#000', 'font-size': '12pt'})
        self.plot_widget.setLabel('bottom', '位移 (mm)', **{'color': '#000', 'font-size': '12pt'})
        self.plot_widget.showGrid(x=True, y=True)

        # 示例数据
        x = [0, 1, 2, 3, 4, 5]
        y = [0, 10, 5, 20, 15, 25]
        self.plot_widget.plot(x, y, pen=pg.mkPen(color='b', width=2), symbol='o')
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_moved)

    def on_mouse_moved(self, evt):
        # TODO: 搞清楚下面那三个是要显示什么
        pos = evt
        mouse_point = self.plot_widget.getPlotItem().vb.mapSceneToView(pos)
        x = mouse_point.x()
        y = mouse_point.y()
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
