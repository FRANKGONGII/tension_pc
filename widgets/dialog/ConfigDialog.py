"""综合配置对话框：打印机名称、打印文件保存地址、串口端口"""
import os
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt

from utils.config_manager import load_config, save_config


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统配置")
        self.setMinimumWidth(420)
        self._init_ui()
        self._load_values()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        # 打印机名称
        self.printer_edit = QLineEdit()
        self.printer_edit.setPlaceholderText("例如：Canon iP1188 series")
        form.addRow("打印机名称：", self.printer_edit)

        # 打印文件保存地址
        save_layout = QHBoxLayout()
        self.save_path_edit = QLineEdit()
        self.save_path_edit.setPlaceholderText("留空则使用程序当前目录；将按年/月子目录自动归档")
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_save_path)
        save_layout.addWidget(self.save_path_edit)
        save_layout.addWidget(browse_btn)
        form.addRow("打印文件保存根目录：", save_layout)

        # 串口端口
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("例如：COM7")
        form.addRow("数据读取端口：", self.port_edit)

        layout.addLayout(form)

        tip = QLabel("提示：串口配置在下次开始测试时生效。")
        tip.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(tip)

        # 按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load_values(self):
        cfg = load_config()
        self.printer_edit.setText(cfg["printer_name"])
        self.save_path_edit.setText(cfg["print_save_path"])
        self.port_edit.setText(cfg["serial_port"])

    def _browse_save_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存目录", self.save_path_edit.text())
        if path:
            self.save_path_edit.setText(path)

    def _on_accept(self):
        printer = self.printer_edit.text().strip()
        save_path = self.save_path_edit.text().strip()
        port = self.port_edit.text().strip()
        if not printer:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "请输入打印机名称。")
            return
        save_config(printer_name=printer, print_save_path=save_path or None, serial_port=port or None)
        self.accept()
