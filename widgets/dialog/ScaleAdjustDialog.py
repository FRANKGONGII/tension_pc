from PyQt5.QtWidgets import (
    QDialog, QLabel, QPushButton, QDoubleSpinBox, QFrame,
    QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import Qt

from utils.config_manager import load_config, save_config


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

        # 执行缩放区域按钮
        self.btn_scale = QPushButton("执行缩放")
        self.btn_cancel = QPushButton("取消")
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_scale)
        button_layout.addWidget(self.btn_cancel)

        # 横线分隔
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        # 超载试验系数区域（底部）
        self.overload_spin = QDoubleSpinBox()
        self.overload_spin.setRange(1.0, 5.0)
        self.overload_spin.setSingleStep(0.1)
        self.overload_spin.setDecimals(1)
        self.overload_spin.setValue(2.5)
        self.overload_spin.setMinimumWidth(100)
        save_overload_btn = QPushButton("保存超载系数")
        save_overload_btn.clicked.connect(self._on_save_overload)
        overload_layout = QHBoxLayout()
        overload_layout.addWidget(QLabel("超载试验系数："))
        overload_layout.addWidget(self.overload_spin)
        overload_layout.addWidget(save_overload_btn)

        # 主布局：上方执行缩放区 + 横线 + 下方超载系数区
        layout = QVBoxLayout()
        layout.addWidget(self.label_current_range)
        layout.addWidget(self.label_current_constancy)
        layout.addWidget(self.label_target_constancy)
        layout.addLayout(button_layout)
        layout.addWidget(line)
        layout.addLayout(overload_layout)

        self.setLayout(layout)

        # 绑定关闭按钮
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_scale.clicked.connect(self.accept)

        self._load_overload_config()

    def _load_overload_config(self):
        """从配置加载超载系数并填充输入框"""
        cfg = load_config()
        self.overload_spin.setValue(float(cfg.get("overload_factor", 2.5)))

    def _on_save_overload(self):
        """保存超载试验系数"""
        from PyQt5.QtWidgets import QMessageBox
        val = self.overload_spin.value()
        save_config(overload_factor=val)
        QMessageBox.information(self, "提示", "超载系数已保存。")

    def set_data_stats(self, min_val, max_val, constancy):
        if min_val is not None and max_val is not None:
            self.label_current_range.setText(f"当前范围：{min_val:.2f} ~ {max_val:.2f}")
        else:
            self.label_current_range.setText("当前范围：")
        if constancy is not None:
            self.label_current_constancy.setText(f"恒定度：{constancy:.4f}")
        else:
            self.label_current_constancy.setText("恒定度：")
        self.label_target_constancy.setText("目标恒定度：6%")



