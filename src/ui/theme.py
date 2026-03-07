"""
主题样式模块

提供简洁的浅色主题。
"""

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk


@dataclass
class ColorScheme:
    """颜色方案"""
    bg_primary: str
    bg_secondary: str
    bg_tertiary: str
    fg_primary: str
    fg_muted: str
    accent: str
    accent_hover: str
    success: str
    warning: str
    error: str
    border: str


# 浅色主题
LIGHT_THEME = ColorScheme(
    bg_primary="#ffffff",
    bg_secondary="#f0f0f0",
    bg_tertiary="#e0e0e0",
    fg_primary="#000000",
    fg_muted="#666666",
    accent="#0078d4",
    accent_hover="#106ebe",
    success="#4caf50",
    warning="#ff9800",
    error="#f44336",
    border="#c0c0c0"
)


class Theme:
    """主题管理器"""

    def __init__(self, dark_mode: bool = False):
        self._dark_mode = dark_mode
        self._colors = LIGHT_THEME

    @property
    def colors(self) -> ColorScheme:
        return self._colors

    @property
    def is_dark_mode(self) -> bool:
        return self._dark_mode

    def configure_styles(self, style: ttk.Style) -> None:
        """配置 ttk 样式 - 使用 clam 主题确保样式生效"""
        colors = self._colors

        # 强制使用 clam 主题
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # 通用样式
        style.configure(".",
                       background=colors.bg_primary,
                       foreground="#000000")

        # 框架
        style.configure("TFrame", background=colors.bg_primary)
        style.configure("Card.TFrame", background=colors.bg_secondary)

        # 标签 - 黑色文字
        style.configure("TLabel",
                       background=colors.bg_primary,
                       foreground="#000000",
                       font=("Microsoft YaHei UI", 10))

        style.configure("Card.TLabel",
                       background=colors.bg_secondary,
                       foreground="#000000")

        style.configure("Status.TLabel",
                       background=colors.bg_secondary,
                       foreground="#000000",
                       font=("Microsoft YaHei UI", 9))

        # 输入框
        style.configure("TEntry",
                       fieldbackground="#ffffff",
                       foreground="#000000")

        # 按钮 - 黑色文字
        style.configure("TButton",
                       background=colors.bg_tertiary,
                       foreground="#000000",
                       font=("Microsoft YaHei UI", 10),
                       padding=(10, 5))

        style.map("TButton",
                 background=[("active", colors.border)],
                 foreground=[("active", "#000000")])

        style.configure("Primary.TButton",
                       background=colors.accent,
                       foreground="#000000")

        style.map("Primary.TButton",
                 background=[("active", colors.accent_hover)],
                 foreground=[("active", "#000000")])

        style.configure("Danger.TButton",
                       background=colors.error,
                       foreground="#000000")

        style.map("Danger.TButton",
                 background=[("active", "#d32f2f")],
                 foreground=[("active", "#000000")])

        style.configure("Success.TButton",
                       background=colors.success,
                       foreground="#000000")

        # 复选框
        style.configure("TCheckbutton",
                       background=colors.bg_primary,
                       foreground="#000000")

        style.configure("Card.TCheckbutton",
                       background=colors.bg_secondary,
                       foreground="#000000")

        # 单选按钮
        style.configure("TRadiobutton",
                       background=colors.bg_primary,
                       foreground="#000000")

        style.configure("Card.TRadiobutton",
                       background=colors.bg_secondary,
                       foreground="#000000")

        # 下拉框
        style.configure("TCombobox",
                       fieldbackground="#ffffff",
                       foreground="#000000")

    def apply_to_root(self, root: tk.Tk) -> None:
        root.configure(bg="#ffffff")


# 全局实例
_theme: Theme = Theme()


def get_theme() -> Theme:
    return _theme


def set_dark_mode(enabled: bool) -> None:
    pass