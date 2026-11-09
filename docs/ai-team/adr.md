# 架构决策记录（ADR）

## ADR-001 项目转向：废弃股票项目，立项开源 Agent 框架 zhixing

- 编号/版本/日期：ADR-001 / v1.0 / 2026-11-09；状态：已接受；范围决定者：老板（直接选择），技术细节：Lead
- 背景：同目录存在 2026-11-09 14:49 获批 S1 的"每日股票分析"项目（REQ-001~006，仅档案、无代码）；老板同日新指令：做一个开源项目宣扬公司实力并发布 GitHub（AI 公司）。
- 决定：旧项目废弃并封存至分支 `archive/stock-analysis-20261109`（a07060a，含全部 4 个提交，可随时恢复）；新项目 **zhixing**——面向 GitHub 的 AI Agent 应用开发框架。
- 方向选型理由（老板委托 Lead 定）：Agent 框架受众最广、涨星最快、同时展示工程与 AI 实力。备选被否：AI 小产品（开发者吸引力弱、维护重）、训练/评测工具链（受众窄）、教程内容库（实力含金量低）。
- 技术选型（Lead 责任）：Python 3.11+、src 布局、pytest+ruff；provider 无关设计，默认对接 OpenAI 兼容接口；MIT 许可；双语 README（中文为主）。
- 代价与风险：旧项目档案投入封存（无代码损失）；项目名重名风险留 M4 核验（RISK-001）。
- 回滚：旧项目可从归档分支完整恢复；本决定纯本地操作，不影响任何远端。
- 证据：.ai-team/evidence/EVD-001-repo-archive.txt（sha256 见 state.json EVD-001）

## ADR-002 治理档案入库、瞬态产物出库、摘要文件迁移

- 编号/版本/日期：ADR-002 / v1.0 / 2026-11-09；状态：已接受；决定者：Lead
- 背景：TASK-001 集成门禁（包根 scripts/task-check.mjs 严格模式）规定：仓库工作区禁止存在任何被 gitignore 的未跟踪文件；`.ai-team/` 下仅允许 state.json、tasks/*.json、evidence/*.log|txt。TASK-001 原任务卡让执行者 gitignore 治理目录，与门禁冲突——责任在 Lead 的任务卡设计，非执行者。
- 决定：
  1. `.ai-team/` 与 `docs/ai-team/` 从 .gitignore 移除，治理档案随仓库提交（含 state.json、任务契约、检查证据、ADR、会话摘要）。
  2. 会话摘要从 `.ai-team/session-digest.md` 迁移至 `docs/ai-team/session-digest.md`（门禁禁止 .ai-team/ 下存放非治理三类文件）。
  3. venv、pytest/ruff 缓存、pip 临时产物一律不放仓库根（放 %TEMP%）；仓库内保持零 ignored 文件。重建 venv 所需的 ensurepip sitecustomize shim 备份于 %TEMP%\zhixing-build\sitecustomize.py。
- 代价与影响：GitHub 公开仓库将包含治理档案（内部工作痕迹对外可见）；M4/S5 发布前须再决策公共仓库内容处理（候选方案：干净发布分支/压缩历史），到时需老板拍板。摘要每次更新需随治理提交入库。
- 回滚：恢复 .gitignore 两行 + 移回摘要文件即可；无数据风险。
- 集成环境限制备案：task-check.mjs 内部以管道方式调用 git，DSH 沙箱报告 EPERM（read-only 与 workspace-write 均拦），经用户批准后以 danger-full-access 单条命令运行通过；后续里程碑每次集成同样需要该提权。
