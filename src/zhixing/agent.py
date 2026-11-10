"""Agent 运行时：知行闭环的规划-执行循环。

"知行合一"在本模块落地——模型负责**知**（理解、规划、决策），工具负责
**行**（真实执行），:meth:`Agent.run` 把两者装进同一个可控循环：

1. 组装上下文：系统提示 + 记忆中的历史对话 + 本轮用户输入；
2. 请求模型（知）：交给 :class:`~zhixing.providers.base.Provider` 补全，
   配置了工具则附带工具 schema 清单，让模型知道"能做什么"；
3. 执行工具（行）：模型发起工具调用时逐个执行，结果（含失败摘要）作为
   tool 消息回喂模型——错误不终结循环，而是成为模型下一步规划的依据，
   这是 Agent 相对单次问答的核心差异：**自我修复**；
4. 闭环收敛：模型不再发起工具调用即视为得出最终答案，本轮结束；
   :attr:`Agent.max_iterations` 是护栏，模型无限调用工具时抛出
   :class:`~zhixing.core.exceptions.MaxIterationsError` 兜底。

每个节点（开始 / 请求模型 / 模型返回 / 工具执行 / 结束）都发出事件：
注入 ``on_event`` 可实时观测，:attr:`AgentResult.events` 保存完整轨迹
供回放与审计——这是"每步可观测"卖点的实现层。

循环为何这样设计：模型每拿到一次工具结果就重新规划一次（而非一次性
编排全部调用），既贴合大模型逐轮决策的真实行为，也让每次"知→行"都
留下可审计的事件轨迹；工具失败折叠为结果而非异常，则保证循环只会因
"无话可说"（迭代上限）或模型侧故障（ProviderError）而中断，不会因为
一个工具出错就整体崩溃。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

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
from zhixing.core.exceptions import MaxIterationsError, ZhixingError
from zhixing.core.types import Message, ToolResult
from zhixing.memory.base import Memory
from zhixing.providers.base import Provider
from zhixing.tools.registry import ToolRegistry


@dataclass
class AgentResult:
    """一次 :meth:`Agent.run` 的完整产出：答案、全量消息与事件轨迹。

    Attributes:
        answer: 给用户的最终回答（不含工具调用的助手消息文本）。
        messages: 本次运行的全量消息列表（列表副本）——含系统提示、记忆
            历史、用户输入、助手的工具调用、工具结果与最终回答，可整段
            交给调试器回放或后续轮次复用。
        events: 完整事件轨迹（列表副本），按发生顺序排列。
        iterations: 实际发生的模型调用次数。
        stopped_reason: 停止原因；正常结束恒为 ``"completed"``。异常路径
            （如超出迭代上限）以抛出异常收尾，不会返回本结果。
    """

    answer: str
    messages: list[Message]
    events: list[Event]
    iterations: int
    stopped_reason: str


class Agent:
    """规划-执行循环的编排者：模型负责"知"，工具负责"行"。

    Agent 只依赖两个协议——:class:`~zhixing.providers.base.Provider` 与
    :class:`~zhixing.memory.base.Memory`，因此更换模型厂商、更换存储后端
    都不需要改动循环本身（依赖倒置）。

    Attributes:
        provider: 模型服务（唯一必需的依赖）。
        tools: 工具注册表；``None`` 表示纯对话 Agent。
        system_prompt: 系统提示，每轮都会排在消息列表最前。
        memory: 会话记忆；``None`` 表示单轮无状态运行。
        max_iterations: 单次 ``run`` 内模型调用次数上限（护栏）。
        on_event: 实时事件回调；每条事件在入列后立即转发。
    """

    def __init__(
        self,
        provider: Provider,
        tools: ToolRegistry | None = None,
        system_prompt: str | None = None,
        memory: Memory | None = None,
        max_iterations: int = 10,
        on_event: Callable[[Event], None] | None = None,
    ) -> None:
        """初始化 Agent（全部依赖显式注入，便于测试与替换实现）。

        Args:
            provider: 模型服务实现。
            tools: 工具注册表；缺省为纯对话 Agent。
            system_prompt: 系统提示；``None`` 表示不发送 system 消息。
            memory: 会话记忆；``None`` 表示无记忆。
            max_iterations: 模型调用次数上限，至少为 1。
            on_event: 实时事件回调；``None`` 表示只收集不转发。

        Raises:
            ZhixingError: ``max_iterations`` 小于 1（护栏必须真实生效，
                配置错误应在构造期暴露，不能拖到运行期）。
        """
        if max_iterations < 1:
            raise ZhixingError(f"max_iterations 必须至少为 1，收到 {max_iterations}")
        self._provider = provider
        self._tools = tools
        self._system_prompt = system_prompt
        self._memory = memory
        self._max_iterations = max_iterations
        self._on_event = on_event

    def run(self, user_input: str) -> AgentResult:
        """执行一轮"规划-执行"循环，直到模型给出最终答案或触发护栏。

        循环语义（每一步都有事件，完整轨迹见 :attr:`AgentResult.events`）：

        1. ``AgentStarted`` → 组装 ``[system] + 记忆历史 + [user]``；
        2. ``LlmRequested`` → 调用 ``provider.complete``（配置了工具则
           附带工具 schema 清单）→ ``LlmResponded``；
        3. 响应含 ``tool_calls``：逐个 ``ToolCallStarted`` → 执行（未注册
           或执行失败都折算为 ``is_error=True`` 的结果，不抛异常）→
           ``ToolCallFinished`` → 结果作为 tool 消息追加 → 回到第 2 步；
        4. 响应不含 ``tool_calls``：``AgentFinished`` → 最终回答写入记忆
           → 返回结果。

        记忆只沉淀对话骨架（用户输入与最终回答），工具调用的中间过程完整
        保留在 :attr:`AgentResult.messages` 与事件轨迹中——多轮上下文保持
        简洁，过程细节又随时可查。

        Args:
            user_input: 本轮用户输入。

        Returns:
            :class:`AgentResult`：答案、全量消息副本、事件副本、迭代次数
            与停止原因。

        Raises:
            MaxIterationsError: 连续 ``max_iterations`` 次调用模型仍未得到
                最终答案（异常消息含已迭代次数；已发生的事件仍可通过
                ``on_event`` 回调获取）。
        """
        recorder = TraceRecorder(on_event=self._on_event)
        recorder.record(AgentStarted(user_input=user_input))

        assembled: list[Message] = []
        if self._system_prompt is not None:
            assembled.append(Message.system(self._system_prompt))
        if self._memory is not None:
            assembled.extend(self._memory.messages())
        user_message = Message.user(user_input)
        assembled.append(user_message)
        if self._memory is not None:
            self._memory.append(user_message)

        iterations = 0
        while True:
            if iterations >= self._max_iterations:
                raise MaxIterationsError(
                    f"Agent 循环已达最大迭代上限：已迭代 {iterations} 次仍未得到"
                    f"最终答案（max_iterations={self._max_iterations}）"
                )

            recorder.record(LlmRequested(messages=list(assembled)))
            response = self._provider.complete(
                messages=list(assembled),
                tools=self._tools.schemas() if self._tools is not None else None,
            )
            iterations += 1
            recorder.record(LlmResponded(response=response))

            assistant_message = response.message
            assembled.append(assistant_message)

            if assistant_message.tool_calls:
                for call in assistant_message.tool_calls:
                    recorder.record(ToolCallStarted(call=call))
                    if self._tools is not None:
                        result = self._tools.execute(call.name, call.arguments)
                    else:
                        result = ToolResult(
                            tool_call_id="",
                            content=f"工具 {call.name!r} 未注册（当前 Agent 未配置任何工具）",
                            is_error=True,
                        )
                    # 注册表层面以空串占位，这里统一回填为模型侧调用 id。
                    result.tool_call_id = call.id
                    recorder.record(ToolCallFinished(result=result))
                    assembled.append(
                        Message.tool(tool_call_id=call.id, content=result.content)
                    )
                continue

            answer = assistant_message.content or ""
            recorder.record(AgentFinished(answer=answer, iterations=iterations))
            if self._memory is not None:
                self._memory.append(assistant_message)
            return AgentResult(
                answer=answer,
                messages=list(assembled),
                events=list(recorder.events),
                iterations=iterations,
                stopped_reason="completed",
            )
