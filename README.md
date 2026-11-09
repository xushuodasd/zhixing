# ZhiXing（知行）

> 知行合一的轻量级 AI Agent 应用开发框架。

ZhiXing（知行）取意"知行合一"：让大模型的"知"（规划与决策）和工具的"行"（真实调用与执行）在同一套可控的框架里闭环。项目当前处于立项与骨架阶段（M1），本文档描述的是项目定位与规划，尚未包含可运行的 Agent 实现。

## 特性（规划中）

- **工具调用**：统一注册、校验与执行外部工具，让 Agent 能"动手"。
- **记忆**：短期上下文与长期记忆分层管理，存储后端可插拔。
- **多 Provider 适配**：屏蔽不同模型服务商的 API 差异，一套代码切换底层模型。
- **轻量可控**：核心保持极简，行为可观测、可测试、可审计。

> 以上特性是 M2 及后续里程碑的规划目标，当前代码库仅包含包骨架与占位模块。

## 快速开始

项目尚未发布到 PyPI，当前以源码安装方式体验骨架（占位步骤，后续里程碑会更新）：

```bash
git clone <仓库地址>
cd zhixing

# 创建并激活虚拟环境（需要 Python >= 3.11）
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 以可编辑模式安装，并附带开发依赖
pip install -e ".[dev]"

# 运行冒烟测试
pytest -q
```

## 许可证

本项目基于 [MIT License](LICENSE) 开源，Copyright (c) 2026 ZhiXing Contributors。
