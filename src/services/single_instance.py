"""
单实例检查模块

防止应用被重复启动多个实例。
"""

import sys
import socket
from typing import Optional, Tuple

from src.utils.logger import get_logger

logger = get_logger()

# 用于单实例检查的本地 socket 端口
SINGLE_INSTANCE_PORT = 18790


class SingleInstanceChecker:
    """
    单实例检查器

    使用本地 socket 端口检测是否已有实例运行。
    """

    # 类变量，可被测试覆盖
    SINGLE_INSTANCE_PORT = 18790

    def __init__(self, port: int = None):
        """
        初始化单实例检查器

        Args:
            port: 可选的端口号，默认使用 SINGLE_INSTANCE_PORT
        """
        self._socket: Optional[socket.socket] = None
        self._is_running = False
        self._port = port if port is not None else self.SINGLE_INSTANCE_PORT

    def check_and_acquire(self) -> Tuple[bool, str]:
        """
        检查是否已有实例运行并尝试获取锁

        Returns:
            (是否成功获取锁，错误信息)
        """
        try:
            # 尝试创建监听 socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 注意：不使用 SO_REUSEADDR，否则无法检测到重复实例
            # self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # 尝试绑定端口
            self._socket.bind(("127.0.0.1", self._port))
            self._socket.listen(1)

            # 绑定成功，说明我们是第一个实例
            self._is_running = True
            logger.info("单实例检查通过：当前是唯一的实例")
            return True, ""

        except OSError as e:
            if e.errno in (10048, 98):  # 端口已被占用 (Windows/Linux)
                logger.warning("检测到已有实例运行")
                return False, "检测到 GatewayMapper 已在运行中，请勿重复启动"
            else:
                logger.error(f"单实例检查出错：{e}")
                return False, f"单实例检查失败：{e}"

        except Exception as e:
            logger.error(f"单实例检查出错：{e}")
            return False, f"单实例检查失败：{e}"

    def release(self) -> None:
        """释放单实例锁"""
        if self._socket is not None:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
        self._is_running = False
        logger.debug("已释放单实例锁")


# 全局单实例检查器实例
_checker: Optional[SingleInstanceChecker] = None


def get_single_instance_checker() -> SingleInstanceChecker:
    """获取全局单实例检查器实例"""
    global _checker
    if _checker is None:
        _checker = SingleInstanceChecker()
    return _checker


def check_single_instance() -> Tuple[bool, str]:
    """
    检查单实例并获取锁

    Returns:
        (是否成功，错误信息)
    """
    return get_single_instance_checker().check_and_acquire()


def release_single_instance() -> None:
    """释放单实例锁"""
    get_single_instance_checker().release()
