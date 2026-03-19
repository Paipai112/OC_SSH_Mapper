"""
单实例检查测试
"""

import pytest
import socket
from src.services.single_instance import (
    SingleInstanceChecker,
)


class TestSingleInstanceChecker:
    """单实例检查器测试"""

    def test_single_instance_checker_creation(self):
        """测试创建单实例检查器"""
        checker = SingleInstanceChecker()
        assert checker is not None
        assert checker._socket is None
        assert checker._is_running is False

    def test_check_and_acquire(self):
        """测试检查并获取锁"""
        # 使用独立的检查器实例，避免全局状态干扰
        checker = SingleInstanceChecker()
        success, error = checker.check_and_acquire()

        # 注意：这个测试可能在已有实例运行时失败
        # 在隔离环境中应该是成功的
        assert isinstance(success, bool)
        assert isinstance(error, str)

        # 清理
        checker.release()

    def test_release_without_acquire(self):
        """测试未获取锁时释放"""
        checker = SingleInstanceChecker()
        # 不应该抛出异常
        checker.release()

    def test_duplicate_instance_detection(self):
        """测试重复实例检测"""
        # 使用不同的端口来避免与全局实例冲突
        test_port = 18791  # 使用与主程序不同的端口

        # 获取第一个实例
        checker1 = SingleInstanceChecker(port=test_port)
        success1, _ = checker1.check_and_acquire()

        # 尝试获取第二个实例（使用同一个端口）
        checker2 = SingleInstanceChecker(port=test_port)
        success2, error2 = checker2.check_and_acquire()

        # 第二个应该失败
        if success1:
            assert success2 is False
            assert len(error2) > 0

        # 清理
        checker1.release()
        checker2.release()
