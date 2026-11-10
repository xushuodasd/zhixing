"""Provider 协议：模型服务的统一抽象。

Agent 循环只依赖本协议（依赖倒置）：生产环境用 OpenAI 兼容实现，
离线测试与演示用脚本化的 FakeProvider；接入新厂商 = 新增一个本协议的
实现，不改动 Agent 与工具层。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from zhixing.core.types import Message, ProviderResponse


@runtime_checkable
class Provider(Protocol):
    """模型服务协议：把对话消息补全为模型响应。

    方法约定：

    - ``messages``：完整对话消息列表（system / user / assistant / tool），
      实现方负责转换为自家 API 的请求格式；
    - ``tools``：可选的工具 schema 列表，形态为
      :meth:`zhixing.tools.registry.ToolRegistry.schemas` 的输出
      （OpenAI function calling 形态）；``None`` 或空列表表示本轮不带工具；
    - 失败语义：网络错误、超时、非 2xx 响应等一律抛出
      :class:`~zhixing.core.exceptions.ProviderError`，不返回错误值、
      不返回 ``None``。

    Returns:
        Provider 无关的统一响应（消息 + 停止原因）。

    Raises:
        ProviderError: 一切调用失败场景。
    """

    def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, object]] | None = None,
    ) -> ProviderResponse:
        """执行一次对话补全。"""
        ...
