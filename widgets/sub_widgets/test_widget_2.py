from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QComboBox, QHBoxLayout, QVBoxLayout,
    QGridLayout, QPushButton
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph as pg



class TestViewWidget_2(QWidget):
    mouse_data_changed = pyqtSignal(object)
    show_buttons = False

    def __init__(self):
        super().__init__()
        # 图表组件
        # 下面两个是控制开始测试和结束的显示
        show_buttons = True
        self.if_start = True
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

        # # 注册监听器
        # ToolBarWidget.visibility_changed.connect(self.setVisible)
        form_layout.addLayout(button_layout)

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
            "恒定度", "载荷偏移度", "测试结果"
        ]:
            add_label_input(label)

        return form_layout

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
            # print("开始按钮被点击")
            self.btn1.setEnabled(False)
            self.btn2.setEnabled(True)


    def on_end_clicked(self):
        if self.btn2.isEnabled():
            # 逻辑处理
            # print("结束按钮被点击")
            self.btn2.setEnabled(False)
            self.btn1.setEnabled(True)
            # 后续如需重新开始，也可以再启用 start


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
