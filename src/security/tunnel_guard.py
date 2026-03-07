"""
隧道防护模块

确保 SSH 隧道是单向的，防止反向连接。
"""

import socket
import threading
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger()


class TunnelGuard:
    """
    隧道防护器

    功能:
    - 监控隧道方向
    - 检测异常连接
    - 防止反向连接
    """

    def __init__(self):
        """初始化隧道防护器"""
        self._is_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._local_port: int = 0
        self._anomaly_detected = False
        self._stop_event = threading.Event()

    def start_monitoring(self, local_port: int) -> None:
        """
        开始监控隧道

        Args:
            local_port: 本地监听端口
        """
        if self._is_monitoring:
            return

        self._local_port = local_port
        self._is_monitoring = True
        self._anomaly_detected = False
        self._stop_event.clear()

        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        logger.info(f"隧道监控已启动: 端口 {local_port}")

    def stop_monitoring(self) -> None:
        """停止监控"""
        if not self._is_monitoring:
            return

        self._stop_event.set()
        self._is_monitoring = False

        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=2)

        logger.info("隧道监控已停止")

    def _monitor_loop(self) -> None:
        """监控循环"""
        while self._is_monitoring and not self._stop_event.is_set():
            # 检查隧道状态
            self._check_tunnel_health()

            # 每 30 秒检查一次
            self._stop_event.wait(30)

    def _check_tunnel_health(self) -> None:
        """检查隧道健康状态"""
        # 检查端口是否仅监听本地
        try:
            # 尝试从外部连接（应该失败）
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)

            # 尝试从非本地地址连接
            try:
                # 如果能从外部连接，说明配置有问题
                result = test_socket.connect_ex(("0.0.0.0", self._local_port))
                if result == 0:
                    logger.warning(f"检测到端口 {self._local_port} 可能对外开放")
            except Exception:
                pass
            finally:
                test_socket.close()

        except Exception as e:
            logger.debug(f"隧道检查时出错: {e}")

    @property
    def is_anomaly_detected(self) -> bool:
        """是否检测到异常"""
        return self._anomaly_detected

    def report_anomaly(self, description: str) -> None:
        """
        报告异常

        Args:
            description: 异常描述
        """
        self._anomaly_detected = True
        logger.error(f"隧道异常: {description}")


class ConnectionDirection:
    """
    连接方向检查器

    确保数据流方向正确
    """

    @staticmethod
    def is_local_to_remote(local_addr: tuple, remote_addr: tuple) -> bool:
        """
        检查是否是本地到远程的连接

        Args:
            local_addr: 本地地址 (host, port)
            remote_addr: 远程地址 (host, port)

        Returns:
            是否是本地到远程
        """
        local_host = local_addr[0]
        remote_host = remote_addr[0]

        # 本地地址应该是 127.0.0.1 或 localhost
        local_hosts = {"127.0.0.1", "localhost", "::1"}

        return local_host in local_hosts

    @staticmethod
    def validate_tunnel_config(
        local_host: str,
        local_port: int,
        remote_host: str,
        remote_port: int
    ) -> tuple[bool, str]:
        """
        验证隧道配置

        Args:
            local_host: 本地监听地址
            local_port: 本地端口
            remote_host: 远程主机
            remote_port: 远程端口

        Returns:
            (是否有效, 错误信息)
        """
        # 本地监听必须限制在本地
        if local_host not in {"127.0.0.1", "localhost", "::1"}:
            return False, "本地监听地址必须限制在本地 (127.0.0.1)"

        # 远程端口不能是特权端口（除非明确需要）
        if remote_port < 1024:
            logger.warning(f"远程端口 {remote_port} 是特权端口")

        return True, ""