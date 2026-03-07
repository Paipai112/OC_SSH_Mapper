"""
系统托盘服务模块

管理系统托盘图标和菜单。
"""

import threading
from typing import Optional, Callable

import pystray
from PIL import Image, ImageDraw

from src.utils.logger import get_logger

logger = get_logger()


class SystemTrayService:
    """
    系统托盘服务

    功能:
    - 托盘图标管理
    - 右键菜单
    - 状态切换
    """

    def __init__(
        self,
        on_show: Optional[Callable] = None,
        on_exit: Optional[Callable] = None
    ):
        """
        初始化系统托盘

        Args:
            on_show: 显示窗口回调
            on_exit: 退出应用回调
        """
        self._on_show = on_show
        self._on_exit = on_exit
        self._is_connected = False
        self._tray: Optional[pystray.Icon] = None
        self._running = False

    def start(self) -> None:
        """启动托盘服务"""
        if self._running:
            return

        self._running = True

        # 创建托盘图标
        icon = self._create_icon(connected=False)

        # 创建菜单
        menu = pystray.Menu(
            pystray.MenuItem("显示窗口", self._show_window, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出程序", self._exit_app)
        )

        # 创建托盘实例
        self._tray = pystray.Icon(
            "GatewayMapper",
            icon,
            "GatewayMapper - 未连接",
            menu
        )

        # 在后台线程运行
        threading.Thread(target=self._tray.run, daemon=True).start()
        logger.info("系统托盘已启动")

    def stop(self) -> None:
        """停止托盘服务"""
        if not self._running:
            return

        self._running = False

        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass

        logger.info("系统托盘已停止")

    def set_connected(self) -> None:
        """设置已连接状态"""
        self._is_connected = True
        self._update_icon()

    def set_disconnected(self) -> None:
        """设置已断开状态"""
        self._is_connected = False
        self._update_icon()

    def _create_icon(self, connected: bool = False) -> Image.Image:
        """
        创建托盘图标

        Args:
            connected: 是否已连接

        Returns:
            PIL Image 对象
        """
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 绘制圆形图标
        if connected:
            # 绿色 - 已连接
            color = (76, 175, 80, 255)
        else:
            # 红色 - 未连接
            color = (244, 67, 54, 255)

        # 绘制圆形
        margin = 8
        draw.ellipse(
            (margin, margin, width - margin, height - margin),
            fill=color
        )

        # 绘制内部图案（表示隧道）
        center = width // 2
        if connected:
            # 绘制连接符号
            draw.line((margin + 10, center, center - 5, center), fill=(255, 255, 255, 255), width=3)
            draw.line((center + 5, center, width - margin - 10, center), fill=(255, 255, 255, 255), width=3)
            draw.ellipse((center - 5, center - 5, center + 5, center + 5), fill=(255, 255, 255, 255))
        else:
            # 绘制断开符号
            draw.line((margin + 10, center - 5, width - margin - 10, center + 5), fill=(255, 255, 255, 255), width=3)

        return image

    def _update_icon(self) -> None:
        """更新托盘图标"""
        if self._tray is None:
            return

        try:
            icon = self._create_icon(self._is_connected)
            self._tray.icon = icon
            self._tray.title = f"GatewayMapper - {'已连接' if self._is_connected else '未连接'}"
        except Exception as e:
            logger.error(f"更新托盘图标失败: {e}")

    def _show_window(self, icon=None, _item=None) -> None:
        """显示窗口"""
        if self._on_show:
            self._on_show()

    def _exit_app(self, icon=None, _item=None) -> None:
        """退出应用"""
        if self._on_exit:
            self._on_exit()