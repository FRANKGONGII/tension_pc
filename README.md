# tension_pc
# 项目定位
- GUI 桌面应用，用于“恒力吊架性能测试系统”的数据采集、实时曲线展示、指标计算与报表打印
- 技术栈以 PyQt5 + pyqtgraph 做交互与实时绘图，matplotlib 用于生成高分辨率静态图供 Word 报表嵌入
- 使用 SQLite 管理测试明细与曲线数据；支持历史查询与数据回灌到曲线
# 目录结构
- 核心入口
  - main.py 程序入口，初始化字体并启动主窗口
  - app.py 主窗体 MainWindow，组装 Toolbar、数据展示、两套测试视图、搜索侧栏
- 业务模块
  - widgets
    - toolbar.py 顶部工具栏：切图、坐标轴范围对话框、入库/编辑/历史/打印等
    - data_display.py 实时数据显示（mm、kg、N）
    - header.py , footer.py 页眉页脚部件
    - dialog/ScaleAdjustDialog.py 量程/居中调整对话框（被主窗体调用）
    - sub_widgets
      - test_widget_1.py 主测试视图：实时曲线、表单输入、数据采集、指标计算、生成高分辨率图
      - test_widget_2.py 第二测试视图（示例/备用）
      - search_history_widget.py 历史查询侧栏（含数据导入到曲线）
  - utils
    - serial_reader.py 串口/测试数据产生与信号分发
    - data_manager.py SQLite 建表、保存、查询
    - calculate.py 指标计算（恒定度、载荷偏差度等）
    - print_doc.py 生成 Word 报表并打印，嵌入静态曲线图
    - style.py 字体初始化为微软雅黑
  - PO/input_data.py 输入管理器（表单字段映射、值设置/获取）
- 资源与文档
  - resources/styles.qss 全局样式（控件、输入框、标签等）
  - 多份历史 Word 报表样例：“恒力吊架性能试验记录X.docx”
- 其他
  - requirements.txt 依赖列表（见“依赖与环境”）
  - README.md 目前仅标题，需要完善
  - .gitignore

# 运行入口与 UI 组装
- 入口：执行 main.py 的 main()，创建 QApplication，设置字体 style.py:init_fonts ，实例化并展示 MainWindow
- 主窗体：
  - 顶部工具栏 toolbar.py 支持“重新测试、坐标轴范围、历史查询、打印”等，发射信号供主窗体与图表响应
  - 中部使用 QStackedLayout 切换两套图表视图 app.py:switch_chart_1/2
  - 右侧可显示历史查询侧栏 SearchHistoryWidget
  - 底部为实时数据展示 DataDisplayWidget
数据采集与实时绘图

- 数据产生与分发
  - SerialReader 可读串口 COM7 也可运行测试线程 start_test_thread ，以 pyqtSignal 发送字符串报文“(x, y)”
  - 测试模式默认启动于“开始”按钮点击后 test_widget_1:on_start_clicked
- 主视图 1（实时曲线）
  - 初始化与曲线创建 create_chart ，使用 pyqtgraph 绘制点、显示网格、反转 Y 轴、设置 X/Y 范围
  - 鼠标移动信号用于更新右下实时数据 on_mouse_moved → 主窗体转发至 DataDisplayWidget.update_data
  - 接收与处理数据 handle_data ：支持“x 去零”“固定首点 y=100”“自动高亮每 N 点并保存静态图”
- 高分辨率静态图生成（供报表嵌入）
  - save_high_res_chart 使用 matplotlib 复绘、标签与上下 5%“工作载荷”辅助线、反转 y 轴（见 ax.invert_yaxis()），保存到 resources/png.png
数据库与历史查询

- SQLite 表结构与操作
  - 建表与保存 DataManager.init_db/save_detail/save_test_data 管理 test_detail 与 test_data
  - 查询封装 queryById/queryTestDataByFormId/queryByYear/ByYearAndUser/ByYearAndFactoryNum
- 历史查询侧栏
  - 搜索并填表格 handle_search ，文件链接列支持打开历史 Word 文件
  - “导入”按钮可将数据库明细与曲线数据回灌到主测试视图 on_import_clicked （注意 test_widget_1 的 rewrite_chart 目前注释掉）
报表与打印

- 生成 Word 报表与打印
  - print_doc 使用 python-docx 构建多段标题与多表格布局，将静态图 png.png 嵌入，再调用 win32com 打印（Windows）
  - 保存文件命名为“恒力吊架性能试验记录 <id>.docx”，根目录已有大量样例文档供历史查询使用</id>
依赖与环境

- 列表见 requirements.txt ：pypandoc、python-docx、pyserial、boto、matplotlib、pyqtgraph、sympy
- 实际代码使用 PyQt5，但当前 requirements 未列出 PyQt5；运行 GUI 需安装 PyQt5
- Windows 打印使用 win32com；通常需安装 pywin32 才能正常调用
- 综述：
  - 必要：PyQt5、pyqtgraph、matplotlib、python-docx、pypandoc、pyserial、sqlite3（标准库）、sympy
  - 可选/特别：pywin32（打印）、boto（app.py 中导入但未见实际使用）
典型工作流

- 启动程序：python main.py
- 在主测试视图：
  - 输入基本信息（用户、吊点代号、工作载荷、工作位移等）
  - 点击“重新测试”进入测试模式，实时曲线显示；可记录“初始值（去0）”“拔销值”
  - 系统每隔 N 点自动高亮并保存静态图；结束后写入计算指标（恒定度、总位移、位移起止/实测、载荷偏差度等）
- 数据入库与打印：
  - 顶部“测试入库”保存至 SQLite；菜单“打印(M)”生成并打印 Word 报表
- 历史查询：
  - 右侧侧栏按年/用户/出厂编号检索；可点击“查看文件”或“导入”回灌到曲线视图