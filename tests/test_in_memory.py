"""InMemoryMemory 测试：追加、快照读取与清空语义。"""

from zhixing import InMemoryMemory, Memory, Message


def test_append_then_messages_returns_all_in_order() -> None:
    """按顺序追加的消息在读取时保持原序与原内容。"""
    memory = InMemoryMemory()
    memory.append(Message.user("你好"))
    memory.append(Message.assistant("你好，我是知行。"))

    snapshot = memory.messages()
    assert [m.role for m in snapshot] == ["user", "assistant"]
    assert snapshot[0].content == "你好"
    assert snapshot[1].content == "你好，我是知行。"


def test_messages_returns_snapshot_copy() -> None:
    """messages 返回快照副本：修改返回值不影响记忆内部状态。"""
    memory = InMemoryMemory()
    memory.append(Message.user("你好"))

    snapshot = memory.messages()
    snapshot.append(Message.user("外部伪造的消息"))
    snapshot.clear()

    assert [m.content for m in memory.messages()] == ["你好"]


def test_clear_empties_memory() -> None:
    """clear 后记忆为空。"""
    memory = InMemoryMemory()
    memory.append(Message.user("你好"))
    memory.append(Message.assistant("你好"))

    memory.clear()

    assert memory.messages() == []


def test_clear_is_idempotent() -> None:
    """对空记忆重复 clear 同样安全。"""
    memory = InMemoryMemory()

    memory.clear()
    memory.clear()

    assert memory.messages() == []


def test_satisfies_memory_protocol() -> None:
    """InMemoryMemory 是 Memory 协议的合法实现（结构化子类型）。"""
    assert isinstance(InMemoryMemory(), Memory)
