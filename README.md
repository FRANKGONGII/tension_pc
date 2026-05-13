# 恒力吊架性能测试系统（tension_pc）

桌面端应用程序，用于恒力吊架试验的**串口数据采集**、**载荷–位移实时曲线**、**指标计算**、**SQLite 存储**与 **Word 报表生成/打印**。

---

## 技术栈

| 用途 | 主要依赖 |
|------|----------|
| 界面 | PyQt5 |
| 实时曲线 | pyqtgraph |
| 静态报表配图 | matplotlib |
| Word 报表 | python-docx |
| 串口 | pyserial |
| 本地数据库 | SQLite（标准库 `sqlite3`） |

---

## 运行环境与依赖安装

- **Python**：建议 3.8+（与当前依赖版本相容即可）。
- **安装依赖**（在项目根目录执行）：

  ```bash
  pip install -r requirements.txt
  ```

- **GUI 必需但未列入 `requirements.txt`**：请单独安装 **PyQt5**（例如 `pip install PyQt5`），否则无法启动界面。
- **Windows 打印**：`utils/print_doc.py` 通过 **win32com** 调用本机 Word 打印，需安装 **pywin32**。
- `requirements.txt` 中的 `boto` 在业务代码中已注释未使用，可按需省略。

---

## 启动方式

在项目根目录执行：

```bash
python main.py
```

`main.py` 会初始化字体（`utils/style.py`）并创建主窗口 `app.py` 中的 `MainWindow`。

---

## 数据与配置文件位置（重要）

可写数据目录优先为 **`%LOCALAPPDATA%\tension_pc`**（Windows），避免在 `Program Files` 等目录无写权限。

| 文件 | 说明 |
|------|------|
| `form_data.db` | SQLite 数据库：试验明细表 `test_detail`、曲线表 `test_data` |
| `app_config.json` | 打印机、打印保存根目录、串口、缩放/查询等配置 |
| `png.png` | 高分辨率曲线图，供 Word 嵌入（与数据目录同路径逻辑，见 `utils/paths.data_path`） |

静态资源（样式表、图标等）来自程序包目录；PyInstaller 打包时使用 `bundle_root()` 解析。

---

## 配置文件 `app_config.json` 说明

由「操作菜单 → 配置选项」保存，或由 `utils/config_manager.py` 读写。主要键名：

| 键 | 含义 |
|----|------|
| `printer_name` | 默认打印机名称 |
| `print_save_path` | Word 与日志等使用的**根目录**；打印文件会按 **年/月** 子目录归档（见 `get_print_save_dir_for_today`） |
| `serial_port` | 串口名，如 `COM7` |
| `overload_factor` | 超载试验系数（数据缩放对话框中可保存） |
| `target_constancy_percent` | 目标恒定度（百分数，如 `5.0` 表示 5%） |
| `scale_hysteresis_mm` | 恒定度缩放位移滞回 δ（mm）；`0` 表示按工作位移自动：`max(1.0, 0.5% × 工作位移)` |
| `query_year_start` | 历史查询侧栏「查询年份」下拉框起始年 |
| `combobox_history` | 「用户」「吊点代号」等下拉历史 |

修改串口并确定后，主窗口会对 `SerialReader` 调用 `reopen_serial()`，在下次读串口前生效；界面提示「下次开始测试时生效」指逻辑上与新打开的端口一致。

---

## 主界面结构

- **顶部工具栏**（`widgets/toolbar.py`）：操作菜单、算法视图切换、测试入库、打印、查询历史、清空面板、数据编辑、帮助，以及右侧实时时钟。
- **中部**：`QStackedLayout`——当前实际使用为「恒力吊架性能测试系统」占位页与 **主测试视图**（`TestViewWidget_1`）。原「算法 2」已在代码中注释关闭。
- **底部**：`DataDisplayWidget`——实时显示与力/位移相关的监测数值（由测试视图 `received_data_changed` 驱动）。
- **右侧可停靠**：「查询栏」`SearchHistoryWidget`，默认隐藏，通过「查询历史」切换显示。

---

## 工具栏与操作菜单

- **恒力吊架测试算法**：切换到主曲线/表单界面（当前仅此一种算法入口）。
- **测试入库**：将当前表单 + 位移/力曲线点写入数据库。需已有有效 **x/y 点**；**测试中禁用**；同一轮测试成功入库后会标记为已保存并再次禁用，防止重复入库。
- **打印**：根据**当前入库记录 ID** 生成 Word 并尝试打印。未入库或该记录无曲线数据时会提示无法打印。
- **查询历史**：显示/隐藏右侧 Dock；打开时会触发一次检索刷新。
- **清空面板**：清空曲线与表单、重置与本轮测试相关的内部状态，并将测试按钮恢复为适合新试验的状态；当前处理记录 ID 会重置。
- **数据编辑**：在**非测试进行中**打开「数据缩放调整」对话框（见下）；若当前无坐标点则对话框缺少缩放对象。
- **操作菜单**
  - **打印(M)**：与工具栏「打印」相同（快捷键 Ctrl+P 已绑定到菜单项，需配合菜单使用）。
  - **打印预览(N)**：保留快捷键与菜单项，**当前无单独实现**（点击无业务响应）。
  - **配置选项**：打开 `ConfigDialog`（打印机、打印根目录、串口、缩放位移滞回 δ）。

程序内 **帮助** 按钮打开 `widgets/dialog/HelpDialog.py` 中的说明（与本文一致维护）。

---

## 测试视图工作流程（`widgets/sub_widgets/test_widget_1.py`）

1. **串口**：`SerialReader` 在启动时尝试打开配置端口并后台读线程解析报文；测试过程中将合法数据送入 `handle_data` 绘制曲线。
2. **按钮**（可见性由 `change_retest_visible` 等控制）：**记录初始值(去0)**、**开始**、**结束**——用于去零、正式采点起止与结束后的计算/导出。
3. **图表**：pyqtgraph 绘制；内部以 JSON 形式与数据库交互时，**displacement 存 y、force 存 x**（见 `DataManager.save_test_data` 字段命名与序列化）。
4. **显示比例**：部分设备/状态码会映射 `SCALE_MAP` 中的预设轴范围，否则使用 `DEFAULT_SCALE`。
5. **高分辨率图**：结束流程中会生成 matplotlib 静态图，写入数据目录下的 `png.png`，供 `print_doc` 嵌入 Word。
6. **测试状态与主窗口**：`test_started` / `test_ended` 信号用于在测试进行中禁用「测试入库」和「数据编辑」。

主窗口 `MainWindow` 在试验结束后启用「测试入库」；入库成功后会清除本轮「数据编辑/执行缩放」相关的临时参数，避免下一轮误用。

---

## 历史查询与导入（`search_history_widget.py`）

- **查询方式**：试验日期（按年）、用户（年 + 关键字）、出厂编号（年 + 关键字）。
- **查询年份**：范围由配置 `query_year_start` 至**当年 +1**。
- **表格**：试验日期、用户、出厂编号、**打开目录**（若有打印生成的文件路径则打开所在文件夹）、**导入**。
- **导入**：从数据库载入明细与曲线；可能重绘图表并设置 `now_handle_data_id`；导入记录视为已入库场景，会限制再次测试入库直到用户清空面板等操作。

---

## 数据缩放与「数据编辑」

「数据编辑」打开 `ScaleAdjustDialog`（`widgets/dialog/ScaleAdjustDialog.py`）：

- 显示当前力值范围与**恒定度**统计；
- 设置**目标恒定度(%)**，可写入配置；
- **执行缩放**：确认后由主窗口 `try_scaling` 依据**工作载荷**与目标比例启用曲线上的缩放重映射（恒定力业务逻辑，见 `app.py` 与 `test_widget_1` 中 `_scale_remap_*`）；
- 可单独保存**超载试验系数**到配置。

配置中的 **缩放位移滞回 δ** 在「系统配置」对话框中设置（与恒定度缩放分段逻辑相关）。

---

## 打印与 Word 生成（`utils/print_doc.py`）

- 使用 **python-docx** 组装《恒力吊架性能试验记录》类文档，并嵌入 `png.png`。
- 输出文件名形如：`恒力吊架性能试验记录-<出厂编号><时间后缀>.docx`（见源码中 `filename` 构造）。
- 打印：Windows 下 Dispatch Word 应用；用户取消时会抛出 `PrintCancelled`，界面不弹成功提示。

---

## 日志

`utils/system_logger.py`：日志写入**打印保存根目录**下的 `System_Log_<年份>.log`（与配置中的 `print_save_path` 一致）。

---

## 目录结构（源码）

| 路径 | 说明 |
|------|------|
| `main.py` | 程序入口 |
| `app.py` | 主窗口、入库/打印/配置/清空面板等总控 |
| `widgets/` | 工具栏、数据显示、测试视图、历史查询、对话框 |
| `utils/` | 串口、数据库、配置、计算、打印、路径、日志 |
| `PO/input_data.py` | 表单字段与 `inputManager` |
| `component/buttons.py` | 菜单按钮、算法切换按钮 |
| `resources/styles.qss` | Qt 样式表 |

---

## 常见问题

1. **无法打印**：请先「测试入库」，并确保该记录已成功保存曲线点；打印机与 Word 可用（Windows + pywin32）。
2. **串口无数据**：检查配置端口、线缆及是否被其他程序占用；查看日志或控制台中的串口错误提示。
3. **缺少 PyQt5**：安装 `PyQt5` 后再运行。
4. **`requirements.txt` 与运行时不一致**：以本文「运行环境」为准补全 PyQt5 / pywin32。

---

*文档版本与当前仓库代码同步生成；若行为以源码为准。*

Set-Location "d:\lcynju\Documents\Projects\2025-huitong\tension_pc"
python -m PyInstaller main.spec --noconfirm