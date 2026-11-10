"""Agent 循环端到端测试：全部场景基于离线 Provider 驱动，不联网。"""

from __future__ import annotations

import pytest

from zhixing import (
    Agent,
    AgentFinished,
    AgentStarted,
    Event,
    FakeProvider,
    InMemoryMemory,
    LlmRequested,
    LlmResponded,
    MaxIterationsError,
    Message,
    ProviderResponse,
    ToolCall,
    ToolCallFinished,
    ToolCallStarted,
    ToolRegistry,
    ZhixingError,
    tool,
)


@tool
def get_weather(city: str) -> str:
    """查询指定城市当前的天气状况。"""
    return f"{city}：晴，气温 12℃，微风"


@tool
def always_fails() -> str:
    """一个总会失败的工具（用于测试错误回喂恢复路径）。"""
    raise RuntimeError("数据库连接失败")


class RecordingProvider:
    """测试替身：记录每次收到的消息与工具清单，并按脚本顺序返回响应。"""

    def __init__(self, script: list[ProviderResponse]) -> None:
        """按顺序预置响应脚本。"""
        self._script = list(script)
        self._cursor = 0
        self.calls: list[tuple[list[Message], list[dict[str, object]] | None]] = []

    def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, object]] | None = None,
    ) -> ProviderResponse:
        """记录本次调用入参，返回下一条脚本响应。"""
        self.calls.append((list(messages), tools))
        response = self._script[self._cursor]
        self._cursor += 1
        return response


def _weather_registry() -> ToolRegistry:
    """构造一个只含 get_weather 的注册表。"""
    registry = ToolRegistry()
    registry.register(get_weather)
    return registry


def _tool_call_response(call_id: str = "call-001", city: str = "北京") -> ProviderResponse:
    """构造一条"模型发起 get_weather 工具调用"的脚本响应。"""
    return ProviderResponse(
        message=Message.assistant(
            tool_calls=[ToolCall(id=call_id, name="get_weather", arguments={"city": city})]
        ),
        finish_reason="tool_calls",
    )


def test_direct_answer_completes_in_one_iteration() -> None:
    """模型直接给最终答案：单轮收敛，消息与事件轨迹完整。"""
    provider = FakeProvider(
        [ProviderResponse(message=Message.assistant("你好，我是知行。"), finish_reason="stop")]
    )
    agent = Agent(provider=provider)

    result = agent.run("你好")

    assert result.answer == "你好，我是知行。"
    assert result.stopped_reason == "completed"
    assert result.iterations == 1
    assert [m.role for m in result.messages] == ["user", "assistant"]
    assert result.messages[0].content == "你好"
    assert result.messages[1].content == "你好，我是知行。"
    assert [type(e) for e in result.events] == [
        AgentStarted,
        LlmRequested,
        LlmResponded,
        AgentFinished,
    ]
    assert result.events[0].user_input == "你好"
    assert result.events[3].answer == "你好，我是知行。"
    assert result.events[3].iterations == 1


def test_tool_call_then_answer_round_trip() -> None:
    """工具调用后回答：结果回填 tool_call_id，事件按序完整包裹。"""
    provider = FakeProvider(
        [
            _tool_call_response(call_id="call-001"),
            ProviderResponse(message=Message.assistant("北京今天晴，12℃。"), finish_reason="stop"),
        ]
    )
    agent = Agent(provider=provider, tools=_weather_registry())

    result = agent.run("北京天气怎么样？")

    assert result.answer == "北京今天晴，12℃。"
    assert result.stopped_reason == "completed"
    assert result.iterations == 2
    assert [m.role for m in result.messages] == ["user", "assistant", "tool", "assistant"]
    tool_message = result.messages[2]
    assert tool_message.tool_call_id == "call-001"
    assert tool_message.content == "北京：晴，气温 12℃，微风"
    assert [type(e) for e in result.events] == [
        AgentStarted,
        LlmRequested,
        LlmResponded,
        ToolCallStarted,
        ToolCallFinished,
        LlmRequested,
        LlmResponded,
        AgentFinished,
    ]
    finished = result.events[4]
    assert isinstance(finished, ToolCallFinished)
    assert finished.result.tool_call_id == "call-001"
    assert finished.result.is_error is False
    assert finished.result.content == "北京：晴，气温 12℃，微风"


def test_provider_receives_system_prompt_and_tool_schemas() -> None:
    """配置了 system_prompt 与工具：发给模型的首条是 system，并附 schema 清单。"""
    provider = RecordingProvider(
        [ProviderResponse(message=Message.assistant("好的"), finish_reason="stop")]
    )
    registry = _weather_registry()
    agent = Agent(provider=provider, tools=registry, system_prompt="你是知行助手。")

    agent.run("帮我")

    messages, tools = provider.calls[0]
    assert messages[0].role == "system"
    assert messages[0].content == "你是知行助手。"
    assert messages[-1].role == "user"
    assert tools == registry.schemas()


def test_provider_receives_none_tools_without_registry() -> None:
    """未配置工具：provider.complete 的 tools 参数为 None。"""
    provider = RecordingProvider(
        [ProviderResponse(message=Message.assistant("好的"), finish_reason="stop")]
    )
    agent = Agent(provider=provider)

    agent.run("在吗")

    _, tools = provider.calls[0]
    assert tools is None


def test_tool_error_is_fed_back_and_model_recovers() -> None:
    """工具执行抛异常：错误结果回喂模型，循环不崩并给出最终回答。"""
    provider = FakeProvider(
        [
            ProviderResponse(
                message=Message.assistant(
                    tool_calls=[ToolCall(id="call-100", name="always_fails")]
                ),
                finish_reason="tool_calls",
            ),
            ProviderResponse(
                message=Message.assistant("查询失败了，请稍后再试。"), finish_reason="stop"
            ),
        ]
    )
    registry = ToolRegistry()
    registry.register(always_fails)
    agent = Agent(provider=provider, tools=registry)

    result = agent.run("查一下数据")

    assert result.answer == "查询失败了，请稍后再试。"
    tool_message = result.messages[2]
    assert tool_message.role == "tool"
    assert tool_message.tool_call_id == "call-100"
    assert "RuntimeError" in tool_message.content
    assert "数据库连接失败" in tool_message.content
    finished = next(e for e in result.events if isinstance(e, ToolCallFinished))
    assert finished.result.is_error is True


def test_unknown_tool_error_is_fed_back_and_model_recovers() -> None:
    """模型调用未注册工具：同样走错误回喂恢复路径。"""
    provider = FakeProvider(
        [
            ProviderResponse(
                message=Message.assistant(
                    tool_calls=[ToolCall(id="call-200", name="no_such_tool", arguments={"x": 1})]
                ),
                finish_reason="tool_calls",
            ),
            ProviderResponse(
                message=Message.assistant("这个工具我不支持。"), finish_reason="stop"
            ),
        ]
    )
    agent = Agent(provider=provider, tools=ToolRegistry())  # 空注册表：任何工具都是未知

    result = agent.run("用不存在的工具")

    assert result.answer == "这个工具我不支持。"
    tool_message = result.messages[2]
    assert tool_message.tool_call_id == "call-200"
    assert "未注册" in tool_message.content
    finished = next(e for e in result.events if isinstance(e, ToolCallFinished))
    assert finished.result.is_error is True


def test_tool_calls_without_registry_are_reported_as_errors() -> None:
    """未配置任何工具但模型仍发起调用：折算为错误结果回喂，不崩溃。"""
    provider = FakeProvider(
        [
            ProviderResponse(
                message=Message.assistant(
                    tool_calls=[ToolCall(id="call-300", name="get_weather")]
                ),
                finish_reason="tool_calls",
            ),
            ProviderResponse(message=Message.assistant("没有工具可用。"), finish_reason="stop"),
        ]
    )
    agent = Agent(provider=provider)

    result = agent.run("查天气")

    assert result.answer == "没有工具可用。"
    tool_message = result.messages[2]
    assert tool_message.role == "tool"
    assert tool_message.tool_call_id == "call-300"
    assert "未注册" in tool_message.content


def test_max_iterations_raises_and_keeps_events() -> None:
    """模型永远只发起工具调用：达到上限抛 MaxIterationsError，已发生事件完整。"""
    script: list[ProviderResponse] = []
    for i in range(2):
        script.append(
            ProviderResponse(
                message=Message.assistant(
                    tool_calls=[
                        ToolCall(id=f"call-{i}", name="get_weather", arguments={"city": "北京"})
                    ]
                ),
                finish_reason="tool_calls",
            )
        )
    events: list[Event] = []
    agent = Agent(
        provider=FakeProvider(script),
        tools=_weather_registry(),
        max_iterations=2,
        on_event=events.append,
    )

    with pytest.raises(MaxIterationsError) as excinfo:
        agent.run("北京天气怎么样？")

    assert "已迭代 2 次" in str(excinfo.value)
    event_types = [type(e) for e in events]
    assert event_types[0] is AgentStarted
    assert event_types.count(LlmRequested) == 2
    assert event_types.count(LlmResponded) == 2
    assert event_types.count(ToolCallFinished) == 2
    assert all(kind is not AgentFinished for kind in event_types)


def test_memory_keeps_context_across_runs() -> None:
    """记忆跨两次 run 保持上下文：第二次请求的消息里能看到第一次的问答。"""
    memory = InMemoryMemory()
    first_provider = FakeProvider(
        [ProviderResponse(message=Message.assistant("你好，我是知行。"), finish_reason="stop")]
    )
    first = Agent(provider=first_provider, memory=memory).run("你好")

    assert [m.role for m in first.messages] == ["user", "assistant"]
    assert [m.role for m in memory.messages()] == ["user", "assistant"]

    seen: list[Event] = []
    second_provider = FakeProvider(
        [ProviderResponse(message=Message.assistant("你在的，欢迎回来。"), finish_reason="stop")]
    )
    second = Agent(provider=second_provider, memory=memory, on_event=seen.append).run("我在吗")

    requested = next(e for e in seen if isinstance(e, LlmRequested))
    sent_contents = [m.content for m in requested.messages]
    assert "你好" in sent_contents
    assert "你好，我是知行。" in sent_contents
    assert "我在吗" in sent_contents
    assert [m.role for m in memory.messages()] == ["user", "assistant", "user", "assistant"]
    assert [m.role for m in second.messages] == ["user", "assistant", "user", "assistant"]
    assert second.answer == "你在的，欢迎回来。"


def test_on_event_receives_same_events_as_result() -> None:
    """on_event 实时回调与结果里的 events 副本内容一致。"""
    provider = FakeProvider(
        [
            _tool_call_response(),
            ProviderResponse(message=Message.assistant("好了"), finish_reason="stop"),
        ]
    )
    live: list[Event] = []
    agent = Agent(provider=provider, tools=_weather_registry(), on_event=live.append)

    result = agent.run("查天气")

    assert live == result.events


def test_invalid_max_iterations_rejected_upfront() -> None:
    """max_iterations 小于 1 属于配置错误，构造期即暴露。"""
    with pytest.raises(ZhixingError, match="max_iterations"):
        Agent(provider=FakeProvider([]), max_iterations=0)
