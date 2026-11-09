"""Agent 运行事件与轨迹记录：让每一步都可观测。

"每步可观测"是 zhixing 的核心卖点之一：Agent 在开始处理、调用模型、
执行工具、结束本轮的每个节点都发出事件。调用方可以用
:class:`TraceRecorder` 收集完整轨迹（事后回放/审计），也可以注入
``on_event`` 回调做实时展示（如逐步打印思考与工具执行过程）。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from zhixing.core.types import Message, ProviderResponse, ToolCall, ToolResult


@dataclass
class AgentStarted:
    """Agent 开始处理一轮用户输入。

    Attributes:
        user_input: 本轮的用户原始输入。
    """

    user_input: str


@dataclass
class LlmRequested:
    """即将调用模型：携带本次发送的完整消息列表。

    Attributes:
        messages: 发送给模型的全部消息（含系统提示、历史与工具结果）。
    """

    messages: list[Message]


@dataclass
class LlmResponded:
    """模型已返回：携带统一的响应对象。

    Attributes:
        response: Provider 无关的响应（消息 + 停止原因）。
    """

    response: ProviderResponse


@dataclass
class ToolCallStarted:
    """即将执行一次工具调用。

    Attributes:
        call: 模型发起的工具调用（名称与参数）。
    """

    call: ToolCall


@dataclass
class ToolCallFinished:
    """工具调用已结束：携带执行结果（含失败标记）。

    Attributes:
        result: 工具执行结果；``is_error=True`` 表示执行失败。
    """

    result: ToolResult


@dataclass
class AgentFinished:
    """Agent 结束本轮：携带最终答案与实际迭代次数。

    Attributes:
        answer: 给用户的最终回答。
        iterations: 本轮实际经历的模型调用次数。
    """

    answer: str
    iterations: int


#: 全部运行事件的联合类型，供 ``TraceRecorder`` 与事件回调的签名使用。
Event = (
    AgentStarted
    | LlmRequested
    | LlmResponded
    | ToolCallStarted
    | ToolCallFinished
    | AgentFinished
)


class TraceRecorder:
    """事件收集器：按发生顺序记录事件，并可实时转发给回调。

    用法::

        recorder = TraceRecorder(on_event=lambda event: print(type(event).__name__))
        recorder.record(AgentStarted(user_input="帮我查天气"))
        recorder.events  # 按序包含已发生的全部事件

    Attributes:
        events: 已记录的事件列表。这是活跃视图（每次 ``record`` 实时增长），
            读取方不应向其追加或删除元素。
    """

    def __init__(self, on_event: Callable[[Event], None] | None = None) -> None:
        """初始化记录器。

        Args:
            on_event: 可选的实时回调，签名 ``(event) -> None``；每条事件在
                完成入列后转发给它。回调抛出的异常会原样上抛（事件本身
                已入列，不会丢失），由调用方决定是否容错。
        """
        self.events: list[Event] = []
        self._on_event = on_event

    def record(self, event: Event) -> None:
        """记录一条事件：先入列，再触发 ``on_event`` 回调（如已注入）。"""
        self.events.append(event)
        if self._on_event is not None:
            self._on_event(event)
