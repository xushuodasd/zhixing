"""记忆模块：会话状态的可插拔协议与内存实现。

- :mod:`zhixing.memory.base`：:class:`Memory` 协议；
- :mod:`zhixing.memory.in_memory`：:class:`InMemoryMemory` 内存实现。
"""

from zhixing.memory.base import Memory
from zhixing.memory.in_memory import InMemoryMemory

__all__ = [
    "InMemoryMemory",
    "Memory",
]
