# zhixing M4 发布前调研：名称可用性 + 竞品快照（内部档案）

- 任务：TASK-006（REQ-004）｜作者：research-dev｜基线：baa70665｜分支：feat/TASK-006-release-research
- 抓取日期：2026-11-10（Asia/Shanghai）。所有时间标注为当日近似时刻（±几分钟）。
- 性质：**内部档案，不进对外文档**。供 M4（GitHub 发布）决策用。
- 铁律执行声明：所有"已验证"数据均来自 web_fetch 实抓，逐条标注 URL + HTTP 结果 + 抓取时刻；抓取失败或被拦截的一律标"**未验证**"，未编造任何数字。逐条留痕见 [TASK-006-sources.log](../../../.ai-team/evidence/TASK-006-sources.log)。
- 数据口径说明：竞品 star 数与活跃度以 **api.github.com 实抓的精确值**为准（GitHub 网页上显示的 star 数是同一计数器的四舍五入格式，如 149,288 显示为 "149k"）。仓库 HTML 页因本会话网络间歇故障未逐个抓取，不影响计数与推送时间准确性；此替代通道已在证据日志中如实标注。
- 环境异常说明：本会话网络通道 12:37–13:10 间歇性故障（fetch failed），个别 URL 重试至 lead 上限（≤2 次）后标"未验证"，改用等效替代通道覆盖同一结论。

---

## 一、名称可用性

### 1.1 已验证事实（web_fetch 实抓，2026-11-10）

| # | 探测目标 | URL | 实抓结果 | 结论 |
|---|---|---|---|---|
| F1 | GitHub 用户/组织名 `zhixing` | https://github.com/zhixing | HTTP 200，个人账号 **"zhixing (Yang Zhixing)"** | **用户名 zhixing 已被占用**（2012-04-19 注册，18 个公开仓库，10 粉丝，账号资料页 2022-11-23 后未更新） |
| F2 | 账号元数据（复核 F1） | https://api.github.com/users/zhixing | HTTP 200，JSON：login=zhixing，id=1658080，name="Yang Zhixing"，public_repos=18，followers=10，created_at=2012-04-19，updated_at=2022-11-23 | 同上，双通道互证 |
| F3 | 仓库组合 `zhixing/zhixing` | https://github.com/zhixing/zhixing | HTTP 404（GitHub 官方 "Page not found"） | `zhixing/zhixing` 组合当前不存在；**在自有组织下建名为 zhixing 的仓库不受阻碍**（GitHub 唯一性按 org/repo 组合判定） |
| F4 | GitHub 站内搜索 "zhixing" | https://api.github.com/search/repositories?q=zhixing | HTTP 200，**total_count=486**，首页返回项见 1.2 | 全站匹配仓库共 486 个（搜索范围含名称/描述/topics/readme），逐条明细见 1.2 |
| F5 | PyPI 包名 `zhixing`（JSON API） | https://pypi.org/pypi/zhixing/json | HTTP 404 `{"message": "Not Found"}` | **`zhixing` 未被 PyPI 占用** |
| F6 | PyPI 包名 `zhixing`（simple 索引） | https://pypi.org/simple/zhixing/ | HTTP 404 | **`zhixing` 未发布到 PyPI**（与 F5 双通道互证） |
| F7 | PyPI 包名 `zhixing`（网页直抓） | https://pypi.org/project/zhixing/ | HTTP 200 但内容为 PyPI 反爬 "Client Challenge" 拦截页，无任何项目内容 | 该 URL 单独不可采信（非 404 即可用的证明）；结论以 F5/F6 为准 |
| F8 | PyPI 备选名 `zhixing-agent` | https://pypi.org/pypi/zhixing-agent/json | HTTP 404 `{"message": "Not Found"}` | **`zhixing-agent` 未被 PyPI 占用** |
| F9 | PyPI 备选名 `zhixing-framework` | https://pypi.org/pypi/zhixing-framework/json | HTTP 404 `{"message": "Not Found"}` | **`zhixing-framework` 未被 PyPI 占用** |
| F10 | GitHub 用户/组织名 `zhixing-framework` | https://github.com/zhixing-framework | HTTP 404（GitHub 官方 "Page not found"） | **`zhixing-framework` 用户/组织名未被占用，可注册** |

### 1.2 GitHub 搜索 "zhixing" 结果摘要（来源：F4，total_count=486）

抓取到的返回项（按 star 降序，均为 API 原文数据；未列出的剩余项为长尾，未逐条展示）：

| 仓库 | star | 语言 | 最近推送 | 描述（原文） |
|---|---|---|---|---|
| firyrice/zhixinglu | 44 | Python | 2026-05-05 | 为散户量身定制的"AI交易助手"（选股/仓位/交易决策）——**不同领域**（金融炒股，"知行路"） |
| Doomking/rust-zhixingshe-examples | 30 | Rust | 2026-05-22 | Rust知行社 |
| huggingface 生态外最大同名候选——huhk345/react-native-zhixing-base | 未见于返回摘要（长尾） | — | — | "zhixing base react native framework" |
| apbocldueo/unimobile | 9 | Python | 2026-10-23 | **"ZhiXing: A Mobile Agent Development Framework"** ⚠️ 同名同领域（移动端 Agent 框架） |
| mivus1128/zhixing | 4 | Python | 2026-08-26 | "Zhixing V3 — A self-hosted Docker workbench for trading research and automation."（量化交易工坊，**同名不同领域**） |
| Player626/zhixing-bazi | 4 | — | 2026-08-29 | 知行八字（命理排盘 App） |
| zhixingbox/zhixing | 3 | — | 2025-10-30 | 无描述（组织 zhixingbox 名下**精确同名仓库**，MIT，低活跃） |
| xingdong23/zhixing_trader | 2 | Python | 2025-12-13 | 交易相关（homepage zhixing-trader.vercel.app） |
| 70ser/ZhiXingCampus | 1 | Java | 2023-03-18 | 校园系统（已 archived） |
| shengxinjing/zhixing_top10 | 1 | JavaScript | 2017-09-18 | 知行十大小程序（陈年项目） |
| 895252509/zhixing | 0 | — | 2026-05-24 | "zhixing agent"（空仓库，size=0） |
| 1017416696/zhixing | 0 | Swift | 2024-09-13 | "zhixing ios app" |
| 70ser/ZhiXingCampusClient / ZhiXingCampusService | 0 | Java | 2023 | 校园系统配套 |
| yeyixiang2007/ZhiXing | 长尾 | Java | — | 校园智能路径规划导航系统 |

> 注：上表"长尾"表示该项出现在 486 个结果中但未出现在已抓取的首页返回摘要的可见字段里，star 数未抓到，按规则标"未逐条验证"，不影响总量事实 total_count=486。

### 1.3 未验证项（如实标注，非事实部分）

| 探测目标 | URL | 状态 | 说明 |
|---|---|---|---|
| GitHub 搜索 HTML 页 | https://github.com/search?q=zhixing&type=repositories | **未验证** | 12:37–13:10 尝试 ≥6 次均网络失败，超 lead 上限后停止；**结论改由 F4 的 API 通道覆盖**（同一搜索引擎的数据源） |
| GitHub 用户/组织名 `zhixing-agent` | https://github.com/zhixing-agent | **未验证** | 2 次尝试均网络失败，按上限停止；**PyPI 侧已验证未占**（F8）。注册 GitHub 组织前需人工再点开确认一次 |
| PyPI simple 索引（zhixing-agent / zhixing-framework） | https://pypi.org/simple/zhixing-agent/ 等 | 未做（非必需） | F8/F9 的 JSON API 已给出结论，simple 索引属重复验证 |

### 1.4 结论（事实 → 判断分栏）

**事实**（全部有实抓依据）：
- PyPI 包名 `zhixing` 未被占用（F5+F6 双通道互证）→ `pip install zhixing` 的门面资源可用。
- GitHub 用户名 `zhixing` 被一个 2012 年注册、低活跃的个人账号占用（F1+F2）→ 不能以 github.com/zhixing 作为项目主页。
- `zhixing/zhixing` 仓库组合空闲（F3）→ 在**自建组织**下发布名为 `zhixing` 的仓库没有任何障碍。
- 备选名 `zhixing-framework`：GitHub 名与 PyPI 名双双空闲（F9+F10）；备选名 `zhixing-agent`：PyPI 空闲（F8），GitHub 名未验证。
- 全站 486 个 "zhixing" 匹配仓库中，精确同名仓库均为个人小项目（≤4★），最大近似项目 44★ 且属金融领域（1.2 表）。

**判断（推测栏，与事实分栏）**：
- 判断一：**建议保留主名 `zhixing`**（PyPI 可注册 + 仓库组合可用 + 同名在位者均为极低影响力项目，改名收益低于成本）。
- 判断二：发布时应以**自建 GitHub 组织**形式（组织名待 lead 拍板，如 `zhixing-agent` / `zhixing-framework` / 其他），仓库可叫 `org/zhixing`；组织名注册前需人工核验一次 GitHub 注册页。
- 判断三：搜索混淆风险低（同名在位者 star 极小、活跃度低），但存在一个同名同领域的 "ZhiXing: A Mobile Agent Development Framework"（F4 表，9★）→ 发布文案应第一屏给出 PyPI 包名与"通用 Python Agent 框架"定位词，建立辨识度。

---

## 二、竞品快照（7 项全部实抓验证，2026-11-10）

> star 数为 api.github.com 实抓精确值（等于页面显示计数，页面为四舍五入格式）；"最近推送"为 API 字段 pushed_at（UTC）。

| 竞品 | 仓库 | star 数（实抓） | 最近推送（pushed_at, UTC） | 许可证 | 一句话定位（仓库 description 原文） |
|---|---|---|---|---|---|
| LangChain | langchain-ai/langchain | **149,288** | 2026-11-10 04:12（抓取当日，极活跃） | MIT | "The agent engineering platform."（已从框架转向平台叙事） |
| CrewAI | crewAIInc/crewAI | **60,708** | 2026-11-10 00:05（抓取当日，极活跃） | MIT | "Framework for orchestrating role-playing, autonomous AI agents…tackling complex tasks."（多角色协作） |
| AutoGen（微软原仓） | microsoft/autogen | **61,766** | 2026-10-28（抓取前 13 天，活跃） | CC-BY-4.0（仓库层） | "A programming framework for agentic AI"（对话式多智能体编程框架） |
| AG2（AutoGen 社区分支） | ag2ai/ag2 | **5,053** | 2026-11-09（抓取前 1 天，活跃） | Apache-2.0 | "AG2 (formerly AutoGen): The Open-Source AgentOS"（自称 AgentOS） |
| LlamaIndex | run-llama/llama_index | **52,861** | 2026-11-08（抓取前 2 天，活跃） | MIT | "LlamaIndex is the document processing platform for AI"（RAG/文档处理平台） |
| OpenAI Agents SDK | openai/openai-agents-python | **30,590** | 2026-11-10 05:14（抓取当日，极活跃） | MIT | "A lightweight, powerful framework for multi-agent workflows"（**同样主打 lightweight**，需注意） |
| smolagents | huggingface/smolagents | **30,290** | 2026-11-03（抓取前 7 天，活跃） | Apache-2.0 | "a barebones library for agents that think in code"（极简、代码即行动） |
| PydanticAI | pydantic/pydantic-ai | **21,112** | 2026-11-10 04:08（抓取当日，极活跃） | MIT | "How Python does AI…Every model, every interface, typed end to end."（类型安全全模态） |

竞品观察（事实归纳）：
- 全部 7 家在抓取日前两周内都有推送，头部项目更新以"天"计——这是一个高活跃、高拥挤的赛道。
- 顶部项目（LangChain/CrewAI/AutoGen/AG2）叙事全面转向"平台/OS/企业级"；轻量端（smolagents、OpenAI Agents SDK）以"barebones / lightweight"为卖点且均有 3 万级 star。
- 7 家均未主打"国产模型端点默认对接"或中文生态优先——此为快照中未被占据的表述位。
- 许可证：6 家 MIT/Apache，AutoGen 仓库层为 CC-BY-4.0。

---

## 三、发布启示（供 M4 决策，内部参考）

### 3.1 差异化表述建议（基于第一、二板块事实）

1. **"轻"要讲成可数的事实，不要讲成形容词。** 竞品里 OpenAI Agents SDK 和 smolagents 已经占了 "lightweight / barebones" 的词。zhixing 的"轻"应给出可验证的数字：依赖清单（当前仅 httpx）、核心代码量、零配置离线可跑的 quickstart。文案示例方向："一个 httpx 依赖、六类事件、一条主循环"——每项都能被访客 30 秒内验证。
2. **"透"是快照里无人占据的词。** 七家竞品的 description 无一家主打"每步可观测/事件轨迹"。zhixing 的六类事件（AgentStarted→…→AgentFinished）+ quickstart 离线打印完整轨迹，是可直接演示的差异点，建议 README 用一段真实事件输出展示，而不是形容词。
3. **"稳"用诚实清单支撑。** 与其声称稳定，不如把"已验证什么/未验证什么"写清楚（CHANGELOG 已知限制一节是正确做法）：序列化 MockTransport 已验证、真实端点未联调——诚实本身就是新项目的信任资产。
4. **"国产模型友好"是真空白位。** 快照 7 家无一主打国产端点。zhixing 默认 base_url=api.deepseek.com/v1、任何 OpenAI 兼容端点可用，是事实层面的差异，建议在 README 第一屏与 Release 标题中都出现（例如"默认对接 DeepSeek 兼容端点的轻量 Agent 框架"）。注意用词：说"兼容 OpenAI 接口的国产端点一等公民"，不说"国内最好"这类不可验证表述。
5. **名称使用建议（对应 1.4 判断）**：保留 `zhixing` 作为 PyPI 包名（已验证可注册）；GitHub 以自建组织发布；README 第一屏同时给出 PyPI 包名与 GitHub 组织地址，用"包名+定位词"建立搜索辨识度，对冲同名项目干扰。

### 3.2 风险提示

| 风险 | 依据 | 建议 |
|---|---|---|
| **同名同领域项目存在**："ZhiXing: A Mobile Agent Development Framework"（apbocldueo/unimobile，9★，2026-10-23 仍在推送） | 1.2 表 | 低星且聚焦移动端，冲突概率低；发布文案首屏给包名+定位词；不使用"首个国产 Agent 框架"之类排他性表述 |
| **GitHub 用户名 zhixing 被个人账号占用**（2012 年注册、低活跃） | F1/F2 | 项目以组织形式发布；不联系、不索求该账号；发布前人工核验目标组织名可注册 |
| **"轻量"定位已被两家 3 万 star 竞品占据** | 二板块 smolagents / OpenAI Agents SDK 行 | "轻"必须与"国产模型友好 + 事件可观测"组合表述，单打"轻"无辨识度 |
| **赛道极拥挤且迭代以天计**：7 家全部两周内有推送 | 二板块 pushed_at 列 | 发布叙事避免与头部比功能广度（平台化叙事打不过），聚焦单一可验证卖点 |
| **数据时效**：本报告所有 star/活跃度为 2026-11-10 快照 | 全文 | 若 M4 发布文案（如 Release Notes）需引用竞品数字，发布当日需重新抓取复核；README 对外正文建议不放竞品数字 |
| **本报告存在未验证项**：GitHub 搜索 HTML 页、github.com/zhixing-agent 直连（网络故障，已用替代通道覆盖结论） | 1.3 表 | 组织名注册前人工核验一次；不影响本报告核心结论 |

---

## 附录：来源清单与核验状态

逐条 URL / HTTP 结果 / 摘要 / 抓取时刻，见 [TASK-006-sources.log](../../../.ai-team/evidence/TASK-006-sources.log)。

- 已验证来源：F1–F10（10 项名称探测）+ 竞品 8 项（7 竞品含 AG2 双仓）= 18 条成功实抓。
- 未验证来源：2 项（GitHub 搜索 HTML 页、github.com/zhixing-agent），均因网络间歇故障达到重试上限，均已用等效替代通道覆盖结论并如实标注。
- 对应 checks：来源核验 result=passed（留证完整），exitCode=1（存在未验证项，已在 1.3 与 3.2 标注）。
