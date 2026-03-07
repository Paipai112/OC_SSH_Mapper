"""
SSH 客户端模块

封装 Paramiko SSH 连接功能。
"""

import socket
import paramiko
from paramiko.ssh_exception import AuthenticationException, SSHException, BadHostKeyException
from typing import Optional, Tuple
from pathlib import Path

from src.models.connection_config import ConnectionConfig, AuthType
from src.utils.logger import get_logger

logger = get_logger()


class SSHClient:
    """
    SSH 客户端封装

    功能:
    - 建立 SSH 连接
    - 支持密码和密钥认证
    - 获取传输通道
    - 健康检查
    """

    def __init__(self):
        """初始化 SSH 客户端"""
        self._client: Optional[paramiko.SSHClient] = None
        self._config: Optional[ConnectionConfig] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        if self._client is None:
            return False
        transport = self._client.get_transport()
        return transport is not None and transport.is_active()

    @property
    def transport(self) -> Optional[paramiko.Transport]:
        """获取 SSH 传输通道"""
        if self._client is None:
            return None
        return self._client.get_transport()

    def connect(self, config: ConnectionConfig, timeout: int = 10) -> Tuple[bool, str]:
        """
        建立 SSH 连接

        Args:
            config: 连接配置
            timeout: 连接超时时间（秒）

        Returns:
            (是否成功, 错误信息)
        """
        try:
            # 断开现有连接
            if self._client is not None:
                self.disconnect()

            self._config = config
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 根据认证类型选择认证方式
            if config.auth_type == AuthType.KEY_FILE:
                # 密钥认证
                key_path = Path(config.key_file_path).expanduser()
                if not key_path.exists():
                    return False, f"密钥文件不存在: {key_path}"

                logger.info(f"使用密钥认证连接 {config.ssh_host}")
                self._client.connect(
                    hostname=config.ssh_host,
                    port=config.ssh_port,
                    username=config.ssh_user,
                    key_filename=str(key_path),
                    timeout=timeout,
                    allow_agent=False,
                    look_for_keys=False
                )
            else:
                # 密码认证
                if not config.password:
                    return False, "密码不能为空"

                logger.info(f"使用密码认证连接 {config.ssh_host}")
                self._client.connect(
                    hostname=config.ssh_host,
                    port=config.ssh_port,
                    username=config.ssh_user,
                    password=config.password,
                    timeout=timeout,
                    allow_agent=False,
                    look_for_keys=False
                )

            self._connected = True
            logger.info(f"SSH 连接成功: {config.ssh_user}@{config.ssh_host}:{config.ssh_port}")
            return True, ""

        except AuthenticationException as e:
            error_msg = "认证失败：用户名或密码错误"
            logger.error(error_msg)
            return False, error_msg

        except BadHostKeyException as e:
            error_msg = f"主机密钥验证失败: {e}"
            logger.error(error_msg)
            return False, error_msg

        except SSHException as e:
            error_msg = f"SSH 错误: {e}"
            logger.error(error_msg)
            return False, error_msg

        except socket.timeout:
            error_msg = "连接超时，请检查网络或服务器地址"
            logger.error(error_msg)
            return False, error_msg

        except socket.gaierror as e:
            error_msg = f"无法解析主机名: {config.ssh_host}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"连接失败: {e}"
            logger.exception(error_msg)
            return False, error_msg

    def disconnect(self) -> None:
        """断开 SSH 连接"""
        if self._client is not None:
            try:
                self._client.close()
                logger.info("SSH 连接已断开")
            except Exception as e:
                logger.warning(f"断开连接时出错: {e}")
            finally:
                self._client = None
                self._connected = False

    def check_health(self) -> bool:
        """
        检查连接健康状态

        Returns:
            连接是否健康
        """
        if self._client is None:
            return False

        transport = self._client.get_transport()
        if transport is None:
            return False

        try:
            # 发送心跳包检测连接
            transport.send_ignore()
            return True
        except Exception:
            return False

    def exec_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """
        执行远程命令

        Args:
            command: 要执行的命令
            timeout: 超时时间

        Returns:
            (返回码, 标准输出, 标准错误)
        """
        if not self.is_connected:
            raise RuntimeError("SSH 未连接")

        logger.debug(f"执行命令: {command}")
        stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)

        exit_code = stdout.channel.recv_exit_status()
        stdout_text = stdout.read().decode('utf-8', errors='replace')
        stderr_text = stderr.read().decode('utf-8', errors='replace')

        return exit_code, stdout_text, stderr_text