"""
预设选择器组件

快速切换和管理配置预设。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, List

from src.models.connection_config import ConnectionConfig
from src.config.config_manager import get_config_manager
from src.ui.theme import get_theme
from src.utils.logger import get_logger

logger = get_logger()


class PresetSelector(ttk.Frame):
    """
    预设选择器组件

    功能:
    - 显示预设列表
    - 快速切换预设
    - 保存/删除预设
    """

    def __init__(self, parent, on_select: Optional[Callable[[ConnectionConfig], None]] = None):
        """
        初始化预设选择器

        Args:
            parent: 父组件
            on_select: 选择回调
        """
        super().__init__(parent)
        self._on_select = on_select
        self._theme = get_theme()
        self._config_manager = get_config_manager()
        self._build_ui()
        self._load_presets()

    def _build_ui(self) -> None:
        """构建 UI"""
        self.configure(style="Card.TFrame", padding=10)

        # 标题行
        title_frame = ttk.Frame(self, style="Card.TFrame")
        title_frame.pack(fill="x")

        ttk.Label(title_frame, text="配置预设:", style="Card.TLabel").pack(side="left")

        # 操作按钮
        btn_frame = ttk.Frame(title_frame, style="Card.TFrame")
        btn_frame.pack(side="right")

        ttk.Button(btn_frame, text="保存", width=6, command=self._save_preset).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="删除", width=6, command=self._delete_preset).pack(side="left", padx=2)

        # 预设下拉框
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(
            self, textvariable=self.preset_var,
            state="readonly", width=30
        )
        self.preset_combo.pack(fill="x", pady=(10, 0))
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

    def _load_presets(self) -> None:
        """加载预设列表"""
        presets = self._config_manager.get_presets()
        preset_names = [p.name for p in presets]

        self.preset_combo['values'] = preset_names

        # 设置当前预设
        current = self._config_manager.get_current_preset_name()
        if current and current in preset_names:
            self.preset_var.set(current)

    def _on_preset_selected(self, _event) -> None:
        """预设选择事件"""
        name = self.preset_var.get()
        config = self._config_manager.get_decrypted_preset(name)

        if config and self._on_select:
            self._on_select(config)
            self._config_manager.set_current_preset(name)
            logger.info(f"已选择预设: {name}")

    def _save_preset(self) -> None:
        """保存当前配置为预设"""
        # 这个方法需要从外部获取当前配置
        # 通过 emit 事件让父组件处理
        self.event_generate("<<SavePreset>>")

    def _delete_preset(self) -> None:
        """删除当前预设"""
        name = self.preset_var.get()
        if not name:
            messagebox.showwarning("警告", "请先选择一个预设")
            return

        if messagebox.askyesno("确认", f"确定要删除预设 '{name}' 吗?"):
            self._config_manager.delete_preset(name)
            self._load_presets()
            logger.info(f"已删除预设: {name}")

    def save_current_config(self, config: ConnectionConfig) -> bool:
        """
        保存配置到预设

        Args:
            config: 连接配置

        Returns:
            是否保存成功
        """
        # 检查是否已存在
        existing = self._config_manager.get_preset(config.name)
        if existing:
            if not messagebox.askyesno("确认", f"预设 '{config.name}' 已存在，是否覆盖?"):
                return False
            self._config_manager.update_preset(config.name, config)
        else:
            self._config_manager.add_preset(config)

        self._load_presets()
        self.preset_var.set(config.name)
        logger.info(f"已保存预设: {config.name}")
        return True

    def refresh(self) -> None:
        """刷新预设列表"""
        self._load_presets()