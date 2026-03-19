"""
GatewayMapper 应用入口

启动 SSH 端口转发工具。
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置多进程支持
import multiprocessing
multiprocessing.freeze_support()


def main():
    """应用主入口"""
    from src.utils.logger import get_logger
    from src.ui.main_window import MainWindow
    from src.services.single_instance import get_single_instance_checker, release_single_instance
    import tkinter as tk
    from tkinter import messagebox

    logger = get_logger()

    # 检查单实例
    checker = get_single_instance_checker()
    success, error = checker.check_and_acquire()
    if not success:
        # 已有实例运行
        messagebox.showerror("重复启动", error)
        logger.warning(error)
        return

    logger.info("GatewayMapper 启动中...")

    root = tk.Tk()
    app = MainWindow(root)

    # 注意：WM_DELETE_WINDOW 已经在 MainWindow._setup_root() 中设置为 _hide_to_tray
    # 窗口关闭时会隐藏到托盘，不会触发退出

    # 设置退出回调（从托盘菜单"退出程序"触发）
    def on_exit_from_tray():
        logger.info("收到退出请求...")
        # 断开连接
        if app._connection_manager.is_connected:
            app._connection_manager.disconnect()
        # 停止托盘
        app._tray.stop()
        # 停止主循环
        root.quit()
        # 销毁窗口
        root.destroy()
        # 释放单实例锁
        release_single_instance()
        logger.info("应用已退出")

    # 将退出回调注册到 MainWindow
    app._set_exit_callback(on_exit_from_tray)

    root.mainloop()

    logger.info("GatewayMapper 主循环结束")


if __name__ == "__main__":
    main()