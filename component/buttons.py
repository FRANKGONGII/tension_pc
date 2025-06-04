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
    def __init__(self, parent=None):
        super().__init__("操作菜单", parent)
        self.setCursor(Qt.PointingHandCursor)
        self._create_menu()

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

    def _on_menu_clicked(self, text):
        """菜单项点击事件处理"""
        print(f"菜单项被点击: {text}")
        # 这里可以发射信号或调用回调函数
        # 实际应用中可以将此信号连接到主窗口的槽函数