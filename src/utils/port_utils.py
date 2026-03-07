"""
端口工具模块

提供端口检查和释放功能。
"""

import socket
import time
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger()


def check_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """
    检查端口是否可用

    Args:
        port: 端口号
        host: 主机地址

    Returns:
        端口是否可用
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
        return True
    except OSError:
        return False


def release_port(port: int, host: str = "127.0.0.1") -> bool:
    """
    尝试释放端口

    Args:
        port: 端口号
        host: 主机地址

    Returns:
        是否成功释放
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b'\x00\x00\x00\x00')
        s.bind((host, port))
        s.close()
        time.sleep(0.1)
        return True
    except Exception:
        return False


def find_available_port(start_port: int = 18000, max_attempts: int = 100) -> Optional[int]:
    """
    查找可用端口

    Args:
        start_port: 起始端口
        max_attempts: 最大尝试次数

    Returns:
        可用端口号，如果找不到返回 None
    """
    for port in range(start_port, start_port + max_attempts):
        if check_port_available(port):
            return port
    return None


def get_port_status(port: int, host: str = "127.0.0.1") -> dict:
    """
    获取端口状态

    Args:
        port: 端口号
        host: 主机地址

    Returns:
        状态字典
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            if result == 0:
                return {"status": "in_use", "available": False}
            return {"status": "available", "available": True}
    except Exception as e:
        return {"status": "error", "error": str(e), "available": False}