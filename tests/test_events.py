"""事件模型与 TraceRecorder 测试：顺序收集、回调转发与回调时机。"""

from zhixing import (
    AgentFinished,
    AgentStarted,
    LlmRequested,
    LlmResponded,
    Message,
    ProviderResponse,
    ToolCall,
    ToolCallFinished,
    ToolCallStarted,
    ToolResult,
    TraceRecorder,
)


def _sample_events() -> list[object]:
    """构造覆盖全部六类事件的一段典型轨迹。"""
    return [
        AgentStarted(user_input="北京天气如何？"),
        LlmRequested(messages=[Message.user("北京天气如何？")]),
        LlmResponded(
            response=ProviderResponse(
                message=Message.assistant(tool_calls=[ToolCall(id="call-1", name="get_weather")]),
                finish_reason="tool_calls",
            )
        ),
        ToolCallStarted(call=ToolCall(id="call-1", name="get_weather", arguments={"city": "北京"})),
        ToolCallFinished(result=ToolResult(tool_call_id="call-1", content="晴")),
        AgentFinished(answer="北京今天晴", iterations=1),
    ]


def test_recorder_collects_events_in_order() -> None:
    """record 顺序收集全部事件，保持同一对象引用。"""
    recorder = TraceRecorder()
    events = _sample_events()
    for event in events:
        recorder.record(event)
    assert recorder.events == events
    assert all(a is b for a, b in zip(recorder.events, events, strict=True))


def test_events_is_live_view_across_records() -> None:
    """events 是活跃视图：record 后既得引用同步增长（非每次快照拷贝）。"""
    recorder = TraceRecorder()
    recorder.record(AgentStarted(user_input="第一轮"))
    live = recorder.events
    recorder.record(AgentFinished(answer="完成", iterations=1))
    assert live is recorder.events
    assert len(live) == 2


def test_recorder_forwards_to_callback_in_order() -> None:
    """on_event 回调按记录顺序收到相同的事件序列。"""
    seen: list[object] = []
    recorder = TraceRecorder(on_event=seen.append)
    events = _sample_events()
    for event in events:
        recorder.record(event)
    assert seen == events


def test_callback_runs_after_recording() -> None:
    """回调触发时当前事件已完成入列：记录先于转发。"""
    box: dict[str, TraceRecorder] = {}
    sizes_in_callback: list[int] = []
    recorder = TraceRecorder(
        on_event=lambda event: sizes_in_callback.append(len(box["recorder"].events))
    )
    box["recorder"] = recorder
    recorder.record(AgentStarted(user_input="你好"))
    recorder.record(AgentFinished(answer="完成", iterations=1))
    assert sizes_in_callback == [1, 2]


def test_recorder_without_callback_is_fine() -> None:
    """未注入回调时仅收集，不报错。"""
    recorder = TraceRecorder()
    recorder.record(AgentStarted(user_input="你好"))
    assert len(recorder.events) == 1
    assert recorder.events[0].user_input == "你好"
