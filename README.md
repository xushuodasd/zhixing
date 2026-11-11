# ZhiXing（知行）

> 知行合一的轻量级 AI Agent 框架——让模型的"知"与工具的"行"在可控框架内闭环；轻、透、稳。

ZhiXing（知行）取意"知行合一"：模型负责**知**（理解、规划、决策），工具负责**行**（真实执行），框架把两者装进同一个可控循环。三个字对应三个设计承诺：**轻**——运行时仅依赖 `httpx`；**透**——每一步都有事件轨迹，可观测、可审计；**稳**——工具出错不中断循环，迭代上限护栏兜底。

当前版本 [0.1.0](CHANGELOG.md) 已完成核心循环、工具系统、事件轨迹、Provider 抽象与记忆接口，59 个离线测试全绿；示例 `examples/quickstart.py` 无需 API Key 即可运行。

## 已实现特性

### 知行闭环的 Agent 循环

`Agent.run()` 驱动"规划-执行"循环：组装上下文 → 请求模型 → 执行工具调用 → 结果回喂模型 → 直到模型给出最终答案。`max_iterations` 护栏防止模型无限调用工具，超限时抛出 `MaxIterationsError`。每次运行返回 `AgentResult`：最终答案、全量消息、完整事件轨迹、迭代次数与停止原因。

### 工具调用：@tool 装饰器 + 注册表 + 错误自愈

- `@tool` 装饰器：从函数签名与 docstring 自动推导 JSON Schema——写一个普通的 Python 函数，就是一个 Agent 工具；
- `ToolRegistry`：统一注册（重名拒绝）、导出 schema、按名执行；
- **错误自愈**：工具抛异常不会中断循环——异常自动折算为 `is_error=True` 的工具结果回喂模型，由模型决定下一步；未注册的工具同样按错误结果处理。

### 事件轨迹：每步可观测

六类事件覆盖 Agent 运行全程：`AgentStarted` / `LlmRequested` / `LlmResponded` / `ToolCallStarted` / `ToolCallFinished` / `AgentFinished`。注入 `on_event` 回调即可实时观测，`AgentResult.events` 保存完整轨迹，可回放、可审计。

### 多 Provider：OpenAI 兼容，默认 DeepSeek

- `Provider` 协议 + `OpenAICompatProvider` 实现：对接任意 OpenAI chat completions 兼容端点（DeepSeek、Kimi、Qwen、vLLM 自部署等），默认端点为 DeepSeek 开放平台，默认模型 `deepseek-chat`；
- API Key 解析链：显式传参 → 环境变量 `ZHIXING_API_KEY` → `OPENAI_API_KEY`，全部缺失时构造期快速失败；
- `FakeProvider`：按脚本回放预置响应，离线测试与演示专用。

### 可插拔记忆

`Memory` 协议（append / messages / clear）+ 内置 `InMemoryMemory`。记忆只沉淀对话骨架（用户输入与最终回答），工具调用的中间过程完整保留在结果与事件轨迹中。实现协议即可接入自己的存储后端，Agent 循环零改动。

### 极轻的依赖面

运行时唯一第三方依赖是 `httpx`；核心数据结构全部为标准库 dataclass；Python 3.11+。

## 快速开始

以下 Windows 命令已在本机照跑验证，全程离线、无需 API Key：

```bash
# 1. 克隆仓库
git clone https://github.com/xushuodasd/zhixing
cd zhixing

# 2. 创建虚拟环境（需要 Python >= 3.11）
python -m venv .venv

# 3. 以可编辑模式安装（含 pytest / ruff 开发依赖）
.venv\Scripts\python.exe -m pip install -e ".[dev]"    # Windows
# .venv/bin/python -m pip install -e ".[dev]"          # macOS / Linux

# 4. 运行离线示例
.venv\Scripts\python.exe examples\quickstart.py        # Windows
# .venv/bin/python examples/quickstart.py              # macOS / Linux
```

> 偏好激活虚拟环境的读者：Windows 下可运行 `.venv\Scripts\activate.bat`（cmd）或 `.venv\Scripts\Activate.ps1`（PowerShell，若被执行策略拦截，请直接使用上面的 `.venv\Scripts\python.exe` 路径）；macOS / Linux 执行 `source .venv/bin/activate`。

真实运行输出（8 条事件轨迹 + 最终答案，从实际运行复制）：

```text
[事件] AgentStarted     —— 接到任务：北京今天天气怎么样？
[事件] LlmRequested     —— 请求模型（携带 2 条消息）
[事件] LlmResponded     —— 模型发起工具调用
[事件] ToolCallStarted  —— 执行工具 get_weather，参数 {'city': '北京'}
[事件] ToolCallFinished —— 工具执行成功：北京：晴，气温 12℃，微风
[事件] LlmRequested     —— 请求模型（携带 4 条消息）
[事件] LlmResponded     —— 模型给出最终回答
[事件] AgentFinished    —— 本轮结束，共调用模型 2 次

最终答案：北京现在天气晴，气温 12℃，微风，适合外出。
事件轨迹共 8 条，模型调用 2 次。
```

示例中的模型响应由 `FakeProvider` 按脚本回放，因此离线可跑；`get_weather` 是一个 `@tool` 装饰的普通函数。从事件轨迹可以完整看到一次"知行合一"：接到任务 → 请求模型 → 模型发起工具调用 → 执行工具 → 结果回喂 → 模型给出最终回答。

验证安装（可选）：

```bash
.venv\Scripts\python.exe -m pytest -q    # Windows（macOS / Linux: .venv/bin/python -m pytest -q）
```

预期输出末行：`59 passed`。

## 接入真实模型

把 `FakeProvider` 换成 `OpenAICompatProvider` 即可对接真实模型，Agent 循环与工具层零改动：

```python
from zhixing import Agent, InMemoryMemory, OpenAICompatProvider, ToolRegistry, tool


@tool
def get_weather(city: str) -> str:
    """查询指定城市当前的天气状况。"""
    return f"{city}：晴，气温 12℃，微风"


# 方式一：API Key 走环境变量链（推荐）
#   PowerShell:  $env:ZHIXING_API_KEY = "sk-..."
#   bash:        export ZHIXING_API_KEY="sk-..."
provider = OpenAICompatProvider()  # 默认 https://api.deepseek.com/v1 + deepseek-chat

# 方式二：显式传参（换任意 OpenAI 兼容端点，只改 base_url 与 model）
provider = OpenAICompatProvider(
    base_url="https://api.deepseek.com/v1",
    model="deepseek-chat",
    api_key="sk-...",
)

registry = ToolRegistry()
registry.register(get_weather)

agent = Agent(provider=provider, tools=registry, system_prompt="你是知行助手。", memory=InMemoryMemory())
result = agent.run("北京今天天气怎么样？")
print(result.answer)
```

所有失败（网络错误、超时、非 2xx、响应格式异常）都会折算为 `ProviderError` 抛出，错误信息只含状态码与响应摘要，不包含 API Key。

> 诚实声明：`OpenAICompatProvider` 的请求构造、消息与工具调用序列化、错误路径已通过 `httpx.MockTransport` 离线验证；**真实模型端点已于 2026-11-10 完成单次联调验证**（模型自主调用工具 → 中文最终答案，见 [CHANGELOG](CHANGELOG.md) 已知限制更新）。

## 规划中（Roadmap）

以下能力尚未实现，禁止把它们当成已有功能使用；欢迎在 issue 区讨论设计：

- **长期记忆后端**：跨会话持久化（当前内置 `InMemoryMemory` 仅会话级）；
- **流式输出**：逐 token / 逐事件流式返回（当前为一次性返回）；
- **多智能体协作**：Agent 之间的编排与通信。

## 参与贡献

欢迎 issue 与 PR。开发环境搭建、测试与 lint 命令、提交规范见 [CONTRIBUTING](CONTRIBUTING.md)；参与社区请遵守[行为准则](CODE_OF_CONDUCT.md)。

## 许可证

本项目基于 [MIT License](LICENSE) 开源，Copyright (c) 2026 ZhiXing Contributors。

---

## What is ZhiXing?

ZhiXing ("知行合一" — unity of knowledge and action) is a lightweight AI Agent framework: the model's *knowledge* (planning and decision-making) and tools' *action* (real execution) close the loop inside one controllable runtime. It ships a plan-execute Agent loop, a `@tool` decorator that infers JSON Schema from type hints and docstrings, full event tracing for every step, an OpenAI-compatible provider (DeepSeek by default), and a pluggable memory interface — with `httpx` as the only runtime dependency. See the [full Chinese documentation](#zhixing知行) for details.

## Quick Start

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"    # Windows: .venv\Scripts\python.exe
.venv/bin/python examples/quickstart.py        # offline demo, no API key needed
```

See the [Chinese quick start](#快速开始) for the verified walkthrough and real output.

## License

[MIT](LICENSE) © 2026 ZhiXing Contributors.
