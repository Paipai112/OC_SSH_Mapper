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
    import tkinter as tk

    logger = get_logger()
    logger.info("GatewayMapper 启动中...")

    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

    logger.info("GatewayMapper 已退出")


if __name__ == "__main__":
    main()