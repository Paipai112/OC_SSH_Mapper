"""
输入验证器测试
"""

import pytest
from src.utils.validators import (
    validate_ip, validate_port, validate_username,
    validate_password, sanitize_input
)


class TestValidators:
    """验证器测试"""

    def test_validate_ip_valid(self):
        """测试有效的 IP 地址"""
        # IPv4
        valid, _ = validate_ip("192.168.1.1")
        assert valid == True

        valid, _ = validate_ip("127.0.0.1")
        assert valid == True

        # 域名
        valid, _ = validate_ip("example.com")
        assert valid == True

        valid, _ = validate_ip("sub.example.com")
        assert valid == True

    def test_validate_ip_invalid(self):
        """测试无效的 IP 地址"""
        valid, _ = validate_ip("")
        assert valid == False

        valid, _ = validate_ip("   ")
        assert valid == False

    def test_validate_port_valid(self):
        """测试有效的端口"""
        valid, _ = validate_port(22)
        assert valid == True

        valid, _ = validate_port(80)
        assert valid == True

        valid, _ = validate_port(443)
        assert valid == True

        valid, _ = validate_port(65535)
        assert valid == True

    def test_validate_port_invalid(self):
        """测试无效的端口"""
        valid, _ = validate_port(-1)
        assert valid == False

        valid, _ = validate_port(0)
        assert valid == False

        valid, _ = validate_port(65536)
        assert valid == False

    def test_validate_username(self):
        """测试用户名验证"""
        valid, _ = validate_username("root")
        assert valid == True

        valid, _ = validate_username("user123")
        assert valid == True

        valid, _ = validate_username("")
        assert valid == False

    def test_validate_password(self):
        """测试密码验证"""
        valid, _ = validate_password("password123")
        assert valid == True

        valid, _ = validate_password("")
        assert valid == False

    def test_sanitize_input(self):
        """测试输入清理"""
        # 正常输入
        assert sanitize_input("test") == "test"

        # 带空格的输入
        assert sanitize_input("  test  ") == "test"

        # 带危险字符的输入（sanitize_input 只清理空白，不移除特殊字符）
        result = sanitize_input("test; rm -rf /")
        assert result == "test; rm -rf /"  # 特殊字符不会被清理