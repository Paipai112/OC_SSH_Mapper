"""
访问控制模块

实现白名单机制和端口限制。
"""

from typing import List, Set, Optional
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class AccessRule:
    """访问规则"""
    allowed_remote_hosts: Set[str]
    allowed_remote_ports: Set[int]
    allow_all_hosts: bool = False
    allow_all_ports: bool = False


class AccessControl:
    """
    访问控制器

    功能:
    - 白名单主机检查
    - 端口范围限制
    - 访问日志
    """

    def __init__(self, rule: Optional[AccessRule] = None):
        """
        初始化访问控制器

        Args:
            rule: 访问规则，默认允许所有访问
        """
        self._rule = rule or AccessRule(
            allowed_remote_hosts={"127.0.0.1", "localhost"},
            allowed_remote_ports=set(range(1, 65536)),
            allow_all_hosts=True,
            allow_all_ports=True
        )
        self._access_log: List[dict] = []

    def check_access(self, remote_host: str, remote_port: int) -> tuple[bool, str]:
        """
        检查访问权限

        Args:
            remote_host: 远程主机
            remote_port: 远程端口

        Returns:
            (是否允许, 拒绝原因)
        """
        # 检查主机
        if not self._rule.allow_all_hosts:
            if remote_host not in self._rule.allowed_remote_hosts:
                reason = f"主机 {remote_host} 不在白名单中"
                self._log_access(remote_host, remote_port, False, reason)
                return False, reason

        # 检查端口
        if not self._rule.allow_all_ports:
            if remote_port not in self._rule.allowed_remote_ports:
                reason = f"端口 {remote_port} 不在允许范围内"
                self._log_access(remote_host, remote_port, False, reason)
                return False, reason

        self._log_access(remote_host, remote_port, True)
        return True, ""

    def _log_access(
        self,
        host: str,
        port: int,
        allowed: bool,
        reason: str = ""
    ) -> None:
        """记录访问日志"""
        from datetime import datetime

        entry = {
            "timestamp": datetime.now().isoformat(),
            "host": host,
            "port": port,
            "allowed": allowed,
            "reason": reason
        }
        self._access_log.append(entry)

        if allowed:
            logger.debug(f"访问允许: {host}:{port}")
        else:
            logger.warning(f"访问拒绝: {host}:{port} - {reason}")

    def get_access_log(self) -> List[dict]:
        """获取访问日志"""
        return self._access_log.copy()

    def clear_access_log(self) -> None:
        """清空访问日志"""
        self._access_log.clear()

    def update_rule(self, rule: AccessRule) -> None:
        """更新访问规则"""
        self._rule = rule
        logger.info("访问规则已更新")


# 默认访问规则：仅允许本地回环
DEFAULT_RULE = AccessRule(
    allowed_remote_hosts={"127.0.0.1", "localhost"},
    allowed_remote_ports=set(range(1, 65536)),
    allow_all_hosts=False,
    allow_all_ports=True
)