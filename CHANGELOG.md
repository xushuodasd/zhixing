# 更新日志（Changelog）

本项目所有显著变更记录于此。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2026-11-10

### Added

- **核心 Agent 循环**：`Agent.run()` 规划-执行循环（组装上下文 → 请求模型 → 执行工具 → 结果回喂 → 收敛），`max_iterations` 护栏（超限抛出 `MaxIterationsError`）；返回 `AgentResult`（最终答案 / 全量消息 / 事件轨迹 / 迭代次数 / 停止原因）；
- **工具系统**：`@tool` 装饰器（从函数签名与 docstring 自动推导 JSON Schema）、`Tool` 数据类、`ToolRegistry`（重名拒绝、schema 导出、执行异常折算为 `is_error=True` 的结果回喂模型，不中断循环）；
- **事件轨迹**：六类运行事件（`AgentStarted` / `LlmRequested` / `LlmResponded` / `ToolCallStarted` / `ToolCallFinished` / `AgentFinished`）、`TraceRecorder` 收集器、`on_event` 实时回调；
- **Provider 抽象**：`Provider` 协议、`OpenAICompatProvider`（基于 httpx，兼容任意 OpenAI chat completions 端点，默认 DeepSeek，Key 解析链 `ZHIXING_API_KEY` → `OPENAI_API_KEY`）、`FakeProvider`（脚本化响应，离线测试与演示用）；
- **记忆接口**：`Memory` 协议与内置 `InMemoryMemory` 实现；
- **离线示例**：`examples/quickstart.py`（无需 API Key，展示完整事件轨迹与最终答案）；
- **离线测试**：59 个测试全部离线运行（含端到端场景：直接回答 / 工具调用后回答 / 工具异常恢复 / 未知工具恢复 / 迭代上限 / 记忆跨轮保持）。

### Known Limitations

- 真实模型端点联调未执行：`OpenAICompatProvider` 的请求构造、序列化与错误路径已通过 `httpx.MockTransport` 离线验证，尚未对接真实 API；
- 无流式输出：模型补全为一次性返回；
- 内置 `InMemoryMemory` 为单线程内存实现：无持久化，无并发安全保障。
