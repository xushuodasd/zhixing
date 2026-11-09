"""ToolRegistry 测试：登记/查重、schema 形态与安全执行（含异常折算）。"""

import pytest

from zhixing import Tool, ToolRegistry, ZhixingError, tool


def test_register_and_get_roundtrip() -> None:
    """登记后可以按名称取回同一工具实例。"""

    @tool
    def echo(text: str) -> str:
        """原样返回输入。"""
        return text

    registry = ToolRegistry()
    registry.register(echo)
    assert registry.get("echo") is echo


def test_duplicate_register_rejected() -> None:
    """重名注册抛出 ZhixingError。"""

    @tool
    def echo(text: str) -> str:
        """原样返回输入。"""
        return text

    registry = ToolRegistry()
    registry.register(echo)
    with pytest.raises(ZhixingError, match="已注册"):
        registry.register(echo)


def test_get_unknown_tool_raises() -> None:
    """get 查无工具抛出 ZhixingError。"""
    registry = ToolRegistry()
    with pytest.raises(ZhixingError, match="未注册"):
        registry.get("ghost")


def test_schemas_openai_function_shape() -> None:
    """schemas() 输出 OpenAI function calling 形态的完整结构。"""

    @tool
    def get_weather(city: str, unit: str = "celsius") -> str:
        """查询城市天气。"""
        return f"{city}:{unit}"

    registry = ToolRegistry()
    registry.register(get_weather)
    assert registry.schemas() == [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询城市天气。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "unit": {"type": "string"},
                    },
                    "required": ["city"],
                },
            },
        }
    ]


def test_schemas_empty_registry() -> None:
    """空注册表返回空 schema 列表。"""
    assert ToolRegistry().schemas() == []


def test_execute_success_returns_result() -> None:
    """正常执行：参数按关键字传入，返回 is_error=False 的结果。"""

    @tool
    def add(a: int, b: int) -> int:
        """整数相加。"""
        return a + b

    registry = ToolRegistry()
    registry.register(add)
    result = registry.execute("add", {"a": 2, "b": 5})
    assert result.is_error is False
    assert result.content == "7"
    assert result.tool_call_id == ""  # 注册表层无调用 id，由 Agent 循环回填


def test_execute_converts_non_string_result() -> None:
    """handler 返回非字符串时折算为字符串形态。"""

    @tool
    def make_pair(key: str, value: str) -> dict[str, str]:
        """构造键值对。"""
        return {"key": key, "value": value}

    registry = ToolRegistry()
    registry.register(make_pair)
    result = registry.execute("make_pair", {"key": "k", "value": "v"})
    assert result.is_error is False
    assert isinstance(result.content, str)
    assert "k" in result.content and "v" in result.content


def test_execute_unknown_tool_is_error_result() -> None:
    """查无工具不抛异常，折算为 is_error=True 的结果。"""
    registry = ToolRegistry()
    result = registry.execute("ghost", {})
    assert result.is_error is True
    assert "ghost" in result.content


def test_execute_handler_exception_becomes_error_result() -> None:
    """handler 抛异常不外逃，折算为含错误摘要的 is_error=True 结果。"""

    @tool
    def boom(text: str) -> str:
        """总是抛错。"""
        raise ValueError("炸了")

    registry = ToolRegistry()
    registry.register(boom)
    result = registry.execute("boom", {"text": "x"})
    assert result.is_error is True
    assert "ValueError" in result.content
    assert "炸了" in result.content


def test_execute_bad_arguments_become_error_result() -> None:
    """缺参与多余参数都不允许异常外逃。"""

    @tool
    def add(a: int, b: int) -> int:
        """整数相加。"""
        return a + b

    registry = ToolRegistry()
    registry.register(add)
    missing = registry.execute("add", {"a": 1})
    extra = registry.execute("add", {"a": 1, "b": 2, "c": 3})
    assert missing.is_error is True
    assert extra.is_error is True


def test_execute_none_arguments_uses_defaults() -> None:
    """arguments 为 None 时视为空参数，handler 默认值生效。"""

    @tool
    def greet(name: str = "世界") -> str:
        """问候。"""
        return f"你好，{name}"

    registry = ToolRegistry()
    registry.register(greet)
    result = registry.execute("greet", None)
    assert result.is_error is False
    assert result.content == "你好，世界"


def test_manual_tool_registration_works() -> None:
    """手工构造 Tool（不经装饰器）同样可以登记与执行。"""
    manual = Tool(
        name="shout",
        description="把输入变大写",
        parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        handler=lambda text: text.upper(),
    )
    registry = ToolRegistry()
    registry.register(manual)
    assert "shout" in [schema["function"]["name"] for schema in registry.schemas()]
    result = registry.execute("shout", {"text": "zhixing"})
    assert result.is_error is False
    assert result.content == "ZHIXING"
