from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFormLayout
)
from PyQt5.QtCore import Qt

class ScaleAdjustDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据缩放调整")
        self.setMinimumWidth(300)

        # 当前范围显示
        self.label_current_range = QLabel("当前范围：尚未加载")
        self.label_current_range.setAlignment(Qt.AlignCenter)

        # 当前恒定度显示
        self.label_current_constancy = QLabel("恒定度：尚未加载")
        self.label_current_constancy.setAlignment(Qt.AlignCenter)

        # 目标恒定度显示
        self.label_target_constancy = QLabel("目标恒定度：尚未加载")
        self.label_target_constancy.setAlignment(Qt.AlignCenter)

        # 缩放比率输入框
        self.input_ratio = QLineEdit()
        self.input_ratio.setPlaceholderText("例如：1.2 表示放大 20%")

        form_layout = QFormLayout()
        form_layout.addRow("缩放比率：", self.input_ratio)

        # 按钮
        self.btn_scale = QPushButton("执行缩放")
        self.btn_cancel = QPushButton("取消")
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_scale)
        button_layout.addWidget(self.btn_cancel)

        # 主布局
        layout = QVBoxLayout()
        layout.addWidget(self.label_current_range)
        layout.addWidget(self.label_current_constancy)
        layout.addWidget(self.label_current_constancy)
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 绑定关闭按钮
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_scale.clicked.connect(self.accept)

    def set_data_stats(self, min_val, max_val, constancy):
        self.label_current_range.setText(f"当前范围：{min_val:.2f} ~ {max_val:.2f}")
        self.label_current_constancy.setText(f"当前恒定度：{constancy:.4f}")
        self.label_target_constancy.setText("目标恒定度：6%")


    def get_scale_ratio(self):
        try:
            return float(self.input_ratio.text())
        except ValueError:
            return None
