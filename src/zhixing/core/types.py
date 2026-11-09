"""核心数据类型：对话消息、工具调用与 Provider 响应。

本模块定义 Agent 运行时在"对话"与"工具调用"两条主线上的最小数据形态，
是全框架的通用语言：Provider 适配层负责把各家 API 的响应映射为这里的
:class:`ProviderResponse`；Agent 循环、记忆与工具注册表都围绕这些类型协作。

类型约定（与主流大模型 API 对齐）：

- ``role`` 取 ``"system"`` / ``"user"`` / ``"assistant"`` / ``"tool"`` 四种；
- 助手消息通过 ``tool_calls`` 携带模型发起的工具调用列表；
- 工具结果以 ``role="tool"``、``tool_call_id`` 与 ``content`` 回传给模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ToolCall:
    """一次工具调用请求（通常由模型在助手消息中发起）。

    Attributes:
        id: 调用唯一标识，用于把工具结果回填到对应的调用上。
        name: 被调用工具的名称。
        arguments: 调用参数，键为参数名，值为 JSON 兼容的标量或容器。
    """

    id: str
    name: str
    arguments: dict[str, object] = field(default_factory=dict)


@dataclass
class Message:
    """对话消息（Provider 无关的统一形态）。

    Attributes:
        role: 消息角色，``"system"`` / ``"user"`` / ``"assistant"`` / ``"tool"``。
        content: 文本内容；纯工具调用消息可为 ``None``。
        tool_calls: 助手消息携带的工具调用列表；其他角色为 ``None``。
        tool_call_id: 工具结果消息对应的调用 id；其他角色为 ``None``。
    """

    role: str
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None

    @classmethod
    def system(cls, content: str) -> Message:
        """构造 system 消息（设定 Agent 的身份与行为约束）。"""
        return cls(role="system", content=content)

    @classmethod
    def user(cls, content: str) -> Message:
        """构造 user 消息（用户输入）。"""
        return cls(role="user", content=content)

    @classmethod
    def assistant(
        cls,
        content: str | None = None,
        tool_calls: list[ToolCall] | None = None,
    ) -> Message:
        """构造 assistant 消息（模型回复，可携带工具调用列表）。"""
        return cls(role="assistant", content=content, tool_calls=tool_calls)

    @classmethod
    def tool(cls, tool_call_id: str, content: str) -> Message:
        """构造 tool 消息（工具结果回传，``tool_call_id`` 指向对应调用）。"""
        return cls(role="tool", content=content, tool_call_id=tool_call_id)


@dataclass
class ToolResult:
    """一次工具调用的执行结果。

    Attributes:
        tool_call_id: 对应的 :class:`ToolCall.id`；注册表层面尚无调用 id
            时以空字符串占位，由 Agent 循环在回填消息时补齐。
        content: 结果内容（字符串形态，供模型阅读）。
        is_error: 是否为失败结果；失败不代表抛异常，而是显式标记。
    """

    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class ProviderResponse:
    """模型服务的统一响应形态。

    Attributes:
        message: 模型回复的消息（可能含文本、工具调用或两者皆有）。
        finish_reason: 原生停止原因（如 ``"stop"`` / ``"tool_calls"``），
            无法获取时为 ``None``。
    """

    message: Message
    finish_reason: str | None = None
