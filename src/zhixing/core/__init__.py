"""zhixing 核心层：统一类型、事件轨迹与异常体系。

本包聚合 M2 的三类基础件：

- :mod:`zhixing.core.types`：消息与工具调用的统一数据形态；
- :mod:`zhixing.core.events`：Agent 运行事件与 :class:`TraceRecorder`；
- :mod:`zhixing.core.exceptions`：以 :class:`ZhixingError` 为根的异常体系。
"""

from zhixing.core.events import (
    AgentFinished,
    AgentStarted,
    Event,
    LlmRequested,
    LlmResponded,
    ToolCallFinished,
    ToolCallStarted,
    TraceRecorder,
)
from zhixing.core.exceptions import (
    MaxIterationsError,
    ProviderError,
    ToolExecutionError,
    ZhixingError,
)
from zhixing.core.types import Message, ProviderResponse, ToolCall, ToolResult

__all__ = [
    "AgentFinished",
    "AgentStarted",
    "Event",
    "LlmRequested",
    "LlmResponded",
    "MaxIterationsError",
    "Message",
    "ProviderError",
    "ProviderResponse",
    "ToolCall",
    "ToolCallFinished",
    "ToolCallStarted",
    "ToolExecutionError",
    "ToolResult",
    "TraceRecorder",
    "ZhixingError",
]
