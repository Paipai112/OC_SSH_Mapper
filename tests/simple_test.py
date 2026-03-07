"""
简单测试脚本 - 不依赖 pytest

运行: python tests/simple_test.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.validators import (
    validate_ip, validate_port, validate_username,
    validate_password, sanitize_input
)
from src.models.connection_config import ConnectionConfig, AuthType


def test_validators():
    """测试验证器"""
    print("测试验证器...")

    # IP 验证
    assert validate_ip("192.168.1.1")[0] == True, "IPv4 验证失败"
    assert validate_ip("127.0.0.1")[0] == True, "本地回环地址验证失败"
    assert validate_ip("example.com")[0] == True, "域名验证失败"
    assert validate_ip("")[0] == False, "空 IP 应该无效"
    print("  [PASS] IP 验证")

    # 端口验证
    assert validate_port(22)[0] == True, "端口 22 应该有效"
    assert validate_port(80)[0] == True, "端口 80 应该有效"
    assert validate_port(65535)[0] == True, "端口 65535 应该有效"
    assert validate_port(0)[0] == False, "端口 0 应该无效"
    assert validate_port(65536)[0] == False, "端口 65536 应该无效"
    assert validate_port(-1)[0] == False, "负端口应该无效"
    print("  [PASS] 端口验证")

    # 用户名验证
    assert validate_username("root")[0] == True, "用户名 root 应该有效"
    assert validate_username("user123")[0] == True, "用户名 user123 应该有效"
    assert validate_username("")[0] == False, "空用户名应该无效"
    print("  [PASS] 用户名验证")

    # 密码验证
    assert validate_password("password123")[0] == True, "密码应该有效"
    assert validate_password("")[0] == False, "空密码应该无效"
    print("  [PASS] 密码验证")

    print("[OK] 验证器测试通过")


def test_config_model():
    """测试配置模型"""
    print("测试配置模型...")

    # 创建配置
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

    assert config.name == "测试服务器", "配置名称不匹配"
    assert config.ssh_host == "192.168.1.1", "主机地址不匹配"
    assert config.ssh_port == 22, "SSH 端口不匹配"
    assert config.auth_type == AuthType.PASSWORD, "认证类型不匹配"
    print("  [PASS] 配置创建")

    # 测试字典转换
    data = config.to_dict()
    assert data["name"] == "测试服务器", "字典转换失败"
    assert data["ssh_host"] == "192.168.1.1", "字典转换失败"
    print("  [PASS] 配置转字典")

    # 测试从字典创建
    config2 = ConnectionConfig.from_dict(data)
    assert config2.name == "测试服务器", "从字典创建失败"
    assert config2.ssh_host == "192.168.1.1", "从字典创建失败"
    print("  [PASS] 从字典创建")

    # 测试验证
    valid, _ = config.validate()
    assert valid == True, "有效配置验证失败"

    invalid_config = ConnectionConfig(
        name="测试",
        ssh_host="",  # 无效：空主机
        ssh_port=22,
        ssh_user="root",
        local_port=8080,
        remote_host="127.0.0.1",
        remote_port=80,
        auth_type=AuthType.PASSWORD
    )
    valid, _ = invalid_config.validate()
    assert valid == False, "无效配置应该验证失败"
    print("  [PASS] 配置验证")

    print("[OK] 配置模型测试通过")


def test_encryption():
    """测试加密模块"""
    print("测试加密模块...")

    from src.config.encryption import encrypt_password, decrypt_password

    # 测试加密解密
    original = "my_secret_password"
    encrypted = encrypt_password(original)

    assert encrypted != original, "加密后应该不同"
    assert len(encrypted) > 0, "加密结果不应为空"

    decrypted = decrypt_password(encrypted)
    assert decrypted == original, "解密后应该与原始值相同"
    print("  [PASS] 加密解密")

    print("[OK] 加密模块测试通过")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("GatewayMapper 核心功能测试")
    print("=" * 50)
    print()

    try:
        test_validators()
        print()
        test_config_model()
        print()
        test_encryption()
        print()
        print("=" * 50)
        print("所有测试通过!")
        print("=" * 50)
        return 0
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())