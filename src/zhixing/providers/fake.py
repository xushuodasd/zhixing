"""脚本化假模型：离线测试与演示用的 Provider 实现。"""

from __future__ import annotations

from collections.abc import Iterable

from zhixing.core.exceptions import ProviderError
from zhixing.core.types import Message, ProviderResponse


class FakeProvider:
    """按脚本顺序返回预置响应的假模型（:class:`~zhixing.providers.base.Provider` 实现）。

    - 每次调用 :meth:`complete` 按顺序消费下一条脚本响应；
    - 脚本耗尽（或脚本为空）时抛出 :class:`ProviderError`；
    - 完全离线：不发起任何网络请求；``tools`` 参数仅被接受，不参与行为。

    用法::

        provider = FakeProvider([
            ProviderResponse(message=Message.assistant("你好")),
            ProviderResponse(message=Message.assistant(tool_calls=[...])),
        ])
    """

    def __init__(self, script: Iterable[ProviderResponse]) -> None:
        """初始化脚本化假模型。

        Args:
            script: 预置响应序列，按 ``complete`` 调用顺序逐条返回。
        """
        self._script = list(script)
        self._cursor = 0

    def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, object]] | None = None,
    ) -> ProviderResponse:
        """按顺序返回下一条脚本响应；耗尽时抛 :class:`ProviderError`。"""
        if self._cursor >= len(self._script):
            raise ProviderError(
                f"FakeProvider 脚本已耗尽（共 {len(self._script)} 条，已消费 {self._cursor} 条）"
            )
        response = self._script[self._cursor]
        self._cursor += 1
        return response
