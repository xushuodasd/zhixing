"""工具注册表：集中登记、对外暴露 schema 并安全执行工具。"""

from __future__ import annotations

from zhixing.core.exceptions import ZhixingError
from zhixing.core.types import ToolResult
from zhixing.tools.base import Tool


class ToolRegistry:
    """工具注册表：模型可见的工具目录与安全执行入口。

    职责：

    - ``register`` / ``get``：按名称登记与查找工具，重名、查无直接报错；
    - ``schemas``：输出 OpenAI function calling 形态的工具清单，
      Provider 层可直接映射为请求参数；
    - ``execute``：安全执行——查无工具或 handler 抛异常都不向外抛，
      一律折算为 ``is_error=True`` 的 :class:`ToolResult`，让 Agent 循环
      可以把失败信息反馈给模型而不是崩溃。
    """

    def __init__(self) -> None:
        """初始化一个空注册表。"""
        self._tools: dict[str, Tool] = {}

    def register(self, tool_obj: Tool) -> None:
        """登记一个工具。

        Args:
            tool_obj: 待登记的 :class:`Tool`。

        Raises:
            ZhixingError: 同名工具已存在时抛出（重名即配置错误，
                必须在注册期暴露，不能拖到执行期）。
        """
        if tool_obj.name in self._tools:
            raise ZhixingError(f"工具 {tool_obj.name!r} 已注册，禁止重名注册")
        self._tools[tool_obj.name] = tool_obj

    def get(self, name: str) -> Tool:
        """按名称取回工具。

        Args:
            name: 工具名称。

        Returns:
            对应的 :class:`Tool`。

        Raises:
            ZhixingError: 工具未注册时抛出。
        """
        try:
            return self._tools[name]
        except KeyError:
            raise ZhixingError(f"工具 {name!r} 未注册") from None

    def schemas(self) -> list[dict[str, object]]:
        """返回全部工具的 OpenAI function calling 形态 schema 列表。

        Returns:
            形如 ``[{"type": "function", "function": {"name": ..., ...}}]``
            的列表，顺序为登记顺序。
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": item.name,
                    "description": item.description,
                    "parameters": item.parameters,
                },
            }
            for item in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict[str, object] | None = None) -> ToolResult:
        """执行工具，把一切失败折算为错误结果，不向调用方抛异常。

        Args:
            name: 工具名称。
            arguments: 工具参数（键值对，按关键字参数传给 handler）；
                ``None`` 视为空参数。

        Returns:
            成功时 ``is_error=False``，``content`` 为 handler 返回值的字符串
            形态；查无工具或 handler 抛异常（含参数不匹配）时
            ``is_error=True``，``content`` 为错误摘要。``tool_call_id`` 以
            空字符串占位，由 Agent 循环回填消息时补齐。

        Note:
            仅捕获 ``Exception``；``KeyboardInterrupt`` / ``SystemExit``
            等控制流异常按 Python 语义正常上抛。
        """
        item = self._tools.get(name)
        if item is None:
            return ToolResult(tool_call_id="", content=f"工具 {name!r} 未注册", is_error=True)
        call_arguments: dict[str, object] = {} if arguments is None else arguments
        try:
            raw_result = item.handler(**call_arguments)
        except Exception as exc:  # noqa: BLE001 —— 注册表的职责就是把失败折算为结果
            summary = f"{type(exc).__name__}: {exc}"
            return ToolResult(
                tool_call_id="",
                content=f"工具 {name!r} 执行失败：{summary}",
                is_error=True,
            )
        content = raw_result if isinstance(raw_result, str) else str(raw_result)
        return ToolResult(tool_call_id="", content=content, is_error=False)
