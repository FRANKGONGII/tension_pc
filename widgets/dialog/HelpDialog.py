"""帮助对话框：介绍各按钮的使用逻辑"""
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
from PyQt5.QtCore import Qt

HELP_CONTENT = """
<h3>恒力吊架性能测试系统 - 按钮使用说明</h3>

<p><b>操作菜单</b><br>
下拉菜单，包含：<br>
• 打印(M)：与工具栏「打印」功能相同，需先入库后可打印当前记录报表<br>
• 打印预览(N)：预留功能<br>
• 配置选项：设置打印机名称、打印文件保存根目录、数据读取串口端口</p>

<p><b>算法1</b><br>
切换到载荷-位移曲线图表界面，进行测试数据采集与显示。点击后可开始/结束测试。</p>

<p><b>算法2</b><br>
预留算法视图，当前已禁用。</p>

<p><b>测试入库</b><br>
将当前测试数据（表单 + 位移/力坐标点）保存到数据库。需先完成测试（点击「开始」并采集数据）后再入库，且不能重复入库。</p>

<p><b>数据编辑</b><br>
弹出数据缩放调整对话框，用于调整恒定度相关参数。需先完成一次测试后才能使用。</p>

<p><b>打印</b><br>
生成 Word 报表并打印。需先「测试入库」后进行，且该记录需有有效测试数据。</p>

<p><b>坐标轴范围</b><br>
设置图表 X 轴（载荷）和 Y 轴（位移）的显示范围，可选用预设或自定义。</p>

<p><b>查询历史</b><br>
显示/隐藏右侧查询栏，可按试验日期、用户、出厂编号查询历史记录，支持导入和打开文件目录。</p>
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("帮助")
        self.setMinimumSize(560, 700)
        self.resize(600, 560)
        layout = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setHtml(HELP_CONTENT)
        layout.addWidget(self.text)
        btn = QPushButton("确定")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
