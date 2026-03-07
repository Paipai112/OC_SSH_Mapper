"""
状态面板组件

显示连接状态和操作按钮。
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from src.models.connection_state import ConnectionStatus, ConnectionState
from src.ui.theme import get_theme
from src.utils.logger import get_logger

logger = get_logger()


class StatusPanel(ttk.Frame):
    """
    状态面板组件

    功能:
    - 显示连接状态
    - 操作按钮
    - 状态图标
    """

    def __init__(self, parent, on_start: Optional[Callable] = None, on_stop: Optional[Callable] = None, on_open_browser: Optional[Callable] = None):
        """
        初始化状态面板

        Args:
            parent: 父组件
            on_start: 启动回调
            on_stop: 停止回调
            on_open_browser: 打开浏览器回调
        """
        super().__init__(parent)
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_open_browser = on_open_browser
        self._theme = get_theme()
        self._build_ui()

    def _build_ui(self) -> None:
        """构建 UI"""
        self.configure(style="Card.TFrame", padding=15)

        # 状态区域
        status_frame = ttk.Frame(self, style="Card.TFrame")
        status_frame.pack(fill="x", pady=(0, 10))

        # 状态图标（用文字代替）
        self.status_icon = ttk.Label(status_frame, text="○", font=("Segoe UI", 16), style="Card.TLabel")
        self.status_icon.pack(side="left", padx=(0, 10))

        # 状态文本
        self.status_label = ttk.Label(status_frame, text="未连接", style="Status.TLabel")
        self.status_label.pack(side="left")

        # 连接时间
        self.uptime_label = ttk.Label(status_frame, text="", style="Status.TLabel")
        self.uptime_label.pack(side="right")

        # 操作按钮行1
        btn_frame1 = ttk.Frame(self, style="Card.TFrame")
        btn_frame1.pack(fill="x")

        self.start_btn = ttk.Button(
            btn_frame1, text="启动连接", style="Primary.TButton",
            command=self._on_start_click
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.stop_btn = ttk.Button(
            btn_frame1, text="断开连接", style="Danger.TButton",
            command=self._on_stop_click, state="disabled"
        )
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # 操作按钮行2 - 打开OpenClaw
        btn_frame2 = ttk.Frame(self, style="Card.TFrame")
        btn_frame2.pack(fill="x", pady=(5, 0))

        self.open_btn = ttk.Button(
            btn_frame2, text="打开 OpenClaw", style="TButton",
            command=self._on_open_click, state="disabled"
        )
        self.open_btn.pack(fill="x")

        # 日志区域
        self.log_text = tk.Text(self, height=6, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, pady=(10, 0))

        # 配置文本框样式
        colors = self._theme.colors
        self.log_text.configure(
            bg=colors.bg_tertiary,
            fg=colors.fg_primary,
            font=("Consolas", 9),
            relief="flat",
            padx=5,
            pady=5,
            insertbackground=colors.fg_primary
        )

    def _on_start_click(self) -> None:
        """启动按钮点击"""
        if self._on_start:
            # 立即更新按钮状态
            self.start_btn.config(state="disabled")
            self._on_start()

    def _on_stop_click(self) -> None:
        """停止按钮点击"""
        if self._on_stop:
            # 立即更新按钮状态
            self.stop_btn.config(state="disabled")
            self._on_stop()

    def _on_open_click(self) -> None:
        """打开浏览器按钮点击"""
        if self._on_open_browser:
            self._on_open_browser()

    def update_status(self, status: ConnectionStatus) -> None:
        """
        更新状态显示

        Args:
            status: 连接状态
        """
        colors = self._theme.colors

        # 更新状态图标和文本
        if status.state == ConnectionState.CONNECTED:
            self.status_icon.config(text="●", foreground=colors.success)
            self.status_label.config(text="已连接", foreground=colors.success)
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.open_btn.config(state="normal")

            # 显示连接时间
            if status.uptime_seconds is not None:
                mins, secs = divmod(status.uptime_seconds, 60)
                hours, mins = divmod(mins, 60)
                if hours > 0:
                    self.uptime_label.config(text=f"已运行 {hours}h {mins}m")
                elif mins > 0:
                    self.uptime_label.config(text=f"已运行 {mins}m {secs}s")
                else:
                    self.uptime_label.config(text=f"已运行 {secs}s")

        elif status.state == ConnectionState.CONNECTING:
            self.status_icon.config(text="◐", foreground=colors.warning)
            self.status_label.config(text="正在连接...", foreground=colors.warning)
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
            self.open_btn.config(state="disabled")
            self.uptime_label.config(text="")

        elif status.state == ConnectionState.RECONNECTING:
            self.status_icon.config(text="◐", foreground=colors.warning)
            self.status_label.config(text=status.message, foreground=colors.warning)
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.open_btn.config(state="disabled")
            self.uptime_label.config(text="")

        elif status.state == ConnectionState.ERROR:
            self.status_icon.config(text="●", foreground=colors.error)
            self.status_label.config(text=status.message, foreground=colors.error)
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.open_btn.config(state="disabled")
            self.uptime_label.config(text="")

        elif status.state == ConnectionState.STOPPING:
            self.status_icon.config(text="○", foreground=colors.fg_muted)
            self.status_label.config(text="正在停止...", foreground=colors.fg_muted)
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
            self.open_btn.config(state="disabled")
            self.uptime_label.config(text="")

        else:  # DISCONNECTED
            self.status_icon.config(text="○", foreground=colors.fg_muted)
            self.status_label.config(text="未连接", foreground=colors.fg_muted)
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.open_btn.config(state="disabled")
            self.uptime_label.config(text="")

    def append_log(self, message: str, level: str = "info") -> None:
        """
        添加日志

        Args:
            message: 日志消息
            level: 日志级别
        """
        self.log_text.config(state="normal")

        # 根据级别添加标签
        colors = self._theme.colors
        tag = None
        if level == "error":
            tag = "error"
            self.log_text.tag_configure(tag, foreground=colors.error)
        elif level == "warning":
            tag = "warning"
            self.log_text.tag_configure(tag, foreground=colors.warning)
        elif level == "success":
            tag = "success"
            self.log_text.tag_configure(tag, foreground=colors.success)

        # 添加时间戳
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] ", "time")
        self.log_text.tag_configure("time", foreground=colors.fg_muted)

        if tag:
            self.log_text.insert("end", f"{message}\n", tag)
        else:
            self.log_text.insert("end", f"{message}\n")

        self.log_text.see("end")
        self.log_text.config(state="disabled")