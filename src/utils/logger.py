"""
日志工具模块

提供统一的日志记录功能，支持文件日志和控制台输出。
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """
    统一日志记录器

    支持:
    - 控制台输出（彩色）
    - 文件日志（按日期滚动）
    - 日志级别过滤
    """

    _instance: Optional['Logger'] = None
    _initialized: bool = False

    def __new__(cls) -> 'Logger':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化日志器"""
        if self._initialized:
            return

        self._initialized = True
        self._logger = logging.getLogger("GatewayMapper")
        self._logger.setLevel(logging.DEBUG)

        # 避免重复添加 handler
        if self._logger.handlers:
            self._logger.handlers.clear()

        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # 文件处理器
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"gatewaymapper_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """记录调试信息"""
        self._logger.debug(message)

    def info(self, message: str) -> None:
        """记录一般信息"""
        self._logger.info(message)

    def warning(self, message: str) -> None:
        """记录警告信息"""
        self._logger.warning(message)

    def error(self, message: str) -> None:
        """记录错误信息"""
        self._logger.error(message)

    def critical(self, message: str) -> None:
        """记录严重错误"""
        self._logger.critical(message)

    def exception(self, message: str) -> None:
        """记录异常信息（包含堆栈跟踪）"""
        self._logger.exception(message)


# 全局日志实例
logger = Logger()


def get_logger() -> Logger:
    """获取全局日志实例"""
    return logger