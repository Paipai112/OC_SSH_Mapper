"""
数据模型模块

包含连接配置和连接状态的数据模型定义。
"""

from .connection_config import ConnectionConfig, AuthType
from .connection_state import ConnectionStatus, ConnectionState

__all__ = [
    "ConnectionConfig",
    "AuthType",
    "ConnectionStatus",
    "ConnectionState"
]