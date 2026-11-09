"""工具模块：工具声明、注册与安全执行。

- :mod:`zhixing.tools.base`：:class:`Tool` 数据类与 :func:`tool` 装饰器；
- :mod:`zhixing.tools.registry`：:class:`ToolRegistry` 注册表。
"""

from zhixing.tools.base import Tool, tool
from zhixing.tools.registry import ToolRegistry

__all__ = [
    "Tool",
    "ToolRegistry",
    "tool",
]
