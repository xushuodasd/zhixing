"""examples/quickstart.py 离线冒烟：无网络、无 API key 也能完整跑通。"""

from __future__ import annotations

import runpy
from pathlib import Path

QUICKSTART_PATH = Path(__file__).resolve().parents[1] / "examples" / "quickstart.py"


def test_quickstart_prints_events_and_final_answer(capsys) -> None:
    """执行示例入口：输出应包含逐行事件轨迹与最终答案。"""
    runpy.run_path(str(QUICKSTART_PATH), run_name="__main__")

    output = capsys.readouterr().out

    # 事件轨迹逐行可观测：开始 / 请求模型 / 工具执行 / 结束都要出现。
    assert "AgentStarted" in output
    assert "LlmRequested" in output
    assert "ToolCallStarted" in output
    assert "ToolCallFinished" in output
    assert "AgentFinished" in output
    # 最终答案与统计信息完整打印。
    assert "北京现在天气晴" in output
    assert "最终答案" in output
