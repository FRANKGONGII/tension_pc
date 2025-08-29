import sys
import time
from random import random

import serial
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton
from PyQt5.QtCore import pyqtSignal, QObject

class SerialReader(QObject):
    data_received = pyqtSignal(str)

    def __init__(self, port='COM1', baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self._running = False
        self.thread = None

    def start(self):
        if self._running:
            return  # 已经在运行，不重复启动

        try:
            # self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self._running = True
            # 这里替换测试或者实际调用
            self.thread = threading.Thread(target=self.test)
            self.thread.daemon = True
            self.thread.start()
        except serial.SerialException as e:
            self.data_received.emit(f"[串口错误] {e}")

    def stop(self):
        self._running = False
        if self.ser and self.ser.is_open:
            self.ser.close()

    def read_data(self):
        print("status", )
        while self._running:
            try:
                if self.ser.in_waiting:
                    data = self.ser.readline().decode(errors='ignore').strip()
                    self.data_received.emit(data)
            except Exception as e:
                self.data_received.emit(f"[读取错误] {e}")
                break


    # 注意这里生成的是以55为中心的随机数
    def test(self):
        from random import uniform
        y = 200
        for i in range(100):
            if i <= 50:
                y += 1
                x = uniform(55, 60)
            else:
                y -= 1
                x = uniform(50, 55)  # 生成 [50, 60) 范围内的随机小数
            data = f"({x}, {y})"
            self.data_received.emit(data)
            time.sleep(0.2)
        self._running = False