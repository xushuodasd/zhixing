# 参与贡献（CONTRIBUTING）

感谢关注 ZhiXing（知行）！本文档介绍如何搭建开发环境、运行检查，以及提交代码需要遵守的规范。

## 开发环境

- Python 3.11+
- Git

```bash
git clone <仓库地址>
cd zhixing

python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"    # Windows
# .venv/bin/python -m pip install -e ".[dev]"          # macOS / Linux
```

`dev` 附加依赖包含 pytest 与 ruff。

## 运行测试与静态检查

```bash
# 全量单测（当前 59 个，全部离线，不需要 API Key）
.venv\Scripts\python.exe -m pytest -q        # Windows
# .venv/bin/python -m pytest -q              # macOS / Linux

# 静态检查（全绿是合并前提）
.venv\Scripts\ruff.exe check .               # Windows
# .venv/bin/ruff check .                     # macOS / Linux
```

项目约定：

- 所有测试必须离线可跑——模型响应用 `FakeProvider` 脚本回放，HTTP 交互用 `httpx.MockTransport` 打桩，不依赖网络与真实 API Key；
- 不新增运行时依赖；确有必要时先在 issue 中说明理由，达成一致再动手；
- 新代码需带类型标注与中文 docstring，与现有风格保持一致。

## 提交规范（Conventional Commits）

提交信息格式：

```text
<type>(<scope>?): <一句话摘要，祈使句，结尾不加句号>

<可选正文：动机与要点>

Task: <任务编号>
Requirements: <需求编号>
Checks: <已运行的检查及结果>
Documentation: <受影响文档，或 no impact>
Risks: <已知风险，或 none>
```

type 取值：`feat` / `fix` / `docs` / `refactor` / `test` / `chore`。

真实提交示例：

```text
feat: add agent loop with memory and end-to-end tests

Task: TASK-004
Requirements: REQ-002
Checks: pytest 59 passed, ruff all green
Documentation: README.md, CHANGELOG.md
Risks: none
```

## 代码走查（独立审查）

每个改动在合并前由**非作者**进行独立审查：审查者逐项核对任务契约的验收标准、检查命令与证据（`.ai-team/evidence/`）、代码与文档的一致性。审查结论（approved / changes-requested）记录在任务卡中；通过后由维护者统一集成合并。

## 行为准则

参与本项目（包括 issue、PR、代码审查与社区交流）即表示同意遵守[行为准则](CODE_OF_CONDUCT.md)。

## Roadmap

尚未实现的能力（长期记忆后端、流式输出、多智能体协作等）见 README 的[规划中](README.md#规划中roadmap)一节。想认领某个方向，请先开 issue 描述思路，与维护者达成一致后再动手，避免重复劳动。
