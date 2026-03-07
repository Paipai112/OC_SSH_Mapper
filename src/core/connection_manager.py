"""
连接管理器模块

管理 SSH 连接状态、自动重连和健康监控。
"""

import threading
import time
import webbrowser
from typing import Optional, Callable
from dataclasses import dataclass

from src.models.connection_config import ConnectionConfig
from src.models.connection_state import ConnectionStatus, ConnectionState
from src.core.ssh_client import SSHClient
from src.core.port_forwarder import PortForwarder
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class ReconnectConfig:
    """重连配置"""
    enabled: bool = True
    interval: int = 5  # 秒
    max_attempts: int = 10


class ConnectionManager:
    """
    连接管理器

    功能:
    - 管理 SSH 连接生命周期
    - 自动重连
    - 健康监控
    - 状态回调
    """

    def __init__(self, reconnect_config: Optional[ReconnectConfig] = None):
        """
        初始化连接管理器

        Args:
            reconnect_config: 重连配置
        """
        self._ssh_client = SSHClient()
        self._forwarder = PortForwarder()
        self._status = ConnectionStatus()
        self._config: Optional[ConnectionConfig] = None
        self._reconnect_config = reconnect_config or ReconnectConfig()
        self._lock = threading.Lock()
        self._reconnect_thread: Optional[threading.Thread] = None
        self._health_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._status_callback: Optional[Callable[[ConnectionStatus], None]] = None
        self._open_browser_on_connect = True

    @property
    def status(self) -> ConnectionStatus:
        """获取当前状态"""
        return self._status

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._status.is_connected

    def set_status_callback(self, callback: Optional[Callable[[ConnectionStatus], None]]) -> None:
        """
        设置状态变化回调

        Args:
            callback: 回调函数
        """
        self._status_callback = callback

    def _notify_status_change(self) -> None:
        """通知状态变化"""
        if self._status_callback is not None:
            try:
                self._status_callback(self._status)
            except Exception as e:
                logger.error(f"状态回调出错: {e}")

    def connect(self, config: ConnectionConfig, open_browser: bool = True) -> tuple[bool, str]:
        """
        建立连接

        Args:
            config: 连接配置
            open_browser: 是否打开浏览器

        Returns:
            (是否成功, 错误信息)
        """
        with self._lock:
            if self._status.is_active:
                return False, "已有活跃连接"

            self._config = config
            self._open_browser_on_connect = open_browser
            self._stop_event.clear()

        # 更新状态
        self._status.set_connecting()
        self._notify_status_change()

        # 执行连接
        success, error = self._do_connect()

        if success:
            # 启动健康监控
            self._start_health_monitor()

            # 打开浏览器
            if open_browser:
                self._open_browser()
        else:
            self._status.set_error(error)

        self._notify_status_change()
        return success, error

    def _do_connect(self) -> tuple[bool, str]:
        """执行实际连接"""
        if self._config is None:
            return False, "配置为空"

        # 验证配置
        valid, error = self._config.validate()
        if not valid:
            return False, error

        # 建立 SSH 连接
        success, error = self._ssh_client.connect(self._config)
        if not success:
            return False, error

        # 启动端口转发
        transport = self._ssh_client.transport
        if transport is None:
            self._ssh_client.disconnect()
            return False, "无法获取传输通道"

        success = self._forwarder.start(
            transport,
            self._config.local_port,
            self._config.remote_host,
            self._config.remote_port
        )

        if not success:
            self._ssh_client.disconnect()
            return False, "启动端口转发失败"

        self._status.set_connected()
        logger.info(f"连接成功: {self._config.ssh_host}")
        return True, ""

    def disconnect(self) -> None:
        """断开连接"""
        with self._lock:
            if not self._status.is_active:
                return

            self._status.set_stopping()
            self._notify_status_change()

        # 停止重连和健康监控
        self._stop_event.set()
        self._stop_health_monitor()
        self._stop_reconnect()

        # 停止端口转发
        self._forwarder.stop()

        # 断开 SSH 连接
        self._ssh_client.disconnect()

        self._status.set_disconnected()
        self._notify_status_change()
        logger.info("已断开连接")

    def reconnect(self) -> tuple[bool, str]:
        """
        手动重连

        Returns:
            (是否成功, 错误信息)
        """
        if self._config is None:
            return False, "没有可用配置"

        self.disconnect()
        time.sleep(1)

        return self.connect(self._config, self._open_browser_on_connect)

    def _start_health_monitor(self) -> None:
        """启动健康监控线程"""
        if self._health_thread is not None and self._health_thread.is_alive():
            return

        self._health_thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
        self._health_thread.start()

    def _stop_health_monitor(self) -> None:
        """停止健康监控"""
        if self._health_thread is not None and self._health_thread.is_alive():
            self._health_thread.join(timeout=2)

    def _health_monitor_loop(self) -> None:
        """健康监控循环"""
        while not self._stop_event.is_set() and self._status.is_connected:
            time.sleep(10)

            if self._stop_event.is_set():
                break

            # 检查连接健康
            if not self._ssh_client.check_health():
                logger.warning("检测到连接异常")
                self._on_connection_lost()
                break

    def _on_connection_lost(self) -> None:
        """连接丢失处理"""
        if not self._reconnect_config.enabled:
            self._status.set_error("连接已断开")
            self._notify_status_change()
            return

        # 启动自动重连
        self._start_reconnect()

    def _start_reconnect(self) -> None:
        """启动自动重连"""
        if self._reconnect_thread is not None and self._reconnect_thread.is_alive():
            return

        self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self._reconnect_thread.start()

    def _stop_reconnect(self) -> None:
        """停止重连"""
        if self._reconnect_thread is not None and self._reconnect_thread.is_alive():
            self._reconnect_thread.join(timeout=2)

    def _reconnect_loop(self) -> None:
        """重连循环"""
        attempt = 0
        max_attempts = self._reconnect_config.max_attempts
        interval = self._reconnect_config.interval

        while attempt < max_attempts and not self._stop_event.is_set():
            attempt += 1
            self._status.set_reconnecting(attempt)
            self._notify_status_change()

            logger.info(f"尝试重连 ({attempt}/{max_attempts})...")

            # 清理现有资源
            self._forwarder.stop()
            self._ssh_client.disconnect()

            time.sleep(interval)

            if self._stop_event.is_set():
                break

            # 尝试重连
            success, error = self._do_connect()

            if success:
                logger.info("重连成功")
                self._notify_status_change()
                self._start_health_monitor()
                return

            logger.warning(f"重连失败: {error}")

        # 重连失败
        self._status.set_error(f"重连失败，已尝试 {attempt} 次")
        self._notify_status_change()

    def _open_browser(self) -> None:
        """打开浏览器"""
        if self._config is None:
            return

        url = f"http://localhost:{self._config.local_port}"
        try:
            # 使用新标签页打开，避免影响现有浏览器会话
            webbrowser.open(url, new=1, autoraise=True)
            logger.info(f"已打开浏览器: {url}")
        except Exception as e:
            logger.error(f"打开浏览器失败: {e}")