"""
输入验证器模块

提供各种输入验证功能。
"""

import re
from typing import Tuple, Optional
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger()


def validate_ip(ip: str) -> Tuple[bool, str]:
    """
    验证 IP 地址

    Args:
        ip: IP 地址字符串

    Returns:
        (是否有效, 错误信息)
    """
    if not ip or not ip.strip():
        return False, "IP 地址不能为空"

    ip = ip.strip()

    # IPv4 验证
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ipv4_pattern, ip):
        parts = ip.split('.')
        for part in parts:
            if int(part) > 255:
                return False, f"无效的 IP 地址段: {part}"
        return True, ""

    # 主机名验证
    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    if re.match(hostname_pattern, ip):
        return True, ""

    return False, "无效的 IP 地址或主机名"


def validate_port(port: int) -> Tuple[bool, str]:
    """
    验证端口号

    Args:
        port: 端口号

    Returns:
        (是否有效, 错误信息)
    """
    if not isinstance(port, int):
        return False, "端口号必须是整数"

    if port < 1:
        return False, "端口号不能小于 1"

    if port > 65535:
        return False, "端口号不能大于 65535"

    if port < 1024:
        logger.warning(f"使用特权端口 {port}，可能需要管理员权限")

    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """
    验证用户名

    Args:
        username: 用户名

    Returns:
        (是否有效, 错误信息)
    """
    if not username or not username.strip():
        return False, "用户名不能为空"

    username = username.strip()

    # 基本格式验证
    if len(username) > 32:
        return False, "用户名不能超过 32 个字符"

    # 允许的字符：字母、数字、下划线、连字符、点
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        return False, "用户名只能包含字母、数字、下划线、连字符和点"

    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    验证密码

    Args:
        password: 密码

    Returns:
        (是否有效, 错误信息)
    """
    if not password:
        return False, "密码不能为空"

    # 警告弱密码
    if len(password) < 8:
        logger.warning("密码长度不足 8 位，建议使用更强的密码")

    return True, ""


def validate_key_file(path: str) -> Tuple[bool, str]:
    """
    验证密钥文件路径

    Args:
        path: 文件路径

    Returns:
        (是否有效, 错误信息)
    """
    if not path or not path.strip():
        return False, "密钥文件路径不能为空"

    key_path = Path(path.strip()).expanduser()

    if not key_path.exists():
        return False, f"密钥文件不存在: {key_path}"

    if not key_path.is_file():
        return False, f"路径不是文件: {key_path}"

    # 检查文件权限（仅 Unix）
    try:
        import stat
        mode = key_path.stat().st_mode
        if mode & stat.S_IRWXO:
            logger.warning("密钥文件权限过于开放，建议设置为 600")
    except Exception:
        pass

    return True, ""


def sanitize_input(value: str, max_length: int = 256) -> str:
    """
    清理输入字符串

    Args:
        value: 输入值
        max_length: 最大长度

    Returns:
        清理后的字符串
    """
    if not value:
        return ""

    # 去除首尾空白
    value = value.strip()

    # 限制长度
    if len(value) > max_length:
        value = value[:max_length]
        logger.warning(f"输入已截断至 {max_length} 个字符")

    # 移除控制字符
    value = ''.join(c for c in value if ord(c) >= 32 or c in '\t\n')

    return value


def validate_config_name(name: str) -> Tuple[bool, str]:
    """
    验证配置名称

    Args:
        name: 配置名称

    Returns:
        (是否有效, 错误信息)
    """
    if not name or not name.strip():
        return False, "配置名称不能为空"

    name = name.strip()

    if len(name) > 64:
        return False, "配置名称不能超过 64 个字符"

    # 禁止特殊字符
    if re.search(r'[<>:"/\\|?*]', name):
        return False, "配置名称包含非法字符"

    return True, ""


class InputValidator:
    """
    输入验证器类

    提供统一的验证接口
    """

    @staticmethod
    def validate_ip(ip: str) -> Tuple[bool, str]:
        """验证 IP 地址"""
        return validate_ip(ip)

    @staticmethod
    def validate_port(port: int) -> Tuple[bool, str]:
        """验证端口号"""
        return validate_port(port)

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """验证用户名"""
        return validate_username(username)

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """验证密码"""
        return validate_password(password)

    @staticmethod
    def validate_key_file(path: str) -> Tuple[bool, str]:
        """验证密钥文件"""
        return validate_key_file(path)

    @staticmethod
    def sanitize(value: str, max_length: int = 256) -> str:
        """清理输入"""
        return sanitize_input(value, max_length)

    @staticmethod
    def validate_config_name(name: str) -> Tuple[bool, str]:
        """验证配置名称"""
        return validate_config_name(name)