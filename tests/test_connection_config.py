"""
连接配置模型测试
"""

import pytest
from src.models.connection_config import ConnectionConfig, AuthType


class TestConnectionConfig:
    """连接配置测试"""

    def test_create_config(self):
        """测试创建配置"""
        config = ConnectionConfig(
            name="测试",
            ssh_host="192.168.1.1",
            ssh_port=22,
            ssh_user="root",
            local_port=8080,
            remote_host="127.0.0.1",
            remote_port=80,
            auth_type=AuthType.PASSWORD,
            password="test123"
        )

        assert config.name == "测试"
        assert config.ssh_host == "192.168.1.1"
        assert config.ssh_port == 22
        assert config.auth_type == AuthType.PASSWORD

    def test_config_to_dict(self):
        """测试配置转字典"""
        config = ConnectionConfig(
            name="测试",
            ssh_host="192.168.1.1",
            ssh_port=22,
            ssh_user="root",
            local_port=8080,
            remote_host="127.0.0.1",
            remote_port=80,
            auth_type=AuthType.PASSWORD
        )

        data = config.to_dict()
        assert data["name"] == "测试"
        assert data["ssh_host"] == "192.168.1.1"

    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            "name": "测试",
            "ssh_host": "192.168.1.1",
            "ssh_port": 22,
            "ssh_user": "root",
            "local_port": 8080,
            "remote_host": "127.0.0.1",
            "remote_port": 80,
            "auth_type": "password",
            "password": "test123"
        }

        config = ConnectionConfig.from_dict(data)
        assert config.name == "测试"
        assert config.ssh_host == "192.168.1.1"

    def test_config_validation(self):
        """测试配置验证"""
        # 有效配置
        config = ConnectionConfig(
            name="测试",
            ssh_host="192.168.1.1",
            ssh_port=22,
            ssh_user="root",
            local_port=8080,
            remote_host="127.0.0.1",
            remote_port=80,
            auth_type=AuthType.PASSWORD,
            password="test123"
        )
        valid, _ = config.validate()
        assert valid == True

        # 无效配置（缺少主机）
        config2 = ConnectionConfig(
            name="测试",
            ssh_host="",
            ssh_port=22,
            ssh_user="root",
            local_port=8080,
            remote_host="127.0.0.1",
            remote_port=80,
            auth_type=AuthType.PASSWORD,
            password="test123"
        )
        valid, _ = config2.validate()
        assert valid == False