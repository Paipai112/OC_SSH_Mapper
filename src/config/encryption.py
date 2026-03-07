"""
密码加密模块

使用 Fernet (AES-128) 加密密码，替代不安全的 Base64 编码。
"""

import os
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet

from src.utils.logger import get_logger

logger = get_logger()


class AESCipher:
    """
    AES 加密器

    使用 Fernet (AES-128-CBC + HMAC) 进行对称加密。
    密钥由应用密钥派生，存储在用户目录中。
    """

    def __init__(self):
        """初始化加密器"""
        self._key: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None
        self._init_key()

    def _get_key_path(self) -> Path:
        """获取密钥文件路径"""
        # 存储在用户目录下，避免被普通用户访问
        key_dir = Path.home() / ".gatewaymapper"
        key_dir.mkdir(exist_ok=True)
        return key_dir / ".key"

    def _init_key(self) -> None:
        """初始化加密密钥"""
        key_path = self._get_key_path()

        if key_path.exists():
            # 加载现有密钥
            try:
                with open(key_path, "rb") as f:
                    self._key = f.read()
                self._fernet = Fernet(self._key)
                logger.debug("已加载现有加密密钥")
                return
            except Exception as e:
                logger.warning(f"加载密钥失败，将重新生成: {e}")

        # 生成新密钥
        self._key = Fernet.generate_key()
        self._fernet = Fernet(self._key)

        # 保存密钥
        try:
            with open(key_path, "wb") as f:
                f.write(self._key)
            # 设置文件权限（仅所有者可读写）
            os.chmod(key_path, 0o600)
            logger.info("已生成新的加密密钥")
        except Exception as e:
            logger.error(f"保存密钥失败: {e}")

    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串

        Args:
            plaintext: 明文字符串

        Returns:
            加密后的字符串（Base64 编码）
        """
        if not plaintext:
            return ""

        if self._fernet is None:
            raise RuntimeError("加密器未初始化")

        try:
            encrypted = self._fernet.encrypt(plaintext.encode("utf-8"))
            return encrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise

    def decrypt(self, encrypted: str) -> str:
        """
        解密字符串

        Args:
            encrypted: 加密后的字符串

        Returns:
            解密后的明文
        """
        if not encrypted:
            return ""

        if self._fernet is None:
            raise RuntimeError("加密器未初始化")

        try:
            decrypted = self._fernet.decrypt(encrypted.encode("utf-8"))
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"解密失败: {e}")
            return ""

    def is_encrypted(self, value: str) -> bool:
        """
        判断字符串是否已加密

        Fernet 加密的字符串以 'gAAAAA' 开头
        """
        if not value:
            return False
        return value.startswith("gAAAAA")


# 全局加密器实例
_cipher: Optional[AESCipher] = None


def get_cipher() -> AESCipher:
    """获取全局加密器实例"""
    global _cipher
    if _cipher is None:
        _cipher = AESCipher()
    return _cipher


def encrypt_password(password: str) -> str:
    """加密密码"""
    return get_cipher().encrypt(password)


def decrypt_password(encrypted: str) -> str:
    """解密密码"""
    return get_cipher().decrypt(encrypted)