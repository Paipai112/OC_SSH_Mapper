"""
主窗口模块

应用程序主界面。
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
from typing import Optional

from src.models.connection_config import ConnectionConfig
from src.models.connection_state import ConnectionStatus
from src.core.connection_manager import ConnectionManager, ReconnectConfig
from src.config.config_manager import get_config_manager
from src.ui.theme import get_theme, Theme
from src.ui.components.connection_form import ConnectionForm
from src.ui.components.status_panel import StatusPanel
from src.ui.components.preset_selector import PresetSelector
from src.services.system_tray import SystemTrayService
from src.utils.logger import get_logger

logger = get_logger()


class MainWindow:
    """
    主窗口

    功能:
    - 集成所有 UI 组件
    - 管理连接生命周期
    - 系统托盘集成
    """

    def __init__(self, root: tk.Tk):
        """
        初始化主窗口

        Args:
            root: Tk 根窗口
        """
        self._root = root
        self._theme = get_theme()
        self._config_manager = get_config_manager()
        self._connection_manager = ConnectionManager(
            reconnect_config=ReconnectConfig(
                enabled=self._config_manager.get_setting("auto_reconnect", True),
                interval=self._config_manager.get_setting("reconnect_interval", 5),
                max_attempts=self._config_manager.get_setting("max_reconnect_attempts", 10)
            )
        )
        self._exit_callback = None

        self._setup_root()
        self._setup_styles()
        self._build_ui()
        self._setup_callbacks()
        self._setup_tray()
        self._load_last_config()

    def _set_exit_callback(self, callback) -> None:
        """设置退出回调"""
        self._exit_callback = callback
        # 同时将回调传递给系统托盘服务
        if hasattr(self, '_tray') and self._tray:
            self._tray.set_exit_callback(self._on_exit_from_tray)

    def _on_exit_from_tray(self) -> None:
        """从托盘菜单触发的退出"""
        if self._exit_callback:
            self._exit_callback()

    def _setup_root(self) -> None:
        """配置根窗口"""
        self._root.title("GatewayMapper - SSH 端口转发工具")
        self._root.geometry("500x600")
        self._root.minsize(450, 500)

        # 应用主题
        self._theme.apply_to_root(self._root)

        # 关闭时隐藏到托盘（不退出应用）
        self._root.protocol("WM_DELETE_WINDOW", self._hide_to_tray)

        # 居中显示
        self._root.update_idletasks()
        x = (self._root.winfo_screenwidth() - self._root.winfo_width()) // 2
        y = (self._root.winfo_screenheight() - self._root.winfo_height()) // 2
        self._root.geometry(f"+{x}+{y}")

    def _setup_styles(self) -> None:
        """配置样式"""
        style = ttk.Style()
        self._theme.configure_styles(style)

    def _build_ui(self) -> None:
        """构建 UI"""
        # 主容器
        main_frame = ttk.Frame(self._root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # 预设选择器
        self.preset_selector = PresetSelector(
            main_frame,
            on_select=self._on_preset_selected
        )
        self.preset_selector.pack(fill="x", pady=(0, 10))
        self.preset_selector.bind("<<SavePreset>>", self._on_save_preset)

        # 连接表单
        self.connection_form = ConnectionForm(
            main_frame,
            on_connect=self._start_connection
        )
        self.connection_form.pack(fill="x", pady=(0, 10))

        # 状态面板
        self.status_panel = StatusPanel(
            main_frame,
            on_start=self._start_connection,
            on_stop=self._stop_connection,
            on_open_browser=self._open_browser
        )
        self.status_panel.pack(fill="both", expand=True)

    def _setup_callbacks(self) -> None:
        """设置回调"""
        self._connection_manager.set_status_callback(self._on_status_changed)

    def _setup_tray(self) -> None:
        """设置系统托盘"""
        self._tray = SystemTrayService(
            on_show=self._show_window,
            on_exit=self._exit_app
        )
        self._tray.start()

    def _load_last_config(self) -> None:
        """加载上次使用的配置"""
        config = self._config_manager.get_current_preset()
        if config:
            self.connection_form.set_config(config)
            # 同步更新 PresetSelector 的选中状态
            current_preset_name = self._config_manager.get_current_preset_name()
            if current_preset_name:
                self.preset_selector.preset_var.set(current_preset_name)
            logger.info(f"已加载上次使用的预设：{current_preset_name}")

    def _on_preset_selected(self, config: ConnectionConfig) -> None:
        """预设选择回调"""
        self.connection_form.set_config(config)

    def _on_save_preset(self, _event) -> None:
        """保存预设回调"""
        config = self.connection_form.get_config()
        if config:
            self.preset_selector.save_current_config(config)

    def _start_connection(self) -> None:
        """启动连接"""
        config = self.connection_form.get_config()
        if config is None:
            return

        # 在后台线程执行连接
        def connect_task():
            success, error = self._connection_manager.connect(config, open_browser=False)
            if not success:
                self._root.after(0, lambda: self.status_panel.append_log(error, "error"))

        threading.Thread(target=connect_task, daemon=True).start()
        self.status_panel.append_log(f"正在连接 {config.ssh_host}...")

    def _stop_connection(self) -> None:
        """停止连接"""
        self._connection_manager.disconnect()

    def _open_browser(self) -> None:
        """打开OpenClaw WebUI"""
        config = self.connection_form.get_config()
        if config is None:
            return

        url = f"http://localhost:{config.local_port}"
        try:
            webbrowser.open(url, new=1, autoraise=True)
            self.status_panel.append_log(f"已打开浏览器: {url}")
            logger.info(f"已打开浏览器: {url}")
        except Exception as e:
            self.status_panel.append_log(f"打开浏览器失败: {e}", "error")
            logger.error(f"打开浏览器失败: {e}")

    def _on_status_changed(self, status: ConnectionStatus) -> None:
        """状态变化回调"""
        self._root.after(0, lambda: self.status_panel.update_status(status))

        # 更新托盘图标
        if status.is_connected:
            self._tray.set_connected()
        else:
            self._tray.set_disconnected()

    def _hide_to_tray(self) -> None:
        """隐藏窗口到系统托盘"""
        self._root.withdraw()
        logger.debug("窗口已隐藏到托盘")

    def _hide_window(self) -> None:
        """隐藏窗口（同 hide_to_tray，保持兼容）"""
        self._root.withdraw()

    def _show_window(self) -> None:
        """显示窗口"""
        self._root.deiconify()
        self._root.lift()
        self._root.focus_force()

    def _exit_app(self) -> None:
        """退出应用"""
        logger.info("正在退出应用...")

        # 如果有退出回调，先调用回调（由 main.py 处理单实例释放）
        if self._exit_callback:
            self._exit_callback()
            return

        # 断开连接
        if self._connection_manager.is_connected:
            self._connection_manager.disconnect()

        # 停止托盘
        self._tray.stop()

        # 停止 tkinter 主循环
        self._root.quit()

        # 销毁窗口
        self._root.destroy()

        logger.info("应用已退出")