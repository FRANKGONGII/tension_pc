import os
import sys


APP_NAME = "tension_pc"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_root() -> str:
    """
    Read-only bundle root.
    - source run: project root (directory containing main.py)
    - PyInstaller onefile/onedir: sys._MEIPASS
    """
    if is_frozen():
        return str(getattr(sys, "_MEIPASS"))
    # utils/paths.py -> utils -> project root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def exe_dir() -> str:
    """
    Directory of the running executable (or project root when running from source).
    """
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def data_dir() -> str:
    """
    Writable application data directory.
    Prefer LOCALAPPDATA to avoid permission issues under Program Files.
    Fallback to exe_dir when env is unavailable.
    """
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    root = os.path.join(base, APP_NAME) if base else exe_dir()
    os.makedirs(root, exist_ok=True)
    return root


def resource_path(relative_path: str) -> str:
    return os.path.join(bundle_root(), relative_path)


def data_path(relative_path: str) -> str:
    path = os.path.join(data_dir(), relative_path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path

