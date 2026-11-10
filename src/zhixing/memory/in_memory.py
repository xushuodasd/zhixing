"""内存记忆实现：单进程内以列表维护会话消息。

这是 :class:`~zhixing.memory.base.Memory` 协议的参考实现——足够简单、
零依赖，覆盖"多轮对话保持上下文"的基本诉求；需要持久化或跨进程共享时，
按同一协议实现新后端即可，Agent 循环不感知差异。
"""

from __future__ import annotations

from zhixing.core.types import Message


class InMemoryMemory:
    """基于列表的内存记忆（:class:`~zhixing.memory.base.Memory` 协议实现）。

    语义约定：

    - ``append``：按发生顺序追加一条消息到末尾；
    - ``messages``：返回当前全部消息的**快照副本**——外部对返回列表的
      修改（增删元素）不会影响记忆内部状态；
    - ``clear``：清空全部记忆，可重复调用。

    线程安全边界：本实现面向**单线程**使用，内部是普通 ``list``，不做
    任何加锁；多线程共享同一实例可能出现竞态。并发场景请为每个线程（或
    每次会话）持有独立实例，或在外部自行序列化访问。

    用法::

        memory = InMemoryMemory()
        memory.append(Message.user("你好"))
        memory.messages()  # [Message(role="user", content="你好")]
    """

    def __init__(self) -> None:
        """初始化一条空记忆。"""
        self._messages: list[Message] = []

    def append(self, message: Message) -> None:
        """按发生顺序追加一条消息到记忆末尾。

        Args:
            message: 待追加的消息。
        """
        self._messages.append(message)

    def messages(self) -> list[Message]:
        """返回当前记忆中全部消息的快照副本（外部修改不影响内部状态）。

        Returns:
            按追加顺序排列的消息列表副本。
        """
        return list(self._messages)

    def clear(self) -> None:
        """清空全部记忆（幂等：对空记忆重复调用同样安全）。"""
        self._messages.clear()
