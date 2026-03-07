"""
连接配置数据模型

定义 SSH 连接配置的数据结构。
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class AuthType(Enum):
    """认证类型"""
    PASSWORD = "password"
    KEY_FILE = "key_file"


@dataclass
class ConnectionConfig:
    """
    连接配置数据模型

    Attributes:
        name: 配置名称（用于预设）
        ssh_host: SSH 服务器地址
        ssh_port: SSH 端口
        ssh_user: SSH 用户名
        local_port: 本地监听端口
        remote_host: 远程目标主机
        remote_port: 远程目标端口
        auth_type: 认证类型
        password: 密码（明文，运行时使用）
        encrypted_password: 加密后的密码（存储用）
        key_file_path: 私钥文件路径
        remember_password: 是否记住密码
    """
    name: str = "默认配置"
    ssh_host: str = ""
    ssh_port: int = 22
    ssh_user: str = "root"
    local_port: int = 18789
    remote_host: str = "127.0.0.1"
    remote_port: int = 18789
    auth_type: AuthType = AuthType.PASSWORD
    password: str = ""
    encrypted_password: str = ""
    key_file_path: str = ""
    remember_password: bool = False

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "ssh_host": self.ssh_host,
            "ssh_port": self.ssh_port,
            "ssh_user": self.ssh_user,
            "local_port": self.local_port,
            "remote_host": self.remote_host,
            "remote_port": self.remote_port,
            "auth_type": self.auth_type.value,
            "encrypted_password": self.encrypted_password,
            "key_file_path": self.key_file_path,
            "remember_password": self.remember_password
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConnectionConfig':
        """从字典创建实例"""
        auth_type = AuthType.PASSWORD
        if data.get("auth_type"):
            try:
                auth_type = AuthType(data["auth_type"])
            except ValueError:
                pass

        return cls(
            name=data.get("name", "默认配置"),
            ssh_host=data.get("ssh_host", ""),
            ssh_port=data.get("ssh_port", 22),
            ssh_user=data.get("ssh_user", "root"),
            local_port=data.get("local_port", 18789),
            remote_host=data.get("remote_host", "127.0.0.1"),
            remote_port=data.get("remote_port", 18789),
            auth_type=auth_type,
            encrypted_password=data.get("encrypted_password", ""),
            key_file_path=data.get("key_file_path", ""),
            remember_password=data.get("remember_password", False)
        )

    def validate(self) -> tuple[bool, str]:
        """
        验证配置有效性

        Returns:
            (是否有效, 错误信息)
        """
        if not self.ssh_host:
            return False, "服务器地址不能为空"

        if not (1 <= self.ssh_port <= 65535):
            return False, "SSH 端口必须在 1-65535 之间"

        if not (1 <= self.local_port <= 65535):
            return False, "本地端口必须在 1-65535 之间"

        if not (1 <= self.remote_port <= 65535):
            return False, "远程端口必须在 1-65535 之间"

        if not self.ssh_user:
            return False, "用户名不能为空"

        if self.auth_type == AuthType.KEY_FILE and not self.key_file_path:
            return False, "密钥文件路径不能为空"

        return True, ""