"""
连接表单组件

用于输入 SSH 连接配置。
"""

import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional, Callable

from src.models.connection_config import ConnectionConfig, AuthType
from src.ui.theme import get_theme
from src.utils.validators import (
    validate_ip, validate_port, validate_username,
    validate_password, validate_key_file, sanitize_input
)
from src.utils.logger import get_logger

logger = get_logger()


class ConnectionForm(ttk.Frame):
    """
    连接表单组件

    功能:
    - 输入 SSH 连接参数
    - 支持密码和密钥认证
    - 输入验证
    - 配置保存/加载
    """

    def __init__(self, parent, on_connect: Optional[Callable] = None):
        """
        初始化连接表单

        Args:
            parent: 父组件
            on_connect: 连接回调函数
        """
        super().__init__(parent)
        self._on_connect = on_connect
        self._theme = get_theme()
        self._build_ui()

    def _build_ui(self) -> None:
        """构建 UI"""
        colors = self._theme.colors

        # 主框架
        self.configure(style="Card.TFrame", padding=15)

        # 表单字段
        row = 0

        # 预设名称
        ttk.Label(self, text="配置名称:", style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(self, width=30)
        self.name_entry.grid(row=row, column=1, columnspan=2, sticky="we", pady=5, padx=(10, 0))
        row += 1

        # 服务器地址
        ttk.Label(self, text="服务器地址:", style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        self.host_entry = ttk.Entry(self, width=30)
        self.host_entry.grid(row=row, column=1, sticky="we", pady=5, padx=(10, 0))
        ttk.Label(self, text="端口:", style="Card.TLabel").grid(row=row, column=2, sticky="w", pady=5, padx=(10, 0))
        self.ssh_port_entry = ttk.Entry(self, width=8)
        self.ssh_port_entry.insert(0, "22")
        self.ssh_port_entry.grid(row=row, column=3, sticky="w", pady=5, padx=(5, 0))
        row += 1

        # 用户名
        ttk.Label(self, text="用户名:", style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        self.user_entry = ttk.Entry(self, width=30)
        self.user_entry.insert(0, "root")
        self.user_entry.grid(row=row, column=1, columnspan=3, sticky="we", pady=5, padx=(10, 0))
        row += 1

        # 认证方式
        ttk.Label(self, text="认证方式:", style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        self.auth_type_var = tk.StringVar(value="password")
        auth_frame = ttk.Frame(self, style="Card.TFrame")
        auth_frame.grid(row=row, column=1, columnspan=3, sticky="w", pady=5, padx=(10, 0))

        ttk.Radiobutton(
            auth_frame, text="密码", variable=self.auth_type_var,
            value="password", command=self._on_auth_type_change,
            style="Card.TRadiobutton"
        ).pack(side="left")

        ttk.Radiobutton(
            auth_frame, text="密钥文件", variable=self.auth_type_var,
            value="key_file", command=self._on_auth_type_change,
            style="Card.TRadiobutton"
        ).pack(side="left", padx=(15, 0))
        row += 1

        # 密码输入
        self.pwd_frame = ttk.Frame(self, style="Card.TFrame")
        self.pwd_frame.grid(row=row, column=0, columnspan=4, sticky="we", pady=5)

        ttk.Label(self.pwd_frame, text="密码:", style="Card.TLabel").pack(side="left")
        self.password_entry = ttk.Entry(self.pwd_frame, show="*", width=25)
        self.password_entry.pack(side="left", padx=(10, 0), fill="x", expand=True)

        self.remember_pwd_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.pwd_frame, text="记住", variable=self.remember_pwd_var,
                       style="Card.TCheckbutton").pack(side="left", padx=(10, 0))
        row += 1

        # 密钥文件
        self.key_frame = ttk.Frame(self, style="Card.TFrame")
        # 初始隐藏

        ttk.Label(self.key_frame, text="密钥文件:", style="Card.TLabel").pack(side="left")
        self.key_file_entry = ttk.Entry(self.key_frame, width=25)
        self.key_file_entry.pack(side="left", padx=(10, 0), fill="x", expand=True)
        ttk.Button(self.key_frame, text="浏览", command=self._browse_key_file, width=6).pack(side="left", padx=(5, 0))
        row += 1

        # 本地端口
        ttk.Label(self, text="本地端口:", style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        self.local_port_entry = ttk.Entry(self, width=10)
        self.local_port_entry.insert(0, "18789")
        self.local_port_entry.grid(row=row, column=1, sticky="w", pady=5, padx=(10, 0))
        row += 1

        # 远程端口
        ttk.Label(self, text="远程端口:", style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        self.remote_port_entry = ttk.Entry(self, width=10)
        self.remote_port_entry.insert(0, "18789")
        self.remote_port_entry.grid(row=row, column=1, sticky="w", pady=5, padx=(10, 0))
        row += 1

        # 错误提示
        self.error_label = ttk.Label(self, text="", foreground=self._theme.colors.error, style="Card.TLabel")
        self.error_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=5)

        # 配置列权重
        self.columnconfigure(1, weight=1)

    def _on_auth_type_change(self) -> None:
        """认证方式变更"""
        if self.auth_type_var.get() == "password":
            self.pwd_frame.grid()
            self.key_frame.grid_remove()
        else:
            self.pwd_frame.grid_remove()
            self.key_frame.grid()

    def _browse_key_file(self) -> None:
        """浏览密钥文件"""
        file_path = filedialog.askopenfilename(
            title="选择 SSH 私钥文件",
            filetypes=[("所有文件", "*.*"), ("PEM 文件", "*.pem"), ("PPK 文件", "*.ppk")]
        )
        if file_path:
            self.key_file_entry.delete(0, tk.END)
            self.key_file_entry.insert(0, file_path)

    def get_config(self) -> Optional[ConnectionConfig]:
        """
        获取当前配置

        Returns:
            ConnectionConfig 或 None（如果验证失败）
        """
        # 清除错误
        self.error_label.config(text="")

        # 获取值
        name = sanitize_input(self.name_entry.get()) or "默认配置"
        host = sanitize_input(self.host_entry.get())
        ssh_port = self._parse_int(self.ssh_port_entry.get(), 22)
        user = sanitize_input(self.user_entry.get())
        local_port = self._parse_int(self.local_port_entry.get(), 18789)
        remote_port = self._parse_int(self.remote_port_entry.get(), 18789)
        auth_type = AuthType.PASSWORD if self.auth_type_var.get() == "password" else AuthType.KEY_FILE
        password = self.password_entry.get()
        key_file = sanitize_input(self.key_file_entry.get())

        # 验证
        valid, error = validate_ip(host)
        if not valid:
            self._show_error(error)
            return None

        valid, error = validate_port(ssh_port)
        if not valid:
            self._show_error(error)
            return None

        valid, error = validate_username(user)
        if not valid:
            self._show_error(error)
            return None

        if auth_type == AuthType.PASSWORD:
            valid, error = validate_password(password)
            if not valid:
                self._show_error(error)
                return None
        else:
            valid, error = validate_key_file(key_file)
            if not valid:
                self._show_error(error)
                return None

        return ConnectionConfig(
            name=name,
            ssh_host=host,
            ssh_port=ssh_port,
            ssh_user=user,
            local_port=local_port,
            remote_host="127.0.0.1",
            remote_port=remote_port,
            auth_type=auth_type,
            password=password,
            key_file_path=key_file,
            remember_password=self.remember_pwd_var.get()
        )

    def set_config(self, config: ConnectionConfig) -> None:
        """
        设置配置

        Args:
            config: 连接配置
        """
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, config.name)

        self.host_entry.delete(0, tk.END)
        self.host_entry.insert(0, config.ssh_host)

        self.ssh_port_entry.delete(0, tk.END)
        self.ssh_port_entry.insert(0, str(config.ssh_port))

        self.user_entry.delete(0, tk.END)
        self.user_entry.insert(0, config.ssh_user)

        self.local_port_entry.delete(0, tk.END)
        self.local_port_entry.insert(0, str(config.local_port))

        self.remote_port_entry.delete(0, tk.END)
        self.remote_port_entry.insert(0, str(config.remote_port))

        self.auth_type_var.set(config.auth_type.value)
        self._on_auth_type_change()

        if config.auth_type == AuthType.KEY_FILE:
            self.key_file_entry.delete(0, tk.END)
            self.key_file_entry.insert(0, config.key_file_path)
        else:
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, config.password)

        self.remember_pwd_var.set(config.remember_password)

    def _parse_int(self, value: str, default: int) -> int:
        """解析整数"""
        try:
            return int(value.strip())
        except (ValueError, AttributeError):
            return default

    def _show_error(self, message: str) -> None:
        """显示错误"""
        self.error_label.config(text=message)