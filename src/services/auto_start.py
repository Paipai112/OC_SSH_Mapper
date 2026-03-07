"""
开机启动服务模块

管理 Windows 开机自启动。
"""

import sys
import platform
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger()


class AutoStartService:
    """
    开机启动服务

    支持:
    - Windows 注册表
    - Linux systemd (可选)
    - macOS LaunchAgent (可选)
    """

    def __init__(self):
        """初始化开机启动服务"""
        self._platform = platform.system()

    def is_enabled(self) -> bool:
        """
        检查是否已启用开机启动

        Returns:
            是否已启用
        """
        if self._platform == "Windows":
            return self._check_windows()
        elif self._platform == "Linux":
            return self._check_linux()
        elif self._platform == "Darwin":
            return self._check_macos()
        return False

    def enable(self) -> tuple[bool, str]:
        """
        启用开机启动

        Returns:
            (是否成功, 错误信息)
        """
        if self._platform == "Windows":
            return self._enable_windows()
        elif self._platform == "Linux":
            return self._enable_linux()
        elif self._platform == "Darwin":
            return self._enable_macos()
        return False, "不支持的平台"

    def disable(self) -> tuple[bool, str]:
        """
        禁用开机启动

        Returns:
            (是否成功, 错误信息)
        """
        if self._platform == "Windows":
            return self._disable_windows()
        elif self._platform == "Linux":
            return self._disable_linux()
        elif self._platform == "Darwin":
            return self._disable_macos()
        return False, "不支持的平台"

    # ========== Windows 实现 ==========

    def _check_windows(self) -> bool:
        """检查 Windows 注册表"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, "GatewayMapper")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception as e:
            logger.error(f"检查注册表失败: {e}")
            return False

    def _enable_windows(self) -> tuple[bool, str]:
        """启用 Windows 开机启动"""
        try:
            import winreg

            # 获取可执行文件路径
            if getattr(sys, 'frozen', False):
                # 打包后的 exe
                exe_path = sys.executable
            else:
                # 开发模式，使用 pythonw 运行主脚本
                main_script = Path(__file__).parent.parent / "main.py"
                exe_path = f'pythonw "{main_script}"'

            # 写入注册表
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, "GatewayMapper", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)

            logger.info("已启用开机启动")
            return True, ""

        except Exception as e:
            error = f"启用开机启动失败: {e}"
            logger.error(error)
            return False, error

    def _disable_windows(self) -> tuple[bool, str]:
        """禁用 Windows 开机启动"""
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE
            )
            try:
                winreg.DeleteValue(key, "GatewayMapper")
                logger.info("已禁用开机启动")
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
            return True, ""

        except Exception as e:
            error = f"禁用开机启动失败: {e}"
            logger.error(error)
            return False, error

    # ========== Linux 实现 ==========

    def _check_linux(self) -> bool:
        """检查 Linux systemd 服务"""
        desktop_file = Path.home() / ".config" / "autostart" / "gatewaymapper.desktop"
        return desktop_file.exists()

    def _enable_linux(self) -> tuple[bool, str]:
        """启用 Linux 开机启动"""
        try:
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)

            desktop_file = autostart_dir / "gatewaymapper.desktop"

            # 获取可执行文件路径
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                main_script = Path(__file__).parent.parent / "main.py"
                exe_path = f"python3 {main_script}"

            desktop_content = f"""[Desktop Entry]
Type=Application
Name=GatewayMapper
Exec={exe_path}
Icon=gatewaymapper
Comment=SSH Port Forwarding Tool
Terminal=false
Categories=Network;
"""
            desktop_file.write_text(desktop_content)
            logger.info("已启用开机启动")
            return True, ""

        except Exception as e:
            error = f"启用开机启动失败: {e}"
            logger.error(error)
            return False, error

    def _disable_linux(self) -> tuple[bool, str]:
        """禁用 Linux 开机启动"""
        try:
            desktop_file = Path.home() / ".config" / "autostart" / "gatewaymapper.desktop"
            if desktop_file.exists():
                desktop_file.unlink()
            logger.info("已禁用开机启动")
            return True, ""
        except Exception as e:
            error = f"禁用开机启动失败: {e}"
            logger.error(error)
            return False, error

    # ========== macOS 实现 ==========

    def _check_macos(self) -> bool:
        """检查 macOS LaunchAgent"""
        plist_file = Path.home() / "Library" / "LaunchAgents" / "com.gatewaymapper.plist"
        return plist_file.exists()

    def _enable_macos(self) -> tuple[bool, str]:
        """启用 macOS 开机启动"""
        # 留作后续实现
        return False, "macOS 支持尚未实现"

    def _disable_macos(self) -> tuple[bool, str]:
        """禁用 macOS 开机启动"""
        # 留作后续实现
        return False, "macOS 支持尚未实现"