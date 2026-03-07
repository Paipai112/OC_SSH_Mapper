"""
端口转发器模块

实现 SSH 本地端口转发功能。
"""

import socket
import threading
import time
from typing import Optional, Callable

from src.utils.logger import get_logger
from src.utils.port_utils import check_port_available, release_port

logger = get_logger()


class PortForwarder:
    """
    端口转发器

    功能:
    - 本地端口监听
    - 通过 SSH 通道转发数据
    - 支持多连接
    - 优雅停止
    """

    def __init__(self):
        """初始化端口转发器"""
        self._server_socket: Optional[socket.socket] = None
        self._local_port: int = 0
        self._remote_host: str = ""
        self._remote_port: int = 0
        self._is_running = False
        self._accept_thread: Optional[threading.Thread] = None
        self._transport = None
        self._client_threads: list = []
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running

    @property
    def local_port(self) -> int:
        """本地监听端口"""
        return self._local_port

    def start(
        self,
        transport,
        local_port: int,
        remote_host: str,
        remote_port: int
    ) -> bool:
        """
        启动端口转发

        Args:
            transport: SSH 传输通道
            local_port: 本地监听端口
            remote_host: 远程目标主机
            remote_port: 远程目标端口

        Returns:
            是否启动成功
        """
        if self._is_running:
            logger.warning("端口转发器已在运行")
            return False

        try:
            # 检查端口是否可用
            if not check_port_available(local_port):
                logger.error(f"本地端口 {local_port} 不可用")
                return False

            self._transport = transport
            self._local_port = local_port
            self._remote_host = remote_host
            self._remote_port = remote_port

            # 创建监听 socket
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b'\x01\x00\x00\x00')
            self._server_socket.bind(("127.0.0.1", local_port))
            self._server_socket.listen(5)

            self._is_running = True

            # 启动接受连接线程
            self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self._accept_thread.start()

            logger.info(f"端口转发已启动: 127.0.0.1:{local_port} -> {remote_host}:{remote_port}")
            return True

        except Exception as e:
            logger.error(f"启动端口转发失败: {e}")
            self._cleanup()
            return False

    def stop(self) -> None:
        """停止端口转发"""
        if not self._is_running:
            return

        logger.info("正在停止端口转发...")
        self._is_running = False

        # 关闭服务器 socket
        if self._server_socket is not None:
            try:
                # 发送一个空连接来触发 accept 退出
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect(("127.0.0.1", self._local_port))
                s.close()
            except Exception:
                pass

            time.sleep(0.1)

            try:
                self._server_socket.close()
            except Exception:
                pass

            self._server_socket = None

        # 等待接受线程结束
        if self._accept_thread is not None and self._accept_thread.is_alive():
            self._accept_thread.join(timeout=2)

        # 释放端口
        release_port(self._local_port)

        logger.info("端口转发已停止")

    def _accept_loop(self) -> None:
        """接受连接循环"""
        while self._is_running:
            try:
                self._server_socket.settimeout(0.5)
                client_socket, client_addr = self._server_socket.accept()

                logger.debug(f"接受新连接: {client_addr}")

                # 启动线程处理连接
                thread = threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket,),
                    daemon=True
                )
                thread.start()

                with self._lock:
                    self._client_threads.append(thread)

            except socket.timeout:
                continue
            except Exception as e:
                if self._is_running:
                    logger.error(f"接受连接时出错: {e}")

        # 清理已结束的线程
        with self._lock:
            self._client_threads = [t for t in self._client_threads if t.is_alive()]

    def _handle_connection(self, client_socket: socket.socket) -> None:
        """
        处理单个连接

        使用双线程实现全双工通信
        """
        try:
            # 建立到远程目标的 SSH 通道
            channel = self._transport.open_channel(
                "direct-tcpip",
                (self._remote_host, self._remote_port),
                client_socket.getsockname()
            )

            if channel is None:
                logger.error("无法建立 SSH 通道")
                client_socket.close()
                return

            # 本地 -> 远程
            def forward_local_to_remote():
                try:
                    while self._is_running:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                        channel.send(data)
                except Exception:
                    pass
                finally:
                    try:
                        channel.close()
                    except Exception:
                        pass

            # 远程 -> 本地
            def forward_remote_to_local():
                try:
                    while self._is_running:
                        data = channel.recv(4096)
                        if not data:
                            break
                        client_socket.send(data)
                except Exception:
                    pass
                finally:
                    try:
                        client_socket.close()
                    except Exception:
                        pass

            # 启动双向转发线程
            t1 = threading.Thread(target=forward_local_to_remote, daemon=True)
            t2 = threading.Thread(target=forward_remote_to_local, daemon=True)
            t1.start()
            t2.start()

            # 等待两个方向都结束
            t1.join()
            t2.join()

        except Exception as e:
            logger.debug(f"处理连接时出错: {e}")
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
            try:
                channel.close()
            except Exception:
                pass

    def _cleanup(self) -> None:
        """清理资源"""
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None

        self._is_running = False