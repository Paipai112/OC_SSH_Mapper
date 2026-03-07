"""
配置管理模块

负责配置文件的读取、保存和预设管理。
"""

import json
import os
from pathlib import Path
from typing import Optional, List

from src.models.connection_config import ConnectionConfig
from src.config.encryption import encrypt_password, decrypt_password
from src.utils.logger import get_logger

logger = get_logger()

# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent.parent
CONFIG_FILE = CONFIG_DIR / "config.json"


class ConfigManager:
    """
    配置管理器

    功能:
    - 加载/保存配置文件
    - 管理多个预设配置
    - 加密存储密码
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为项目根目录下的 config.json
        """
        self.config_path = config_path or CONFIG_FILE
        self._config: dict = {}
        self._presets: List[ConnectionConfig] = []
        self._settings: dict = {}
        self._current_preset: Optional[str] = None
        self._load()

    def _get_default_config(self) -> dict:
        """获取默认配置结构"""
        return {
            "version": "2.0",
            "presets": [],
            "settings": {
                "auto_start": False,
                "dark_mode": True,
                "auto_reconnect": True,
                "reconnect_interval": 5,
                "max_reconnect_attempts": 10
            },
            "current_preset": None
        }

    def _load(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                logger.info(f"已加载配置文件: {self.config_path}")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                self._config = self._get_default_config()
        else:
            self._config = self._get_default_config()
            logger.info("使用默认配置")

        # 解析预设
        self._presets = []
        for preset_data in self._config.get("presets", []):
            preset = ConnectionConfig.from_dict(preset_data)
            self._presets.append(preset)

        # 解析设置
        self._settings = self._config.get("settings", self._get_default_config()["settings"])

        # 当前预设
        self._current_preset = self._config.get("current_preset")

    def _save(self) -> None:
        """保存配置文件"""
        try:
            config_data = {
                "version": "2.0",
                "presets": [p.to_dict() for p in self._presets],
                "settings": self._settings,
                "current_preset": self._current_preset
            }

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)

            logger.debug("配置已保存")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise

    # ========== 预设管理 ==========

    def get_presets(self) -> List[ConnectionConfig]:
        """获取所有预设"""
        return self._presets.copy()

    def get_preset(self, name: str) -> Optional[ConnectionConfig]:
        """
        获取指定名称的预设

        Args:
            name: 预设名称

        Returns:
            预设配置，如果不存在返回 None
        """
        for preset in self._presets:
            if preset.name == name:
                return preset
        return None

    def add_preset(self, config: ConnectionConfig) -> bool:
        """
        添加预设

        Args:
            config: 连接配置

        Returns:
            是否添加成功
        """
        # 检查是否已存在同名预设
        if self.get_preset(config.name) is not None:
            logger.warning(f"预设 '{config.name}' 已存在")
            return False

        # 加密密码后再存储
        stored_config = ConnectionConfig(
            name=config.name,
            ssh_host=config.ssh_host,
            ssh_port=config.ssh_port,
            ssh_user=config.ssh_user,
            local_port=config.local_port,
            remote_host=config.remote_host,
            remote_port=config.remote_port,
            auth_type=config.auth_type,
            encrypted_password=encrypt_password(config.password) if config.password else "",
            key_file_path=config.key_file_path,
            remember_password=config.remember_password
        )

        self._presets.append(stored_config)
        self._save()
        logger.info(f"已添加预设: {config.name}")
        return True

    def update_preset(self, name: str, config: ConnectionConfig) -> bool:
        """
        更新预设

        Args:
            name: 原预设名称
            config: 新的配置

        Returns:
            是否更新成功
        """
        for i, preset in enumerate(self._presets):
            if preset.name == name:
                # 加密密码
                stored_config = ConnectionConfig(
                    name=config.name,
                    ssh_host=config.ssh_host,
                    ssh_port=config.ssh_port,
                    ssh_user=config.ssh_user,
                    local_port=config.local_port,
                    remote_host=config.remote_host,
                    remote_port=config.remote_port,
                    auth_type=config.auth_type,
                    encrypted_password=encrypt_password(config.password) if config.password else preset.encrypted_password,
                    key_file_path=config.key_file_path,
                    remember_password=config.remember_password
                )
                self._presets[i] = stored_config
                self._save()
                logger.info(f"已更新预设: {name}")
                return True

        logger.warning(f"预设 '{name}' 不存在")
        return False

    def delete_preset(self, name: str) -> bool:
        """
        删除预设

        Args:
            name: 预设名称

        Returns:
            是否删除成功
        """
        for i, preset in enumerate(self._presets):
            if preset.name == name:
                self._presets.pop(i)
                if self._current_preset == name:
                    self._current_preset = None
                self._save()
                logger.info(f"已删除预设: {name}")
                return True

        logger.warning(f"预设 '{name}' 不存在")
        return False

    def get_decrypted_preset(self, name: str) -> Optional[ConnectionConfig]:
        """
        获取解密后的预设（包含明文密码）

        Args:
            name: 预设名称

        Returns:
            解密后的配置
        """
        preset = self.get_preset(name)
        if preset is None:
            return None

        # 解密密码
        decrypted_config = ConnectionConfig(
            name=preset.name,
            ssh_host=preset.ssh_host,
            ssh_port=preset.ssh_port,
            ssh_user=preset.ssh_user,
            local_port=preset.local_port,
            remote_host=preset.remote_host,
            remote_port=preset.remote_port,
            auth_type=preset.auth_type,
            password=decrypt_password(preset.encrypted_password),
            encrypted_password=preset.encrypted_password,
            key_file_path=preset.key_file_path,
            remember_password=preset.remember_password
        )

        return decrypted_config

    # ========== 设置管理 ==========

    def get_settings(self) -> dict:
        """获取所有设置"""
        return self._settings.copy()

    def get_setting(self, key: str, default=None):
        """获取单个设置"""
        return self._settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """设置单个配置项"""
        self._settings[key] = value
        self._save()

    def update_settings(self, settings: dict) -> None:
        """批量更新设置"""
        self._settings.update(settings)
        self._save()

    # ========== 当前预设 ==========

    def get_current_preset_name(self) -> Optional[str]:
        """获取当前预设名称"""
        return self._current_preset

    def set_current_preset(self, name: Optional[str]) -> None:
        """设置当前预设"""
        if name is not None and self.get_preset(name) is None:
            logger.warning(f"预设 '{name}' 不存在")
            return
        self._current_preset = name
        self._save()

    def get_current_preset(self) -> Optional[ConnectionConfig]:
        """获取当前预设（解密后）"""
        if self._current_preset is None:
            return None
        return self.get_decrypted_preset(self._current_preset)


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager