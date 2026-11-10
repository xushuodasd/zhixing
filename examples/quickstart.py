"""zhixing 上手示例：一个会查天气的 Agent（完全离线，无需 API key）。

本示例展示 zhixing 的两个核心卖点：

1. **知行合一**：模型（知）决定何时调用 ``get_weather`` 工具（行），
   拿到工具结果后给出最终回答——一次完整的"规划-执行-回答"闭环；
2. **每步可观测**：Agent 的每个动作（开始 / 请求模型 / 执行工具 / 结束）
   都会发出事件，``on_event`` 回调逐行打印，运行过程一目了然。

运行方式（不联网、不设密钥）::

    python examples/quickstart.py

演示中的模型响应由 :class:`~zhixing.providers.fake.FakeProvider` 按脚本
回放；接入真实模型时，把 provider 换成
:class:`~zhixing.providers.openai_compat.OpenAICompatProvider` 即可，
Agent 循环与工具层零改动。
"""

from __future__ import annotations

from zhixing import (
    Agent,
    AgentFinished,
    AgentStarted,
    Event,
    FakeProvider,
    InMemoryMemory,
    LlmRequested,
    LlmResponded,
    Message,
    ProviderResponse,
    ToolCall,
    ToolCallFinished,
    ToolCallStarted,
    ToolRegistry,
    tool,
)


@tool
def get_weather(city: str) -> str:
    """查询指定城市当前的天气状况。"""
    # 演示用固定数据；真实场景中这里调用天气 API。
    return f"{city}：晴，气温 12℃，微风"


def _print_event(event: Event) -> None:
    """把一条事件翻译成一行人类可读的观测记录（每步可观测）。"""
    if isinstance(event, AgentStarted):
        print(f"[事件] AgentStarted     —— 接到任务：{event.user_input}")
    elif isinstance(event, LlmRequested):
        print(f"[事件] LlmRequested     —— 请求模型（携带 {len(event.messages)} 条消息）")
    elif isinstance(event, LlmResponded):
        detail = "模型发起工具调用" if event.response.message.tool_calls else "模型给出最终回答"
        print(f"[事件] LlmResponded     —— {detail}")
    elif isinstance(event, ToolCallStarted):
        print(f"[事件] ToolCallStarted  —— 执行工具 {event.call.name}，参数 {event.call.arguments}")
    elif isinstance(event, ToolCallFinished):
        mark = "失败" if event.result.is_error else "成功"
        print(f"[事件] ToolCallFinished —— 工具执行{mark}：{event.result.content}")
    elif isinstance(event, AgentFinished):
        print(f"[事件] AgentFinished    —— 本轮结束，共调用模型 {event.iterations} 次")


def main() -> None:
    """组装并运行一个查天气 Agent，逐行打印事件轨迹与最终答案。"""
    provider = FakeProvider(
        [
            # 第一次调用：模型决定先查天气（发起工具调用）。
            ProviderResponse(
                message=Message.assistant(
                    tool_calls=[
                        ToolCall(id="call-001", name="get_weather", arguments={"city": "北京"})
                    ]
                ),
                finish_reason="tool_calls",
            ),
            # 第二次调用：模型拿到工具结果后给出最终回答。
            ProviderResponse(
                message=Message.assistant("北京现在天气晴，气温 12℃，微风，适合外出。"),
                finish_reason="stop",
            ),
        ]
    )

    registry = ToolRegistry()
    registry.register(get_weather)

    agent = Agent(
        provider=provider,
        tools=registry,
        system_prompt="你是知行助手，回答要简洁实用。",
        memory=InMemoryMemory(),
        on_event=_print_event,
    )

    result = agent.run("北京今天天气怎么样？")

    print()
    print(f"最终答案：{result.answer}")
    print(f"事件轨迹共 {len(result.events)} 条，模型调用 {result.iterations} 次。")


if __name__ == "__main__":
    main()
