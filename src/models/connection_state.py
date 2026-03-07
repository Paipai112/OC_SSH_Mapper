"""
连接状态数据模型

定义 SSH 连接状态的数据结构。
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ConnectionState(Enum):
    """连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    STOPPING = "stopping"


@dataclass
class ConnectionStatus:
    """
    连接状态数据模型

    Attributes:
        state: 当前连接状态
        message: 状态消息
        error: 错误信息
        connected_at: 连接建立时间
        reconnect_count: 重连次数
        last_error_time: 最后一次错误时间
    """
    state: ConnectionState = ConnectionState.DISCONNECTED
    message: str = "未连接"
    error: Optional[str] = None
    connected_at: Optional[datetime] = None
    reconnect_count: int = 0
    last_error_time: Optional[datetime] = None

    def set_connecting(self) -> None:
        """设置正在连接状态"""
        self.state = ConnectionState.CONNECTING
        self.message = "正在连接..."
        self.error = None

    def set_connected(self) -> None:
        """设置已连接状态"""
        self.state = ConnectionState.CONNECTED
        self.message = "已连接"
        self.error = None
        self.connected_at = datetime.now()
        self.reconnect_count = 0

    def set_disconnected(self, message: str = "已断开") -> None:
        """设置已断开状态"""
        self.state = ConnectionState.DISCONNECTED
        self.message = message
        self.connected_at = None

    def set_reconnecting(self, attempt: int = 1) -> None:
        """设置正在重连状态"""
        self.state = ConnectionState.RECONNECTING
        self.message = f"正在重连... (第 {attempt} 次)"
        self.reconnect_count = attempt

    def set_error(self, error: str) -> None:
        """设置错误状态"""
        self.state = ConnectionState.ERROR
        self.message = f"错误: {error}"
        self.error = error
        self.last_error_time = datetime.now()
        self.connected_at = None

    def set_stopping(self) -> None:
        """设置正在停止状态"""
        self.state = ConnectionState.STOPPING
        self.message = "正在停止..."

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self.state == ConnectionState.CONNECTED

    @property
    def is_active(self) -> bool:
        """是否有活跃的连接尝试"""
        return self.state in (
            ConnectionState.CONNECTING,
            ConnectionState.CONNECTED,
            ConnectionState.RECONNECTING
        )

    @property
    def uptime_seconds(self) -> Optional[int]:
        """连接持续时间（秒）"""
        if self.connected_at is None:
            return None
        return int((datetime.now() - self.connected_at).total_seconds())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "state": self.state.value,
            "message": self.message,
            "error": self.error,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "reconnect_count": self.reconnect_count,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None
        }