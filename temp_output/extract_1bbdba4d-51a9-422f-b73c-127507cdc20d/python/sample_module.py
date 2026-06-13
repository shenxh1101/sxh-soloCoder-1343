"""
样本Python模块，用于测试文档生成器。

这个模块包含了各种Python代码结构，包括类、函数、
异常处理和文档字符串示例。

@author: Test Author
@version: 1.0.0
"""

from typing import List, Optional, Dict, Any
import math


class Calculator:
    """
    一个简单的计算器类，支持基本的数学运算。

    这个类展示了如何使用Python的类和方法，
    以及各种类型的文档字符串标签。

    @since: 1.0.0
    @see: MathUtil
    """

    def __init__(self, precision: int = 2):
        """
        初始化计算器。

        @param precision: 计算结果的小数位数，默认为2
        @type precision: int
        """
        self.precision = precision
        self._memory = 0.0

    def add(self, a: float, b: float) -> float:
        """
        两个数相加。

        @param a: 第一个加数
        @param b: 第二个加数
        @return: 两数之和
        @rtype: float

        @example:
        >>> calc = Calculator()
        >>> calc.add(2, 3)
        5.0
        """
        return round(a + b, self.precision)

    def divide(self, a: float, b: float) -> float:
        """
        两个数相除。

        @param a: 被除数
        @param b: 除数
        @return: 两数之商
        @rtype: float
        @raises ZeroDivisionError: 当除数为0时抛出

        @example:
        >>> calc = Calculator()
        >>> calc.divide(10, 2)
        5.0
        """
        if b == 0:
            raise ZeroDivisionError("除数不能为零")
        return round(a / b, self.precision)

    @property
    def memory(self) -> float:
        """获取当前内存中的值。"""
        return self._memory

    @memory.setter
    def memory(self, value: float):
        """设置内存中的值。"""
        self._memory = value


class MathUtil:
    """数学工具类，提供常用的数学函数。"""

    @staticmethod
    def fibonacci(n: int) -> List[int]:
        """
        生成斐波那契数列。

        @param n: 要生成的数列长度
        @return: 斐波那契数列
        @rtype: List[int]
        @raises ValueError: 当n小于0时抛出
        """
        if n < 0:
            raise ValueError("n不能为负数")
        if n == 0:
            return []
        if n == 1:
            return [0]
        
        result = [0, 1]
        for i in range(2, n):
            result.append(result[i-1] + result[i-2])
        return result


def greet(name: str, greeting: str = "Hello") -> str:
    """
    生成问候语。

    @param name: 要问候的人的名字
    @param greeting: 问候语，默认为"Hello"
    @return: 完整的问候语字符串
    @rtype: str
    """
    return f"{greeting}, {name}!"


async def fetch_data(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    异步获取数据（示例）。

    @param url: 数据的URL地址
    @param timeout: 超时时间（秒），默认为30
    @return: 解析后的JSON数据
    @rtype: Dict[str, Any]
    @raises TimeoutError: 当请求超时时抛出
    """
    pass
