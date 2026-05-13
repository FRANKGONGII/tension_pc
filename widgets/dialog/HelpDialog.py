"""帮助对话框：介绍各按钮的使用逻辑"""
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
from PyQt5.QtCore import Qt

HELP_CONTENT = """
<h3>恒力吊架性能测试系统 · 使用说明</h3>

<p><b>操作菜单</b><br>
• <b>打印(M)</b>（Ctrl+P）：与工具栏「打印」相同。须先对当前记录执行「测试入库」，且该记录下存在有效曲线数据。<br>
• <b>打印预览(N)</b>（Ctrl+R）：菜单预留项，当前版本点击无单独预览逻辑。<br>
• <b>配置选项</b>：打印机名称、打印文件保存根目录（Word 与日志等按此根目录归档）、数据读取串口、恒定度缩放用位移滞回 δ（mm）。修改串口并保存后，程序会重新打开串口。</p>

<p><b>恒力吊架测试算法</b><br>
切换到主测试界面：左侧为试验表单与流程按钮，右侧为实时载荷–位移曲线。第二套「算法」视图已在程序中关闭，当前仅此一种。</p>

<p><b>测试入库</b><br>
将当前表单与全部曲线采样点写入本地 SQLite。须在结束测试流程后、且本轮尚未入库时使用；若已入库，请先「清空面板」再测。测试进行中「测试入库」不可用。</p>

<p><b>数据编辑</b><br>
在非测试状态下打开「数据缩放调整」：查看当前力值范围与恒定度、设置目标恒定度(%)并执行缩放，或单独保存超载试验系数。若当前无曲线点则无法执行缩放。测试进行中不可用。</p>

<p><b>打印</b><br>
根据最近一次成功入库的记录生成 Word 报表并尝试通过本机 Word 打印（Windows）。无入库记录、或记录中 x/y 点为空时会提示无法打印。</p>

<p><b>查询历史</b><br>
显示或隐藏右侧查询栏。可按年份（范围由配置起始年至明年）、试验日期/用户/出厂编号检索；表格中可打开报表所在目录，或使用「导入」将历史记录加载到主界面（导入后视为已入库场景，具体以界面状态为准）。</p>

<p><b>清空面板</b><br>
清除当前曲线与表单、重置本轮状态，便于开始新试验。当前打印所关联的记录 ID 也会被清除。</p>

<p><b>帮助</b><br>
本对话框。更完整的安装路径、配置项与数据文件位置见项目根目录 <b>README.md</b>。</p>
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
