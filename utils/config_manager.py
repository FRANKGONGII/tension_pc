"""配置管理：打印机名称、打印文件保存地址、串口端口、combobox 历史等"""
import os
import json
import copy
from datetime import datetime

CONFIG_FILENAME = "app_config.json"
DEFAULT_PRINTER = "Canon iP1188 series"
DEFAULT_SAVE_PATH = ""
DEFAULT_SERIAL_PORT = "COM7"
DEFAULT_OVERLOAD_FACTOR = 2.5
# 执行缩放校准用的目标恒定度（百分数，如 5.0 表示 5%）
DEFAULT_TARGET_CONSTANCY_PERCENT = 5.0
# 位移滞回 δ（mm）：0 或未设置表示自动 max(1.0, 0.5% * 工作位移)
DEFAULT_SCALE_HYSTERESIS_MM = 0.0

# 与 test_widget_1 中带 save_history 的 combobox 键一致；仅启动时作缺省合并，不主动写盘
DEFAULT_COMBOBOX_HISTORY = {
    "用户": [],
    "吊点代号": [],
}


def _config_path():
    """配置文件路径（与主程序同目录）"""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, CONFIG_FILENAME)


def _default_combobox_history():
    return {k: list(v) for k, v in DEFAULT_COMBOBOX_HISTORY.items()}


def _read_raw_config():
    """读取磁盘上的完整 JSON；无文件或损坏时返回空 dict。启动过程不修改文件。"""
    path = _config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _compute_overload_factor(disk):
    if "overload_factor" in disk:
        try:
            return float(disk["overload_factor"])
        except (TypeError, ValueError):
            pass
    if "overload_factor_min" in disk and "overload_factor_max" in disk:
        try:
            return (float(disk["overload_factor_min"]) + float(disk["overload_factor_max"])) / 2
        except (TypeError, ValueError):
            pass
    return DEFAULT_OVERLOAD_FACTOR


def load_config():
    """
    加载配置（内存合并：默认值 + 磁盘上的键）。
    返回 dict 含 combobox_history；不会在启动时改写 app_config.json。
    """
    disk = _read_raw_config()
    out = {
        "printer_name": DEFAULT_PRINTER,
        "print_save_path": DEFAULT_SAVE_PATH or os.getcwd(),
        "serial_port": DEFAULT_SERIAL_PORT,
        "overload_factor": DEFAULT_OVERLOAD_FACTOR,
        "target_constancy_percent": DEFAULT_TARGET_CONSTANCY_PERCENT,
        "scale_hysteresis_mm": DEFAULT_SCALE_HYSTERESIS_MM,
        "combobox_history": _default_combobox_history(),
    }

    for k, v in disk.items():
        if k == "combobox_history" and isinstance(v, dict):
            ch = out["combobox_history"]
            for hk, hv in v.items():
                if isinstance(hv, list):
                    ch[hk] = [str(x) for x in hv]
                elif hv is not None:
                    ch[hk] = [str(hv)]
        else:
            out[k] = v

    for k in DEFAULT_COMBOBOX_HISTORY:
        if k not in out["combobox_history"]:
            out["combobox_history"][k] = list(DEFAULT_COMBOBOX_HISTORY[k])

    out["overload_factor"] = _compute_overload_factor(disk)
    try:
        out["target_constancy_percent"] = float(
            out.get("target_constancy_percent", DEFAULT_TARGET_CONSTANCY_PERCENT)
        )
    except (TypeError, ValueError):
        out["target_constancy_percent"] = DEFAULT_TARGET_CONSTANCY_PERCENT
    try:
        out["scale_hysteresis_mm"] = float(
            out.get("scale_hysteresis_mm", DEFAULT_SCALE_HYSTERESIS_MM)
        )
    except (TypeError, ValueError):
        out["scale_hysteresis_mm"] = DEFAULT_SCALE_HYSTERESIS_MM

    if disk.get("printer_name") is not None:
        out["printer_name"] = str(disk["printer_name"])
    psp = disk.get("print_save_path")
    if psp is not None and str(psp).strip():
        out["print_save_path"] = str(psp).strip()
    else:
        out["print_save_path"] = out["print_save_path"] or os.getcwd()
    if disk.get("serial_port") is not None:
        out["serial_port"] = str(disk["serial_port"]).strip() or DEFAULT_SERIAL_PORT

    return out


def save_config(printer_name=None, print_save_path=None, serial_port=None,
                overload_factor=None, target_constancy_percent=None,
                scale_hysteresis_mm=None):
    """
    保存配置：在磁盘当前内容基础上只改传入字段，保留 combobox_history 及未知扩展键。
    """
    path = _config_path()
    cfg = load_config()
    if printer_name is not None:
        cfg["printer_name"] = str(printer_name).strip()
    if print_save_path is not None:
        cfg["print_save_path"] = str(print_save_path).strip() or os.getcwd()
    if serial_port is not None:
        cfg["serial_port"] = str(serial_port).strip() or DEFAULT_SERIAL_PORT
    if overload_factor is not None:
        cfg["overload_factor"] = float(overload_factor)
    if target_constancy_percent is not None:
        cfg["target_constancy_percent"] = float(target_constancy_percent)
    if scale_hysteresis_mm is not None:
        cfg["scale_hysteresis_mm"] = float(scale_hysteresis_mm)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_printer_name():
    return load_config()["printer_name"]


def get_print_save_path():
    p = load_config()["print_save_path"]
    return p if p else os.getcwd()


def get_print_save_dir_for_today():
    """返回今日打印文件保存目录：根目录/年份/月份/，自动创建不存在的目录"""
    root = get_print_save_path()
    now = datetime.now()
    year_dir = str(now.year)
    month_dir = f"{now.month:02d}"
    save_dir = os.path.join(root, year_dir, month_dir)
    os.makedirs(save_dir, exist_ok=True)
    return save_dir


def get_serial_port():
    return load_config()["serial_port"]


def get_overload_factor():
    return load_config()["overload_factor"]


def get_target_constancy_percent():
    """目标恒定度（百分数，如 5.0 表示 5%）"""
    return float(load_config()["target_constancy_percent"])


def get_scale_hysteresis_delta_mm(working_displacement_mm=None):
    """
    恒定度缩放位移滞回 δ（mm）。
    若配置 scale_hysteresis_mm > 0 则使用该值；否则 max(1.0, 0.5% * 工作位移)，无工作位移时用 1.0。
    """
    cfg = load_config()
    v = cfg.get("scale_hysteresis_mm", DEFAULT_SCALE_HYSTERESIS_MM)
    try:
        fv = float(v)
    except (TypeError, ValueError):
        fv = DEFAULT_SCALE_HYSTERESIS_MM
    if fv > 0:
        return fv
    if working_displacement_mm is not None:
        try:
            wd = float(working_displacement_mm)
        except (TypeError, ValueError):
            wd = 0.0
        if wd > 0:
            return max(1.0, 0.005 * wd)
    return 1.0


def get_combobox_history(key):
    """获取某个 combobox 的历史输入列表"""
    history = load_config().get("combobox_history") or {}
    if not isinstance(history, dict):
        return []
    raw = history.get(key, [])
    return list(raw) if isinstance(raw, list) else []


def save_combobox_item(key, value):
    """将 combobox 值追加到历史记录末尾（已存在则移到末尾，保证最后一项是最近使用的）"""
    value = str(value).strip()
    if not value:
        return
    path = _config_path()
    try:
        cfg = load_config()
        history = cfg.setdefault("combobox_history", _default_combobox_history())
        if not isinstance(history, dict):
            history = _default_combobox_history()
            cfg["combobox_history"] = history
        items = list(history.get(key, []))
        if value in items:
            items.remove(value)
        items.append(value)
        history[key] = items
        cfg["combobox_history"] = history
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
