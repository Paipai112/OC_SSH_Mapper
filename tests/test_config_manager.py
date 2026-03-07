"""
配置管理模块测试
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.config.config_manager import ConfigManager
from src.models.connection_config import ConnectionConfig, AuthType


class TestConfigManager:
    """配置管理器测试"""

    def test_default_config(self):
        """测试默认配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            manager = ConfigManager(config_path)

            # 验证默认设置
            assert manager.get_setting("auto_start") == False
            assert manager.get_setting("dark_mode") == True
            assert manager.get_setting("auto_reconnect") == True

    def test_add_preset(self):
        """测试添加预设"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            manager = ConfigManager(config_path)

            config = ConnectionConfig(
                name="测试服务器",
                ssh_host="192.168.1.1",
                ssh_port=22,
                ssh_user="root",
                local_port=8080,
                remote_host="127.0.0.1",
                remote_port=80,
                auth_type=AuthType.PASSWORD,
                password="test123"
            )

            result = manager.add_preset(config)
            assert result == True

            # 验证预设已添加
            presets = manager.get_presets()
            assert len(presets) == 1
            assert presets[0].name == "测试服务器"

    def test_delete_preset(self):
        """测试删除预设"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            manager = ConfigManager(config_path)

            config = ConnectionConfig(
                name="测试服务器",
                ssh_host="192.168.1.1",
                ssh_port=22,
                ssh_user="root",
                local_port=8080,
                remote_host="127.0.0.1",
                remote_port=80,
                auth_type=AuthType.PASSWORD,
                password="test123"
            )

            manager.add_preset(config)
            result = manager.delete_preset("测试服务器")
            assert result == True

            presets = manager.get_presets()
            assert len(presets) == 0

    def test_settings_update(self):
        """测试设置更新"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            manager = ConfigManager(config_path)

            manager.set_setting("dark_mode", False)
            assert manager.get_setting("dark_mode") == False

            manager.update_settings({
                "auto_start": True,
                "auto_reconnect": False
            })
            assert manager.get_setting("auto_start") == True
            assert manager.get_setting("auto_reconnect") == False