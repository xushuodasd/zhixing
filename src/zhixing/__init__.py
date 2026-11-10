"""知行（ZhiXing）：知行合一的轻量级 AI Agent 应用开发框架。

ZhiXing 旨在让大模型的"知"（规划与决策）与工具的"行"（真实调用与执行）
在同一套可控框架内闭环，围绕工具调用、记忆与多 Provider 适配，提供轻量、
可观测、可测试的 Agent 应用开发体验。

公共 API 一览（M2 完整交付）：

- Agent：:class:`Agent` 规划-执行循环与 :class:`AgentResult`
  （知行闭环的落点）；
- 核心类型：:class:`Message` / :class:`ToolCall` / :class:`ToolResult` /
  :class:`ProviderResponse`；
- 工具：:class:`Tool` / :func:`tool` 装饰器 / :class:`ToolRegistry`；
- 记忆：:class:`Memory` 协议与 :class:`InMemoryMemory` 实现；
- 事件：六类运行事件与 :class:`TraceRecorder`（"每步可观测"落点）；
- Provider：:class:`Provider` 协议 / :class:`OpenAICompatProvider` /
  :class:`FakeProvider`；
- 异常：:class:`ZhixingError` 及其细分（Provider / 工具 / 迭代上限）。
"""

from zhixing.agent import Agent, AgentResult
from zhixing.core import (
    AgentFinished,
    AgentStarted,
    Event,
    LlmRequested,
    LlmResponded,
    MaxIterationsError,
    Message,
    ProviderError,
    ProviderResponse,
    ToolCall,
    ToolCallFinished,
    ToolCallStarted,
    ToolExecutionError,
    ToolResult,
    TraceRecorder,
    ZhixingError,
)
from zhixing.memory import InMemoryMemory, Memory
from zhixing.providers import FakeProvider, OpenAICompatProvider, Provider
from zhixing.tools import Tool, ToolRegistry, tool

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "AgentFinished",
    "AgentResult",
    "AgentStarted",
    "Event",
    "FakeProvider",
    "InMemoryMemory",
    "LlmRequested",
    "LlmResponded",
    "MaxIterationsError",
    "Memory",
    "Message",
    "OpenAICompatProvider",
    "Provider",
    "ProviderError",
    "ProviderResponse",
    "Tool",
    "ToolCall",
    "ToolCallFinished",
    "ToolCallStarted",
    "ToolExecutionError",
    "ToolRegistry",
    "ToolResult",
    "TraceRecorder",
    "ZhixingError",
    "tool",
]
