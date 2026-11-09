"""记忆模块：会话状态的可插拔协议与实现。

当前提供 :class:`~zhixing.memory.base.Memory` 协议；具体实现
（如 InMemoryMemory）由后续里程碑补齐。
"""

from zhixing.memory.base import Memory

__all__ = [
    "Memory",
]
