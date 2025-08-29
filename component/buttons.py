import os

from PyQt5.QtWidgets import QPushButton, QMenu, QAction
from PyQt5.QtCore import Qt,pyqtSignal

# 图表显示button1
class ChartButton1(QPushButton):
    def __init__(self, text="算法1"):
        super().__init__(text)

# 图表显示button2
class ChartButton2(QPushButton):
    def __init__(self, text="算法2"):
        super().__init__(text)


# 菜单button
class MenuButton(QPushButton):
    # 用于打印的信号量
    print_doc_signal = pyqtSignal(int) 
    
    def __init__(self, parent=None):
        super().__init__("操作菜单", parent)
        self.setCursor(Qt.PointingHandCursor)
        self._create_menu()
        # 当前处理的数据表ID
        self._now_handle_data_id = - 1

    def _create_menu(self):
        self.menu = QMenu(self)

        # 菜单项分组配置
        menu_structure = [
            # (分组名称, 菜单项列表)
            ("测试", [
                ("重新测试(I)", "Ctrl+N"),
                ("编辑数据(V)", "Ctrl+E"),
                ("数据入库(L)", "Ctrl+S")
            ]),
            ("打印", [
                ("打印(M)", "Ctrl+P"),
                ("打印预览(N)", "Ctrl+R")
            ]),
            ("设置", [
                ("打印设置(O)", "", True),  # 有子菜单
                ("实际量程选择(P)", "", True),
                ("操作选择(Q)", "", True)
            ]),
            ("工具", [
                ("曲线自动居中(R)", ""),
                ("自动零点参考(S)", ""),
                ("设为零点(T)", ""),
                ("绝对力值(U)", "")
            ]),
            ("文件", [
                ("保存到磁盘(V)", "Ctrl+H"),
                ("从文件卷入(W)", "Ctrl+L"),
                ("历史查询(X)", "Ctrl+Q")
            ]),
            ("系统", [
                ("调试模式(Y)", ""),
                ("退出(Z)", "Ctrl+E")
            ])
        ]

        for group_name, items in menu_structure:
            if group_name:
                self.menu.addSeparator()

            for item in items:
                text, shortcut, *rest = item
                has_submenu = rest[0] if rest else False

                if has_submenu:
                    submenu = QMenu(text, self.menu)
                    submenu.addAction("子菜单项1")
                    submenu.addAction("子菜单项2")

                    menu_action = QAction(text, self.menu)
                    menu_action.setMenu(submenu)
                    self.menu.addAction(menu_action)
                else:
                    action = QAction(text, self.menu)
                    if shortcut:
                        action.setShortcut(shortcut)
                    action.triggered.connect(lambda _, x=text: self._on_menu_clicked(x))
                    self.menu.addAction(action)

        self.setMenu(self.menu)
        
    def set_now_handle_data_id(self, data_id):
        self._now_handle_data_id = data_id


    def _on_menu_clicked(self, text):
        print(f"菜单项被点击: {text}")
        if text == "打印(M)":
            print(os.getcwd())
            # 发射打印信号量
            self.print_doc_signal.emit(self._now_handle_data_id) 