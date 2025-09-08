import sys
import time
from random import random

import serial
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton
from PyQt5.QtCore import pyqtSignal, QObject

class SerialReader(QObject):
    data_received = pyqtSignal(str)

    def __init__(self, port='COM7', baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self._running = False
        self.thread = None

    def start(self):
        # if self._running:
        #     return  # 已经在运行，不重复启动

        try:
            print("here")
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self._running = True
            self.thread = threading.Thread(target=self.read_data)
            self.thread.daemon = True
            self.thread.start()
            # 这里替换测试或者实际调用
            # self.thread = threading.Thread(target=self.test)
            # self.thread.daemon = True
            # self.thread.start()
        except serial.SerialException as e:
            print(e)
            self.data_received.emit(f"[串口错误] {e}")

    def stop(self):
        self._running = False
        if self.ser and self.ser.is_open:
            self.ser.close()

    def read_data(self):
        print("status", self._running)
        buffer = ""
        while self._running:
            try:
                bytes_to_read = self.ser.in_waiting
                if bytes_to_read > 0:
                    raw_data = self.ser.read(bytes_to_read).decode(errors='ignore')
                    buffer += raw_data

                    while ':' in buffer:
                        start_index = buffer.find(':')
                        next_start_index = buffer.find(':', start_index + 1)

                        if next_start_index == -1:
                            break

                        one_record = buffer[start_index:next_start_index]
                        buffer = buffer[next_start_index:]

                        # ----------------- 解析报文 -----------------
                        try:
                            hex_str = one_record[1:]  # 去掉前导冒号
                            data_bytes = bytes.fromhex(hex_str)

                            # 这里根据你前面的结构，3个寄存器数据从第 7 字节开始
                            # [功能码02 10] [寄存器地址00 00] [寄存器数量00 03] [字节数06]
                            # => 实际数据部分从索引 7 开始，共 6 个字节（3*2）
                            if len(data_bytes) >= 13:  # 确保长度够
                                force = int.from_bytes(data_bytes[7:9], byteorder="big", signed=False)
                                distance = int.from_bytes(data_bytes[9:11], byteorder="big", signed=False)
                                status = int.from_bytes(data_bytes[11:13], byteorder="big", signed=False)

                                parsed = {
                                    "raw": one_record,
                                    "distance": distance,
                                    "force": force,
                                    "status": status,
                                }
                                print(parsed)
                                data = f"({force}, {distance})"
                                self.data_received.emit(data)
                            else:
                                print("无效报文:", one_record)

                        except Exception as e:
                            print(f"解析错误: {e}, 报文={one_record}")
                            self.data_received.emit(one_record)

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




