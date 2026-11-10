"""FakeProvider 测试：脚本顺序、耗尽报错与协议兼容性（全离线）。"""

import pytest

from zhixing import FakeProvider, Message, ProviderError, ProviderResponse


def test_returns_scripted_responses_in_order() -> None:
    """按脚本顺序逐条返回，且返回的是同一对象。"""
    first = ProviderResponse(message=Message.assistant("第一句"))
    second = ProviderResponse(message=Message.assistant("第二句"))
    provider = FakeProvider([first, second])

    assert provider.complete([Message.user("问")]) is first
    assert provider.complete([Message.user("再问")]) is second


def test_empty_script_raises_immediately() -> None:
    """空脚本第一次调用就抛 ProviderError。"""
    provider = FakeProvider([])
    with pytest.raises(ProviderError, match="耗尽"):
        provider.complete([Message.user("问")])


def test_exhausted_script_raises_on_every_subsequent_call() -> None:
    """脚本耗尽后继续调用持续抛 ProviderError。"""
    provider = FakeProvider([ProviderResponse(message=Message.assistant("仅此一条"))])
    assert provider.complete([Message.user("问")]).message.content == "仅此一条"

    with pytest.raises(ProviderError, match="耗尽"):
        provider.complete([Message.user("再问")])
    with pytest.raises(ProviderError, match="耗尽"):
        provider.complete([Message.user("还要问")])


def test_accepts_tools_argument_without_effect() -> None:
    """tools 参数被接受（满足 Provider 协议），不影响脚本行为。"""
    provider = FakeProvider([ProviderResponse(message=Message.assistant("ok"))])
    response = provider.complete([Message.user("问")], [{"type": "function", "function": {}}])
    assert response.message.content == "ok"
