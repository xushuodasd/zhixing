"""记忆接口：Agent 会话状态的可插拔协议。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from zhixing.core.types import Message


@runtime_checkable
class Memory(Protocol):
    """记忆协议：定义 Agent 会话状态的读写契约。

    实现方负责维护消息序列的生命周期（如 InMemoryMemory 及后续的
    持久化后端）；Agent 循环只依赖本协议，不感知具体存储形态。

    方法约定：

    - ``append``：按发生顺序追加一条消息；
    - ``messages``：返回当前全部消息，建议返回快照副本，
      避免调用方修改影响内部状态；
    - ``clear``：清空全部记忆。
    """

    def append(self, message: Message) -> None:
        """追加一条消息到记忆末尾。"""
        ...

    def messages(self) -> list[Message]:
        """返回当前记忆中的全部消息（建议快照副本）。"""
        ...

    def clear(self) -> None:
        """清空全部记忆。"""
        ...
