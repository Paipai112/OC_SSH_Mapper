"""
配置管理模块

负责配置文件的读取、保存和预设管理。
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, List

from src.models.connection_config import ConnectionConfig
from src.config.encryption import encrypt_password, decrypt_password
from src.utils.logger import get_logger

logger = get_logger()


def _get_config_dir() -> Path:
    """
    获取配置文件目录

    在开发环境下使用项目根目录
    在打包 EXE 后使用用户数据目录 (APPDATA)
    """
    # 检查是否在 PyInstaller 打包环境中运行
    if getattr(sys, 'frozen', False):
        # 打包后的 EXE 环境 - 使用 APPDATA
        if sys.platform == 'win32':
            appdata = os.getenv('APPDATA')
            if appdata:
                config_dir = Path(appdata) / 'GatewayMapper'
                config_dir.mkdir(parents=True, exist_ok=True)
                return config_dir
        # 非 Windows 或 APPDATA 不可用时，使用用户主目录
        config_dir = Path.home() / '.gatewaymapper'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    else:
        # 开发环境 - 使用项目根目录
        return Path(__file__).parent.parent.parent


def _get_legacy_config_path() -> Path:
    """
    获取旧版配置文件路径（项目根目录）

    用于从旧版本迁移配置
    """
    if getattr(sys, 'frozen', False):
        # EXE 环境下，尝试从临时目录的父目录查找
        # PyInstaller 会解压到 %TEMP%\_MEIxxxxx\
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        # 旧版本可能将配置保存到了临时目录
        # 这里返回项目根目录作为备用
        return Path(__file__).parent.parent.parent / "config.json"
    else:
        return Path(__file__).parent.parent.parent / "config.json"


def _migrate_config_if_needed(new_config_path: Path) -> None:
    """
    如果需要，从旧版路径迁移配置到新路径

    Args:
        new_config_path: 新的配置文件路径
    """
    # 如果新路径已存在，不需要迁移
    if new_config_path.exists():
        return

    # 检查旧版配置文件
    legacy_path = _get_legacy_config_path()
    if legacy_path.exists() and legacy_path != new_config_path:
        try:
            # 复制配置文件
            import shutil
            new_config_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(legacy_path, new_config_path)
            logger.info(f"已从旧版路径迁移配置：{legacy_path} -> {new_config_path}")
        except Exception as e:
            logger.error(f"迁移配置文件失败：{e}")


# 配置文件路径
CONFIG_DIR = _get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"

# 在模块加载时尝试迁移配置（仅在 EXE 环境下）
if getattr(sys, 'frozen', False):
    _migrate_config_if_needed(CONFIG_FILE)


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